import boto3
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, time
from botocore.exceptions import ClientError
from tqdm import tqdm
import re

# === AWS Setup ===
session = boto3.Session(profile_name="calpoly", region_name="us-west-2")
bedrock_agent = session.client("bedrock-agent-runtime")
knowledge_base_id = "DB1EZE0UT6"

# === Load & Clean Excel ===
current_dir = Path(__file__).resolve().parent
file_path = current_dir.parent / "FY2024_Q2_Continous_Auditing_Procedures.xlsx"
df = pd.read_excel(file_path, skiprows=8)

# Ensure column names
df.columns = [col if pd.notna(col) and str(col).strip() else f"Unnamed_{i}" for i, col in enumerate(df.columns)]

# Convert dates
for col in ["Travel Start Date", "Travel End Date", "Transaction Date"]:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")

if "Report Key" not in df.columns:
    raise ValueError("Missing 'Report Key' column.")

# Add output columns
df["Flagged"] = ""
df["Reason"] = ""

# === JSON-safe converter ===
def make_json_safe(obj):
    if isinstance(obj, (datetime, pd.Timestamp)):
        return obj.isoformat()
    if isinstance(obj, time):
        return obj.strftime("%H:%M:%S")
    return obj

# === AI Call Wrapper ===
def call_knowledge_base(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = bedrock_agent.retrieve_and_generate(
                input={"text": prompt},
                retrieveAndGenerateConfiguration={
                    "type": "KNOWLEDGE_BASE",
                    "knowledgeBaseConfiguration": {
                        "knowledgeBaseId": knowledge_base_id,
                        "modelArn": "arn:aws:bedrock:us-west-2::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0",
                        'retrievalConfiguration': {
                            'vectorSearchConfiguration': {
                                'numberOfResults': 1
                            }
                        },
                    }
                }
            )
            return response['output']['text']
        except ClientError as e:
            if attempt < max_retries - 1:
                continue
            raise e

# === Helpers for robust parsing ===
def extract_json_array(text):
    pattern = re.compile(r'\[\s*{.*?}\s*\]', re.DOTALL)
    match = pattern.search(text)
    if not match:
        return None
    candidate = match.group(0)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None

def normalize_flag(value):
    if not isinstance(value, str):
        return "No"
    val = value.strip().lower()
    if val in ['yes', 'true', '1']:
        return "Yes"
    return "No"

def safe_parse_flags(text):
    text_strip = text.strip()
    # Auto-fix missing closing bracket for JSON array
    if text_strip.startswith('[') and not text_strip.endswith(']'):
        text_strip += ']'
    flags = extract_json_array(text_strip)
    if flags is None:
        return None
    # Normalize flags and ensure 'Reason' key
    for f in flags:
        f["Flagged"] = normalize_flag(f.get("Flagged", "No"))
        if "Reason" not in f:
            f["Reason"] = ""
    return flags


results = []

report_keys = df["Report Key"].unique()[:]

for report_key in tqdm(report_keys, desc="🔍 Evaluating All Trips"):
    trip_df = df[df["Report Key"] == report_key]
    base = trip_df.iloc[0]
    trip_context = {
        "employee": base.get('Employee Name', ''),
        "employee_id": base.get('Employee ID', ''),
        "trip_type": base.get('Trip Type', ''),
        "travel_start": base.get('Travel Start Date', ''),
        "travel_end": base.get('Travel End Date', ''),
        "with_students": base.get('Are you traveling with students/employees?', ''),
        "purpose": base.get('Trip Purpose', ''),
        "expenses": [
            {
                "type": row.get("Expense Type", ""),
                "amount": row.get("Expense Amount (rpt)", 0),
                "transaction_date": row.get("Transaction Date", ""),
                "vendor": row.get("Vendor", ""),
                "mileage_rate": row.get("Mileage Rate", None),
                "is_personal": str(row.get("Is Personal Expense?", "")).lower() in ['yes', 'true']
            }
            for _, row in trip_df.iterrows()
        ]
    }

    try:
        context_json = json.dumps(trip_context, indent=2, default=make_json_safe)
    except Exception as e:
        print(f"❌ JSON serialization error for Report Key {report_key}: {e}")
        continue

    prompt = f"""
You are a university travel compliance officer.

Use the Cal Poly and CSU travel policies from your knowledge base to evaluate this trip and its expenses.

Trip context:
{context_json}

Respond only with a JSON array, and nothing else.

Do NOT include any introduction, markdown, or commentary.

Your output MUST be a valid JSON array where each element includes "Flagged" and "Reason" keys, e.g.:

[
  {{"Flagged": "Yes", "Reason": "Exceeded daily meal limit"}},
  {{"Flagged": "No", "Reason": ""}}
]
"""

    try:
        ai_response = call_knowledge_base(prompt)
        print(f"\nRaw AI response for Report Key {report_key}:\n{ai_response}\n")  # Debug print

        flags = safe_parse_flags(ai_response)
        if flags is None or len(flags) != len(trip_df):
            print(f"⚠️ Parsing failed or length mismatch for Report Key {report_key}")
            with open(current_dir / f"bad_response_{report_key}.txt", "w", encoding="utf-8") as f:
                f.write(ai_response)
            continue

        trip_df.loc[:, "Flagged"] = [f.get("Flagged", "") for f in flags]
        trip_df.loc[:, "Reason"] = [f.get("Reason", "") for f in flags]
        results.append(trip_df)

    except Exception as e:
        print(f"❌ Error on Report Key {report_key}: {e}")
        continue

# === Save Final Output ===
if results:
    final_df = pd.concat(results)
    output_file = current_dir.parent / "flagged_expenses_kb_bedrock_sample.xlsx"
    final_df.to_excel(output_file, index=False)
    print(f"✅ Done. Output saved to {output_file}")
else:
    print("⚠️ No output generated.")

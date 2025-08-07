import boto3
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, time
from botocore.exceptions import ClientError
from tqdm import tqdm
import re
from io import BytesIO

# === AWS Setup ===
try:
    session = boto3.Session(profile_name="calpoly", region_name="us-west-2")
    bedrock_agent = session.client("bedrock-agent-runtime")
    knowledge_base_id = "DB1EZE0UT6"
    AWS_AVAILABLE = True
except Exception:
    AWS_AVAILABLE = False
    print("AWS not configured - running in basic mode")

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
    if text_strip.startswith('[') and not text_strip.endswith(']'):
        text_strip += ']'
    flags = extract_json_array(text_strip)
    if flags is None:
        return None
    for f in flags:
        f["Flagged"] = normalize_flag(f.get("Flagged", "No"))
        if "Reason" not in f:
            f["Reason"] = ""
    return flags

def clean_data_sheet(df_raw):
    """Clean the raw Excel data"""
    df = df_raw.copy()
    if len(df) > 8:
        df = df[8:].copy()
        if len(df_raw) > 7:
            df.columns = df_raw.iloc[7]
    
    # Ensure column names
    df.columns = [col if pd.notna(col) and str(col).strip() else f"Unnamed_{i}" for i, col in enumerate(df.columns)]
    
    # Convert dates
    for col in ["Travel Start Date", "Travel End Date", "Transaction Date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    
    # Drop entirely empty columns
    df = df.dropna(axis=1, how='all')
    
    # Add AI analysis columns if not present
    if "Flagged" not in df.columns:
        df["Flagged"] = ""
    if "Reason" not in df.columns:
        df["Reason"] = ""
    
    df = df.reset_index(drop=True)
    return df

def process_with_ai(df):
    """Process DataFrame with AI compliance checking"""
    if not AWS_AVAILABLE:
        print("AWS not available - skipping AI analysis")
        return df
    
    if "Report Key" not in df.columns:
        print("No Report Key column found - skipping AI analysis")
        return df
    
    results = []
    report_keys = df["Report Key"].unique()[:5]  # Limit for demo
    
    for report_key in tqdm(report_keys, desc="🔍 AI Analysis"):
        trip_df = df[df["Report Key"] == report_key].copy()
        base = trip_df.iloc[0]
        
        trip_context = {
            "employee": base.get('Employee Name', ''),
            "trip_type": base.get('Trip Type', ''),
            "expenses": [
                {
                    "type": row.get("Expense Type", ""),
                    "amount": row.get("Expense Amount (rpt)", 0),
                    "vendor": row.get("Vendor", "")
                }
                for _, row in trip_df.iterrows()
            ]
        }
        
        try:
            context_json = json.dumps(trip_context, default=make_json_safe)
            prompt = f"Analyze this trip for compliance violations: {context_json}"
            ai_response = call_knowledge_base(prompt)
            flags = safe_parse_flags(ai_response)
            
            if flags and len(flags) == len(trip_df):
                trip_df.loc[:, "Flagged"] = [f.get("Flagged", "") for f in flags]
                trip_df.loc[:, "Reason"] = [f.get("Reason", "") for f in flags]
            
            results.append(trip_df)
        except Exception as e:
            print(f"AI analysis failed for {report_key}: {e}")
            results.append(trip_df)
    
    return pd.concat(results) if results else df

def clean_excel_with_ai(file):
    """Main function for Flask integration"""
    try:
        # Read Excel file
        if hasattr(file, 'read'):
            df_raw = pd.read_excel(file)
        else:
            df_raw = pd.read_excel(file)
        
        # Clean the data
        df_clean = clean_data_sheet(df_raw)
        
        # Apply AI analysis if available
        if AWS_AVAILABLE:
            df_clean = process_with_ai(df_clean)
        
        return df_clean
        
    except Exception as e:
        print(f"Error processing file: {e}")
        # Fallback to basic cleaning
        df = pd.read_excel(file, skiprows=8) if hasattr(file, 'read') else pd.read_excel(file, skiprows=8)
        df.columns = [col if pd.notna(col) else f"Col_{i}" for i, col in enumerate(df.columns)]
        return df
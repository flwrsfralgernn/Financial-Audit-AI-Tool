import json
import random
import os
from typing import Optional
from services.prompt_builder import *
from config.settings import REPORTS_DIR
from services.policy_loader import load_policy_text
from config.settings import DEFAULT_POLICY_FILE  # optiona

def invoke_claude_model(prompt: str, bedrock_runtime) -> str:
    """
    Sends a prompt to Claude 3 Sonnet via Amazon Bedrock and returns the full streamed response text.
    """

    response = bedrock_runtime.invoke_model_with_response_stream(
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1024,
            "temperature": 0.5,
        }),
        modelId="anthropic.claude-3-sonnet-20240229-v1:0",  # full Claude 3 model ID
        accept="application/json",
        contentType="application/json"
    )

    response_body = response['body']
    full_response = ""

    for event in response_body:
        if "chunk" in event:
            chunk_data = json.loads(event["chunk"]["bytes"].decode())

            if "delta" in chunk_data and "text" in chunk_data["delta"]:
                full_response += chunk_data["delta"]["text"]

    return full_response


import re

def extract_violation_exception_rows(text: str):
    """
    Robustly parse violation/exception row numbers from the full response.
    1) Try strict footer lines (with ':' or '-').
    2) Fallback: scan 'Violations:' / 'Exceptions:' sections for 'Row <num>' patterns.
    Returns (violations:list[int], exceptions:list[int]).
    """

    def parse_footer(label):
        # Accept "Violation Rows:" or "Violation Rows -", any case/spacing, emoji optional
        pat = rf"{label}\s*rows\s*[:\-]\s*([^\n\r]+)"
        m = re.search(pat, text, flags=re.IGNORECASE)
        if not m:
            return []
        s = m.group(1).strip()
        if s.lower() == "none":
            return []
        return [int(x) for x in re.findall(r"\d+", s)]

    # 1) Footer attempt
    viol = parse_footer("violation")
    exce = parse_footer("exception")
    if viol or exce:
        return viol, exce

    # 2) Section fallback: collect numbers after "Row " tokens under headings
    def rows_from_section(section_title):
        # Find the section start
        m = re.search(rf"{section_title}\s*:", text, flags=re.IGNORECASE)
        if not m:
            return []
        start = m.end()
        # Take the next ~1200 chars (enough for a few bullets)
        chunk = text[start:start+1200]
        # Extract all "Row 123" and also plain numbers in comma lists
        nums = set(int(n) for n in re.findall(r"\bRow\s+(\d+)\b", chunk, flags=re.IGNORECASE))
        # plus numbers in lists like "Row 1, 2, 3" or "1, 2, 3" right under the section
        nums.update(int(n) for n in re.findall(r"\b(\d{1,7})\b", chunk) if len(n) <= 7)
        return sorted(nums)

    viol2 = rows_from_section("Violations")
    exce2 = rows_from_section("Exceptions")
    return viol2, exce2



def audit_single_employee(employee_id, report_key, df_emp, bedrock_runtime, policy_path: Optional[str] = None):
    """Audit a single employee group - used for parallel processing"""
    print(f"\n🔍 Auditing Employee: {employee_id}, Report Key: {report_key}")

    constant_fields, csv_data = format_employee_expenses_as_csv(df_emp)
    policy_text = load_policy_text(policy_path or str(DEFAULT_POLICY_FILE))
    prompt = create_audit_prompt(constant_fields, csv_data, policy_text=policy_text)

    full_response = invoke_claude_model(prompt, bedrock_runtime)
    print("✅ Audit Result received")

    # write .txt next to Excel outputs (project_root/audit_reports)
    filename = f"Report Employee ID-{employee_id} Report Key-{report_key}.txt"
    filepath = REPORTS_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_response)
    print(f"📝 Saved model response to: {filepath}")

    violation_rows, exception_rows = extract_violation_exception_rows(full_response)

    return {
        "employee_id": employee_id,
        "report_key": report_key,
        "response": full_response,
        "violation_rows": violation_rows,
        "exception_rows": exception_rows,
    }



def run_audit_for_multiple_employees(df_clean, bedrock_runtime, group_count=3):
    """
    Processes a random sample of `group_count` employee-report groups using parallel processing.
    Returns only the audited rows flagged and saved to Excel.
    """
    from concurrent.futures import ThreadPoolExecutor

    groups = df_clean.groupby(['Employee ID', 'Report Key'])
    group_keys = list(groups.groups.keys())
    sampled_keys = random.sample(group_keys, min(group_count, len(group_keys)))

    results = []
    all_violation_rows = []
    all_exception_rows = []

    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=32) as executor:
        futures = []
        for employee_id, report_key in sampled_keys:
            df_emp = groups.get_group((employee_id, report_key))
            future = executor.submit(audit_single_employee, employee_id, report_key, df_emp, bedrock_runtime)
            futures.append(future)

        # Collect results
        for future in futures:
            result = future.result()
            all_violation_rows.extend(result["violation_rows"])
            all_exception_rows.extend(result["exception_rows"])
            results.append({
                "employee_id": result["employee_id"],
                "report_key": result["report_key"],
                "response": result["response"]
            })

    return all_violation_rows, all_exception_rows, results
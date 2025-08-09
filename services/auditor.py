import json
import random
import os
from services.prompt_builder import *
from pathlib import Path
from config.settings import REPORTS_DIR

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


def extract_violation_exception_rows(response_text):
    """
    Extracts violation and exception row numbers from the end of the Claude response.
    Assumes the format is always the same and the last two lines contain the info.
    """
    lines = response_text.strip().splitlines()[-5:]  # look at last few lines
    violation_line = next((line for line in lines if "Violation Rows:" in line), "")
    exception_line = next((line for line in lines if "Exception Rows:" in line), "")

    violation_content = violation_line.replace("👉", "").replace("Violation Rows:", "").strip()
    exception_content = exception_line.replace("👉", "").replace("Exception Rows:", "").strip()

    violation_rows = []
    exception_rows = []

    if violation_content.lower() != "none":
        violation_rows = [int(x.strip()) for x in violation_content.split(",") if x.strip().isdigit()]

    if exception_content.lower() != "none":
        exception_rows = [int(x.strip()) for x in exception_content.split(",") if x.strip().isdigit()]

    return violation_rows, exception_rows


def audit_single_employee(employee_id, report_key, df_emp, bedrock_runtime):
    """Audit a single employee group - used for parallel processing"""
    print(f"\n🔍 Auditing Employee: {employee_id}, Report Key: {report_key}")

    constant_fields, csv_data = format_employee_expenses_as_csv(df_emp)
    prompt = create_audit_prompt(constant_fields, csv_data)

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
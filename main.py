import pandas as pd
from boto3 import Session
import json
import random
import os
from openpyxl.styles import PatternFill
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl import Workbook
from config import *


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


def clean_data_sheet(df_raw):
    """
    Cleans the 'DATA' sheet from FY2024_Q2_Continous_Auditing_Procedures.xlsx
    """
    # Set proper headers from row 7
    df1 = df_raw[8:].copy()
    df1.columns = df_raw.iloc[7]

    # Drop columns that are entirely NaN
    df1 = df1.dropna(axis=1, how='all')

    df1["Original Row"] = df_raw.index[8:] + 2  # since Excel is 1-based and header is row 8

    # Reset index
    df1 = df1.reset_index(drop=True)
    # Normalize column names
    # df.columns = [str(col).strip().lower().replace(' ', '_').replace('\n', '_') for col in df.columns]

    keep_columns = [
        "Original Row",
        "Employee ID",
        "Employee Department",
        "Report Key",
        "Trip Type",
        "Parent Expense Type",
        "Expense Type",
        "Expense Amount (rpt)",
        "Approved Amount (rpt)",
        "Are you traveling with students/employees?",
        "Travel Start Date",
        "Travel End Date",
        "First Submitted Date",
        "Last Submitted Date",
        "Reports to Approval 2",
        "Budget Approval",
        "Approved Date / Sent for Payment Date",
        "Transaction Date",
        "Payment Type",
        "Vendor",
        "Vendor State/Province/Region",
        "Transportation Type ",
        "Is Personal Expense?",
        "Personal Car Mileage From Location",
        "Personal Car Mileage To Location",
        "Entry Comment(s)",
        "Trip Purpose",
        "Active/Term Date",
        "Total Approved Amount (rpt)",
        "Processor Approval Date",
        "Sent for Payment Date",
        "Paid Date"
    ]
    df1 = df1[keep_columns]

    return df_raw, df1


def format_employee_expenses_as_csv(employee_df, max_rows=50):
    """
    Converts an employee's expense records into a CSV-formatted string for LLM prompt.
    - Removes columns with same value in all rows.
    - Returns CSV and list of constant fields.
    """
    df_trunc = employee_df.head(max_rows)

    # Detect columns with same value in all rows
    constant_columns = {}
    variable_df = df_trunc.copy()

    for col in df_trunc.columns:
        if df_trunc[col].nunique(dropna=False) == 1:
            constant_columns[col] = df_trunc[col].iloc[0]
            variable_df.drop(columns=[col], inplace=True)

    # Format constant columns as key=value lines
    constant_lines = [f"{key} = {value}" for key, value in constant_columns.items()]
    constants_text = "\n".join(constant_lines)

    # CSV output
    csv_text = variable_df.to_csv(index=False)

    return constants_text, csv_text


def create_audit_prompt(constant_fields: str, csv_data: str) -> str:
    return f"""
\n\nHuman: You are a travel expense compliance auditor.

Review the following expense data and detect any **violations or exceptions** based on the Cal Poly and CSU travel policy.

The expense data is split into two parts:
1. **Constant Fields** — these apply to all rows equally.
2. **Variable Expense Records (CSV)** — each row represents a specific expense entry.

Use **both the constant and variable fields** when checking for compliance.

Be clear and specific about each row:
- What was violated or what exception applies
- Why it's a violation or exception
- Any important details

At the end of your response:
👉 Return two separate lists of **Original Row** values (from the 'Original Row' column in the CSV):
Example:
    Violation Rows: 120, 123, 127  
    Exception Rows: 121, 125

### Constant Fields (apply to all rows):
{constant_fields}

### Variable Expense Records (CSV):
{csv_data}

### Policy Compliance Rules (Violations and Exceptions):

🚫 GENERAL VIOLATIONS:
1. Travel without pre-approval via Concur, Pre-Auth form, or 1A (students).
2. Booking bundled travel packages without itemized expenses.
3. International travel not registered with International Center.
4. Claiming meals for <24h travel without overnight stay or approval.
5. Reimbursement for lunch on <24h travel (never allowed).
6. Personal vehicle used without justification or Driver Safety Program.
7. Personal vehicle used for >250mi without cost comparison to airfare.
8. Optional car rental insurance purchased (domestic travel).
9. Rental from non-preferred vendor without required insurance.
10. Renting 15-passenger vans.
11. Airfare extended for personal travel without business-only price proof.
12. Personal charges on university account not repaid or flagged.
13. Missing required receipts ($75+) without missing receipt form.
14. Foreign expenses not properly converted to USD with proof.
15. Reimbursement claimed for commuting from home to Cal Poly.

✅ EXCEPTIONS:
1. Meals reimbursed on <24h travel if overnight stay included or approved (taxable).
2. Cash advances allowed only for:
   - Remote travel (no cards accepted)
   - Group/student travel (meals, taxis)
   - Must be pre-approved
3. Shared lodging reimbursed if cost does not exceed per-person per-night cap.
4. Bundled packages allowed if:
   - Each component is itemized
   - Cost savings are shown
5. Personal travel combined with business allowed if:
   - Business-only airfare documented
   - Traveler pays excess
6. Hospitality meals allowed but reduce per diem.
7. Missing lodging receipt allowed with valid explanation (friend, airport, etc.).

🏨 HOTEL VIOLATIONS:
- Hotel night > $500 — Flag if no adequate justification is provided.
- Hotel night > $333 — Flag if justification is vague or missing.
- Unreasonable cost — Especially for student or international travel.
- Missing itemization or comments — No breakdown or description in Concur report.
- Duplicate charges — Same expense appears in multiple months.

✈️ AIRFARE VIOLATIONS:
- Flight cost > $1500 — With missing or weak justification.
- Student airfare > $1500 — No detail on per-person or policy alignment.
- Duplicate flights or credits — Same trip entered more than once or refunded.
- Unjustified premium or international fares — If not explained in "Entry Comments".

🚗 CAR RENTAL VIOLATIONS:
- Daily rate > $36.04 — Per CP policy, without proper documentation.
- Non-Enterprise vendor used — No justification for deviating from contracted vendor.
- Rental total exceeds reasonable amount — Large charges not supported by trip duration.
- Missing justification — No "Entry Comments" or backup for the above issues.

🍽️ MEAL VIOLATIONS:
- Domestic meal > $55 — Without reviewer/preparer comment.
- Team/Group meal exceeds per-person limits:
  - $30 for breakfast
  - $60 for lunch
  - $90 for dinner
- No attendee count for group/team meal — Missing context to assess per-person costs.
- Meal type not specified — Makes validation against policy impossible.
- In-county purchases for team meals — Could indicate non-travel-related use.
- Athletics-related hospitality > $30 per person — For athletes/staff, per local rules.
- No "Entry Comment(s)" — For large or unusual hospitality expenses.

\n\nAssistant:
"""



def run_audit_for_multiple_employees(df_clean, bedrock_runtime, group_count=3):
    """
    Processes a random sample of `group_count` employee-report groups.
    """


    os.makedirs("audit_reports", exist_ok=True)

    groups = df_clean.groupby(['Employee ID', 'Report Key'])
    group_keys = list(groups.groups.keys())
    sampled_keys = random.sample(group_keys, min(group_count, len(group_keys)))

    results = []
    all_violation_rows = []
    all_exception_rows = []

    for employee_id, report_key in sampled_keys:
        df_emp = groups.get_group((employee_id, report_key))

        print(f"\n🔍 Auditing Employee: {employee_id}, Report Key: {report_key}")

        # Format data for prompt
        constant_fields, csv_data = format_employee_expenses_as_csv(df_emp)
        prompt = create_audit_prompt(constant_fields, csv_data)

        full_response = invoke_claude_model(prompt, bedrock_runtime)
        print("✅ Audit Result:\n", full_response)

        filename = f"Report Employee ID-{employee_id} Report Key-{report_key}.txt"
        filepath = os.path.join("audit_reports", filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(full_response)

        violation_rows, exception_rows = extract_violation_exception_rows(full_response)

        all_violation_rows.extend(violation_rows)
        all_exception_rows.extend(exception_rows)

        df_flagged = flag_audit_rows(df_clean.copy(), df_clean, all_violation_rows, all_exception_rows)
        excel_path = os.path.join("audit_reports", "Audited_Expenses.xlsx")
        save_to_excel_with_formatting(df_flagged, excel_path)

        results.append({
            "employee_id": employee_id,
            "report_key": report_key,
            "response": full_response
        })

    return all_violation_rows, all_exception_rows, results


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


def flag_audit_rows(df_original, df_clean, violation_rows, exception_rows):
    """
    Flags rows in df_original based on violation/exception row numbers.
    Adds a new column 'Audit Flag' with values 'Violation', 'Exception', or blank.
    """

    def get_flag(row_number):
        if row_number in violation_rows:
            return "Violation"
        elif row_number in exception_rows:
            return "Exception"
        return ""

    df_original["Audit Flag"] = df_clean["Original Row"].apply(get_flag)
    return df_original


def save_to_excel_with_formatting(df_flagged, output_path="audit_reports/Audited_Expenses.xlsx"):
    """
    Saves the DataFrame to Excel with colors for Violation (red) and Exception (yellow).
    """


    wb = Workbook()
    ws = wb.active
    ws.title = "Audited Data"

    # Add the dataframe rows
    for r in dataframe_to_rows(df_flagged, index=False, header=True):
        ws.append(r)

    # Define fills
    red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")  # Violation
    yellow_fill = PatternFill(start_color="FFFACD", end_color="FFFACD", fill_type="solid")  # Exception

    # Apply fills based on "Audit Flag"
    audit_flag_col = list(df_flagged.columns).index("Audit Flag") + 1  # 1-based index for Excel

    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):  # skip header
        cell = row[audit_flag_col - 1]
        if cell.value == "Violation":
            for c in row:
                c.fill = red_fill
        elif cell.value == "Exception":
            for c in row:
                c.fill = yellow_fill

    # Freeze top row
    ws.freeze_panes = "A2"

    # Save the workbook
    wb.save(output_path)
    print(f"✅ Saved audited file to: {output_path}")





# xls = pd.ExcelFile("data/FY2024_Q2_Continous_Auditing_Procedures.xlsx")
# print("📄 Sheets in the file:", xls.sheet_names)
#
# # Load a specific sheet (e.g., the first one)
# df = pd.read_excel(xls, sheet_name=xls.sheet_names[0])
# df_original, df_clean = clean_data_sheet(df)
#
# groups = df_clean.groupby(['Employee ID', 'Report Key'])
#
# session = Session(
#     aws_access_key_id=aws_access_key_id,
#     aws_secret_access_key=aws_secret_access_key,
#     aws_session_token=aws_session_token,
#     region_name="us-west-2"
# )
#
# bedrock_runtime = session.client("bedrock-runtime")
#
# violation_rows, exception_rows, results = run_audit_for_multiple_employees(df_clean, bedrock_runtime)
# # Step 1: Flag the original DataFrame
# df_flagged = flag_audit_rows(df_original, df_clean, violation_rows, exception_rows)
#
# # Step 2: Save to Excel
# save_to_excel_with_formatting(df_flagged)

import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
from boto3 import Session
import os

from main import (
    clean_data_sheet,
    run_audit_for_multiple_employees,
    flag_audit_rows,
    save_to_excel_with_formatting
)
from config import aws_access_key_id, aws_secret_access_key, aws_session_token


class AuditApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cal Poly Travel Expense Auditor")
        self.root.geometry("400x200")

        self.excel_path = None
        self.df_original = None
        self.df_clean = None
        self.bedrock_runtime = self.init_bedrock_runtime()

        self.import_btn = tk.Button(root, text="📁 Import Excel File", command=self.import_excel, width=30)
        self.import_btn.pack(pady=20)

        self.generate_btn = tk.Button(root, text="🚀 Generate Reports", command=self.generate_report, state=tk.DISABLED, width=30)
        self.generate_btn.pack(pady=10)

    def init_bedrock_runtime(self):
        session = Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            region_name="us-west-2"
        )
        return session.client("bedrock-runtime")

    def import_excel(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if file_path:
            try:
                xls = pd.ExcelFile(file_path)
                df = pd.read_excel(xls, sheet_name=xls.sheet_names[0])
                self.df_original, self.df_clean = clean_data_sheet(df)
                self.excel_path = file_path
                self.generate_btn.config(state=tk.NORMAL)
                messagebox.showinfo("Success", "Excel file imported successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load Excel file:\n{str(e)}")

    def generate_report(self):
        try:
            violation_rows, exception_rows, _ = run_audit_for_multiple_employees(self.df_clean, self.bedrock_runtime)
            df_flagged = flag_audit_rows(self.df_original, self.df_clean, violation_rows, exception_rows)

            messagebox.showinfo("✅ Done")
        except Exception as e:
            messagebox.showerror("Error", f"Error during audit:\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = AuditApp(root)
    root.mainloop()











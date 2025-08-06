import pandas as pd
import os


def clean_data_sheet(df_raw):
    """
    Cleans the 'DATA' sheet from FY2024_Q2_Continous_Auditing_Procedures.xlsx
    """
    # Set proper headers from row 7
    df = df_raw[8:].copy()
    df.columns = df_raw.iloc[7]

    # Drop columns that are entirely NaN
    df = df.dropna(axis=1, how='all')

    # Reset index
    df = df.reset_index(drop=True)
    print(df.columns)
    # Normalize column names
    # df.columns = [str(col).strip().lower().replace(' ', '_').replace('\n', '_') for col in df.columns]

    return df


def format_employee_expenses_all_columns(employee_df):
    """
    Formats all rows and all columns of the employee's expenses for LLM review.
    """
    lines = []
    for idx, (_, row) in enumerate(employee_df.iterrows(), start=1):
        entry_lines = [f"Entry #{idx}"]
        for col in employee_df.columns:
            entry_lines.append(f"{col}: {row[col]}")
        lines.append("\n".join(entry_lines))

    return "\n\n".join(lines)

def create_audit_prompt(employee_id, df):
    table = df.to_markdown(index=False)
    prompt = f"""
You are a compliance auditor.

Below is the travel expense report for employee ID `{employee_id}`. Use the policy information (available in your knowledge base) to identify **any violations**, and explain clearly why each one is a violation.

### Expense Data (Table):
{table}

List all potential violations and briefly justify them.
"""
    return prompt



xls = pd.ExcelFile("FY2024_Q2_Continous_Auditing_Procedures.xlsx")
print("📄 Sheets in the file:", xls.sheet_names)

# Load a specific sheet (e.g., the first one)
df = pd.read_excel(xls, sheet_name=xls.sheet_names[0])
df_clean = clean_data_sheet(df)

groups = df_clean.groupby('Employee ID')


employee_id, employee_df = list(groups)[0]

formatted_text = format_employee_expenses_all_columns(employee_df)
print(f"Employee ID: {employee_id}")
print(formatted_text)
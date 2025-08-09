
def format_employee_expenses_as_csv(employee_df, max_rows=10000):
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


def create_audit_prompt(constant_fields: str, csv_data: str, policy_text: str = "") -> str:
    policy_block = f"\n\n### Policy Reference (user-provided):\n{policy_text}\n" if policy_text else ""
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
👉 Return two separate lists of **Original Row** values at the end of the response (from the 'Original Row' column in the CSV):
Example:
    Violation Rows: 120, 123, 127  
    Exception Rows: 121, 125

### Constant Fields (apply to all rows):
{constant_fields}

### Variable Expense Records (CSV):
{csv_data}
{policy_block}

\n\nAssistant:
"""

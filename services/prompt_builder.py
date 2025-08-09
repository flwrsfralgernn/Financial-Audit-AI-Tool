
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
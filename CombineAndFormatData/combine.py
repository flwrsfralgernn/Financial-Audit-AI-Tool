import pandas as pd

expense_etd_df = pd.read_excel("Expense - Expense Type Detail (SLO) 2024.xlsx", sheet_name="Details_1", header=8)
employee_active_df = pd.read_excel("EE Active.xlsx", sheet_name="EE-Active")
employee_active_df = employee_active_df[["Emplid", "Empl Status Pay Ldescr", "Division", "Deptid Ldescr", "Position Ldescr"]]

# Merge on differently named keys
merged_df = pd.merge(
    expense_etd_df,
    employee_active_df,
    left_on ="Employee ID",
    right_on ="Emplid",
    how ="left"
)

# Drop the 'empid' column since it was just for matching
merged_df.drop(columns=["Emplid"], inplace=True)

expense_cf_df = pd.read_excel("Expense - Expense Reports with CF Information and Comments (2).xlsx", sheet_name="Summary_1", header=6)
expense_cf_df = expense_cf_df[["Report Key", "Request ID and Destination", "Total Approved Amount (rpt)", "Processor Approval Date"]]

merged_df = pd.merge(
    merged_df,
    expense_cf_df,
    on ="Report Key",
    how ="left"
)

expense_ppsa_df = pd.read_excel("Expense - Processor Paid Summary Account.xlsx", sheet_name="Page1_1", header=4)
expense_ppsa_df = expense_ppsa_df[["Sent for Payment Date",	"Paid Date", "Report Key", "Transaction Date", "Expense Type", "Approved Amount"]]

merged_df = pd.merge(
    merged_df,
    expense_ppsa_df,
    left_on=["Report Key", "Transaction Date", "Expense Type", "Approved Amount (rpt)"],
    right_on =["Report Key", "Transaction Date", "Expense Type", "Approved Amount"],
    how ="left"
)
merged_df.drop(columns=["Approved Amount"], inplace=True)

request_rit_df = pd.read_excel("Request - Risk International Travel with Header Comments (1).xlsx", sheet_name="Request - Risk International_1", header=7)
request_rit_df = request_rit_df[["Request ID", "Authorized Date", "Destination City/Location", "Destination Country"]]
merged_df = pd.merge(
    merged_df,
    request_rit_df,
    left_on=["Request ID(s)"],
    right_on =["Request ID"],
    how ="left"
)
merged_df.drop(columns=["Request ID"], inplace=True)

export_path = "master_expense_report.xlsx"
merged_df.to_excel(export_path, index=False)

print("Done Combining Reports")
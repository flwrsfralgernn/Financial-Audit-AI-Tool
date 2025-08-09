import pandas as pd


def load_excel_file(file_path):
    xls = pd.ExcelFile(file_path)
    df = pd.read_excel(xls, sheet_name=xls.sheet_names[0])
    return df

def clean_data_sheet(df_raw):
    """
    Cleans data sheet - handles both master reports (headers at row 0) and original files (headers at row 7)
    """
    # Check if this is a master report (headers already at row 0) or original file (headers at row 7)
    if 'Employee ID' in df_raw.columns:
        # Master report case - headers already at row 0
        df1 = df_raw.copy()
        df1["Original Row"] = df_raw.index + 2  # Excel is 1-based
    else:
        # Original file case - headers at row 7
        df1 = df_raw[8:].copy()
        df1.columns = df_raw.iloc[7]
        df1["Original Row"] = df_raw.index[8:] + 2  # since Excel is 1-based and header is row 8

    # Drop columns that are entirely NaN
    df1 = df1.dropna(axis=1, how='all')

    # Reset index
    df1 = df1.reset_index(drop=True)
    # Normalize column names
    # df.columns = [str(col).strip().lower().replace(' ', '_').replace('\n', '_') for col in df.columns]
    df1.columns = [str(c).strip().replace("\n", " ").replace("  ", " ") for c in df1.columns]
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
        "Transportation Type",
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

    return df1.copy(), df1
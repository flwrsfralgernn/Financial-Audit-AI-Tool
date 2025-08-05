import pandas as pd
import os

xls = pd.ExcelFile("FY2024_Q2_Continous_Auditing_Procedures.xlsx")
print("📄 Sheets in the file:", xls.sheet_names)

# Load a specific sheet (e.g., the first one)
df = pd.read_excel(xls, sheet_name=xls.sheet_names[0])
print(df)
from flask import Flask, render_template, request, redirect, url_for, send_file, session
import pandas as pd
import os
from datetime import datetime
from io import BytesIO
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
import tempfile
import uuid

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

@app.route('/')
def index():
    # Mock recent files for demo
    recent_files = [
        {'name': 'Q2_Audit_Data.xlsx', 'time': '2 hours ago'},
        {'name': 'Travel_Expenses.xlsx', 'time': '1 day ago'},
        {'name': 'Financial_Report.xlsx', 'time': '3 days ago'}
    ]
    return render_template('index.html', 
                         year=datetime.now().year,
                         recent_files=recent_files,
                         aws_available=True)

@app.route('/clean_excel', methods=['POST'])
def clean_excel():
    print("Upload route called")  # Debug
    
    if 'files' not in request.files:
        print("No files in request")
        return render_template('index.html', error="No files uploaded", year=datetime.now().year)
    
    files = request.files.getlist('files')
    print(f"Files received: {[f.filename for f in files]}")  # Debug
    
    if not files or all(f.filename == '' for f in files):
        return render_template('index.html', error="No files selected", year=datetime.now().year)
    
    # Filter valid Excel files
    valid_files = [f for f in files if f.filename.endswith(('.xlsx', '.xls'))]
    
    if not valid_files:
        return render_template('index.html', 
                             error="Please upload valid Excel files (.xlsx or .xls)",
                             year=datetime.now().year)
    
    try:
        print(f"Processing {len(valid_files)} files with AI...")  # Debug
        
        # Process each file and combine
        all_dataframes = []
        file_names = []
        
        for file in valid_files:
            print(f"Processing: {file.filename}")
            df_cleaned = clean_excel_with_ai(file)
            
            # Add source file column
            df_cleaned['Source_File'] = file.filename
            all_dataframes.append(df_cleaned)
            file_names.append(file.filename)
        
        # Combine all dataframes
        master_df = pd.concat(all_dataframes, ignore_index=True, sort=False)
        print(f"Combined {len(master_df)} total rows from {len(valid_files)} files")  # Debug
        
        # Fix duplicate column names
        cols = master_df.columns.tolist()
        seen = {}
        for i, col in enumerate(cols):
            if col in seen:
                seen[col] += 1
                cols[i] = f"{col}_{seen[col]}"
            else:
                seen[col] = 0
        master_df.columns = cols
        
        # Store cleaned data in temp file (for download)
        temp_id = str(uuid.uuid4())
        temp_file = os.path.join(tempfile.gettempdir(), f'cleaned_data_{temp_id}.pkl')
        master_df.to_pickle(temp_file)
        session['temp_file'] = temp_file
        
        # Calculate stats
        row_count = len(master_df)
        flagged_count = len(master_df[master_df.get('Flagged', '') == 'Yes']) if 'Flagged' in master_df.columns else 0
        
        # Generate HTML table for preview
        table_html = master_df.head(50).to_html(classes='table', table_id='data-table', escape=False)
        
        return render_template('index.html', 
                             table_html=table_html,
                             row_count=row_count,
                             flagged_count=flagged_count,
                             filename=f"Master file from {len(valid_files)} files",
                             file_count=len(valid_files),
                             year=datetime.now().year)
    except Exception as e:
        print(f"Error: {str(e)}")  # Debug
        return render_template('index.html', 
                             error=f"Error processing files: {str(e)}",
                             year=datetime.now().year)

@app.route('/upload_incomplete', methods=['POST'])
def upload_incomplete():
    if 'files' not in request.files:
        return render_template('index.html', error="No files uploaded", year=datetime.now().year)
    
    files = request.files.getlist('files')
    
    if not files or all(f.filename == '' for f in files):
        return render_template('index.html', error="No files selected", year=datetime.now().year)
    
    # Filter valid Excel files only for combining
    valid_files = [f for f in files if f.filename.endswith(('.xlsx', '.xls'))]
    
    if not valid_files:
        return render_template('index.html', 
                             error="Please upload valid Excel files (.xlsx or .xls) for combining",
                             year=datetime.now().year)
    
    try:
        # Combine and format the uploaded files
        master_df = combine_incomplete_reports(valid_files)
        
        # Store combined data in temp file
        temp_id = str(uuid.uuid4())
        temp_file = os.path.join(tempfile.gettempdir(), f'cleaned_data_{temp_id}.pkl')
        master_df.to_pickle(temp_file)
        session['temp_file'] = temp_file
        
        # Calculate stats
        row_count = len(master_df)
        flagged_count = 0  # No flagging for incomplete reports
        
        # Generate HTML table for preview
        table_html = master_df.head(50).to_html(classes='table', table_id='data-table', escape=False)
        
        return render_template('index.html', 
                             table_html=table_html,
                             row_count=row_count,
                             flagged_count=flagged_count,
                             filename=f"Combined incomplete reports from {len(valid_files)} files",
                             file_count=len(valid_files),
                             year=datetime.now().year)
    except Exception as e:
        return render_template('index.html', 
                             error=f"Error processing files: {str(e)}",
                             year=datetime.now().year)

def combine_incomplete_reports(files):
    """Combine multiple Excel files using the logic from combine.py"""
    date_columns = [
        "Travel Start Date", "Travel End Date", "First Submitted Date", "Last Submitted Date",
        "Reports to Approval 2", "Budget Approval", "Approved Date / Sent for Payment Date",
        "Transaction Date", "Processor Approval Date", "Sent for Payment Date", "Paid Date"
    ]
    
    # Create a mapping of expected file patterns to their processing logic
    file_data = {}
    
    for file in files:
        filename = file.filename.lower()
        
        # Identify file types based on filename patterns
        if 'expense type detail' in filename or 'etd' in filename:
            file_data['expense_etd'] = pd.read_excel(file, sheet_name=0, header=8)
        elif 'ee active' in filename or 'employee' in filename:
            df = pd.read_excel(file, sheet_name=0)
            file_data['employee_active'] = df[[col for col in ["Emplid", "Empl Status Pay Ldescr", "Division", "Deptid Ldescr", "Position Ldescr"] if col in df.columns]]
        elif 'expense reports with cf' in filename or 'cf information' in filename:
            df = pd.read_excel(file, sheet_name=0, header=6)
            file_data['expense_cf'] = df[[col for col in ["Report Key", "Request ID and Destination", "Total Approved Amount (rpt)", "Processor Approval Date"] if col in df.columns]]
        elif 'processor paid summary' in filename or 'ppsa' in filename:
            df = pd.read_excel(file, sheet_name=0, header=4)
            file_data['expense_ppsa'] = df[[col for col in ["Sent for Payment Date", "Paid Date", "Report Key", "Transaction Date", "Expense Type", "Approved Amount"] if col in df.columns]]
        elif 'risk international travel' in filename or 'international travel' in filename:
            df = pd.read_excel(file, sheet_name=0, header=7)
            file_data['request_rit'] = df[[col for col in ["Request ID", "Authorized Date", "Destination City/Location", "Destination Country"] if col in df.columns]]
        else:
            # Generic file - try to read with different headers
            try:
                df = pd.read_excel(file, header=0)
            except:
                try:
                    df = pd.read_excel(file, header=8)
                except:
                    df = pd.read_excel(file, header=6)
            df['Source_File'] = file.filename
            file_data['generic'] = df
    
    # Start with the main expense file or first available file
    if 'expense_etd' in file_data:
        merged_df = file_data['expense_etd'].copy()
        
        # Merge employee data
        if 'employee_active' in file_data:
            merged_df = pd.merge(
                merged_df,
                file_data['employee_active'],
                left_on="Employee ID" if "Employee ID" in merged_df.columns else merged_df.columns[0],
                right_on="Emplid" if "Emplid" in file_data['employee_active'].columns else file_data['employee_active'].columns[0],
                how="left"
            )
            if "Emplid" in merged_df.columns:
                merged_df.drop(columns=["Emplid"], inplace=True)
        
        # Merge expense CF data
        if 'expense_cf' in file_data:
            merged_df = pd.merge(
                merged_df,
                file_data['expense_cf'],
                on="Report Key" if "Report Key" in merged_df.columns else None,
                how="left"
            )
        
        # Merge expense PPSA data
        if 'expense_ppsa' in file_data:
            merge_cols = [col for col in ["Report Key", "Transaction Date", "Expense Type", "Approved Amount (rpt)"] if col in merged_df.columns]
            if merge_cols:
                merged_df = pd.merge(
                    merged_df,
                    file_data['expense_ppsa'],
                    left_on=merge_cols,
                    right_on=["Report Key", "Transaction Date", "Expense Type", "Approved Amount"][:len(merge_cols)],
                    how="left"
                )
                if "Approved Amount" in merged_df.columns:
                    merged_df.drop(columns=["Approved Amount"], inplace=True)
        
        # Merge request data
        if 'request_rit' in file_data:
            merged_df = pd.merge(
                merged_df,
                file_data['request_rit'],
                left_on="Request ID(s)" if "Request ID(s)" in merged_df.columns else None,
                right_on="Request ID" if "Request ID" in file_data['request_rit'].columns else None,
                how="left"
            )
            if "Request ID" in merged_df.columns:
                merged_df.drop(columns=["Request ID"], inplace=True)
    
    else:
        # If no main expense file, combine all available data
        all_dfs = list(file_data.values())
        merged_df = pd.concat(all_dfs, ignore_index=True, sort=False)
    
    # Apply date formatting from format.py
    for col in date_columns:
        if col in merged_df.columns:
            merged_df[col] = pd.to_datetime(merged_df[col], errors='coerce').dt.date
    
    return merged_df

@app.route('/download_cleaned')
def download_cleaned():
    if 'temp_file' not in session or not os.path.exists(session['temp_file']):
        return redirect(url_for('index'))
    
    # Load DataFrame from temp file
    df = pd.read_pickle(session['temp_file'])
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Cleaned_Data', index=False)
    output.seek(0)
    
    # Clean up temp file
    try:
        os.remove(session['temp_file'])
        session.pop('temp_file', None)
    except:
        pass
    
    return send_file(output, 
                     download_name='master_financial_data.xlsx',
                     as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

if __name__ == '__main__':
    app.run(debug=True)
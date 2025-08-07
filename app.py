from flask import Flask, render_template, request, redirect, url_for, send_file, session
import pandas as pd
from ai_cleaner import clean_excel_with_ai
import os
from datetime import datetime
from io import BytesIO

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
        
        # Store cleaned data in session (for download)
        session['cleaned_data'] = master_df.to_json(date_format='iso')
        
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

@app.route('/download_cleaned')
def download_cleaned():
    if 'cleaned_data' not in session:
        return redirect(url_for('index'))
    
    # Reconstruct DataFrame from session
    df = pd.read_json(session['cleaned_data'])
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Cleaned_Data', index=False)
    output.seek(0)
    
    return send_file(output, 
                     download_name='master_financial_data.xlsx',
                     as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

if __name__ == '__main__':
    app.run(debug=True)
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
    
    if 'file' not in request.files:
        print("No file in request")
        return render_template('index.html', error="No file uploaded", year=datetime.now().year)
    
    file = request.files['file']
    print(f"File received: {file.filename}")  # Debug
    
    if file.filename == '':
        return render_template('index.html', error="No file selected", year=datetime.now().year)
    
    if file and file.filename.endswith(('.xlsx', '.xls')):
        try:
            print("Processing file with AI...")  # Debug
            # Process the file with AI
            df_cleaned = clean_excel_with_ai(file)
            print(f"Processed {len(df_cleaned)} rows")  # Debug
            
            # Fix duplicate column names
            cols = df_cleaned.columns.tolist()
            seen = {}
            for i, col in enumerate(cols):
                if col in seen:
                    seen[col] += 1
                    cols[i] = f"{col}_{seen[col]}"
                else:
                    seen[col] = 0
            df_cleaned.columns = cols
            
            # Store cleaned data in session (for download)
            session['cleaned_data'] = df_cleaned.to_json(date_format='iso')
            
            # Calculate stats
            row_count = len(df_cleaned)
            flagged_count = len(df_cleaned[df_cleaned.get('Flagged', '') == 'Yes']) if 'Flagged' in df_cleaned.columns else 0
            
            # Generate HTML table for preview
            table_html = df_cleaned.head(50).to_html(classes='table', table_id='data-table', escape=False)
            
            return render_template('index.html', 
                                 table_html=table_html,
                                 row_count=row_count,
                                 flagged_count=flagged_count,
                                 filename=file.filename,
                                 year=datetime.now().year)
        except Exception as e:
            print(f"Error: {str(e)}")  # Debug
            return render_template('index.html', 
                                 error=f"Error processing file: {str(e)}",
                                 year=datetime.now().year)
    else:
        return render_template('index.html', 
                             error="Please upload a valid Excel file (.xlsx or .xls)",
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
                     download_name='cleaned_financial_data.xlsx',
                     as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

if __name__ == '__main__':
    app.run(debug=True)
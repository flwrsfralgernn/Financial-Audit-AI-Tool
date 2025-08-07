from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

@app.route('/')
def index():
    try:
        return render_template('index.html', year=datetime.now().year)
    except Exception as e:
        return f"<h1>Template Error: {str(e)}</h1><p>Check if templates/index.html exists</p>"

@app.route('/clean_excel', methods=['POST'])
def clean_excel():
    return "<h1>File upload received!</h1>"

if __name__ == '__main__':
    print("Starting Flask app...")
    print("Templates folder exists:", os.path.exists('templates'))
    print("Static folder exists:", os.path.exists('static'))
    app.run(debug=True, host='0.0.0.0', port=5000)
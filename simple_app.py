from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Cal Poly Dashboard</title>
        <style>
            body { font-family: Arial; background: #f0f0f0; margin: 0; padding: 20px; }
            .header { background: #1a472a; color: white; padding: 20px; text-align: center; }
            .content { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; }
            .upload-form { margin: 20px 0; }
            input[type="file"] { margin: 10px 0; }
            button { background: #1a472a; color: white; padding: 10px 20px; border: none; border-radius: 4px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🐎 Cal Poly Financial Audit</h1>
        </div>
        <div class="content">
            <h2>Upload Excel File</h2>
            <form action="/upload" method="post" enctype="multipart/form-data" class="upload-form">
                <input type="file" name="file" accept=".xlsx,.xls" required />
                <br>
                <button type="submit">Process File</button>
            </form>
        </div>
    </body>
    </html>
    ''')

@app.route('/upload', methods=['POST'])
def upload():
    return "<h1>File upload would work here!</h1>"

if __name__ == '__main__':
    app.run(debug=True, port=5002)
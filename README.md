# Cal Poly Travel Expense Audit AI Tool

This project is an AI-powered system designed to automate and improve Cal Poly’s travel expense audit process. It reviews employee travel data exported from Concur and uses a large language model (Claude 3 Sonnet via Amazon Bedrock) to identify policy violations and exceptions based on CSU and Cal Poly travel rules.

## 🚀 Main Features

- Upload raw Concur Excel reports
- Clean and format data automatically
- Group expenses by employee and report
- Send expense data to Claude AI for review
- Detect violations and exceptions
- Generate color-coded Excel reports:
  - 🔴 Red = Violation
  - 🟡 Yellow = Exception
- Simple user interface (built with Tkinter)

## 🛠️ Technologies Used

- Python
- Amazon Bedrock (Claude 3 Sonnet)
- Pandas
- OpenPyXL
- Tkinter
- Boto3

## ⚙️ How It Works

1. You import the raw Excel file.
2. The program cleans and prepares the data.
3. It selects a few employee reports at random.
4. Each group is sent to Claude AI with a custom prompt.
5. Claude returns a list of flagged entries with reasons.
6. The result is saved as an Excel file in the `audit_reports` folder.

## 📦 Setup

1. Install the required Python packages:
2. Set up your AWS Bedrock access credentials in `config.py`
3. Run the app:

## 👨‍💻 Team Members

- Davit Hakobyan  
- Ashton Liu  
- Wenfan Wei  
- Isabela Fernandez
-Ellie Romero

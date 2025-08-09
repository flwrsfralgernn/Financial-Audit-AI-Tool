# Financial Audit AI Tool

AI-powered auditor for corporate travel & expense data. This desktop app ingests Concur-style Excel exports, applies policy rules (including your own), runs them through a Large Language Model (LLM) for nuanced checks, and produces clean reports and charts.

> **Note:** For illustration/demo purposes, the tool currently audits only **3 randomly selected employee/report groups** from the dataset. You can modify this in the code to process all groups.

## ✨ What it does
- **Import** one or many Concur Excel files (XLS/XLSX).
- **Clean & group** expenses by employee/report.
- **Policy checks**
  - **Rule-based**: fast validations from your configurable policy file.
  - **LLM checks**: context-aware audits against the provided policy text.
- **Outputs**
  - `audit_reports/`
    - `Audited_Expenses_<timestamp>.xlsx` (full dataset with an **Audit Flag** column)
    - `Violations_Report_<timestamp>.xlsx`
    - `Exceptions_Report_<timestamp>.xlsx`
    - Per-group `.txt` summaries
  - `summary_charts/` PNG charts for quick insights
- **GUI workflow** (simple desktop app) — point, click, audit.

## 🧭 Project structure
```
Financial-Audit-AI-Tool/
├─ app/
│  ├─ main.py                 # Launch the desktop app (start here)
│  ├─ ...                     # UI and helpers
├─ config/
│  ├─ policies/
│  │  └─ policy.txt           # Editable rule-based policy (your quick rules)
│  └─ .env.example            # (optional) example env file
├─ audit_reports/             # Generated audit workbooks & text reports
├─ summary_charts/            # Generated PNG charts
├─ requirements.txt           # Python deps
├─ README.md                  # ← You are here
└─ ...                        # Other modules/utilities
```
> Your exact tree may differ a bit as you iterate.

## 🛠️ Prerequisites
- **Python 3.10+**
- **pip**
- **AWS account** with access to **Amazon Bedrock** (for the LLM API)
- Works on Windows/macOS/Linux

## 🚀 Quick Start

### 1) Clone
```bash
git clone https://github.com/flwrsfralgernn/Financial-Audit-AI-Tool.git
cd Financial-Audit-AI-Tool
```

### 2) (Optional) Create a virtual environment
```bash
python -m venv venv
# macOS / Linux
source venv/bin/activate
# Windows
venv\Scripts\activate
```

### 3) Install dependencies
```bash
pip install -r requirements.txt
```

### 4) Configure AWS credentials
Option A — AWS CLI:
```bash
aws configure
# Enter AWS Access Key ID, Secret, and default region (e.g., us-west-2)
```
Option B — Environment variables:
```bash
# macOS / Linux
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=us-west-2

# Windows PowerShell
$env:AWS_ACCESS_KEY_ID="..."
$env:AWS_SECRET_ACCESS_KEY="..."
$env:AWS_DEFAULT_REGION="us-west-2"
```

### 5) Configure the app
Create a `.env` file or set env vars:
```ini
AWS_REGION=us-west-2
BEDROCK_MODEL_ID=amazon.titan-text-lite-v1
```

### 6) Run the application
```bash
python app/main.py
```
Select your Concur Excel file (or combine multiple), click **Run Audit**, and check `audit_reports/` & `summary_charts/`.

## 📁 Input expectations
- Concur-style Excel export (XLS/XLSX)
- Typical fields: date, category, amount, merchant, payment type, report/employee IDs
- Includes `Original Row` index for model output alignment

## 🧩 How the audit works
1. Load & clean data
2. Group by employee/report
3. Apply rule-based checks from `config/policies/policy_rules.txt`
4. **Randomly select 3 groups** (demo mode)
5. Send selected groups to anthropic.claude-3-sonnet-20240229-v1:0 for detailed analysis based on your policy text
6. Merge returned row flags into dataset
7. Output Excel, text reports, and charts

## 📝 Editing the policy
- **Local rules:** Edit `config/policies/policy_rules.txt`
- This text is also sent to the LLM to guide compliance checking.

## ▶️ Usage
1. Run `python app/main.py`
2. Select or combine Excel files
3. Click **Run Audit**
4. Review:
   - `audit_reports/Audited_Expenses_<timestamp>.xlsx`
   - `audit_reports/Violations_Report_<timestamp>.xlsx`
   - `audit_reports/Exceptions_Report_<timestamp>.xlsx`
   - Individual `.txt` summaries
   - Charts in `summary_charts/`

## 📊 Output details
- **Audited_Expenses**: All rows + `Audit Flag` column, with optional color formatting (red for violations, yellow for exceptions)
- **Violations/Exceptions Reports**: Only flagged rows
- **TXT Summaries**: Plain text findings
- **Charts**: PNG bar/pie charts of violation data

## 🔧 Configuration
Required env vars:
- `AWS_REGION`
- `BEDROCK_MODEL_ID`
Optional:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

## 🧪 Dev tips
- Test with small files first
- Keep `policy.txt` concise
- Log prompts & outputs during debugging
- Keep UI thin; call core logic from buttons

## ❗ Troubleshooting
- **Invalid AWS token:** Re-run `aws configure` or update env vars
- **No results from LLM:** Ensure policy.txt is not empty
- **Nothing flagged:** Ensure policy rules are clear and data matches expected format
- **Output path issues:** Ensure `audit_reports/` and `summary_charts/` exist

## 🤝 Contributing
1. Open an issue
2. Branch from main
3. Add tests/docs

## 📜 License
MIT (or update for your org)

## 💡 Roadmap
- CLI mode
- Multi-policy runs
- Dashboards
- Per-diem & receipt OCR
- Exception workflow enhancements

## 🙌 Acknowledgments
Thanks to contributors and the AWS Cal Poly DxHub AI Summer Program community.

## 👥 Contributors
- Davit Hakobyan
- Isabela Fernandez
- Wenfan Wei
- Ellie Romero
- Ashton Liu  

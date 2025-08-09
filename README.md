# Financial Audit AI Tool

An AI-powered desktop application that audits travel expense reports for **policy compliance** using **Amazon Bedrock** and a customizable travel policy file.  
Designed during the **CSU Summer AI Camp 2025** to help organizations automatically detect policy **violations** and **exceptions** in expense data.

---

## 📌 Features

- **Excel Upload & Audit** – Import Concur or other expense spreadsheets and run a compliance check.  
- **Policy-Aware Analysis** – Uses rules from a customizable `policy.txt` file in `config/policies/`.  
- **Random Sample Auditing** – For demonstration purposes, the app audits **3 random employee/report groups** per run.  
- **Detailed AI Explanations** – Each audited group produces a `.txt` report with clear reasoning.  
- **Flagged Excel Output** – Generates an Excel file with:
  - Red highlighting for violations  
  - Yellow highlighting for exceptions  
- **Separate Reports** – Creates separate **Violations** and **Exceptions** workbooks.  
- **Management Visuals** – Generates summary charts:
  - Total violations by category  
  - Trends over time  
  - Top 10 repeat offenders  
- **Tkinter UI** – Simple, no-code interface for running audits.

---

## 🗂 Folder Structure

financial-audit-ai-tool/
├─ app/ # Tkinter UI
│ ├─ main.py # Entry point – run this to start the app
│ ├─ controllers.py
│ ├─ widgets.py
│ └─ threads.py
├─ services/ # Core logic and helpers
│ ├─ io_loader.py
│ ├─ grouper.py
│ ├─ prompt_builder.py
│ ├─ bedrock_client.py
│ ├─ policy_parser.py
│ ├─ auditor.py
│ ├─ report_writer.py
│ ├─ summary_stats.py
│ └─ charts.py
├─ config/
│ ├─ settings.py
│ └─ policies/
│ └─ policy.txt # Editable travel policy rules
├─ audit_reports/ # Generated Excel, text reports, and charts
├─ tests/
├─ requirements.txt
└─ README.md


---

## ⚙️ Installation

### 1. Create a virtual environment (optional but recommended)
```bash
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows

## 2. (Optional) Create a Virtual Environment

```bash
python -m venv venv

# Mac/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate

## 3. Install Dependencies

```bash
pip install -r requirements.txt



## 👨‍💻 Team Members

- Davit Hakobyan  
- Ashton Liu  
- Wenfan Wei  
- Isabela Fernandez
-Ellie Romero

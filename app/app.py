from combine_and_format import combine_and_format
import tkinter as tk
from tkinter import filedialog, ttk
from boto3 import Session
from config.config import aws_access_key_id, aws_secret_access_key, aws_session_token
from services.report_writer import *
from services.auditor import *
from services.io_loader import *


class AuditApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cal Poly Travel Expense Auditor")
        self.root.geometry("700x600")
        self.root.resizable(False, False)

        self.excel_path = None
        self.df_original = None
        self.df_clean = None
        self.bedrock_runtime = self.init_bedrock_runtime()

        # File paths for master report creation
        self.master_files = {
            'Expense Type Detail': None,
            'EE Active': None,
            'CF Information': None,
            'Processor Paid Summary': None,
            'Risk International Travel': None
        }

        self.create_widgets()

    def init_bedrock_runtime(self):
        session = Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            region_name="us-west-2"
        )
        return session.client("bedrock-runtime")

    def create_widgets(self):
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(expand=True, fill="both")

        self.title_label = ttk.Label(frame, text="Travel Audit Assistant", font=("Segoe UI", 16, "bold"))
        self.title_label.pack(pady=(0, 10))

        self.import_btn = ttk.Button(frame, text="📁 Import Excel File", command=self.import_excel)
        self.import_btn.pack(pady=10, fill="x")

        self.file_label = ttk.Label(frame, text="No file selected", foreground="gray")
        self.file_label.pack(pady=(0, 10))

        self.generate_btn = ttk.Button(frame, text="Audit Report", command=self.generate_report)
        self.generate_btn.pack(pady=10, fill="x")
        self.generate_btn.config(state=tk.DISABLED)

        self.status_label = ttk.Label(frame, text="", foreground="green")
        self.status_label.pack(pady=(10, 0))

        # Master report section
        separator = ttk.Separator(frame, orient='horizontal')
        separator.pack(fill='x', pady=10)

        master_label = ttk.Label(frame, text="📊 Create Report", font=('Segoe UI', 12, 'bold'))
        master_label.pack(pady=(0, 10))

        self.upload_files_btn = ttk.Button(frame, text="📁 Select All Files", command=self.upload_master_files)
        self.upload_files_btn.pack(pady=5, fill="x")

        self.files_status_label = ttk.Label(frame, text="Files needed: All 5 files", foreground="orange")
        self.files_status_label.pack(pady=5)

        self.create_master_btn = ttk.Button(frame, text="Create and Audit Report", command=self.create_master_report)
        self.create_master_btn.pack(pady=5, fill="x")
        self.create_master_btn.config(state=tk.DISABLED)

    def import_excel(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if file_path:
            try:
                df = pd.read_excel(file_path)
                self.df_original, self.df_clean = clean_data_sheet(df)
                print("🧩 df_original.columns =", self.df_original.columns.tolist())
                self.excel_path = file_path
                self.file_label.config(text=os.path.basename(file_path), foreground="black")
                self.generate_btn.config(state=tk.NORMAL)
                self.status_label.config(text="✅ Excel file loaded successfully!", foreground="green")
            except Exception as e:
                self.status_label.config(text=f"❌ Failed to load Excel: {e}", foreground="red")

    def generate_report(self):
        try:
            self.status_label.config(text="🔍 Auditing in progress... Please wait.", foreground="blue")
            self.root.update()
            df_flagged = audit_and_flag(self.df_original, self.df_clean, self.bedrock_runtime)
            self.status_label.config(text="✅ Audit complete. Report saved to audit_reports folder.", foreground="green")
        except Exception as e:
            self.status_label.config(text=f"❌ Error during audit: {str(e)}", foreground="red")

    def upload_master_files(self):
        file_paths = filedialog.askopenfilenames(
            title="Select all 5 required files",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )

        if file_paths:
            self.classify_files(file_paths)

        self.update_files_status()

    def classify_files(self, file_paths):
        file_keywords = {
            'Expense Type Detail': ['expense type detail'],
            'EE Active': ['ee active'],
            'CF Information': ['cf information'],
            'Processor Paid Summary': ['processor paid summary'],
            'Risk International Travel': ['risk', 'International', 'Travel']
        }

        for file_path in file_paths:
            filename = os.path.basename(file_path).lower()

            for file_type, keywords in file_keywords.items():
                if any(keyword in filename for keyword in keywords):
                    self.master_files[file_type] = file_path
                    break

    def update_files_status(self):
        uploaded = [k for k, v in self.master_files.items() if v is not None]
        missing = [k for k, v in self.master_files.items() if v is None]

        if len(uploaded) == 5:
            self.files_status_label.config(text="✅ All 5 files uploaded", foreground="green")
            self.create_master_btn.config(state=tk.NORMAL)
        else:
            missing_text = ", ".join(missing)
            self.files_status_label.config(text=f"Missing: {missing_text}", foreground="orange")
            self.create_master_btn.config(state=tk.DISABLED)

    def create_master_report(self):
        try:
            self.status_label.config(text="🔧 Creating master report...", foreground="blue")
            self.root.update()

            # Get the combined DataFrame directly
            merged_df = combine_and_format(
                expense_etd_path=self.master_files['Expense Type Detail'],
                ee_active_path=self.master_files['EE Active'],
                expense_cf_path=self.master_files['CF Information'],
                expense_ppsa_path=self.master_files['Processor Paid Summary'],
                request_rit_path=self.master_files['Risk International Travel']
            )

            self.status_label.config(text="🔍 Master report created. Now auditing...", foreground="blue")
            self.root.update()

            # Audit the DataFrame directly
            df_original, df_clean = clean_data_sheet(merged_df)
            df_flagged = audit_and_flag(df_original, df_clean, self.bedrock_runtime)

            self.status_label.config(text="✅ Master report created and audited in audit_reports folder!",
                                     foreground="green")
        except Exception as e:
            self.status_label.config(text=f"❌ Master report failed: {e}", foreground="red")



import tkinter as tk
from tkinter import ttk
from app import AuditApp  # adjust this path if AuditApp lives elsewhere

if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style(root)
    style.theme_use("clam")
    app = AuditApp(root)
    root.mainloop()















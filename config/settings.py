from pathlib import Path

# Project root (parent of /config)
BASE_DIR = Path(__file__).resolve().parents[1]
REPORTS_DIR = BASE_DIR / "audit_reports"
REPORTS_DIR.mkdir(exist_ok=True)

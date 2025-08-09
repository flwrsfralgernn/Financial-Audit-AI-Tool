from pathlib import Path

# Project root (parent of /config)
BASE_DIR = Path(__file__).resolve().parents[1]
REPORTS_DIR = BASE_DIR / "audit_reports"
REPORTS_DIR.mkdir(exist_ok=True)

POLICIES_DIR = BASE_DIR / "config" / "policies"
POLICIES_DIR.mkdir(exist_ok=True)

# Optional defaults
DEFAULT_POLICY_FILE = POLICIES_DIR / "policy_rules.txt"  # you’ll create this file
MAX_POLICY_CHARS = 12000  # trim to protect token budget

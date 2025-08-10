# services/summary_stats.py
from typing import List
import pandas as pd

DEFAULT_COLS = {
    "employee": ["Employee ID", "EmployeeId", "Employee_Id"],
    "category": ["Expense Type", "Category", "Parent Expense Type", "Expense_Category"],
    "flag":     ["Audit Flag", "Flag"],
    "date": [
        "Transaction Date",
        "Approved Date / Sent for Payment Date",
        "Paid Date",
        "First Submitted Date",
        "Last Submitted Date",
    ],
}

def _pick(df: pd.DataFrame, candidates: List[str]) -> str:
    for c in candidates:
        if c in df.columns:
            return c
    raise KeyError(f"None of {candidates} found. Available: {list(df.columns)}")

# services/summary_stats.py
from collections import Counter
from typing import Dict, List
import pandas as pd

# If you already have resolve_col(), keep using it; otherwise this is a tiny inline version:
def _resolve_col(df: pd.DataFrame, candidates: List[str]):
    cols = list(df.columns)
    norm = {str(c).strip().lower(): c for c in cols}
    for cand in candidates:
        if cand in df.columns:
            return cand
        key = str(cand).strip().lower()
        if key in norm:
            return norm[key]
        for k, orig in norm.items():
            if key in k:   # loose contains
                return orig
    return None



def compute_summary(df_original: pd.DataFrame, df_flagged: pd.DataFrame,
                    colmap: Dict[str, str] = None) -> Dict:
    colmap = colmap or {}
    # Resolve column names from whatever your file actually has (no renaming!)
    emp = colmap.get("employee") or _resolve_col(df_original, DEFAULT_COLS["employee"])
    cat = colmap.get("category") or _resolve_col(df_original, DEFAULT_COLS["category"])
    flag = colmap.get("flag")     or _resolve_col(df_flagged,  DEFAULT_COLS["flag"])
    date = colmap.get("date")     or _resolve_col(df_original, DEFAULT_COLS["date"])

    if emp is None or cat is None or flag is None:
        raise KeyError("Missing required columns among employee/category/flag in provided dataframes.")

    # --- CRITICAL PART: pick only necessary columns to avoid duplicates ---
    left  = df_flagged[["Original Row", flag]].copy()              # only keep the flag from flagged df
    right_cols = ["Original Row", emp, cat] + ([date] if date else [])
    right = df_original[right_cols].copy()

    # Now merge has no overlapping column names except the key, so no _x/_y suffixes
    merged = left.merge(right, on="Original Row", how="left", validate="many_to_one", suffixes=("", ""))

    # Totals
    total_flagged = int((merged[flag] == "Violation").sum() + (merged[flag] == "Exception").sum())
    by_flag = merged[flag].value_counts().to_dict()

    # Violations by category
    viol = merged[merged[flag] == "Violation"]
    by_category = viol[cat].value_counts().to_dict()

    # Monthly trend (optional if a date col exists)
    monthly = {}
    if date:
        months = pd.to_datetime(merged[date], errors="coerce").dt.to_period("M").astype(str)
        monthly = (merged.assign(_Month=months)
                         .loc[merged[flag] == "Violation", "_Month"]
                         .value_counts()
                         .sort_index()
                         .to_dict())

    # Repeat offenders (2+)
    offenders = Counter(viol[emp].dropna().astype(str))
    top10 = dict(sorted(((k, v) for k, v in offenders.items() if v >= 2),
                        key=lambda x: x[1], reverse=True)[:10])

    return {
        "total_flagged": total_flagged,
        "by_flag": by_flag,
        "violations_by_category": by_category,
        "violations_monthly": monthly,       # {} if no usable date column
        "top_repeat_offenders": top10,
    }

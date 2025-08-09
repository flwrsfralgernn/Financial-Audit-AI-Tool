# services/charts.py
from pathlib import Path
from typing import Dict, List
import matplotlib.pyplot as plt

def _save(fig, out_dir: Path, name: str) -> str:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / name
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    return str(path)

def render_summary_charts(summary: Dict, out_dir: str) -> List[str]:
    out_path = Path(out_dir)
    paths: List[str] = []

    # 1) Violations by Category (bar)
    cat_counts = summary.get("violations_by_category", {})
    if cat_counts:
        cats = list(cat_counts.keys())
        vals = list(cat_counts.values())
        fig = plt.figure()
        plt.title("Violations by Category")
        plt.bar(cats, vals)
        plt.xticks(rotation=45, ha="right")
        plt.ylabel("Count")
        paths.append(_save(fig, out_path, "violations_by_category.png"))

    # 2) Monthly Trend of Violations (line)
    monthly = summary.get("violations_monthly", {})
    if monthly:
        months = list(monthly.keys())
        counts = list(monthly.values())
        fig = plt.figure()
        plt.title("Violations Over Time (Monthly)")
        plt.plot(months, counts, marker="o")
        plt.xticks(rotation=45, ha="right")
        plt.ylabel("Count")
        plt.xlabel("Month")
        paths.append(_save(fig, out_path, "violations_trend_monthly.png"))

    # 3) Top 10 Repeat Offenders (bar)
    offenders = summary.get("top_repeat_offenders", {})
    if offenders:
        emps = list(offenders.keys())
        counts = list(offenders.values())
        fig = plt.figure()
        plt.title("Repeat Offenders (Top 10)")
        plt.bar(emps, counts)
        plt.xticks(rotation=45, ha="right")
        plt.ylabel("Violations")
        paths.append(_save(fig, out_path, "repeat_offenders_top10.png"))

    return paths

import os
from services.io_loader import load_excel_file, clean_data_sheet
from services.bedrock_client import init_bedrock_runtime
from services.auditor import run_audit_for_multiple_employees
from services.report_writer import flag_audit_rows, save_to_excel_with_formatting, create_violations_exceptions_report
# from services.summary_stats import compute_summary
# from services.charts import render_summary_charts

def quick_audit_pipeline(excel_path: str, group_count: int = 3):

    # Load + clean
    df_raw = load_excel_file(excel_path)
    df_clean, df_original_view = clean_data_sheet(df_raw)

    # Bedrock
    bedrock = init_bedrock_runtime()
    if not bedrock:
        raise RuntimeError("Bedrock client failed to initialize")

    # Audit
    violation_rows, exception_rows, audit_results = run_audit_for_multiple_employees(
        df_clean, bedrock, group_count=group_count
    )

    # Flag + Save
    df_flagged = flag_audit_rows(df_original_view, df_clean, violation_rows, exception_rows)
    audited_path = save_to_excel_with_formatting(df_flagged)
    create_violations_exceptions_report(df_flagged, audit_results)

    # # Summary + Charts
    # summary = compute_summary(df_original=df_original_view, flags_df=df_flagged)
    # charts = render_summary_charts(summary, out_dir="audit_reports/summary_charts")

    return {
        "audited_excel": audited_path,
        # "charts": charts,
        # "summary": summary,
        "violations": len(df_flagged[df_flagged["Audit Flag"] == "Violation"]),
        "exceptions": len(df_flagged[df_flagged["Audit Flag"] == "Exception"]),
    }

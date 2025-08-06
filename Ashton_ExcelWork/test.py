# === Evaluate Trips ===
results = []

# Get unique Report Keys (preserving original order)
report_keys = df["Report Key"].unique()[:3]  # first 3 keys only

for report_key in tqdm(report_keys, desc="🔍 Evaluating First 3 Trips"):
    trip_df = df[df["Report Key"] == report_key]
    base = trip_df.iloc[0]
    trip_context = {
        "employee": base.get('Employee Name', ''),
        "employee_id": base.get('Employee ID', ''),
        "trip_type": base.get('Trip Type', ''),
        "travel_start": base.get('Travel Start Date', ''),
        "travel_end": base.get('Travel End Date', ''),
        "with_students": base.get('Are you traveling with students/employees?', ''),
        "purpose": base.get('Trip Purpose', ''),
        "expenses": [
            {
                "type": row.get("Expense Type", ""),
                "amount": row.get("Expense Amount (rpt)", 0),
                "transaction_date": row.get("Transaction Date", ""),
                "vendor": row.get("Vendor", ""),
                "mileage_rate": row.get("Mileage Rate", None),
                "is_personal": str(row.get("Is Personal Expense?", "")).lower() in ['yes', 'true']
            }
            for _, row in trip_df.iterrows()
        ]
    }

    try:
        context_json = json.dumps(trip_context, indent=2, default=make_json_safe)
    except Exception as e:
        print(f"❌ JSON serialization error for Report Key {report_key}: {e}")
        continue

    prompt = f"""
You are a university travel compliance officer.

Use the Cal Poly and CSU travel policies from your knowledge base to evaluate this trip and its expenses.

Trip context:
{context_json}

Respond only with a JSON array, and nothing else.

Do NOT include any introduction, markdown, or commentary.

Your output MUST be a valid JSON array where each element includes "Flagged" and "Reason" keys, e.g.:

[
  {{"Flagged": "Yes", "Reason": "Exceeded daily meal limit"}},
  {{"Flagged": "No", "Reason": ""}}
]
"""

    try:
        ai_response = call_knowledge_base(prompt)
        print(f"\nRaw AI response for Report Key {report_key}:\n{ai_response}\n")  # Debug print

        flags = safe_parse_flags(ai_response)
        if flags is None or len(flags) != len(trip_df):
            print(f"⚠️ Parsing failed or length mismatch for Report Key {report_key}")
            with open(current_dir / f"bad_response_{report_key}.txt", "w", encoding="utf-8") as f:
                f.write(ai_response)
            continue

        trip_df.loc[:, "Flagged"] = [f.get("Flagged", "") for f in flags]
        trip_df.loc[:, "Reason"] = [f.get("Reason", "") for f in flags]
        results.append(trip_df)

    except Exception as e:
        print(f"❌ Error on Report Key {report_key}: {e}")
        continue

# === Save Final Output ===
if results:
    final_df = pd.concat(results)
    output_file = current_dir.parent / "flagged_expenses_kb_bedrock_sample.xlsx"
    final_df.to_excel(output_file, index=False)
    print(f"✅ Done. Output saved to {output_file}")
else:
    print("⚠️ No output generated.")

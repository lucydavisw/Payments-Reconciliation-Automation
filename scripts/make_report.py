import json
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

# Paths
BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
OUT = BASE / "outputs"

def main():
    # Load summary.json
    with open(OUT / "summary.json", "r") as f:
        summary = json.load(f)

    # Convert summary to DataFrame for charting
    df = pd.DataFrame([summary])

    # Make chart of exceptions by type (if available)
    exc_series = pd.Series(summary.get("exceptions_by_type", {}))

    chart_note = ""
    if exc_series.sum() > 0:
        exc_df = exc_series.reset_index().rename(
            columns={"index": "exception_type", 0: "count"}
        )
        plt.figure(figsize=(8, 4.5))
        plt.bar(exc_df["exception_type"], exc_df["count"])
        plt.title("Exceptions by Type")
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        plt.savefig(OUT / "exceptions_by_type.png", dpi=150)
        plt.close()
        chart_note = "![Exceptions by type](exceptions_by_type.png)"

    # Markdown report
    md = f"""# Payments Reconciliation – Test Report

## Summary Metrics
- Processor rows: {summary.get("total_processor_rows")}
- Ledger rows: {summary.get("total_ledger_rows")}
- Matched rows: {summary.get("matched_rows")}
- Match rate: {summary.get("match_rate_pct"):.2f}%
- Exceptions: {summary.get("exceptions_rows")}

## Exceptions Breakdown
{chart_note if chart_note else "No exception chart generated."}

## Notes
This test run demonstrates reconciliation between processor and ledger with tolerances.
"""

    with open(OUT / "report.md", "w") as f:
        f.write(md)

    print("Report written ->", OUT / "report.md")


if __name__ == "__main__":
    main()

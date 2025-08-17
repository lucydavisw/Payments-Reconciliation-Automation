import json, sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

OUT = Path("reports"); OUT.mkdir(exist_ok=True, parents=True)

summary = json.loads(Path("outputs/summary.json").read_text())
exceptions = pd.read_csv("outputs/exceptions.csv")

# 1) KPI table (Markdown)
kpi_md = "\n".join([
  "| Metric | Value |",
  "|---|---:|",
  f"| Total processor rows | {summary['total_processor_rows']} |",
  f"| Total ledger rows | {summary['total_ledger_rows']} |",
  f"| Matched rows | {summary['matched_rows']} |",
  f"| Match rate (%) | {summary['match_rate_pct']} |",
  f"| Exceptions rows | {summary['exceptions_rows']} |",
])

# 2) Exception breakdown (top categories)
exc = exceptions["exception_reasons"].fillna("undetermined").str.get_dummies(";").sum().sort_values(ascending=False)
exc = exc[exc>0]
exc_df = exc.reset_index().rename(columns={"index":"exception_type",0:"count"})

# Plot bar chart
plt.figure(figsize=(8,4.5))
exc.plot(kind="bar", x="exception_type", y="count", legend=False, rot=30)
plt.title("Exceptions by Type")
plt.tight_layout()
plt.savefig(OUT/"exceptions_by_type.png", dpi=160)
plt.close()

# Sample rows (first 10)
sample_exc_md = exceptions.head(10).to_markdown(index=False)

# 3) Build report.md
md = f"""# Payments Reconciliation – Test Report

**Objective.** Validate two-pass reconciliation with amount tolerance and date window.  
**Controls.** `amount_tolerance={0.05}`, `date_window={2}` (days).

## 1) KPIs
{kpi_md}

## 2) Exception Breakdown
![chart](exceptions_by_type.png)

Top exception types:

{exc_df.to_markdown(index=False)}

## 3) Sample Exceptions (first 10)
{sample_exc_md}

## 4) Repro Steps
```bash
python scripts/generate_data.py
python scripts/reconcile.py --amount-tolerance 0.05 --date-window 2 --sqlite outputs/recon.db
python scripts/make_report.py


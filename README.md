# Payments Reconciliation Automation (Mini-Project)

This project automates reconciliation between a payment processor feed and an internal ledger, applying configurable tolerances for date and amount differences. It demonstrates the same reconciliation principles used by financial institutions to detect mismatches, duplicates, and exceptions in payment data.

 **Why it matters:** This project simulates reconciliation controls in risk and compliance functions, producing clear exception reports, auditable logs, and a human-readable summary of results.

---

## Features
- **Two-pass reconciliation**
  - **Exact matching** by transaction ID
  - **Heuristic matching** by user + rounded amount + date window
- **Tunable tolerances**  
  - Amount differences allowed (e.g., rounding errors)  
  - Date windows (posting vs settlement delays)
- **Exception tracking**
  - Duplicates on either side
  - Out-of-balance transactions
- **Outputs**
  - CSVs (`matched.csv`, `exceptions.csv`, etc.)
  - SQLite database (`recon.db`) for queries
  - JSON summary (`summary.json`)
  - Markdown report (`report.md`) with optional chart

---

## Project Structure

unit-recon-mini/
├─ scripts/
│ ├─ generate_data.py # creates sample data (processor & ledger)
│ ├─ reconcile.py # runs reconciliation logic & writes outputs
│ └─ make_report.py # builds Markdown report (+ optional chart)
├─ data/
│ ├─ processor_transactions.csv
│ └─ ledger_postings.csv
├─ outputs/
│ ├─ recon.db
│ ├─ summary.json
│ ├─ report.md
│ └─ exceptions_by_type.png (auto-generated if exceptions exist)
├─ requirements.txt
└─ README.md


---

## Setup Instructions
1. Clone the repo and enter the directory:
   ```bash
   git clone https://github.com/<your-username>/unit-recon-mini.git
   cd unit-recon-mini

    Create and activate a virtual environment:

python3 -m venv .venv
source .venv/bin/activate

Install dependencies:

    pip install -r requirements.txt

Usage
1. Generate sample data

python3 scripts/generate_data.py

This creates processor_transactions.csv and ledger_postings.csv in the data/ folder.
2. Run reconciliation

python3 scripts/reconcile.py --amount-tolerance 0.05 --date-window 2 --sqlite outputs/recon.db

This compares both feeds, flags exceptions, and writes CSVs + a database in outputs/.
3. Generate report

python3 scripts/make_report.py

Creates outputs/report.md and, if exceptions exist, a bar chart (exceptions_by_type.png).
Example CLI Variations

# Strict: very tight tolerance
python3 scripts/reconcile.py --amount-tolerance 0.01 --date-window 1

# Loose: allow more room
python3 scripts/reconcile.py --amount-tolerance 0.10 --date-window 3

Outputs

    CSV files

        matched.csv

        exceptions.csv

        unmatched_processor.csv

        unmatched_ledger.csv

    Database

        recon.db (for SQL queries)

    Reports

        summary.json (machine-readable summary)

        report.md (human-readable with KPIs)

        exceptions_by_type.png (if exceptions exist)

Example SQL Checks

Inside SQLite:

.headers on
.mode column

-- Count matched vs exceptions
SELECT (SELECT COUNT(*) FROM matched) AS matched,
       (SELECT COUNT(*) FROM exceptions) AS exceptions;

-- Top 5 exception types
SELECT exception_reasons, COUNT(*) AS n
FROM exceptions
GROUP BY exception_reasons
ORDER BY n DESC
LIMIT 5;


Relevance to Risk/Compliance Roles

    Shows how reconciliation can prevent financial leakage

    Produces exception classes for investigation

    Builds auditable artifacts (database + reports)

    Communicates results with clear visuals and KP

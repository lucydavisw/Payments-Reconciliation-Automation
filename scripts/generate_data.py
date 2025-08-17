import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

np.random.seed(42)
OUT = Path("data"); OUT.mkdir(parents=True, exist_ok=True)

N = 500
start = pd.Timestamp("2025-05-01")
users = [f"U{str(i).zfill(4)}" for i in range(200)]
merchants = ["ACME INC","GLOBEX","WAYNE ENTERPRISES","STARK","HONEYBOOK","WIX","RELAY","BILL.COM"]

def random_date():
    return start + pd.to_timedelta(np.random.randint(0, 60), unit="D")

def gen_processor():
    rows = []
    for i in range(N):
        txn_id = f"T{100000+i}"
        user = np.random.choice(users)
        merchant = np.random.choice(merchants)
        amount = np.round(np.random.uniform(5, 500), 2)
        currency = np.random.choice(["USD"]*95 + ["EUR"]*5)
        created_at = random_date()
        settled_at = created_at + pd.to_timedelta(np.random.randint(0, 3), unit="D")
        rows.append({
            "txn_id": txn_id,
            "user_id": user,
            "merchant": merchant,
            "amount": amount,
            "currency": currency,
            "created_at": created_at,
            "settled_at": settled_at,
            "status": "settled"
        })
    df = pd.DataFrame(rows)

    # Inject issues
    # 2% duplicates
    dups = df.sample(frac=0.02, random_state=7).copy()
    df = pd.concat([df, dups], ignore_index=True)

    # 2% missing in ledger later
    df.loc[df.sample(frac=0.02, random_state=8).index, "status"] = "missing_test_only"

    return df

def gen_ledger(proc: pd.DataFrame):
    # Map most txn_ids -> external_id; post with minor lag
    rows = []
    for _, r in proc.iterrows():
        if r["status"] == "missing_test_only":
            # Simulate never posted in ledger
            continue
        ext = r["txn_id"] if np.random.rand() > 0.03 else f"EXT{r['txn_id']}"  # 3% different external ids
        post_date = pd.to_datetime(r["settled_at"]) + pd.to_timedelta(np.random.randint(0, 2), unit="D")
        amount = r["amount"]
        currency = r["currency"]
        # Amount drift 2%
        if np.random.rand() < 0.02:
            amount = np.round(amount + np.random.choice([-0.03, 0.03, 0.05]), 2)
        # Date drift 3% (push beyond normal window)
        if np.random.rand() < 0.03:
            post_date = post_date + pd.to_timedelta(np.random.randint(3, 6), unit="D")
        rows.append({
            "entry_id": f"L{np.random.randint(1_000_000, 9_999_999)}",
            "external_id": ext,
            "user_id": r["user_id"],
            "amount": amount,
            "currency": currency,
            "posting_date": post_date,
            "account": np.random.choice(["Cash","Clearing","Fees"]),
            "status": "posted"
        })
    df = pd.DataFrame(rows)

    # 1% duplicate postings
    if len(df) > 0:
        dup = df.sample(frac=0.01, random_state=9)
        df = pd.concat([df, dup], ignore_index=True)
    return df

if __name__ == "__main__":
    proc = gen_processor()
    ledg = gen_ledger(proc)

    proc.sort_values("txn_id").to_csv(OUT/"processor_transactions.csv", index=False)
    ledg.sort_values("external_id").to_csv(OUT/"ledger_postings.csv", index=False)
    print("Wrote data/processor_transactions.csv and data/ledger_postings.csv")

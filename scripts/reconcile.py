import argparse, json, sqlite3
from pathlib import Path
import pandas as pd

def load_df(path):
    df = pd.read_csv(path)
    # normalize types
    for c in df.columns:
        lc = c.lower()
        if any(k in lc for k in ["date","created","settled","posting"]):
            df[c] = pd.to_datetime(df[c], errors="coerce")
    if "amount" in df.columns:
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    return df

def run(proc_path, ledg_path, outdir, amt_tol, date_win, sqlite_path=None):
    out = Path(outdir); out.mkdir(parents=True, exist_ok=True)

    proc = load_df(proc_path).rename(columns={"currency":"currency_p","amount":"amount_p"})
    ledg = load_df(ledg_path).rename(columns={"currency":"currency_l","amount":"amount_l"})

    # duplicates
    proc["dup_flag_p"] = proc.duplicated(subset=["txn_id"], keep=False)
    ledg["dup_flag_l"] = ledg.duplicated(subset=["external_id"], keep=False)

    # Pass 1: direct id match
    m = proc.merge(
        ledg, left_on="txn_id", right_on="external_id",
        how="outer", indicator=True, suffixes=("_p","_l")
    )

    # Pass 2: heuristic match for remaining processor rows by (user, rounded amount, currency) within date window
    p_un = m[m["external_id"].isna() & m["txn_id"].notna()][
        ["txn_id","user_id_p","amount_p","currency_p","settled_at"]
    ].copy()
    l_un = m[m["txn_id"].isna() & m["external_id"].notna()][
        ["external_id","user_id_l","amount_l","currency_l","posting_date"]
    ].copy()
    if not p_un.empty and not l_un.empty:
        p_un["amt_round"] = p_un["amount_p"].round(2)
        l_un["amt_round"] = l_un["amount_l"].round(2)
        cand = p_un.merge(
            l_un,
            left_on=["user_id_p","amt_round","currency_p"],
            right_on=["user_id_l","amt_round","currency_l"],
            how="left",
        )
        cand = cand[
            (cand["posting_date"].notna()) &
            ((cand["settled_at"] - cand["posting_date"]).abs().dt.days <= date_win)
        ].drop_duplicates(subset=["txn_id"])
        if not cand.empty:
            m = m.set_index("txn_id")
            for _, r in cand.iterrows():
                if r["txn_id"] in m.index and pd.isna(m.loc[r["txn_id"], "external_id"]):
                    m.loc[r["txn_id"], ["external_id","user_id_l","amount_l","currency_l","posting_date"]] = [
                        r["external_id"], r["user_id_l"], r["amount_l"], r["currency_l"], r["posting_date"]
                    ]
            m = m.reset_index()

    # final match flag
    m["match_flag"] = (
        m["txn_id"].notna() & m["external_id"].notna() &
        (m["currency_p"] == m["currency_l"]) &
        (m["settled_at"].notna() & m["posting_date"].notna()) &
        ((m["settled_at"] - m["posting_date"]).abs().dt.days <= date_win) &
        ((m["amount_p"] - m["amount_l"]).abs() <= amt_tol) &
        (~m["dup_flag_p"].fillna(False)) & (~m["dup_flag_l"].fillna(False))
    )

    matched = m[m["match_flag"]].copy()
    exceptions = m[~m["match_flag"]].copy()

    # splits
    unmatched_processor = exceptions[exceptions["external_id"].isna()]
    unmatched_ledger = exceptions[exceptions["txn_id"].isna()]

    # outputs
    matched.to_csv(out/"matched.csv", index=False)
    exceptions.to_csv(out/"exceptions.csv", index=False)
    unmatched_processor.to_csv(out/"unmatched_processor.csv", index=False)
    unmatched_ledger.to_csv(out/"unmatched_ledger.csv", index=False)

    total_proc = int(m[m["txn_id"].notna()].shape[0])
    summary = {
        "total_processor_rows": total_proc,
        "total_ledger_rows": int(m[m["external_id"].notna()].shape[0]),
        "matched_rows": int(matched.shape[0]),
        "match_rate_pct": round(100*matched.shape[0]/max(1,total_proc),2),
        "exceptions_rows": int(exceptions.shape[0]),
    }
    (out/"summary.json").write_text(json.dumps(summary, indent=2))

    print("\n=== Reconciliation Summary ===")
    for k,v in summary.items():
        print(f"{k}: {v}")

    if sqlite_path:
        con = sqlite3.connect(sqlite_path)
        matched.to_sql("matched", con, if_exists="replace", index=False)
        exceptions.to_sql("exceptions", con, if_exists="replace", index=False)
        unmatched_processor.to_sql("unmatched_processor", con, if_exists="replace", index=False)
        unmatched_ledger.to_sql("unmatched_ledger", con, if_exists="replace", index=False)
        con.close()
        print(f"\nSQLite written -> {sqlite_path}")

def main():
    ap = argparse.ArgumentParser(description="Payments Reconciliation Automation (mini)")
    ap.add_argument("--processor", default="data/processor_transactions.csv")
    ap.add_argument("--ledger", default="data/ledger_postings.csv")
    ap.add_argument("--outdir", default="outputs")
    ap.add_argument("--amount-tolerance", type=float, default=0.05)
    ap.add_argument("--date-window", type=int, default=2)
    ap.add_argument("--sqlite", default="")
    args = ap.parse_args()
    run(
        args.processor, args.ledger, args.outdir,
        amt_tol=args.amount_tolerance, date_win=args.date_window,
        sqlite_path=(args.sqlite or None),
    )

if __name__ == "__main__":
    main()

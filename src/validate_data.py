from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

HISTORY_FILE = ROOT / "data" / "historical.csv"
COMPETITORS_FILE = ROOT / "config" / "competitors.csv"

history = pd.read_csv(HISTORY_FILE)
competitors = pd.read_csv(COMPETITORS_FILE)

print()
print("=" * 70)
print("NBA COMPETITOR TRACKER - DATA VALIDATION")
print("=" * 70)
print()

print("Historical rows:", len(history))
print("Historical accounts:", history["handle"].nunique())
print("Snapshot dates:", history["date"].nunique())

print()
print("Checking aliases...")
print()

if "icntas" in history["handle"].values:
    print("ERROR: icntas still exists in cleaned history")
else:
    print("OK: icntas successfully removed")

if "icn_tasmania" in history["handle"].values:
    count = len(history[history["handle"] == "icn_tasmania"])
    print(f"OK: icn_tasmania exists with {count} historical rows")
else:
    print("ERROR: icn_tasmania missing")

print()
print("Checking anbqldofficial...")

if "anbqldofficial" in history["handle"].values:
    count = len(history[history["handle"] == "anbqldofficial"])
    print(f"OK: anbqldofficial preserved with {count} historical rows")
else:
    print("WARNING: anbqldofficial not found in historical dataset")

print()
print("Latest historical snapshot per account:")
print()

history["date"] = pd.to_datetime(history["date"])

latest = (
    history.sort_values("date")
    .groupby("handle", as_index=False)
    .tail(1)
    .sort_values("followers", ascending=False)
)

for _, row in latest.iterrows():
    followers = int(row["followers"]) if pd.notna(row["followers"]) else 0
    published = int(row["published_content"]) if pd.notna(row["published_content"]) else 0

    print(
        f"{row['handle']:<30} "
        f"{followers:>8,} followers   "
        f"{published:>5,} posts   "
        f"{row['date'].strftime('%Y-%m-%d')}"
    )

print()
print("=" * 70)

tracked = set(
    competitors.loc[
        competitors["active"].str.lower() == "yes",
        "handle"
    ]
)

historical = set(history["handle"])

missing_from_history = sorted(tracked - historical)

if missing_from_history:
    print()
    print("Tracked accounts with no historical records:")
    for handle in missing_from_history:
        print(" -", handle)

print()

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "data" / "instagram_snapshots.csv"

df = pd.read_csv(FILE)

before = len(df)

df["collected_at"] = pd.to_datetime(
    df["collected_at"],
    errors="coerce"
)

# Keep the most recent collection for each account/date.
df = (
    df.sort_values("collected_at")
      .drop_duplicates(
          subset=["date", "handle"],
          keep="last"
      )
)

df.to_csv(FILE, index=False)

after = len(df)

print()
print("=" * 65)
print("SNAPSHOT CLEANUP COMPLETE")
print("=" * 65)
print()
print(f"Rows before: {before}")
print(f"Rows after:  {after}")
print(f"Duplicates removed: {before - after}")
print()

samples = [
    "nbaaustralia_official",
    "icnqld",
    "nabbaaustralia",
    "pca_australia",
]

latest = df[df["handle"].isin(samples)].copy()

latest = (
    latest.sort_values("collected_at")
          .groupby("handle", as_index=False)
          .tail(1)
)

print("Latest values:")
print()

for _, row in latest.iterrows():
    print(
        f"{row['handle']:<28} "
        f"{int(row['followers']):>8,} followers   "
        f"{row.get('follower_precision', '')}"
    )

print()

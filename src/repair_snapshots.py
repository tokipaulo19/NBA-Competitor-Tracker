from pathlib import Path
import csv
import shutil
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]

FILE = ROOT / "data" / "instagram_snapshots.csv"
BACKUP = ROOT / "data" / "instagram_snapshots_before_repair.csv"

NEW_FIELDS = [
    "date",
    "collected_at",
    "handle",
    "followers",
    "follower_precision",
    "follower_source",
    "total_posts",
    "status",
    "source",
    "profile_url",
]


def main():

    if not FILE.exists():
        raise FileNotFoundError(FILE)

    # --------------------------------------------------------
    # Backup first
    # --------------------------------------------------------

    shutil.copy2(FILE, BACKUP)

    print()
    print("Backup created:")
    print(BACKUP)
    print()

    # --------------------------------------------------------
    # Read raw CSV rows
    # --------------------------------------------------------

    with open(
        FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        rows = list(csv.reader(f))

    if not rows:
        raise RuntimeError("Snapshot CSV is empty.")

    old_header = rows[0]

    print("Existing header:")
    print(old_header)
    print()

    repaired = []

    for line_number, row in enumerate(rows[1:], start=2):

        if not row:
            continue

        # ----------------------------------------------------
        # OLD FORMAT: 8 columns
        # ----------------------------------------------------

        if len(row) == 8:

            (
                date,
                collected_at,
                handle,
                followers,
                total_posts,
                status,
                source,
                profile_url,
            ) = row

            repaired.append({
                "date": date,
                "collected_at": collected_at,
                "handle": handle,
                "followers": followers,
                "follower_precision": "",
                "follower_source": "",
                "total_posts": total_posts,
                "status": status,
                "source": source,
                "profile_url": profile_url,
            })

        # ----------------------------------------------------
        # NEW FORMAT: 10 columns
        # ----------------------------------------------------

        elif len(row) == 10:

            repaired.append(
                dict(zip(NEW_FIELDS, row))
            )

        else:

            print(
                f"WARNING: skipped line {line_number} "
                f"because it had {len(row)} columns"
            )

    # --------------------------------------------------------
    # Sort and keep newest row per date/account
    # --------------------------------------------------------

    def timestamp_value(item):

        value = item.get("collected_at", "")

        try:
            return datetime.fromisoformat(value)
        except Exception:
            return datetime.min

    repaired.sort(
        key=lambda x: (
            x.get("date", ""),
            x.get("handle", ""),
            timestamp_value(x)
        )
    )

    latest = {}

    for item in repaired:

        key = (
            item.get("date", ""),
            item.get("handle", "")
        )

        latest[key] = item

    cleaned = list(latest.values())

    cleaned.sort(
        key=lambda x: (
            x.get("date", ""),
            x.get("handle", "")
        )
    )

    # --------------------------------------------------------
    # Rewrite clean CSV
    # --------------------------------------------------------

    with open(
        FILE,
        "w",
        encoding="utf-8",
        newline=""
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=NEW_FIELDS
        )

        writer.writeheader()
        writer.writerows(cleaned)

    print("=" * 70)
    print("SNAPSHOT REPAIR COMPLETE")
    print("=" * 70)
    print()

    print(f"Raw rows found:       {len(rows) - 1}")
    print(f"Rows after cleanup:   {len(cleaned)}")
    print(
        f"Duplicates removed:   "
        f"{len(repaired) - len(cleaned)}"
    )

    print()

    # --------------------------------------------------------
    # Show our key accounts
    # --------------------------------------------------------

    test_handles = {
        "nbaaustralia_official",
        "icnqld",
        "nabbaaustralia",
        "pca_australia",
    }

    print("Latest key account values:")
    print()

    for item in cleaned:

        if item["handle"] not in test_handles:
            continue

        followers = int(item["followers"])

        precision = (
            item["follower_precision"]
            or "legacy"
        )

        follower_source = (
            item["follower_source"]
            or "legacy"
        )

        print(
            f"{item['handle']:<28} "
            f"{followers:>8,} followers   "
            f"{precision:<8} "
            f"{follower_source}"
        )

    print()
    print("Clean file:")
    print(FILE)
    print()


if __name__ == "__main__":
    main()

from pathlib import Path
from datetime import datetime, timedelta
import csv

ROOT = Path(__file__).resolve().parents[1]

SNAPSHOT_FILE = ROOT / "data" / "instagram_snapshots.csv"
HISTORICAL_FILE = ROOT / "data" / "historical.csv"
REPORT_FILE = ROOT / "data" / "weekly_report.csv"

NBA_HANDLE = "nbaaustralia_official"
MIN_GROWTH_DAYS = 30


def to_int(value):
    try:
        if value is None or str(value).strip() == "":
            return None

        return int(
            float(
                str(value)
                .replace(",", "")
                .strip()
            )
        )

    except (ValueError, TypeError):
        return None


def parse_date(value):
    try:
        return datetime.strptime(
            str(value).strip(),
            "%Y-%m-%d"
        ).date()

    except (ValueError, TypeError):
        return None


def load_csv(path):
    if not path.exists():
        return []

    with open(
        path,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        return list(csv.DictReader(file))


def find_field(row, candidates):
    for field in candidates:
        if field in row:
            return field

    return None


def main():

    snapshots = load_csv(
        SNAPSHOT_FILE
    )

    if not snapshots:
        raise RuntimeError(
            "No Instagram snapshots found."
        )

    # ========================================================
    # CURRENT STANDARDIZED SNAPSHOT
    # ========================================================

    snapshot_dates = sorted({
        row["date"]
        for row in snapshots
        if row.get("date")
    })

    current_date_string = snapshot_dates[-1]
    current_date = parse_date(
        current_date_string
    )

    if current_date is None:
        raise RuntimeError(
            "Current snapshot date is invalid."
        )

    current_rows = [
        row
        for row in snapshots
        if row.get("date") == current_date_string
    ]

    current_map = {
        row["handle"]: row
        for row in current_rows
    }

    # ========================================================
    # PREVIOUS STANDARDIZED SNAPSHOT
    # Used ONLY for post activity
    # ========================================================

    previous_standard_date = (
        snapshot_dates[-2]
        if len(snapshot_dates) >= 2
        else None
    )

    previous_standard = {}

    if previous_standard_date:

        previous_standard = {
            row["handle"]: row
            for row in snapshots
            if row.get("date") == previous_standard_date
        }

    # ========================================================
    # BUILD FOLLOWER HISTORY
    #
    # We combine:
    # 1. manually collected historical follower data
    # 2. standardized automated snapshots
    #
    # Then choose a comparison observation that is
    # AT LEAST 30 DAYS OLD.
    # ========================================================

    follower_history = {}

    def add_observation(
        handle,
        date_value,
        followers,
        source
    ):

        date_obj = parse_date(
            date_value
        )

        follower_count = to_int(
            followers
        )

        if (
            not handle
            or date_obj is None
            or follower_count is None
        ):
            return

        follower_history.setdefault(
            handle,
            []
        ).append({
            "date": date_obj,
            "followers": follower_count,
            "source": source,
        })

    # --------------------------------------------------------
    # Historical manually collected data
    # --------------------------------------------------------

    historical_rows = load_csv(
        HISTORICAL_FILE
    )

    if historical_rows:

        sample = historical_rows[0]

        historical_date_field = find_field(
            sample,
            [
                "date",
                "snapshot_date"
            ]
        )

        historical_handle_field = find_field(
            sample,
            [
                "handle",
                "account",
                "username"
            ]
        )

        historical_follower_field = find_field(
            sample,
            [
                "followers",
                "follower_count",
                "followers_count"
            ]
        )

        if (
            historical_date_field
            and historical_handle_field
            and historical_follower_field
        ):

            for row in historical_rows:

                add_observation(
                    row.get(
                        historical_handle_field,
                        ""
                    ).strip(),
                    row.get(
                        historical_date_field,
                        ""
                    ),
                    row.get(
                        historical_follower_field
                    ),
                    "historical"
                )

    # --------------------------------------------------------
    # Automated snapshots
    # --------------------------------------------------------

    for row in snapshots:

        # Current observation does not need to be
        # considered as historical comparison data.
        if row.get("date") == current_date_string:
            continue

        add_observation(
            row.get(
                "handle",
                ""
            ).strip(),
            row.get(
                "date",
                ""
            ),
            row.get(
                "followers"
            ),
            "instagram_snapshot"
        )

    for handle in follower_history:

        follower_history[handle].sort(
            key=lambda item: item["date"]
        )

    # ========================================================
    # 30-DAY TARGET
    # ========================================================

    target_date = (
        current_date
        - timedelta(
            days=MIN_GROWTH_DAYS
        )
    )

    # ========================================================
    # NBA CURRENT DATA
    # ========================================================

    nba_row = current_map.get(
        NBA_HANDLE
    )

    if not nba_row:
        raise RuntimeError(
            f"NBA account @{NBA_HANDLE} "
            "is missing from current snapshot."
        )

    nba_followers = to_int(
        nba_row.get(
            "followers"
        )
    )

    if nba_followers is None:
        raise RuntimeError(
            "NBA follower count is missing."
        )

    # ========================================================
    # CURRENT FOLLOWER RANKING
    # ========================================================

    ranked = sorted(
        current_rows,
        key=lambda row: (
            to_int(
                row.get("followers")
            )
            or -1
        ),
        reverse=True
    )

    rank_lookup = {
        row["handle"]: index
        for index, row in enumerate(
            ranked,
            start=1
        )
    }

    accounts_ahead = sum(
        1
        for row in current_rows
        if (
            to_int(
                row.get("followers")
            )
            or 0
        ) > nba_followers
    )

    # ========================================================
    # GENERATE REPORT
    # ========================================================

    report_rows = []

    for row in ranked:

        handle = row["handle"]

        current_followers = to_int(
            row.get(
                "followers"
            )
        )

        current_posts = to_int(
            row.get(
                "total_posts"
            )
        )

        # ----------------------------------------------------
        # AT LEAST 30-DAY FOLLOWER COMPARISON
        # ----------------------------------------------------

        comparison = None

        candidates = [
            observation
            for observation in follower_history.get(
                handle,
                []
            )
            if observation["date"] <= target_date
        ]

        if candidates:

            # Choose the newest observation that is
            # still at least 30 days old.
            comparison = candidates[-1]

        previous_followers = None
        comparison_date = None
        comparison_days = None
        comparison_source = None

        follower_change = None
        growth_percent = None

        if comparison:

            previous_followers = comparison[
                "followers"
            ]

            comparison_date = comparison[
                "date"
            ]

            comparison_source = comparison[
                "source"
            ]

            comparison_days = (
                current_date
                - comparison_date
            ).days

            if (
                current_followers is not None
                and previous_followers is not None
            ):

                follower_change = (
                    current_followers
                    - previous_followers
                )

                if previous_followers != 0:

                    growth_percent = round(
                        (
                            follower_change
                            / previous_followers
                        )
                        * 100,
                        2
                    )

        # ----------------------------------------------------
        # POSTS SINCE PREVIOUS AUTOMATED SNAPSHOT
        # ----------------------------------------------------

        previous_posts = None
        posts_published = None

        if handle in previous_standard:

            previous_posts = to_int(
                previous_standard[
                    handle
                ].get(
                    "total_posts"
                )
            )

        if (
            current_posts is not None
            and previous_posts is not None
        ):

            difference = (
                current_posts
                - previous_posts
            )

            if difference >= 0:
                posts_published = difference

        report_rows.append({
            "date": current_date_string,

            "rank": rank_lookup[
                handle
            ],

            "handle": handle,

            "current_followers": (
                current_followers
                if current_followers is not None
                else ""
            ),

            "comparison_followers": (
                previous_followers
                if previous_followers is not None
                else ""
            ),

            "follower_change_30d_plus": (
                follower_change
                if follower_change is not None
                else ""
            ),

            "growth_percent_30d_plus": (
                growth_percent
                if growth_percent is not None
                else ""
            ),

            "comparison_date": (
                comparison_date.isoformat()
                if comparison_date
                else ""
            ),

            "comparison_days": (
                comparison_days
                if comparison_days is not None
                else ""
            ),

            "comparison_source": (
                comparison_source
                or ""
            ),

            "current_total_posts": (
                current_posts
                if current_posts is not None
                else ""
            ),

            "posts_since_previous_snapshot": (
                posts_published
                if posts_published is not None
                else ""
            ),

            "previous_post_snapshot_date": (
                previous_standard_date
                or ""
            ),

            "ahead_of_nba": (
                "yes"
                if (
                    current_followers is not None
                    and current_followers > nba_followers
                )
                else "no"
            ),
        })

    # ========================================================
    # EXPORT CSV
    # ========================================================

    fields = [
        "date",
        "rank",
        "handle",
        "current_followers",
        "comparison_followers",
        "follower_change_30d_plus",
        "growth_percent_30d_plus",
        "comparison_date",
        "comparison_days",
        "comparison_source",
        "current_total_posts",
        "posts_since_previous_snapshot",
        "previous_post_snapshot_date",
        "ahead_of_nba",
    ]

    with open(
        REPORT_FILE,
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields
        )

        writer.writeheader()

        writer.writerows(
            report_rows
        )

    # ========================================================
    # CONSOLE SUMMARY
    # ========================================================

    print()
    print("=" * 78)
    print("NBA 30-DAY+ COMPETITOR GROWTH REPORT")
    print("=" * 78)

    print()
    print(
        f"Current snapshot:     "
        f"{current_date_string}"
    )

    print(
        f"30-day target date:   "
        f"{target_date.isoformat()}"
    )

    print(
        f"NBA followers:        "
        f"{nba_followers:,}"
    )

    print(
        f"NBA follower rank:    "
        f"{rank_lookup[NBA_HANDLE]} "
        f"of {len(current_rows)}"
    )

    print(
        f"Accounts ahead NBA:   "
        f"{accounts_ahead}"
    )

    nba_report = next(
        item
        for item in report_rows
        if item["handle"] == NBA_HANDLE
    )

    print()

    if (
        nba_report[
            "follower_change_30d_plus"
        ] != ""
    ):

        change = nba_report[
            "follower_change_30d_plus"
        ]

        sign = (
            "+"
            if change >= 0
            else ""
        )

        print(
            f"NBA comparison:       "
            f"{nba_report['comparison_date']} "
            f"→ {current_date_string}"
        )

        print(
            f"Comparison period:    "
            f"{nba_report['comparison_days']} days"
        )

        print(
            f"NBA follower change:  "
            f"{sign}{change:,}"
        )

        print(
            f"NBA growth:           "
            f"{nba_report['growth_percent_30d_plus']}%"
        )

    else:

        print(
            "NBA 30-day growth:    "
            "Not enough historical data"
        )

    # --------------------------------------------------------
    # Top follower ranking
    # --------------------------------------------------------

    print()
    print("TOP 5 BY FOLLOWERS")
    print("-" * 78)

    for item in report_rows[:5]:

        print(
            f"{item['rank']:>2}. "
            f"@{item['handle']:<27} "
            f"{item['current_followers']:>8,}"
        )

    # --------------------------------------------------------
    # Fastest 30-day+ growth
    # --------------------------------------------------------

    growth_available = [
        item
        for item in report_rows
        if item[
            "growth_percent_30d_plus"
        ] != ""
    ]

    growth_available.sort(
        key=lambda item: item[
            "growth_percent_30d_plus"
        ],
        reverse=True
    )

    if growth_available:

        print()
        print("FASTEST 30-DAY+ FOLLOWER GROWTH")
        print("-" * 78)

        for item in growth_available[:5]:

            change = item[
                "follower_change_30d_plus"
            ]

            sign = (
                "+"
                if change >= 0
                else ""
            )

            print(
                f"@{item['handle']:<27} "
                f"{sign}{change:>6,}  "
                f"({item['growth_percent_30d_plus']}%)  "
                f"{item['comparison_days']}d"
            )

    print()
    print("Report saved:")
    print(REPORT_FILE)
    print()


if __name__ == "__main__":
    main()

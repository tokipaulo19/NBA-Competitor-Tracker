from pathlib import Path
from datetime import datetime
import argparse
import csv
import random
import re
import shutil
import sys
import time

from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError
)

ROOT = Path(__file__).resolve().parents[1]

COMPETITORS_FILE = ROOT / "config" / "competitors.csv"
SNAPSHOT_FILE = ROOT / "data" / "instagram_snapshots.csv"
ERROR_FILE = ROOT / "data" / "profile_validation_errors.csv"

SNAPSHOT_FIELDS = [
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


def clean_number(value):
    if not value:
        return None

    value = (
        str(value)
        .strip()
        .replace(",", "")
        .replace(" ", "")
    )

    multiplier = 1

    if value.lower().endswith("k"):
        multiplier = 1_000
        value = value[:-1]

    elif value.lower().endswith("m"):
        multiplier = 1_000_000
        value = value[:-1]

    try:
        return round(float(value) * multiplier)
    except ValueError:
        return None


def extract_metric(text, metric):
    if not text:
        return None

    patterns = [
        rf"([\d,.]+[KkMm]?)\s+{metric}",
        rf"([\d,.]+[KkMm]?)\s+{metric.capitalize()}",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            return clean_number(match.group(1))

    return None


def find_exact_followers_in_text(text):
    if not text:
        return None

    patterns = [
        r'"edge_followed_by"\s*:\s*\{\s*"count"\s*:\s*(\d+)',
        r'"follower_count"\s*:\s*(\d+)',
        r'"followers_count"\s*:\s*(\d+)',
        r'"followers"\s*:\s*\{\s*"count"\s*:\s*(\d+)',
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:
            return int(match.group(1))

    return None


def load_profiles():
    profiles = []

    with open(
        COMPETITORS_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            if row.get("active", "").strip().lower() != "yes":
                continue

            handle = row.get("handle", "").strip()

            if not handle:
                continue

            url = row.get("profile_url", "").strip()

            if not url:
                url = f"https://www.instagram.com/{handle}/"

            row["profile_url"] = url
            profiles.append(row)

    return profiles


def meta_content(page, selector):
    try:
        locator = page.locator(selector)

        if locator.count():
            return locator.first.get_attribute("content") or ""

    except Exception:
        pass

    return ""


def inspect_profile(page, profile):
    handle = profile["handle"]
    url = profile["profile_url"]

    result = {
        "handle": handle,
        "name": profile.get("name", ""),
        "group": profile.get("group", ""),
        "profile_url": url,
        "followers": None,
        "follower_precision": None,
        "follower_source": None,
        "total_posts": None,
        "status": "failed",
        "reason": "",
    }

    try:
        response = page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=30000,
        )

    except PlaywrightTimeoutError:
        result["reason"] = "Page load timed out"
        return result

    except Exception as exc:
        result["reason"] = f"Browser error: {exc}"
        return result

    page.wait_for_timeout(2500)

    current_url = page.url.lower()

    if "/accounts/login" in current_url:
        result["reason"] = "Instagram redirected to login"
        return result

    if response and response.status >= 400:
        result["reason"] = f"HTTP {response.status}"
        return result

    try:
        body = page.locator("body").inner_text(
            timeout=5000
        )
    except Exception:
        body = ""

    lower_body = body.lower()

    unavailable_phrases = [
        "sorry, this page isn't available",
        "page isn't available",
        "the link you followed may be broken",
        "user not found",
    ]

    for phrase in unavailable_phrases:
        if phrase in lower_body:
            result["reason"] = "Profile unavailable"
            return result

    sources = []

    description = meta_content(
        page,
        'meta[name="description"]'
    )

    og_description = meta_content(
        page,
        'meta[property="og:description"]'
    )

    if description:
        sources.append(description)

    if og_description:
        sources.append(og_description)

    if body:
        sources.append(body)

    combined = "\n".join(sources)

    html = page.content()

    exact_followers = find_exact_followers_in_text(
        html
    )

    if exact_followers is not None:

        followers = exact_followers
        precision = "exact"
        follower_source = "page_html"

    else:

        followers = extract_metric(
            combined,
            "followers"
        )

        precision = None
        follower_source = "visible_profile"

        follower_match = re.search(
            r"([\d,.]+[KkMm]?)\s+[Ff]ollowers",
            combined
        )

        if follower_match:

            raw_follower_value = follower_match.group(1)

            if raw_follower_value.lower().endswith(("k", "m")):
                precision = "rounded"
            else:
                precision = "exact"

    posts = extract_metric(
        combined,
        "posts"
    )

    if followers is None:
        result["reason"] = (
            "Profile opened but follower count "
            "could not be extracted"
        )
        return result

    result["followers"] = followers
    result["follower_precision"] = precision
    result["follower_source"] = follower_source
    result["total_posts"] = posts
    result["status"] = "ok"
    result["reason"] = "Profile validated"

    return result


def collect_with_retry(page, profile):
    result = inspect_profile(
        page,
        profile
    )

    if result["status"] == "ok":
        return result

    print(
        f"      First attempt failed: "
        f"{result['reason']}"
    )

    print("      Retrying once...")

    time.sleep(3)

    return inspect_profile(
        page,
        profile
    )


def save_error_report(errors):
    ERROR_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    fields = [
        "handle",
        "name",
        "profile_url",
        "reason"
    ]

    with open(
        ERROR_FILE,
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields
        )

        writer.writeheader()

        for item in errors:
            writer.writerow({
                field: item.get(field, "")
                for field in fields
            })


def migrate_snapshot_schema():
    if not SNAPSHOT_FILE.exists():
        return

    with open(
        SNAPSHOT_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.reader(file)
        rows = list(reader)

    if not rows:
        return

    current_header = rows[0]

    if current_header == SNAPSHOT_FIELDS:
        return

    print()
    print("Snapshot schema update required.")
    print("Migrating existing snapshot file...")

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup = (
        ROOT
        / "data"
        / f"instagram_snapshots_schema_backup_{timestamp}.csv"
    )

    shutil.copy2(
        SNAPSHOT_FILE,
        backup
    )

    print(f"Backup created: {backup}")

    migrated = []

    for line_number, row in enumerate(
        rows[1:],
        start=2
    ):

        if not row:
            continue

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

            migrated.append({
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

        elif len(row) == 10:

            migrated.append(
                dict(zip(SNAPSHOT_FIELDS, row))
            )

        else:

            raise RuntimeError(
                f"Cannot safely migrate line {line_number}: "
                f"found {len(row)} columns."
            )

    temp_file = SNAPSHOT_FILE.with_suffix(
        ".migration.tmp"
    )

    with open(
        temp_file,
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=SNAPSHOT_FIELDS
        )

        writer.writeheader()
        writer.writerows(migrated)

    temp_file.replace(
        SNAPSHOT_FILE
    )

    print("Snapshot schema migration complete.")
    print()


def get_rows_for_date(date_string):
    if not SNAPSHOT_FILE.exists():
        return []

    with open(
        SNAPSHOT_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        return [
            row
            for row in reader
            if row.get("date") == date_string
        ]


def remove_date_snapshot(date_string):
    if not SNAPSHOT_FILE.exists():
        return

    with open(
        SNAPSHOT_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        rows = list(
            csv.DictReader(file)
        )

    kept = [
        row
        for row in rows
        if row.get("date") != date_string
    ]

    with open(
        SNAPSHOT_FILE,
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=SNAPSHOT_FIELDS
        )

        writer.writeheader()
        writer.writerows(kept)


def ask_existing_snapshot_action(date_string):
    while True:

        answer = input(
            f"\nA snapshot already exists for {date_string}.\n"
            "[R] Replace today's snapshot\n"
            "[C] Cancel\n"
            "Choose R or C: "
        ).strip().lower()

        if answer in ("r", "replace"):
            return "replace"

        if answer in ("c", "cancel"):
            return "cancel"

        print("Please enter R or C.")


def save_snapshot(results, date_string):
    SNAPSHOT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    exists = SNAPSHOT_FILE.exists()

    timestamp = datetime.now().isoformat(
        timespec="seconds"
    )

    with open(
        SNAPSHOT_FILE,
        "a",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=SNAPSHOT_FIELDS
        )

        if not exists:
            writer.writeheader()

        for result in results:

            if result["status"] != "ok":
                continue

            writer.writerow({
                "date": date_string,
                "collected_at": timestamp,
                "handle": result["handle"],
                "followers": result["followers"],
                "follower_precision": result["follower_precision"],
                "follower_source": result["follower_source"],
                "total_posts": result["total_posts"],
                "status": "ok",
                "source": "instagram_public_profile",
                "profile_url": result["profile_url"],
            })


def ask_continue():
    while True:

        answer = input(
            "\nProceed despite these errors? [Y/N]: "
        ).strip().lower()

        if answer in ("y", "yes"):
            return True

        if answer in ("n", "no"):
            return False

        print("Please enter Y or N.")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mode",
        choices=[
            "interactive",
            "strict",
            "continue"
        ],
        default="interactive",
    )

    parser.add_argument(
        "--headed",
        action="store_true",
    )

    args = parser.parse_args()

    try:
        migrate_snapshot_schema()

    except Exception as exc:

        print()
        print("SNAPSHOT MIGRATION FAILED")
        print(str(exc))
        print()
        print("No new data was written.")

        return 4

    profiles = load_profiles()

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    print()
    print("=" * 78)
    print("NBA COMPETITOR TRACKER")
    print("INSTAGRAM WEEKLY COLLECTION")
    print("=" * 78)

    print()
    print(f"Date: {today}")
    print(f"Mode: {args.mode}")
    print(f"Profiles: {len(profiles)}")
    print()

    existing_rows = get_rows_for_date(
        today
    )

    if existing_rows:

        if args.mode == "strict":

            print(
                f"A snapshot already exists for {today}."
            )

            print(
                "STRICT MODE: Run cancelled."
            )

            return 3

        if args.mode == "interactive":

            action = ask_existing_snapshot_action(
                today
            )

            if action == "cancel":

                print()
                print("Run cancelled.")

                return 3

            if action == "replace":

                print()
                print(
                    "Existing snapshot will be replaced "
                    "only after the new collection validates."
                )

    results = []

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=not args.headed
        )

        context = browser.new_context(
            viewport={
                "width": 1440,
                "height": 1000,
            },
            locale="en-US",
        )

        page = context.new_page()

        for index, profile in enumerate(
            profiles,
            start=1
        ):

            print(
                f"[{index:02}/{len(profiles)}] "
                f"Checking @{profile['handle']}..."
            )

            result = collect_with_retry(
                page,
                profile
            )

            results.append(result)

            if result["status"] == "ok":

                followers = (
                    f"{result['followers']:,}"
                    if result["followers"] is not None
                    else "N/A"
                )

                posts = (
                    f"{result['total_posts']:,}"
                    if result["total_posts"] is not None
                    else "N/A"
                )

                precision = (
                    result["follower_precision"]
                    or "unknown"
                )

                print(
                    f"      OK | "
                    f"{followers} followers | "
                    f"{posts} total posts | "
                    f"{precision}"
                )

            else:

                print(
                    f"      FAILED | "
                    f"{result['reason']}"
                )

            time.sleep(
                random.uniform(
                    1.5,
                    3.0
                )
            )

        browser.close()

    failures = [
        item
        for item in results
        if item["status"] != "ok"
    ]

    print()
    print("=" * 78)
    print("VALIDATION SUMMARY")
    print("=" * 78)
    print()

    print(
        f"Successful: "
        f"{len(results) - len(failures)}"
    )

    print(
        f"Failed:     "
        f"{len(failures)}"
    )

    if failures:

        print()
        print("FAILED PROFILES")
        print("-" * 78)

        for failure in failures:

            print(
                f"@{failure['handle']:<25} "
                f"{failure['reason']}"
            )

        save_error_report(failures)

        print()
        print("Error report:")
        print(ERROR_FILE)

        if args.mode == "strict":

            print()
            print("STRICT MODE:")
            print("Snapshot cancelled.")
            print("NO DATA WAS EXPORTED.")

            return 2

        if args.mode == "interactive":

            if not ask_continue():

                print()
                print("Run cancelled.")
                print("NO DATA WAS EXPORTED.")

                return 2

    if existing_rows:
        remove_date_snapshot(
            today
        )

    print()
    print("Saving snapshot...")

    save_snapshot(
        results,
        today
    )

    print()
    print("=" * 78)
    print("COLLECTION COMPLETE")
    print("=" * 78)

    print()
    print("Snapshot saved to:")
    print(SNAPSHOT_FILE)

    print()

    print(
        f"Profiles exported: "
        f"{len(results) - len(failures)}"
    )

    if failures:

        print(
            f"Profiles omitted:  "
            f"{len(failures)}"
        )

    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())

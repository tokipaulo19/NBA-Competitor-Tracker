from pathlib import Path
from datetime import datetime
import argparse
import csv
import json
import os
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]

COMPETITORS_FILE = ROOT / "config" / "competitors.csv"
SNAPSHOT_FILE = ROOT / "data" / "instagram_snapshots.csv"
ERROR_FILE = ROOT / "data" / "profile_validation_errors.csv"

APIFY_ACTOR = "apify~instagram-scraper"
APIFY_PROFILE_ACTOR = "apify~instagram-profile-scraper"

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

            profile_url = row.get("profile_url", "").strip()

            if not profile_url:
                profile_url = (
                    f"https://www.instagram.com/{handle}/"
                )

            row["profile_url"] = profile_url

            profiles.append(row)

    return profiles


def normalize_handle(value):
    if value is None:
        return ""

    return (
        str(value)
        .strip()
        .lower()
        .lstrip("@")
    )


def run_apify(profiles, token):
    url = (
        f"https://api.apify.com/v2/actors/"
        f"{APIFY_ACTOR}/run-sync-get-dataset-items"
    )

    payload = {
        "directUrls": [
            profile["profile_url"]
            for profile in profiles
        ],
        "resultsType": "details",
        "resultsLimit": 1,
    }

    body = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        url=url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=300
        ) as response:

            raw = response.read().decode("utf-8")

    except urllib.error.HTTPError as exc:

        error_body = (
            exc.read().decode("utf-8", errors="replace")
        )

        raise RuntimeError(
            f"Apify API returned HTTP {exc.code}: "
            f"{error_body}"
        )

    except urllib.error.URLError as exc:

        raise RuntimeError(
            f"Could not reach Apify API: {exc}"
        )

    except TimeoutError:

        raise RuntimeError(
            "Apify request timed out."
        )

    try:
        data = json.loads(raw)

    except json.JSONDecodeError:

        raise RuntimeError(
            "Apify returned invalid JSON."
        )

    if not isinstance(data, list):
        raise RuntimeError(
            f"Unexpected Apify response: {data}"
        )

    return data


def detect_username(item):
    candidates = [
        item.get("username"),
        item.get("userName"),
        item.get("ownerUsername"),
    ]

    for value in candidates:

        handle = normalize_handle(value)

        if handle:
            return handle

    input_url = (
        item.get("inputUrl")
        or item.get("url")
        or ""
    )

    if "instagram.com/" in input_url:

        try:
            part = (
                input_url
                .split("instagram.com/", 1)[1]
                .split("?", 1)[0]
                .strip("/")
                .split("/", 1)[0]
            )

            return normalize_handle(part)

        except Exception:
            pass

    return ""


def get_followers(item):
    candidates = [
        "followersCount",
        "followerCount",
        "followers",
    ]

    for field in candidates:

        value = item.get(field)

        if value is not None:

            try:
                return int(value)
            except (ValueError, TypeError):
                pass

    return None


def get_posts(item):
    candidates = [
        "postsCount",
        "mediaCount",
        "posts",
    ]

    for field in candidates:

        value = item.get(field)

        if value is not None:

            try:
                return int(value)
            except (ValueError, TypeError):
                pass

    return None




def get_missing_post_counts(handles, token):
    """
    Use Apify's dedicated Instagram Profile Scraper only for
    profiles where the primary scraper did not return postsCount.
    """

    if not handles:
        return {}

    url = (
        f"https://api.apify.com/v2/actors/"
        f"{APIFY_PROFILE_ACTOR}/run-sync-get-dataset-items"
    )

    payload = {
        "usernames": handles,
        "includeAboutSection": False,
    }

    request = urllib.request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=300
        ) as response:

            raw = response.read().decode("utf-8")

    except Exception as exc:

        print()
        print(
            "WARNING: Post-count fallback request failed:"
        )

        print(str(exc))

        return {}

    try:
        items = json.loads(raw)
    except json.JSONDecodeError:
        return {}

    if not isinstance(items, list):
        return {}

    results = {}

    for item in items:

        handle = detect_username(item)

        if not handle:
            continue

        post_count = get_posts(item)

        if post_count is not None:
            results[handle] = post_count

    return results

def save_error_report(errors):
    ERROR_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    fields = [
        "date_checked",
        "handle",
        "name",
        "profile_url",
        "reason",
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

        for error in errors:

            row = {
                field: error.get(field, "")
                for field in fields
            }

            row["date_checked"] = datetime.now().strftime("%Y-%m-%d")

            writer.writerow(row)


def get_existing_rows():
    if not SNAPSHOT_FILE.exists():
        return []

    with open(
        SNAPSHOT_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        return list(
            csv.DictReader(file)
        )


def snapshot_exists(date_string):
    return any(
        row.get("date") == date_string
        for row in get_existing_rows()
    )


def remove_snapshot_date(date_string):
    rows = get_existing_rows()

    rows = [
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

        for row in rows:

            normalized = {
                field: row.get(field, "")
                for field in SNAPSHOT_FIELDS
            }

            writer.writerow(normalized)


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

            writer.writerow({
                "date": date_string,
                "collected_at": timestamp,
                "handle": result["handle"],
                "followers": result["followers"],
                "follower_precision": "exact",
                "follower_source": "apify",
                "total_posts": (
                    result["total_posts"]
                    if result["total_posts"] is not None
                    else ""
                ),
                "status": "ok",
                "source": "apify_instagram_scraper",
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
            "continue",
        ],
        default="interactive",
    )

    parser.add_argument(
        "--replace-existing",
        action="store_true",
    )

    args = parser.parse_args()

    token = os.environ.get(
        "APIFY_TOKEN",
        ""
    ).strip()

    if not token:

        print()
        print(
            "ERROR: APIFY_TOKEN environment "
            "variable is missing."
        )

        return 5

    profiles = load_profiles()

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    print()
    print("=" * 78)
    print("NBA COMPETITOR TRACKER")
    print("APIFY INSTAGRAM COLLECTION")
    print("=" * 78)
    print()

    print(f"Date:     {today}")
    print(f"Mode:     {args.mode}")
    print(f"Profiles: {len(profiles)}")
    print()

    if snapshot_exists(today):

        if args.replace_existing:

            print(
                "A snapshot already exists for today."
            )

            print(
                "Replacement requested. Existing data "
                "will only be removed after validation."
            )

        elif args.mode == "strict":

            print(
                "A snapshot already exists for today."
            )

            print(
                "STRICT MODE: Run cancelled."
            )

            return 3

        else:

            print(
                "A snapshot already exists for today."
            )

            print(
                "Run with --replace-existing if you "
                "want to replace it."
            )

            return 3

    print(
        "Sending profile list to Apify..."
    )

    try:
        items = run_apify(
            profiles,
            token
        )

    except Exception as exc:

        print()
        print("APIFY RUN FAILED")
        print(str(exc))
        print()

        return 6

    print(
        f"Apify returned {len(items)} result(s)."
    )

    by_handle = {}

    for item in items:

        handle = detect_username(item)

        if handle:
            by_handle[handle] = item

    successful = []
    failures = []

    primary_results = {}

    for item in items:

        handle = detect_username(item)

        if handle:
            primary_results[handle] = item


    missing_post_handles = []

    for profile in profiles:

        handle = normalize_handle(
            profile["handle"]
        )

        item = primary_results.get(handle)

        if item is None:
            continue

        if get_followers(item) is None:
            continue

        if get_posts(item) is None:
            missing_post_handles.append(handle)


    post_fallbacks = {}

    if missing_post_handles:

        print()
        print(
            "Post count missing for "
            f"{len(missing_post_handles)} profile(s)."
        )

        print(
            "Running profile-detail fallback..."
        )

        post_fallbacks = get_missing_post_counts(
            missing_post_handles,
            token
        )


    print()
    print("PROFILE RESULTS")
    print("-" * 78)

    for profile in profiles:

        handle = normalize_handle(
            profile["handle"]
        )

        item = by_handle.get(handle)

        if item is None:

            failure = {
                "handle": handle,
                "name": profile.get("name", ""),
                "profile_url": profile["profile_url"],
                "reason": (
                    "No profile result returned by Apify. "
                    "Profile may be unavailable, renamed, "
                    "or could not be scraped."
                ),
            }

            failures.append(failure)

            print(
                f"[FAIL] @{handle:<27} "
                f"No Apify result"
            )

            continue

        followers = get_followers(item)

        if followers is None:

            failure = {
                "handle": handle,
                "name": profile.get("name", ""),
                "profile_url": profile["profile_url"],
                "reason": (
                    "Profile returned but follower count "
                    "was missing."
                ),
            }

            failures.append(failure)

            print(
                f"[FAIL] @{handle:<27} "
                f"Follower count missing"
            )

            continue

        posts = get_posts(item)

        post_source = "primary"

        if posts is None:

            posts = post_fallbacks.get(handle)

            if posts is not None:
                post_source = "profile_fallback"
            else:
                post_source = "missing"

        result = {
            "handle": handle,
            "followers": followers,
            "total_posts": posts,
            "profile_url": profile["profile_url"],
        }

        successful.append(result)

        posts_display = (
            f"{posts:,}"
            if posts is not None
            else "N/A"
        )

        print(
            f"[OK]   @{handle:<27} "
            f"{followers:>8,} followers | "
            f"{posts_display} posts"
        )

    print()
    print("=" * 78)
    print("VALIDATION SUMMARY")
    print("=" * 78)
    print()

    print(
        f"Successful: {len(successful)}"
    )

    print(
        f"Failed:     {len(failures)}"
    )

    if len(successful) == 0:

        if failures:
            save_error_report(failures)

        print()
        print("CRITICAL ERROR:")
        print("All profiles failed.")
        print("No snapshot will be exported.")
        print()

        return 7

    if failures:

        save_error_report(
            failures
        )

    elif ERROR_FILE.exists():

        ERROR_FILE.unlink()

        print()
        print(
            "No current profile errors. "
            "Previous error report removed."
        )

        print()
        print("FAILED PROFILES")
        print("-" * 78)

        for failure in failures:

            print(
                f"@{failure['handle']:<28} "
                f"{failure['reason']}"
            )

        print()
        print("Error report:")
        print(ERROR_FILE)

        if args.mode == "strict":

            print()
            print(
                "STRICT MODE: Snapshot cancelled."
            )

            print(
                "NO DATA WAS EXPORTED."
            )

            return 2

        if args.mode == "interactive":

            if not ask_continue():

                print()
                print(
                    "Run cancelled."
                )

                print(
                    "NO DATA WAS EXPORTED."
                )

                return 2

    if snapshot_exists(today):

        remove_snapshot_date(
            today
        )

    save_snapshot(
        successful,
        today
    )

    print()
    print("=" * 78)
    print("COLLECTION COMPLETE")
    print("=" * 78)
    print()

    print(
        f"Profiles exported: {len(successful)}"
    )

    if failures:

        print(
            f"Profiles omitted:  {len(failures)}"
        )

    print()
    print("Snapshot:")
    print(SNAPSHOT_FILE)
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())



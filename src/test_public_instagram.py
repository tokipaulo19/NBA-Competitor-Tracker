from pathlib import Path
import argparse
import csv
import re
import sys
from typing import Optional

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


ROOT = Path(__file__).resolve().parents[1]

COMPETITORS_FILE = ROOT / "config" / "competitors.csv"

TEST_HANDLES = [
    "icnqld",
    "nabbaaustralia",
    "pca_australia",
]


def clean_number(value: str) -> Optional[int]:
    if not value:
        return None

    value = (
        value.strip()
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


def extract_followers(text: str) -> Optional[int]:
    if not text:
        return None

    patterns = [
        r"([\d,.]+[KkMm]?)\s+followers",
        r"([\d,.]+[KkMm]?)\s+Followers",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            return clean_number(match.group(1))

    return None


def extract_posts(text: str) -> Optional[int]:
    if not text:
        return None

    patterns = [
        r"([\d,.]+[KkMm]?)\s+posts",
        r"([\d,.]+[KkMm]?)\s+Posts",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            return clean_number(match.group(1))

    return None


def get_meta_content(page, selector: str) -> str:
    try:
        locator = page.locator(selector)

        if locator.count() > 0:
            return locator.first.get_attribute("content") or ""

    except Exception:
        pass

    return ""


def inspect_profile(page, profile):
    handle = profile["handle"]
    url = profile["profile_url"]

    result = {
        "handle": handle,
        "url": url,
        "status": "unknown",
        "followers": None,
        "posts": None,
        "reason": "",
    }

    try:
        response = page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=30000,
        )

    except PlaywrightTimeoutError:
        result["status"] = "failed"
        result["reason"] = "Page load timed out"
        return result

    except Exception as exc:
        result["status"] = "failed"
        result["reason"] = f"Browser error: {exc}"
        return result


    page.wait_for_timeout(3000)


    current_url = page.url.lower()

    if "/accounts/login" in current_url:
        result["status"] = "failed"
        result["reason"] = "Instagram redirected to login"
        return result


    status_code = response.status if response else None

    if status_code and status_code >= 400:
        result["status"] = "failed"
        result["reason"] = f"HTTP status {status_code}"
        return result


    try:
        body_text = page.locator("body").inner_text(timeout=5000)
    except Exception:
        body_text = ""


    unavailable_phrases = [
        "sorry, this page isn't available",
        "page isn't available",
        "the link you followed may be broken",
        "user not found",
    ]


    lower_body = body_text.lower()

    for phrase in unavailable_phrases:

        if phrase in lower_body:
            result["status"] = "failed"
            result["reason"] = "Instagram profile unavailable"
            return result


    sources = []


    meta_description = get_meta_content(
        page,
        'meta[name="description"]'
    )

    if meta_description:
        sources.append(meta_description)


    og_description = get_meta_content(
        page,
        'meta[property="og:description"]'
    )

    if og_description:
        sources.append(og_description)


    if body_text:
        sources.append(body_text)


    combined = "\n".join(sources)


    result["followers"] = extract_followers(combined)

    result["posts"] = extract_posts(combined)


    if result["followers"] is None:

        result["status"] = "failed"
        result["reason"] = (
            "Profile opened but follower count "
            "could not be extracted"
        )

        return result


    result["status"] = "ok"
    result["reason"] = "Profile opened successfully"

    return result


def load_test_profiles():
    with open(
        COMPETITORS_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        reader = csv.DictReader(f)

        rows = {
            row["handle"].strip(): row
            for row in reader
        }


    profiles = []

    for handle in TEST_HANDLES:

        if handle not in rows:

            raise RuntimeError(
                f"Missing test account in competitors.csv: {handle}"
            )

        profiles.append(rows[handle])


    return profiles


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--headed",
        action="store_true",
        help="Show Chromium while testing",
    )

    args = parser.parse_args()


    profiles = load_test_profiles()


    print()
    print("=" * 72)
    print("NBA COMPETITOR TRACKER")
    print("PUBLIC INSTAGRAM PROFILE TEST")
    print("=" * 72)
    print()

    print("Profiles being tested:")

    for profile in profiles:
        print(f" - {profile['handle']}")

    print()


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


        for profile in profiles:

            print(
                f"Opening @{profile['handle']}..."
            )

            result = inspect_profile(
                page,
                profile,
            )

            results.append(result)


            if result["status"] == "ok":

                followers = (
                    f"{result['followers']:,}"
                    if result["followers"] is not None
                    else "N/A"
                )

                posts = (
                    f"{result['posts']:,}"
                    if result["posts"] is not None
                    else "N/A"
                )

                print(
                    f"[OK] @{result['handle']} | "
                    f"Followers: {followers} | "
                    f"Posts: {posts}"
                )

            else:

                print(
                    f"[FAIL] @{result['handle']} | "
                    f"{result['reason']}"
                )

            print()


        browser.close()


    print("=" * 72)
    print("TEST SUMMARY")
    print("=" * 72)
    print()


    failures = [
        result
        for result in results
        if result["status"] != "ok"
    ]


    for result in results:

        print(
            f"{result['handle']:<25} "
            f"{result['status'].upper():<8} "
            f"{result['followers'] or 'N/A'}"
        )


    print()


    if failures:

        print(
            f"{len(failures)} profile(s) failed."
        )

        print()

        print(
            "IMPORTANT: Nothing has been exported."
        )

        print(
            "This is only a collector test."
        )

        return 2


    print(
        "All three profiles successfully returned follower data."
    )

    print()

    print(
        "Nothing has been exported yet."
    )

    print(
        "Next step will be the full 23-account collector."
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())

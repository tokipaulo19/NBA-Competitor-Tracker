from pathlib import Path
import json
import re

from playwright.sync_api import sync_playwright

TEST_HANDLES = [
    "icnqld",
    "nabbaaustralia",
    "pca_australia",
    "nbaaustralia_official",
]


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


def inspect(handle, page):
    url = f"https://www.instagram.com/{handle}/"

    print()
    print("=" * 70)
    print(f"Testing @{handle}")
    print("=" * 70)

    page.goto(
        url,
        wait_until="domcontentloaded",
        timeout=30000
    )

    page.wait_for_timeout(3000)

    # --------------------------------------------------------
    # 1. Search complete HTML
    # --------------------------------------------------------

    html = page.content()

    exact = find_exact_followers_in_text(html)

    if exact is not None:
        print(f"[EXACT] Found in page HTML: {exact:,}")
        return exact


    # --------------------------------------------------------
    # 2. Search each script tag separately
    # --------------------------------------------------------

    scripts = page.locator("script")

    print(f"Script tags found: {scripts.count()}")

    for index in range(scripts.count()):

        try:
            text = scripts.nth(index).text_content() or ""
        except Exception:
            continue

        exact = find_exact_followers_in_text(text)

        if exact is not None:
            print(
                f"[EXACT] Found in script #{index}: "
                f"{exact:,}"
            )

            return exact


    # --------------------------------------------------------
    # 3. Look for likely follower-related JSON fragments
    # --------------------------------------------------------

    follower_fragments = []

    for index in range(scripts.count()):

        try:
            text = scripts.nth(index).text_content() or ""
        except Exception:
            continue

        lower = text.lower()

        if (
            "follower" in lower
            or "edge_followed_by" in lower
        ):

            follower_fragments.append(
                (index, text)
            )


    print(
        f"Scripts containing follower-related text: "
        f"{len(follower_fragments)}"
    )


    # --------------------------------------------------------
    # 4. Visible / meta fallback
    # --------------------------------------------------------

    sources = []

    try:
        description = (
            page.locator(
                'meta[name="description"]'
            )
            .first
            .get_attribute("content")
        )

        if description:
            sources.append(description)

    except Exception:
        pass


    try:
        og_description = (
            page.locator(
                'meta[property="og:description"]'
            )
            .first
            .get_attribute("content")
        )

        if og_description:
            sources.append(og_description)

    except Exception:
        pass


    try:
        body = page.locator("body").inner_text()

        if body:
            sources.append(body)

    except Exception:
        pass


    combined = "\n".join(sources)

    visible_match = re.search(
        r"([\d,.]+[KkMm]?)\s+[Ff]ollowers",
        combined
    )


    if visible_match:

        raw = visible_match.group(1)

        print(
            f"[VISIBLE FALLBACK] Instagram shows: {raw}"
        )

    else:

        print(
            "[FAIL] Could not find follower count anywhere."
        )


    return None


def main():

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        context = browser.new_context(
            viewport={
                "width": 1440,
                "height": 1000
            },
            locale="en-US"
        )

        page = context.new_page()


        results = {}


        for handle in TEST_HANDLES:

            try:

                results[handle] = inspect(
                    handle,
                    page
                )

            except Exception as exc:

                print(
                    f"[ERROR] @{handle}: {exc}"
                )

                results[handle] = None


        print()
        print("=" * 70)
        print("EXACT FOLLOWER TEST SUMMARY")
        print("=" * 70)
        print()


        for handle, value in results.items():

            if value is None:

                print(
                    f"{handle:<25} "
                    f"No exact count found"
                )

            else:

                print(
                    f"{handle:<25} "
                    f"{value:,}"
                )


        print()

        browser.close()


if __name__ == "__main__":
    main()

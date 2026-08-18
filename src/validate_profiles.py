from pathlib import Path
import argparse
import csv
import json
import sys

ROOT = Path(__file__).resolve().parents[1]

COMPETITORS_FILE = ROOT / "config" / "competitors.csv"
SETTINGS_FILE = ROOT / "config" / "settings.json"
ERROR_REPORT = ROOT / "data" / "profile_validation_errors.csv"


def load_settings():
    with open(SETTINGS_FILE, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def load_competitors():
    rows = []

    with open(COMPETITORS_FILE, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            if row.get("active", "").strip().lower() == "yes":
                rows.append(row)

    return rows


def validate_profile(profile):
    """
    Placeholder validator.

    The live Instagram collector will replace this function
    with the actual API/provider/profile request.

    For now, it validates configuration only.
    """

    handle = profile.get("handle", "").strip()

    if not handle:
        return False, "Missing handle"

    return True, "Configured"


def save_error_report(errors):
    ERROR_REPORT.parent.mkdir(parents=True, exist_ok=True)

    with open(ERROR_REPORT, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "handle",
                "name",
                "reason"
            ]
        )

        writer.writeheader()

        for error in errors:
            writer.writerow(error)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mode",
        choices=["interactive", "strict", "continue"],
        default=None
    )

    args = parser.parse_args()

    settings = load_settings()

    mode = args.mode or settings.get(
        "manual_validation_mode",
        "interactive"
    )

    competitors = load_competitors()

    print()
    print("=" * 70)
    print("NBA COMPETITOR TRACKER - PROFILE PREFLIGHT")
    print("=" * 70)
    print()
    print(f"Validation mode: {mode}")
    print(f"Profiles to validate: {len(competitors)}")
    print()

    errors = []

    for profile in competitors:
        handle = profile.get("handle", "").strip()
        name = profile.get("name", "").strip()

        ok, reason = validate_profile(profile)

        if ok:
            print(f"[OK]   {handle}")
        else:
            print(f"[FAIL] {handle} - {reason}")

            errors.append({
                "handle": handle,
                "name": name,
                "reason": reason
            })

    print()

    if not errors:
        print("All profiles passed validation.")
        print()
        return 0

    save_error_report(errors)

    print("=" * 70)
    print("PROFILE VALIDATION ERRORS")
    print("=" * 70)
    print()

    for error in errors:
        print(
            f"{error['handle']}: "
            f"{error['reason']}"
        )

    print()
    print(
        f"Error report saved to:\n{ERROR_REPORT}"
    )
    print()

    if mode == "strict":
        print("STRICT MODE: Run cancelled.")
        print("No snapshot should be exported.")
        return 2

    if mode == "continue":
        print("CONTINUE MODE: Proceeding despite errors.")
        return 0

    if mode == "interactive":
        while True:
            answer = input(
                "Proceed despite these errors? [Y/N]: "
            ).strip().lower()

            if answer in ("y", "yes"):
                print()
                print("Proceeding despite validation errors.")
                return 0

            if answer in ("n", "no"):
                print()
                print("Run cancelled.")
                print("No snapshot should be exported.")
                return 2

            print("Please enter Y or N.")


if __name__ == "__main__":
    sys.exit(main())

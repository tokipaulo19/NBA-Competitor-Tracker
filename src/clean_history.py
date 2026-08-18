from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

RAW_FILE = ROOT / "data" / "historical_raw.csv"
OUTPUT_FILE = ROOT / "data" / "historical.csv"
ALIASES_FILE = ROOT / "config" / "aliases.csv"


def extract_handle(account_value):
    """
    Historical Account cells may contain both the handle
    and display name on separate lines.

    We only want the first line.
    """

    if pd.isna(account_value):
        return None

    value = str(account_value).strip()

    if not value:
        return None

    return value.splitlines()[0].strip()


def load_aliases():

    if not ALIASES_FILE.exists():
        return {}

    aliases = pd.read_csv(ALIASES_FILE)

    return dict(
        zip(
            aliases["old_handle"].astype(str).str.strip(),
            aliases["current_handle"].astype(str).str.strip(),
        )
    )


def clean_number(value):
    """
    Convert values such as:

    18.3K -> 18300
    914   -> 914
    1,234 -> 1234
    """

    if pd.isna(value):
        return None

    value = str(value).strip().replace(",", "")

    if not value:
        return None

    multiplier = 1

    if value.upper().endswith("K"):
        multiplier = 1000
        value = value[:-1]

    elif value.upper().endswith("M"):
        multiplier = 1_000_000
        value = value[:-1]

    try:
        return round(float(value) * multiplier)

    except ValueError:
        return None


def main():

    if not RAW_FILE.exists():

        raise FileNotFoundError(
            f"Could not find historical file: {RAW_FILE}"
        )


    df = pd.read_csv(RAW_FILE)


    required_columns = {
        "Date",
        "Account",
        "Followers (lifetime)",
        "Published content",
    }


    missing = required_columns - set(df.columns)


    if missing:

        raise ValueError(
            f"Historical CSV is missing columns: {sorted(missing)}"
        )


    aliases = load_aliases()


    df["handle"] = df["Account"].apply(
        extract_handle
    )


    df["handle"] = df["handle"].replace(
        aliases
    )


    df["date"] = pd.to_datetime(
        df["Date"],
        dayfirst=True,
        errors="coerce",
    ).dt.strftime("%Y-%m-%d")


    df["followers"] = df[
        "Followers (lifetime)"
    ].apply(clean_number)


    df["published_content"] = df[
        "Published content"
    ].apply(clean_number)


    cleaned = df[
        [
            "date",
            "handle",
            "followers",
            "published_content",
        ]
    ].copy()


    cleaned["source"] = "historical_manual"


    cleaned = cleaned.dropna(
        subset=[
            "date",
            "handle",
        ]
    )


    cleaned = cleaned.sort_values(
        [
            "date",
            "handle",
        ]
    )


    cleaned = cleaned.drop_duplicates(
        subset=[
            "date",
            "handle",
        ],
        keep="last",
    )


    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )


    cleaned.to_csv(
        OUTPUT_FILE,
        index=False,
    )


    print()
    print("=" * 60)
    print("NBA COMPETITOR TRACKER")
    print("Historical data cleaned successfully")
    print("=" * 60)

    print()
    print(f"Rows written: {len(cleaned)}")
    print(
        f"Accounts: {cleaned['handle'].nunique()}"
    )
    print(
        f"Snapshot dates: {cleaned['date'].nunique()}"
    )

    print()

    print("Date range:")

    print(
        cleaned["date"].min(),
        "to",
        cleaned["date"].max(),
    )

    print()

    print("Saved to:")
    print(OUTPUT_FILE)

    print()


if __name__ == "__main__":
    main()

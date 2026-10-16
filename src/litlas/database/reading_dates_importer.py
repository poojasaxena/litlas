
"""Import reading dates from Litlas ODS files."""

from collections import Counter
from pathlib import Path

import pandas as pd

from datetime import datetime
import sqlite3

from litlas.processing.core import (
    reading_dates_dir,
    library_dir,
    load_config,
)
from litlas.database.connection import connect


def normalize(value: str) -> str:
    """Normalize book titles and author names for matching."""
    return (
        " ".join(str(value).split())
        .casefold()
        .replace("’", "'")
        .replace("‘", "'")
    )

def resolve_reading_dates_file(source: str | int) -> Path:
    """Locate a reading-date ODS file using a year or filename."""

    source = str(source).strip()

    if source.isdigit():
        filename = f"Book_Read_Dates_{source}.ods"
    else:
        filename = source

    if Path(filename).name != filename or not filename.endswith(".ods"):
        raise ValueError("Provide a year or an ODS filename.")

    file = reading_dates_dir() / filename

    if not file.is_file():
        raise FileNotFoundError(
            f"Reading-date file not found: {file}"
        )

    return file

def preview_reading_dates(
    source: str | int,
    strict_id: bool = False,
) -> list[dict]:
    """Compare ODS reading dates with SQLite without modifying it."""

    file = resolve_reading_dates_file(source)

    df = pd.read_excel(file, engine="odf")

    if strict_id and "Goodread Id" not in df.columns:
        raise ValueError(
            "Strict ID mode requires a 'Goodread Id' column."
        )
    required = {"Book name", "Date Read"}
    missing_columns = required - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing ODS columns: {', '.join(sorted(missing_columns))}"
        )

    if "Author" not in df.columns:
        df["Author"] = None

    if strict_id:
        df = df.loc[
            df["Goodread Id"].notna()
            & df["Goodread Id"].astype(str).str.strip().ne("")
        ].copy()

        print(f"Strict ID mode: checking {len(df)} rows with Goodreads IDs.")
    with connect() as db:
        books = db.execute(
            """
            SELECT b.goodreads_id,
                   b.display_title,
                   b.original_title,
                   b.date_read,
                   a.name AS author
            FROM books b
            JOIN authors a ON a.id = b.author_id
            """
        ).fetchall()

    results = []
    seen_ids = set()

    for _, row in df.iterrows():
        title = normalize(row["Book name"])
        author = (
            normalize(row["Author"])
            if pd.notna(row["Author"]) else None
        )

        # Prefer Goodreads ID when supplied; otherwise match title and author.
        raw_id = row.get("Goodread Id")

        if pd.notna(raw_id) and str(raw_id).strip():
            goodreads_id = str(raw_id).strip()

            if goodreads_id.endswith(".0"):
                goodreads_id = goodreads_id[:-2]

            matches = [
                book for book in books
                if str(book["goodreads_id"]) == goodreads_id
                and (
                    not strict_id
                    or title in (
                        normalize(book["display_title"]),
                        normalize(book["original_title"]),
                    )
                )
            ]

        elif strict_id:
            matches = []

        else:
            matches = [
                book for book in books
                if title in (
                    normalize(book["display_title"]),
                    normalize(book["original_title"]),
                )
                and (author is None or normalize(book["author"]) == author)
            ]

        if len(matches) == 0:
            status = "MISSING"
            book_id = None
            old_date = None

        elif len(matches) > 1:
            status = "AMBIGUOUS"
            book_id = None
            old_date = None

        else:
            book = matches[0]
            book_id = book["goodreads_id"]
            old_date = book["date_read"]

            if book_id in seen_ids:
                status = "DUPLICATE"
                print(
                    f"DUPLICATE MATCH: {row['Book name']!r} "
                    f"→ SQLite ID {book_id}"
                )
            else:
                seen_ids.add(book_id)

                date = pd.to_datetime(
                    row["Date Read"], errors="raise"
                ).strftime("%Y/%m/%d")

                if not old_date:
                    status = "NEW DATE"
                elif old_date.replace("-", "/") == date:
                    status = "UNCHANGED"
                else:
                    status = "CONFLICT"

        results.append(
            {
                "title": row["Book name"],
                "author": row["Author"],
                "book_id": book_id,
                "old_date": old_date,
                "new_date": pd.to_datetime(
                    row["Date Read"]
                ).strftime("%Y/%m/%d"),
                "status": status,
            }
        )

    return results


def apply_reading_dates(
    source: str | int,
    strict_id: bool = False,
) -> None:
    """Apply verified ODS reading dates to SQLite, with a backup."""

    results = preview_reading_dates(source, strict_id=strict_id)

    counts = Counter(row["status"] for row in results)

    updates = [
        row for row in results
        if row["status"] in ("NEW DATE", "CONFLICT")
    ]

    # Never silently resolve ambiguous or duplicated books.
    if counts["AMBIGUOUS"] or counts["DUPLICATE"]:
        raise RuntimeError(
            "Ambiguous or duplicate matches found. "
            "Resolve them before importing."
        )

    if counts["MISSING"]:
            raise RuntimeError(
                f"{counts['MISSING']} books could not be matched. "
                "Resolve them before importing."
            )

    print(f"Source: {resolve_reading_dates_file(source).name}")
    print(f"Dates to update: {len(updates)}")
    print(f"Unmatched books: {counts['MISSING']}")

    if not updates:
        print("All matching reading dates are already up to date.")
        return

    # Back up the actual connected SQLite database.
    backup_dir = (
        library_dir()
        / load_config()["paths"]["litlas"]
        / "Backups"
    )
    backup_dir.mkdir(parents=True, exist_ok=True)

    backup_path = backup_dir / (
        f"litlas_before_reading_dates_"
        f"{datetime.now():%Y%m%d_%H%M%S_%f}.db"
    )

    with connect() as db:
        with sqlite3.connect(backup_path) as backup_db:
            db.backup(backup_db)

        print(f"Backup created: {backup_path}")

        db.execute("BEGIN IMMEDIATE")

        # Ensure records have not changed since preview.
        for row in updates:
            current = db.execute(
                """
                SELECT date_read
                FROM books
                WHERE goodreads_id = ?
                """,
                (row["book_id"],),
            ).fetchone()

            if current is None or current["date_read"] != row["old_date"]:
                raise RuntimeError(
                    f"Database changed for {row['title']}. "
                    "Import cancelled."
                )

        db.executemany(
            """
            UPDATE books
            SET date_read = ?
            WHERE goodreads_id = ?
            """,
            [
                (row["new_date"], row["book_id"])
                for row in updates
            ],
        )

    print(f"Successfully updated {len(updates)} reading dates.")
    print("Unmatched books were left untouched.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Preview or import Litlas reading dates."
    )

    parser.add_argument(
        "source",
        nargs="?",
        default="2026",
        help="Year or ODS filename inside the Reading_Dates folder.",
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Back up SQLite and apply reading dates.",
    )

    parser.add_argument(
        "--strict-id",
        action="store_true",
        help="Require both Goodreads ID and book title to match SQLite.",
    )
    args = parser.parse_args()

    if args.apply:
        apply_reading_dates(
            args.source,
            strict_id=args.strict_id,
        )
    else:
        results = preview_reading_dates(
            args.source,
            strict_id=args.strict_id,
        )

        print("\nReading dates preview:")

        for status, count in sorted(
            Counter(row["status"] for row in results).items()
        ):
            print(f"{status:<12} {count}")

        print("\nRecords needing review:")

        for row in results:
            if row["status"] in (
                "MISSING", "AMBIGUOUS", "DUPLICATE"
            ):
                print(f"  {row['status']}: {row['title']}")
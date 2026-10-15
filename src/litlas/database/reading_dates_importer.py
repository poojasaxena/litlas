
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


def preview_reading_dates(year: int) -> list[dict]:
    """Compare yearly ODS reading dates with SQLite without modifying it."""

    file = reading_dates_dir() / f"Book_Read_Dates_{year}.ods"

    if not file.exists():
        raise FileNotFoundError(f"Reading-date file not found: {file}")

    df = pd.read_excel(file, engine="odf")

    required = {"Book name", "Date Read"}
    missing_columns = required - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing ODS columns: {', '.join(sorted(missing_columns))}"
        )

    if "Author" not in df.columns:
        df["Author"] = None

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

        matches = [
            book for book in books
            if title in (
                normalize(book["display_title"]),
                normalize(book["original_title"]),
            )
            and (
                author is None
                or normalize(book["author"]) == author
            )
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


def apply_reading_dates(year: int) -> None:
    """Apply verified ODS reading dates to SQLite, with a backup."""

    results = preview_reading_dates(year)

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

    print(f"Year: {year}")
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
        "year",
        type=int,
        nargs="?",
        default=2026,
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Back up SQLite and apply reading dates.",
    )

    args = parser.parse_args()

    if args.apply:
        apply_reading_dates(args.year)
    else:
        results = preview_reading_dates(args.year)

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

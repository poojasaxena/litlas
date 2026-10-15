"""Incrementally import Goodreads records into Litlas SQLite."""

import pandas as pd

from litlas.processing.cleaning import clean_title
from litlas.processing.core import latest_goodreads, load_config
from litlas.database.connection import connect


def import_goodreads(source=None):
    source = source or latest_goodreads()
    books = pd.read_csv(source, dtype=str, keep_default_na=False)

    required = {
        "Book Id",
        "Title",
        "Author",
        "My Rating",
        "Exclusive Shelf",
        "Date Read",
        "Number of Pages",
    }
    missing = required - set(books.columns)
    if missing:
        raise ValueError(f"Missing Goodreads columns: {sorted(missing)}")

    if books["Book Id"].eq("").any():
        raise ValueError("Empty Goodreads Book Id")

    if books["Book Id"].duplicated().any():
        raise ValueError("Duplicate Goodreads Book Id")

    tracked_ids = set()

    with connect() as db:
        tracked_ids = {
            row["goodreads_id"]
            for row in db.execute("SELECT goodreads_id FROM books")
        }

    relevant = books[
        books["Exclusive Shelf"].eq("read")
        | books["Book Id"].isin(tracked_ids)
    ]

    ratings = pd.to_numeric(
        relevant["My Rating"].replace("", "0"),
        errors="coerce",
    )
    if (
        ratings.isna().any()
        or (~ratings.between(0, 5)).any()
    ):
        raise ValueError("Invalid Goodreads ratings")

    # Goodreads uses blank values for unknown page counts.
    # Store these as NULL in SQLite.
    # Blank and zero mean the page count is unavailable.
    raw_pages = relevant["Number of Pages"].str.strip()

    pages = pd.to_numeric(
        raw_pages.replace("", pd.NA),
        errors="coerce",
    )

    invalid_pages = (
        raw_pages.ne("")
        & (
            pages.isna()
            | (pages < 0)
            | (pages % 1 != 0)
        )
    )

    if invalid_pages.any():
        raise ValueError(
            "Invalid Goodreads page counts:\n"
            + relevant.loc[
                invalid_pages, ["Book Id", "Title", "Number of Pages"]
            ].to_string(index=False)
        )

    remove_subtitles = load_config().get("cleaning", {}).get("remove_subtitles", False)

    added = 0
    updated = 0
    skipped = 0

    with connect() as db:
        existing = {
            row["goodreads_id"] for row in db.execute("SELECT goodreads_id FROM books")
        }

        for book in relevant.to_dict("records"):
            book_id = book["Book Id"]
            rating = float(book["My Rating"] or 0)
            shelf = book["Exclusive Shelf"]
            date_read = book["Date Read"]

            raw_pages = book["Number of Pages"].strip()

            page_count = int(raw_pages) if raw_pages else None

            if page_count == 0:
                page_count = None

            if book_id in existing:
                # Update Goodreads data, preserving local page corrections.
                db.execute(
                    """
                    UPDATE books
                    SET rating = ?,
                        shelf = ?,
                        date_read = ?,
                        pages = ?
                    WHERE goodreads_id = ?
                    """,
                    (rating, shelf, date_read, page_count, book_id),
                )
                updated += 1
                continue

            # Litlas currently stores books once they are read.
            if shelf != "read":
                skipped += 1
                continue

            author_name = book["Author"]
            author = db.execute(
                "SELECT id FROM authors WHERE name = ?",
                (author_name,),
            ).fetchone()

            if author is None:
                cursor = db.execute(
                    "INSERT INTO authors (name) VALUES (?)",
                    (author_name,),
                )
                author_id = cursor.lastrowid
            else:
                author_id = author["id"]

            display_title = clean_title(
                book["Title"],
                remove_subtitles=remove_subtitles,
            )

            work_id = f"goodreads:{book_id}"

            db.execute(
                """
                INSERT INTO works (id, title, author_id)
                VALUES (?, ?, ?)
                """,
                (work_id, display_title, author_id),
            )

            db.execute(
                """
                INSERT INTO books (
                    goodreads_id, author_id, work_id,
                    original_title, display_title,
                    rating, shelf, date_read, pages
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    book_id,
                    author_id,
                    work_id,
                    book["Title"],
                    display_title,
                    rating,
                    shelf,
                    date_read,
                    page_count,
                ),
            )

            added += 1

    print(f"Goodreads source: {source}")
    print(f"New read books: {added}")
    print(f"Existing books updated: {updated}")
    print(f"Untracked non-read books: {skipped}")


if __name__ == "__main__":
    import_goodreads()

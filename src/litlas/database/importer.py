"""Incrementally import Goodreads records into Litlas SQLite."""

import pandas as pd

from litlas.processing.cleaning import clean_title
from litlas.processing.paths import latest_goodreads, load_config
from litlas.database.connection import connect


def _ensure_date_resolutions_table(db):
    """Create storage for confirmed reading-date decisions."""
    db.execute("""
        CREATE TABLE IF NOT EXISTS goodreads_date_resolutions (
            book_id TEXT PRIMARY KEY,
            litlas_date TEXT NOT NULL,
            goodreads_date TEXT NOT NULL,
            decision TEXT NOT NULL
                CHECK (decision = 'keep_litlas'),
            FOREIGN KEY (book_id) REFERENCES books(goodreads_id)
        )
    """)


def resolve_goodreads_date_conflict(
    book_id: str,
    litlas_date: str,
    goodreads_date: str,
    decision: str,
    source=None,
) -> None:
    """Apply a verified decision to one reading-date conflict."""

    if decision not in ("keep_litlas", "use_goodreads"):
        raise ValueError("Invalid reading-date decision.")

    # Refresh from the actual Goodreads export before saving.
    # This must happen outside the write transaction.
    preview = preview_goodreads_import(source)

    conflict = next(
        (
            item for item in preview["date_conflicts"]
            if item["book_id"] == book_id
        ),
        None,
    )

    if conflict is None or (
        conflict["litlas_date"] != litlas_date
        or conflict["goodreads_date"] != goodreads_date
    ):
        raise ValueError(
            "This conflict has changed. Check for changes again."
        )

    with connect() as db:
        db.execute("BEGIN IMMEDIATE")
        _ensure_date_resolutions_table(db)

        current = db.execute(
            "SELECT date_read FROM books WHERE goodreads_id = ?",
            (book_id,),
        ).fetchone()

        if current is None or current["date_read"] != litlas_date:
            raise ValueError(
                "Litlas reading date changed. Refresh the preview."
            )

        if decision == "keep_litlas":
            db.execute(
                """
                INSERT INTO goodreads_date_resolutions (
                    book_id, litlas_date, goodreads_date, decision
                )
                VALUES (?, ?, ?, 'keep_litlas')
                ON CONFLICT(book_id) DO UPDATE SET
                    litlas_date = excluded.litlas_date,
                    goodreads_date = excluded.goodreads_date,
                    decision = excluded.decision
                """,
                (book_id, litlas_date, goodreads_date),
            )

        else:
            cursor = db.execute(
                """
                UPDATE books
                SET date_read = ?
                WHERE goodreads_id = ?
                  AND date_read = ?
                """,
                (goodreads_date, book_id, litlas_date),
            )

            if cursor.rowcount != 1:
                raise ValueError(
                    "Reading date could not be updated."
                )

            db.execute(
                """
                DELETE FROM goodreads_date_resolutions
                WHERE book_id = ?
                """,
                (book_id,),
            )



def preview_goodreads_import(source=None):
    """Compare a Goodreads export against Litlas without modifying SQLite."""

    source = source or latest_goodreads()

    books = pd.read_csv(
        source,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig",
    )

    required = {
        "Book Id", "Title", "Author", "My Rating",
        "Exclusive Shelf", "Date Read", "Number of Pages",
    }

    missing = required - set(books.columns)
    if missing:
        raise ValueError(
            f"Missing Goodreads columns: {sorted(missing)}"
        )

    if books["Book Id"].eq("").any():
        raise ValueError("Empty Goodreads Book Id")

    if books["Book Id"].duplicated().any():
        raise ValueError("Duplicate Goodreads Book Id")

    with connect() as db:
        existing_books = {
            row["goodreads_id"]: dict(row)
            for row in db.execute(
                """
                SELECT goodreads_id, rating, shelf, date_read, pages
                FROM books
                """
            )
        }

        # The resolution table may not exist on first use.
        table_exists = db.execute(
            """
            SELECT 1 FROM sqlite_master
            WHERE type = 'table'
              AND name = 'goodreads_date_resolutions'
            """
        ).fetchone()

        resolved_dates = {}

        if table_exists:
            resolved_dates = {
                row["book_id"]: dict(row)
                for row in db.execute(
                    """
                    SELECT book_id, litlas_date,
                           goodreads_date, decision
                    FROM goodreads_date_resolutions
                    """
                )
            }

        existing_authors = {
            " ".join(row["name"].split()).casefold()
            for row in db.execute("SELECT name FROM authors")
        }

    new_books = []
    changed_books = []
    unchanged_books = []
    date_conflicts = []
    new_authors = set()

    for book in books.to_dict("records"):
        book_id = book["Book Id"]
        shelf = book["Exclusive Shelf"]

        # Only import new books once they have been read.
        if book_id not in existing_books and shelf != "read":
            continue

        rating_raw = book["My Rating"].strip()
        pages_raw = book["Number of Pages"].strip()

        try:
            rating = float(rating_raw or 0)
            if rating not in (0, 1, 2, 2.5, 3, 3.5, 4, 4.5, 5):
                raise ValueError
        except ValueError:
            raise ValueError(
                f"Invalid rating for {book['Title']}: {rating_raw}"
            )

        try:
            pages = int(pages_raw) if pages_raw else None
            if pages is not None and pages < 0:
                raise ValueError
            if pages == 0:
                pages = None
        except ValueError:
            raise ValueError(
                f"Invalid page count for {book['Title']}: {pages_raw}"
            )

        stored = existing_books.get(book_id)

        incoming = {
            "rating": rating,
            "shelf": shelf,
            "date_read": (
                book["Date Read"].strip()
                or (stored["date_read"] if stored else None)
            ),
            "pages": (
                pages
                if pages is not None
                else (stored["pages"] if stored else None)
            ),
        }

        if book_id not in existing_books:
            new_books.append(book)

            author_key = " ".join(book["Author"].split()).casefold()
            if author_key not in existing_authors:
                new_authors.add(book["Author"].strip())

            continue


        stored = existing_books[book_id]

        differences = {
            field: {
                "old": stored[field],
                "new": value,
            }
            for field, value in incoming.items()
            if (stored[field] or None) != (value or None)
        }

        # Reading dates are curated independently in Litlas.
        # Never treat date differences as automatic updates.
        date_difference = differences.pop("date_read", None)

        unresolved_date_difference = date_difference

        if date_difference is not None:
            previous = resolved_dates.get(book_id)

            already_resolved = (
                previous is not None
                and previous["decision"] == "keep_litlas"
                and previous["litlas_date"] == date_difference["old"]
                and previous["goodreads_date"] == date_difference["new"]
            )

            if already_resolved:
                unresolved_date_difference = None
            else:
                date_conflicts.append({
                    "book_id": book_id,
                    "title": book["Title"],
                    "litlas_date": date_difference["old"],
                    "goodreads_date": date_difference["new"],
                })

        if differences:
            changed_books.append({
                "book_id": book_id,
                "title": book["Title"],
                "changes": differences,
            })
        elif unresolved_date_difference is None:
            unchanged_books.append(book["Title"])


    return {
        "source": str(source),
        "new_books": new_books,
        "changed_books": changed_books,
        "unchanged_books": unchanged_books,
        "date_conflicts": date_conflicts,
        "new_authors": sorted(new_authors),
    }


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

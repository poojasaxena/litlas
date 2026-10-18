"""Migrate Litlas CSV data into SQLite."""

import pandas as pd

from litlas.processing.paths import authors_path, enriched_books_path
from litlas.database.connection import connect, database_path
from litlas.database.schema import initialize_database


def migrate():
    authors = pd.read_csv(authors_path(), dtype=str, keep_default_na=False)
    books = pd.read_csv(enriched_books_path(), dtype=str, keep_default_na=False)

    required_authors = {"Author", "Country", "ISO3", "Status", "Wikidata ID"}
    required_books = {
        "Book Id",
        "Author",
        "Title",
        "Display Title",
        "My Rating",
        "Exclusive Shelf",
        "Date Read",
        "Work ID",
        "Work Title",
    }

    for name, df, required in (
        ("authors.csv", authors, required_authors),
        ("books_enriched.csv", books, required_books),
    ):
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"{name} is missing columns: {sorted(missing)}")

    books = books.loc[books["Exclusive Shelf"].eq("read")].copy()

    if authors["Author"].duplicated().any():
        raise ValueError("Duplicate author names in authors.csv")

    if books["Book Id"].duplicated().any():
        raise ValueError("Duplicate Goodreads book IDs")

    if books["Book Id"].eq("").any():
        raise ValueError("Empty Goodreads book ID")

    # Ensure shared work IDs describe the same work.
    conflicting = books.groupby("Work ID").agg(
        titles=("Work Title", "nunique"),
        authors=("Author", "nunique"),
    )
    if (conflicting[["titles", "authors"]] > 1).any().any():
        raise ValueError("Conflicting work IDs detected")

    # Validate all ratings before writing anything.
    ratings = pd.to_numeric(books["My Rating"], errors="coerce")
    if ratings.isna().any() or (~ratings.between(0, 5)).any():
        raise ValueError("Invalid Goodreads rating detected")

    initialize_database()

    with connect() as db:
        for table in ("authors", "works", "books"):
            if db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]:
                raise RuntimeError(f"{table} is not empty; refusing to migrate twice")

        # 1. Authors
        for author in authors.to_dict("records"):
            db.execute(
                """
                INSERT INTO authors
                    (name, country, iso3, wikidata_id, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    author["Author"],
                    author["Country"],
                    author["ISO3"],
                    author["Wikidata ID"],
                    author["Status"] or "unresolved",
                ),
            )

        # Preserve book authors missing from the author cache.
        for name in books["Author"].unique():
            db.execute(
                "INSERT OR IGNORE INTO authors (name) VALUES (?)",
                (name,),
            )

        author_ids = {
            row["name"]: row["id"] for row in db.execute("SELECT id, name FROM authors")
        }

        # 2. Works and Goodreads records
        for book in books.to_dict("records"):
            author_id = author_ids[book["Author"]]
            book_id = book["Book Id"]
            work_id = book["Work ID"] or f"goodreads:{book_id}"
            display_title = book["Display Title"] or book["Title"]
            work_title = book["Work Title"] or display_title

            db.execute(
                """
                INSERT OR IGNORE INTO works (id, title, author_id)
                VALUES (?, ?, ?)
                """,
                (work_id, work_title, author_id),
            )

            db.execute(
                """
                INSERT INTO books (
                    goodreads_id, author_id, work_id,
                    original_title, display_title,
                    rating, shelf, date_read
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    book_id,
                    author_id,
                    work_id,
                    book["Title"],
                    display_title,
                    int(book["My Rating"]),
                    book["Exclusive Shelf"],
                    book["Date Read"],
                ),
            )

        # 3. Final validation (before commit)
        counts = {
            table: db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("authors", "works", "books")
        }

        if counts["books"] != len(books):
            raise RuntimeError("Book count mismatch")

        if counts["authors"] != len(author_ids):
            raise RuntimeError("Author count mismatch")

    print(f"Database: {database_path()}")
    for table, count in counts.items():
        print(f"{table}: {count}")

    print("Migration completed successfully.")


if __name__ == "__main__":
    migrate()

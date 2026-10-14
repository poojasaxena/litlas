"""Database queries used by the Litlas application."""

import pandas as pd

from litlas.database.connection import connect
from litlas.processing.cleaning import clean_title
from litlas.processing.core import load_config

def load_read_books():
    """Return read books with their authors and canonical works."""

    query = """
        SELECT
            b.goodreads_id AS "Book Id",
            b.original_title AS "Title",
            b.display_title AS "Display Title",
            a.name AS "Author",
            COALESCE(a.iso3, '') AS "ISO3",
            COALESCE(a.country, '') AS "Country",
            b.rating AS "My Rating",
            b.work_id AS "Work ID",
            COALESCE(w.title, b.display_title) AS "Work Title",
            COALESCE(b.volume_label, '') AS "Volume"
        FROM books AS b
        JOIN authors AS a
            ON a.id = b.author_id
        LEFT JOIN works AS w
            ON w.id = b.work_id
        WHERE b.shelf = 'read'
          AND b.excluded_from_display = 0
        ORDER BY a.name, w.title, b.goodreads_id
    """

    with connect() as db:
        return pd.read_sql_query(query, db)


def get_authors_for_review(include_provisional=False):
    """Authors requiring birthplace review, prioritised by read books."""

    condition = (
        "(COALESCE(a.iso3, '') = '' " "OR a.status LIKE 'provisional%')"
        if include_provisional
        else "COALESCE(a.iso3, '') = ''"
    )

    query = f"""
        SELECT
            a.id,
            a.name,
            COALESCE(a.country, '') AS country,
            COALESCE(a.iso3, '') AS iso3,
            a.status,
            COALESCE(a.wikidata_id, '') AS wikidata_id,
            COUNT(b.goodreads_id) AS book_count
        FROM authors AS a
        JOIN books AS b ON b.author_id = a.id
        WHERE b.shelf = 'read'
          AND {condition}
          AND a.status NOT LIKE 'verified%'
          AND a.status NOT LIKE 'manual%'
          AND b.excluded_from_display = 0
        GROUP BY a.id
        ORDER BY book_count DESC, a.name COLLATE NOCASE
    """

    with connect() as db:
        return [dict(row) for row in db.execute(query)]


def get_author_books(author_id):
    """Get an author's displayed read books to help verify identity."""

    with connect() as db:
        return [
            dict(row)
            for row in db.execute(
                """
                SELECT
                    b.original_title AS title,
                    b.rating AS rating
                FROM books AS b
                WHERE b.author_id = ?
                  AND b.shelf = 'read'
                  AND b.excluded_from_display = 0
                ORDER BY b.original_title COLLATE NOCASE
                """,
                (author_id,),
            )
        ]

def get_country_reading_density():
    """Count unique literary works by author's birth country."""

    query = """
        SELECT
            a.iso3 AS iso3,
            COUNT(DISTINCT b.work_id) AS works
        FROM books AS b
        JOIN authors AS a ON a.id = b.author_id
        WHERE b.shelf = 'read'
          AND b.excluded_from_display = 0
          AND COALESCE(a.iso3, '') != ''
        GROUP BY a.iso3
        ORDER BY works DESC
    """

    with connect() as db:
        return pd.read_sql_query(query, db)


def refresh_display_titles():
    """Reapply title-cleaning rules to existing Goodreads titles."""

    remove_subtitles = load_config().get("cleaning", {}).get("remove_subtitles", False)

    with connect() as db:
        books = db.execute("""
            SELECT goodreads_id, original_title, display_title
            FROM books
        """).fetchall()

        updated = 0

        for book in books:
            cleaned = clean_title(
                book["original_title"],
                remove_subtitles=remove_subtitles,
            )

            if cleaned != book["display_title"]:
                db.execute(
                    """
                    UPDATE books
                    SET display_title = ?
                    WHERE goodreads_id = ?
                    """,
                    (cleaned, book["goodreads_id"]),
                )
                updated += 1

        # Update automatically generated, single-book work titles.
        # Leave curated relationships such as murakami-1q84 alone.
        db.execute("""
            UPDATE works
            SET title = (
                SELECT b.display_title
                FROM books AS b
                WHERE b.work_id = works.id
            )
            WHERE works.id LIKE 'goodreads:%'
              AND (
                  SELECT COUNT(*)
                  FROM books AS b
                  WHERE b.work_id = works.id
              ) = 1
        """)

    return updated


def verify_author_country(author_id, country, iso3):
    """Save a manually verified country without overwriting prior verification."""

    with connect() as db:
        cursor = db.execute(
            """
            UPDATE authors
            SET country = ?,
                iso3 = ?,
                status = 'verified birthplace',
                source = 'manual review'
            WHERE id = ?
              AND status NOT LIKE 'verified%'
              AND status NOT LIKE 'manual%'
            """,
            (country, iso3, author_id),
        )

        if cursor.rowcount != 1:
            raise ValueError("Author not found or already manually verified.")

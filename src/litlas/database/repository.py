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

def get_books_read_by_year():
    """Count displayed read books by recorded reading year."""

    query = """
        SELECT
            SUBSTR(date_read, 1, 4) AS year,
            COUNT(*) AS books
        FROM books
        WHERE shelf = 'read'
          AND excluded_from_display = 0
          AND date_read IS NOT NULL
          AND TRIM(date_read) != ''
          AND SUBSTR(date_read, 1, 4) GLOB '[0-9][0-9][0-9][0-9]'
          AND SUBSTR(date_read, 5, 1) IN ('/', '-')
        GROUP BY SUBSTR(date_read, 1, 4)
        ORDER BY year
    """

    with connect() as db:
        return pd.read_sql_query(query, db)
    
def get_page_statistics():
    """Return page totals and the longest and shortest read books."""

    with connect() as db:
        summary = db.execute("""
            SELECT
                COUNT(*) AS total_books,
                COUNT(COALESCE(pages_override, pages)) AS books_with_pages,
                SUM(COALESCE(pages_override, pages)) AS total_pages
            FROM books
            WHERE shelf = 'read'
              AND excluded_from_display = 0
        """).fetchone()

        longest = db.execute("""
            SELECT
                b.display_title AS title,
                a.name AS author,
                COALESCE(b.pages_override, b.pages) AS pages
            FROM books b
            JOIN authors a ON a.id = b.author_id
            WHERE b.shelf = 'read'
              AND b.excluded_from_display = 0
              AND COALESCE(b.pages_override, b.pages) IS NOT NULL
            ORDER BY pages DESC, title
            LIMIT 1
        """).fetchone()

        shortest = db.execute("""
            SELECT
                b.display_title AS title,
                a.name AS author,
                COALESCE(b.pages_override, b.pages) AS pages
            FROM books b
            JOIN authors a ON a.id = b.author_id
            WHERE b.shelf = 'read'
              AND b.excluded_from_display = 0
              AND COALESCE(b.pages_override, b.pages) IS NOT NULL
            ORDER BY pages ASC, title
            LIMIT 1
        """).fetchone()

    return {
        "total_books": summary["total_books"],
        "books_with_pages": summary["books_with_pages"],
        "total_pages": summary["total_pages"] or 0,
        "longest": dict(longest) if longest else None,
        "shortest": dict(shortest) if shortest else None,
    }



def get_editable_books():
    """Return tracked books for the Library Editor."""

    query = """
        SELECT
            b.goodreads_id,
            b.display_title,
            b.original_title,
            a.name AS author,
            b.rating,
            b.rating_override,
            COALESCE(b.rating_override, b.rating) AS effective_rating,
            b.pages,
            b.pages_override,
            COALESCE(b.pages_override, b.pages) AS effective_pages
        FROM books AS b
        JOIN authors AS a ON a.id = b.author_id
        WHERE b.shelf = 'read'
          AND b.excluded_from_display = 0
        ORDER BY a.name COLLATE NOCASE, b.display_title COLLATE NOCASE
    """

    with connect() as db:
        return pd.read_sql_query(query, db)


def update_book_details(
    goodreads_id,
    display_title,
    rating_override,
    pages_override,
):
    """Save locally curated book details without changing Goodreads data."""

    display_title = display_title.strip()

    if not display_title:
        raise ValueError("Book title cannot be empty.")

    if rating_override is not None:
        rating_override = float(rating_override)
        if not 0 <= rating_override <= 5:
            raise ValueError("Rating must be between 0 and 5.")

    if pages_override is not None:
        pages_override = int(pages_override)
        if pages_override <= 0:
            raise ValueError("Page count must be positive.")

    with connect() as db:
        cursor = db.execute(
            """
            UPDATE books
            SET display_title = ?,
                rating_override = ?,
                pages_override = ?
            WHERE goodreads_id = ?
              AND shelf = 'read'
              AND excluded_from_display = 0
            """,
            (
                display_title,
                rating_override,
                pages_override,
                goodreads_id,
            ),
        )

        if cursor.rowcount != 1:
            raise ValueError("Book not found or excluded.")


def get_top_authors(limit=10):
    """Return most-read authors and their average personal ratings."""

    query = """
        SELECT
            a.name AS author,
            COUNT(*) AS books,
            COUNT(NULLIF(b.rating, 0)) AS rated_books,
            ROUND(AVG(NULLIF(b.rating, 0)), 2) AS avg_rating
        FROM books AS b
        JOIN authors AS a ON a.id = b.author_id
        WHERE b.shelf = 'read'
          AND b.excluded_from_display = 0
        GROUP BY a.id, a.name
        ORDER BY books DESC, avg_rating DESC, a.name COLLATE NOCASE
        LIMIT ?
    """

    with connect() as db:
        return pd.read_sql_query(query, db, params=(limit,))
        
def get_rating_distribution():
    """Count displayed read books by personal rating."""

    query = """
        SELECT
            rating,
            COUNT(*) AS books
        FROM books
        WHERE shelf = 'read'
          AND excluded_from_display = 0
          AND rating > 0
        GROUP BY rating
        ORDER BY rating
    """

    with connect() as db:
        return pd.read_sql_query(query, db)
    
def get_reading_summary():
    """Return overall statistics for displayed read books."""

    query = """
        SELECT
            COUNT(*) AS books,
            COUNT(DISTINCT work_id) AS works,
            COUNT(DISTINCT author_id) AS authors,
            COUNT(DISTINCT NULLIF(a.iso3, '')) AS countries
        FROM books AS b
        JOIN authors AS a ON a.id = b.author_id
        WHERE b.shelf = 'read'
          AND b.excluded_from_display = 0
    """

    with connect() as db:
        return dict(db.execute(query).fetchone())
    
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

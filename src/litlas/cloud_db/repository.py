"""
litlas.cloud_db.repository
Database queries used by the Litlas application.
"""

import pandas as pd

from litlas.cloud_db.connection import connect
from litlas.processing.cleaning import clean_title
from litlas.processing.paths import load_config
from difflib import SequenceMatcher
from litlas.processing.countries import country_name
from uuid import uuid4

def _read_dataframe(db, query, params=None):
    """Read a query into pandas using psycopg's dict-row connection."""
    cursor = db.execute(query) if params is None else db.execute(query, params)
    columns = [column.name for column in cursor.description]
    return pd.DataFrame(cursor.fetchall(), columns=columns)


def _lock_author_changes(db):
    """Serialize author mutations, replacing SQLite BEGIN IMMEDIATE."""
    db.execute("SELECT pg_advisory_xact_lock(7142183)")

def update_work_title(work_id, new_title):
    new_title = new_title.strip()
    if not new_title:
        raise ValueError("Book title cannot be empty.")

    with connect() as db:
        rows = db.execute(
            "SELECT goodreads_id FROM books WHERE work_id = %s",
            (work_id,),
        ).fetchall()

        if len(rows) != 1:
            raise ValueError("This title belongs to a multi-book work.")

        db.execute(
            "UPDATE works SET title = %s WHERE id = %s",
            (new_title, work_id),
        )
        db.execute(
            "UPDATE books SET display_title = %s WHERE work_id = %s",
            (new_title, work_id),
        )
        db.commit()

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
            COALESCE(b.rating_override, b.rating) AS "My Rating",
            b.date_read AS "Date Read",
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
        return _read_dataframe(db, query)


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
        ORDER BY book_count DESC, LOWER(a.name)
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
                WHERE b.author_id = %s
                  AND b.shelf = 'read'
                  AND b.excluded_from_display = 0
                ORDER BY LOWER(b.original_title)
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
        return _read_dataframe(db, query)


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
                    SET display_title = %s
                    WHERE goodreads_id = %s
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


def get_literary_wanderlust() -> pd.DataFrame:
    """Count first encounters and returns to authors by reading year.

    The earliest dated book by each author is a discovery.
    Subsequent books by that author are returns.
    """
    query = """
        WITH dated_books AS (
            SELECT
                goodreads_id,
                author_id,
                REPLACE(date_read, '/', '-') AS reading_date,
                SUBSTR(date_read, 1, 4) AS year
            FROM books
            WHERE shelf = 'read'
              AND excluded_from_display = 0
              AND date_read IS NOT NULL
              AND TRIM(date_read) != ''
              AND SUBSTR(date_read, 1, 4)
                  ~ '^[0-9]{4}$'
              AND SUBSTR(date_read, 5, 1) IN ('/', '-')
        ),
        reading_order AS (
            SELECT
                year,
                ROW_NUMBER() OVER (
                    PARTITION BY author_id
                    ORDER BY reading_date, goodreads_id
                ) AS author_encounter
            FROM dated_books
        )
        SELECT
            year,
            SUM(
                CASE WHEN author_encounter = 1 THEN 1 ELSE 0 END
            ) AS new_authors,
            SUM(
                CASE WHEN author_encounter > 1 THEN 1 ELSE 0 END
            ) AS returning_authors,
            COUNT(*) AS total_books
        FROM reading_order
        GROUP BY year
        ORDER BY year
    """

    with connect() as db:
        return _read_dataframe(db, query)


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
          AND SUBSTR(date_read, 1, 4) ~ '^[0-9]{4}$'
          AND SUBSTR(date_read, 5, 1) IN ('/', '-')
        GROUP BY SUBSTR(date_read, 1, 4)
        ORDER BY year
    """

    with connect() as db:
        return _read_dataframe(db, query)
    
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
            b.date_read,
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
        ORDER BY LOWER(a.name), LOWER(b.display_title)
    """

    with connect() as db:
        return _read_dataframe(db, query)


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
            SET display_title = %s,
                rating_override = %s,
                pages_override = %s
            WHERE goodreads_id = %s
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

        db.execute(
            """
            UPDATE works
            SET title = %s
            WHERE id = (
                SELECT work_id
                FROM books
                WHERE goodreads_id = %s
            )
            AND (
                SELECT COUNT(*)
                FROM books
                WHERE work_id = works.id
            ) = 1
            """,
            (display_title, goodreads_id),
        )


def get_top_authors(limit=10):
    """Return most-read authors using effective Litlas ratings."""

    query = """
        SELECT
            a.name AS author,
            COUNT(*) AS books,
            COUNT(
                NULLIF(COALESCE(b.rating_override, b.rating), 0)
            ) AS rated_books,
            ROUND(
                AVG(
                    NULLIF(COALESCE(b.rating_override, b.rating), 0)
                )::NUMERIC,
                2
            ) AS avg_rating
        FROM books AS b
        JOIN authors AS a ON a.id = b.author_id
        WHERE b.shelf = 'read'
          AND b.excluded_from_display = 0
        GROUP BY a.id, a.name
        ORDER BY books DESC, avg_rating DESC, LOWER(a.name)
        LIMIT %s
    """

    with connect() as db:
        return _read_dataframe(db, query, (limit,))


def get_rating_distribution():
    """Count read books by effective personal rating."""

    query = """
        SELECT
            COALESCE(b.rating_override, b.rating) AS rating,
            COUNT(*) AS books
        FROM books AS b
        WHERE b.shelf = 'read'
          AND b.excluded_from_display = 0
          AND COALESCE(b.rating_override, b.rating) > 0
        GROUP BY COALESCE(b.rating_override, b.rating)
        ORDER BY rating
    """

    with connect() as db:
        return _read_dataframe(db, query)




def add_book(
    author_id: int | None,
    title: str,
    rating: float = 0,
    pages: int | None = None,
    shelf: str = "read",
    date_read: str | None = None,
    new_author_name: str | None = None,
    new_author_iso3: str | None = None,
    confirm_similar: bool = False,
) -> str:
    """Add a book independently of Goodreads."""

    title = title.strip()

    if not title:
        raise ValueError("Book title cannot be empty.")

    if rating not in (0, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5):
        raise ValueError("Invalid rating.")

    if pages is not None and pages <= 0:
        raise ValueError("Page count must be positive.")

    if shelf not in ("read", "currently-reading", "to-read"):
        raise ValueError("Invalid reading status.")

    # Generate identifiers for the new book and literary work.
    record_id = uuid4().hex
    book_id = f"litlas:{record_id}"
    work_id = f"litlas:{record_id}"

    with connect() as db:
        _lock_author_changes(db)

        if new_author_name is not None:
            name = " ".join(new_author_name.split())

            if not name:
                raise ValueError("Author name cannot be empty.")

            if not new_author_iso3:
                raise ValueError("Please select a country.")

            existing_authors = db.execute(
                "SELECT id, name FROM authors"
            ).fetchall()

            normalized = name.casefold()

            for author in existing_authors:
                existing_name = " ".join(
                    author["name"].split()
                ).casefold()

                if normalized == existing_name:
                    raise ValueError(
                        f"Author already exists: {author['name']}"
                    )

                similarity = SequenceMatcher(
                    None,
                    normalized,
                    existing_name,
                ).ratio()

                if similarity >= 0.80 and not confirm_similar:
                    raise ValueError(
                        f"Similar author found: {author['name']}. "
                        "Please confirm this is a different person."
                    )

            cursor = db.execute(
                """
                INSERT INTO authors
                    (name, country, iso3, status, source)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    name,
                    country_name(new_author_iso3),
                    new_author_iso3,
                    "manual",
                    "manual entry",
                ),
            )

            author_id = cursor.fetchone()["id"]

        else:
            author = db.execute(
                "SELECT id FROM authors WHERE id = %s",
                (author_id,),
            ).fetchone()

            if author is None:
                raise ValueError("Selected author does not exist.")


        # A literary work must exist for country statistics
        # and unique-work counting.
        db.execute(
            """
            INSERT INTO works (id, title, author_id)
            VALUES (%s, %s, %s)
            """,
            (work_id, title, author_id),
        )

        # Goodreads rating is integer-valued in the schema.
        # Preserve half-star ratings as Litlas overrides.
        base_rating = int(rating) if float(rating).is_integer() else 0
        rating_override = rating if rating != base_rating else None

        db.execute(
            """
            INSERT INTO books (
                goodreads_id,
                author_id,
                work_id,
                original_title,
                display_title,
                rating,
                rating_override,
                pages,
                shelf,
                date_read,
                excluded_from_display
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
            """,
            (
                book_id,
                author_id,
                work_id,
                title,
                title,
                base_rating,
                rating_override,
                pages,
                shelf,
                date_read,
            ),
        )

    return book_id

    
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

    
def get_authors_for_favourites():
    """Retrieve authors and their personal literary categories."""
    with connect() as db:
        return db.execute(
            """
            SELECT id, name, favourite_tier
            FROM authors
            ORDER BY LOWER(name)
            """
        ).fetchall()


def set_author_favourite(author_id: int, tier: int) -> None:
    """Save an author's literary category."""

    if tier not in (0, 1, 2, 3):
        raise ValueError("Invalid favourite category.")

    with connect() as db:
        cursor = db.execute(
            """
            UPDATE authors
            SET favourite_tier = %s
            WHERE id = %s
            """,
            (tier, author_id),
        )

        if cursor.rowcount == 0:
            raise ValueError("Author not found.")

def delete_author(author_id: int) -> str:
    """Delete an author only when no books or works reference them."""

    with connect() as db:
        _lock_author_changes(db)

        author = db.execute(
            "SELECT name FROM authors WHERE id = %s",
            (author_id,),
        ).fetchone()

        if author is None:
            raise ValueError("Author not found.")

        books = db.execute(
            "SELECT COUNT(*) AS count FROM books WHERE author_id = %s",
            (author_id,),
        ).fetchone()["count"]

        works = db.execute(
            "SELECT COUNT(*) AS count FROM works WHERE author_id = %s",
            (author_id,),
        ).fetchone()["count"]

        if books or works:
            raise ValueError(
                f"Cannot delete {author['name']}: "
                f"{books} book(s) and {works} work(s) are linked."
            )

        db.execute(
            "DELETE FROM authors WHERE id = %s",
            (author_id,),
        )

        return author["name"]

def get_yearly_highlights():
    """Return one highest-rated completed book per reading year."""

    query = """
        WITH ranked AS (
            SELECT
                SUBSTR(b.date_read, 1, 4) AS year,
                b.display_title AS title,
                a.name AS author,
                COALESCE(b.rating_override, b.rating) AS rating,
                ROW_NUMBER() OVER (
                    PARTITION BY SUBSTR(b.date_read, 1, 4)
                    ORDER BY
                        COALESCE(b.rating_override, b.rating) DESC,
                        COALESCE(b.pages_override, b.pages, 0) DESC,
                        REPLACE(b.date_read, '/', '-') DESC,
                        LOWER(b.display_title) ASC,
                        b.goodreads_id ASC
                ) AS position
            FROM books AS b
            JOIN authors AS a ON a.id = b.author_id
            WHERE b.shelf = 'read'
              AND b.excluded_from_display = 0
              AND b.date_read IS NOT NULL
              AND SUBSTR(b.date_read, 1, 4)
                  ~ '^[0-9]{4}$'
              AND SUBSTR(b.date_read, 5, 1) IN ('/', '-')
              AND COALESCE(b.rating_override, b.rating) > 0
        )
        SELECT year, title, author, rating
        FROM ranked
        WHERE position = 1
        ORDER BY year DESC
    """

    with connect() as db:
        return _read_dataframe(db, query)


def get_books_for_rating(rating: float):
    """Return read books with the specified effective personal rating."""

    query = """
        SELECT
            b.display_title AS title,
            a.name AS author,
            COALESCE(b.rating_override, b.rating) AS rating
        FROM books AS b
        JOIN authors AS a ON a.id = b.author_id
        WHERE b.shelf = 'read'
          AND b.excluded_from_display = 0
          AND COALESCE(b.rating_override, b.rating) = %s
        ORDER BY LOWER(b.display_title)
    """

    with connect() as db:
        return _read_dataframe(db, query, (float(rating),))
    

def get_books_for_reading_year(year: str):
    """Return all books completed in a given year."""

    query = """
        SELECT
            b.display_title AS title,
            a.name AS author,
            b.date_read,
            COALESCE(b.rating_override, b.rating) AS rating
            b.date_read AS "Date Read",
        FROM books AS b
        JOIN authors AS a ON a.id = b.author_id
        WHERE b.shelf = 'read'
          AND b.excluded_from_display = 0
          AND SUBSTR(b.date_read, 1, 4) = %s
        ORDER BY
            REPLACE(b.date_read, '/', '-') DESC,
            LOWER(b.display_title)
    """

    with connect() as db:
        return _read_dataframe(db, query, (str(year),))



def get_constellation_book_details():
    """Read authoritative metadata for curated constellation books."""

    query = """
        SELECT
            SUBSTR(b.date_read, 1, 4) AS year,
            b.display_title AS title,
            a.name AS author,
            COALESCE(b.rating_override, b.rating) AS rating,
            COALESCE(b.pages_override, b.pages) AS pages
        FROM books AS b
        JOIN authors AS a ON a.id = b.author_id
        WHERE b.shelf = 'read'
          AND b.excluded_from_display = 0
          AND b.date_read IS NOT NULL
          AND SUBSTR(b.date_read, 1, 4)
              ~ '^[0-9]{4}$'
          AND SUBSTR(b.date_read, 5, 1) IN ('/', '-')
    """

    with connect() as db:
        return _read_dataframe(db, query)


def get_author_dependencies(author_id: int) -> tuple[int, int]:
    """Count books and works linked to an author."""
    with connect() as db:
        books = db.execute(
            "SELECT COUNT(*) AS count FROM books WHERE author_id = %s",
            (author_id,),
        ).fetchone()["count"]

        works = db.execute(
            "SELECT COUNT(*) AS count FROM works WHERE author_id = %s",
            (author_id,),
        ).fetchone()["count"]

    return books, works

def update_author_details(
    author_id: int,
    name: str,
    country: str,
    iso3: str,
) -> None:
    """Correct an existing author's name and country."""

    name = " ".join(name.split())

    if not name:
        raise ValueError("Author name cannot be empty.")

    if not country or not iso3:
        raise ValueError("Please select a country.")

    with connect() as db:
        _lock_author_changes(db)

        authors = db.execute(
            "SELECT id, name FROM authors"
        ).fetchall()

        for author in authors:
            if author["id"] == author_id:
                continue

            existing = " ".join(author["name"].split()).casefold()

            if existing == name.casefold():
                raise ValueError(
                    f"Another author already uses this name: "
                    f"{author['name']}"
                )

        cursor = db.execute(
            """
            UPDATE authors
            SET name = %s,
                country = %s,
                iso3 = %s,
                status = 'manual',
                source = 'manual correction'
            WHERE id = %s
            """,
            (name, country, iso3, author_id),
        )

        if cursor.rowcount != 1:
            raise ValueError("Author not found.")
        

def add_author(name: str, country: str, iso3: str,
               confirm_similar: bool = False) -> int:
    """Add an author with duplicate protection."""

    from difflib import SequenceMatcher

    name = " ".join(name.split())

    if not name:
        raise ValueError("Author name cannot be empty.")

    if not country or not iso3:
        raise ValueError("Please select a country.")

    normalized = name.casefold()

    with connect() as db:
        # Serialize the duplicate check and insertion.
        _lock_author_changes(db)

        existing = db.execute(
            "SELECT id, name FROM authors"
        ).fetchall()

        for author in existing:
            existing_name = " ".join(
                author["name"].split()
            ).casefold()

            if normalized == existing_name:
                raise ValueError(
                    f"Author already exists: {author['name']}"
                )

            similarity = SequenceMatcher(
                None, normalized, existing_name
            ).ratio()

            if similarity >= 0.80 and not confirm_similar:
                raise ValueError(
                    f"Similar author found: {author['name']}. "
                    "Please confirm this is a different person."
                )

        cursor = db.execute(
            """
            INSERT INTO authors
                (name, country, iso3, status, source)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                name,
                country,
                iso3,
                "manual",
                "manual entry",
            ),
        )

        return cursor.fetchone()["id"]


def get_favourite_authors():
    """Return all classified authors, grouped by literary tier."""
    with connect() as db:
        return db.execute(
            """
            SELECT id, name, favourite_tier
            FROM authors
            WHERE favourite_tier BETWEEN 1 AND 3
            ORDER BY favourite_tier, LOWER(name)
            """
        ).fetchall()

def verify_author_country(author_id, country, iso3):
    """Save a manually verified country without overwriting prior verification."""

    with connect() as db:
        cursor = db.execute(
            """
            UPDATE authors
            SET country = %s,
                iso3 = %s,
                status = 'verified birthplace',
                source = 'manual review'
            WHERE id = %s
              AND status NOT LIKE 'verified%%'
              AND status NOT LIKE 'manual%%'
            """,
            (country, iso3, author_id),
        )

        if cursor.rowcount != 1:
            raise ValueError("Author not found or already manually verified.")

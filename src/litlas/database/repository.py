"""Database queries used by the Litlas application."""

import pandas as pd

from litlas.database.connection import connect


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

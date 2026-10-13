"""Tests for the author-enrichment queue."""

import sqlite3

from litlas.enrichment import enrich


def test_pending_authors_order_and_protection(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"

    def test_connect():
        return sqlite3.connect(db_path)

    # Create a test database using our actual schema.
    from litlas.database.schema import SCHEMA

    with test_connect() as db:
        db.executescript(SCHEMA)

        db.executemany(
            """
            INSERT INTO authors
                (id, name, iso3, status, last_lookup_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    1,
                    "Already attempted",
                    "",
                    "review identity",
                    "2026-10-10T12:00:00+00:00",
                ),
                (2, "Never retried", "", "review identity", None),
                (3, "Mapped Author", "GBR", "provisional birthplace", None),
                (4, "Verified Author", "", "verified birthplace", None),
                (
                    5,
                    "Older attempt",
                    "",
                    "review birthplace",
                    "2026-10-01T12:00:00+00:00",
                ),
            ],
        )

        db.executemany(
            """
            INSERT INTO books (
                goodreads_id, author_id, original_title,
                display_title, shelf
            )
            VALUES (?, ?, ?, ?, 'read')
            """,
            [(str(i), i, f"Title {i}", f"Title {i}") for i in range(1, 6)],
        )

    # Return connections with the Row factory expected by enrich.py.
    from contextlib import contextmanager

    @contextmanager
    def fake_connect():
        db = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr(enrich, "connect", fake_connect)

    pending = enrich.pending_authors(retry_unresolved=True)

    assert pending == [
        (2, "Never retried"),
        (5, "Older attempt"),
        (1, "Already attempted"),
    ]

    # Previously reviewed authors should not be retried normally.
    assert enrich.pending_authors(retry_unresolved=False) == []

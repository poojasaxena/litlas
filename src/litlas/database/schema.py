from litlas.database.connection import connect

SCHEMA = """
CREATE TABLE IF NOT EXISTS authors (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    country TEXT,
    iso3 TEXT,
    birthplace TEXT,
    wikidata_id TEXT,
    status TEXT NOT NULL DEFAULT 'unresolved',
    source TEXT
);

CREATE TABLE IF NOT EXISTS works (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    author_id INTEGER NOT NULL,
    FOREIGN KEY (author_id) REFERENCES authors(id)
);

CREATE TABLE IF NOT EXISTS books (
    goodreads_id TEXT PRIMARY KEY,
    author_id INTEGER NOT NULL,
    work_id TEXT,
    original_title TEXT NOT NULL,
    display_title TEXT NOT NULL,
    volume_label TEXT,
    rating REAL NOT NULL DEFAULT 0
        CHECK (rating BETWEEN 0 AND 5),
    shelf TEXT,
    date_read TEXT,
    excluded_from_display INTEGER NOT NULL DEFAULT 0
        CHECK (excluded_from_display IN (0, 1)),
    FOREIGN KEY (author_id) REFERENCES authors(id),
    FOREIGN KEY (work_id) REFERENCES works(id)
);

CREATE INDEX IF NOT EXISTS idx_books_author
    ON books(author_id);

CREATE INDEX IF NOT EXISTS idx_books_work
    ON books(work_id);

CREATE INDEX IF NOT EXISTS idx_authors_country
    ON authors(iso3);
"""


def initialize_database():
    with connect() as db:
        db.executescript(SCHEMA)

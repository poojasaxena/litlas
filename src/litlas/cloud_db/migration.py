"""

litlas.cloud_db.migration
One-time, non-destructive migration from local Litlas SQLite to PostgreSQL.

Run only after DATABASE_URL is configured for the intended cloud database.
The SQLite source is opened read-only. The PostgreSQL destination must be empty.
"""

import sqlite3
from pathlib import Path

from psycopg import sql

from litlas.cloud_db.connection import connect as cloud_connect
from litlas.cloud_db.schema import initialize_database as initialize_cloud_database
from litlas.database.connection import database_path


TABLES = ("authors", "works", "books")  # Foreign-key dependency order.


def _source_columns(db: sqlite3.Connection, table: str) -> list[str]:
    return [row["name"] for row in db.execute(f"PRAGMA table_info({table})")]


def _target_columns(db, table: str) -> set[str]:
    rows = db.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = %s
        """,
        (table,),
    ).fetchall()
    return {row["column_name"] for row in rows}


def migrate() -> dict[str, int]:
    """Copy every row atomically, preserving identifiers and checking counts."""
    path = Path(database_path()).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"SQLite source not found: {path}")

    # mode=ro prevents accidental changes to the local Litlas database.
    source = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    source.row_factory = sqlite3.Row

    try:
        for table in TABLES:
            if not _source_columns(source, table):
                raise RuntimeError(f"SQLite source is missing table: {table}")

        # Only creates missing cloud tables; never drops tables or existing rows.
        initialize_cloud_database()

        counts = {}
        with cloud_connect() as target:
            # Block competing migrations and ordinary writer transactions that
            # cooperate with this lock; no concurrent app writers should run yet.
            target.execute("SELECT pg_advisory_xact_lock(7142183)")

            for table in TABLES:
                existing = target.execute(
                    sql.SQL("SELECT COUNT(*) AS n FROM {}")
                    .format(sql.Identifier(table))
                ).fetchone()["n"]
                if existing:
                    raise RuntimeError(
                        f"Cloud table '{table}' already contains {existing} row(s). "
                        "Migration cancelled; no cloud data was changed."
                    )

            for table in TABLES:
                source_columns = _source_columns(source, table)

                if table == "authors":
                    source_columns = [
                        column for column in source_columns
                        if column != "is_favourite"
                    ]

                target_columns = _target_columns(target, table)
                unsupported = set(source_columns) - target_columns
                if unsupported:
                    raise RuntimeError(
                        f"Cloud table '{table}' lacks SQLite columns: "
                        f"{sorted(unsupported)}. Migration cancelled."
                    )

                rows = source.execute(f'SELECT * FROM "{table}"').fetchall()
                if rows:
                    insert_sql = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                        sql.Identifier(table),
                        sql.SQL(", ").join(map(sql.Identifier, source_columns)),
                        sql.SQL(", ").join(sql.Placeholder() for _ in source_columns),
                    )
                    with target.cursor() as cursor:
                        cursor.executemany(
                            insert_sql,
                            [tuple(row[column] for column in source_columns) for row in rows],
                        )

                actual = target.execute(
                    sql.SQL("SELECT COUNT(*) AS n FROM {}")
                    .format(sql.Identifier(table))
                ).fetchone()["n"]
                if actual != len(rows):
                    raise RuntimeError(
                        f"Count mismatch for '{table}': "
                        f"SQLite={len(rows)}, PostgreSQL={actual}."
                    )
                counts[table] = actual

            # Explicit imported author IDs do not advance the IDENTITY sequence.
            max_author_id = target.execute(
                "SELECT MAX(id) AS max_id FROM authors"
            ).fetchone()["max_id"]
            if max_author_id is not None:
                target.execute(
                    "SELECT setval(pg_get_serial_sequence('authors', 'id'), %s, true)",
                    (max_author_id,),
                )

            # Commit happens automatically upon leaving cloud_connect().
        return counts
    finally:
        source.close()


if __name__ == "__main__":
    result = migrate()
    print("Litlas SQLite -> PostgreSQL migration completed:")
    for name, count in result.items():
        print(f"  {name}: {count} rows")

"""
litlas.cloud_db.connection
PostgreSQL connection handling for cloud-hosted Litlas.
"""

import os
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row


def database_url() -> str:
    """Return the PostgreSQL connection URL from the environment."""
    url = os.environ.get("DATABASE_URL", "").strip()

    if not url:
        raise RuntimeError(
            "DATABASE_URL is not configured. "
            "Set it in the deployment environment."
        )

    return url


@contextmanager
def connect():
    """Open a PostgreSQL connection with transaction handling."""
    connection = psycopg.connect(
        conninfo=database_url(),
        row_factory=dict_row,
        connect_timeout=10,
    )

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

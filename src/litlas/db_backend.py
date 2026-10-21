"""Centralized database backend selection for Litlas."""

import os


def backend_name() -> str:
    """Return the configured backend, defaulting to local SQLite."""
    backend = os.environ.get(
        "LITLAS_DB_BACKEND", "sqlite"
    ).strip().lower()

    if backend not in ("sqlite", "postgres"):
        raise ValueError(
            f"Unsupported Litlas database backend: {backend}"
        )

    return backend


def is_postgres() -> bool:
    """Return whether Litlas is configured to use PostgreSQL."""
    return backend_name() == "postgres"


def get_repository():
    """Return the repository module for the selected backend."""
    if is_postgres():
        from litlas.cloud_db import repository
    else:
        from litlas.database import repository

    return repository


def connect():
    """Return the selected backend's connection context manager."""
    if is_postgres():
        from litlas.cloud_db.connection import connect as db_connect
    else:
        from litlas.database.connection import connect as db_connect

    return db_connect()
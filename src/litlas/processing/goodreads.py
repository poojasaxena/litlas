
"""
litlas.processing.goodreads
Read and validate Goodreads CSV exports.
"""

import pandas as pd

from litlas.processing.paths import latest_goodreads


def load_goodreads(source=None):
    """Load a Goodreads export and normalise essential columns."""
    df = pd.read_csv(
        source if source is not None else latest_goodreads(),
        low_memory=False,
    )

    required = [
        "Author",
        "Title",
        "Exclusive Shelf",
        "My Rating",
    ]

    missing = set(required) - set(df)

    if missing:
        raise ValueError(
            "Missing Goodreads columns: "
            + ", ".join(sorted(missing))
        )

    df["Author"] = (
        df["Author"].fillna("").astype(str).str.strip()
    )
    df["Title"] = df["Title"].fillna("").astype(str)
    df["My Rating"] = (
        pd.to_numeric(df["My Rating"], errors="coerce")
        .fillna(0)
        .astype(int)
    )

    return df

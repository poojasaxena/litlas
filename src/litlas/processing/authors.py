
"""
litlas.processing.authors
Author birthplace metadata for literary enrichment.
"""

import pandas as pd

from litlas.processing.paths import authors_path
from litlas.processing.countries import iso3


FIELDS = [
    "Author",
    "Country",
    "ISO3",
    "Status",
    "Wikidata ID",
]


def load_authors(folder=None):
    """Load persisted author birthplace metadata."""
    path = authors_path(folder)

    if not path.exists():
        return pd.DataFrame(columns=FIELDS)

    df = pd.read_csv(
        path,
        keep_default_na=False,
        dtype=str,
    )

    for column in FIELDS:
        if column not in df:
            df[column] = ""

    return df[FIELDS].drop_duplicates(
        "Author",
        keep="last",
    )


def save_authors(df, folder=None):
    """Persist author birthplace metadata to CSV."""
    path = authors_path(folder)
    path.parent.mkdir(
        exist_ok=True,
        parents=True,
    )

    (
        df[FIELDS]
        .drop_duplicates("Author", keep="last")
        .sort_values("Author")
        .to_csv(path, index=False)
    )

    return path


def attach_country(books, authors):
    """Attach author birthplace metadata to Goodreads books."""
    out = books.merge(
        authors[FIELDS],
        on="Author",
        how="left",
    )

    for column in FIELDS[1:]:
        out[column] = out[column].fillna("")

    out["ISO3"] = out["ISO3"].where(
        out["ISO3"].astype(bool),
        out["Country"].map(iso3),
    )

    return out

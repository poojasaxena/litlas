"""
litlas.core — Goodreads reading data and persistent birthplace metadata.
"""

from pathlib import Path
import tomllib

import pandas as pd
import pycountry


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = PROJECT_ROOT / "config.toml"

FIELDS = ["Author", "Country", "ISO3", "Status", "Wikidata ID"]
ALIASES = {
    "England": "GBR",
    "Scotland": "GBR",
    "Wales": "GBR",
    "Northern Ireland": "GBR",
    "United Kingdom": "GBR",
    "USA": "USA",
    "United States": "USA",
    "United States of America": "USA",
    "Russia": "RUS",
    "South Korea": "KOR",
    "North Korea": "PRK",
    "Taiwan": "TWN",
    "Türkiye": "TUR",
    "Czech Republic": "CZE",
    "Kosovo": "XKX",
    "Ivory Coast": "CIV",
}

def load_config() -> dict:
    if not CONFIG_PATH.is_file():
        raise FileNotFoundError(
            f"Litlas configuration missing: {CONFIG_PATH}\n"
            "Create config.toml from config.example.toml."
        )

    with CONFIG_PATH.open("rb") as file:
        return tomllib.load(file)


def library_dir() -> Path:
    config = load_config()

    path = Path(config["paths"]["library"]).expanduser().resolve()

    if not path.is_dir():
        raise FileNotFoundError(
            f"Litlas library directory does not exist: {path}\n"
            f"Please check {CONFIG_PATH}"
        )

    return path


def latest_goodreads(folder=None):
    root = Path(folder) if folder else library_dir()
    goodreads_dir = root / load_config()["paths"]["goodreads"]

    files = list(goodreads_dir.glob("Goodreads_*.csv"))

    if not files:
        raise FileNotFoundError(
            f"No Goodreads exports found in {goodreads_dir}\n"
            f"Please check {CONFIG_PATH}"
        )

    return sorted(files, key=lambda p: p.name)[-1]


def authors_path(folder=None):
    root = Path(folder) if folder else library_dir()
    return root / load_config()["paths"]["litlas"] / "authors.csv"


def enriched_books_path(folder=None):
    root = Path(folder) if folder else library_dir()
    return root / load_config()["paths"]["litlas"] / "books_enriched.csv"


def iso3(name):
    if not isinstance(name,str) or not name.strip(): return ''
    name=name.strip()
    if name in ALIASES: return ALIASES[name]
    try: return pycountry.countries.lookup(name).alpha_3
    except LookupError: return ''

def load_goodreads(source=None):
    df=pd.read_csv(source if source is not None else latest_goodreads(), low_memory=False)
    required=['Author','Title','Exclusive Shelf','My Rating']
    missing=set(required)-set(df)
    if missing: raise ValueError('Missing Goodreads columns: '+', '.join(sorted(missing)))
    df['Author']=df['Author'].fillna('').astype(str).str.strip()
    df['Title']=df['Title'].fillna('').astype(str)
    df['My Rating']=pd.to_numeric(df['My Rating'],errors='coerce').fillna(0).astype(int)
    return df

def load_authors(folder=None):
    path=authors_path(folder)
    if not path.exists(): return pd.DataFrame(columns=FIELDS)
    x=pd.read_csv(path, keep_default_na=False, dtype=str)
    for col in FIELDS:
        if col not in x: x[col]=''
    return x[FIELDS].drop_duplicates('Author',keep='last')

def save_authors(df, folder=None):
    path=authors_path(folder)
    path.parent.mkdir(exist_ok=True,parents=True)
    df[FIELDS].drop_duplicates('Author',keep='last').sort_values('Author').to_csv(path,index=False)
    return path

def attach_country(books,authors):
    out=books.merge(authors[FIELDS],on='Author',how='left')
    for col in FIELDS[1:]: out[col]=out[col].fillna('')
    out['ISO3']=out['ISO3'].where(out['ISO3'].astype(bool),out['Country'].map(iso3))
    return out

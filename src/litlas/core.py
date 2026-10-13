"""Goodreads reading data and persistent birthplace metadata."""
import os
from pathlib import Path
import pandas as pd
import pycountry

FIELDS = ['Author', 'Country', 'ISO3', 'Status', 'Wikidata ID']
ALIASES = {'England':'GBR','Scotland':'GBR','Wales':'GBR','Northern Ireland':'GBR',
           'United Kingdom':'GBR','USA':'USA','United States':'USA',
           'United States of America':'USA','Russia':'RUS','South Korea':'KOR',
           'North Korea':'PRK','Taiwan':'TWN','Türkiye':'TUR','Czech Republic':'CZE',
           'Kosovo':'XKX','Ivory Coast':'CIV'}

def library_dir():
    """Personal Vault directory; never silently write to the code checkout."""
    value = os.getenv('LITLAS_LIBRARY_DIR')
    if not value:
        raise RuntimeError('Set LITLAS_LIBRARY_DIR to your Vault/Personal/Learning/Library folder.')
    path = Path(value).expanduser().resolve()
    if not path.is_dir():
        raise FileNotFoundError(f'Library directory does not exist: {path}')
    return path

def latest_goodreads(folder=None):
    folder = Path(folder) if folder else library_dir()
    files = list((folder / 'Archive').glob('Goodreads_Library_FULL_*.csv'))
    files += list(folder.glob('Goodreads_Library_FULL_*.csv'))
    if not files:
        raise FileNotFoundError(f'No Goodreads_Library_FULL_*.csv in {folder}/Archive or {folder}')
    return sorted(files, key=lambda p: p.name)[-1]

def authors_path(folder=None):
    return (Path(folder) if folder else library_dir()) / 'authors.csv'

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

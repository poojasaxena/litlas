# Litlas 🌍📚

**Litlas = Literature + Atlas**

An interactive literary world atlas that visualises your
reading history by authors' countries of birth.

Import your Goodreads history, enrich author metadata,
and explore the world through the books you've read.


Your personal Goodreads data stays under `Vault/Personal/Learning/Library/`, never in the Python package.

## Installation (Ubuntu)

```bash
cd Vault/Professional/Workbench/Tools/Python/PLibraries/Literary_Atlas
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
export LITLAS_LIBRARY_DIR="/ABSOLUTE/PATH/TO/Vault/Personal/Learning/Library"
```

The program automatically picks the latest `Archive/Goodreads_Library_FULL_*.csv`.

## Preparation is separate from displaying the map

First, create a complete enriched CSV **immediately** from the cached metadata (works offline):

```bash
litlas-prepare --no-lookup
```

Next, enrich **all** missing read-shelf authors (not only a batch of 20):

```bash
litlas-prepare --delay 5 --max-retries 3
```

This may take a long time for hundreds of authors. It saves `authors.csv` and refreshes `books_enriched.csv` after every successfully completed lookup, so you can stop with Ctrl+C and resume. HTTP 429 errors receive exponential backoff. Failed network requests are **not** treated as validated unknown countries. Some authors need manual review because Wikidata cannot safely match them or resolve their historical birthplace.

The output is:

```text
Vault/Personal/Learning/Library/
├── Archive/Goodreads_Library_FULL_2026-10.csv    # untouched source export
├── authors.csv                                   # reusable author-country metadata
├── books_enriched.csv                            # ALL read books, with ISO3 or blank
└── Reading_Journey.ods
```

Correct birthplace errors by editing `authors.csv` (columns `Country`, `ISO3`, `Status`), then regenerate the full book CSV without any external requests:

```bash
litlas-prepare --no-lookup
```

## Map

```bash
litlas
```

The Streamlit app reads only `books_enriched.csv` and plots flag markers for every country that has at least one matched author. Click a country to see authors, books, and your actual Goodreads ratings. Unknown countries cannot honestly be flagged until they are resolved; the CSV preserves all such rows.

Author country follows birthplace, not later citizenship. Historical/uncertain identity matches require review. No Goodreads original data is modified.

# Litlas — A Literary Atlas 🌍📚

*A personal atlas of books, authors, places, and reading history.*

Litlas is a local, Python-based literary tracking application with a **Streamlit** interface, **SQLite** persistence, and an interactive **Folium/Leaflet** map. It transforms reading data (including Goodreads exports) into a visual journey through the countries where authors were born, reading statistics, author collections, and tools for maintaining a curated library.

The guiding distinction is **author's country of birth**, not nationality, citizenship, writing language, or the country in which the book is set. The atlas uses present-day geographic boundaries and country codes. Unresolved author locations should stay unresolved rather than being guessed.

> **Project snapshot — 18 October 2026.** This README describes the package structure and functionality discussed during development. The file tree was supplied from the current `main` branch; not every implementation or CLI entry point was available for inspection. Sections marked **verify** are intentionally conservative.

## Features at a glance

- **Literary Atlas:** vintage-styled world map with read countries highlighted, flag markers, and popups for the authors/books associated with each country.
- **Unexplored Lands:** compact parchment-style search control inside the map, listing sovereign states not yet represented among read books. Uses the **193 UN members + Holy See + Palestine** convention (195 entries), with friendly display names maintained centrally.
- **Reading Density:** separate Streamlit page for geographical reading analysis.
- **Reading Statistics:** visualizations for reading by year, ratings, frequently read and favourite authors, and **Literary Wanderlust** (new vs. returning authors by reading year). The vintage ratings/year graphics use book-spine PNG assets.
- **Library Management:** pages and components for adding/editing books, author details/reviews, and maintaining the collection.
- **Goodreads preparation and reconciliation:** cleaning, importing, enriching, migrating and managing reading data; keep original source fields distinct from curated Litlas values.
- **Tests:** cleaning, core processing, enrichment, and Wikidata-related tests under `tests/`.

## Quick start

Prerequisites: a supported Python version and the dependencies declared in `pyproject.toml`. Work in a virtual environment so Streamlit and the application import packages from the same interpreter.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

The sovereign-country feature requires **`country_converter`**. Ensure it is declared in `pyproject.toml` and installed (if necessary):

```bash
python -m pip install country_converter
```

Run the app using the project's configured entry point (verify the current `[project.scripts]` in `pyproject.toml`). Earlier Litlas versions used:

```bash
litlas
```

For direct Streamlit execution from the repository root, the application module is:

```bash
streamlit run src/litlas/app/main.py
```

**Configuration and data:** `config.toml` controls presentation/settings, and the DB path is resolved by `litlas.database.connection.database_path()`. Do not assume the SQLite database lives in this repository: confirm its configured location before importing, backing up, or migrating data. Earlier Litlas releases supported an external `LITLAS_LIBRARY_DIR` directory; verify the current `processing/core.py` and `database/connection.py` before relying on it.

## How the code is organised

This is a **`src/`-layout Python package**. `litlas` contains shared application logic, rather than one monolithic Streamlit script.

```text
.
├── config.toml                    # Project configuration
├── pyproject.toml                 # Python packaging, dependencies, entry points
├── README.md
├── data/                          # Sample/working CSVs and design images
│   ├── constellation_books.csv
│   ├── constellation_books_bk.csv
│   ├── constellation_collection.csv
│   └── images/
├── src/litlas/
│   ├── launcher.py                # App/CLI launch integration
│   ├── app/                        # Streamlit UI and presentation
│   │   ├── main.py                # Main Literary Atlas page
│   │   ├── map_style.py           # Folium map construction/vintage styling
│   │   ├── popups.py              # Map popup/flag presentation
│   │   ├── ui.py                  # Shared page styles and headers
│   │   ├── pages/                # Other Streamlit pages
│   │   │   ├── 1_Reading_Density.py
│   │   │   ├── 2_Reading_Statistics.py
│   │   │   └── 3_Library_Management.py
│   │   ├── visualizations/
│   │   │   ├── unexplored_lands.py # Map's floating explorer control
│   │   │   ├── book_spines.py      # Ratings/year book-spine graphics
│   │   │   ├── wanderlust.py       # New/returning author chart
│   │   │   └── assets/book_spines/ # rating_*.png artwork
│   │   ├── author_details.py
│   │   ├── author_favourites.py
│   │   ├── author_review.py
│   │   ├── book_add.py
│   │   ├── book_editor.py
│   │   ├── constellation.py
│   │   └── assets/
│   ├── database/                  # SQLite storage and import workflows
│   │   ├── connection.py
│   │   ├── schema.py
│   │   ├── repository.py
│   │   ├── importer.py
│   │   ├── migration.py
│   │   └── reading_dates_importer.py
│   ├── processing/                # Domain transformations/reference data
│   │   ├── core.py
│   │   ├── cleaning.py
│   │   ├── countries.py
│   │   └── prepare.py
│   └── enrichment/                # External author metadata enrichment
│       ├── enrich.py
│       └── wikidata.py
├── tests/
│   ├── test_cleaning.py
│   ├── test_core.py
│   ├── test_enrichment.py
│   └── test_wikidata.py
└── test/                           # Separate existing directory; purpose verify
```

### Package boundaries: where changes belong

| Area | Owns | Put changes here when… |
|---|---|---|
| `processing/` | Normalisation, country reference names/codes, preparation | A rule should apply consistently across the whole application |
| `database/` | SQLite connections, schema, reads/writes, imports, migrations | Data must be loaded, stored, reconciled, or upgraded |
| `enrichment/` | Wikidata/author metadata discovery | Birthplace or author metadata must be looked up or reviewed |
| `app/` | Streamlit layout, interactions, editing interfaces, map composition | You are changing the user-facing experience |
| `app/visualizations/` | Specific charts, controls and their assets | The feature is a reusable display/control, not a database rule |
| `tests/` | Executable behavioural expectations | A parsing, mapping, or data-flow rule changes |

**Dependency direction:** Prefer `app → database / processing / enrichment`, rather than putting UI code in domain modules. Query/aggregation work belongs in `database.repository`; plotting belongs in `app.visualizations`.

## Main data flows

### 1. Literature on the map

```text
SQLite library
    │
    ▼
repository.load_read_books()
    │  book, author, ISO3, rating, etc.
    ▼
app/main.py
    ├── country boundaries → processing.countries.load_country_boundaries()
    ├── names/coordinates → processing.countries
    ├── vintage map → app.map_style.create_litlas_map()
    ├── flag markers + book popups → app.popups
    └── Unexplored Lands control → app.visualizations.unexplored_lands
    ▼
streamlit_folium.st_folium(...)
```

A country is marked **explored** when a read book has a corresponding author's birth-country `ISO3` code. Author metadata that cannot be mapped should not be silently counted as an explored country.

### 2. Unexplored Lands: agreed scope and architecture

- The **main map remains unchanged** (its GeoJSON geometry still determines what gets drawn).
- The explorer is an **additional Leaflet control** mounted from `app/visualizations/unexplored_lands.py`, beside the map zoom controls. It uses a Branca `MacroElement` so its JavaScript runs as part of Folium's map rendering.
- `processing.countries.sovereign_country_codes()` produces a cached `frozenset` of **195 ISO3 codes**: 193 UN members plus `VAT` and `PSE`. This is a deliberately defined tracking scope, **not** a universal legal adjudication of sovereignty.
- The currently read birth-country codes are intersected with this reference set. **Unexplored = reference set − explored.** The displayed total is 195; the unexplored count depends on database contents.
- Country names come from `processing.countries.country_name()`, which first checks `COUNTRY_DISPLAY_NAMES`, then falls back to `pycountry`. All display-name corrections belong in that shared dictionary, not inside the map control.
- Dependent territories such as `UMI`, `MAF`, `SGS` and `SHN` are excluded from the explorer's 195-state scope. `TWN` and `XKX` remain recognised by general Litlas country handling but are not part of this specific UN-based explorer scope.
- Search filters the **unexplored** list, not all countries. An already explored country is therefore absent from the panel by design.
- The control uses CSS classes prefixed `litlas-explorer-`, plus a small `unexplored-toggle` button. Keep its compact parchment appearance and initial closed state.

**Important:** Avoid reintroducing a hard-coded `AFRICA_ISO3` dataset or deriving sovereign-state membership by simply counting all GeoJSON entries; boundary sources include dependent territories.

### 3. Reading Statistics

The statistics page is `app/pages/2_Reading_Statistics.py` and draws on repository queries/aggregations. The visual work developed so far includes:

- A vintage book-spine treatment for rating distributions and yearly reading totals, backed by `app/visualizations/book_spines.py` and `assets/book_spines/rating_*.png`.
- A click-driven year selection for the books-read-by-year view; the selected plot position must resolve back to the correct year in the source data.
- Panels for most-read authors, favourite authors and **Literary Wanderlust**.
- `app/visualizations/wanderlust.py` presents the proportion of books by *new-to-the-reader* versus *returning* authors in each year; the data is supplied by a repository-level aggregation (`get_literary_wanderlust()` in the implementation discussed).

**Design rule:** Preserve the existing vintage artwork, chart interactions and layout when adding features. Do not replace custom book-spine images with generic charts unless explicitly intended.

### 4. Library maintenance and Goodreads data

The files imply a separation between source imports, persistent data, and editing views:

```text
Goodreads export / external metadata
      │
      ├── processing.cleaning / processing.prepare
      ├── enrichment.wikidata / enrichment.enrich
      └── database.importer / reading_dates_importer
                         │
                         ▼
                  SQLite database
                         │
               database.repository
                         │
                app management UI
```

The ongoing design principle is **non-destructive handling** of Goodreads source data and explicit preservation of user-curated Litlas values. Goodreads reconciliation/conflict-resolution UI has been worked on; do not assume that the final write/import path is complete without testing the exact current importer implementation.

#### Title-cleaning rules (recent test fix)

`processing/cleaning.py` exposes `clean_title(title, remove_subtitles=False)`:

- Normalise whitespace and remove recognised series, edition, layout and other suffixes.
- If `remove_subtitles=True`, remove text after the first colon.
- Remove trailing text starting at the first opening `(` or `[` under the current display-title policy.
- **Do not split every title at `/`.** Bilingual `Title / Translation` formatting is handled conditionally in `clean_title()` when known edition/bilingual markers are present.
- Regression example: `An English / French Dictionary` must remain unchanged when `remove_subtitles=True`.

The original problematic unconditional `title.split('/', 1)[0]` has been removed. See `tests/test_cleaning.py`.

## Shared country reference module

`processing/countries.py` owns:

| Symbol | Purpose |
|---|---|
| `COUNTRY_DISPLAY_NAMES` | Reader-friendly names (e.g. `VEN → Venezuela`, `FSM → Micronesia`, `VAT → Vatican City`) |
| `SPECIAL_COORDINATES` | Explicit marker positions for exceptional cases (`XKX`, `TWN`, `PSE`) |
| `country_name(iso3, fallback=None)` | Consistent, central display-name lookup |
| `country_coordinates(iso3)` | Approximate country marker positions; special cases and `CountryInfo` fallback |
| `sovereign_country_codes()` | Cached 195-state reference used by Unexplored Lands |
| `load_country_boundaries()` | Cached external GeoJSON country boundaries used for map rendering |

**Two different concepts:** the **map boundary dataset** may include territories, while the **Unexplored Lands reference set** deliberately includes only the 195 designated states. Do not conflate them.

The GeoJSON loader currently requests the `datasets/geo-countries` data from GitHub at runtime and caches the result in Streamlit. A missing network connection or unavailable source may prevent a cold-cache map load; consider a bundled fallback only as a future enhancement.

## Configuration, state and asset handling

- `config.toml` contains application settings. Map settings already observed include `map.flag_size` and `map.height` (defaults shown in code were approximately 14 and 800, respectively); confirm actual values in the checked-in configuration.
- The persistent library is SQLite; `database.connection.database_path()` determines its location.
- `data/` holds the visible constellation CSVs and design images. Treat `_bk` files as backups unless the current code says otherwise.
- Visual assets should be stored alongside their consuming feature. Ratings spine assets are in `app/visualizations/assets/book_spines/`.
- Do not overwrite original Goodreads exports or hand-curated SQLite values when experimenting with import workflows.
- Avoid committing personal exports, private databases, temporary caches, generated artifacts or secrets; check `.gitignore` before publishing the repository.

## Development and verification

From the project root with the environment active:

```bash
# All available tests
python -m pytest

# Focused title-cleaning regressions
python -m pytest tests/test_cleaning.py -v

# Check the sovereign-country reference set
python - <<'PY'
from litlas.processing.countries import sovereign_country_codes, country_name
codes = sovereign_country_codes()
assert len(codes) == 195
assert {'VAT', 'PSE', 'VEN', 'FSM'} <= codes
assert not {'UMI', 'MAF', 'SGS', 'SHN'} & codes
print('Reference states:', len(codes))
print('Friendly names:', country_name('VAT'), country_name('FSM'))
PY
```

The expected sovereign-country count has been verified in the development conversation: `195`. The import of `country_converter` has also been verified in the user's active environment. When running module checks outside Streamlit, `No runtime found, using MemoryCacheStorageManager` can appear because `@st.cache_data` is imported without a Streamlit server; this warning alone does not indicate a test failure.

**Manual smoke-test checklist:**

1. Launch Litlas; verify existing map colours, zoom, country flag markers and book popups are unchanged.
2. Open/close **Unexplored Lands**; verify its vintage control overlays the map without shifting the map layout.
3. Check `World · X of 195 unexplored`, search for a known unread sovereign state, and confirm dependent territories are absent.
4. Check `Vatican City`, `Micronesia`, `Venezuela` and other friendly names.
5. Check Reading Statistics image assets, year selection and Literary Wanderlust.
6. Run `pytest`, especially `test_cleaning.py`, after any title-transformation change.
7. For data imports or migrations, back up SQLite first and test using a disposable database.

## Decisions to preserve

1. **One shared country module.** Names, codes and exceptional coordinates should not be copied between Streamlit pages.
2. **Birth-country semantics.** The author's birthplace drives the literary map; don't silently substitute citizenship.
3. **Data/UI separation.** Queries in `database`, transformations in `processing`, visualizations in `app`.
4. **Non-destructive source handling.** Preserve original Goodreads input separately from Litlas curation.
5. **Vintage visual language.** Compact parchment cards, consistent sepia tones and purpose-made book-spine artwork.
6. **Small, testable changes.** Keep working map and chart behaviour stable while iterating.

## Next development checkpoints

- **Verify** actual CLI commands, Python requirements and optional dependencies against `pyproject.toml` and `launcher.py`; update Quick Start if they differ.
- **Verify** persistent SQLite location, schema, backup/import behaviour and migration procedure from the checked-in database modules.
- Confirm end-to-end **Goodreads conflict-resolution write-back**, including how `keep_litlas`/`use_goodreads` decisions are persisted and subsequently imported.
- Consider a **continent filter** in Unexplored Lands without changing its default global 195-state scope or the underlying map.
- Consider supporting **country-name search aliases** (e.g. formal ISO names), while displaying only friendly names.
- Add targeted tests for country classification and the new explorer-data computation, separate from the browser/Leaflet UI.
- Clarify whether the top-level `test/` directory is needed alongside `tests/`.

---

**Maintenance note:** This README is a living architecture and project-continuity document. When adding a feature, update its package location, source-of-truth module, data flow, relevant tests, and any newly agreed behaviour here rather than documenting only the UI screenshot.

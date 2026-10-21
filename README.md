# Litlas — A Literary Atlas 🌍📚

**A personal literary atlas of books, authors, places, and reading journeys.**

Litlas turns a reading library into an interactive exploration of literature around the world. Discover where the authors you read were born, explore countries not yet represented in your collection, revisit reading patterns, and celebrate the writers and books that have stayed with you.

Built with **Python**, **Streamlit**, **Folium/Leaflet**, and **Plotly**, Litlas combines a vintage-inspired interface with an editable literary library.

> **Geographic principle:** The Literary Atlas maps an **author's country of birth**, not their nationality, citizenship, language of writing, or a book's setting. Unknown birthplaces are not guessed. Present-day boundaries and country codes are used for visualisation.

## Explore Litlas

### Literary Atlas

An interactive world map showing the countries represented in your reading history, with country markers and details about the associated authors and books.

**Unexplored Lands** offers a searchable list of places not yet represented in your reading library. Its deliberately defined reference set consists of 193 UN member states plus the Holy See and Palestine (195 entries); this is a tracking convention, not a statement about every disputed territorial status.

### Reading Density

Geographical reading analysis to reveal how your literary journeys are distributed across the world.

### Reading Statistics

A collection of illustrated and interactive views, including:

- Books read by year, ratings, and author reading patterns.
- **Literary Wanderlust:** new-to-you versus returning authors across reading years.
- **My Literary Book of Honour:** a live, antique-book-style presentation of writers ranked as **Exceptional**, **Favourites**, and **Good authors**.
- **Literary Constellation:** a star-filled, interactive tribute to personally significant books, with groupings, labels, and book details on hover.

The visual language uses parchment tones, book-spine illustrations, vintage cartography, and original decorative assets.

### Library Management

The owner's editing workspace supports maintaining books, authors, and curated favourite-author tiers. Public visitors can explore the literary visualisations without receiving library-editing access.

Goodreads data preparation, enrichment, and reconciliation are part of the local data-management workflow. **Do not assume Goodreads import is available in the hosted application**; its cloud integration remains separate from the public deployment.

## Architecture

Litlas uses a `src/`-layout Python package with separate responsibilities for presentation, processing, persistence, and enrichment.

| Component | Responsibility |
| --- | --- |
| `src/litlas/app/` | Streamlit interface, pages, and visualisations |
| `src/litlas/app/visualizations/` | Individual charts and custom literary artwork integration |
| `src/litlas/database/` | SQLite repositories and library data workflows |
| `src/litlas/db_backend.py` | Selects the appropriate database repository |
| `src/litlas/processing/` | Country reference data, transformation logic, and central asset paths |
| `src/litlas/enrichment/` | Author metadata enrichment tools |
| `data/assets/` | Illustrations, branding, and book-spine artwork |
| `data/constellation/` | Curated constellation data and related resources |
| `tests/` | Automated tests |

### Data storage

- **Local mode:** SQLite for development and personal use.
- **Cloud mode:** Neon-hosted PostgreSQL for the deployed application.

Repository selection is handled by the application rather than by duplicating the public pages. Public data views and owner-only editing use the active repository. Local and cloud data are separate unless explicitly migrated or synchronised.

## Run locally

Requires **Python 3.10+** and the dependencies declared in `pyproject.toml`.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Launch local SQLite mode:

```bash
litlas
```

A separate cloud-mode CLI entry point is also declared:

```bash
litlas-cloud
```

**Cloud mode requires valid private PostgreSQL and authentication configuration.** It should not be used as a substitute for the normal local setup unless those settings are available.

The package also defines data preparation and enrichment commands (`litlas-prepare` and `litlas-enrich`). Consult their implementation before running operations that could update library data.

## Deployment

Litlas is designed for a Streamlit-hosted frontend connected to Neon PostgreSQL.

Before deploying:

1. Verify that all runtime dependencies are declared in `pyproject.toml` and that the deployment installs the local package (for example, using a root-level `requirements.txt` containing `-e .`).
2. Confirm the Streamlit application entrypoint and its cloud database-selection logic.
3. Set database connection details and Google OAuth credentials in the hosting provider's **private secrets configuration**.
4. Confirm that owner-only editing requires successful authentication and that public visitors cannot reach write operations.
5. Validate the hosted Literary Atlas, Reading Density, Reading Statistics, and Book of Honour against the PostgreSQL data.

**Never commit credentials** such as `.streamlit/secrets.toml`, database connection URLs, API tokens, or OAuth client secrets. The public `.streamlit/config.toml` can be version-controlled when it contains non-sensitive UI settings.

Free-tier hosting is a project requirement. Review the providers' current free-plan conditions and usage limits before enabling any service; do not enable billing or paid add-ons.

## Project configuration and artwork

- `config.toml` contains application-specific settings.
- `.streamlit/config.toml` controls Streamlit client behaviour, including custom navigation presentation.
- `src/litlas/processing/paths.py` centralises references to artwork and other project assets.
- `data/assets/illustrations/honour_book_background_transparent.png` supplies the antique Book of Honour artwork; its author names and counts are rendered dynamically from the database, not baked into the image.
- The constellation uses curated book records and PNG star illustrations alongside interactive Plotly annotations and tooltips.

## Development

Run tests from the repository root:

```bash
python -m pytest
```

Suggested smoke tests before publishing or updating the hosted version:

- Verify world-map markers, popups, country counts, and Unexplored Lands search.
- Confirm Reading Density and all Reading Statistics sections render.
- Confirm the Book of Honour updates when a favourite-author tier changes.
- Confirm constellation labels, stars, and hover details still work.
- Confirm that public visitors cannot edit the library and the owner can sign in.
- Confirm local SQLite remains usable independently of cloud PostgreSQL.

## Project status

**Active development — version 0.4.0.** The hosted deployment and its configuration should be validated before a public deployment URL is advertised.

## Credits

Created and maintained by **[Your publishing name]**.

Litlas is a personal project celebrating the places, authors, and books that shape a reading life.

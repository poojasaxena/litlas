# Litlas — A Literary Atlas 🌍📚

**A personal literary atlas of books, authors, places, and reading journeys.**

[Explore the live atlas](https://litlas.onrender.com/)

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
| `src/litlas/cloud_db/` | PostgreSQL connection and repositories for the hosted library |
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

I published Litlas as a Docker web service on Render, connected to my existing Neon PostgreSQL library. The first installable version used a GitHub Pages wrapper that embedded Streamlit in an iframe. Google sign-in for Library Management returned a 403 through that wrapper. The Render version serves Litlas directly and receives the Google sign-in callback on the same site.

1. **Build and host the app.** The Render service deploys from the `litlas-pwa` branch. Its `Dockerfile` installs the Python package and starts Streamlit with the PostgreSQL backend. At build time, `deploy/install_pwa.py` adds the Litlas install manifest and book-and-butterflies icons to the frontend. [Docker on Render](https://render.com/docs/docker)
2. **Connect the library and configure owner sign-in.** In Render, set `DATABASE_URL` to the Neon connection string and add a private Secret File named `secrets.toml` with `admin_email` and the `[auth]` settings. Set `redirect_uri` under `[auth]` to `https://litlas.onrender.com/oauth2callback` and register that exact URL under **Authorized redirect URIs** for the Google OAuth client. Visitors can browse the atlas without signing in. Library editing requires the owner's verified Google account. [Render secrets](https://render.com/docs/configure-environment-variables) · [Streamlit Google sign-in](https://docs.streamlit.io/develop/tutorials/authentication/google)

**Never commit credentials** such as `.streamlit/secrets.toml`, database connection URLs, API tokens, or OAuth client secrets.

Litlas is hosted on Render's free tier. The first visit after a period of inactivity may take longer while the service starts. Free-tier hosting is a project requirement. [Render free-tier limits](https://render.com/docs/free)

### Install on Android

Open [Litlas](https://litlas.onrender.com/) in Chrome and choose **Install** from the browser menu. The installed app opens in its own window with the Litlas name and icon. I verified Google sign-in from the installed app on a Pixel 8 and confirmed in the browser that a book added in Library Management appeared on the homepage.

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

**Active development — version 0.4.0.**

## Credits

Created and maintained by **[Your publishing name]**.

Litlas is a personal project celebrating the places, authors, and books that shape a reading life.

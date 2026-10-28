"""
litlas.processing.paths 

Central configuration and filesystem paths for Litlas.
"""

from pathlib import Path
import tomllib

PROJECT_ROOT = Path(__file__).resolve().parents[3]

CONFIG_PATH = PROJECT_ROOT / "config.toml"

DATA_DIR = PROJECT_ROOT / "data"

GEOGRAPHY_DIR = DATA_DIR / "geography"
COUNTRY_BOUNDARIES_GEOJSON = GEOGRAPHY_DIR / "countries_simplified.geojson"
COUNTRY_COORDINATES_JSON = GEOGRAPHY_DIR / "country_coordinates.json"

ASSETS_DIR = DATA_DIR / "assets"
BOOK_SPINES_DIR = ASSETS_DIR / "book_spines"
ILLUSTRATIONS_DIR = ASSETS_DIR / "illustrations"
BOOK_COVERS_DIR = ASSETS_DIR / "covers"
GALLERY_DIR = ASSETS_DIR / "gallery"

CONSTELLATION_DIR = DATA_DIR / "constellation"
CONSTELLATION_BOOKS_CSV = CONSTELLATION_DIR / "constellation_books.csv"
CONSTELLATION_COLLECTION_CSV = CONSTELLATION_DIR / "constellation_collection.csv"

HONOUR_BOOK_BACKGROUND = ILLUSTRATIONS_DIR / "honour_book_background_transparent.png"
GALLERY_DIR = ASSETS_DIR / "gallery"

JINDAGI_COVER = GALLERY_DIR / "jindagi_sarakti_rahi_front_cover.png"
LIFE_ENDLESS_EBB_COVER = GALLERY_DIR / "life_endless_ebb_front_cover.jpg"

WELCOME_IMAGE = ILLUSTRATIONS_DIR / "Litlas_Screensaver.png"
MOBILE_WELCOME_IMAGE = ILLUSTRATIONS_DIR / "Litlas_Mobile_Welcome.png"

HEADER_DIR = ASSETS_DIR / "headers/Vivaldi"

HEADER_FILES = {
    "Literary Atlas": "Litlas.svg",
    "Reading Density": "ReadingDensity.svg",
    "Reading Statistics": "ReadingStatistics.svg",
    "Library Management": "LibraryManagement.svg",
    "Ink & Verse": "Ink&Verse.svg",
    "About Litlas": "AboutLitlas.svg",
}


def load_config() -> dict:
    if not CONFIG_PATH.is_file():
        raise FileNotFoundError(
            f"Litlas configuration missing: {CONFIG_PATH}"
        )

    with CONFIG_PATH.open("rb") as file:
        return tomllib.load(file)

def resolve_project_path(value: str) -> Path:
    """Resolve absolute or project-relative filesystem paths."""
    path = Path(value).expanduser()

    if not path.is_absolute():
        path = PROJECT_ROOT / path

    return path.resolve()

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

def default_constellation_csv() -> Path:
    return CONSTELLATION_BOOKS_CSV

def authors_path(folder=None):
    root = Path(folder) if folder else library_dir()
    return root / load_config()["paths"]["litlas"] / "authors.csv"

def works_path(folder=None) -> Path:
    """Return the path of the Litlas works metadata CSV."""
    root = Path(folder) if folder else library_dir()
    return root / load_config()["paths"]["litlas"] / "works.csv"

def enriched_books_path(folder=None):
    root = Path(folder) if folder else library_dir()
    return root / load_config()["paths"]["litlas"] / "books_enriched.csv"

def reading_dates_dir() -> Path:
    """Return the directory containing yearly reading-date files."""
    return library_dir() / load_config()["paths"]["reading_date"]


def constellation_background_path() -> Path | None:
    """Resolve the configured constellation background illustration."""
    configured = load_config().get(
        "illustrations", {}
    ).get("constellation_illustration")

    if not configured:
        return None

    return resolve_project_path(configured)

def illustration_path(name: str) -> Path:
    """Resolve a configured illustration by its name."""
    config = load_config()

    try:
        configured = config["illustrations"][name]
    except KeyError as exc:
        raise KeyError(
            f"Illustration '{name}' is not defined in {CONFIG_PATH}"
        ) from exc

    return resolve_project_path(configured)
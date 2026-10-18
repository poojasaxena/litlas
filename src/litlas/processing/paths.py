"""
litlas.processing.paths 

Central configuration and filesystem paths for Litlas.
"""

from pathlib import Path
import tomllib

PROJECT_ROOT = Path(__file__).resolve().parents[3]

CONFIG_PATH = PROJECT_ROOT / "config.toml"

DATA_DIR = PROJECT_ROOT / "data"

ASSETS_DIR = DATA_DIR / "assets"
BOOK_SPINES_DIR = ASSETS_DIR / "book_spines"
ILLUSTRATIONS_DIR = ASSETS_DIR / "illustrations"
BOOK_COVERS_DIR = ASSETS_DIR / "covers"
GALLERY_DIR = ASSETS_DIR / "gallery"

CONSTELLATION_DIR = DATA_DIR / "constellation"
CONSTELLATION_BOOKS_CSV = CONSTELLATION_DIR / "constellation_books.csv"
CONSTELLATION_COLLECTION_CSV = CONSTELLATION_DIR / "constellation_collection.csv"


def load_config() -> dict:
    if not CONFIG_PATH.is_file():
        raise FileNotFoundError(
            f"Litlas configuration missing: {CONFIG_PATH}"
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

def default_constellation_csv() -> Path:
    return CONSTELLATION_BOOKS_CSV

def authors_path(folder=None):
    root = Path(folder) if folder else library_dir()
    return root / load_config()["paths"]["litlas"] / "authors.csv"


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

    return Path(configured).expanduser()
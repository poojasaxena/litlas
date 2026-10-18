from pathlib import Path
from litlas.processing.goodreads import latest_goodreads
from litlas.processing.countries import iso3


def test_latest_export(tmp_path):
    goodreads = tmp_path / "Goodreads"
    archive = goodreads / "Archive"

    archive.mkdir(parents=True)

    (archive / "Goodreads_2026-01.csv").touch()
    (goodreads / "Goodreads_2026-10.csv").touch()
    (goodreads / "Goodreads_2026-09.csv").touch()

    assert latest_goodreads(tmp_path).name == "Goodreads_2026-10.csv"


def test_birth_country_aliases():
    assert iso3('Russia')=='RUS'
    assert iso3('England')=='GBR'

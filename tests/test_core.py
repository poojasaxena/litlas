from pathlib import Path
from litlas.core import latest_goodreads, iso3

def test_latest_export(tmp_path):
    folder=tmp_path/'Archive'
    folder.mkdir()
    (folder/'Goodreads_Library_FULL_2026-01.csv').touch()
    (folder/'Goodreads_Library_FULL_2026-10.csv').touch()
    assert latest_goodreads(tmp_path).name=='Goodreads_Library_FULL_2026-10.csv'

def test_birth_country_aliases():
    assert iso3('Russia')=='RUS'
    assert iso3('England')=='GBR'

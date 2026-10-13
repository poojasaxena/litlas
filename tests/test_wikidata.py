from litlas.enrichment.wikidata import normalize_author_name
from litlas.enrichment import wikidata

def test_normalize_author_name():
    assert normalize_author_name("Abraham   Verghese") == "Abraham Verghese"
    assert normalize_author_name(" Anna  Johnston ") == "Anna Johnston"
    assert normalize_author_name("Haruki Murakami") == "Haruki Murakami"


def test_ambiguous_historical_country(monkeypatch):
    entities = {
        "place": {
            "claims": {
                "P17": [
                    {"mainsnak": {"datavalue": {"value": {"id": "roman"}}}},
                    {"mainsnak": {"datavalue": {"value": {"id": "britain"}}}},
                ]
            }
        },
        "roman": {"labels": {"en": {"value": "Roman Empire"}}},
        "britain": {"labels": {"en": {"value": "United Kingdom"}}},
    }

    monkeypatch.setattr(wikidata, "entity", lambda qid: entities[qid])

    country, status = wikidata.resolve_place_country("place")

    assert country == ""
    assert status == "review ambiguous country"


def test_single_modern_country(monkeypatch):
    entities = {
        "place": {
            "claims": {
                "P17": [{"mainsnak": {"datavalue": {"value": {"id": "ireland"}}}}]
            }
        },
        "ireland": {"labels": {"en": {"value": "Ireland"}}},
    }

    monkeypatch.setattr(wikidata, "entity", lambda qid: entities[qid])

    country, status = wikidata.resolve_place_country("place")

    assert country == "Ireland"
    assert status == "provisional birthplace"


def test_only_historical_country(monkeypatch):
    entities = {
        "place": {
            "claims": {"P17": [{"mainsnak": {"datavalue": {"value": {"id": "roman"}}}}]}
        },
        "roman": {"labels": {"en": {"value": "Roman Empire"}}},
    }

    monkeypatch.setattr(wikidata, "entity", lambda qid: entities[qid])

    country, status = wikidata.resolve_place_country("place")

    assert country == ""
    assert status == "review historical or unknown country"

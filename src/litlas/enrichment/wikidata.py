"""
litlas.enrichment.wikidata
Conservative birthplace lookup. Never silently substitute citizenship for birthplace.
"""

import requests
from litlas.processing.countries import iso3

API = 'https://www.wikidata.org/w/api.php'

class WikidataRateLimit(RuntimeError):
    """Raised when Wikidata asks the client to slow down."""
    pass

HEADERS = {'User-Agent': 'PersonalLiteraryAtlas/0.1 (local personal research)'}


def api(params):
    response = requests.get(API, params={'format':'json', **params}, headers=HEADERS, timeout=18)
    if response.status_code == 429:
        raise WikidataRateLimit(
            'Wikidata returned HTTP 429 (too many requests). Stop this batch and retry later.'
        )
    response.raise_for_status()
    return response.json()


def entity(qid):
    data = api({'action':'wbgetentities', 'ids':qid, 'languages':'en', 'props':'labels|claims'})
    return data.get('entities',{}).get(qid,{})


def claim_ids(entry, prop):
    out = []
    for claim in entry.get('claims',{}).get(prop,[]):
        value = claim.get('mainsnak',{}).get('datavalue',{}).get('value',{})
        if isinstance(value,dict) and value.get('id'): out.append(value['id'])
    return out


def label(entry):
    return entry.get('labels',{}).get('en',{}).get('value','')


def normalize_author_name(name):
    """Normalise whitespace without changing the author's identity."""
    return " ".join(name.split())


def candidate(author):
    author = normalize_author_name(author)

    results = api(
        {
            "action": "wbsearchentities",
            "search": author,
            "language": "en",
            "type": "item",
            "limit": 5,
        }
    ).get("search", [])

    allowed = (
        "writer",
        "novelist",
        "author",
        "poet",
        "playwright",
        "journalist",
        "literary",
    )

    matches = [
        r
        for r in results
        if normalize_author_name(r.get("label", "")).casefold() == author.casefold()
        and any(word in r.get("description", "").lower() for word in allowed)
    ]

    return matches[0] if len(matches) == 1 else None


def resolve_place_country(place_qid):
    """Resolve a birthplace country without guessing from claim order."""

    seen = set()
    place = place_qid

    for _ in range(5):
        if place in seen:
            break
        seen.add(place)

        entry = entity(place)
        country_ids = set(claim_ids(entry, "P17"))

        if country_ids:
            country_names = {label(entity(qid)) for qid in country_ids}

            # Do not select the first claim: claim order is
            # not evidence of the present-day country.
            if len(country_names) != 1:
                return "", "review ambiguous country"

            country = next(iter(country_names))

            if not iso3(country):
                return "", "review historical or unknown country"

            return country, "provisional birthplace"

        # Only traverse upwards when no country claim exists.
        parents = set(claim_ids(entry, "P131"))

        if len(parents) != 1:
            return "", "review birthplace geography"

        place = next(iter(parents))

    return "", "review birthplace geography"


def resolve_birth_country(author):
    try:
        match = candidate(author)

        if not match:
            return "", "review identity", ""

        qid = match["id"]
        author_entry = entity(qid)
        places = set(claim_ids(author_entry, "P19"))

        if len(places) != 1:
            return "", "review birthplace", qid

        country, status = resolve_place_country(next(iter(places)))

        return country, status, qid

    except (requests.RequestException, ValueError, KeyError) as exc:
        return "", f"lookup error: {str(exc)[:85]}", ""

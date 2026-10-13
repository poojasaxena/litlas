"""Conservative birthplace lookup. Never silently substitute citizenship for birthplace."""
import requests

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


def candidate(author):
    results = api({'action':'wbsearchentities','search':author,'language':'en','type':'item','limit':5}).get('search',[])
    # Only exact-label writer candidates accepted, to reduce false matches.
    allowed = ('writer','novelist','author','poet','playwright','journalist','literary')
    matches = [r for r in results if r.get('label','').casefold()==author.casefold() and
               any(word in r.get('description','').lower() for word in allowed)]
    return matches[0] if len(matches)==1 else None


def resolve_birth_country(author):
    try:
        match = candidate(author)
        if not match:
            return ('', 'review identity', '')
        qid = match['id']
        author_entry = entity(qid)
        places = claim_ids(author_entry, 'P19')  # birthplace
        if not places:
            return ('', 'review birthplace', qid)
        place = places[0]
        # P17: country of birthplace. P131: enclosing administrative unit.
        # Limit levels; historical entities may need manual intervention.
        seen = set()
        for _ in range(5):
            if place in seen: break
            seen.add(place)
            entry = entity(place)
            countries = claim_ids(entry, 'P17')
            if countries:
                country_name = label(entity(countries[0]))
                if country_name in {'Soviet Union','Yugoslavia','Ottoman Empire','British Raj'}:
                    return ('', 'review historical country', qid)
                return (country_name, 'provisional birthplace', qid)
            parents = claim_ids(entry, 'P131')
            if not parents: break
            place = parents[0]
        return ('', 'review birthplace geography', qid)
    except (requests.RequestException, ValueError, KeyError) as exc:
        return ('', f'lookup error: {str(exc)[:85]}', '')

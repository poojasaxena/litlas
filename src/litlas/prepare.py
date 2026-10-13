"""Prepare a full, cached birth-country enriched Goodreads table before launching the map."""
import argparse
import os
import random
import time
from pathlib import Path
import pandas as pd
import requests
from litlas.core import (FIELDS, library_dir, latest_goodreads, load_goodreads,
                         load_authors, save_authors, attach_country, iso3)
from litlas.wikidata import resolve_birth_country, WikidataRateLimit


def build_csv(source=None, folder=None):
    folder = Path(folder) if folder else library_dir()
    book_df = load_goodreads(source or latest_goodreads(folder))
    books = book_df.loc[book_df['Exclusive Shelf'].eq('read')].copy()
    # All read books are included, even when the author has not yet been resolved.
    out = attach_country(books, load_authors(folder))
    target = folder / 'books_enriched.csv'
    temp = folder / 'books_enriched.csv.tmp'
    out.to_csv(temp, index=False)
    os.replace(temp, target)
    return out, target


def main():
    p = argparse.ArgumentParser(description='Build a complete enriched Goodreads CSV; optionally resolve every missing author.')
    p.add_argument('--csv', help='Explicit Goodreads source, otherwise latest Vault archive export')
    p.add_argument('--no-lookup', action='store_true', help='Just rebuild from existing authors.csv (no network)')
    p.add_argument('--delay', type=float, default=5.0, help='Seconds between author lookups')
    p.add_argument('--max-retries', type=int, default=3, help='Max retries per transient error / HTTP 429')
    p.add_argument('--limit', type=int, help='Optional max authors to process (default: all)')
    p.add_argument('--retry-unresolved', action='store_true', help='Revisit unresolved identity/geography records')
    args = p.parse_args()
    if args.delay < 0 or args.max_retries < 0 or (args.limit is not None and args.limit < 1):
        p.error('Use nonnegative --delay/--max-retries and a positive --limit')
    folder = library_dir()
    source = Path(args.csv) if args.csv else latest_goodreads(folder)
    all_books, destination = build_csv(source, folder)
    print(f'Read books: {len(all_books)} | Authors: {all_books.Author.nunique()}')
    print(f'Complete output available immediately: {destination}', flush=True)
    if args.no_lookup:
        return
    authors = load_authors(folder)
    known = authors.set_index('Author') if len(authors) else pd.DataFrame(columns=FIELDS).set_index('Author')
    pending = []
    for author in sorted(set(all_books.Author) - {''}):
        if author not in known.index:
            pending.append(author)
        elif args.retry_unresolved and not str(known.loc[author,'ISO3']):
            pending.append(author)
        elif str(known.loc[author,'Status']).startswith('lookup error:'):
            pending.append(author)
    if args.limit:
        pending = pending[:args.limit]
    print(f'Pending author lookups: {len(pending)}', flush=True)
    for count, name in enumerate(pending, 1):
        country = status = qid = ''
        for attempt in range(args.max_retries + 1):
            try:
                country, status, qid = resolve_birth_country(name)
                if status.startswith('lookup error:'):
                    raise RuntimeError(status)
                break
            except (WikidataRateLimit, requests.RequestException, RuntimeError) as exc:
                if attempt == args.max_retries:
                    print(f'[{count}/{len(pending)}] {name}: request failed; left pending ({exc})', flush=True)
                    status = 'lookup error: retry later'
                    break
                wait = min(180, 15 * 2**attempt) + random.uniform(0, 2)
                print(f'Rate limited / transient error for {name}; retrying in {wait:.0f}s', flush=True)
                time.sleep(wait)
        if status.startswith('lookup error:'):
            # Never persist a transient error as an authoritative result.
            continue
        code = iso3(country)
        if country and not code:
            status = 'review country name: ' + status
        row = dict(zip(FIELDS, [name, country, code, status, qid]))
        authors = pd.concat([authors[authors.Author != name], pd.DataFrame([row])], ignore_index=True)
        save_authors(authors, folder)
        enriched, _ = build_csv(source, folder)  # checkpoint per author
        print(f'[{count}/{len(pending)}] {name}: {country or "UNRESOLVED"} [{status}]', flush=True)
        if count != len(pending):
            time.sleep(args.delay)
    enriched, _ = build_csv(source, folder)
    num = enriched.loc[enriched.ISO3.ne(''), 'Author'].nunique()
    print(f'Done. {num}/{enriched.Author.nunique()} authors with countries; {len(enriched)} books exported to {destination}')
    print('Unknown authors remain in the CSV for review; no country is guessed.')

if __name__ == '__main__':
    main()

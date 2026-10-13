"""CLI: litlas-enrich --batch 20"""
import argparse
import time
import pandas as pd
from litlas.core import FIELDS, load_goodreads, load_authors, save_authors, iso3, latest_goodreads
from litlas.wikidata import resolve_birth_country, WikidataRateLimit

def main():
    parser=argparse.ArgumentParser(description='Enrich authors with country of birth via Wikidata')
    parser.add_argument('--csv',default=None,help='Override the latest Goodreads export')
    parser.add_argument('--batch',type=int,default=20,help='Authors to try in this run')
    parser.add_argument('--retry-unresolved',action='store_true')
    parser.add_argument('--delay',type=float,default=2.0,help='Seconds between requests (default: 2)')
    args=parser.parse_args()
    if args.batch < 1: parser.error('--batch must be positive')
    source=args.csv or latest_goodreads()
    print(f'Using Goodreads export: {source}')
    read=load_goodreads(source)
    read=read[read['Exclusive Shelf'].eq('read')]
    names=sorted(set(read['Author'])-{''})
    authors=load_authors()
    saved=set(authors['Author'])
    # Earlier network errors are never considered completed lookups.
    transient=set(authors.loc[authors['Status'].str.startswith('lookup error:',na=False),'Author'])
    pending=[a for a in names if a not in saved or a in transient]
    if args.retry_unresolved:
        unresolved=set(authors.loc[authors['ISO3'].eq(''),'Author'])
        pending=[a for a in names if a not in saved or a in unresolved or a in transient]
    pending=pending[:args.batch]
    if not pending:
        print('Nothing pending. Use --retry-unresolved to revisit missing matches.')
        return
    for idx,author in enumerate(pending,1):
        try:
            country,status,qid=resolve_birth_country(author)
        except WikidataRateLimit:
            print(f'Wikidata rate-limited at author {idx}/{len(pending)} ({author}).',flush=True)
            print('Stopping without saving this failed lookup. Wait a while before rerunning.',flush=True)
            break
        if status.startswith('lookup error:'):
            print(f'[{idx}/{len(pending)}] {author}: temporary lookup error; NOT marking as resolved [{status}]',flush=True)
            continue
        code=iso3(country)
        if country and not code: status='review country name: '+status
        row=dict(zip(FIELDS,[author,country,code,status,qid]))
        authors=pd.concat([authors[authors['Author']!=author],pd.DataFrame([row])],ignore_index=True)
        path=save_authors(authors)
        print(f'[{idx}/{len(pending)}] {author}: {country or "UNKNOWN"} [{status}]',flush=True)
        time.sleep(args.delay)
    print(f'Saved {len(authors)} author records to {path}')

if __name__=='__main__':main()

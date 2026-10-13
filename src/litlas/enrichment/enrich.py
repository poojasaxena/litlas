"""CLI: litlas-enrich --batch 20"""

import argparse
import time
from datetime import datetime, timezone
from litlas.core import iso3
from litlas.database.connection import connect
from litlas.enrichment.wikidata import resolve_birth_country, WikidataRateLimit


def pending_authors(retry_unresolved=False):
    """Select authors eligible for birthplace lookup.

    Never overwrite mapped or manually verified authors.
    Unresolved retries are ordered by oldest attempt first.
    """

    with connect() as db:
        rows = db.execute("""
            SELECT DISTINCT
                a.id,
                a.name,
                COALESCE(a.iso3, '') AS iso3,
                COALESCE(a.status, '') AS status,
                a.last_lookup_at
            FROM authors AS a
            JOIN books AS b ON b.author_id = a.id
            WHERE b.shelf = 'read'
            ORDER BY
                a.last_lookup_at IS NOT NULL,
                a.last_lookup_at,
                a.name COLLATE NOCASE
        """).fetchall()

    pending = []

    for row in rows:
        status = row["status"]
        iso = row["iso3"]

        if iso:
            continue

        if status.startswith(("verified", "manual")):
            continue

        # An author imported without a completed lookup.
        never_searched = row["last_lookup_at"] is None and status in ("", "unresolved")

        # Temporary lookup errors can be retried.
        transient = status.startswith("lookup error:")

        if never_searched or transient or retry_unresolved:
            pending.append((row["id"], row["name"]))

    return pending


def main():
    parser = argparse.ArgumentParser(
        description="Enrich author birthplaces using Wikidata"
    )

    parser.add_argument(
        "--batch",
        type=int,
        default=20,
        help="Maximum authors to look up",
    )

    parser.add_argument(
        "--retry-unresolved",
        action="store_true",
        help="Revisit unresolved author identities and birthplaces",
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Seconds between Wikidata lookups",
    )

    args = parser.parse_args()

    if args.batch < 1:
        parser.error("--batch must be positive")

    if args.delay < 0:
        parser.error("--delay cannot be negative")

    pending = pending_authors(args.retry_unresolved)[: args.batch]

    if not pending:
        print("Nothing pending.")
        return

    print(f"Looking up {len(pending)} authors")

    mapped_count = 0
    unresolved_count = 0
    error_count = 0

    for idx, (author_id, author_name) in enumerate(pending, 1):
        try:
            country, status, qid = resolve_birth_country(author_name)

        except WikidataRateLimit:
            print(
                f"Rate-limited at {idx}/{len(pending)}: {author_name}",
                flush=True,
            )
            print("Stopping. Retry later.", flush=True)
            break

        if status.startswith("lookup error:"):
            error_count += 1
            print(
                f"[{idx}/{len(pending)}] {author_name}: {status}",
                flush=True,
            )
            continue

        country_code = iso3(country)

        if country and not country_code:
            status = "review country name: " + status

        attempted_at = datetime.now(timezone.utc).isoformat()

        with connect() as db:
            cursor = db.execute(
                """
                UPDATE authors
                SET country = ?,
                    iso3 = ?,
                    status = ?,
                    wikidata_id = ?,
                    source = 'wikidata',
                    last_lookup_at = ?
                WHERE id = ?
                AND COALESCE(iso3, '') = ''
                AND COALESCE(status, '') NOT LIKE 'verified%'
                AND COALESCE(status, '') NOT LIKE 'manual%'
                """,
                (
                    country,
                    country_code,
                    status,
                    qid,
                    attempted_at,
                    author_id,
                ),
            )

        if cursor.rowcount:
            if country_code:
                mapped_count += 1
            else:
                unresolved_count += 1

            print(
                f"[{idx}/{len(pending)}] {author_name}: "
                f"{country or 'UNKNOWN'} [{status}]",
                flush=True,
            )

        if idx < len(pending):
            time.sleep(args.delay)

    print("\nEnrichment summary")
    print(f"Newly mapped:     {mapped_count}")
    print(f"Still unresolved: {unresolved_count}")
    print(f"Temporary errors: {error_count}")


if __name__ == "__main__":
    main()

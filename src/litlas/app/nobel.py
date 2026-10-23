"""Automatic Nobel Prize in Literature matching for Litlas."""

import json
import re
import unicodedata
from pathlib import Path
from urllib.request import Request, urlopen

import streamlit as st


API_URL = (
    "https://api.nobelprize.org/2.1/laureates"
    "?nobelPrizeCategory=lit&limit=1000"
)

# Use a bundled snapshot if the API is temporarily unavailable.
SNAPSHOT = (
    Path(__file__).resolve().parents[3]
    / "data/reference/nobel_literature.json"
)


def normalize_name(name):
    name = unicodedata.normalize("NFKD", str(name))
    name = "".join(
        char for char in name
        if not unicodedata.combining(char)
    )
    return re.sub(r"[^a-z0-9]", "", name.casefold())


def fetch_literature_laureates():
    request = Request(
        API_URL,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
    )

    with urlopen(request, timeout=15) as response:
        data = json.load(response)

    laureates = []

    for person in data["laureates"]:
        prizes = person.get("nobelPrizes", [])

        if not any(
            prize.get("category", {}).get("en") == "Literature"
            for prize in prizes
        ):
            continue

        literature_prizes = [
            prize for prize in prizes
            if prize.get("category", {}).get("en") == "Literature"
        ]

        award_year = literature_prizes[0]["awardYear"]

        names = []

        for field in ("fullName", "knownName", "penName"):
            value = person.get(field, "")

            if isinstance(value, dict):
                value = value.get("en", "")

            if isinstance(value, str) and value.strip():
                names.append(value.strip())

        if names:
            laureates.append({
                "names": names,
                "year": award_year,
            })

    if not laureates:
        raise ValueError("No literature laureates returned")

    return laureates


@st.cache_data(ttl=30 * 24 * 3600, show_spinner=False)
def load_literature_laureates():
    try:
        return fetch_literature_laureates()
    except (OSError, ValueError, KeyError, TypeError):
        if SNAPSHOT.is_file():
            return json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        return []


def match_nobel_authors(authors):
    laureates = load_literature_laureates()

    lookup = {
        normalize_name(name): laureate["year"]
        for laureate in laureates
        for name in laureate["names"]
    }

    return sorted(
        {
            (str(author).strip(), lookup[normalize_name(author)])
            for author in authors
            if normalize_name(author) in lookup
        },
        key=lambda item: int(item[1]),
    )
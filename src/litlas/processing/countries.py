
"""
litlas.processing.countries
Shared country names for Litlas.
"""
import json
from pathlib import Path
import country_converter as coco
from functools import lru_cache
import pycountry
import requests

from copy import deepcopy
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

import streamlit as st
from countryinfo import CountryInfo
from litlas.processing.paths import (
    COUNTRY_BOUNDARIES_GEOJSON,
    COUNTRY_COORDINATES_JSON,
)

COUNTRY_BOUNDARIES_URL = (
    "https://raw.githubusercontent.com/"
    "datasets/geo-countries/master/data/countries.geojson"
)


TERRITORY_MERGES = {
    "MAR": {"ESH"},  # Western Sahara → Morocco
    "SOM": {"Somaliland"},  # Somaliland → Somalia
    "CYP": {"Northern Cyprus", "Cyprus No Mans Area"},
    "KAZ": {"Baykonur Cosmodrome"},
    "SRB": {"Kosovo"},  # Kosovo → Serbia
}

COUNTRY_DISPLAY_NAMES = {
    "VEN": "Venezuela",
    "VAT": "Vatican City",
    "FSM": "Micronesia",
    "BOL": "Bolivia",
    "TZA": "Tanzania",
    "SYR": "Syria",
    "LAO": "Laos",
    "VNM": "Vietnam",
    "BRN": "Brunei",
    "MDA": "Moldova",
    "RUS": "Russia",
    "KOR": "South Korea",
    "PRK": "North Korea",
    "COD": "DR Congo",
    "COG": "Republic of the Congo",
    "CIV": "Ivory Coast",
    "SWZ": "Eswatini",
    "STP": "São Tomé and Príncipe",
    "SHN": "Saint Helena",
    "MAF": "Saint Martin",
    "VCT": "Saint Vincent and the Grenadines",
    "USA": "United States",
    "GBR": "United Kingdom",
    "CZE": "Czech Republic",
    "IRN": "Iran",
    "TWN": "Taiwan",
    "PSE": "Palestine",
    "XKX": "Kosovo",
    "TUR": "Turkey",
}


SPECIAL_COORDINATES = {
    "XKX": [42.6, 21.0],    # Kosovo
    "TWN": [23.7, 121.0],  # Taiwan
    "PSE": [31.9, 35.2],   # Palestine
}


ALIASES = {
    "England": "GBR",
    "Scotland": "GBR",
    "Wales": "GBR",
    "Northern Ireland": "GBR",
    "United Kingdom": "GBR",
    "USA": "USA",
    "United States": "USA",
    "United States of America": "USA",
    "Russia": "RUS",
    "South Korea": "KOR",
    "North Korea": "PRK",
    "Taiwan": "TWN",
    "Türkiye": "TUR",
    "Czech Republic": "CZE",
    "Kosovo": "XKX",
    "Ivory Coast": "CIV",
}

def iso3(name):
    """Resolve a country name or alias to an ISO3 code."""
    if not isinstance(name, str) or not name.strip():
        return ""

    name = name.strip()

    if name in ALIASES:
        return ALIASES[name]

    try:
        return pycountry.countries.lookup(name).alpha_3
    except LookupError:
        return ""


@lru_cache(maxsize=1)
def sovereign_country_codes() -> frozenset[str]:
    """UN members plus the two UN observer states."""

    converter = coco.CountryConverter(
        only_UNmember=True
    )

    members = {
        str(iso).strip().upper()
        for iso in converter.data["ISO3"].dropna()
        if len(str(iso).strip()) == 3
    }

    if len(members) != 193:
        raise ValueError(
            "Unexpected UN member-state count: "
            f"{len(members)}. Check country_converter data."
        )

    sovereign = members | {"VAT", "PSE"}

    if len(sovereign) != 195:
        raise ValueError(
            "Unexpected sovereign-state reference count."
        )

    return frozenset(sovereign)


def is_litlas_country(iso: str) -> bool:
    """Check whether an ISO3 code belongs to Litlas's 195 countries."""
    return (
        isinstance(iso, str)
        and iso.strip().upper() in sovereign_country_codes()
    )

@lru_cache(maxsize=1)
def _load_country_coordinates() -> dict:
    """Load precomputed country coordinates."""
    return json.loads(
        COUNTRY_COORDINATES_JSON.read_text(encoding="utf-8")
    )

@lru_cache(maxsize=256)
def country_coordinates(iso3: str) -> list[float] | None:
    """Return approximate map-marker coordinates for a country."""

    if iso3 in SPECIAL_COORDINATES:
        return SPECIAL_COORDINATES[iso3]

    coordinates = _load_country_coordinates()

    if iso3 in coordinates:
        return coordinates[iso3]

    # Existing CountryInfo fallback remains below.
    country = pycountry.countries.get(alpha_3=iso3)
    if country is None:
        return None

    try:
        return CountryInfo(country.name).latlng()
    except (KeyError, ValueError, AttributeError, TypeError):
        try:
            return CountryInfo(
                COUNTRY_DISPLAY_NAMES.get(iso3, iso3)
            ).latlng()
        except (KeyError, ValueError, AttributeError, TypeError):
            return None
        
def country_name(iso3: str, fallback: str | None = None) -> str:
    """Return a consistent display name for an ISO3 country code."""
    if iso3 in COUNTRY_DISPLAY_NAMES:
        return COUNTRY_DISPLAY_NAMES[iso3]

    country = pycountry.countries.get(alpha_3=iso3)
    if country:
        return country.name

    return fallback or iso3 or "Unknown territory"


@st.cache_data
def load_country_boundaries() -> dict:
    """Load and cache country boundaries for Litlas maps."""
    response = requests.get(COUNTRY_BOUNDARIES_URL, timeout=30)
    response.raise_for_status()
    return response.json()

@st.cache_data(show_spinner=False)
def load_simplified_country_boundaries() -> dict:
    """Load optimized country boundaries."""
    return json.loads(
        COUNTRY_BOUNDARIES_GEOJSON.read_text(encoding="utf-8")
    )


@st.cache_data(show_spinner=False)
def litlas_country_features() -> list[dict]:
    """Return Litlas country geometries with configured territory merges."""
    allowed = sovereign_country_codes()
    features = deepcopy(load_simplified_country_boundaries()["features"])

    for parent_iso, territories in TERRITORY_MERGES.items():
        parent = next(
            (
                f for f in features
                if f["properties"].get("ISO3166-1-Alpha-3") == parent_iso
            ),
            None,
        )

        if parent is None:
            raise ValueError(f"Parent country not found: {parent_iso}")

        matches = [
            f for f in features
            if (
                f["properties"].get("ISO3166-1-Alpha-3") in territories
                or f["properties"].get("name") in territories
            )
        ]

        if not matches:
            raise ValueError(f"Territory not found: {territories}")

        parent["geometry"] = mapping(
            unary_union([
                shape(parent["geometry"]),
                *(shape(f["geometry"]) for f in matches),
            ])
        )

    return [
        f for f in features
        if f["properties"].get("ISO3166-1-Alpha-3") in allowed
    ]
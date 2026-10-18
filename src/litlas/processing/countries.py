
"""
litlas.processing.countries
Shared country names for Litlas.
"""
import country_converter as coco
from functools import lru_cache
import pycountry
import requests
import streamlit as st
from countryinfo import CountryInfo

COUNTRY_BOUNDARIES_URL = (
    "https://raw.githubusercontent.com/"
    "datasets/geo-countries/master/data/countries.geojson"
)


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


def country_coordinates(iso3: str) -> list[float] | None:
    """Return approximate map-marker coordinates for a country."""

    if iso3 in SPECIAL_COORDINATES:
        return SPECIAL_COORDINATES[iso3]

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
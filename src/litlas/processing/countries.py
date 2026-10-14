
"""Shared country names for Litlas."""

import pycountry
import requests
import streamlit as st
from countryinfo import CountryInfo

COUNTRY_BOUNDARIES_URL = (
    "https://raw.githubusercontent.com/"
    "datasets/geo-countries/master/data/countries.geojson"
)


COUNTRY_NAMES = {
    "RUS": "Russia",
    "USA": "United States",
    "GBR": "United Kingdom",
    "KOR": "South Korea",
    "PRK": "North Korea",
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

COUNTRYINFO_ALIASES = {
    "USA": "United States",
    "GBR": "United Kingdom",
    "KOR": "South Korea",
    "RUS": "Russia",
    "CZE": "Czech Republic",
    "IRN": "Iran",
}


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
                COUNTRYINFO_ALIASES.get(iso3, iso3)
            ).latlng()
        except (KeyError, ValueError, AttributeError, TypeError):
            return None
        
def country_name(iso3: str, fallback: str | None = None) -> str:
    """Return a consistent display name for an ISO3 country code."""
    if iso3 in COUNTRY_NAMES:
        return COUNTRY_NAMES[iso3]

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
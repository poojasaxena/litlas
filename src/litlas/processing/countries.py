
"""Shared country names for Litlas."""

import pycountry


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


def country_name(iso3: str, fallback: str | None = None) -> str:
    """Return a consistent display name for an ISO3 country code."""
    if iso3 in COUNTRY_NAMES:
        return COUNTRY_NAMES[iso3]

    country = pycountry.countries.get(alpha_3=iso3)
    if country:
        return country.name

    return fallback or iso3 or "Unknown territory"

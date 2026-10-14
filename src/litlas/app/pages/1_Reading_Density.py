"""Reading-density choropleth map for Litlas."""

from copy import deepcopy
from math import log1p

import folium
import pycountry
import requests
import streamlit as st
from branca.colormap import LinearColormap
from streamlit_folium import st_folium
from branca.element import Element
from litlas.app.popups import pop_html
from litlas.app.ui import apply_page_style
from litlas.processing.core import load_config
from html import escape
from litlas.database.repository import (
    get_country_reading_density,
    load_read_books,
)

st.set_page_config(
    page_title="Reading Density · Litlas",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed",
)
apply_page_style()

st.title("🌍 Reading Density")
st.caption(
    "Countries shaded by the number of unique literary works "
    "you've read, based on authors' birthplaces."
)

# st.page_link("app.py", label="← Literary Atlas")


@st.cache_data
def load_boundaries():
    url = (
        "https://raw.githubusercontent.com/"
        "datasets/geo-countries/master/data/countries.geojson"
    )
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


density = get_country_reading_density()
books = load_read_books()

if density.empty:
    st.info("No countries with mapped literary works yet.")
    st.stop()

counts = dict(zip(density["iso3"], density["works"]))
max_count = max(counts.values())

# A logarithmic scale keeps high-volume countries from
# overwhelming countries represented by just a few works.
# Colour palettes, ordered from low to high reading density.
PALETTES = {
    "Cream → Gold → Terracotta": [
        "#f5eac9",
        "#e8c76c",
        "#d99b5a",
        "#bb6e50",
        "#7b3d45",
    ],
    "Yellow → Teal → Deep Blue": [
        "#f4e7a1",
        "#c7dfad",
        "#78bca9",
        "#397e92",
        "#254c70",
    ],
    "Mint → Yellow → Forest Green": [
        "#cceadd",
        "#e6e59a",
        "#dfb965",
        "#75a886",
        "#235b49",
    ],
}

palette_name = st.sidebar.selectbox(
    "Map colour palette",
    options=list(PALETTES),
    index=0,
)

colors = LinearColormap(
    colors=PALETTES[palette_name],
    vmin=0,
    vmax=log1p(max_count),
)
config = load_config()
height = config.get("map", {}).get("height", 800)


def country_popup(country_books, country_name, count):
    """Build a scrollable popup listing authors and their works."""

    sections = []

    for author, author_books in sorted(
        country_books.groupby("Author"),
        key=lambda item: item[0].casefold(),
    ):
        entries = []

        for _, records in author_books.groupby("Work ID", sort=False):
            title = escape(str(records.iloc[0]["Work Title"]))

            entries.append(f'<div style="margin:4px 0 4px 12px">' f"{title}</div>")

        sections.append(
            f'<h4 style="margin:12px 0 5px">'
            f"{escape(str(author))}</h4>" + "".join(entries)
        )

    return (
        '<div style="font-family:system-ui,sans-serif;'
        "width:310px;max-height:350px;overflow-y:auto;"
        'color:#222">'
        f'<h3 style="margin:0 0 5px">{escape(country_name)}</h3>'
        f'<div style="color:#777;font-size:12px">'
        f"{count} unique works · "
        f'{country_books["Author"].nunique()} authors</div>'
        + "".join(sections)
        + "</div>"
    )


geojson = deepcopy(load_boundaries())

books_by_country = {iso: group for iso, group in books.groupby("ISO3")}

for feature in geojson["features"]:
    props = feature["properties"]
    iso = props.get("ISO3166-1-Alpha-3", "")
    count = int(counts.get(iso, 0))

    country = pycountry.countries.get(alpha_3=iso)
    name = (
        country.name
        if country
        else props.get("ADMIN") or props.get("name") or "Unknown territory"
    )

    if name == "-99":
        name = "Unknown territory"

    if iso == "KOR":
        name = "South Korea"
    elif iso == "PRK":
        name = "North Korea"
    elif iso == "RUS":
        name = "Russia"

    props["litlas_country"] = name
    props["litlas_works"] = count
    if count > 0 and iso in books_by_country:
        props["litlas_popup"] = pop_html(
            books_by_country[iso],
            name,
            iso,
        )
    else:
        props["litlas_popup"] = (
            f"<strong>{escape(str(name))}</strong>" "<div>No mapped works</div>"
        )

m = folium.Map(
    location=[15, 0],
    zoom_start=2,
    tiles="OpenStreetMap",
    control_scale=True,
    world_copy_jump=True,
)


m.get_root().header.add_child(Element("""
<style>
    /* Remove popup pointer */
    .leaflet-popup-tip-container,
    .leaflet-popup-tip {
        display: none !important;
    }

    /* Remove tooltip pointer */
    .leaflet-tooltip::before,
    .leaflet-tooltip::after {
        display: none !important;
    }

    /* Keep popup corners rounded */
    .leaflet-popup-content-wrapper {
        border-radius: 12px !important;
    }
</style>
"""))

m.fit_bounds([[-55, -170], [75, 180]])


def style_country(feature):
    props = feature["properties"]
    count = props["litlas_works"]

    return {
        "fillColor": (colors(log1p(count)) if count > 0 else "#f0f0f0"),
        "fillOpacity": 0.8 if count > 0 else 0.25,
        "color": "transparent",
        "weight": 0,
        "opacity": 0,
    }


layer = folium.GeoJson(
    geojson,
    name="Reading density",
    style_function=style_country,
).add_to(m)


folium.GeoJsonPopup(
    fields=["litlas_popup"],
    labels=False,
    localize=False,
    max_width=400,
    style=(
        "border:0;"
        "font-family:system-ui,sans-serif;"
        "font-size:12px;"
        "line-height:1.35;"
    ),
).add_to(layer)


st_folium(
    m,
    height=height,
    use_container_width=True,
    returned_objects=[],
    key="reading_density",
)

st.markdown("**Reading density — unique works**")

# Display the legend using actual work counts, not logarithmic values.
legend_counts = [1, 5, 15, 50, max_count]

legend_html = """
<div style="font-family: sans-serif; max-width: 600px;">
    <div style="display: flex; height: 18px;">
"""

for count in legend_counts:
    legend_html += f'<div style="flex:1; background:{colors(log1p(count))};"></div>'

legend_html += """
    </div>
    <div style="display:flex; justify-content:space-between;
                font-size:12px; margin-top:5px;">
"""

for count in legend_counts:
    legend_html += f"<span>{count}</span>"

legend_html += "</div></div>"

st.components.v1.html(legend_html, height=55)
st.caption(
    f"{len(density)} countries represented · "
    "Unique works counted once per country · "
    "Colour intensity uses a logarithmic scale."
)

"""Minimal interactive literary map. Run: streamlit run app.py"""

import pandas as pd
import streamlit as st
import folium
from branca.element import Element

from streamlit_folium import st_folium
from litlas.processing.paths import load_config
from litlas.app.popups import flag, pop_html
from litlas.database.connection import database_path
from litlas.db_backend import get_repository, is_postgres
from litlas.app.ui import apply_page_style, render_page_header
from litlas.app.map_style import (
    create_litlas_map,
    LAND_COLOR,
    BORDER_COLOR,
    EXPLORED_COLOR,
)
from litlas.processing.countries import (
    country_name,
    country_coordinates,
    load_simplified_country_boundaries,
)
from litlas.app.visualizations.unexplored_lands import (
    add_unexplored_lands_control,
)

## Configuration constants for the map and flag display
config = load_config()
map_config = config.get("map", {})

FLAG_SIZE = map_config.get("flag_size", 14)
MAP_HEIGHT = map_config.get("height", 800)

st.set_page_config(page_title='Literary Atlas',page_icon='🌍',layout='wide',initial_sidebar_state='collapsed')
apply_page_style()

render_page_header(
    "Literary Atlas",
    "A journey through literature and geography...",
    illustration="literary_atlas",
    illustration_size=220,
)


# SQLite requires a local database file; PostgreSQL does not.
if not is_postgres():
    source = database_path()

    if not source.is_file():
        st.warning("Litlas database not found. Initialise and import the database first.")
        st.stop()

try:
    books = get_repository().load_read_books()
except Exception as exc:
    st.error("Could not read the Litlas database.")
    st.stop()

books["My Rating"] = pd.to_numeric(books["My Rating"], errors="coerce").fillna(0)

mapped = books[books["ISO3"].astype(bool)].copy()

m = create_litlas_map()

## Highlight countries that have been read
read_countries = set(mapped["ISO3"].unique())


## Load country boundaries for the map
geojson = load_simplified_country_boundaries()

for feature in geojson["features"]:
    iso = feature["properties"].get("ISO3166-1-Alpha-3")

    if iso:
        feature["properties"]["litlas_country_name"] = country_name(iso)
    else:
        feature["properties"]["litlas_country_name"] = "Unknown"


folium.GeoJson(
    geojson,
    name="Countries explored",
    style_function=lambda feature: {
        "fillColor": (
            EXPLORED_COLOR
            if feature["properties"].get("ISO3166-1-Alpha-3") in read_countries
            else LAND_COLOR
        ),
        "fillOpacity": 1,
        "color": BORDER_COLOR,
        "weight": 0.5,
        "opacity": 1,
    },
    tooltip=folium.GeoJsonTooltip(
        fields=["litlas_country_name"],
        aliases=[""],
        labels=False,
        sticky=True,
    ),
).add_to(m)

placed = 0

for iso, group in mapped.groupby("ISO3", sort=True):
    position = country_coordinates(iso)

    if not position:
        continue

    name = country_name(iso)

    html = f"""
    <div style="
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: {FLAG_SIZE}px;
        line-height: 1;
    ">
        {flag(iso)}
    </div>
    """

    popup_content = pop_html(group, name, iso)

    folium.Marker(
        location=position,
        icon=folium.DivIcon(
            html=html,
            class_name="",
            icon_size=(20, 20),
            icon_anchor=(10, 10),
        ),
        popup=folium.Popup(
            popup_content,
            max_width=400,
            auto_pan=True,
            auto_pan_padding_top_left=(95, 85),
            auto_pan_padding_bottom_right=(15, 15),
        ),
        tooltip=name,
    ).add_to(m)

    placed += 1



folium.LayerControl(position="topright").add_to(m)

add_unexplored_lands_control(
    m,
    read_countries,
)

# -------------------------------------------------
# Literary Journey — compact map information panel
# -------------------------------------------------

TOTAL_COUNTRIES = 195

explored_count = len(read_countries)
unexplored_count = max(0, TOTAL_COUNTRIES - explored_count)

journey_html = f"""
<div style="
    position:fixed;
    bottom:4px;
    right:4px;
    width:160px;
    padding:6px 8px;
    background:rgba(250,247,241,0.93);
    border:1px solid #D4C1A7;
    border-radius:7px;
    box-shadow:0 2px 8px rgba(0,0,0,0.12);
    z-index:1000;
    font-family:Georgia,serif;
    color:#58412F;
    pointer-events:none;
">
    <div style="
        font-size:14px;
        font-style:italic;
        text-align:center;
        margin-bottom:0;
    ">
        My Literary Journey
    </div>

    <div style="
        display:flex;
        justify-content:space-around;
        text-align:center;
    ">
        <div>
            <div style="font-size:23px;color:#8B634B;">
                {explored_count}
            </div>
            <div style="font-size:11px;color:#81776E;">
                Explored
            </div>
        </div>

        <div>
            <div style="font-size:23px;color:#8B634B;">
                {unexplored_count}
            </div>
            <div style="font-size:11px;color:#81776E;">
                Awaiting
            </div>
        </div>
    </div>

</div>
"""

m.get_root().html.add_child(Element(journey_html))


st_folium(
    m,
    height=MAP_HEIGHT,
    width="stretch",
    returned_objects=[],
    key="literarymap",
)

if mapped.empty:
    st.info('No author birth countries assigned yet. Run `litlas-prepare` in your terminal, then refresh this page.')
elif placed==0:
    st.warning('Authors have country codes, but map coordinates were unavailable. Check Vault/Personal/Learning/Library/authors.csv.')

missing=books.loc[~books['ISO3'].astype(bool),'Author'].nunique()
#st.caption(f'{len(books)} read books · {books["Author"].nunique()} authors · {placed} mapped countries · {missing} authors still without a mapped birth country. Birth-country matches are provisional until reviewed.')

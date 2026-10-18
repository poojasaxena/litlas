"""Minimal interactive literary map. Run: streamlit run app.py"""

import pandas as pd
import streamlit as st
import folium

from streamlit_folium import st_folium
from litlas.processing.paths import load_config
from litlas.app.popups import flag, pop_html
from litlas.database.connection import database_path
from litlas.database.repository import load_read_books
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
    load_country_boundaries,
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

# st.page_link(
#     "pages/1_Reading_Density.py",
#     label="🌍 Explore reading density",
# )
# st.page_link(
#     "pages/2_Author_Review.py",
#     label="📚 Review author birthplaces",
# )
# st.page_link(
#     "pages/3_Reading_Statistics.py",
#     label="📊 Explore reading statistics",
# )

# Load the literary map data from SQLite.
source = database_path()

if not source.is_file():
    st.warning("Litlas database not found. Initialise and import the database first.")
    st.stop()


try:
    books = load_read_books()
except Exception as exc:
    st.error(f"Could not read Litlas database: {exc}")
    st.stop()

books["My Rating"] = pd.to_numeric(books["My Rating"], errors="coerce").fillna(0)

mapped = books[books["ISO3"].astype(bool)].copy()


m = folium.Map(
    location=[15, 0],
    zoom_start=2,
    tiles=None,
    control_scale=True,
    prefer_canvas=False,
    world_copy_jump=True,
    zoom_control=True,
)

m = create_litlas_map()

## Highlight countries that have been read
read_countries = set(mapped["ISO3"].unique())


## Load country boundaries for the map
geojson = load_country_boundaries()

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
).add_to(m)

# cluster=MarkerCluster(name='Countries',disableClusteringAtZoom=4,showCoverageOnHover=False).add_to(m)
placed=0
for iso, group in mapped.groupby('ISO3',sort=True):
    position = country_coordinates(iso)
    if not position: continue
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

    folium.Marker(
        location=position,
        icon=folium.DivIcon(
            html=html,
            class_name="",
            icon_size=(20, 20),
            icon_anchor=(10, 10),
        ),
        popup=folium.Popup(
            pop_html(group, name, iso),
            max_width=400,
        ),
        tooltip=name,
    ).add_to(m)
    placed+=1

folium.LayerControl(position="topright").add_to(m)

add_unexplored_lands_control(
    m,
    read_countries,
)

st_folium(
    m,
    height=MAP_HEIGHT,
    use_container_width=True,
    returned_objects=[],
    key="literarymap",
)

if mapped.empty:
    st.info('No author birth countries assigned yet. Run `litlas-prepare` in your terminal, then refresh this page.')
elif placed==0:
    st.warning('Authors have country codes, but map coordinates were unavailable. Check Vault/Personal/Learning/Library/authors.csv.')

missing=books.loc[~books['ISO3'].astype(bool),'Author'].nunique()
st.caption(f'{len(books)} read books · {books["Author"].nunique()} authors · {placed} mapped countries · {missing} authors still without a mapped birth country. Birth-country matches are provisional until reviewed.')

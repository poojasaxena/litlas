"""Minimal interactive literary map. Run: streamlit run app.py"""

import pandas as pd
import streamlit as st
import folium

from streamlit_folium import st_folium
from countryinfo import CountryInfo
import pycountry
from litlas.processing.core import load_config
from litlas.app.popups import flag, pop_html
from litlas.database.connection import database_path
from litlas.database.repository import load_read_books
from litlas.app.ui import apply_page_style, render_page_header
from litlas.app.map_style import apply_map_style
from litlas.processing.countries import country_name
from litlas.processing.countries import country_name, load_country_boundaries

## Configuration constants for the map and flag display
config = load_config()
map_config = config.get("map", {})

FLAG_SIZE = map_config.get("flag_size", 14)
MAP_HEIGHT = map_config.get("height", 800)
COUNTRY_FILL = map_config.get("country_fill", "#82BFA0")
COUNTRY_OPACITY = map_config.get("country_opacity", 0.25)


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

# Approximate marker anchors; CountryInfo includes packaged offline geographic coordinates.
SPECIAL={'XKX':[42.6,21.0], 'TWN':[23.7,121.0], 'PSE':[31.9,35.2]}
def locate(iso):
    if iso in SPECIAL:return SPECIAL[iso]
    try:
        country=pycountry.countries.get(alpha_3=iso)
        if country is None:return None
        return CountryInfo(country.name).latlng()
    except (KeyError,ValueError,AttributeError,TypeError):
        try:
            aliases={'USA':'United States','GBR':'United Kingdom','KOR':'South Korea','RUS':'Russia', 'CZE':'Czech Republic', 'IRN':'Iran'}
            return CountryInfo(aliases.get(iso,iso)).latlng()
        except (KeyError,ValueError,AttributeError,TypeError):return None


m = folium.Map(
    location=[15, 0],
    zoom_start=2,
    tiles=None,
    control_scale=True,
    prefer_canvas=False,
    world_copy_jump=True,
    zoom_control=True,
)
apply_map_style(m)

m.fit_bounds([[-55, -170], [75, 180]])
read_countries = set(mapped["ISO3"].unique())

geojson = load_country_boundaries()

folium.GeoJson(
    geojson,
    name="Countries explored",
    style_function=lambda feature: {
        "fillColor": (
            "#B5A17F"
            if feature["properties"].get("ISO3166-1-Alpha-3") in read_countries
            else "#F6F0E6"
        ),
        "fillOpacity": 1,
        "color": "#C9BBA6",
        "weight": 0.5,
        "opacity": 1,
    },
).add_to(m)

# cluster=MarkerCluster(name='Countries',disableClusteringAtZoom=4,showCoverageOnHover=False).add_to(m)
placed=0
for iso, group in mapped.groupby('ISO3',sort=True):
    position=locate(iso)
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
folium.LayerControl(position='topright').add_to(m)
st_folium(m,height=MAP_HEIGHT,use_container_width=True,returned_objects=[],key='literarymap')
frame_css = {
    "Minimal Frame": """
        border: 1px solid #B7A48A;
        border-radius: 3px;
        box-shadow: 0 2px 5px rgba(85, 63, 42, 0.08);
    """,
    "Vintage Card": """
        border: 1px solid #B7A48A;
        border-radius: 12px;
        box-shadow: 0 10px 24px rgba(85, 63, 42, 0.16);
    """,
    "Mounted Parchment": """
        border: 1px solid #B7A48A;
        border-radius: 4px;
        box-shadow:
            0 0 0 6px #F3EDE3,
            0 0 0 7px #B7A48A,
            0 9px 22px 7px rgba(85, 63, 42, 0.13);
    """,
}

if mapped.empty:
    st.info('No author birth countries assigned yet. Run `litlas-prepare` in your terminal, then refresh this page.')
elif placed==0:
    st.warning('Authors have country codes, but map coordinates were unavailable. Check Vault/Personal/Learning/Library/authors.csv.')

missing=books.loc[~books['ISO3'].astype(bool),'Author'].nunique()
st.caption(f'{len(books)} read books · {books["Author"].nunique()} authors · {placed} mapped countries · {missing} authors still without a mapped birth country. Birth-country matches are provisional until reviewed.')

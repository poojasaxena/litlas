"""Minimal interactive literary map. Run: streamlit run app.py"""
from html import escape
from pathlib import Path
import pandas as pd
import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from countryinfo import CountryInfo
import pycountry
from litlas.core import load_config
from litlas.database.connection import database_path
from litlas.database.repository import load_read_books
import requests
from litlas.popups import flag, pop_html
from litlas.ui import apply_page_style


## Configuration constants for the map and flag display
config = load_config()
map_config = config.get("map", {})

FLAG_SIZE = map_config.get("flag_size", 14)
MAP_HEIGHT = map_config.get("height", 800)
COUNTRY_FILL = map_config.get("country_fill", "#82BFA0")
COUNTRY_OPACITY = map_config.get("country_opacity", 0.25)


@st.cache_data
def load_country_boundaries():
    url = (
        "https://raw.githubusercontent.com/"
        "datasets/geo-countries/master/data/countries.geojson"
    )
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


st.set_page_config(page_title='Literary Atlas',page_icon='🌍',layout='wide',initial_sidebar_state='collapsed')
apply_page_style()

st.title('🌍 Literary Atlas')
st.caption('A world of books, mapped by author birthplaces')
st.page_link(
    "pages/1_Reading_Density.py",
    label="🌍 Explore reading density",
)
st.page_link(
    "pages/2_Author_Review.py",
    label="📚 Review author birthplaces",
)


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
    tiles="OpenStreetMap",
    control_scale=True,
    prefer_canvas=False,
    world_copy_jump=True,
    zoom_control=True,
)

m.fit_bounds([[-55, -170], [75, 180]])
read_countries = set(mapped["ISO3"].unique())

geojson = load_country_boundaries()

folium.GeoJson(
    geojson,
    name="Countries explored",
    style_function=lambda feature: {
        "fillColor": (
            COUNTRY_FILL
            if feature["properties"].get("ISO3166-1-Alpha-3") in read_countries
            else "transparent"
        ),
        "fillOpacity": (
            COUNTRY_OPACITY
            if feature["properties"].get("ISO3166-1-Alpha-3") in read_countries
            else 0
        ),
        "color": "#8A9A9F",
        "weight": 0.4,
        "opacity": 0.5,
    },
).add_to(m)

# cluster=MarkerCluster(name='Countries',disableClusteringAtZoom=4,showCoverageOnHover=False).add_to(m)
placed=0
for iso,group in mapped.groupby('ISO3',sort=True):
    position=locate(iso)
    if not position: continue
    c=pycountry.countries.get(alpha_3=iso)
    name=(c.name if c else iso)
    if iso=='USA':name='United States'
    if iso=='GBR':name='United Kingdom'

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
if mapped.empty:
    st.info('No author birth countries assigned yet. Run `litlas-prepare` in your terminal, then refresh this page.')
elif placed==0:
    st.warning('Authors have country codes, but map coordinates were unavailable. Check Vault/Personal/Learning/Library/authors.csv.')
missing=books.loc[~books['ISO3'].astype(bool),'Author'].nunique()
st.caption(f'{len(books)} read books · {books["Author"].nunique()} authors · {placed} mapped countries · {missing} authors still without a mapped birth country. Birth-country matches are provisional until reviewed.')

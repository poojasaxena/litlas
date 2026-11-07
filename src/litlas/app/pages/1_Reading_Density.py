"""Reading-density choropleth map for Litlas."""

from copy import deepcopy
from math import log1p

from branca.element import Element
import folium
import streamlit as st
from branca.colormap import LinearColormap
from streamlit_folium import st_folium
import json
from pathlib import Path

from litlas.app.map_style import get_map_height
from litlas.app.popups import pop_html
from litlas.processing.paths import load_config
from html import escape
from litlas.db_backend import get_repository, backend_name
from litlas.app.map_style import (
    create_litlas_map,
    LAND_COLOR,
    BORDER_COLOR,
    DENSITY_COLORS,
)
from litlas.processing.countries import load_simplified_country_boundaries, country_name, load_country_boundaries
from litlas.app.ui import apply_page_style, render_page_header

st.set_page_config(
    page_title="Reading Density · Litlas",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed",
)
apply_page_style()


render_page_header(
    "Reading Density",
    "Where literature meets geography",
    illustration="reading_density",

    # Desktop — unchanged
    illustration_size=160,
    illustration_top=-20,
    illustration_left=0,
    heading_gap=20,
    title_height=95,
    ornament_width=170,

    # Mobile
    mobile_illustration_size=60,
    mobile_illustration_top=-4,

    mobile_eyebrow_offset_x=-20,
    mobile_heading_gap=8,
    mobile_heading_offset_x=-5,
    mobile_title_width=290,
    mobile_title_offset_x=-10,
    mobile_ornament_width=180,
    mobile_ornament_offset_x=-10,
    mobile_subtitle_offset_x=-17,

    mobile_header_bottom_gap=-10,
)

@st.cache_data(ttl=60, show_spinner=False)
def load_density_data(backend):
    repo = get_repository()
    return (
        repo.get_country_reading_density(),
        repo.load_read_books(),
    )
    
density, books = load_density_data(backend_name())

if density.empty:
    st.info("No countries with mapped literary works yet.")
    st.stop()

counts = dict(zip(density["iso3"], density["works"]))
max_count = max(counts.values())

colors = LinearColormap(
    colors=DENSITY_COLORS,
    vmin=0,
    vmax=log1p(max_count),
)

config = load_config()

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

geojson = load_simplified_country_boundaries()

books_by_country = {iso: group for iso, group in books.groupby("ISO3")}

for feature in geojson["features"]:
    props = feature["properties"]
    iso = props.get("ISO3166-1-Alpha-3", "")
    count = int(counts.get(iso, 0))

    fallback = props.get("ADMIN") or props.get("name")

    if fallback == "-99":
        fallback = None

    name = country_name(iso, fallback=fallback)

    props["litlas_country"] = name
    props["litlas_works"] = count
    props["litlas_country_name"] = name

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


m = create_litlas_map(mobile_focus=True)

def style_country(feature):
    count = feature["properties"]["litlas_works"]

    return {
        "fillColor": (
            colors(log1p(count))
            if count > 0
            else LAND_COLOR
        ),
        "fillOpacity": 1,
        "color": BORDER_COLOR,
        "weight": 0.5,
        "opacity": 1,
    }


layer = folium.GeoJson(
    geojson,
    name="Reading density",
    style_function=style_country,
    tooltip=folium.GeoJsonTooltip(
        fields=["litlas_country"],
        aliases=[""],
        labels=False,
        sticky=True,
    ),
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

# Compact reading-density legend inside the map
legend_counts = [1, 5, 15, 50, max_count]

legend_segments = "".join(
    f'<div style="flex:1;background:{colors(log1p(count))};"></div>'
    for count in legend_counts
)

legend_labels = "".join(
    f"<span>{count}</span>"
    for count in legend_counts
)

legend_html = f"""
<div class="litlas-density-legend" style="
    position:fixed;
    bottom:4px;
    right:4px;
    width:180px;
    padding:6px 8px;
    background:rgba(250,247,241,0.93);
    border:1px solid #D4C1A7;
    border-radius:7px;
    box-shadow:0 2px 8px rgba(0,0,0,0.12);
    z-index:1000;
    font-family:Georgia,serif;
    color:#58412F;
">
    <div style="font-size:13px;margin-bottom:7px;">
        Reading density
    </div>
    <div style="display:flex;height:12px;">
        {legend_segments}
    </div>
    <div style="
        display:flex;
        justify-content:space-between;
        font-size:11px;
        margin-top:4px;
    ">
        {legend_labels}
    </div>
</div>
"""
# Mobile styling for the Reading Density legend
m.get_root().header.add_child(Element("""
<style>
@media screen and (max-width: 640px) {
    .litlas-density-legend {
        bottom: 2px !important;
        right: 2px !important;
        width: 120px !important;
        padding: 5px 6px !important;
        box-sizing: border-box !important;
        background: rgba(250, 247, 241, 0.98) !important;
    }

    /* Title */
    .litlas-density-legend > div:first-child {
        font-size: 11px !important;
        margin-bottom: 5px !important;
    }

    /* Colour bar */
    .litlas-density-legend > div:nth-child(2) {
        height: 9px !important;
    }

    /* Legend numbers */
    .litlas-density-legend > div:last-child {
        font-size: 9px !important;
        margin-top: 3px !important;
    }
}
</style>
"""))

# Insert the legend into the Folium map
m.get_root().html.add_child(Element(legend_html))

# Render the map
st_folium(
    m,
    height=get_map_height(),
    width="stretch",
    returned_objects=[],
    key="reading_density",
)
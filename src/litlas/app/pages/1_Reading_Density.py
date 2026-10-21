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

from litlas.app.popups import pop_html
from litlas.processing.paths import load_config
from html import escape
from litlas.db_backend import get_repository, backend_name
from litlas.app.ui import apply_page_style, render_page_header
from litlas.app.map_style import (
    create_litlas_map,
    LAND_COLOR,
    BORDER_COLOR,
    DENSITY_COLORS,
)
from litlas.processing.countries import country_name
from litlas.processing.countries import country_name, load_country_boundaries
import time

_perf_start = time.perf_counter()
_perf_last = _perf_start

def perf(label):
    global _perf_last
    now = time.perf_counter()
    print(
        f"[DENSITY] {label:<30} "
        f"step={now - _perf_last:.3f}s  "
        f"total={now - _perf_start:.3f}s",
        flush=True,
    )
    _perf_last = now

st.set_page_config(
    page_title="Reading Density · Litlas",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed",
)
apply_page_style()


render_page_header(
    "Reading Density",
    "Where the pages I've turned meet the places they came from...",
    illustration="reading_density",
    illustration_size=170,
    illustration_top=-20,
    illustration_left=0,
    heading_gap=20,
)

@st.cache_data(ttl=60, show_spinner=False)
def load_density_data(backend):
    repo = get_repository()
    return (
        repo.get_country_reading_density(),
        repo.load_read_books(),
    )


density, books = load_density_data(backend_name())
perf("Database data loaded")

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


@st.cache_data(show_spinner=False)
def load_simplified_boundaries():
    path = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "countries_simplified.geojson"
    )
    return json.loads(path.read_text(encoding="utf-8"))
geojson = load_simplified_boundaries()
perf("Country boundaries loaded")

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

perf("Country GeoJSON processed")

m = create_litlas_map()
perf("Base map created")

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
).add_to(m)
perf("Folium GeoJSON layer created")

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
<div style="
    position:fixed;
    bottom:2px;
    right:2px;
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

m.get_root().html.add_child(Element(legend_html))

perf("Before st_folium")

# Temporary Folium performance diagnostics
render_start = time.perf_counter()
render_seconds = time.perf_counter() - render_start

print(
    f"[DENSITY] Folium HTML render: {render_seconds:.3f}s",
    flush=True,
)

print(
    f"[DENSITY] GeoJSON features: {len(geojson['features'])}",
    flush=True,
)
st_folium(
    m,
    height=height,
    use_container_width=True,
    returned_objects=[],
    key="reading_density",
)
perf("After st_folium")


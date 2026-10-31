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
from litlas.processing.paths import WELCOME_IMAGE, MOBILE_WELCOME_IMAGE
from litlas.processing.countries import (
    country_name,
    country_coordinates,
    sovereign_country_codes,
    litlas_country_features,
    load_simplified_country_boundaries
)
from litlas.app.visualizations.unexplored_lands import (
    add_unexplored_lands_control,
)

## Configuration constants for the map and flag display
config = load_config()
map_config = config.get("map", {})

FLAG_SIZE = map_config.get("flag_size", 14)
MAP_HEIGHT = 580


st.set_page_config(page_title='Literary Atlas',page_icon='🌍',layout='wide',initial_sidebar_state='collapsed')
apply_page_style()

render_page_header(
    "Literary Atlas",
    "A journey through literature and geography",
    illustration="literary_atlas",
    illustration_size=220,
    title_height=90,
    ornament_width=170,
)

if not st.session_state.get("litlas_welcome_dismissed", False):

    st.html("""
    <style>
    /* Shared welcome layout */
    .litlas-welcome-intro {
        max-width: 560px;
        margin: 0 auto 12px;
        font-family: Georgia, serif;
        text-align: center;
        color: #58412F;
        display: none;
    }

    .litlas-welcome-intro h2 {
        font-size: 28px !important;
        font-weight: 400;
        font-style: italic;
        margin: 0 0 10px;
    }

    .litlas-welcome-intro p {
        font-size: 16px;
        line-height: 1.5;
        color: #795740;
        margin: 0;
        margin-bottom: 4px;
    }

    /* Desktop: landscape illustration */
    .st-key-litlas_welcome_desktop_image {
        max-width: 780px;
        margin: 0 auto;
    }

    .st-key-litlas_welcome_mobile_image {
        display: none;
    }

    /* Instruction */
    .litlas-welcome-instruction {
        font-family: Georgia, serif;
        font-size: 14px;
        font-style: italic;
        color: #795740;
        text-align: center;
        margin: -35px auto 0;
    }

    /* Entry button */
    .st-key-litlas_enter_atlas button {
        background: #F5EFE4 !important;
        color: #58412F !important;
        border: 1px solid #B29A7C !important;
        border-radius: 6px !important;
        font-family: Georgia, serif !important;
    }

    .st-key-litlas_enter_atlas button p {
        color: #58412F !important;
        font-family: Georgia, serif !important;
    }

    .st-key-litlas_enter_atlas button:hover {
        background: #EDE2D2 !important;
        border-color: #96785D !important;
    }

    /* Mobile adjustments */
    @media screen and (max-width: 640px) {
        .litlas-welcome-intro {
            max-width: 340px;
        }

    .st-key-litlas_welcome_desktop_image {
        display: none !important;
    }

    .st-key-litlas_welcome_mobile_image {
        display: block !important;
        max-width: 320px;
        margin: 0 auto;
        margin-top: -60px !important;
    }

    /* Bring the entry button closer to the instruction */
    .st-key-litlas_enter_atlas {
        margin-top: -25px !important;
    }
    /* Compact, centred entry button on mobile */
    .st-key-litlas_enter_atlas {
        max-width: 190px !important;
        width: 100%;
        margin: -25px auto 0 !important;
    }

    .st-key-litlas_enter_atlas button {
        width: 100% !important;
        min-height: 40px !important;
        padding: 6px 14px !important;
    }

    }
    </style>
    """)

    left, centre, right = st.columns([1, 4, 1])

    with centre:

        st.html("""
        <div class="litlas-welcome-intro">
            <h2>Explore a World of Literature</h2>
            <p>
                Discover the books I've read, the authors I return to,
                and the countries that shape my reading journey.
            </p>
        </div>
        """)

        # Landscape illustration for desktop
        with st.container(key="litlas_welcome_desktop_image"):
            st.image(str(WELCOME_IMAGE), width="stretch")

        # Portrait illustration for mobile
        with st.container(key="litlas_welcome_mobile_image"):
            st.image(str(MOBILE_WELCOME_IMAGE), width="stretch")

        st.html("""
        <p class="litlas-welcome-instruction">
            Select a country's flag to explore its literary journey.
        </p>
        """)

        button_left, button_centre, button_right = st.columns([2, 2, 2])

        with button_centre:
            if st.button(
                "Enter Litlas ⟶",
                key="litlas_enter_atlas",
                use_container_width=True,
            ):
                st.session_state["litlas_welcome_dismissed"] = True
                st.rerun()

    st.stop()

    # Mobile welcome
    with st.container(key="litlas_mobile_welcome"):

        st.html("""
        <div class="litlas-mobile-intro">
            <h2>Explore a World of Literature</h2>
            <p>
                Discover the books I've read, the authors I return to,
                and the countries that shape my reading journey.
            </p>
        </div>
        """)

        st.image(str(MOBILE_WELCOME_IMAGE), width="stretch")

        st.html("""
        <p style="
            text-align:center;
            font-family:Georgia,serif;
            font-size:14px;
            font-style:italic;
            color:#795740;
            margin:4px auto 12px;
        ">
            Select a country's flag to explore its literary journey.
        </p>
        """)

        if st.button(
            "Enter Litlas ⟶",
            key="litlas_enter_atlas_mobile",
            use_container_width=True,
        ):
            st.session_state["litlas_welcome_dismissed"] = True
            st.rerun()

    st.stop()

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

m = create_litlas_map(mobile_focus=True)
#     fit_world=False,
#     initial_zoom=1,
# )

## Highlight countries that have been read
read_countries = (
    set(mapped["ISO3"].unique())
    & sovereign_country_codes()
)


## Load country boundaries for the map
geojson = {
    "type": "FeatureCollection",
    "features": litlas_country_features(),
}


for feature in geojson["features"]:
    iso = feature["properties"].get("ISO3166-1-Alpha-3")

    if iso and iso != "-99":
        feature["properties"]["litlas_country_name"] = country_name(iso)
    else:
        feature["properties"]["litlas_country_name"] = (
            feature["properties"].get("name") or "Unknown"
        )


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
            auto_pan_padding_top_left=(20, 20),
            auto_pan_padding_bottom_right=(65, 20),
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
<div class="litlas-journey-card" style="
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
m.get_root().header.add_child(Element("""
<style>
@media screen and (max-width: 640px) {
    .litlas-journey-card {
        bottom: 75px !important;
        right: 8px !important;
        width: 140px !important;
        padding: 5px 6px !important;
        box-sizing: border-box !important;
    }

    .litlas-journey-card > div:first-child {
        font-size: 12px !important;
    }

    .litlas-journey-card > div:nth-child(2) > div > div:first-child {
        font-size: 19px !important;
    }
}
</style>
"""))


# Discreet About Litlas invitation — above the map
st.html("""
<style>
.litlas-about-hint {
    font-family: Georgia, serif;
    font-size: 13px;
    font-style: italic;
    color: #896A50;
    text-align: left;
    white-space: nowrap;
    margin: 0;
    padding: 0;
    line-height: 1.2;
}

.litlas-about-hint a {
    color: #795740;
    font-weight: 600;
    text-decoration: none;
    margin-left: 5px;
}

.litlas-about-hint a:hover {
    text-decoration: underline;
}

@media screen and (max-width: 640px) {
    .litlas-about-hint {
        font-size: 10px;
    }
}
</style>

<div class="litlas-about-hint">
    Curious about the story behind this atlas?
    <a href="/About_Litlas">📖 About Litlas</a>
</div>
""")

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

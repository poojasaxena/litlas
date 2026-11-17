"""Reading-density choropleth map for Litlas."""

import streamlit as st
from streamlit_folium import st_folium

from litlas.app.map_style import create_litlas_map, get_map_height
from litlas.app.ui import apply_page_style, render_page_header
from litlas.app.visualizations.reading_density import add_reading_density
from litlas.db_backend import backend_name, get_repository

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
    illustration_size=230,
    illustration_top=-42,
    title_height=90,
    ornament_width=170,

    # Mobile illustration on the left
    mobile_illustration_size=100,
    mobile_illustration_top=0,  # Move the illustration up 4 px

    # Mobile layout of the text group
    mobile_heading_gap=0,         # Gap between the illustration and text columns
    mobile_heading_offset_x=-45, # Move the entire text group left 45 px

    # Individual elements, from top to bottom
    mobile_eyebrow_offset_x=6,   # Move the eyebrow right 2 px
    mobile_eyebrow_offset_y=-19,  # Move the eyebrow up 9 px
    mobile_title_width=290,      # Large decorative page title (Literary Atlas here)
    mobile_title_offset_x=17,
    mobile_title_offset_y=-12,  # Move the large Litlas lettering up 12 px
    mobile_ornament_width=120,   # Thin decorative line
    mobile_ornament_offset_x=12,
    mobile_ornament_offset_y=-12,  # Move the line up
    mobile_subtitle_offset_x=13, # Where stories meet the world
    mobile_subtitle_offset_y=-12,  # Move “Where stories meet the world” up
    mobile_header_bottom_gap=-14,  # Pull the mobile navigation up toward the header
)

@st.cache_data(ttl=60, show_spinner=False)
def load_density_data(backend):
    return get_repository().load_read_books()


m = create_litlas_map(mobile_focus=True)
if add_reading_density(m, load_density_data(backend_name())) is None:
    st.info("No countries with mapped literary works yet.")
    st.stop()

# Render the map
st_folium(
    m,
    height=get_map_height(),
    width="stretch",
    returned_objects=[],
    key="reading_density",
)
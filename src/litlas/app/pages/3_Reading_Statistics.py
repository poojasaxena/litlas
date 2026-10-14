"""Reading statistics for Litlas."""

import streamlit as st

from litlas.app.ui import apply_page_style, render_page_header
from litlas.database.repository import get_country_reading_density

st.set_page_config(
    page_title="Reading Statistics · Litlas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_page_style()

render_page_header(
    "📊 Reading Statistics",
    "Explore your literary journey through numbers and patterns.",
)

density = get_country_reading_density()

if density.empty:
    st.info("No reading statistics available yet.")
    st.stop()

# Convert country codes to display names.
import pycountry

density["country"] = density["iso3"].apply(
    lambda code: (
        pycountry.countries.get(alpha_3=code).name
        if pycountry.countries.get(alpha_3=code)
        else code
    )
)

density = density.sort_values("works", ascending=False)

st.subheader("Literary works by country")

st.bar_chart(
    density.head(15),
    x="country",
    y="works",
    horizontal=True,
    sort=False,
    x_label="Unique works",
    y_label="Country of author's birth",
)

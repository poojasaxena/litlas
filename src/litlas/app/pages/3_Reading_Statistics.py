"""Reading statistics for Litlas."""

import streamlit as st

from litlas.app.ui import apply_page_style, render_page_header
from litlas.database.repository import get_country_reading_density
from litlas.processing.countries import country_name
import plotly.graph_objects as go

st.set_page_config(
    page_title="Reading Statistics · Litlas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_page_style()

render_page_header(
    "Reading Statistics",
    "A life in books, told through numbers and patterns...",
    illustration="reading_statistics",
    illustration_size=175,
    illustration_top=-35,
    illustration_left=0,
    heading_gap=20,
)

density = get_country_reading_density()

if density.empty:
    st.info("No reading statistics available yet.")
    st.stop()


density["country"] = density["iso3"].apply(country_name)

density = density.sort_values("works", ascending=False)

st.subheader("Literary works by country")

top_density = density.head(15).copy()
top_density = top_density.sort_values("works", ascending=True)

# Vintage Litlas palette
base_bar = "#B79B74"
highlight_1 = "#6E4B3A"
highlight_2 = "#8B634B"
highlight_3 = "#A47B43"

bar_colors = [base_bar] * len(top_density)

if len(top_density) >= 1:
    bar_colors[-1] = highlight_1
if len(top_density) >= 2:
    bar_colors[-2] = highlight_2
if len(top_density) >= 3:
    bar_colors[-3] = highlight_3

fig = go.Figure(
    go.Bar(
        x=top_density["works"],
        y=top_density["country"],
        orientation="h",
        marker=dict(
            color=bar_colors,
            line=dict(color="#8E735B", width=1),
        ),
        text=top_density["works"],
        textposition="outside",
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Unique works: %{x}<extra></extra>"
        ),
    )
)

## Configure and render the Plotly bar chart for reading statistics by country
fig.update_layout(
    height=620,
    margin=dict(l=20, r=40, t=20, b=40),
    paper_bgcolor="#FAF7F1",
    plot_bgcolor="#F5EFE4",
    font=dict(
        family="Georgia, serif",
        size=14,
        color="#58412F",
    ),
    xaxis=dict(
        title="Unique works",
        title_font=dict(size=14, color="#58412F"),
        showgrid=True,
        gridcolor="#DDD2C2",
        zeroline=False,
        showline=False,
        tickfont=dict(color="#7A6553"),
    ),
    yaxis=dict(
        title="Country of author's birth",
        title_font=dict(size=14, color="#58412F"),
        showgrid=False,
        tickfont=dict(color="#58412F"),
    ),
    bargap=0.22,
)

st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

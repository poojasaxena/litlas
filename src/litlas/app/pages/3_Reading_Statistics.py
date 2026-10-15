"""Reading statistics for Litlas."""

import streamlit as st
import plotly.graph_objects as go
from html import escape
import numpy as np

from litlas.app.ui import apply_page_style, render_page_header
from litlas.database.repository import get_country_reading_density
from litlas.processing.countries import country_name
from litlas.database.repository import (
    get_country_reading_density,
    get_reading_summary,
    get_rating_distribution,
    get_books_read_by_year,
    get_top_authors,
)

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


summary = get_reading_summary()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Books read", summary["books"])

with col2:
    st.metric("Authors", summary["authors"])

with col3:
    st.metric("Countries explored", summary["countries"])

density = get_country_reading_density()

if density.empty:
    st.info("No reading statistics available yet.")
    st.stop()


density["country"] = density["iso3"].apply(country_name)

density = density.sort_values("works", ascending=False)

country_col, ratings_col = st.columns([3, 1], gap="large")

with country_col:
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
    height=420,
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

with country_col:
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False},
    )

# Ratings distribution
ratings = get_rating_distribution()

with ratings_col:
    st.subheader("My ratings")

if ratings.empty:
    st.info("No rated books available yet.")
else:
    fig_ratings = go.Figure(
        go.Bar(
            x=ratings["rating"],
            y=ratings["books"],
            marker=dict(
                color="#A98160",
                line=dict(color="#855C45", width=1),
            ),
            text=ratings["books"],
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                "<b>%{x} stars</b><br>"
                "%{y} books<extra></extra>"
            ),
        )
    )

    fig_ratings.update_layout(
        height=420,
        margin=dict(l=40, r=10, t=30, b=50),
        paper_bgcolor="#FAF7F1",
        plot_bgcolor="#EFE3D0",
        font=dict(
            family="Georgia, serif",
            size=11,
            color="#58412F",
        ),
        xaxis=dict(
            title=None,
            tickmode="array",
            tickvals=[1, 2, 3, 4, 5],
            ticktext=["1", "2", "3", "4", "5"],
            showgrid=False,
            zeroline=False,
        ),
        yaxis=dict(
            title=None,
            showgrid=True,
            gridcolor="#D1BEA4",
            zeroline=False,
        ),
        bargap=0.25,
        showlegend=False,
    )

    with ratings_col:
        st.plotly_chart(
            fig_ratings,
            use_container_width=True,
            config={"displayModeBar": False},
        )


# Reading history based on recorded Date Read values.
history_col, _ = st.columns([2, 1], gap="large")
history = get_books_read_by_year()

with history_col:
    st.subheader("Books Read Through the Years")

if history.empty:
    st.info("No books have a recorded reading date yet.")
else:
    fig_history = go.Figure(
        go.Bar(
            x=history["year"],
            y=history["books"],
            marker=dict(
                color="#A98160",
                line=dict(color="#855C45", width=1),
            ),
            text=history["books"],
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                "<b>%{x}</b><br>"
                "%{y} books read<extra></extra>"
            ),
        )
    )

    fig_history.update_layout(
        height=300,
        margin=dict(l=45, r=25, t=30, b=40),
        paper_bgcolor="#FAF7F1",
        plot_bgcolor="#F5EFE4",
        font=dict(
            family="Georgia, serif",
            size=13,
            color="#58412F",
        ),
        xaxis=dict(
            title=None,
            type="category",
            showgrid=False,
        ),
        yaxis=dict(
            title="Books",
            showgrid=True,
            gridcolor="#DDD2C2",
            zeroline=False,
            rangemode="tozero",
        ),
        bargap=0.35,
        showlegend=False,
    )

    with history_col:
        st.plotly_chart(
            fig_history,
            use_container_width=True,
            config={"displayModeBar": False},
        )

    dated_books = int(history["books"].sum())
    total_books = int(summary["books"])
    missing_dates = total_books - dated_books

    with history_col:
        st.caption(
            f"Based on {dated_books} books with recorded reading dates. "
            f"{missing_dates} books have no usable Date Read value. "
            "Years reflect recorded completion dates, not dates added to Goodreads."
        )


# Most-read authors, with average personal ratings.
top_authors = get_top_authors(limit=25)
st.divider()

most_read_col, favourite_col = st.columns([1, 1], gap="large")

with most_read_col:
    st.subheader("My Most-Read Authors")

    if top_authors.empty:
        st.info("No author statistics available yet.")

    else:
        rows = []

        for rank, (_, author) in enumerate(
            top_authors.iterrows(), start=1
        ):
            name = escape(str(author["author"]))
            books = int(author["books"])
            rated = int(author["rated_books"])

            rating = (
                f'{float(author["avg_rating"]):.1f}★'
                if rated > 0
                else "—"
            )

            rows.append(
                f"""
                <div style="
                    display:grid;
                    grid-template-columns:26px minmax(0,1fr) 40px 52px;
                    align-items:center;
                    gap:8px;
                    padding:9px 5px;
                    border-bottom:1px solid #D4C1A7;
                    font-family:Georgia,serif;
                    color:#58412F;
                    font-size:13px;
                ">
                    <span style="color:#A47B43;">
                        {rank:02d}
                    </span>
                    <span>{name}</span>
                    <span style="text-align:right;">
                        {books}
                    </span>
                    <span style="
                        text-align:right;
                        color:#A47B43;
                    ">
                        {rating}
                    </span>
                </div>
                """
            )

        from textwrap import dedent
        st.markdown(
            dedent("""
            <div style="
                background:#F5EFE4;
                border:1px solid #D4C1A7;
                border-radius:6px;
                padding:12px;
            ">
                <div style="
                    display:grid;
                    grid-template-columns:26px minmax(0,1fr) 40px 52px;
                    gap:8px;
                    padding:0 5px 8px;
                    border-bottom:2px solid #B29A7C;
                    font-family:Georgia,serif;
                    font-size:11px;
                    color:#81776E;
                ">
                    <span>#</span>
                    <span>Author</span>
                    <span style="text-align:right;">Books</span>
                    <span style="text-align:right;">Rating</span>
                </div>
            """)
            + "".join(dedent(row) for row in rows)
            + "</div>",
            unsafe_allow_html=True,
        )

        st.caption(
            "Ranked by books read. Average rating excludes unrated books."
        )

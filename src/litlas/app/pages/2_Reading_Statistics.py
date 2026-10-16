
"""Reading statistics for Litlas."""

from html import escape
from textwrap import dedent

import plotly.graph_objects as go
import streamlit as st

from litlas.app.ui import apply_page_style, render_page_header
from litlas.database.repository import (
    get_country_reading_density,
    get_reading_summary,
    get_rating_distribution,
    get_books_read_by_year,
    get_top_authors,
    get_page_statistics,
    get_yearly_highlights,
)
from litlas.processing.countries import country_name

# ---------------------------------------------------------
# Page setup
# ---------------------------------------------------------

st.set_page_config(
    page_title="Reading Statistics · Litlas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_page_style()


st.markdown("""
<style>
.litlas-mini-card {
    background: #F5EFE4;
    border: 1px solid #D4C1A7;
    border-radius: 8px;
    padding: 14px 18px 12px 18px;
    min-height: 128px;
}

.litlas-mini-card .label {
    font-family: Georgia, serif;
    font-size: 0.95rem;
    color: #9A8066;
    margin-bottom: 8px;
}

.litlas-mini-card .value {
    font-family: Georgia, serif;
    font-size: 1.15rem;
    font-weight: 700;
    color: #6E4B3A;
    margin-bottom: 6px;
    line-height: 1.2;
}

.litlas-mini-card .subline {
    font-family: Georgia, serif;
    font-size: 1.05rem;
    font-style: italic;
    color: #58412F;
    line-height: 1.35;
    margin-bottom: 2px;
}

.litlas-mini-card .meta {
    font-family: Georgia, serif;
    font-size: 0.95rem;
    color: #81776E;
    line-height: 1.3;
}

.litlas-mini-card .soft-note {
    font-family: Georgia, serif;
    font-size: 0.92rem;
    color: #81776E;
    line-height: 1.35;
    margin-top: 4px;
}

/* Reading Statistics — summary metrics */

[data-testid="stMetricLabel"] {
    font-family: Georgia, serif !important;
    color: #96785D !important;
}

[data-testid="stMetricValue"] {
    font-family: Georgia, serif !important;
    color: #6E4B3A !important;
    font-weight: 700 !important;
    font-size: 2rem !important;
}
/* Reading Statistics — prevent the header shifting upward */
[data-testid="stLayoutWrapper"]:has(
    > .st-key-litlas_sticky_header
) {
    top: 45px !important;
}
/* Reading Statistics — section headings */
[data-testid="stHeading"] h3 {
    font-family: "Cormorant Garamond", Georgia, serif !important;
    font-style: italic !important;
    font-size: 2rem !important;
    font-weight: 600 !important;
    color: #58412F !important;
}
</style>
""", unsafe_allow_html=True)

render_page_header(
    "Reading Statistics",
    "A life in books, told through numbers and patterns...",
    illustration="reading_statistics",
    illustration_size=180,
    illustration_top=-40,
    illustration_left=0,
    heading_gap=20,
)


# ---------------------------------------------------------
# Reading summary
# ---------------------------------------------------------

summary = get_reading_summary()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Books devoured", summary["books"])

with col2:
    st.metric("Authors discovered", summary["authors"])

with col3:
    st.metric("Countries explored", summary["countries"])


# ---------------------------------------------------------
# Page milestones
# ---------------------------------------------------------

# Retrieve page statistics from the database.
page_stats = get_page_statistics()

longest = page_stats["longest"]
shortest = page_stats["shortest"]
total_pages = page_stats["total_pages"]

def page_milestone(label, value, title="", author=""):
    """Compact, two-line vintage reading milestone."""

    detail = (
        f"<i>{escape(title)}</i>"
        + (f" · {escape(author)}" if author else "")
        if title else ""
    )

    st.html(
        f"""
        <div style="
            background:#F5EFE4;
            border:1px solid #D4C1A7;
            border-radius:7px;
            padding:9px 15px;
            font-family:Georgia,serif;
            color:#58412F;
        ">
            <div style="
                display:flex;
                align-items:baseline;
                justify-content:space-between;
                gap:10px;
                margin-bottom:5px;
            ">
                <span style="
                    font-size:13px;
                    color:#96785D;
                ">{escape(label)}</span>
                <strong style="
                    font-size:21px;
                    color:#6E4B3A;
                    white-space:nowrap;
                ">{escape(value)}</strong>
            </div>

            <div style="
                font-size:13px;
                line-height:1.3;
                overflow:hidden;
                text-overflow:ellipsis;
                white-space:nowrap;
                color:#58412F;
            " title="{escape(title, quote=True)}">
                {detail or "&nbsp;"}
            </div>
        </div>
        """
    )


longest_col, pages_col, shortest_col = st.columns(3, gap="medium")

with longest_col:
    page_milestone(
        "Longest Book",
        f"{longest['pages']:,} pages" if longest else "—",
        longest["title"] if longest else "",
        longest["author"] if longest else "",
    )

with pages_col:
    page_milestone(
        "Total Pages Read",
        f"{total_pages:,}",
        "A lifetime between pages",
    )

with shortest_col:
    page_milestone(
        "Shortest Book",
        f"{shortest['pages']:,} pages" if shortest else "—",
        shortest["title"] if shortest else "",
        shortest["author"] if shortest else "",
    )


# ---------------------------------------------------------
# Row 1: Country distribution and ratings
# ---------------------------------------------------------

country_col, ratings_col = st.columns([3, 1], gap="large")

density = get_country_reading_density()

with country_col:
    st.subheader("Literary works by country")

    if density.empty:
        st.info("No country statistics available yet.")
    else:
        density["country"] = density["iso3"].apply(country_name)

        top_density = (
            density.sort_values("works", ascending=False)
            .head(15)
            .sort_values("works", ascending=True)
            .copy()
        )

        bar_colors = ["#B79B74"] * len(top_density)

        if len(bar_colors) >= 1:
            bar_colors[-1] = "#6E4B3A"
        if len(bar_colors) >= 2:
            bar_colors[-2] = "#8B634B"
        if len(bar_colors) >= 3:
            bar_colors[-3] = "#A47B43"

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
                showgrid=True,
                gridcolor="#DDD2C2",
                zeroline=False,
                showline=False,
            ),
            yaxis=dict(
                title="Country of author's birth",
                showgrid=False,
            ),
            bargap=0.22,
            showlegend=False,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": False},
        )


ratings = get_rating_distribution()

with ratings_col:
    st.subheader("Ratings")

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

        st.plotly_chart(
            fig_ratings,
            use_container_width=True,
            config={"displayModeBar": False},
        )


# ---------------------------------------------------------
# Row 2: Reading history
# ---------------------------------------------------------

history_col, highlights_col = st.columns([2, 1], gap="large")

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

        st.plotly_chart(
            fig_history,
            use_container_width=True,
            config={"displayModeBar": False},
        )

        dated_books = int(history["books"].sum())
        missing_dates = int(summary["books"]) - dated_books

        st.caption(
            f"Based on {dated_books} books with recorded reading dates. "
            f"{missing_dates} books have no usable Date Read value."
        )

# ---------------------------------------------------------
# Yearly literary highlights
# ---------------------------------------------------------

with highlights_col:
    st.subheader("Literary Highlights")

    highlights = get_yearly_highlights()

    if highlights.empty:
        st.caption("No rated books with reading dates available.")
    else:
        rows = []

        for _, book in highlights.iterrows():
            year = escape(str(book["year"]))
            title = escape(str(book["title"]))
            author = escape(str(book["author"]))

            rating = float(book["rating"])
            whole_stars = int(rating)
            stars = "★" * whole_stars

            if rating - whole_stars >= 0.5:
                stars += "½"

            rows.append(
                f"""
                <div style="
                    display:flex;
                    align-items:baseline;
                    gap:10px;
                    padding:8px 0;
                    border-bottom:1px solid #E2D5C3;
                    font-family:Georgia,serif;
                ">
                    <span style="
                        color:#96785D;
                        font-size:13px;
                        white-space:nowrap;
                    ">{year}</span>

                    <span style="
                        flex:1;
                        min-width:0;
                        font-size:13px;
                        color:#58412F;
                        line-height:1.5;
                    ">
                        <i>{title}</i>
                        <span style="color:#81776E;">
                            · {author}
                        </span>
                    </span>

                    <span style="
                        color:#A47B43;
                        font-size:13px;
                        white-space:nowrap;
                    ">{stars}</span>
                </div>
                """
            )

        st.html("\n".join(rows))

    st.caption(
        "Highest-rated completed book per year. "
        "Ties resolved by completion date."
    )

# ---------------------------------------------------------
# Row 3: Author statistics
# ---------------------------------------------------------

st.divider()

most_read_col, favourite_col = st.columns([1, 1], gap="large")

# Get a sufficiently large pool of authors, not just the
# ten most-read, so favourite rankings are not biased.
all_authors = get_top_authors(limit=10000)

# ---------------------------------------------------------
# Most-read authors: quantity
# ---------------------------------------------------------

with most_read_col:
    st.subheader("My Most-Read Authors")

    if all_authors.empty:
        st.info("No author statistics available yet.")
    else:
        most_read = all_authors.head(10)

        rows = []

        for rank, (_, author) in enumerate(
            most_read.iterrows(), start=1
        )   :
            name = escape(str(author["author"]))
            books = int(author["books"])
            rated = int(author["rated_books"])

            rating = (
                f'{float(author["avg_rating"]):.1f}★'
                if rated > 0
                else "—"
            )

            rows.append(dedent(f"""
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
                <span style="color:#A47B43;">{rank:02d}</span>
                <span>{name}</span>
                <span style="text-align:right;">{books}</span>
                <span style="text-align:right;color:#A47B43;">
                    {rating}
                </span>
            </div>
            """))

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
            + "".join(rows)
            + "</div>",
            unsafe_allow_html=True,
        )

        st.caption(
            "Ranked by books read. Average rating excludes unrated books."
        )


# ---------------------------------------------------------
# Favourite authors: quality with reading confidence
# ---------------------------------------------------------

with favourite_col:
    st.subheader("My Favourite Authors")

    # Only include authors with at least two rated books.
    favourites = all_authors[
        all_authors["rated_books"] >= 2
    ].copy()

    if favourites.empty:
        st.info("Not enough rated authors yet.")
    else:
        # Confidence-adjusted average:
        # Three hypothetical 3-star books provide a neutral
        # starting point. Actual ratings gradually outweigh it.
        #
        # This prevents one or two 5-star books from
        # automatically dominating the ranking.
        prior_rating = 3.0
        prior_books = 3

        favourites["favourite_score"] = (
            favourites["avg_rating"] * favourites["rated_books"]
            + prior_rating * prior_books
        ) / (favourites["rated_books"] + prior_books)

        favourites = (
            favourites.sort_values(
                ["favourite_score", "rated_books", "author"],
                ascending=[False, False, True],
            )
            .head(5)
            .reset_index(drop=True)
        )

        roman_ranks = ["I", "II", "III", "IV", "V"]

        cards = []

        for i, author in favourites.iterrows():
            name = escape(str(author["author"]))
            books = int(author["books"])
            rated = int(author["rated_books"])
            average = float(author["avg_rating"])
            score = float(author["favourite_score"])

            # Visual indicator on a 0-5 scale.
            score_width = min(100, max(0, score / 5 * 100))

            cards.append(dedent(f"""
            <div style="
                background:#F5EFE4;
                border:1px solid #D4C1A7;
                border-radius:7px;
                padding:13px 16px;
                margin-bottom:10px;
                font-family:Georgia,serif;
                color:#58412F;
            ">
                <div style="
                    display:flex;
                    align-items:center;
                    justify-content:space-between;
                    gap:10px;
                ">
                    <span style="
                        font-size:18px;
                        font-weight:bold;
                    ">{name}</span>

                    <span style="
                        font-size:19px;
                        font-style:italic;
                        color:#A47B43;
                    ">{roman_ranks[i]}</span>
                </div>

                <div style="
                    display:flex;
                    justify-content:space-between;
                    gap:10px;
                    margin-top:7px;
                    font-size:13px;
                    color:#81776E;
                ">
                    <span>{books} books · {rated} rated</span>
                    <span style="color:#A47B43;">
                        {average:.1f}★ average
                    </span>
                </div>

                <div style="
                    background:#E2D5C3;
                    height:5px;
                    margin-top:12px;
                    border-radius:4px;
                    overflow:hidden;
                ">
                    <div style="
                        width:{score_width:.1f}%;
                        height:100%;
                        background:#A47B43;
                    "></div>
                </div>
            </div>
            """).strip())


        st.html("\n".join(cards))

        st.caption(
            "Ranked by confidence-adjusted average rating. "
            "At least two rated books required; more ratings "
            "give greater confidence in the score."
        )


"""Reading statistics for Litlas."""

from html import escape
from textwrap import dedent

import plotly.graph_objects as go
import pandas as pd
import streamlit as st
from pathlib import Path
from litlas.app.ui import apply_page_style, render_page_header

from litlas.processing.paths import default_constellation_csv
from litlas.app.visualizations.book_spines import (
    build_rating_spines_figure,
    build_year_spines_figure,
)
from litlas.processing.countries import country_name
from litlas.app.visualizations.constellation import (
    load_constellation_books,
    build_constellation_figure,
)
from litlas.app.visualizations.rating_popup import render_rating_popup
from litlas.app.nobel import match_nobel_authors, load_literature_laureates
from litlas.app.visualizations.book_of_honour import render_book_of_honour
from litlas.app.visualizations.wanderlust import build_wanderlust_figure

from litlas.db_backend import get_repository

from time import perf_counter

PAGE_START = perf_counter()

def perf_checkpoint(label):
    elapsed = perf_counter() - PAGE_START
    print(f"[LITLAS CLOUD PERF] {label}: {elapsed:.2f}s", flush=True)

repository = get_repository()
get_favourite_authors = repository.get_favourite_authors
get_country_reading_density = repository.get_country_reading_density
get_reading_summary = repository.get_reading_summary
get_rating_distribution = repository.get_rating_distribution
get_books_read_by_year = repository.get_books_read_by_year
get_top_authors = repository.get_top_authors
get_page_statistics = repository.get_page_statistics
get_books_for_reading_year = repository.get_books_for_reading_year
get_books_for_rating = repository.get_books_for_rating
get_yearly_highlights = repository.get_yearly_highlights
get_constellation_book_details = repository.get_constellation_book_details
get_literary_wanderlust = repository.get_literary_wanderlust


@st.cache_data(ttl=3600, show_spinner=False)
def load_popup_books(read_books):
    books_by_rating = {}
    books_by_year = {}

    for _, book in read_books.iterrows():
        title = str(book["Display Title"])
        author = str(book["Author"])

        rating = (
            float(book["My Rating"])
            if pd.notna(book["My Rating"])
            else 0
        )

        stars = "★" * int(rating)
        if rating % 1 >= 0.5:
            stars += "½"

        entry = {
            "title": title,
            "author": author,
            "stars": stars or "—",
        }

        # Rating popup
        if pd.notna(book["My Rating"]):
            key = f"{rating:g}"
            books_by_rating.setdefault(key, []).append(entry)

        # Reading-year popup
        date_read = book["Date Read"]

        if pd.notna(date_read) and str(date_read).strip():
            year = str(date_read)[:4]
            books_by_year.setdefault(year, []).append(
                (str(date_read).replace("/", "-"), title.lower(), entry)
            )

    # Preserve the reading-year SQL ordering.
    for year, entries in books_by_year.items():
        entries.sort(key=lambda item: item[1])
        entries.sort(key=lambda item: item[0], reverse=True)
        books_by_year[year] = [entry for _, _, entry in entries]

    return books_by_rating, books_by_year

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

/* Literary year dialog — parchment styling */
div[data-testid="stDialog"] [role="dialog"],
div[role="dialog"]:has(.st-key-litlas_year_books) {
    background: #FAF7F1 !important;
    color: #58412F !important;
}

/* Dialog title */
div[role="dialog"]:has(.st-key-litlas_year_books, .st-key-litlas_rating_books)
[data-testid="stDialogHeader"] {
    padding-bottom: 0 !important;
}

div[role="dialog"]:has(.st-key-litlas_year_books, .st-key-litlas_rating_books)
[data-testid="stDialogHeader"] p,
div[role="dialog"]:has(.st-key-litlas_year_books, .st-key-litlas_rating_books)
[data-testid="stDialogHeader"] h2 {
    font-family: Georgia, serif !important;
    color: #58412F !important;
    font-size: 1.2rem !important;
}

/* Compact scrollable book list */
.st-key-litlas_year_books,
.st-key-litlas_rating_books {
    background: #F5EFE4 !important;
    border: 1px solid #D4C1A7 !important;
    border-radius: 7px !important;
    padding: 5px 12px !important;
}

/* Nobel statistic — self-contained, no Streamlit popover or modal */
.litlas-nobel-stat {
    position: relative;
    font-family: Georgia, serif;
    color: #58412F;
}

.litlas-nobel-stat summary {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    list-style: none;
    cursor: pointer;
    color: #96785D;
    font-family: Georgia, serif;
    font-size: 0.875rem;
    font-weight: 400;
    line-height: 1.5;
}

.litlas-nobel-stat summary::-webkit-details-marker {
    display: none;
}

.litlas-nobel-stat summary:focus-visible {
    outline: 2px solid #A47B43;
    outline-offset: 3px;
    border-radius: 3px;
}

.litlas-nobel-value {
    font-family: Georgia, serif;
    font-size: 2rem;
    font-weight: 700;
    line-height: 1.2;
    color: #6E4B3A;
    margin-top: 3px;
}

/* Anchored literary list — same visual language as Reading Year. */
.litlas-nobel-panel {
    position: absolute;
    top: 28px;
    right: 0;
    z-index: 1000;
    box-sizing: border-box;
    width: 280px;
    max-width: min(280px, calc(100vw - 24px));
    padding: 22px 24px 24px;
    background: #FAF7F1;
    border: 1px solid #E8DED0;
    border-radius: 15px;
    box-shadow: 0 8px 20px rgba(60, 40, 28, 0.14);
}

.litlas-nobel-title {
    font-family: Georgia, serif;
    font-size: 20px;
    font-weight: 600;
    line-height: 1.3;
    color: #58412F;
    margin: 0 0 14px;
}

/* Match the existing Reading Year panel's parchment and row styling. */
.litlas-nobel-list {
    height: 250px;
    overflow-y: auto;
    scrollbar-gutter: stable;
    background: #F5EFE4;
    border: 1px solid #D4C1A7;
    border-radius: 7px;
    padding: 5px 12px;
}

.litlas-nobel-author {
    padding: 5px 2px;
    border-bottom: 1px solid #E2D5C3;
    font-family: Georgia, serif;
    font-size: 13px;
    line-height: 1.3;
    color: #58412F;
}

.litlas-nobel-author:last-child {
    border-bottom: none;
}

.litlas-nobel-empty {
    font-family: Georgia, serif;
    font-size: 13px;
    color: #81776E;
    padding: 8px 2px;
}
.litlas-nobel-caption {
    font-family: Georgia, serif;
    font-size: 13px;
    font-weight: 400;
    color: #96785D;
    margin: 0 0 12px;
}
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

# Automatically compare completed-book authors with Nobel laureates.
start_books = perf_counter()

read_books = repository.load_read_books()
print(f"[LITLAS PERFORMANCE] Read books loaded: {perf_counter() - start_books:.2f}s", flush=True)

# Load cached popup books
start = perf_counter()

cached_ratings, cached_years = load_popup_books(read_books)

perf_checkpoint("Popup data loaded")
print(f"[LITLAS PERFORMANCE] Popup data: {perf_counter() - start:.2f}s", flush=True)

print(
    f"[LITLAS CLOUD PERF] load_read_books alone: "
    f"{perf_counter() - start_books:.2f}s",
    flush=True,
)
read_authors = read_books["Author"].dropna().unique()

nobel_authors = match_nobel_authors(read_authors)
nobel_data_available = bool(load_literature_laureates())

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Books devoured", summary["books"])

with col2:
    st.metric("Authors discovered", summary["authors"])

with col3:
    st.metric("Countries explored", summary["countries"])

with col4:
    if nobel_data_available:
        rows = "".join(
            f'<div class="litlas-nobel-author">'
            f'<span>{escape(author)}</span>'
            f'<span style="float:right;color:#A47B43;">{escape(str(year))}</span>'
            f'</div>'
            for author, year in nobel_authors
        )
        content = (
            f'<div class="litlas-nobel-list">{rows}</div>'
            if rows
            else '<div class="litlas-nobel-empty">No laureates identified yet.</div>'
        )
    else:
        content = (
            '<div class="litlas-nobel-empty">'
            'Laureate data is temporarily unavailable.'
            '</div>'
        )

    count = str(len(nobel_authors)) if nobel_data_available else "—"

    st.html(
        '<div class="litlas-nobel-stat">'
        '<details>'
        '<summary title="View Nobel laureates">'
        '<span aria-hidden="true">🏅</span>'
        '<span>Nobel Laureates Read</span>'
        '</summary>'
        '<div class="litlas-nobel-panel">'
        '<div class="litlas-nobel-title">Nobel Laureates</div>'
        '<div class="litlas-nobel-caption">'
        'Distinguished voices discovered'
        '</div>'
        f'{content}'
        '</div>'
        '</details>'
        f'<div class="litlas-nobel-value">{count}</div>'
        '</div>'
    )

# ---------------------------------------------------------
# Page milestones
# ---------------------------------------------------------

# Retrieve page statistics from the database.
page_stats = get_page_statistics()

longest = page_stats["longest"]
shortest = page_stats["shortest"]
total_pages = page_stats["total_pages"]

def make_book_spine_asset(
    name: str,
    base_color: str,
    edge_color: str,
    gold_color: str = "#D8B36A",
) -> str:
    """
    Create a decorative vertical book-spine PNG and return its file path.
    The image has a transparent background and can be placed inside Plotly.
    """
    out_dir = Path(".litlas_assets")
    out_dir.mkdir(exist_ok=True)

    path = out_dir / f"{name}_spine.png"
    if path.exists():
        return str(path)

    width = 180
    height = 900

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Main body
    x0, y0, x1, y1 = 20, 20, width - 20, height - 20
    draw.rounded_rectangle(
        [x0, y0, x1, y1],
        radius=18,
        fill=base_color,
        outline=edge_color,
        width=6,
    )

    # Left darker edge
    draw.rounded_rectangle(
        [x0, y0, x0 + 18, y1],
        radius=16,
        fill=edge_color,
    )

    # Right subtle highlight edge
    draw.rounded_rectangle(
        [x1 - 8, y0, x1, y1],
        radius=16,
        fill=(255, 255, 255, 35),
    )

    # Top and bottom bands
    band_h = 44
    draw.rounded_rectangle(
        [x0 + 10, y0 + 24, x1 - 10, y0 + 24 + band_h],
        radius=8,
        fill=None,
        outline=gold_color,
        width=4,
    )
    draw.rounded_rectangle(
        [x0 + 10, y1 - 24 - band_h, x1 - 10, y1 - 24],
        radius=8,
        fill=None,
        outline=gold_color,
        width=4,
    )

    # Center vertical gold strip
    cx = width // 2
    draw.rounded_rectangle(
        [cx - 3, y0 + 160, cx + 3, y1 - 160],
        radius=3,
        fill=gold_color,
    )

    # Decorative central frame
    frame_top = height * 0.36
    frame_bottom = height * 0.64
    draw.rounded_rectangle(
        [x0 + 30, frame_top, x1 - 30, frame_bottom],
        radius=12,
        fill=None,
        outline=gold_color,
        width=4,
    )

    # Little ornaments
    for yy in [height * 0.28, height * 0.50, height * 0.72]:
        draw.ellipse(
            [cx - 7, yy - 7, cx + 7, yy + 7],
            fill=gold_color,
        )
        draw.line(
            [cx - 18, yy, cx + 18, yy],
            fill=gold_color,
            width=3,
        )

    # Faint leather texture
    texture = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    tex_draw = ImageDraw.Draw(texture)
    for y in range(y0 + 12, y1 - 12, 18):
        alpha = 12 if (y // 18) % 2 == 0 else 8
        tex_draw.line(
            [(x0 + 12, y), (x1 - 12, y)],
            fill=(255, 255, 255, alpha),
            width=1,
        )
    texture = texture.filter(ImageFilter.GaussianBlur(0.6))
    img = Image.alpha_composite(img, texture)

    img.save(path)
    return str(path)

def add_rating_book_spines(fig, ratings):
    """Draw decorative book spines for each rating category."""

    leather_colors = [
        "#64735E",  # forest green
        "#98513D",  # burgundy leather
        "#4D657A",  # antique blue
        "#B18A53",  # tan leather
        "#69735B",  # olive
        "#8D6847",  # brown
        "#65506F",  # purple
    ]

    for index, (_, row) in enumerate(ratings.iterrows()):
        rating = float(row["rating"])
        count = float(row["books"])

        if count <= 0:
            continue

        width = 0.34
        x0 = rating - width / 2
        x1 = rating + width / 2

        color = leather_colors[index % len(leather_colors)]

        # Main leather-bound spine
        fig.add_shape(
            type="rect",
            x0=x0,
            x1=x1,
            y0=0,
            y1=count,
            fillcolor=color,
            line=dict(color="#5C4335", width=1.5),
            layer="above",
        )

        # Fine golden lines near the top and bottom
        band_offset = min(3, count * 0.15)

        for y in (band_offset, count - band_offset):
            fig.add_shape(
                type="line",
                x0=x0 + 0.035,
                x1=x1 - 0.035,
                y0=y,
                y1=y,
                line=dict(color="#D6B77B", width=1.5),
                layer="above",
            )

        # Narrow gold vertical decoration
        if count >= 10:
            fig.add_shape(
                type="line",
                x0=rating,
                x1=rating,
                y0=count * 0.30,
                y1=count * 0.70,
                line=dict(color="#C8A66C", width=1),
                layer="above",
            )


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
            padding:4px 6px;
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


def add_book_spine_details(fig, x_vals, y_vals):
    """Subtle antique-book details over Plotly bars."""

    gold = "#C7A875"
    pale_gold = "#DDC49A"

    for x, height in zip(x_vals, y_vals):
        height = float(height)
        if height <= 0:
            continue

        half_width = 0.24

        # Subtle leather edge, giving the spine depth.
        fig.add_shape(
            type="rect",
            x0=x - half_width,
            x1=x - half_width + 0.045,
            y0=0,
            y1=height,
            fillcolor="rgba(40,26,20,0.26)",
            line=dict(width=0),
            layer="above",
        )

        # Soft highlight on the opposite edge.
        fig.add_shape(
            type="rect",
            x0=x + half_width - 0.055,
            x1=x + half_width - 0.025,
            y0=0,
            y1=height,
            fillcolor="rgba(255,232,188,0.17)",
            line=dict(width=0),
            layer="above",
        )

        # Short bars need fewer decorative elements.
        if height < 8:
            continue

        inset = 0.085
        left = x - half_width + inset
        right = x + half_width - inset

        # Fine double-ruled bands at each end.
        band_spacing = min(1.0, height * 0.08)
        top_offset = min(2.4, height * 0.19)

        for band_y in (
            top_offset,
            top_offset + band_spacing,
            height - top_offset - band_spacing,
            height - top_offset,
        ):
            fig.add_shape(
                type="line",
                x0=left,
                x1=right,
                y0=band_y,
                y1=band_y,
                line=dict(color=gold, width=0.8),
                layer="above",
            )

        # Small central ornament for taller spines.
        if height >= 25:
            fig.add_annotation(
                x=x,
                y=height * 0.52,
                text="✦",
                showarrow=False,
                font=dict(
                    family="Georgia, serif",
                    size=12,
                    color=pale_gold,
                ),
            )


def add_horizontal_book_stacks(fig, counts):
    """Draw antique books along horizontal chart rows.

    Each row's full illustrated length represents its exact count.
    Decorative books are capped at 12 per row to avoid crowding.
    """
    leather_colors = [
        "#81533C",  # aged brown
        "#A66B47",  # chestnut
        "#667667",  # faded green
        "#596B7D",  # antique blue
        "#956852",  # russet
        "#91764F",  # worn ochre
    ]

    for row_index, count in enumerate(counts):
        count = float(count)

        if count <= 0:
            continue

        number_of_books = min(12, max(1, int(count)))
        book_width = count / number_of_books

        for j in range(number_of_books):
            x0 = j * book_width + book_width * 0.035
            x1 = (j + 1) * book_width - book_width * 0.035

            if x1 <= x0:
                continue

            y0 = row_index - 0.30
            y1 = row_index + 0.30

            color = leather_colors[
                (row_index + j) % len(leather_colors)
            ]

            # Leather book body
            fig.add_shape(
                type="rect",
                xref="x",
                yref="y",
                x0=x0,
                x1=x1,
                y0=y0,
                y1=y1,
                fillcolor=color,
                line=dict(
                    color="#654631",
                    width=1.2,
                ),
                layer="above",
            )

            # Gold decorative upper and lower bands
            for y in (y0 + 0.095, y1 - 0.095):
                fig.add_shape(
                    type="line",
                    xref="x",
                    yref="y",
                    x0=x0,
                    x1=x1,
                    y0=y,
                    y1=y,
                    line=dict(
                        color="#D5B47D",
                        width=1.1,
                    ),
                    layer="above",
                )

            # Subtle spine highlight
            fig.add_shape(
                type="line",
                xref="x",
                yref="y",
                x0=x0 + (x1 - x0) * 0.12,
                x1=x0 + (x1 - x0) * 0.12,
                y0=y0 + 0.13,
                y1=y1 - 0.13,
                line=dict(
                    color="#E8D1A6",
                    width=0.6,
                ),
                layer="above",
            )


# ---------------------------------------------------------
# Row 1: Country distribution and ratings
# ---------------------------------------------------------

country_col, ratings_col = st.columns([2, 1], gap="large")

density = get_country_reading_density()

# Group read books by author's country of birth.
country_books = {}

for iso3, group in read_books.groupby("ISO3"):
    if not iso3:
        continue

    entries = []

    for _, book in group.iterrows():
        rating = (
            float(book["My Rating"])
            if pd.notna(book["My Rating"])
            else 0
        )

        stars = "★" * int(rating)
        if rating % 1 >= 0.5:
            stars += "½"

        entries.append({
            "title": str(book["Display Title"]),
            "author": str(book["Author"]),
            "stars": stars or "—",
        })

    country_books[str(iso3)] = entries

perf_checkpoint("Country books entries are built")

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
                customdata=top_density["iso3"].tolist(),
                marker=dict(
                    color=bar_colors,
                    line=dict(color="#8E735B", width=1),
                ),
                text=top_density["works"],
                textposition="outside",
                hoverinfo="none",
                # hovertemplate=(
                #     "<b>%{y}</b><br>"
                #     "Unique works: %{x}<extra></extra>"
                # ),
            )
        )

        fig.update_layout(
            height=380,
            margin=dict(l=20, r=40, t=30, b=45),
            paper_bgcolor="#FAF7F1",
            plot_bgcolor="#F5EFE4",
            font=dict(
                family="Georgia, serif",
                size=14,
                color="#58412F",
            ),
            xaxis=dict(
                #title="Unique works",
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
            hovermode="closest",
        )
        fig.add_annotation(
            xref="paper",
            yref="paper",
            x=-0.01,
            y=1.08,
            xanchor="left",
            yanchor="top",
            showarrow=False,
            text="✧ Click a country to explore its literary journeys",
            font=dict(
                family="Georgia, serif",
                size=11,
                color="#96785D",
            ),
        )

        st.plotly_chart(
            fig,
            width="stretch",
            config={"displayModeBar": False},
            key="litlas_country_density",
        )

        country_names = dict(
            zip(top_density["iso3"], top_density["country"])
        )

        render_rating_popup(
            country_books,
            mode="country",
            country_names=country_names,
        )

perf_checkpoint("Top-Let-Most Plot is built")

blue_spine_path = make_book_spine_asset(
    name="rating_3_blue",
    base_color="#4F647A",
    edge_color="#344556",
    gold_color="#D8B36A",
)

ratings = get_rating_distribution()

books_by_rating = {
    f"{float(rating):g}": cached_ratings.get(
        f"{float(rating):g}", []
    )
    for rating in ratings["rating"]
}

with ratings_col:
    st.subheader("Ratings")

    if ratings.empty:
        st.info("No rated books available yet.")
    else:
        fig_ratings = build_rating_spines_figure(ratings, image_height=380)

        fig_ratings.add_annotation(
            xref="paper",
            yref="paper",
            x=1.0,
            y=1.0,
            xanchor="right",
            yanchor="top",
            showarrow=False,
            align="left",
            text=(
                "<b>Personal Rating Scale</b><br>"
                "   5 ★  Masterpiece<br>"
                "   4 ★  Excellent<br>"
                "   3 ★  Enjoyed it<br>"
                "   2 ★  Didn't enjoy<br>"
                "   1 ★  Disappointing"
            ),
            font=dict(
                family="Georgia, serif",
                size=12,
                color="#58412F",
            ),
            bgcolor="rgba(0,0,0,0)",
        )


        st.plotly_chart(
            fig_ratings,
            width="stretch",
            config={"displayModeBar": False},
            key="litlas_ratings",
        )

        render_rating_popup(books_by_rating)

perf_checkpoint("Rating plot is built")

# ---------------------------------------------------------
# Row 2: Reading history
# ---------------------------------------------------------

history_col, highlights_col = st.columns([2, 1], gap="large")

history = get_books_read_by_year()

books_by_year = {
    str(year): cached_years.get(str(year), [])
    for year in history["year"]
}


with history_col:
    st.subheader("Books Read Through the Years")

    if history.empty:
        st.info("No books have a recorded reading date yet.")
    else:
        fig_history = build_year_spines_figure(history, spine_width=0.60, image_height=400)
 
        st.plotly_chart(
            fig_history,
            width="stretch",
            config={"displayModeBar": False},
            key="litlas_reading_history",
        )
        render_rating_popup(books_by_year, mode="year")

        # st.caption(
        #     f"Based on {dated_books} books with recorded reading dates. "
        #     f"{missing_dates} books have no usable Date Read value."
        # )

# ---------------------------------------------------------
# Yearly literary highlights
# ---------------------------------------------------------

with highlights_col:
    perf_checkpoint("Reading history completed")
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

        if rows:
            st.html("\n".join(rows))
        else:
            st.caption("No books recorded for this year.")

    # st.caption(
    #     "Highest-rated completed book per year. "
    #     "Ties resolved by length, then completion date."
    # )

st.divider()
st.subheader("My Literary Constellation")


try:
    constellation_df = load_constellation_books(
        default_constellation_csv(),
        get_constellation_book_details(),
    )

    constellation_fig = build_constellation_figure(
        constellation_df,
        height=530,
    )

    st.plotly_chart(
        constellation_fig,
        width="stretch",
        config={"displayModeBar": False},
    )

except (ValueError, FileNotFoundError) as exc:
    st.warning(f"Constellation could not be loaded: {exc}")

perf_checkpoint("Constellation completed")
# ---------------------------------------------------------
# My Literary Book of Honour
# ---------------------------------------------------------

st.divider()

st.subheader("My Literary Book of Honour")

favourite_authors = get_favourite_authors()

render_book_of_honour(favourite_authors)
perf_checkpoint("Book of Honour completed")

# ---------------------------------------------------------
# Row 3: Author statistics
# ---------------------------------------------------------

st.divider()

most_read_col, favourite_col, wanderlust_col = st.columns(
    [1, 1, 1],
    gap="large",
)
# Get a sufficiently large pool of authors, not just the
# ten most-read, so favourite rankings are not biased.
all_authors = get_top_authors(limit=10000)
perf_checkpoint("Author statistics loaded")

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
    favourites["avg_rating"] = favourites["avg_rating"].astype(float)
    
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
            .head(4)
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
                margin-bottom:{'0' if i == len(favourites) - 1 else '10px'};
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
                    height:5.0px;
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

        # st.caption(
        #     "Ranked by confidence-adjusted average rating. "
        # )


# ---------------------------------------------------------
# Literary Wanderlust
# ---------------------------------------------------------

with wanderlust_col:
    st.subheader("Literary Wanderlust")

    wanderlust = get_literary_wanderlust()

    if wanderlust.empty:
        st.info("Not enough reading history available yet.")
    else:
        fig_wanderlust = build_wanderlust_figure(wanderlust)

        st.plotly_chart(
            fig_wanderlust,
            width="stretch",
            config={"displayModeBar": False},
        )
        # st.caption(
        #     "First dated book by an author counts as a discovery; "
        #     "later books count as returns. "
        #     "Based on available reading dates."
        # )
perf_checkpoint("Page script completed")
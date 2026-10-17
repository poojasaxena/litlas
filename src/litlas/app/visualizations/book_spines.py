"""Antique illustrated book-spine rating chart for Litlas."""

from functools import lru_cache
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from PIL import Image, ImageEnhance


_ASSETS = Path(__file__).resolve().parent / "assets" / "book_spines"

# ---------------------------------------------------------
# Visual tuning
# ---------------------------------------------------------
SPINE_CONTRAST = 1.24
SPINE_BRIGHTNESS = 1.07
SPINE_COLOR = 0.85
SPINE_SHARPNESS = 1.18

SPINE_WIDTH = 0.45
CHART_HEIGHT = 420


def _enhance_spine(image: Image.Image) -> Image.Image:
    """Apply light enhancement so spines read better at normal screen size."""
    image = ImageEnhance.Contrast(image).enhance(SPINE_CONTRAST)
    image = ImageEnhance.Brightness(image).enhance(SPINE_BRIGHTNESS)
    image = ImageEnhance.Color(image).enhance(SPINE_COLOR)
    image = ImageEnhance.Sharpness(image).enhance(SPINE_SHARPNESS)
    return image


@lru_cache(maxsize=32)
def _spine_parts(rating: str):
    """Read one spine image once, enhance it, and preserve decorative ends."""
    path = _ASSETS / f"rating_{rating.replace('.', '_')}.png"

    with Image.open(path) as source:
        spine = source.convert("RGBA")
        spine = _enhance_spine(spine)

        width, height = spine.size
        cut = max(1, int(height * 0.24))

        top = spine.crop((0, 0, width, cut))
        middle = spine.crop((0, cut, width, height - cut))
        bottom = spine.crop((0, height - cut, width, height))

        return top, middle, bottom


def build_year_spines_figure(history: pd.DataFrame, spine_width: float = SPINE_WIDTH) -> go.Figure:
    """Display books read per year as illustrated antique spines.

    Uses the same cached illustrations and image enhancements as Ratings.
    Keeps a Plotly bar trace for hover and point selection.
    """
    plot = history.copy()
    plot["year"] = plot["year"].astype(str)
    plot["books"] = pd.to_numeric(
        plot["books"], errors="coerce"
    ).fillna(0).astype(int)

    years = plot["year"].tolist()
    counts = plot["books"].tolist()
    positions = list(range(len(years)))

    # Reuse the existing seven illustrated book spines.
    designs = ["1", "2", "3", "3.5", "4", "4.5", "5"]

    figure = go.Figure()

    # Invisible bars preserve hover and clickable year selection.
    figure.add_trace(
        go.Bar(
            x=positions,
            y=counts,
            width=spine_width,
            customdata=years,
            marker=dict(
                color="rgba(139,99,75,0.001)",
                line=dict(width=0),
            ),
            text=counts,
            textposition="outside",
            textfont=dict(
                family="Georgia, serif",
                size=12,
                color="#7A4F32",
            ),
            cliponaxis=False,
            hovertemplate=(
                "<b>%{customdata}</b><br>"
                "%{y} books read<extra></extra>"
            ),
        )
    )

    for index, count in enumerate(counts):
        if count <= 0:
            continue

        design = designs[index % len(designs)]
        top, middle, bottom = _spine_parts(design)

        cap_height = min(5.0, count * 0.23)
        middle_height = max(0.0, count - 2 * cap_height)

        segments = [
            (bottom, 0, cap_height),
            (middle, cap_height, middle_height),
            (top, cap_height + middle_height, cap_height),
        ]

        for asset, bottom_y, height in segments:
            if height <= 0:
                continue

            figure.add_layout_image(
                dict(
                    source=asset,
                    xref="x",
                    yref="y",
                    x=index,
                    y=bottom_y,
                    sizex=spine_width,
                    sizey=height,
                    xanchor="center",
                    yanchor="bottom",
                    sizing="stretch",
                    layer="below",
                )
            )

    figure.update_layout(
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
            tickmode="array",
            tickvals=positions,
            ticktext=years,
            range=[-0.6, len(years) - 0.4],
            showgrid=False,
            zeroline=False,
        ),
        yaxis=dict(
            title="Books",
            showgrid=True,
            gridcolor="#DDD2C2",
            zeroline=False,
            range=[0, max(counts) * 1.14] if counts else [0, 1],
        ),
        bargap=0.35,
        showlegend=False,
        hovermode="closest",
        clickmode="event+select",
    )

    return figure


def build_rating_spines_figure(ratings: pd.DataFrame) -> go.Figure:
    """Render rating counts as antique book-spine bars.

    The underlying invisible bar trace keeps hover and value labels accurate.
    Decorative spine images are layered on top.
    """
    plot = ratings.sort_values("rating").copy()

    plot["rating"] = pd.to_numeric(plot["rating"], errors="coerce")
    plot["books"] = pd.to_numeric(plot["books"], errors="coerce").fillna(0).astype(int)
    plot = plot.dropna(subset=["rating"])

    plot["rating_label"] = plot["rating"].map(lambda x: f"{x:g} stars")

    x_values = plot["rating"].tolist()
    counts = plot["books"].tolist()

    figure = go.Figure()

    # ---------------------------------------------------------
    # Invisible bars: keep accurate hover + count labels
    # ---------------------------------------------------------
    figure.add_trace(
        go.Bar(
            x=x_values,
            y=counts,
            width=SPINE_WIDTH,
            customdata=plot["rating_label"],
            marker=dict(
                color="rgba(0,0,0,0)",
                line=dict(width=0),
            ),
            text=counts,
            textposition="outside",
            textfont=dict(
                family="Georgia, serif",
                size=12,
                color="#7A4F32",
            ),
            cliponaxis=False,
            hovertemplate=(
                "<b>%{customdata}</b><br>"
                "%{y} books<extra></extra>"
            ),
        )
    )

    # ---------------------------------------------------------
    # Decorative spine images
    # ---------------------------------------------------------
    for rating, count in zip(x_values, counts):
        if count <= 0:
            continue

        top, middle, bottom = _spine_parts(f"{rating:g}")

        # Decorative caps stay proportionate even for short bars.
        cap_height = min(5.0, count * 0.23)
        middle_height = max(0.0, count - 2 * cap_height)

        segments = [
            (bottom, 0, cap_height),
            (middle, cap_height, middle_height),
            (top, cap_height + middle_height, cap_height),
        ]

        for asset, bottom_y, height in segments:
            if height <= 0:
                continue

            figure.add_layout_image(
                dict(
                    source=asset,
                    xref="x",
                    yref="y",
                    x=rating,
                    y=bottom_y,
                    sizex=SPINE_WIDTH,
                    sizey=height,
                    xanchor="center",
                    yanchor="bottom",
                    sizing="stretch",
                    layer="above",
                )
            )

    ymax = max(counts) if counts else 1

    figure.update_layout(
        height=CHART_HEIGHT,
        margin=dict(l=40, r=10, t=30, b=45),
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
            tickvals=x_values,
            ticktext=[f"{x:g}" for x in x_values],
            range=[min(x_values) - 0.45, max(x_values) + 0.45] if x_values else [0, 1],
            showgrid=False,
            zeroline=False,
        ),
        yaxis=dict(
            title=None,
            showgrid=True,
            gridcolor="#D1BEA4",
            zeroline=False,
            range=[0, ymax * 1.13],
        ),
        bargap=0.25,
        showlegend=False,
        hovermode="closest",
    )

    return figure
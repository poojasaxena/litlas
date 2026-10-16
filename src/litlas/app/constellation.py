"""Curated, interactive literary constellation for Litlas."""

from html import escape
from math import cos, log1p, pi, sin, sqrt
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import base64
from litlas.processing.core import load_config

# Coordinates belong to themes, not individual books.
THEME_CENTRES = {
    "Ideas & Society": (0.18, 0.55),
    "Classics": (0.43, 0.67),
    "Close to Heart": (0.63, 0.33),
    "Personal Growth": (0.83, 0.66),
    "Human Nature": (0.86, 0.27),
}
THEME_COLORS = {
    "Ideas & Society": "#F1C578",
    "Classics": "#CEE7F3",
    "Close to Heart": "#F6CB80",
    "Personal Growth": "#F0AF73",
    "Human Nature": "#C5DFEC",
}
TIERS = {"notable": 0.20, "memorable": 0.60, "treasure": 1.00}


def default_constellation_csv() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "constellation_books.csv"


def load_constellation_books(csv_path: str | Path, library: pd.DataFrame) -> pd.DataFrame:
    """Validate CSV and join authoritative title/year/author/rating/page data."""
    curated = pd.read_csv(csv_path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    required = {"year", "title", "constellation", "significance", "note"}
    missing = required - set(curated.columns)
    if missing:
        raise ValueError(f"Missing constellation CSV columns: {', '.join(sorted(missing))}")

    curated = curated.copy()
    for column in required:
        curated[column] = curated[column].str.strip()
    curated = curated.loc[curated["year"].ne("") & curated["title"].ne("")].copy()
    curated["significance"] = curated["significance"].str.casefold()
    invalid = curated.loc[~curated["significance"].isin(TIERS), ["title", "significance"]]
    if not invalid.empty:
        raise ValueError("Unknown significance tags: " + ", ".join(
            f"{r.title} ({r.significance})" for r in invalid.itertuples()
        ))

    curated["key"] = list(zip(curated["year"], curated["title"].str.casefold()))
    if curated["key"].duplicated().any():
        raise ValueError("Duplicate entries in constellation CSV: " + ", ".join(
            curated.loc[curated["key"].duplicated(), "title"]
        ))

    books = library.copy()
    books["year"] = books["year"].astype(str).str.strip()
    books["title"] = books["title"].astype(str).str.strip()
    books["key"] = list(zip(books["year"], books["title"].str.casefold()))
    # The title/year key is expected to identify a single displayed book.
    ambiguous = set(curated["key"]) & set(books.loc[books["key"].duplicated(keep=False), "key"])
    if ambiguous:
        raise ValueError("Ambiguous title/year matches: " + ", ".join(sorted(str(k) for k in ambiguous)))

    matched = curated.merge(
        books[["key", "author", "rating", "pages"]],
        on="key", how="left", indicator=True, validate="one_to_one",
    )
    unmatched = matched.loc[matched["_merge"] != "both", ["year", "title"]]
    if not unmatched.empty:
        raise ValueError("Books not found in Litlas: " + ", ".join(
            f"{r.year}: {r.title}" for r in unmatched.itertuples()
        ))
    return matched.drop(columns=["key", "_merge"])


def _star_size(significance: str, pages) -> float:
    """65% curated importance + 35% log-scaled length (visual size 13-30px)."""
    tier = TIERS[significance]
    length = 0.35  # neutral fallback if page count is missing
    if pd.notna(pages) and float(pages) > 0:
        length = float(np.clip(
            (log1p(float(pages)) - log1p(100)) / (log1p(1500) - log1p(100)), 0, 1
        ))
    return 13 + 17 * (0.65 * tier + 0.35 * length)


def _group_centres(names: list[str]) -> dict[str, tuple[float, float]]:
    """Use aesthetic presets; place novel themes in unused positions automatically."""
    result = {name: THEME_CENTRES[name] for name in names if name in THEME_CENTRES}
    spare = [(0.15, 0.27), (0.39, 0.32), (0.62, 0.72), (0.80, 0.46),
             (0.28, 0.75), (0.50, 0.50)]
    for name in names:
        if name not in result:
            if not spare:
                raise ValueError("Too many constellations for this compact illustration (maximum 11).")
            result[name] = spare.pop(0)
    return result

def build_constellation_figure(df: pd.DataFrame, height: int = 680) -> go.Figure:
    """Draw a compact, illustrated literary constellation."""
    fig = go.Figure()

    # ------------------------------------------------------------------
    # Background illustration from config.toml
    # ------------------------------------------------------------------
    config = load_config()
    background_path = config.get("illustrations", {}).get("constellation_illustration")

    if background_path:
        path = Path(background_path).expanduser()
        if path.is_file():
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
            fig.add_layout_image(
                dict(
                    source=f"data:image/png;base64,{encoded}",
                    xref="paper",
                    yref="paper",
                    x=0,
                    y=1,
                    sizex=1,
                    sizey=1,
                    sizing="stretch",
                    opacity=1,
                    layer="below",
                )
            )

    # Gentle dark veil so foreground stars and text read better
    fig.add_shape(
        type="rect",
        xref="paper",
        yref="paper",
        x0=0,
        y0=0,
        x1=1,
        y1=1,
        fillcolor="rgba(7, 16, 30, 0.22)",
        line=dict(width=0),
        layer="below",
    )

    # ------------------------------------------------------------------
    # Background tiny stars
    # ------------------------------------------------------------------
    rng = np.random.default_rng(42)

    # faint field
    fig.add_trace(
        go.Scatter(
            x=rng.uniform(0.02, 0.98, 150),
            y=rng.uniform(0.06, 0.95, 150),
            mode="markers",
            marker=dict(
                size=rng.uniform(0.7, 2.0, 150),
                color="rgba(237, 204, 143, 0.35)",
            ),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # a few brighter distant stars
    fig.add_trace(
        go.Scatter(
            x=rng.uniform(0.05, 0.95, 22),
            y=rng.uniform(0.10, 0.92, 22),
            mode="markers",
            marker=dict(
                size=rng.uniform(2.0, 4.5, 22),
                color="rgba(255, 228, 180, 0.55)",
            ),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # ------------------------------------------------------------------
    # Constellations
    # ------------------------------------------------------------------
    names = list(dict.fromkeys(df["constellation"].tolist()))
    centres = _group_centres(names)

    for name in names:
        group = df.loc[df["constellation"] == name].copy()
        group = group.sort_values("title", key=lambda s: s.str.casefold()).reset_index(drop=True)

        cx, cy = centres[name]
        n = len(group)

        if n == 1:
            offsets = [(0.0, 0.0)]
        elif n == 2:
            offsets = [(-0.055, 0.050), (0.055, -0.050)]
        else:
            offsets = [
                (
                    0.085 * sqrt((i + 0.45) / n) * cos(i * pi * (3 - sqrt(5))),
                    0.095 * sqrt((i + 0.45) / n) * sin(i * pi * (3 - sqrt(5))),
                )
                for i in range(n)
            ]

        positions = [(cx + dx, cy + dy) for dx, dy in offsets]

        # softer dotted constellation lines
        if n > 1:
            fig.add_trace(
                go.Scatter(
                    x=[p[0] for p in positions],
                    y=[p[1] for p in positions],
                    mode="lines",
                    line=dict(
                        color="rgba(223, 185, 113, 0.36)",
                        width=1.15,
                        dash="dot",
                    ),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

        # constellation title
        fig.add_annotation(
            x=cx,
            y=min(0.93, cy + (0.15 if n > 1 else 0.13)),
            text=f"<i>{escape(name)}</i>",
            showarrow=False,
            font=dict(
                family="Georgia, serif",
                size=17,
                color="#F0C884",
            ),
            xanchor="center",
            yanchor="bottom",
        )

        for (_, book), (x, y) in zip(group.iterrows(), positions):
            significance = str(book["significance"]).casefold()
            size = _star_size(significance, book["pages"])
            color = THEME_COLORS.get(name, "#E9CC9C")

            # glow intensity by significance
            glow_strength = {
                "treasure": (0.08, 0.16, 0.26),
                "memorable": (0.06, 0.12, 0.20),
                "notable": (0.04, 0.08, 0.15),
            }[significance]

            # outer soft glow
            fig.add_trace(
                go.Scatter(
                    x=[x],
                    y=[y],
                    mode="markers",
                    marker=dict(
                        size=size + 26,
                        color=color,
                        opacity=glow_strength[0],
                        line=dict(width=0),
                    ),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

            # middle glow
            fig.add_trace(
                go.Scatter(
                    x=[x],
                    y=[y],
                    mode="markers",
                    marker=dict(
                        size=size + 14,
                        color=color,
                        opacity=glow_strength[1],
                        line=dict(width=0),
                    ),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

            # inner glow
            fig.add_trace(
                go.Scatter(
                    x=[x],
                    y=[y],
                    mode="markers",
                    marker=dict(
                        size=size + 6,
                        color=color,
                        opacity=glow_strength[2],
                        line=dict(width=0),
                    ),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

            # tooltip text
            pages_text = "Unknown" if pd.isna(book["pages"]) else f"{int(book['pages']):,}"
            rating_text = (
                "Unrated"
                if pd.isna(book["rating"]) or not float(book["rating"])
                else f"{float(book['rating']):g}/5"
            )
            note = str(book["note"]).strip()

            tooltip = (
                f"<b>{escape(str(book['title']))}</b><br>"
                f"{escape(str(book['author']))}<br>"
                f"{escape(str(book['year']))} · {pages_text} pages · {rating_text}<br>"
                f"{escape(str(book['constellation']))} · {significance.title()}"
            )
            if note:
                tooltip += f"<br>{escape(note)}"

            # star itself
            fig.add_trace(
                go.Scatter(
                    x=[x],
                    y=[y],
                    mode="markers",
                    marker=dict(
                        symbol="star",
                        size=size,
                        color=color,
                        line=dict(color="#FFF3D4", width=1.0),
                    ),
                    hovertext=[tooltip],
                    hoverinfo="text",
                    showlegend=False,
                )
            )

            # tiny bright centre
            fig.add_trace(
                go.Scatter(
                    x=[x],
                    y=[y],
                    mode="markers",
                    marker=dict(
                        size=max(2.5, size * 0.16),
                        color="rgba(255, 248, 232, 0.95)",
                        line=dict(width=0),
                    ),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

            # label placement
            right_edge = x >= 0.72
            xshift = -(size / 2 + 8) if right_edge else (size / 2 + 8)
            xanchor = "right" if right_edge else "left"

            pages_short = ""
            if pd.notna(book["pages"]):
                pages_short = f"<br><span style='font-size:10px'>{book['year']} · {int(book['pages'])} pages</span>"
            else:
                pages_short = f"<br><span style='font-size:10px'>{book['year']}</span>"

            label_size = 12 if significance == "treasure" else 11

            fig.add_annotation(
                x=x,
                y=y,
                text=f"<i>{escape(str(book['title']))}</i>{pages_short}",
                showarrow=False,
                xshift=xshift,
                xanchor=xanchor,
                yanchor="middle",
                font=dict(
                    family="Georgia, serif",
                    size=label_size,
                    color="#F6DEB3",
                ),
                align="left",
            )

    # ------------------------------------------------------------------
    # Subtitle inside chart
    # ------------------------------------------------------------------
    fig.add_annotation(
        x=0.02,
        y=0.97,
        xref="paper",
        yref="paper",
        text="<i>Some books don’t just fill a year — they light up the sky.</i>",
        showarrow=False,
        xanchor="left",
        yanchor="top",
        font=dict(
            family="Georgia, serif",
            size=14,
            color="#DCC8A0",
        ),
    )

    # ------------------------------------------------------------------
    # Small legend inside chart
    # ------------------------------------------------------------------
    legend_text = (
        "<b>Star size = pages</b><br>"
        "★ under 300 pages<br>"
        "★ 300–600 pages<br>"
        "★ over 600 pages"
    )
    fig.add_annotation(
        x=0.985,
        y=0.965,
        xref="paper",
        yref="paper",
        text=legend_text,
        showarrow=False,
        xanchor="right",
        yanchor="top",
        align="left",
        bordercolor="rgba(224, 188, 122, 0.45)",
        borderwidth=1,
        borderpad=8,
        bgcolor="rgba(8, 18, 35, 0.35)",
        font=dict(
            family="Georgia, serif",
            size=12,
            color="#F0DEBA",
        ),
    )

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        xaxis=dict(
            visible=False,
            range=[0, 1],
            fixedrange=True,
        ),
        yaxis=dict(
            visible=False,
            range=[0, 1],
            fixedrange=True,
        ),
        dragmode=False,
        hoverlabel=dict(
            bgcolor="#FAF7F1",
            bordercolor="#B89C75",
            font=dict(
                family="Georgia, serif",
                size=13,
                color="#58412F",
            ),
        ),
    )

    return fig
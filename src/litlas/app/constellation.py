"""Curated, interactive literary constellation for Litlas."""

from html import escape
from math import cos, log1p, pi, sin, sqrt
from pathlib import Path

from io import BytesIO
from PIL import Image
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

STARBURST_PATH = (
    Path(__file__).resolve().parent
    / "assets"
    / "litlas_golden_starburst.png"
)


def _image_to_data_uri(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"

def default_constellation_csv() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "constellation_books.csv"


def _starburst_source(
    image: Image.Image,
    color: str,
    significance: str,
) -> str:
    """Tint the illustrated star without washing out its colour."""

    pixels = np.asarray(
        image.convert("RGBA"),
        dtype=np.float32,
    ).copy()

    # Colour assigned to the constellation.
    tint = np.array(
        [int(color[i:i + 2], 16) for i in (1, 3, 5)],
        dtype=np.float32,
    )

    # Preserve the original star's light-and-shadow structure.
    original = pixels[:, :, :3]
    brightness = (
        0.2126 * original[:, :, 0]
        + 0.7152 * original[:, :, 1]
        + 0.0722 * original[:, :, 2]
    ) / 255.0

    # Use the chosen hue throughout the star and its rays.
    coloured = tint[None, None, :] * (
        0.30 + 0.70 * brightness[..., None]
    )

    # Only a very small central region stays white-hot.
    h, w = brightness.shape
    yy, xx = np.ogrid[:h, :w]

    distance = np.sqrt(
        ((xx - (w - 1) / 2) / w) ** 2
        + ((yy - (h - 1) / 2) / h) ** 2
    )

    white_core = (
        np.clip((0.055 - distance) / 0.055, 0, 1) ** 2
    ) * np.clip((brightness - 0.75) / 0.25, 0, 1)

    pixels[:, :, :3] = (
        coloured * (1 - white_core[..., None])
        + 255 * white_core[..., None]
    )

    # Personal significance determines luminosity.
    luminosity = {
        "treasure": 1.00,
        "memorable": 0.82,
        "notable": 0.65,
    }[significance]

    pixels[:, :, 3] *= luminosity

    output = Image.fromarray(
        np.clip(pixels, 0, 255).astype(np.uint8),
        mode="RGBA",
    )

    buffer = BytesIO()
    output.save(buffer, format="PNG")

    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"



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




def build_constellation_figure(
    df: pd.DataFrame,
    height: int = 680,
) -> go.Figure:
    """Draw an interactive literary constellation with illustrated stars."""

    fig = go.Figure()

    # ---------------------------------------------------------
    # 1. Background illustration
    # ---------------------------------------------------------

    config = load_config()
    background_path = config.get("illustrations", {}).get(
        "constellation_illustration"
    )

    if background_path:
        path = Path(background_path).expanduser()

        if path.is_file():
            encoded = base64.b64encode(
                path.read_bytes()
            ).decode("ascii")

            fig.add_layout_image(
                dict(
                    source=f"data:image/png;base64,{encoded}",
                    xref="paper",
                    yref="paper",
                    x=0,
                    y=1,
                    xanchor="left",
                    yanchor="top",
                    sizex=1,
                    sizey=1,
                    sizing="stretch",
                    opacity=1,
                    layer="below",
                )
            )

    # Gentle dark veil.
    fig.add_shape(
        type="rect",
        xref="paper",
        yref="paper",
        x0=0,
        y0=0,
        x1=1,
        y1=1,
        fillcolor="rgba(7,16,30,0.18)",
        line=dict(width=0),
        layer="below",
    )

    # ---------------------------------------------------------
    # 2. Load the original illustrated star
    # ---------------------------------------------------------

    starburst_path = (
        Path(__file__).resolve().parent
        / "assets"
        / "litlas_golden_starburst.png"
    )

    if not starburst_path.is_file():
        raise FileNotFoundError(
            f"Starburst asset not found: {starburst_path}"
        )

    with Image.open(starburst_path) as img:
        original_star = img.convert("RGBA")

    # Create one colour variant per theme and significance.
    # Adding another book never requires another image file.
    star_sources = {}

    # ---------------------------------------------------------
    # 3. Constellation groups
    # ---------------------------------------------------------

    names = list(dict.fromkeys(df["constellation"].tolist()))
    centres = _group_centres(names)

    for name in names:
        group = df.loc[
            df["constellation"] == name
        ].copy()

        group = group.sort_values(
            "title",
            key=lambda s: s.str.casefold(),
        ).reset_index(drop=True)

        cx, cy = centres[name]
        n = len(group)

        if n == 1:
            offsets = [(0.0, 0.0)]

        elif n == 2:
            offsets = [
                (-0.055, 0.050),
                (0.055, -0.050),
            ]

        else:
            offsets = [
                (
                    0.085
                    * sqrt((i + 0.45) / n)
                    * cos(i * pi * (3 - sqrt(5))),
                    0.095
                    * sqrt((i + 0.45) / n)
                    * sin(i * pi * (3 - sqrt(5))),
                )
                for i in range(n)
            ]

        positions = [
            (cx + dx, cy + dy)
            for dx, dy in offsets
        ]

        # Delicate constellation connections.
        if n > 1:
            fig.add_trace(
                go.Scatter(
                    x=[p[0] for p in positions],
                    y=[p[1] for p in positions],
                    mode="lines",
                    line=dict(
                        color="rgba(223,185,113,0.36)",
                        width=1.15,
                        dash="dot",
                    ),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

        # Constellation heading.
        fig.add_annotation(
            x=cx,
            y=min(
                0.93,
                cy + (0.15 if n > 1 else 0.13),
            ),
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

        # -----------------------------------------------------
        # 4. Individual book stars
        # -----------------------------------------------------

        for (_, book), (x, y) in zip(
            group.iterrows(),
            positions,
        ):
            title = str(book["title"]).strip()
            significance = str(
                book["significance"]
            ).strip().casefold()

            # Existing 65% significance / 35% page formula.
            size = _star_size(
                significance,
                book["pages"],
            )

            # Colour depends on theme, never on title.
            color = THEME_COLORS.get(
                name,
                "#E9CC9C",
            )

            # Reuse the same image for matching theme/tier.
            source_key = (color, significance)

            if source_key not in star_sources:
                star_sources[source_key] = _starburst_source(
                    original_star,
                    color,
                    significance,
                )

            starburst_source = star_sources[source_key]

            # -------------------------------------------------
            # 5. Tooltip
            # -------------------------------------------------

            pages_text = (
                "Unknown"
                if pd.isna(book["pages"])
                else f"{int(book['pages']):,}"
            )

            rating_text = (
                "Unrated"
                if pd.isna(book["rating"])
                or not float(book["rating"])
                else f"{float(book['rating']):g}/5"
            )

            note = str(book["note"]).strip()

            tooltip = (
                f"<b>{escape(title)}</b><br>"
                f"{escape(str(book['author']))}<br>"
                f"{escape(str(book['year']))}"
                f" · {pages_text} pages"
                f" · {rating_text}<br>"
                f"{escape(name)}"
                f" · {significance.title()}"
            )

            if note:
                tooltip += f"<br>{escape(note)}"

            # -------------------------------------------------
            # 6. Illustrated starburst
            # -------------------------------------------------

            # Same size mapping that worked for Lonesome Dove.
            # The PNG is scaled uniformly according to _star_size().
            image_width = 0.052 * size / 27
            image_height = 0.125 * size / 27

            fig.add_layout_image(
                dict(
                    source=starburst_source,
                    xref="x",
                    yref="y",
                    x=x,
                    y=y,
                    xanchor="center",
                    yanchor="middle",
                    sizex=image_width,
                    sizey=image_height,
                    sizing="contain",
                    opacity=1,
                    layer="below",
                )
            )

            # Invisible Plotly marker for hover interaction.
            fig.add_trace(
                go.Scatter(
                    x=[x],
                    y=[y],
                    mode="markers",
                    marker=dict(
                        symbol="circle",
                        size=max(size + 12, 32),
                        color="rgba(255,255,255,0.01)",
                        line=dict(width=0),
                    ),
                    hovertext=[tooltip],
                    hoverinfo="text",
                    showlegend=False,
                )
            )

            # -------------------------------------------------
            # 7. Labels
            # -------------------------------------------------

            right_edge = x >= 0.72

            label_gap = size / 2 + 18
            xshift = (
                -label_gap if right_edge else label_gap
            )
            xanchor = (
                "right" if right_edge else "left"
            )

            if pd.notna(book["pages"]):
                pages_short = (
                    f"<br><span style='font-size:10px'>"
                    f"{escape(str(book['year']))} · "
                    f"{int(book['pages']):,} pages"
                    f"</span>"
                )
            else:
                pages_short = (
                    f"<br><span style='font-size:10px'>"
                    f"{escape(str(book['year']))}</span>"
                )

            label_size = (
                12 if significance == "treasure" else 11
            )

            fig.add_annotation(
                x=x,
                y=y,
                text=(
                    f"<i>{escape(title)}</i>"
                    f"{pages_short}"
                ),
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

    # ---------------------------------------------------------
    # 8. Subtitle
    # ---------------------------------------------------------

    fig.add_annotation(
        x=0.02,
        y=0.97,
        xref="paper",
        yref="paper",
        text=(
            "<i>Some books don’t just fill a year, they light up the sky...</i>"
        ),
        showarrow=False,
        xanchor="left",
        yanchor="top",
        font=dict(
            family="Georgia, serif",
            size=14,
            color="#DCC8A0",
        ),
    )

    # ---------------------------------------------------------
    # 9. Legend
    # ---------------------------------------------------------

    fig.add_annotation(
        x=0.985,
        y=0.965,
        xref="paper",
        yref="paper",
        text=(
            "<b>What makes a star shine?</b><br>"
            "65% personal significance<br>"
            "35% book length"
        ),
        showarrow=False,
        xanchor="right",
        yanchor="top",
        align="left",
        bordercolor="rgba(224,188,122,0.45)",
        borderwidth=1,
        borderpad=8,
        bgcolor="rgba(8,18,35,0.35)",
        font=dict(
            family="Georgia, serif",
            size=12,
            color="#F0DEBA",
        ),
    )

    # ---------------------------------------------------------
    # 10. Figure layout
    # ---------------------------------------------------------

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


def build_constellation_figure_deprecated(
    df: pd.DataFrame,
    height: int = 680,
) -> go.Figure:
    """Draw the illustrated literary constellation with a test starburst."""

    fig = go.Figure()

    # ---------------------------------------------------------
    # 1. Illustrated night-sky background
    # ---------------------------------------------------------

    config = load_config()
    background_path = config.get("illustrations", {}).get(
        "constellation_illustration"
    )

    if background_path:
        path = Path(background_path).expanduser()

        if path.is_file():
            encoded = base64.b64encode(
                path.read_bytes()
            ).decode("ascii")

            fig.add_layout_image(
                dict(
                    source=f"data:image/png;base64,{encoded}",
                    xref="paper",
                    yref="paper",
                    x=0,
                    y=1,
                    xanchor="left",
                    yanchor="top",
                    sizex=1,
                    sizey=1,
                    sizing="stretch",
                    opacity=1,
                    layer="below",
                )
            )

    # Gentle veil to improve foreground contrast.
    fig.add_shape(
        type="rect",
        xref="paper",
        yref="paper",
        x0=0,
        y0=0,
        x1=1,
        y1=1,
        fillcolor="rgba(7, 16, 30, 0.18)",
        line=dict(width=0),
        layer="below",
    )

    # ---------------------------------------------------------
    # 2. Load the illustrated golden star once
    # ---------------------------------------------------------

    starburst_path = (
        Path(__file__).resolve().parent
        / "assets"
        / "litlas_golden_starburst.png"
    )

    if not starburst_path.is_file():
        raise FileNotFoundError(
            f"Golden starburst image not found: {starburst_path}"
        )

    starburst_encoded = base64.b64encode(
        starburst_path.read_bytes()
    ).decode("ascii")

    starburst_source = (
        f"data:image/png;base64,{starburst_encoded}"
    )

    # ---------------------------------------------------------
    # 3. Constellation groups
    # ---------------------------------------------------------

    names = list(dict.fromkeys(df["constellation"].tolist()))
    centres = _group_centres(names)

    for name in names:
        group = df.loc[
            df["constellation"] == name
        ].copy()

        group = group.sort_values(
            "title",
            key=lambda s: s.str.casefold(),
        ).reset_index(drop=True)

        cx, cy = centres[name]
        n = len(group)

        if n == 1:
            offsets = [(0.0, 0.0)]

        elif n == 2:
            offsets = [
                (-0.055, 0.050),
                (0.055, -0.050),
            ]

        else:
            offsets = [
                (
                    0.085
                    * sqrt((i + 0.45) / n)
                    * cos(i * pi * (3 - sqrt(5))),
                    0.095
                    * sqrt((i + 0.45) / n)
                    * sin(i * pi * (3 - sqrt(5))),
                )
                for i in range(n)
            ]

        positions = [
            (cx + dx, cy + dy)
            for dx, dy in offsets
        ]

        # Delicate connections between stars.
        if n > 1:
            fig.add_trace(
                go.Scatter(
                    x=[p[0] for p in positions],
                    y=[p[1] for p in positions],
                    mode="lines",
                    line=dict(
                        color="rgba(223,185,113,0.36)",
                        width=1.15,
                        dash="dot",
                    ),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

        # Constellation heading.
        fig.add_annotation(
            x=cx,
            y=min(
                0.93,
                cy + (0.15 if n > 1 else 0.13),
            ),
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

        # -----------------------------------------------------
        # 4. Individual books
        # -----------------------------------------------------

        for (_, book), (x, y) in zip(
            group.iterrows(),
            positions,
        ):
            title = str(book["title"]).strip()
            significance = str(
                book["significance"]
            ).strip().casefold()

            size = _star_size(
                significance,
                book["pages"],
            )

            color = THEME_COLORS.get(
                name,
                "#E9CC9C",
            )

            # Only Lonesome Dove uses the new PNG.
            is_lonesome = (
                title.casefold() == "lonesome dove"
            )

            # -------------------------------------------------
            # Existing Plotly glows for other seven books
            # -------------------------------------------------

            if not is_lonesome:
                glow_strength = {
                    "treasure": (0.08, 0.16, 0.26),
                    "memorable": (0.06, 0.12, 0.20),
                    "notable": (0.04, 0.08, 0.15),
                }[significance]

                for extra_size, opacity in zip(
                    (26, 14, 6),
                    glow_strength,
                ):
                    fig.add_trace(
                        go.Scatter(
                            x=[x],
                            y=[y],
                            mode="markers",
                            marker=dict(
                                size=size + extra_size,
                                color=color,
                                opacity=opacity,
                                line=dict(width=0),
                            ),
                            hoverinfo="skip",
                            showlegend=False,
                        )
                    )

            # -------------------------------------------------
            # Tooltip — identical for PNG and Plotly stars
            # -------------------------------------------------

            pages_text = (
                "Unknown"
                if pd.isna(book["pages"])
                else f"{int(book['pages']):,}"
            )

            rating_text = (
                "Unrated"
                if pd.isna(book["rating"])
                or not float(book["rating"])
                else f"{float(book['rating']):g}/5"
            )

            note = str(book["note"]).strip()

            tooltip = (
                f"<b>{escape(title)}</b><br>"
                f"{escape(str(book['author']))}<br>"
                f"{escape(str(book['year']))}"
                f" · {pages_text} pages"
                f" · {rating_text}<br>"
                f"{escape(name)}"
                f" · {significance.title()}"
            )

            if note:
                tooltip += f"<br>{escape(note)}"

            # -------------------------------------------------
            # 5. Star rendering
            # -------------------------------------------------

            if is_lonesome:
                # The actual illustrated star image.
                #
                # These dimensions are in chart coordinates.
                # Adjust together after the first test.
                image_width = 0.052 * size / 27
                image_height = 0.125 * size / 27

                fig.add_layout_image(
                    dict(
                        source=starburst_source,
                        xref="x",
                        yref="y",
                        x=x,
                        y=y,
                        xanchor="center",
                        yanchor="middle",
                        sizex=image_width,
                        sizey=image_height,
                        sizing="contain",
                        opacity=1,
                        layer="below",
                    )
                )

                # Nearly transparent Plotly marker retains
                # the interactive tooltip.
                fig.add_trace(
                    go.Scatter(
                        x=[x],
                        y=[y],
                        mode="markers",
                        marker=dict(
                            symbol="circle",
                            size=max(size + 12, 32),
                            color="rgba(255,255,255,0.01)",
                            line=dict(width=0),
                        ),
                        hovertext=[tooltip],
                        hoverinfo="text",
                        showlegend=False,
                    )
                )

            else:
                # Original Plotly star for comparison.
                fig.add_trace(
                    go.Scatter(
                        x=[x],
                        y=[y],
                        mode="markers",
                        marker=dict(
                            symbol="star",
                            size=size,
                            color=color,
                            line=dict(
                                color="#FFF3D4",
                                width=1,
                            ),
                        ),
                        hovertext=[tooltip],
                        hoverinfo="text",
                        showlegend=False,
                    )
                )

                # Bright centre for Plotly stars only.
                fig.add_trace(
                    go.Scatter(
                        x=[x],
                        y=[y],
                        mode="markers",
                        marker=dict(
                            size=max(2.5, size * 0.16),
                            color="rgba(255,248,232,0.95)",
                            line=dict(width=0),
                        ),
                        hoverinfo="skip",
                        showlegend=False,
                    )
                )

            # -------------------------------------------------
            # 6. Book labels
            # -------------------------------------------------

            right_edge = x >= 0.72

            # The illustrated PNG includes glow and rays,
            # so give Lonesome Dove a little more space.
            label_gap = (
                size / 2 + 18
                if is_lonesome
                else size / 2 + 8
            )

            xshift = (
                -label_gap if right_edge else label_gap
            )

            xanchor = (
                "right" if right_edge else "left"
            )

            if pd.notna(book["pages"]):
                pages_short = (
                    f"<br><span style='font-size:10px'>"
                    f"{book['year']} · "
                    f"{int(book['pages'])} pages"
                    f"</span>"
                )
            else:
                pages_short = (
                    f"<br><span style='font-size:10px'>"
                    f"{book['year']}</span>"
                )

            label_size = (
                12 if significance == "treasure" else 11
            )

            fig.add_annotation(
                x=x,
                y=y,
                text=(
                    f"<i>{escape(title)}</i>"
                    f"{pages_short}"
                ),
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

    # ---------------------------------------------------------
    # 7. Subtitle
    # ---------------------------------------------------------

    fig.add_annotation(
        x=0.02,
        y=0.97,
        xref="paper",
        yref="paper",
        text=(
            "<i>Some books don’t just fill a year "
            "— they light up the sky.</i>"
        ),
        showarrow=False,
        xanchor="left",
        yanchor="top",
        font=dict(
            family="Georgia, serif",
            size=14,
            color="#DCC8A0",
        ),
    )

    # ---------------------------------------------------------
    # 8. Legend
    # ---------------------------------------------------------

    # Star size is a combined measure:
    # 65% significance + 35% log-scaled pages.
    legend_text = (
        "<b>What makes a star shine?</b><br>"
        "65% personal significance<br>"
        "35% book length"
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
        bordercolor="rgba(224,188,122,0.45)",
        borderwidth=1,
        borderpad=8,
        bgcolor="rgba(8,18,35,0.35)",
        font=dict(
            family="Georgia, serif",
            size=12,
            color="#F0DEBA",
        ),
    )

    # ---------------------------------------------------------
    # 9. Plot layout
    # ---------------------------------------------------------

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

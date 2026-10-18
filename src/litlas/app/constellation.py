"""Curated, interactive literary constellation for Litlas."""

from html import escape
from math import cos, log1p, pi, sin, sqrt
from pathlib import Path

from io import BytesIO
from PIL import Image
import numpy as np
from PIL import ImageFilter
import pandas as pd
import plotly.graph_objects as go
import base64
from litlas.processing.paths import load_config

# Coordinates belong to themes, not individual books.
THEME_CENTRES = {
    "Ideas & Society": (0.18, 0.60),
    "Classics": (0.48, 0.65),
    "Close to Heart": (0.40, 0.20),
    "Personal Growth": (0.83, 0.66),
    "Human Nature": (0.80, 0.27),
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

def _starburst_glow(source: str, blur_radius: int = 14) -> str:
    """Create a soft luminous glow from the coloured starburst PNG."""
    encoded = source.split(",", 1)[1]
    image = Image.open(BytesIO(base64.b64decode(encoded))).convert("RGBA")

    # Blur the transparency as well as the coloured light.
    glow = image.filter(ImageFilter.GaussianBlur(blur_radius))

    buffer = BytesIO()
    glow.save(buffer, format="PNG")

    return (
        "data:image/png;base64,"
        + base64.b64encode(buffer.getvalue()).decode("ascii")
    )

def default_constellation_csv() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "constellation_books.csv"

def _star_luminosity(significance: str) -> float:
    """
    Controls how strongly a star glows.
    Keep this independent from size so stars can be bright without becoming huge.
    """
    return {
        "treasure": 1.00,
        "memorable": 0.78,
        "notable": 0.58,
    }.get(significance, 0.70)

def _starburst_source(
    image: Image.Image,
    color: str,
    significance: str,
) -> str:
    """Tint a starburst while retaining bright rays and a luminous core."""

    pixels = np.asarray(
        image.convert("RGBA"), dtype=np.float32
    ).copy()

    original = pixels[:, :, :3]
    alpha = pixels[:, :, 3]

    tint = np.array(
        [int(color[i:i + 2], 16) for i in (1, 3, 5)],
        dtype=np.float32,
    )

    # Preserve the original image's brightness structure.
    brightness = (
        0.2126 * original[:, :, 0]
        + 0.7152 * original[:, :, 1]
        + 0.0722 * original[:, :, 2]
    ) / 255.0

    # Brighter coloured rays, without turning everything white.
    coloured = (
        tint[None, None, :]
        * (0.55 + 0.45 * brightness[..., None])
    )

    # Gradually brighten only the most luminous original pixels.
    highlight = np.clip(
        (brightness - 0.65) / 0.35, 0, 1
    ) ** 2

    # Maximum 45% white blending in the rays.
    highlight *= 0.45

    result = (
        coloured * (1 - highlight[..., None])
        + 255 * highlight[..., None]
    )

    # Small white-hot centre.
    h, w = brightness.shape
    yy, xx = np.ogrid[:h, :w]

    distance = np.sqrt(
        ((xx - (w - 1) / 2) / (w / 2)) ** 2
        + ((yy - (h - 1) / 2) / (h / 2)) ** 2
    )

    core = np.clip(
        (0.12 - distance) / 0.12, 0, 1
    ) ** 1.5

    core *= np.clip(
        (brightness - 0.5) / 0.5, 0, 1
    )

    result = (
        result * (1 - core[..., None])
        + 255 * core[..., None]
    )

    pixels[:, :, :3] = result

    # Tier influences luminosity without changing star colour.
    luminosity = _star_luminosity(significance)

    pixels[:, :, 3] = np.clip(
        alpha * luminosity, 0, 255
    )

    output = Image.fromarray(
        np.clip(pixels, 0, 255).astype(np.uint8),
        mode="RGBA",
    )

    buffer = BytesIO()
    output.save(buffer, format="PNG")

    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"

def load_constellation_books(
    csv_path: str | Path,
    library: pd.DataFrame,
) -> pd.DataFrame:
    """Match curated books by title and retrieve their database metadata."""

    curated = pd.read_csv(
        csv_path,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig",
    )
    curated.columns = curated.columns.str.strip()

    required = {"title", "constellation", "significance", "note"}
    missing = required - set(curated.columns)
    if missing:
        raise ValueError(
            f"Missing constellation CSV columns: {', '.join(sorted(missing))}"
        )

    curated = curated.copy()
    for column in required:
        curated[column] = curated[column].str.strip()

    # Author is optional, used only when titles are ambiguous.
    if "author" not in curated.columns:
        curated["author"] = ""
    curated["author"] = curated["author"].str.strip()

    curated = curated.loc[curated["title"].ne("")].copy()
    curated["significance"] = curated["significance"].str.casefold()

    invalid = curated.loc[
        ~curated["significance"].isin(TIERS),
        ["title", "significance"],
    ]
    if not invalid.empty:
        raise ValueError(
            "Unknown significance tags: "
            + ", ".join(
                f"{r.title} ({r.significance})"
                for r in invalid.itertuples()
            )
        )

    books = library.copy()
    books["title"] = books["title"].astype(str).str.strip()
    books["author"] = books["author"].astype(str).str.strip()

    # Earliest reading first; unknown years go last.
    books["_reading_year"] = pd.to_numeric(
        books["year"], errors="coerce"
    )

    books = books.sort_values(
        "_reading_year",
        ascending=True,
        na_position="last",
        kind="stable",
    )

    # Match titles without relying on the reading year.
    books["_title_key"] = books["title"].str.casefold()
    curated["_title_key"] = curated["title"].str.casefold()

    matches = []

    for row in curated.to_dict("records"):
        candidates = books.loc[
            books["_title_key"] == row["_title_key"]
        ]

        if row["author"]:
            candidates = candidates.loc[
                candidates["author"].str.casefold()
                == row["author"].casefold()
            ]

        if candidates.empty:
            raise ValueError(
                f"Book not found in Litlas: {row['title']}"
            )

        # If multiple records share a title, use the earliest reading.
        book = candidates.iloc[0]

        matches.append({
            "title": book["title"],
            "year": book["year"],
            "author": book["author"],
            "rating": book["rating"],
            "pages": book["pages"],
            "constellation": row["constellation"],
            "significance": row["significance"],
            "note": row["note"],
        })

    result = pd.DataFrame(matches)

    if result.duplicated(subset=["title", "author"]).any():
        raise ValueError(
            "The constellation CSV contains duplicate books."
        )

    return result

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
    height: int = 670,
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
        elif n == 3:
            offsets = [
                (-0.030,  0.120),
                ( 0.025,  0.000),
                (-0.030, -0.120),
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

        if n > 1:
            for (x0, y0), (x1, y1) in zip(positions[:-1], positions[1:]):
                # midpoint of the segment
                mx = (x0 + x1) / 2
                my = (y0 + y1) / 2

                # direction and perpendicular unit vector
                dx = x1 - x0
                dy = y1 - y0
                seg_len = max((dx**2 + dy**2) ** 0.5, 1e-6)

                px = -dy / seg_len
                py = dx / seg_len

                # tiny bend amount: just enough to soften the line
                bend = 0.012

                # control point for a gentle curve
                cx_curve = mx + px * bend
                cy_curve = my + py * bend

                fig.add_shape(
                    type="path",
                    path=f"M {x0},{y0} Q {cx_curve},{cy_curve} {x1},{y1}",
                    xref="x",
                    yref="y",
                    line=dict(
                        color="rgba(255, 211, 130, 0.82)",
                        width=1.25,
                        dash="dot",
                    ),
                    layer="above",
                )




        # -------------------------------------------------
        # Constellation heading with curved ornament
        # -------------------------------------------------

        title_y = min(0.93, cy + (0.15 if n > 1 else 0.13), )

        # Group title
        fig.add_annotation(
            x=cx,
            y=title_y,
            text=f"<i>{escape(name)}</i>",
            showarrow=False,
            xanchor="center",
            yanchor="bottom",
            font=dict(
                family="Georgia, serif",
                size=19,
                color="#F1C77B",
            ),
        )

        # Delicate symmetrical curve directly below title
        flourish_y = title_y - 0.025
        half_width = 0.050

        fig.add_shape(
            type="path",
            path=(
                f"M {cx - half_width},{flourish_y + 0.004} "
                f"C {cx - 0.035},{flourish_y - 0.006} "
                f"{cx - 0.015},{flourish_y - 0.006} "
                f"{cx},{flourish_y} "
                f"C {cx + 0.015},{flourish_y - 0.006} "
                f"{cx + 0.035},{flourish_y - 0.006} "
                f"{cx + half_width},{flourish_y + 0.004}"
            ),
            xref="x",
            yref="y",
            line=dict(
                color="rgba(225,185,116,0.75)",
                width=1.0,
            ),
            layer="above",
        )

        # Small decorative centre
        fig.add_annotation(
            x=cx,
            y=flourish_y,
            text="❦",
            showarrow=False,
            xanchor="center",
            yanchor="middle",
            font=dict(
                family="Georgia, serif",
                size=11,
                color="#D7AE70",
            ),
        )

        # -----------------------------------------------------
        # 4. Individual book stars
        # -----------------------------------------------------

        for (_, book), (x, y) in zip(group.iterrows(), positions,):

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

            source_key = (color, significance)

            if source_key not in star_sources:
                sharp_source = _starburst_source(
                    original_star,
                    color,
                    significance,
                )

                star_sources[source_key] = (
                    sharp_source,
                    _starburst_glow(sharp_source),
                )

            starburst_source, glow_source = star_sources[source_key]

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
            image_width = 0.038 * size / 27
            image_height = 0.105 * size / 27

            # Soft radiance behind the sharp illustrated star.
            fig.add_layout_image(
                dict(
                    source=glow_source,
                    xref="x",
                    yref="y",
                    x=x,
                    y=y,
                    xanchor="center",
                    yanchor="middle",
                    sizex=image_width * 1.65,
                    sizey=image_height * 1.65,
                    sizing="contain",
                    opacity=0.42,
                    layer="below",
                )
            )

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
            # 7. Labels — handwritten title + smaller metadata
            # -------------------------------------------------

            right_edge = x >= 0.72

            # Distance from star to label, in pixels.
            label_gap = size / 2 + 25

            xshift = -label_gap if right_edge else label_gap
            xanchor = "right" if right_edge else "left"

            # Vertical positions, in pixels.
            title_yshift = 9
            meta_yshift = -13

            # Title: larger, calligraphic lettering.
            fig.add_annotation(
                x=x,
                y=y,
                text=f"<i>{escape(title)}</i>",
                showarrow=False,
                xshift=xshift,
                yshift=title_yshift,
                xanchor=xanchor,
                yanchor="middle",
                font=dict(
                    family="Georgia, serif",
                    size=16 if significance == "treasure" else 14,
                    color="#F6DEB3",
                ),
                align="left",
            )

            # Reading year and page count: quieter, conventional serif.
            metadata = escape(str(book["year"]))

            if pd.notna(book["pages"]):
                metadata += f" · {int(book['pages']):,} pages"

            fig.add_annotation(
                x=x,
                y=y,
                text=metadata,
                showarrow=False,
                xshift=xshift,
                yshift=meta_yshift,
                xanchor=xanchor,
                yanchor="middle",
                font=dict(
                    family="Georgia, serif",
                    size=11,
                    color="#D8C8AF",
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

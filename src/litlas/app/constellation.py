from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go


CONSTELLATION_COLORS = {
    "Ideas & Society": "#F0C36A",
    "Classics": "#D7E9FF",
    "Close to Heart": "#FFD47A",
    "Personal Growth": "#F6B35E",
    "Human Nature": "#CFE6FF",
    "Epic Journeys": "#FFD47A",
    "Mystery & Suspense": "#F1C778",
    "Yearly Highlights": "#CFE6FF",
}


def load_constellation_books(csv_path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    required = {
        "title",
        "author",
        "year",
        "constellation",
        "significance",
        "show_label",
        "x",
        "y",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Constellation CSV missing columns: {', '.join(sorted(missing))}"
        )

    df["year"] = df["year"].astype(str)
    df["show_label"] = (
        df["show_label"].astype(str).str.strip().str.lower().isin(
            ["yes", "true", "1"]
        )
    )
    df["significance"] = (
        df["significance"].astype(str).str.strip().str.lower()
    )

    return df


def build_constellation_figure(
    df: pd.DataFrame,
    title: str = "My Literary Constellation",
    height: int = 540,
) -> go.Figure:
    fig = go.Figure()

    # --- soft night-sky background stars
    rng = np.random.default_rng(42)
    bg_x = rng.uniform(0.03, 0.97, 140)
    bg_y = rng.uniform(0.05, 0.95, 140)
    bg_size = rng.uniform(1.2, 3.0, 140)

    fig.add_trace(
        go.Scatter(
            x=bg_x,
            y=bg_y,
            mode="markers",
            marker=dict(
                size=bg_size,
                color="rgba(243, 205, 130, 0.45)",
            ),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # --- constellation connection lines
    for constellation, group in df.groupby("constellation"):
        group = group.sort_values(["x", "y"]).reset_index(drop=True)

        if len(group) >= 2:
            fig.add_trace(
                go.Scatter(
                    x=group["x"],
                    y=group["y"],
                    mode="lines",
                    line=dict(
                        color="rgba(214, 176, 102, 0.38)",
                        width=1.4,
                        dash="dot",
                    ),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

    # --- plot books
    for _, row in df.iterrows():
        constellation = row["constellation"]
        color = CONSTELLATION_COLORS.get(constellation, "#FFD47A")

        is_anchor = row["significance"] == "anchor"
        glow_size = 44 if is_anchor else 30
        star_size = 26 if is_anchor else 18

        # outer glow
        fig.add_trace(
            go.Scatter(
                x=[row["x"]],
                y=[row["y"]],
                mode="markers",
                marker=dict(
                    size=glow_size,
                    color=color,
                    opacity=0.22,
                    line=dict(width=0),
                ),
                hoverinfo="skip",
                showlegend=False,
            )
        )

        # star itself
        fig.add_trace(
            go.Scatter(
                x=[row["x"]],
                y=[row["y"]],
                mode="markers",
                marker=dict(
                    symbol="star",
                    size=star_size,
                    color=color,
                    line=dict(color="#FFF2CC", width=1),
                ),
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "%{customdata[1]}<br>"
                    "%{customdata[2]}<br>"
                    "%{customdata[3]}"
                    "<extra></extra>"
                ),
                customdata=[[
                    row["title"],
                    row["author"],
                    row["year"],
                    row["constellation"],
                ]],
                showlegend=False,
            )
        )

        # label
        if row["show_label"]:
            if row["x"] > 0.72:
                xshift = -16
                xanchor = "right"
            else:
                xshift = 16
                xanchor = "left"

            fig.add_annotation(
                x=row["x"],
                y=row["y"],
                text=f"<i>{row['title']}</i>",
                showarrow=False,
                xanchor=xanchor,
                yanchor="middle",
                xshift=xshift,
                font=dict(
                    family="Georgia, serif",
                    size=12 if is_anchor else 11,
                    color="#F6D193",
                ),
                align="left",
            )

    # --- constellation titles
    for constellation, group in df.groupby("constellation"):
        cx = group["x"].mean()
        cy = min(0.95, group["y"].max() + 0.10)

        fig.add_annotation(
            x=cx,
            y=cy,
            text=constellation,
            showarrow=False,
            font=dict(
                family="Georgia, serif",
                size=16,
                color="#E8BE77",
            ),
            align="center",
        )

    fig.update_xaxes(
        visible=False,
        range=[0, 1],
        fixedrange=True,
    )
    fig.update_yaxes(
        visible=False,
        range=[0, 1],
        fixedrange=True,
        scaleanchor=None,
    )

    fig.update_layout(
        title=dict(
            text=title,
            x=0.02,
            xanchor="left",
            font=dict(
                family="Georgia, serif",
                size=22,
                color="#6B4A32",
            ),
        ),
        paper_bgcolor="#15293D",
        plot_bgcolor="#15293D",
        height=height,
        margin=dict(l=20, r=20, t=60, b=20),
        showlegend=False,
    )

    return fig


def default_constellation_csv() -> Path:
    return (
        Path(__file__).resolve().parents[3]
        / "data"
        / "constellation_books.csv"
    )
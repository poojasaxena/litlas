
"""Literary Wanderlust visualization for Litlas."""

import pandas as pd
import plotly.graph_objects as go


def build_wanderlust_figure(data: pd.DataFrame) -> go.Figure:
    """Show new versus returning authors as percentages of yearly books."""

    plot = data.sort_values("year").copy()

    plot["new_percent"] = (
        plot["new_authors"] / plot["total_books"] * 100
    )
    plot["returning_percent"] = (
        plot["returning_authors"] / plot["total_books"] * 100
    )

    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            name="New Authors",
            x=plot["new_percent"],
            y=plot["year"].astype(str),
            orientation="h",
            marker=dict(
                color="#A47B43",
                line=dict(color="#8B634B", width=0.5),
            ),
            customdata=plot[["new_authors", "total_books"]].to_numpy(),
            hovertemplate=(
                "<b>%{y} · New authors</b><br>"
                "%{customdata[0]} of %{customdata[1]} books<br>"
                "%{x:.1f}%<extra></extra>"
            ),
        )
    )

    figure.add_trace(
        go.Bar(
            name="Returning Authors",
            x=plot["returning_percent"],
            y=plot["year"].astype(str),
            orientation="h",
            marker=dict(
                color="#D8C5A9",
                line=dict(color="#C5AA87", width=0.5),
            ),
            customdata=plot[["returning_authors", "total_books"]].to_numpy(),
            hovertemplate=(
                "<b>%{y} · Returning authors</b><br>"
                "%{customdata[0]} of %{customdata[1]} books<br>"
                "%{x:.1f}%<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        barmode="stack",
        height=470,
        margin=dict(l=10, r=15, t=45, b=15),
        paper_bgcolor="#FAF7F1",
        plot_bgcolor="#F5EFE4",
        font=dict(
            family="Georgia, serif",
            size=12,
            color="#58412F",
        ),
        xaxis=dict(
            title=None,
            range=[0, 100],
            tickvals=[0, 25, 50, 75, 100],
            ticksuffix="%",
            showgrid=True,
            gridcolor="#E1D4C2",
            zeroline=False,
        ),
        yaxis=dict(
            title=None,
            autorange="reversed",
            type="category",
            showgrid=False,
        ),
        legend=dict(
            orientation="h",
            x=0,
            y=1.13,
            xanchor="left",
            yanchor="top",
            font=dict(size=12),
        ),
        bargap=0.30,
        showlegend=True,
        hovermode="closest",
    )

    return figure

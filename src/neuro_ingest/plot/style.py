from __future__ import annotations

import plotly.graph_objects as go

PLOT_LAYOUT = {
    "template": "plotly_white",
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "#fbfcfe",
    "font": {
        "family": "Inter, Segoe UI, sans-serif",
        "size": 12,
        "color": "#18212f",
    },
    "colorway": [
        "#286f8f",
        "#b65f3b",
        "#5b8a72",
        "#7a6fb0",
        "#b18a35",
        "#3b7f7d",
        "#8b5f72",
        "#587092",
    ],
    "xaxis": {
        "gridcolor": "#edf2f7",
        "linecolor": "#b7c2d0",
        "showline": True,
        "ticks": "outside",
        "tickcolor": "#b7c2d0",
        "tickfont": {"color": "#1f2937", "size": 11},
        "title": {"font": {"color": "#111827", "size": 12}},
        "zeroline": False,
    },
    "yaxis": {
        "gridcolor": "#e5ebf3",
        "linecolor": "#b7c2d0",
        "showline": True,
        "ticks": "outside",
        "tickcolor": "#b7c2d0",
        "tickfont": {"color": "#1f2937", "size": 11},
        "title": {"font": {"color": "#111827", "size": 12}},
        "zerolinecolor": "#d3dbe7",
        "automargin": True,
    },
    "legend": {
        "bgcolor": "rgba(255,255,255,0.82)",
        "bordercolor": "#dbe3ee",
        "borderwidth": 1,
        "font": {"color": "#1f2937", "size": 11},
        "title": {"font": {"color": "#111827", "size": 12}},
        "itemsizing": "constant",
    },
    "title": {"font": {"color": "#111827", "size": 15}},
    "hoverlabel": {
        "bgcolor": "#18212f",
        "bordercolor": "#18212f",
        "font": {"color": "#ffffff", "size": 12},
    },
    "margin": {"l": 56, "r": 24, "t": 44, "b": 46},
}


def apply_plot_style(fig: go.Figure) -> go.Figure:
    fig.update_layout(**PLOT_LAYOUT)
    fig.update_xaxes(
        gridcolor="#edf2f7",
        linecolor="#b7c2d0",
        tickcolor="#b7c2d0",
        tickfont={"color": "#1f2937", "size": 11},
        title_font={"color": "#111827", "size": 12},
        zeroline=False,
    )
    fig.update_yaxes(
        gridcolor="#e5ebf3",
        linecolor="#b7c2d0",
        tickcolor="#b7c2d0",
        tickfont={"color": "#1f2937", "size": 11},
        title_font={"color": "#111827", "size": 12},
        zerolinecolor="#d3dbe7",
    )
    fig.update_annotations(font={"color": "#111827", "size": 13})
    return fig

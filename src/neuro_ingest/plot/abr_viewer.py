from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd
import plotly.graph_objects as go
from plotly.colors import qualitative

from neuro_ingest.data.models import SessionData


class PlotService:
    def plot_abr(
        self,
        data: SessionData | pd.DataFrame,
        *,
        color_by: str = "level_db",
        group_by: str = "trace_uid",
        filters: dict[str, Any] | None = None,
        title: str = "ABR Traces",
    ) -> go.Figure:
        rows = self._to_dataframe(data)
        rows = self._apply_filters(rows, filters=filters or {})

        required = {"time_ms", "amplitude_uv", group_by}
        missing = sorted(required - set(rows.columns))
        if missing:
            raise ValueError(f"Cannot plot ABR. Missing columns: {missing}")
        if rows.empty:
            raise ValueError("No rows available for plotting after filters were applied.")

        color_map = self._build_color_map(rows, color_by=color_by)

        fig = go.Figure()
        grouped = rows.groupby(group_by, sort=False)
        for trace_id, chunk in grouped:
            chunk = chunk.sort_values("sample_idx")
            color_key = self._color_key(chunk, color_by=color_by)
            line_color = color_map.get(color_key, "#1f77b4")

            fig.add_trace(
                go.Scatter(
                    x=chunk["time_ms"],
                    y=chunk["amplitude_uv"],
                    mode="lines",
                    name=self._trace_label(trace_id=trace_id, chunk=chunk),
                    legendgroup=str(color_key),
                    line={"color": line_color, "width": 1.4},
                    hovertemplate=(
                        "time_ms=%{x:.3f}<br>"
                        "amplitude_uv=%{y:.3f}<br>"
                        "trace=%{fullData.name}<extra></extra>"
                    ),
                )
            )

        fig.update_layout(
            template="plotly_white",
            title=title,
            xaxis_title="Time (ms)",
            yaxis_title="Amplitude (uV)",
            legend_title=f"Traces (color by {color_by})",
            hovermode="closest",
            uirevision="abr-view",
        )
        # Keep the time axis fixed and allow amplitude zoom.
        fig.update_xaxes(fixedrange=True)
        return fig

    @staticmethod
    def _to_dataframe(data: SessionData | pd.DataFrame) -> pd.DataFrame:
        if isinstance(data, SessionData):
            return data.rows.copy()
        return data.copy()

    @staticmethod
    def _apply_filters(rows: pd.DataFrame, *, filters: dict[str, Any]) -> pd.DataFrame:
        out = rows
        for column, expected in filters.items():
            if column not in out.columns:
                raise ValueError(f"Unknown filter column: {column}")
            if isinstance(expected, Iterable) and not isinstance(expected, (str, bytes)):
                out = out[out[column].isin(list(expected))]
            else:
                out = out[out[column] == expected]
        return out

    @staticmethod
    def _build_color_map(rows: pd.DataFrame, *, color_by: str) -> dict[Any, str]:
        if color_by not in rows.columns:
            return {}

        palette = qualitative.Safe + qualitative.Dark24
        keys = list(pd.Series(rows[color_by]).dropna().unique())
        return {key: palette[idx % len(palette)] for idx, key in enumerate(keys)}

    @staticmethod
    def _color_key(chunk: pd.DataFrame, *, color_by: str) -> Any:
        if color_by not in chunk.columns:
            return "trace"
        return chunk[color_by].iloc[0]

    @staticmethod
    def _trace_label(*, trace_id: Any, chunk: pd.DataFrame) -> str:
        level = chunk["level_db"].iloc[0] if "level_db" in chunk.columns else "?"
        freq = chunk["freq_hz"].iloc[0] if "freq_hz" in chunk.columns else "?"
        return f"{trace_id} | {level} dB | {freq} Hz"

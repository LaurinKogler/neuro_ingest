from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Literal
import warnings

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.colors import qualitative
from plotly.subplots import make_subplots

from neuro_ingest.data.models import SessionData


RelationMode = Literal["ipsi", "ipsi_contra"]
IntensityOrder = Literal["desc", "asc"]


class PlotService:
    def plot_abr(
        self,
        data: SessionData | pd.DataFrame,
        *,
        color_by: str = "level_db",
        group_by: str = "trace_uid",
        filters: dict[str, Any] | None = None,
        title: str = "ABR Traces",
        frequency_hz: float | None = None,
        relation_mode: RelationMode = "ipsi",
        spacing_uv: float = 0.0,
        intensity_order: IntensityOrder = "desc",
    ) -> go.Figure:
        rows = self._to_dataframe(data)
        rows = self._apply_filters(rows, filters=filters or {})
        rows = self._prepare_relation_column(rows)

        required = {"time_ms", "amplitude_uv", "freq_hz", "level_db", group_by}
        missing = sorted(required - set(rows.columns))
        if missing:
            raise ValueError(f"Cannot plot ABR. Missing columns: {missing}")
        if rows.empty:
            raise ValueError("No rows available for plotting after filters were applied.")
        if spacing_uv < 0:
            raise ValueError("spacing_uv must be >= 0.")

        selected_freq = self._resolve_frequency(rows, frequency_hz=frequency_hz)
        freq_rows = rows[np.isclose(rows["freq_hz"].astype(float), float(selected_freq))]
        if freq_rows.empty:
            raise ValueError(f"No rows available for frequency_hz={selected_freq}.")

        color_map = self._build_color_map(freq_rows, color_by=color_by)
        offsets = self._build_offsets(freq_rows, group_by=group_by, spacing_uv=spacing_uv, intensity_order=intensity_order)

        effective_mode = relation_mode
        if relation_mode == "ipsi_contra":
            has_contra = (freq_rows["rel_ear"] == "contra").any()
            if not has_contra:
                warnings.warn("No contra rows available; falling back to ipsi-only plot.")
                effective_mode = "ipsi"

        if effective_mode == "ipsi":
            fig = go.Figure()
            plot_rows = freq_rows[freq_rows["rel_ear"] == "ipsi"]
            if plot_rows.empty:
                plot_rows = freq_rows
            self._add_traces(
                fig=fig,
                rows=plot_rows,
                group_by=group_by,
                color_by=color_by,
                color_map=color_map,
                offsets=offsets,
                subplot=None,
            )
            if relation_mode == "ipsi_contra":
                fig.add_annotation(
                    text="Contra unavailable: showing ipsi only",
                    showarrow=False,
                    x=0.5,
                    y=1.08,
                    xref="paper",
                    yref="paper",
                    font={"size": 12, "color": "#6b7280"},
                )
            fig.update_layout(
                template="plotly_white",
                title=f"{title} | {selected_freq:g} Hz | ipsi",
                xaxis_title="Time (ms)",
                yaxis_title="Amplitude (uV)",
                legend_title="Intensity (dB)",
                hovermode="closest",
                uirevision="abr-clinical",
            )
            fig.update_xaxes(fixedrange=True)
            return fig

        fig = make_subplots(rows=1, cols=2, subplot_titles=("ipsi", "contra"), shared_yaxes=True)
        ipsi_rows = freq_rows[freq_rows["rel_ear"] == "ipsi"]
        contra_rows = freq_rows[freq_rows["rel_ear"] == "contra"]

        self._add_traces(
            fig=fig,
            rows=ipsi_rows,
            group_by=group_by,
            color_by=color_by,
            color_map=color_map,
            offsets=offsets,
            subplot=(1, 1),
        )
        self._add_traces(
            fig=fig,
            rows=contra_rows,
            group_by=group_by,
            color_by=color_by,
            color_map=color_map,
            offsets=offsets,
            subplot=(1, 2),
        )
        fig.update_layout(
            template="plotly_white",
            title=f"{title} | {selected_freq:g} Hz | ipsi vs contra",
            legend_title="Intensity (dB)",
            hovermode="closest",
            uirevision="abr-clinical",
        )
        fig.update_xaxes(title_text="Time (ms)", fixedrange=True, row=1, col=1)
        fig.update_xaxes(title_text="Time (ms)", fixedrange=True, row=1, col=2)
        fig.update_yaxes(title_text="Amplitude (uV)", row=1, col=1)
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
    def _prepare_relation_column(rows: pd.DataFrame) -> pd.DataFrame:
        out = rows.copy()
        if "rel_ear" not in out.columns:
            out["rel_ear"] = "ipsi"
        out["rel_ear"] = out["rel_ear"].fillna("ipsi")
        return out

    @staticmethod
    def _resolve_frequency(rows: pd.DataFrame, *, frequency_hz: float | None) -> float:
        unique_freqs = sorted(float(x) for x in pd.Series(rows["freq_hz"]).dropna().unique())
        if not unique_freqs:
            raise ValueError("No frequency values available to plot.")

        if frequency_hz is None:
            if len(unique_freqs) > 1:
                raise ValueError("Multiple frequencies present. Please provide frequency_hz.")
            return unique_freqs[0]

        for freq in unique_freqs:
            if np.isclose(freq, float(frequency_hz)):
                return freq
        raise ValueError(f"frequency_hz={frequency_hz} not found in dataset frequencies: {unique_freqs}")

    @staticmethod
    def _build_color_map(rows: pd.DataFrame, *, color_by: str) -> dict[Any, str]:
        if color_by not in rows.columns:
            return {}
        palette = qualitative.Safe + qualitative.Dark24
        keys = list(pd.Series(rows[color_by]).dropna().unique())
        return {key: palette[idx % len(palette)] for idx, key in enumerate(keys)}

    @staticmethod
    def _build_offsets(
        rows: pd.DataFrame,
        *,
        group_by: str,
        spacing_uv: float,
        intensity_order: IntensityOrder,
    ) -> dict[Any, float]:
        if spacing_uv == 0:
            return {}

        by_trace = rows.groupby(group_by, sort=False)["level_db"].first()
        levels = sorted(by_trace.astype(float).unique(), reverse=(intensity_order == "desc"))
        rank = {level: idx for idx, level in enumerate(levels)}
        max_rank = len(levels) - 1

        offsets: dict[Any, float] = {}
        for trace_id, level in by_trace.items():
            r = rank[float(level)]
            offsets[trace_id] = (max_rank - r) * spacing_uv
        return offsets

    def _add_traces(
        self,
        *,
        fig: go.Figure,
        rows: pd.DataFrame,
        group_by: str,
        color_by: str,
        color_map: dict[Any, str],
        offsets: dict[Any, float],
        subplot: tuple[int, int] | None,
    ) -> None:
        if rows.empty:
            return

        shown_levels: set[float] = set()
        grouped = rows.groupby(group_by, sort=False)
        for trace_id, chunk in grouped:
            chunk = chunk.sort_values("sample_idx")
            level = float(chunk["level_db"].iloc[0])
            offset = offsets.get(trace_id, 0.0)
            y = chunk["amplitude_uv"] + offset
            color_key = chunk[color_by].iloc[0] if color_by in chunk.columns else level
            line_color = color_map.get(color_key, "#1f77b4")
            showlegend = level not in shown_levels
            shown_levels.add(level)

            trace = go.Scatter(
                x=chunk["time_ms"],
                y=y,
                mode="lines",
                name=f"{level:g} dB",
                legendgroup=f"level-{level:g}",
                showlegend=showlegend,
                line={"color": line_color, "width": 1.4},
                hovertemplate=(
                    "time_ms=%{x:.3f}<br>"
                    "amplitude_uv=%{y:.3f}<br>"
                    f"trace={trace_id}<br>"
                    f"level_db={level:g}<extra></extra>"
                ),
            )

            if subplot is None:
                fig.add_trace(trace)
            else:
                fig.add_trace(trace, row=subplot[0], col=subplot[1])

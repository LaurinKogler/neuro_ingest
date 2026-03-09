from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from neuro_ingest.ingest.ihs import IHSIngestor
from neuro_ingest.ingest.tdt import TDTIngestor
from neuro_ingest.plot.abr_viewer import PlotService


def _ihs_rows() -> pd.DataFrame:
    return IHSIngestor().ingest(
        paths=[Path("tests/data/X48_d0_Click.TXT")],
        animal_id="X48",
        session_date=date(2025, 1, 1),
        paradigm="abr",
        day=0,
        session_id="X48_20250101",
    )


def _tdt_rows() -> pd.DataFrame:
    return TDTIngestor().ingest(
        paths=[Path("tests/data/AC04_ClickABR_right_20251017.txt")],
        animal_id="AC04",
        session_date=date(2025, 10, 17),
        paradigm="abr",
        day=0,
        session_id="AC04_20251017",
    )


def test_requires_explicit_frequency_when_multiple_present():
    rows = _tdt_rows().copy()
    rows.loc[rows.index[:50], "freq_hz"] = 4000.0

    with pytest.raises(ValueError, match="Multiple frequencies present"):
        PlotService().plot_abr(rows)


def test_ipsi_contra_mode_builds_two_horizontal_panels_for_ihs():
    rows = _ihs_rows()
    fig = PlotService().plot_abr(rows, frequency_hz=0.0, relation_mode="ipsi_contra")
    layout = fig.to_plotly_json()["layout"]
    assert "xaxis2" in layout
    assert fig.layout.xaxis.fixedrange is True
    assert fig.layout.xaxis2.fixedrange is True


def test_ipsi_contra_mode_falls_back_when_contra_missing():
    rows = _tdt_rows()
    fig = PlotService().plot_abr(rows, frequency_hz=0.0, relation_mode="ipsi_contra")
    ann_text = [ann.text for ann in fig.layout.annotations or []]
    assert any("Contra unavailable" in str(t) for t in ann_text)
    layout = fig.to_plotly_json()["layout"]
    assert "xaxis2" not in layout


def test_spacing_adds_deterministic_intensity_offsets():
    rows = pd.DataFrame(
        [
            {"trace_uid": "t_high", "freq_hz": 4000.0, "level_db": 90.0, "rel_ear": "ipsi", "sample_idx": 0, "time_ms": 0.0, "amplitude_uv": 1.0},
            {"trace_uid": "t_high", "freq_hz": 4000.0, "level_db": 90.0, "rel_ear": "ipsi", "sample_idx": 1, "time_ms": 0.5, "amplitude_uv": 2.0},
            {"trace_uid": "t_low", "freq_hz": 4000.0, "level_db": 70.0, "rel_ear": "ipsi", "sample_idx": 0, "time_ms": 0.0, "amplitude_uv": 1.0},
            {"trace_uid": "t_low", "freq_hz": 4000.0, "level_db": 70.0, "rel_ear": "ipsi", "sample_idx": 1, "time_ms": 0.5, "amplitude_uv": 2.0},
        ]
    )

    fig0 = PlotService().plot_abr(rows, frequency_hz=4000.0, spacing_uv=0.0)
    fig1 = PlotService().plot_abr(rows, frequency_hz=4000.0, spacing_uv=10.0)

    y0_high = np.array(fig0.data[0].y, dtype=float)
    y1_high = np.array(fig1.data[0].y, dtype=float)
    y0_low = np.array(fig0.data[1].y, dtype=float)
    y1_low = np.array(fig1.data[1].y, dtype=float)

    assert np.allclose(y1_high - y0_high, 10.0)
    assert np.allclose(y1_low - y0_low, 0.0)


def test_amplitude_scale_multiplies_waveform_values():
    rows = pd.DataFrame(
        [
            {"trace_uid": "t1", "freq_hz": 8000.0, "level_db": 80.0, "rel_ear": "ipsi", "sample_idx": 0, "time_ms": 0.0, "amplitude_uv": 1.5},
            {"trace_uid": "t1", "freq_hz": 8000.0, "level_db": 80.0, "rel_ear": "ipsi", "sample_idx": 1, "time_ms": 0.5, "amplitude_uv": -2.0},
        ]
    )
    fig1 = PlotService().plot_abr(rows, frequency_hz=8000.0, amplitude_scale=1.0)
    fig2 = PlotService().plot_abr(rows, frequency_hz=8000.0, amplitude_scale=3.0)

    y1 = np.array(fig1.data[0].y, dtype=float)
    y2 = np.array(fig2.data[0].y, dtype=float)
    assert np.allclose(y2, y1 * 3.0)


def test_plot_uses_taller_default_height_and_allows_override():
    rows = _tdt_rows()
    fig_default = PlotService().plot_abr(rows, frequency_hz=0.0)
    assert int(fig_default.layout.height) >= 700

    fig_override = PlotService().plot_abr(rows, frequency_hz=0.0, figure_height_px=920)
    assert int(fig_override.layout.height) == 920


def test_legend_order_follows_intensity_order():
    rows = pd.DataFrame(
        [
            {"trace_uid": "t_low", "freq_hz": 4000.0, "level_db": 70.0, "rel_ear": "ipsi", "sample_idx": 0, "time_ms": 0.0, "amplitude_uv": 1.0},
            {"trace_uid": "t_low", "freq_hz": 4000.0, "level_db": 70.0, "rel_ear": "ipsi", "sample_idx": 1, "time_ms": 0.5, "amplitude_uv": 2.0},
            {"trace_uid": "t_high", "freq_hz": 4000.0, "level_db": 90.0, "rel_ear": "ipsi", "sample_idx": 0, "time_ms": 0.0, "amplitude_uv": 1.0},
            {"trace_uid": "t_high", "freq_hz": 4000.0, "level_db": 90.0, "rel_ear": "ipsi", "sample_idx": 1, "time_ms": 0.5, "amplitude_uv": 2.0},
        ]
    )

    fig_desc = PlotService().plot_abr(rows, frequency_hz=4000.0, intensity_order="desc")
    desc_legend_names = [trace.name for trace in fig_desc.data if trace.showlegend]
    assert desc_legend_names == ["90 dB", "70 dB"]

    fig_asc = PlotService().plot_abr(rows, frequency_hz=4000.0, intensity_order="asc")
    asc_legend_names = [trace.name for trace in fig_asc.data if trace.showlegend]
    assert asc_legend_names == ["70 dB", "90 dB"]


def test_legend_order_stays_sorted_when_levels_first_appear_in_contra_panel():
    rows = pd.DataFrame(
        [
            {"trace_uid": "ipsi_70", "freq_hz": 4000.0, "level_db": 70.0, "rel_ear": "ipsi", "sample_idx": 0, "time_ms": 0.0, "amplitude_uv": 1.0},
            {"trace_uid": "ipsi_70", "freq_hz": 4000.0, "level_db": 70.0, "rel_ear": "ipsi", "sample_idx": 1, "time_ms": 0.5, "amplitude_uv": 2.0},
            {"trace_uid": "contra_90", "freq_hz": 4000.0, "level_db": 90.0, "rel_ear": "contra", "sample_idx": 0, "time_ms": 0.0, "amplitude_uv": 1.0},
            {"trace_uid": "contra_90", "freq_hz": 4000.0, "level_db": 90.0, "rel_ear": "contra", "sample_idx": 1, "time_ms": 0.5, "amplitude_uv": 2.0},
        ]
    )

    fig = PlotService().plot_abr(
        rows,
        frequency_hz=4000.0,
        relation_mode="ipsi_contra",
        intensity_order="desc",
    )
    legend_names = [trace.name for trace in fig.data if trace.showlegend]
    assert legend_names == ["90 dB", "70 dB"]

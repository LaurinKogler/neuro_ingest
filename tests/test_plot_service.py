from datetime import date
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import pytest

from neuro_ingest.ingest.tdt import TDTIngestor
from neuro_ingest.plot.abr_viewer import PlotService


def _rows() -> pd.DataFrame:
    return TDTIngestor().ingest(
        paths=[Path("tests/data/AC04_ClickABR_right_20251017.txt")],
        animal_id="AC04",
        session_date=date(2025, 10, 17),
        paradigm="abr",
        day=0,
        session_id="AC04_20251017",
    )


def test_plot_service_builds_figure():
    fig = PlotService().plot_abr(_rows(), color_by="level_db")
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0
    assert fig.layout.xaxis.fixedrange is True


def test_plot_service_filters_rows():
    rows = _rows()
    target_level = float(rows["level_db"].iloc[0])
    fig = PlotService().plot_abr(rows, filters={"level_db": target_level})
    assert len(fig.data) > 0


def test_plot_service_missing_required_column_raises():
    rows = _rows().drop(columns=["time_ms"])
    with pytest.raises(ValueError, match="Missing columns"):
        PlotService().plot_abr(rows)

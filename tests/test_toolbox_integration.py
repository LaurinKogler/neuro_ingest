from datetime import date
from pathlib import Path

import plotly.graph_objects as go
import pandas as pd

from neuro_ingest.toolbox import NeuroAudioToolbox


def test_toolbox_end_to_end(tmp_path: Path):
    src = Path("tests/data/AC04_ClickABR_right_20251017.txt")
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / src.name).write_bytes(src.read_bytes())

    toolbox = NeuroAudioToolbox(
        db_path=tmp_path / "neuro_audio.duckdb",
        parquet_dir=tmp_path / "normalized",
    )

    session = toolbox.ingest(
        system="TDT",
        input_path=input_dir,
        animal_id="AC04",
        session_date=date(2025, 10, 17),
        day=1,
        tdt_ear="right",
    )
    write_result = toolbox.save(session, overwrite=True)

    assert write_result.parquet_path.exists()
    assert write_result.db_path.exists()

    sessions = toolbox.list_sessions()
    assert len(sessions) == 1

    subset = toolbox.query(
        "SELECT * FROM samples WHERE session_id = ? LIMIT 500",
        params=[session.session_id],
    )
    assert len(subset) > 0

    subset_no_sql = toolbox.get_samples(
        animal_id="AC04",
        day=1,
        session_id=session.session_id,
        system="TDT",
        limit=1000,
    )
    assert len(subset_no_sql) > 0

    fig = toolbox.plot(subset, color_by="level_db")
    assert isinstance(fig, go.Figure)
    fig2 = toolbox.plot(
        subset,
        color_by="level_db",
        frequency_hz=0.0,
        relation_mode="ipsi",
        spacing_uv=5.0,
    )
    assert isinstance(fig2, go.Figure)

    trace_summary = toolbox.list_trace_summaries(session_id=session.session_id)
    assert len(trace_summary) > 0

    trace_uid = str(trace_summary.iloc[0]["trace_uid"])
    edit_result = toolbox.update_trace_fields(
        session_id=session.session_id,
        trace_uids=[trace_uid],
        updates={"stim_ear": "left"},
    )
    assert edit_result.rows_affected > 0


def test_toolbox_ingests_ihs_to_duckdb_and_parquet(tmp_path: Path):
    src = Path("tests/data/X48_d0_Click.TXT")
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / src.name).write_bytes(src.read_bytes())

    toolbox = NeuroAudioToolbox(
        db_path=tmp_path / "ihs.duckdb",
        parquet_dir=tmp_path / "normalized",
    )

    session = toolbox.ingest(
        system="IHS",
        input_path=input_dir,
        animal_id="X48",
        session_date=date(2025, 1, 1),
        day=0,
        session_id="X48_20250101",
    )
    write_result = toolbox.save(session, overwrite=True)

    db_rows = toolbox.query(
        "SELECT COUNT(*) AS n FROM samples WHERE session_id = ? AND system = 'IHS'",
        params=[session.session_id],
    )
    parquet_rows = pd.read_parquet(write_result.parquet_path, engine="pyarrow")

    assert write_result.db_path.exists()
    assert write_result.parquet_path.exists()
    assert int(db_rows.iloc[0]["n"]) == len(session.rows)
    assert len(parquet_rows) == len(session.rows)
    assert parquet_rows["system"].unique().tolist() == ["IHS"]

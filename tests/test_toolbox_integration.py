from datetime import date
from pathlib import Path

import plotly.graph_objects as go

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

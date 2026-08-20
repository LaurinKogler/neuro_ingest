from datetime import date
from pathlib import Path

import pytest

from neuro_ingest.toolbox import NeuroAudioToolbox
from neuro_ingest.ui.workflow import (
    VIEWER_SOURCE_OPTIONS,
    combine_sessions,
    default_viewer_source_index,
    discover_duckdb_paths,
    format_frequency_label,
    infer_tdt_ear_from_upload_names,
    ingest_and_save,
    parse_day_filter,
    resolve_system,
    stage_uploaded_files,
)


class FakeUpload:
    def __init__(self, name: str, content: bytes):
        self.name = name
        self._content = content

    def getbuffer(self) -> bytes:
        return self._content


def test_stage_uploaded_files(tmp_path: Path):
    uploads = [
        FakeUpload("a.txt", b"hello"),
        FakeUpload("b.txt", b"world"),
    ]
    staged = stage_uploaded_files(uploads, tmp_path)

    assert len(staged) == 2
    assert staged[0].read_bytes() == b"hello"
    assert staged[1].read_bytes() == b"world"


def test_resolve_system_auto_detects_tdt():
    path = Path("tests/data/AC04_ClickABR_right_20251017.txt")
    assert resolve_system("Auto", [path]) == "TDT"


def test_infer_tdt_ear_from_upload_names():
    uploads = [FakeUpload("AC04_ClickABR_right_20251017.txt", b"x")]
    assert infer_tdt_ear_from_upload_names(uploads) == "right"


def test_default_viewer_source_prefers_duckdb_filters_without_last_session():
    index = default_viewer_source_index(has_last_ingested_session=False)

    assert VIEWER_SOURCE_OPTIONS[index] == "DuckDB filters (no SQL)"


def test_default_viewer_source_prefers_last_ingested_session_when_available():
    index = default_viewer_source_index(has_last_ingested_session=True)

    assert VIEWER_SOURCE_OPTIONS[index] == "Last ingested session"


def test_parse_day_filter_accepts_empty_plain_and_d_prefixed_values():
    assert parse_day_filter("") is None
    assert parse_day_filter("14") == 14
    assert parse_day_filter("d14") == 14
    assert parse_day_filter("D14") == 14
    assert parse_day_filter("d 14") == 14


def test_parse_day_filter_rejects_invalid_values():
    with pytest.raises(ValueError, match="optionally prefixed"):
        parse_day_filter("day14")


def test_format_frequency_label_calls_zero_click():
    assert format_frequency_label(0.0) == "Click"
    assert format_frequency_label("0") == "Click"
    assert format_frequency_label(16000.0) == "16000 Hz"


def test_discover_duckdb_paths_lists_existing_databases(tmp_path: Path):
    db_a = tmp_path / "a.duckdb"
    db_b = tmp_path / "nested" / "b.duckdb"
    backup_db = tmp_path / "backups" / "a_20260820.duckdb"
    db_b.parent.mkdir()
    backup_db.parent.mkdir()
    db_a.write_bytes(b"")
    db_b.write_bytes(b"")
    backup_db.write_bytes(b"")

    paths = discover_duckdb_paths([tmp_path], fallback=tmp_path / "missing.duckdb")

    assert paths == sorted([str(db_a), str(db_b)], key=lambda value: value.lower())


def test_ingest_and_save_with_toolbox(tmp_path: Path):
    src = Path("tests/data/AC04_ClickABR_right_20251017.txt")
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / src.name).write_bytes(src.read_bytes())

    toolbox = NeuroAudioToolbox(
        db_path=tmp_path / "ui_ingest.duckdb",
        parquet_dir=tmp_path / "normalized",
    )

    session, result = ingest_and_save(
        toolbox=toolbox,
        system="TDT",
        input_dir=input_dir,
        animal_id="AC04",
        session_date=date(2025, 10, 17),
        paradigm="abr",
        day=0,
        session_id=None,
        overwrite=True,
        tdt_ear="right",
    )

    assert len(session.rows) > 0
    assert result.parquet_path.exists()
    assert result.db_path.exists()


def test_combine_sessions_merges_left_and_right_into_one_session(tmp_path: Path):
    src = Path("tests/data/AC04_ClickABR_right_20251017.txt")
    left_dir = tmp_path / "left"
    right_dir = tmp_path / "right"
    left_dir.mkdir()
    right_dir.mkdir()
    (left_dir / src.name).write_bytes(src.read_bytes())
    (right_dir / src.name).write_bytes(src.read_bytes())

    toolbox = NeuroAudioToolbox(
        db_path=tmp_path / "combined.duckdb",
        parquet_dir=tmp_path / "normalized",
    )

    left_session = toolbox.ingest(
        system="TDT",
        input_path=left_dir,
        animal_id="AC04",
        session_date=date(2025, 10, 17),
        session_id="AC04_20251017",
        tdt_ear="left",
    )
    right_session = toolbox.ingest(
        system="TDT",
        input_path=right_dir,
        animal_id="AC04",
        session_date=date(2025, 10, 17),
        session_id="AC04_20251017",
        tdt_ear="right",
    )

    combined = combine_sessions([left_session, right_session])
    assert combined.session_id == "AC04_20251017"
    assert len(combined.rows) == len(left_session.rows) + len(right_session.rows)
    assert set(combined.rows["stim_ear"].dropna().unique().tolist()) == {"left", "right"}

from datetime import date
from pathlib import Path

from neuro_ingest.data.models import SessionData
from neuro_ingest.ingest.tdt import TDTIngestor
from neuro_ingest.storage.duckdb_store import DuckDBStore
from neuro_ingest.storage.editor import DuckDBEditor


def _build_session(session_id: str = "AC04_20251017") -> SessionData:
    rows = TDTIngestor().ingest(
        paths=[Path("tests/data/AC04_ClickABR_right_20251017.txt")],
        animal_id="AC04",
        session_date=date(2025, 10, 17),
        paradigm="abr",
        day=0,
        session_id=session_id,
    ).copy()
    rows["stim_ear"] = "right"
    rows["rec_ear"] = "right"
    rows["rel_ear"] = "ipsi"
    return SessionData(
        session_id=session_id,
        system="TDT",
        animal_id="AC04",
        session_date=date(2025, 10, 17),
        paradigm="abr",
        rows=rows,
    )


def test_editor_can_create_backup(tmp_path: Path):
    db_path = tmp_path / "sessions.duckdb"
    store = DuckDBStore(db_path=db_path)
    store.append_session(_build_session())

    editor = DuckDBEditor(db_path=db_path)
    backup = editor.create_backup()
    assert backup.exists()
    assert backup.suffix == ".duckdb"


def test_editor_updates_trace_metadata(tmp_path: Path):
    db_path = tmp_path / "sessions.duckdb"
    store = DuckDBStore(db_path=db_path)
    session = _build_session()
    store.append_session(session)

    trace_uid = str(session.rows["trace_uid"].iloc[0])
    editor = DuckDBEditor(db_path=db_path)
    result = editor.update_trace_fields(
        session_id=session.session_id,
        trace_uids=[trace_uid],
        updates={"stim_ear": "left", "rec_ear": "left", "rel_ear": "ipsi"},
    )
    assert result.rows_affected > 0

    updated = store.query(
        "SELECT DISTINCT stim_ear, rec_ear, rel_ear FROM samples WHERE session_id = ? AND trace_uid = ?",
        [session.session_id, trace_uid],
    )
    assert updated.iloc[0]["stim_ear"] == "left"
    assert updated.iloc[0]["rec_ear"] == "left"
    assert updated.iloc[0]["rel_ear"] == "ipsi"


def test_editor_deletes_traces_and_refreshes_session_count(tmp_path: Path):
    db_path = tmp_path / "sessions.duckdb"
    store = DuckDBStore(db_path=db_path)
    session = _build_session()
    store.append_session(session)

    editor = DuckDBEditor(db_path=db_path)
    all_traces = sorted(set(session.rows["trace_uid"].astype(str)))
    target_trace = all_traces[0]
    rows_for_target = int((session.rows["trace_uid"].astype(str) == target_trace).sum())
    before = int(store.query("SELECT COUNT(*) AS n FROM samples").iloc[0]["n"])

    result = editor.delete_traces(
        session_id=session.session_id,
        trace_uids=[target_trace],
    )
    assert result.rows_affected == rows_for_target

    after = int(store.query("SELECT COUNT(*) AS n FROM samples").iloc[0]["n"])
    assert after == before - rows_for_target

    sessions = store.list_sessions()
    assert int(sessions.iloc[0]["row_count"]) == after


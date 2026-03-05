from datetime import date
from pathlib import Path

import pytest

from neuro_ingest.data.models import SessionData
from neuro_ingest.ingest.tdt import TDTIngestor
from neuro_ingest.storage.duckdb_store import DuckDBStore


def _build_session(session_id: str = "AC04_20251017") -> SessionData:
    rows = TDTIngestor().ingest(
        paths=[Path("tests/data/AC04_ClickABR_right_20251017.txt")],
        animal_id="AC04",
        session_date=date(2025, 10, 17),
        paradigm="abr",
        day=0,
        session_id=session_id,
    )
    return SessionData(
        session_id=session_id,
        system="TDT",
        animal_id="AC04",
        session_date=date(2025, 10, 17),
        paradigm="abr",
        rows=rows,
    )


def test_duckdb_store_append_and_query(tmp_path: Path):
    store = DuckDBStore(db_path=tmp_path / "sessions.duckdb")
    session = _build_session()
    store.append_session(session)

    sessions = store.list_sessions()
    assert len(sessions) == 1
    assert sessions.iloc[0]["session_id"] == "AC04_20251017"

    row_count = store.query("SELECT COUNT(*) AS n FROM samples")
    assert int(row_count.iloc[0]["n"]) == len(session.rows)


def test_duckdb_store_conflict_raises(tmp_path: Path):
    store = DuckDBStore(db_path=tmp_path / "sessions.duckdb")
    session = _build_session()
    store.append_session(session)

    with pytest.raises(FileExistsError, match="Session already exists"):
        store.append_session(session, overwrite=False)


def test_duckdb_store_schema_mismatch_rolls_back(tmp_path: Path):
    store = DuckDBStore(db_path=tmp_path / "sessions.duckdb")
    session = _build_session()
    store.append_session(session)

    rows2 = session.rows.copy()
    rows2.loc[:, "session_id"] = "AC04_20251018"
    rows2.loc[:, "extra_debug_col"] = "x"
    session2 = SessionData(
        session_id="AC04_20251018",
        system="TDT",
        animal_id="AC04",
        session_date=date(2025, 10, 17),
        paradigm="abr",
        rows=rows2,
    )

    with pytest.raises(ValueError, match="schema"):
        store.append_session(session2)

    sessions = store.list_sessions()
    assert sessions["session_id"].tolist() == ["AC04_20251017"]

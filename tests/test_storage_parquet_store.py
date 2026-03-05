from datetime import date
from pathlib import Path

import pytest

from neuro_ingest.data.models import SessionData
from neuro_ingest.ingest.tdt import TDTIngestor
from neuro_ingest.storage.parquet_store import ParquetStore


def _build_session() -> SessionData:
    rows = TDTIngestor().ingest(
        paths=[Path("tests/data/AC04_ClickABR_right_20251017.txt")],
        animal_id="AC04",
        session_date=date(2025, 10, 17),
        paradigm="abr",
        day=0,
        session_id="AC04_20251017",
    )
    return SessionData(
        session_id="AC04_20251017",
        system="TDT",
        animal_id="AC04",
        session_date=date(2025, 10, 17),
        paradigm="abr",
        rows=rows,
    )


def test_parquet_store_roundtrip(tmp_path: Path):
    store = ParquetStore(root_dir=tmp_path)
    session = _build_session()

    out_path = store.save_session(session)
    reloaded = store.load(out_path)

    assert out_path.exists()
    assert len(reloaded) == len(session.rows)
    assert set(reloaded.columns) == set(session.rows.columns)


def test_parquet_store_conflict_raises(tmp_path: Path):
    store = ParquetStore(root_dir=tmp_path)
    session = _build_session()
    store.save_session(session)

    with pytest.raises(FileExistsError, match="Output exists"):
        store.save_session(session, overwrite=False)

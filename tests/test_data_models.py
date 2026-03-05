from datetime import date
from pathlib import Path

import pytest

from neuro_ingest.data.models import SessionData
from neuro_ingest.ingest.tdt import TDTIngestor


def _make_rows():
    return TDTIngestor().ingest(
        paths=[Path("tests/data/AC04_ClickABR_right_20251017.txt")],
        animal_id="AC04",
        session_date=date(2025, 10, 17),
        paradigm="abr",
        day=0,
        session_id="AC04_20251017",
    )


def test_session_data_valid():
    rows = _make_rows()
    session = SessionData(
        session_id="AC04_20251017",
        system="TDT",
        animal_id="AC04",
        session_date=date(2025, 10, 17),
        paradigm="abr",
        rows=rows,
    )
    assert len(session.rows) > 0


def test_session_data_missing_required_column_raises():
    rows = _make_rows().drop(columns=["amplitude_uv"])
    with pytest.raises(ValueError, match="missing required columns"):
        SessionData(
            session_id="AC04_20251017",
            system="TDT",
            animal_id="AC04",
            session_date=date(2025, 10, 17),
            paradigm="abr",
            rows=rows,
        )


def test_session_data_inconsistent_metadata_raises():
    rows = _make_rows().copy()
    rows.loc[:, "animal_id"] = "WRONG"
    with pytest.raises(ValueError, match="animal_id"):
        SessionData(
            session_id="AC04_20251017",
            system="TDT",
            animal_id="AC04",
            session_date=date(2025, 10, 17),
            paradigm="abr",
            rows=rows,
        )

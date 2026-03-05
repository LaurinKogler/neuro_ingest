from datetime import date
from pathlib import Path

import pytest

from neuro_ingest.ingest.service import IngestService


def test_ingest_service_ingests_tdt_folder(tmp_path: Path):
    src = Path("tests/data/AC04_ClickABR_right_20251017.txt")
    folder = tmp_path / "input"
    folder.mkdir()
    (folder / src.name).write_bytes(src.read_bytes())

    service = IngestService()
    session = service.ingest_path(
        system="TDT",
        input_path=folder,
        animal_id="AC04",
        session_date=date(2025, 10, 17),
    )

    assert session.system == "TDT"
    assert session.session_id == "AC04_20251017"
    assert len(session.rows) > 0


def test_ingest_service_requires_compatible_files(tmp_path: Path):
    folder = tmp_path / "input"
    folder.mkdir()
    (folder / "notes.md").write_text("not data")

    service = IngestService()
    with pytest.raises(FileNotFoundError, match="TDT-compatible"):
        service.ingest_path(
            system="TDT",
            input_path=folder,
            animal_id="AC04",
            session_date=date(2025, 10, 17),
        )


def test_ingest_service_rejects_unknown_system():
    service = IngestService()
    with pytest.raises(ValueError, match="Unsupported system"):
        service.ingest_path(
            system="UNKNOWN",
            input_path=Path("tests/data/AC04_ClickABR_right_20251017.txt"),
            animal_id="AC04",
            session_date=date(2025, 10, 17),
        )

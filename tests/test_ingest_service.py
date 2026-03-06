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
        tdt_ear="right",
    )

    assert session.system == "TDT"
    assert session.session_id == "AC04_20251017"
    assert len(session.rows) > 0
    assert session.rows["stim_ear"].dropna().unique().tolist() == ["right"]
    assert session.rows["rec_ear"].dropna().unique().tolist() == ["right"]
    assert session.rows["rel_ear"].dropna().unique().tolist() == ["ipsi"]


def test_ingest_service_tdt_inference_requires_confirmation(tmp_path: Path):
    src = Path("tests/data/AC04_ClickABR_right_20251017.txt")
    folder = tmp_path / "input"
    folder.mkdir()
    (folder / src.name).write_bytes(src.read_bytes())

    service = IngestService()
    with pytest.raises(ValueError, match="Confirm by passing tdt_ear='right'"):
        service.ingest_path(
            system="TDT",
            input_path=folder,
            animal_id="AC04",
            session_date=date(2025, 10, 17),
        )


def test_ingest_service_tdt_infers_when_confirmation_disabled(tmp_path: Path):
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
        require_tdt_ear_confirmation=False,
    )

    assert session.rows["stim_ear"].dropna().unique().tolist() == ["right"]


def test_ingest_service_tdt_ambiguous_filename_requires_manual_value(tmp_path: Path):
    src = Path("tests/data/AC04_ClickABR_right_20251017.txt")
    folder = tmp_path / "input"
    folder.mkdir()
    (folder / "AC04_ClickABR_right_20251017.txt").write_bytes(src.read_bytes())
    (folder / "AC04_ClickABR_left_20251017.txt").write_bytes(src.read_bytes())

    service = IngestService()
    with pytest.raises(ValueError, match="Could not determine TDT ear"):
        service.ingest_path(
            system="TDT",
            input_path=folder,
            animal_id="AC04",
            session_date=date(2025, 10, 17),
            require_tdt_ear_confirmation=False,
        )


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

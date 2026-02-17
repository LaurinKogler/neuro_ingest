from datetime import date
from pathlib import Path
import pytest
from neuro_ingest.lab import ingest_session


def test_ingest_session_tdt_folder(tmp_path: Path):
    # copy one fixture into a temp folder
    src = Path("tests/data/AC04_ClickABR_right_20251017.txt")
    folder = tmp_path / "input"
    folder.mkdir()
    dst = folder / src.name
    dst.write_bytes(src.read_bytes())

    out_dir = tmp_path / "out"

    df, out_path = ingest_session(
        system="TDT",
        input_path=folder,
        out_dir=out_dir,
        animal_id="AC04",
        session_date=date(2025, 10, 17),
        overwrite=True,
    )

    assert out_path.exists()
    assert len(df) > 0


def test_ingest_session_requires_compatible_files(tmp_path: Path):
    folder = tmp_path / "input"
    folder.mkdir()
    (folder / "notes.md").write_text("not acquisition data")
    with pytest.raises(FileNotFoundError, match="TDT-compatible"):
        ingest_session(system="TDT", input_path=folder, out_dir=tmp_path / "out", animal_id="AC04", session_date=date(2025, 10, 17))

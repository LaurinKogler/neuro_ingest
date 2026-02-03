from datetime import date
from pathlib import Path

from neuro_ingest.ingest.tdt import TDTIngestor
from neuro_ingest.io import save_session_parquet, load_session_parquet


def test_save_and_load_parquet_roundtrip(tmp_path: Path):
    ing = TDTIngestor()
    df = ing.ingest(
        paths=[Path("tests/data/AC04_ClickABR_right_20251017.txt")],
        animal_id="AC04",
        session_date=date(2025, 10, 17),
        paradigm="abr",
        day=0,
        session_id="AC04_20251017",
    )

    out = save_session_parquet(df, tmp_path, system="TDT", session_id="AC04_20251017")
    df2 = load_session_parquet(out)

    assert len(df2) == len(df)
    assert set(df2.columns) == set(df.columns)

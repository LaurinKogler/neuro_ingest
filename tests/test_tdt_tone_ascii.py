from datetime import date
from pathlib import Path

from neuro_ingest.ingest.tdt import TDTIngestor


def test_tdt_ascii_tone_sets_freq_hz():
    path = Path("tests/data/AC04_ToneABR_right_20251017.txt")
    ing = TDTIngestor()

    df = ing.ingest(
        paths=[path],
        animal_id="AC04",
        session_date=date(2025, 10, 17),
        paradigm="abr",
        day=0,
        session_id="AC04_20251017",
    )

    assert len(df) > 0
    assert (df["freq_hz"] > 0).any()

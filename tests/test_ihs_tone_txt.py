from datetime import date
from pathlib import Path

from neuro_ingest.ingest.ihs import IHSIngestor


def test_ihs_tone_ingest_sets_freq():
    path = Path("tests/data/X48_d0_4kHz.TXT")

    ing = IHSIngestor()
    df = ing.ingest(
        paths=[path],
        animal_id="X48",
        session_date=date(2025, 1, 1),
        paradigm="abr",
        day=0,
        session_id="X48_20250101",
    )

    assert len(df) > 0
    assert (df["freq_hz"] > 0).any()
    assert df["trace_uid"].nunique() > 1

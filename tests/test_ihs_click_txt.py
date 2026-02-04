from datetime import date
from pathlib import Path

from neuro_ingest.ingest.ihs import IHSIngestor


def test_ihs_click_ingest():
    path = Path("tests/data/X48_d0_Click.TXT")

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
    assert df["system"].unique().tolist() == ["IHS"]
    assert set(df["freq_hz"].unique()) == {0.0}
    assert df["trace_uid"].nunique() > 1
    assert set(df["rel_ear"].unique()) <= {"ipsi", "contra"}

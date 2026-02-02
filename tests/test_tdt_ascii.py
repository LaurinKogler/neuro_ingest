from datetime import date
from pathlib import Path

from neuro_ingest.ingest.tdt import TDTIngestor
from neuro_ingest.schema import EvokedPotentialRow


def test_tdt_ascii_click_parses_to_schema_rows():
    path = Path("tests/data/AC04_ClickABR_right_20251017.txt")
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

    first = df.iloc[0].to_dict()
    EvokedPotentialRow(**first)

    assert float(df["freq_hz"].iloc[0]) == 0.0

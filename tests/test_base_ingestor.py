from datetime import date
from neuro_ingest.ingest.base import BaseIngestor
from neuro_ingest.schema import EvokedPotentialRow
from pathlib import Path



class DummyIngestor(BaseIngestor):
    system = "DUMMY"

    def parse_file(self, path):
        return [{
            "freq_hz": 0.0,
            "level_db": 80.0,
            "source_record_id": "t1",
            "sample_idx": 0,
            "time_ms": 0.0,
            "amplitude_uv": 1.23,
        }]


def test_base_ingestor_produces_schema_rows(tmp_path: Path):
    ing = DummyIngestor()

    dummy_file = tmp_path / "fake.csv"
    dummy_file.write_text("dummy")

    df = ing.ingest(
        paths=[dummy_file],
        animal_id="X00",
        session_date=date(2025, 1, 1),
        paradigm="abr",
        day=0,
    )

    # at least one row
    assert len(df) == 1

    # row validates against schema
    EvokedPotentialRow(**df.iloc[0].to_dict())

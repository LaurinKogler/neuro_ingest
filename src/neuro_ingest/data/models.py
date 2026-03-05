from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

from neuro_ingest.schema import EvokedPotentialRow


REQUIRED_SAMPLE_COLUMNS = tuple(EvokedPotentialRow.model_fields.keys())


@dataclass(frozen=True)
class SessionData:
    session_id: str
    system: str
    animal_id: str
    session_date: date
    paradigm: str
    rows: pd.DataFrame

    def __post_init__(self) -> None:
        self._validate_rows()
        self._validate_metadata_consistency()

    def _validate_rows(self) -> None:
        if self.rows.empty:
            raise ValueError("SessionData.rows must contain at least one row.")

        missing = [col for col in REQUIRED_SAMPLE_COLUMNS if col not in self.rows.columns]
        if missing:
            raise ValueError(f"SessionData.rows missing required columns: {missing}")

    def _validate_metadata_consistency(self) -> None:
        if not (self.rows["session_id"] == self.session_id).all():
            raise ValueError("SessionData.rows session_id does not match SessionData.session_id.")
        if not (self.rows["system"] == self.system).all():
            raise ValueError("SessionData.rows system does not match SessionData.system.")
        if not (self.rows["animal_id"] == self.animal_id).all():
            raise ValueError("SessionData.rows animal_id does not match SessionData.animal_id.")
        if not (self.rows["paradigm"] == self.paradigm).all():
            raise ValueError("SessionData.rows paradigm does not match SessionData.paradigm.")

        session_dates = pd.to_datetime(self.rows["session_date"]).dt.date
        if not (session_dates == self.session_date).all():
            raise ValueError("SessionData.rows session_date does not match SessionData.session_date.")

    @classmethod
    def from_rows(cls, rows: pd.DataFrame) -> SessionData:
        first = rows.iloc[0]
        return cls(
            session_id=str(first["session_id"]),
            system=str(first["system"]),
            animal_id=str(first["animal_id"]),
            session_date=pd.to_datetime(first["session_date"]).date(),
            paradigm=str(first["paradigm"]),
            rows=rows,
        )


@dataclass(frozen=True)
class StorageWriteResult:
    parquet_path: Path
    db_path: Path
    rows_written: int

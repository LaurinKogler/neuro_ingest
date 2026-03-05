from __future__ import annotations

from pathlib import Path
from datetime import date
from typing import Literal

import pandas as pd

from neuro_ingest.ingest.service import IngestService
from neuro_ingest.storage.service import StorageService


System = Literal["TDT", "IHS"]


def ingest_session(
    *,
    system: System,
    input_path: str | Path,
    out_dir: str | Path,
    animal_id: str,
    session_date: date,
    paradigm: str = "abr",
    day: int | None = None,
    session_id: str | None = None,
    overwrite: bool = False,
    pattern: str = "*",
    db_path: str | Path | None = None,
) -> tuple[pd.DataFrame, Path]:
    """
    Backward-compatible one-call API.
    Delegates to IngestService + StorageService.
    """
    out_dir = Path(out_dir)
    if db_path is None:
        db_path = out_dir / "neuro_audio.duckdb"

    ingest_service = IngestService()
    session = ingest_service.ingest_path(
        system=system,
        input_path=input_path,
        animal_id=animal_id,
        session_date=session_date,
        paradigm=paradigm,
        day=day,
        session_id=session_id,
        pattern=pattern,
    )

    storage_service = StorageService(db_path=db_path, parquet_dir=out_dir)
    result = storage_service.append_session(session, overwrite=overwrite)
    return session.rows, result.parquet_path

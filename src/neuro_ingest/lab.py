from __future__ import annotations

from pathlib import Path
from datetime import date
from typing import Literal

import pandas as pd

from neuro_ingest.ingest.tdt import TDTIngestor
from neuro_ingest.ingest.ihs import IHSIngestor
from neuro_ingest.io import save_session_parquet


System = Literal["TDT"]  # extend later: "IHS"


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
    pattern: str = "*.txt",
) -> tuple[pd.DataFrame, Path]:
    """
    Lab-facing one-call API.
    Accepts a folder or list of files later (we keep it folder for now).
    """

    input_path = Path(input_path)
    out_dir = Path(out_dir)

    if session_id is None:
        session_id = f"{animal_id}_{session_date:%Y%m%d}"

    if system == "TDT":
        ing = TDTIngestor()
    elif system == "IHS":
        ing = IHSIngestor()
    else:
        raise ValueError(f"Unsupported system: {system}")

    files = sorted(input_path.rglob(pattern)) if input_path.is_dir() else [input_path]
    if not files:
        raise FileNotFoundError(f"No files matching {pattern} in {input_path}")

    df = ing.ingest(
        paths=files,
        animal_id=animal_id,
        session_date=session_date,
        paradigm=paradigm,
        day=day,
        session_id=session_id,
    )

    out_path = save_session_parquet(df, out_dir, system=ing.system, session_id=session_id, overwrite=overwrite)
    return df, out_path

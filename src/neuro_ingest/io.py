from __future__ import annotations

from pathlib import Path

import pandas as pd

from neuro_ingest.storage.parquet_store import ParquetStore, session_filename


def save_session_parquet(
    df: pd.DataFrame,
    out_dir: str | Path,
    *,
    system: str,
    session_id: str,
    overwrite: bool = False,
) -> Path:
    store = ParquetStore(root_dir=out_dir)
    return store.save_dataframe(
        df,
        system=system,
        session_id=session_id,
        overwrite=overwrite,
    )


def load_session_parquet(path: str | Path) -> pd.DataFrame:
    return ParquetStore.load(path)


__all__ = ["load_session_parquet", "save_session_parquet", "session_filename"]

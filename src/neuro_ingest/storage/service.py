from __future__ import annotations

from pathlib import Path

import pandas as pd

from neuro_ingest.data.models import SessionData, StorageWriteResult
from neuro_ingest.storage.duckdb_store import DuckDBStore
from neuro_ingest.storage.parquet_store import ParquetStore


class StorageService:
    def __init__(self, *, db_path: str | Path, parquet_dir: str | Path) -> None:
        self.duckdb_store = DuckDBStore(db_path=db_path)
        self.parquet_store = ParquetStore(root_dir=parquet_dir)

    def append_session(self, session: SessionData, *, overwrite: bool = False) -> StorageWriteResult:
        parquet_path = self.parquet_store.save_session(session, overwrite=overwrite)
        self.duckdb_store.append_session(session, overwrite=overwrite)
        return StorageWriteResult(
            parquet_path=parquet_path,
            db_path=self.duckdb_store.db_path,
            rows_written=len(session.rows),
        )

    def query(self, sql: str, params: dict | list | tuple | None = None) -> pd.DataFrame:
        return self.duckdb_store.query(sql, params=params)

    def list_sessions(
        self,
        *,
        animal_id: str | None = None,
        system: str | None = None,
        paradigm: str | None = None,
        session_id: str | None = None,
    ) -> pd.DataFrame:
        return self.duckdb_store.list_sessions(
            animal_id=animal_id,
            system=system,
            paradigm=paradigm,
            session_id=session_id,
        )

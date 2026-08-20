from __future__ import annotations

from pathlib import Path

import pandas as pd

from neuro_ingest.data.models import SessionData, StorageWriteResult
from neuro_ingest.storage.editor import DBEditResult, DuckDBEditor
from neuro_ingest.storage.duckdb_store import DuckDBStore
from neuro_ingest.storage.parquet_store import ParquetStore


class StorageService:
    def __init__(self, *, db_path: str | Path, parquet_dir: str | Path) -> None:
        self.duckdb_store = DuckDBStore(db_path=db_path)
        self.duckdb_editor = DuckDBEditor(db_path=db_path)
        self.parquet_store = ParquetStore(root_dir=parquet_dir)

    def append_session(self, session: SessionData, *, overwrite: bool = False) -> StorageWriteResult:
        parquet_path = self.parquet_store.save_session(session, overwrite=overwrite)
        self.duckdb_store.append_session(session, overwrite=overwrite)
        return StorageWriteResult(
            parquet_path=parquet_path,
            db_path=self.duckdb_store.db_path,
            rows_written=len(session.rows),
        )

    def session_exists(self, session_id: str) -> bool:
        return self.duckdb_store.session_exists(session_id)

    def query(self, sql: str, params: dict | list | tuple | None = None) -> pd.DataFrame:
        return self.duckdb_store.query(sql, params=params)

    def list_sample_filter_values(self, *, animal_id: str | None = None) -> dict[str, list]:
        return self.duckdb_store.list_sample_filter_values(animal_id=animal_id)

    def get_samples(
        self,
        *,
        animal_id: str | None = None,
        session_id: str | None = None,
        day: int | None = None,
        system: str | None = None,
        paradigm: str | None = None,
        limit: int = 50000,
    ) -> pd.DataFrame:
        if limit <= 0:
            raise ValueError("limit must be > 0.")

        filters: list[str] = []
        values: list[object] = []

        if animal_id is not None and animal_id.strip():
            filters.append("animal_id = ?")
            values.append(animal_id.strip())
        if session_id is not None and session_id.strip():
            filters.append("session_id = ?")
            values.append(session_id.strip())
        if day is not None:
            filters.append("day = ?")
            values.append(int(day))
        if system is not None and system.strip():
            filters.append("system = ?")
            values.append(system.strip())
        if paradigm is not None and paradigm.strip():
            filters.append("paradigm = ?")
            values.append(paradigm.strip())

        where_clause = ""
        if filters:
            where_clause = "WHERE " + " AND ".join(filters)

        sql = f"""
            SELECT *
            FROM samples
            {where_clause}
            ORDER BY session_date DESC, session_id, trace_uid, sample_idx
            LIMIT ?
        """
        values.append(int(limit))
        return self.duckdb_store.query(sql, params=values)

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

    def list_trace_summaries(self, *, session_id: str, limit: int = 20000) -> pd.DataFrame:
        return self.duckdb_editor.list_trace_summaries(session_id=session_id, limit=limit)

    def delete_traces(
        self,
        *,
        session_id: str,
        trace_uids: list[str],
        create_backup: bool = False,
        backup_dir: str | Path | None = None,
    ) -> DBEditResult:
        return self.duckdb_editor.delete_traces(
            session_id=session_id,
            trace_uids=trace_uids,
            create_backup=create_backup,
            backup_dir=backup_dir,
        )

    def update_trace_fields(
        self,
        *,
        session_id: str,
        trace_uids: list[str],
        updates: dict[str, object],
        create_backup: bool = False,
        backup_dir: str | Path | None = None,
    ) -> DBEditResult:
        return self.duckdb_editor.update_trace_fields(
            session_id=session_id,
            trace_uids=trace_uids,
            updates=updates,
            create_backup=create_backup,
            backup_dir=backup_dir,
        )

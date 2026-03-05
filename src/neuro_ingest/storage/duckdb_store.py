from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from neuro_ingest.data.models import SessionData


class DuckDBStore:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def append_session(self, session: SessionData, *, overwrite: bool = False) -> None:
        rows_for_db = self._coerce_dataframe_for_duckdb(session.rows)

        with duckdb.connect(str(self.db_path)) as conn:
            conn.execute("BEGIN TRANSACTION")
            try:
                self._ensure_sessions_table(conn)
                conn.register("incoming_samples", rows_for_db)
                self._ensure_samples_table(conn, incoming_columns=list(rows_for_db.columns))

                existing = conn.execute(
                    "SELECT COUNT(*) FROM sessions WHERE session_id = ?",
                    [session.session_id],
                ).fetchone()[0]

                if existing and not overwrite:
                    raise FileExistsError(
                        f"Session already exists in DB: {session.session_id}. Use overwrite=True."
                    )

                if existing:
                    conn.execute("DELETE FROM samples WHERE session_id = ?", [session.session_id])
                    conn.execute("DELETE FROM sessions WHERE session_id = ?", [session.session_id])

                conn.execute("INSERT INTO samples SELECT * FROM incoming_samples")
                conn.execute(
                    """
                    INSERT INTO sessions (
                        session_id, system, animal_id, session_date, paradigm, row_count, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    [
                        session.session_id,
                        session.system,
                        session.animal_id,
                        session.session_date,
                        session.paradigm,
                        len(session.rows),
                    ],
                )
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise
            finally:
                try:
                    conn.unregister("incoming_samples")
                except Exception:
                    pass

    @staticmethod
    def _coerce_dataframe_for_duckdb(rows: pd.DataFrame) -> pd.DataFrame:
        out = rows.copy()
        for column, dtype in out.dtypes.items():
            # DuckDB 1.4.x on Windows may reject pandas StringDtype shown as "str".
            if str(dtype) in {"str", "string", "string[python]"}:
                out[column] = out[column].astype("object")
        return out

    def query(self, sql: str, params: dict | list | tuple | None = None) -> pd.DataFrame:
        with duckdb.connect(str(self.db_path)) as conn:
            if params is None:
                return conn.execute(sql).fetchdf()
            return conn.execute(sql, params).fetchdf()

    def list_sessions(
        self,
        *,
        animal_id: str | None = None,
        system: str | None = None,
        paradigm: str | None = None,
        session_id: str | None = None,
    ) -> pd.DataFrame:
        filters: list[str] = []
        values: list[Any] = []

        if animal_id is not None:
            filters.append("animal_id = ?")
            values.append(animal_id)
        if system is not None:
            filters.append("system = ?")
            values.append(system)
        if paradigm is not None:
            filters.append("paradigm = ?")
            values.append(paradigm)
        if session_id is not None:
            filters.append("session_id = ?")
            values.append(session_id)

        where_clause = ""
        if filters:
            where_clause = "WHERE " + " AND ".join(filters)

        with duckdb.connect(str(self.db_path)) as conn:
            self._ensure_sessions_table(conn)
            sql = f"""
                SELECT session_id, system, animal_id, session_date, paradigm, row_count, created_at
                FROM sessions
                {where_clause}
                ORDER BY session_date, session_id
            """
            if values:
                return conn.execute(sql, values).fetchdf()
            return conn.execute(sql).fetchdf()

    @staticmethod
    def _ensure_sessions_table(conn: duckdb.DuckDBPyConnection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id VARCHAR PRIMARY KEY,
                system VARCHAR NOT NULL,
                animal_id VARCHAR NOT NULL,
                session_date DATE NOT NULL,
                paradigm VARCHAR NOT NULL,
                row_count BIGINT NOT NULL,
                created_at TIMESTAMP NOT NULL
            )
            """
        )

    @staticmethod
    def _ensure_samples_table(
        conn: duckdb.DuckDBPyConnection,
        *,
        incoming_columns: list[str],
    ) -> None:
        exists = conn.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'main' AND table_name = 'samples'
            """
        ).fetchone()[0]
        if not exists:
            conn.execute("CREATE TABLE samples AS SELECT * FROM incoming_samples LIMIT 0")

        table_info = conn.execute("PRAGMA table_info('samples')").fetchall()
        existing = [col[1] for col in table_info]
        if existing != incoming_columns:
            raise ValueError(
                "Incoming sample schema does not match existing `samples` table schema."
            )

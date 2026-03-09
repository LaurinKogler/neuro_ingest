from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import shutil

import duckdb
import pandas as pd


@dataclass(frozen=True)
class DBEditResult:
    rows_affected: int
    backup_path: Path | None


class DuckDBEditor:
    _EDITABLE_COLUMNS = {"stim_ear", "rec_ear", "rel_ear", "level_db", "freq_hz", "stimulus_label"}

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)

    def create_backup(self, *, backup_dir: str | Path | None = None) -> Path:
        if not self.db_path.exists():
            raise FileNotFoundError(f"DuckDB file not found: {self.db_path}")

        backup_root = Path(backup_dir) if backup_dir is not None else self.db_path.parent / "backups"
        backup_root.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_root / f"{self.db_path.stem}_{stamp}.duckdb"
        shutil.copy2(self.db_path, backup_path)
        return backup_path

    def list_trace_summaries(self, *, session_id: str, limit: int = 20000) -> pd.DataFrame:
        if limit <= 0:
            raise ValueError("limit must be > 0.")

        sql = """
            SELECT
                trace_uid,
                ANY_VALUE(stim_ear) AS stim_ear,
                ANY_VALUE(rec_ear) AS rec_ear,
                ANY_VALUE(rel_ear) AS rel_ear,
                ANY_VALUE(freq_hz) AS freq_hz,
                ANY_VALUE(level_db) AS level_db,
                COUNT(*) AS sample_rows
            FROM samples
            WHERE session_id = ?
            GROUP BY trace_uid
            ORDER BY freq_hz, level_db DESC, trace_uid
            LIMIT ?
        """
        with duckdb.connect(str(self.db_path)) as conn:
            return conn.execute(sql, [session_id, limit]).fetchdf()

    def delete_traces(
        self,
        *,
        session_id: str,
        trace_uids: list[str],
        create_backup: bool = False,
        backup_dir: str | Path | None = None,
    ) -> DBEditResult:
        unique_trace_uids = self._normalize_trace_uids(trace_uids)
        backup_path = self.create_backup(backup_dir=backup_dir) if create_backup else None

        placeholders = ",".join(["?"] * len(unique_trace_uids))
        params = [session_id, *unique_trace_uids]

        with duckdb.connect(str(self.db_path)) as conn:
            conn.execute("BEGIN TRANSACTION")
            try:
                rows_affected = int(
                    conn.execute(
                        f"SELECT COUNT(*) FROM samples WHERE session_id = ? AND trace_uid IN ({placeholders})",
                        params,
                    ).fetchone()[0]
                )
                if rows_affected > 0:
                    conn.execute(
                        f"DELETE FROM samples WHERE session_id = ? AND trace_uid IN ({placeholders})",
                        params,
                    )
                    self._refresh_session_row_count(conn, session_id=session_id)
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise

        return DBEditResult(rows_affected=rows_affected, backup_path=backup_path)

    def update_trace_fields(
        self,
        *,
        session_id: str,
        trace_uids: list[str],
        updates: dict[str, object],
        create_backup: bool = False,
        backup_dir: str | Path | None = None,
    ) -> DBEditResult:
        unique_trace_uids = self._normalize_trace_uids(trace_uids)
        safe_updates = self._normalize_updates(updates)
        backup_path = self.create_backup(backup_dir=backup_dir) if create_backup else None

        set_parts = [f"{col} = ?" for col in safe_updates.keys()]
        set_sql = ", ".join(set_parts)
        placeholders = ",".join(["?"] * len(unique_trace_uids))

        count_params = [session_id, *unique_trace_uids]
        update_params = [*safe_updates.values(), session_id, *unique_trace_uids]

        with duckdb.connect(str(self.db_path)) as conn:
            conn.execute("BEGIN TRANSACTION")
            try:
                rows_affected = int(
                    conn.execute(
                        f"SELECT COUNT(*) FROM samples WHERE session_id = ? AND trace_uid IN ({placeholders})",
                        count_params,
                    ).fetchone()[0]
                )
                if rows_affected > 0:
                    conn.execute(
                        f"UPDATE samples SET {set_sql} WHERE session_id = ? AND trace_uid IN ({placeholders})",
                        update_params,
                    )
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise

        return DBEditResult(rows_affected=rows_affected, backup_path=backup_path)

    @staticmethod
    def _refresh_session_row_count(conn: duckdb.DuckDBPyConnection, *, session_id: str) -> None:
        conn.execute(
            """
            UPDATE sessions
            SET row_count = (
                SELECT COUNT(*)
                FROM samples
                WHERE samples.session_id = sessions.session_id
            )
            WHERE session_id = ?
            """,
            [session_id],
        )
        conn.execute("DELETE FROM sessions WHERE session_id = ? AND row_count = 0", [session_id])

    @staticmethod
    def _normalize_trace_uids(trace_uids: list[str]) -> list[str]:
        unique = sorted({str(uid).strip() for uid in trace_uids if str(uid).strip()})
        if not unique:
            raise ValueError("trace_uids must contain at least one non-empty value.")
        return unique

    @classmethod
    def _normalize_updates(cls, updates: dict[str, object]) -> dict[str, object]:
        if not updates:
            raise ValueError("updates must not be empty.")

        safe: dict[str, object] = {}
        for col, value in updates.items():
            if col not in cls._EDITABLE_COLUMNS:
                raise ValueError(f"Column {col!r} is not editable.")
            safe[col] = value
        return safe

from __future__ import annotations

from pathlib import Path

import pandas as pd

from neuro_ingest.data.models import SessionData


def session_filename(*, system: str, session_id: str) -> str:
    safe = session_id.replace(" ", "_")
    return f"{safe}_{system}.parquet"


class ParquetStore:
    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def session_path(self, *, system: str, session_id: str) -> Path:
        return self.root_dir / session_filename(system=system, session_id=session_id)

    def save_session(self, session: SessionData, *, overwrite: bool = False) -> Path:
        return self.save_dataframe(
            session.rows,
            system=session.system,
            session_id=session.session_id,
            overwrite=overwrite,
        )

    def save_dataframe(
        self,
        df: pd.DataFrame,
        *,
        system: str,
        session_id: str,
        overwrite: bool = False,
    ) -> Path:
        out_path = self.session_path(system=system, session_id=session_id)
        if out_path.exists() and not overwrite:
            raise FileExistsError(f"Output exists: {out_path}. Use overwrite=True.")
        df.to_parquet(out_path, index=False, engine="pyarrow")
        return out_path

    @staticmethod
    def load(path: str | Path) -> pd.DataFrame:
        return pd.read_parquet(Path(path), engine="pyarrow")

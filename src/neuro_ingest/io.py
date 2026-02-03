from __future__ import annotations

from pathlib import Path
import pandas as pd


def session_filename(*, system: str, session_id: str) -> str:
    # one file per system × session
    safe = session_id.replace(" ", "_")
    return f"{safe}__{system}.parquet"


def save_session_parquet(
    df: pd.DataFrame,
    out_dir: str | Path,
    *,
    system: str,
    session_id: str,
    overwrite: bool = False,
) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / session_filename(system=system, session_id=session_id)

    if out_path.exists() and not overwrite:
        raise FileExistsError(f"Output exists: {out_path}. Use overwrite=True.")

    # ensures stable dtypes + fastest path
    df.to_parquet(out_path, index=False, engine="pyarrow")
    return out_path


def load_session_parquet(path: str | Path) -> pd.DataFrame:
    return pd.read_parquet(Path(path), engine="pyarrow")

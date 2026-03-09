from __future__ import annotations

from pathlib import Path
from typing import Literal, Protocol

import pandas as pd

from neuro_ingest.data.models import SessionData
from neuro_ingest.ingest.registry import detect_ingestor
from neuro_ingest.ingest.tdt_ear import infer_tdt_ear_from_filenames
from neuro_ingest.toolbox import NeuroAudioToolbox


class UploadedFileLike(Protocol):
    name: str

    def getbuffer(self) -> bytes:
        ...


def stage_uploaded_files(uploaded_files: list[UploadedFileLike], target_dir: str | Path) -> list[Path]:
    target = Path(target_dir)
    target.mkdir(parents=True, exist_ok=True)

    staged: list[Path] = []
    for uploaded in uploaded_files:
        safe_name = Path(uploaded.name).name
        out_path = target / safe_name
        out_path.write_bytes(bytes(uploaded.getbuffer()))
        staged.append(out_path)
    return staged


def resolve_system(system_choice: str, staged_paths: list[Path]) -> str:
    if system_choice.upper() in {"TDT", "IHS"}:
        return system_choice.upper()
    if system_choice.upper() != "AUTO":
        raise ValueError(f"Unsupported system selection: {system_choice}")

    for path in staged_paths:
        try:
            return detect_ingestor(path).system
        except Exception:
            continue
    raise ValueError("Could not auto-detect system from uploaded files.")


def infer_tdt_ear_from_upload_names(uploaded_files: list[UploadedFileLike]) -> str | None:
    pseudo_paths = [Path(uploaded.name) for uploaded in uploaded_files]
    return infer_tdt_ear_from_filenames(pseudo_paths)


def combine_sessions(
    sessions: list[SessionData],
    *,
    session_id: str | None = None,
) -> SessionData:
    if not sessions:
        raise ValueError("No sessions to combine.")

    base = sessions[0]
    for session in sessions[1:]:
        if session.system != base.system:
            raise ValueError("Cannot combine sessions with different systems.")
        if session.animal_id != base.animal_id:
            raise ValueError("Cannot combine sessions with different animal_id values.")
        if session.session_date != base.session_date:
            raise ValueError("Cannot combine sessions with different session_date values.")
        if session.paradigm != base.paradigm:
            raise ValueError("Cannot combine sessions with different paradigm values.")

    target_session_id = session_id or base.session_id
    if session_id is None:
        distinct_ids = {s.session_id for s in sessions}
        if len(distinct_ids) > 1:
            raise ValueError("Cannot combine different session IDs without explicit target session_id.")

    combined_rows = pd.concat([session.rows for session in sessions], ignore_index=True)
    if not (combined_rows["session_id"] == target_session_id).all():
        combined_rows = combined_rows.copy()
        combined_rows["session_id"] = target_session_id

    return SessionData(
        session_id=target_session_id,
        system=base.system,
        animal_id=base.animal_id,
        session_date=base.session_date,
        paradigm=base.paradigm,
        rows=combined_rows,
    )


def ingest_and_save(
    *,
    toolbox: NeuroAudioToolbox,
    system: str,
    input_dir: str | Path,
    animal_id: str,
    session_date,
    paradigm: str,
    day: int | None,
    session_id: str | None,
    overwrite: bool,
    tdt_ear: Literal["left", "right"] | None,
):
    session = toolbox.ingest(
        system=system,
        input_path=input_dir,
        animal_id=animal_id,
        session_date=session_date,
        paradigm=paradigm,
        day=day,
        session_id=session_id,
        tdt_ear=tdt_ear,
    )
    result = toolbox.save(session, overwrite=overwrite)
    return session, result

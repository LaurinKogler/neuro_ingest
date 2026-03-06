from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Iterable, Literal
import warnings

from neuro_ingest.data.models import SessionData
from neuro_ingest.ingest.registry import INGESTORS
from neuro_ingest.ingest.tdt_ear import infer_tdt_ear_from_filenames


class IngestService:
    def __init__(self, ingestors: Iterable | None = None) -> None:
        self.ingestors = list(ingestors or INGESTORS)

    def ingest_path(
        self,
        *,
        system: str,
        input_path: str | Path,
        animal_id: str,
        session_date: date,
        paradigm: str = "abr",
        day: int | None = None,
        session_id: str | None = None,
        pattern: str = "*",
        tdt_ear: Literal["left", "right"] | None = None,
        infer_tdt_ear: bool = True,
        require_tdt_ear_confirmation: bool = True,
    ) -> SessionData:
        input_path = Path(input_path)
        if session_id is None:
            session_id = f"{animal_id}_{session_date:%Y%m%d}"

        ingestor = self._resolve_ingestor(system)
        files = self._resolve_candidate_files(input_path=input_path, pattern=pattern)
        compatible_files = [path for path in files if ingestor.can_parse(path)]

        if not compatible_files:
            raise FileNotFoundError(
                f"No {ingestor.system}-compatible files matching {pattern} in {input_path}"
            )

        resolved_tdt_ear = self._resolve_tdt_ear(
            system=ingestor.system,
            files=compatible_files,
            tdt_ear=tdt_ear,
            infer_tdt_ear=infer_tdt_ear,
            require_tdt_ear_confirmation=require_tdt_ear_confirmation,
        )

        rows = ingestor.ingest(
            paths=compatible_files,
            animal_id=animal_id,
            session_date=session_date,
            paradigm=paradigm,
            day=day,
            session_id=session_id,
        )
        if ingestor.system == "TDT" and resolved_tdt_ear is not None:
            rows = rows.copy()
            rows["stim_ear"] = resolved_tdt_ear
            rows["rec_ear"] = resolved_tdt_ear
            rows["rel_ear"] = "ipsi"

        return SessionData(
            session_id=session_id,
            system=ingestor.system,
            animal_id=animal_id,
            session_date=session_date,
            paradigm=paradigm,
            rows=rows,
        )

    def _resolve_ingestor(self, system: str):
        try:
            return next(ing for ing in self.ingestors if ing.system.upper() == system.upper())
        except StopIteration:
            raise ValueError(f"Unsupported system: {system}")

    @staticmethod
    def _resolve_candidate_files(*, input_path: Path, pattern: str) -> list[Path]:
        if input_path.is_dir():
            return sorted(path for path in input_path.rglob(pattern) if path.is_file())
        return [input_path]

    @staticmethod
    def _normalize_ear(value: str) -> str:
        val = value.strip().lower()
        if val not in {"left", "right"}:
            raise ValueError(f"Invalid tdt_ear value: {value!r}. Use 'left' or 'right'.")
        return val

    def _resolve_tdt_ear(
        self,
        *,
        system: str,
        files: list[Path],
        tdt_ear: Literal["left", "right"] | None,
        infer_tdt_ear: bool,
        require_tdt_ear_confirmation: bool,
    ) -> str | None:
        if system != "TDT":
            if tdt_ear is not None:
                warnings.warn("tdt_ear was provided for non-TDT ingest and will be ignored.")
            return None

        explicit = self._normalize_ear(tdt_ear) if tdt_ear is not None else None
        inferred = infer_tdt_ear_from_filenames(files) if infer_tdt_ear else None

        if explicit is not None:
            if inferred is not None and inferred != explicit:
                warnings.warn(
                    f"Provided tdt_ear={explicit!r} does not match filename inference {inferred!r}. "
                    "Using provided value."
                )
            return explicit

        if inferred is not None and not require_tdt_ear_confirmation:
            return inferred

        if inferred is not None and require_tdt_ear_confirmation:
            raise ValueError(
                f"TDT ear inferred as '{inferred}' from filenames. "
                f"Confirm by passing tdt_ear='{inferred}'."
            )

        raise ValueError(
            "Could not determine TDT ear from filenames. "
            "Provide tdt_ear='left' or tdt_ear='right'."
        )

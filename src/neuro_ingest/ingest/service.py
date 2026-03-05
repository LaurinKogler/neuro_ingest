from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Iterable

from neuro_ingest.data.models import SessionData
from neuro_ingest.ingest.registry import INGESTORS


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

        rows = ingestor.ingest(
            paths=compatible_files,
            animal_id=animal_id,
            session_date=session_date,
            paradigm=paradigm,
            day=day,
            session_id=session_id,
        )
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

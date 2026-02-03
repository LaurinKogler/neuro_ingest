from abc import ABC, abstractmethod
from pathlib import Path
from datetime import date
import pandas as pd

from neuro_ingest.schema import EvokedPotentialRow
from neuro_ingest.ids import sha256_file, make_trace_uid



class BaseIngestor(ABC):
    system: str  # must be set by subclasses

    def ingest(
        self,
        paths,
        *,
        animal_id: str,
        session_date: date,
        paradigm: str,
        day: int | None = None,
        session_id: str | None = None,
    ) -> pd.DataFrame:

        paths = self._resolve_paths(paths)

        if session_id is None:
            session_id = f"{animal_id}_{session_date}"

        records = []

        for path in paths:
            file_uid = sha256_file(path)
            rows = self.parse_file(Path(path))

            for row in rows:
                row.update(
                    animal_id=animal_id,
                    session_id=session_id,
                    session_date=session_date,
                    day=day,
                    system=self.system,
                    paradigm=paradigm,
                    source_file=str(path),
                )

                if "source_record_id" not in row:
                    raise ValueError(f"Parser did not set source_record_id for file {path}")

                row["file_uid"] = file_uid
                row["trace_uid"] = make_trace_uid(file_uid=file_uid, source_record_id=str(row["source_record_id"]))

                
                validated = EvokedPotentialRow(**row)
                records.append(validated.model_dump())

        return pd.DataFrame(records)

    def _resolve_paths(self, paths):
        if isinstance(paths, (list, tuple)):
            return [Path(p) for p in paths]

        p = Path(paths)
        if p.is_dir():
            return sorted(p.glob("*"))

        return [p]


    @abstractmethod
    def parse_file(self, path: Path) -> list[dict]:
        """
        Must return a list of dicts containing all EvokedPotentialRow
        fields EXCEPT session-level metadata.
        """
        raise NotImplementedError

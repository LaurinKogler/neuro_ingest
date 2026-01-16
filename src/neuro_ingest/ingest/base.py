from abc import ABC, abstractmethod
from pathlib import Path
from datetime import date
import pandas as pd

from neuro_ingest.schema import EvokedPotentialRow


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

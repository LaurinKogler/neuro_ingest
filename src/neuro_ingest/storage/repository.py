from __future__ import annotations

from typing import Protocol

import pandas as pd

from neuro_ingest.data.models import SessionData


class StorageRepository(Protocol):
    def append_session(self, session: SessionData, *, overwrite: bool = False) -> None:
        ...

    def query(self, sql: str, params: dict | list | tuple | None = None) -> pd.DataFrame:
        ...

    def list_sessions(
        self,
        *,
        animal_id: str | None = None,
        system: str | None = None,
        paradigm: str | None = None,
        session_id: str | None = None,
    ) -> pd.DataFrame:
        ...

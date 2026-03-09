from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Literal

import pandas as pd
import plotly.graph_objects as go

from neuro_ingest.data.models import SessionData, StorageWriteResult
from neuro_ingest.ingest.service import IngestService
from neuro_ingest.plot.abr_viewer import PlotService
from neuro_ingest.storage.service import StorageService


class NeuroAudioToolbox:
    def __init__(self, *, db_path: str | Path, parquet_dir: str | Path) -> None:
        self.ingest_service = IngestService()
        self.storage_service = StorageService(db_path=db_path, parquet_dir=parquet_dir)
        self.plot_service = PlotService()

    def ingest(
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
    ) -> SessionData:
        return self.ingest_service.ingest_path(
            system=system,
            input_path=input_path,
            animal_id=animal_id,
            session_date=session_date,
            paradigm=paradigm,
            day=day,
            session_id=session_id,
            pattern=pattern,
            tdt_ear=tdt_ear,
        )

    def save(self, session: SessionData, *, overwrite: bool = False) -> StorageWriteResult:
        return self.storage_service.append_session(session, overwrite=overwrite)

    def query(self, sql: str, params: dict | list | tuple | None = None) -> pd.DataFrame:
        return self.storage_service.query(sql, params=params)

    def list_sessions(
        self,
        *,
        animal_id: str | None = None,
        system: str | None = None,
        paradigm: str | None = None,
        session_id: str | None = None,
    ) -> pd.DataFrame:
        return self.storage_service.list_sessions(
            animal_id=animal_id,
            system=system,
            paradigm=paradigm,
            session_id=session_id,
        )

    def list_trace_summaries(self, *, session_id: str, limit: int = 20000) -> pd.DataFrame:
        return self.storage_service.list_trace_summaries(session_id=session_id, limit=limit)

    def delete_traces(
        self,
        *,
        session_id: str,
        trace_uids: list[str],
        create_backup: bool = False,
        backup_dir: str | Path | None = None,
    ):
        return self.storage_service.delete_traces(
            session_id=session_id,
            trace_uids=trace_uids,
            create_backup=create_backup,
            backup_dir=backup_dir,
        )

    def update_trace_fields(
        self,
        *,
        session_id: str,
        trace_uids: list[str],
        updates: dict[str, object],
        create_backup: bool = False,
        backup_dir: str | Path | None = None,
    ):
        return self.storage_service.update_trace_fields(
            session_id=session_id,
            trace_uids=trace_uids,
            updates=updates,
            create_backup=create_backup,
            backup_dir=backup_dir,
        )

    def plot(
        self,
        data: SessionData | pd.DataFrame,
        *,
        color_by: str = "level_db",
        group_by: str = "trace_uid",
        filters: dict[str, Any] | None = None,
        title: str = "ABR Traces",
        frequency_hz: float | None = None,
        relation_mode: Literal["ipsi", "ipsi_contra"] = "ipsi",
        spacing_uv: float = 0.0,
        amplitude_scale: float = 1.0,
        intensity_order: Literal["desc", "asc"] = "desc",
        figure_height_px: int | None = None,
    ) -> go.Figure:
        return self.plot_service.plot_abr(
            data,
            color_by=color_by,
            group_by=group_by,
            filters=filters,
            title=title,
            frequency_hz=frequency_hz,
            relation_mode=relation_mode,
            spacing_uv=spacing_uv,
            amplitude_scale=amplitude_scale,
            intensity_order=intensity_order,
            figure_height_px=figure_height_px,
        )

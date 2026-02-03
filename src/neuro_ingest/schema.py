from typing import Optional
from datetime import date
from pydantic import BaseModel, Field, ConfigDict


SCHEMA_VERSION = "0.1"


class EvokedPotentialRow(BaseModel):
    # --- core identifiers ---
    animal_id: str
    session_id: str
    session_date: date
    day: Optional[int] = None
    system: str
    paradigm: str
    stim_ear: str | None = None
    rec_ear: str | None = None
    rel_ear: str | None = None

    # --- stimulus metadata ---
    freq_hz: float = Field(
        description="Stimulus frequency in Hz. Use 0 for click or broadband."
    )
    level_db: float
    stimulus_label: Optional[str] = None

    # --- trace identity ---
    file_uid: str
    source_record_id: str
    trace_uid: str        # Trace-Gruppe
    sample_uid: str       # einzelne Sample-Zeile

    repetition_idx: Optional[int] = None

    # --- time axis ---
    sample_idx: int
    time_ms: float

    # --- signal ---
    amplitude_uv: float

    # --- provenance ---
    source_file: str
    schema_version: str = Field(default=SCHEMA_VERSION)

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )

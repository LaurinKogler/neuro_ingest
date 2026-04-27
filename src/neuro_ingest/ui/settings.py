from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from datetime import date
from pathlib import Path
import tomllib

LOCAL_UI_SETTINGS_FILENAME = "ingest_ui.local.toml"
LOCAL_UI_SETTINGS_EXAMPLE_FILENAME = "ingest_ui.local.example.toml"
DEFAULT_VIEWER_QUERY_SQL = "SELECT * FROM samples ORDER BY session_date DESC, session_id DESC LIMIT 100000"
_SYSTEM_CHOICES = {"TDT", "IHS"}


@dataclass(frozen=True, slots=True)
class IngestUISettings:
    system_choice: str = "TDT"
    animal_id: str = ""
    paradigm: str = "abr"
    day_text: str = ""
    session_id: str = ""
    session_id_template: str = "{animal_id}_{date_ymd}"
    parquet_dir: str = "normalized"
    db_path: str = "normalized/neuro_audio.duckdb"
    overwrite: bool = False
    viewer_row_limit: int = 100000
    editor_trace_limit: int = 5000
    viewer_query_sql: str = DEFAULT_VIEWER_QUERY_SQL


def load_ui_settings(base_dir: str | Path) -> tuple[IngestUISettings, list[str]]:
    settings_path = Path(base_dir) / LOCAL_UI_SETTINGS_FILENAME
    if not settings_path.exists():
        return IngestUISettings(), []

    try:
        data = tomllib.loads(settings_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"{settings_path.name} is not valid TOML: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"{settings_path.name} must contain top-level key/value settings.")

    values = asdict(IngestUISettings())
    warnings: list[str] = []
    string_fields = {
        "system_choice",
        "animal_id",
        "paradigm",
        "day_text",
        "session_id",
        "session_id_template",
        "parquet_dir",
        "db_path",
        "viewer_query_sql",
    }
    int_fields = {"viewer_row_limit", "editor_trace_limit"}
    bool_fields = {"overwrite"}
    known_fields = {field.name for field in fields(IngestUISettings)}

    for key, value in data.items():
        if key not in known_fields:
            warnings.append(f"Ignoring unknown UI setting '{key}' in {settings_path.name}.")
            continue

        if key in string_fields:
            if not isinstance(value, str):
                raise ValueError(f"Setting '{key}' in {settings_path.name} must be a string.")
        elif key in int_fields:
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValueError(f"Setting '{key}' in {settings_path.name} must be an integer.")
        elif key in bool_fields and not isinstance(value, bool):
            raise ValueError(f"Setting '{key}' in {settings_path.name} must be true or false.")

        values[key] = value

    settings = IngestUISettings(**values)
    if settings.system_choice not in _SYSTEM_CHOICES:
        choices = ", ".join(sorted(_SYSTEM_CHOICES))
        raise ValueError(f"system_choice must be one of: {choices}")
    if settings.viewer_row_limit <= 0:
        raise ValueError("viewer_row_limit must be greater than zero.")
    if settings.editor_trace_limit <= 0:
        raise ValueError("editor_trace_limit must be greater than zero.")
    return settings, warnings


def build_session_id(*, template: str, animal_id: str, session_date: date, day: int | None) -> str:
    format_values = {
        "animal_id": animal_id,
        "session_date": session_date,
        "date_ymd": session_date.strftime("%Y%m%d"),
        "day": "" if day is None else day,
        "day_suffix": "" if day is None else f"_d{day}",
    }

    try:
        rendered = template.format(**format_values).strip()
    except (IndexError, KeyError, ValueError) as exc:
        available = ", ".join(sorted(format_values))
        raise ValueError(
            f"Invalid session_id_template. Available placeholders: {available}."
        ) from exc

    if not rendered:
        raise ValueError("session_id_template produced an empty session_id.")
    return rendered

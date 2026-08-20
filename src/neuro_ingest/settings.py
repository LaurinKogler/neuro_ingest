"""Persistent user defaults for the Streamlit workbench.

Shipped defaults live in this module. User overrides are written to
``data/processed/settings/user_settings.json`` so local preferences stay out of
Git and raw acquisition files remain untouched.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_USER_SETTINGS_PATH = (
    PROJECT_ROOT / "data" / "processed" / "settings" / "user_settings.json"
)

DEFAULT_SETTINGS: dict[str, Any] = {
    "plot": {
        "trace_spacing_mode": "readable",
        "trace_spacing_uv": 5.0,
        "amplitude_scale": 1.0,
        "relation_mode": "ipsi",
    },
    "viewer": {
        "row_limit": 100000,
    },
    "editor": {
        "trace_limit": 5000,
        "create_backup": True,
    },
}


def default_settings() -> dict[str, Any]:
    return copy.deepcopy(DEFAULT_SETTINGS)


def user_settings_path(path: str | Path | None = None) -> Path:
    return Path(path) if path is not None else DEFAULT_USER_SETTINGS_PATH


def load_settings(path: str | Path | None = None) -> dict[str, Any]:
    settings = default_settings()
    settings_path = user_settings_path(path)
    if not settings_path.exists():
        return settings

    try:
        user_values = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid settings JSON: {settings_path}") from exc

    if not isinstance(user_values, dict):
        raise ValueError(f"Settings file must contain a JSON object: {settings_path}")
    return _merge_known_settings(settings, user_values)


def save_settings(settings: dict[str, Any], path: str | Path | None = None) -> Path:
    settings_path = user_settings_path(path)
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    merged = _merge_known_settings(default_settings(), settings)
    settings_path.write_text(
        json.dumps(merged, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return settings_path


def reset_user_settings(path: str | Path | None = None) -> None:
    settings_path = user_settings_path(path)
    if settings_path.exists():
        settings_path.unlink()


def get_setting(settings: dict[str, Any], path: str, fallback: Any = None) -> Any:
    current: Any = settings
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return fallback
        current = current[part]
    return current


def _merge_known_settings(
    base: dict[str, Any], user_values: dict[str, Any]
) -> dict[str, Any]:
    for key, value in user_values.items():
        if key not in base:
            continue
        if isinstance(base[key], dict) and isinstance(value, dict):
            base[key] = _merge_known_settings(base[key], value)
        elif _compatible_value(base[key], value):
            base[key] = value
    return base


def _compatible_value(default: Any, value: Any) -> bool:
    if isinstance(default, bool):
        return isinstance(value, bool)
    if isinstance(default, int) and not isinstance(default, bool):
        return isinstance(value, int) and not isinstance(value, bool)
    if isinstance(default, float):
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if isinstance(default, str):
        return isinstance(value, str)
    if isinstance(default, list):
        return isinstance(value, list)
    return type(value) is type(default)

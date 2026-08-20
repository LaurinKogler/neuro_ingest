import json

import pytest

from neuro_ingest import settings as app_settings


def test_load_settings_returns_defaults_when_user_file_is_missing(tmp_path):
    settings = app_settings.load_settings(tmp_path / "missing.json")

    assert settings == app_settings.default_settings()


def test_save_and_load_settings_roundtrip(tmp_path):
    path = tmp_path / "user_settings.json"

    saved_path = app_settings.save_settings(
        {
            "plot": {
                "trace_spacing_mode": "manual",
                "trace_spacing_uv": 8.5,
                "amplitude_scale": 1.25,
            },
            "viewer": {"row_limit": 250000},
        },
        path,
    )
    loaded = app_settings.load_settings(path)

    assert saved_path == path
    assert loaded["plot"]["trace_spacing_mode"] == "manual"
    assert loaded["plot"]["trace_spacing_uv"] == 8.5
    assert loaded["plot"]["amplitude_scale"] == 1.25
    assert loaded["plot"]["relation_mode"] == "ipsi"
    assert loaded["viewer"]["row_limit"] == 250000


def test_load_settings_ignores_unknown_keys_and_wrong_types(tmp_path):
    path = tmp_path / "user_settings.json"
    path.write_text(
        json.dumps(
            {
                "plot": {
                    "trace_spacing_uv": "wide",
                    "unknown": True,
                },
                "unknown_section": {"value": 1},
            }
        ),
        encoding="utf-8",
    )

    loaded = app_settings.load_settings(path)

    assert loaded == app_settings.default_settings()


def test_load_settings_rejects_invalid_json(tmp_path):
    path = tmp_path / "user_settings.json"
    path.write_text("{", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid settings JSON"):
        app_settings.load_settings(path)

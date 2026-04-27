from datetime import date

import pytest

from neuro_ingest.ui.settings import IngestUISettings, build_session_id, load_ui_settings


def test_load_ui_settings_returns_defaults_when_local_file_is_missing(tmp_path):
    settings, warnings = load_ui_settings(tmp_path)

    assert settings == IngestUISettings()
    assert warnings == []


def test_load_ui_settings_applies_local_overrides(tmp_path):
    config_path = tmp_path / "ingest_ui.local.toml"
    config_path.write_text(
        "\n".join(
            [
                'db_path = "D:/NeuroIngest/neuro_audio.duckdb"',
                'parquet_dir = "D:/NeuroIngest/normalized"',
                'session_id_template = "{animal_id}{day_suffix}_{date_ymd}"',
                "overwrite = true",
                "viewer_row_limit = 250000",
                "editor_trace_limit = 2500",
            ]
        ),
        encoding="utf-8",
    )

    settings, warnings = load_ui_settings(tmp_path)

    assert warnings == []
    assert settings.db_path == "D:/NeuroIngest/neuro_audio.duckdb"
    assert settings.parquet_dir == "D:/NeuroIngest/normalized"
    assert settings.overwrite is True
    assert settings.viewer_row_limit == 250000
    assert settings.editor_trace_limit == 2500
    assert build_session_id(
        template=settings.session_id_template,
        animal_id="AC04",
        session_date=date(2025, 10, 17),
        day=3,
    ) == "AC04_d3_20251017"


def test_load_ui_settings_warns_on_unknown_fields(tmp_path):
    config_path = tmp_path / "ingest_ui.local.toml"
    config_path.write_text(
        "\n".join(
            [
                'db_path = "normalized/custom.duckdb"',
                'unknown_setting = "ignored"',
            ]
        ),
        encoding="utf-8",
    )

    settings, warnings = load_ui_settings(tmp_path)

    assert settings.db_path == "normalized/custom.duckdb"
    assert warnings == ["Ignoring unknown UI setting 'unknown_setting' in ingest_ui.local.toml."]


def test_load_ui_settings_rejects_invalid_types(tmp_path):
    config_path = tmp_path / "ingest_ui.local.toml"
    config_path.write_text('viewer_row_limit = "lots"', encoding="utf-8")

    with pytest.raises(ValueError, match="viewer_row_limit"):
        load_ui_settings(tmp_path)

import pandas as pd

from neuro_ingest.ui.tables import display_dataframe, first_value, source_columns


def test_display_dataframe_hides_source_columns_and_renames():
    rows = pd.DataFrame(
        {
            "session_id": ["S1"],
            "session_date": ["2025-10-17"],
            "source_file": ["raw/file.txt"],
            "artifact_path": ["cache/file.parquet"],
        }
    )

    display = display_dataframe(
        rows,
        rename={"session_id": "Session"},
    )

    assert display.columns.tolist() == ["Session", "session_date"]
    assert display.iloc[0]["Session"] == "S1"


def test_source_columns_identifies_provenance_paths():
    rows = pd.DataFrame(columns=["source_file", "db_path", "animal_id"])

    assert source_columns(rows) == ["source_file", "db_path"]


def test_first_value_returns_first_non_null_value():
    rows = pd.DataFrame({"animal_id": [None, "AC04"]})

    assert first_value(rows, "animal_id") == "AC04"

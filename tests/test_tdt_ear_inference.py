from pathlib import Path

from neuro_ingest.ingest.tdt_ear import infer_tdt_ear_from_filenames


def test_click_token_does_not_imply_left():
    paths = [Path("AC04_ClickABR_20251017.txt")]
    assert infer_tdt_ear_from_filenames(paths) is None


def test_infers_right_from_filename_tokens():
    paths = [Path("AC04_ClickABR_right_20251017.txt")]
    assert infer_tdt_ear_from_filenames(paths) == "right"


def test_mixed_sides_returns_none():
    paths = [
        Path("AC04_ClickABR_left_20251017.txt"),
        Path("AC04_ClickABR_right_20251017.txt"),
    ]
    assert infer_tdt_ear_from_filenames(paths) is None

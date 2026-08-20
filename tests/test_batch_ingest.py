from __future__ import annotations

from pathlib import Path

from neuro_ingest.batch import discover_tdt_tree, ingest_tdt_tree
from neuro_ingest.toolbox import NeuroAudioToolbox


def _copy_sample_tree(root: Path) -> Path:
    src = Path("tests/data/AC04_ClickABR_right_20251017.txt")
    tree = root / "Data Noise Gerbil AC102 CS"
    session = tree / "AC04" / "AC04_d0_20251017"
    session.mkdir(parents=True)
    for idx, name in enumerate(
        [
        "AC04_ClickABR_left_20251017.txt",
        "AC04_ClickABR_right_20251017.txt",
        "AC04_ToneABR_left_20251017_110dB.txt",
        "AC04_ToneABR_left_lower_20251017.txt",
        "AC04_ToneABR_right_20251017.txt",
        ]
    ):
        (session / name).write_bytes(src.read_bytes() + f"\n# fixture copy {idx}\n".encode())
    return tree


def test_discover_tdt_tree_groups_folder_session_and_merges_extra_files(tmp_path: Path):
    root = _copy_sample_tree(tmp_path)

    discovery = discover_tdt_tree(root)

    assert len(discovery.sessions) == 1
    assert discovery.rejected_files == []
    plan = discovery.sessions[0]
    assert plan.session_id == "AC04_d0_20251017"
    assert plan.animal_id == "AC04"
    assert plan.day == 0
    assert len(plan.files) == 5
    assert plan.status == "warning"
    assert any("ToneABR left has 2 files" in warning for warning in plan.warnings)
    labels = sorted({file.stimulus_label for file in plan.files})
    assert "ToneABR 110dB" in labels
    assert "ToneABR lower" in labels


def test_discover_tdt_tree_reports_rejected_ambiguous_side(tmp_path: Path):
    src = Path("tests/data/AC04_ClickABR_right_20251017.txt")
    root = tmp_path / "tree"
    session = root / "AC01" / "AC01_d3_20250801"
    session.mkdir(parents=True)
    (session / "AC01_ToneABR_rleft_20250801.txt").write_bytes(src.read_bytes())

    discovery = discover_tdt_tree(root)

    assert discovery.sessions == []
    assert len(discovery.rejected_files) == 1
    assert "filename did not expose" in discovery.rejected_files[0].reason


def test_ingest_tdt_tree_writes_merged_session_to_storage(tmp_path: Path):
    root = _copy_sample_tree(tmp_path)
    toolbox = NeuroAudioToolbox(
        db_path=tmp_path / "batch.duckdb",
        parquet_dir=tmp_path / "normalized",
    )

    result = ingest_tdt_tree(root=root, toolbox=toolbox, overwrite=True)

    assert len(result.results) == 1
    written = result.results[0]
    assert written.status == "written"
    assert written.write is not None
    assert written.write.parquet_path.exists()

    rows = toolbox.get_samples(session_id="AC04_d0_20251017", limit=1_000_000)
    assert not rows.empty
    assert rows["session_id"].unique().tolist() == ["AC04_d0_20251017"]
    assert set(rows["stim_ear"].dropna().unique()) == {"left", "right"}
    labels = set(rows["stimulus_label"].dropna().unique())
    assert "ToneABR 110dB" in labels
    assert "ToneABR lower" in labels


def test_ingest_tdt_tree_can_skip_existing_sessions(tmp_path: Path):
    root = _copy_sample_tree(tmp_path)
    toolbox = NeuroAudioToolbox(
        db_path=tmp_path / "batch.duckdb",
        parquet_dir=tmp_path / "normalized",
    )

    first = ingest_tdt_tree(root=root, toolbox=toolbox, on_existing="fail")
    second = ingest_tdt_tree(root=root, toolbox=toolbox, on_existing="skip")

    assert first.results[0].status == "written"
    assert second.results[0].status == "skipped"


def test_ingest_tdt_tree_fails_existing_sessions_by_default(tmp_path: Path):
    root = _copy_sample_tree(tmp_path)
    toolbox = NeuroAudioToolbox(
        db_path=tmp_path / "batch.duckdb",
        parquet_dir=tmp_path / "normalized",
    )

    ingest_tdt_tree(root=root, toolbox=toolbox)
    second = ingest_tdt_tree(root=root, toolbox=toolbox)

    assert second.results[0].status == "error"

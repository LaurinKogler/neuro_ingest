from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

import pytest


@pytest.fixture
def tmp_path():
    """
    Project-local replacement for pytest's built-in tmp_path fixture.

    Some locked-down Windows environments reject pytest's default temp-dir
    creation mode. Using tempfile.mkdtemp keeps temp test directories usable
    without patching pytest internals.
    """
    root = Path("test_runtime") / "tmp"
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"neuro_ingest_test_{uuid4().hex}"
    path.mkdir(parents=False, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)

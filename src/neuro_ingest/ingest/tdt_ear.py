from __future__ import annotations

import re
from pathlib import Path


LEFT_TOKENS = {"l", "left", "links"}
RIGHT_TOKENS = {"r", "right", "rechts"}


def infer_tdt_ear_from_filenames(paths: list[Path]) -> str | None:
    """
    Infer a single TDT ear side from filenames.

    Returns:
        "left" / "right" when all files resolve to the same side.
        None if any file is unresolved or files resolve to mixed sides.
    """
    if not paths:
        return None

    inferred_per_file: list[str | None] = []
    for path in paths:
        inferred_per_file.append(_infer_ear_from_name(path.name))

    if all(side == "left" for side in inferred_per_file):
        return "left"
    if all(side == "right" for side in inferred_per_file):
        return "right"
    return None


def _infer_ear_from_name(filename: str) -> str | None:
    stem = Path(filename).stem.lower()
    tokens = [tok for tok in re.split(r"[^a-z0-9]+", stem) if tok]
    has_left = any(tok in LEFT_TOKENS for tok in tokens)
    has_right = any(tok in RIGHT_TOKENS for tok in tokens)

    if has_left and has_right:
        return None
    if has_left:
        return "left"
    if has_right:
        return "right"
    return None

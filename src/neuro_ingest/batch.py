from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
import re
from typing import Literal

import pandas as pd

from neuro_ingest.data.models import SessionData, StorageWriteResult
from neuro_ingest.toolbox import NeuroAudioToolbox


SESSION_DIR_RE = re.compile(
    r"^(?P<animal_id>[A-Za-z]+\d+)_d(?P<day>\d+)_(?P<date_ymd>\d{8})$"
)
STIMULUS_TOKENS = {"clickabr": "ClickABR", "toneabr": "ToneABR"}
EAR_TOKENS = {"left": "left", "right": "right"}
EAR_ALIASES = {"leftt": "left"}
SUPPORTED_SUFFIXES = {".txt", ".asc", ".csv"}
ExistingSessionMode = Literal["fail", "skip", "overwrite"]


@dataclass(frozen=True)
class BatchFile:
    path: Path
    animal_id: str
    session_id: str
    session_date: date
    day: int
    stimulus: str
    ear: Literal["left", "right"]
    stimulus_label: str
    filename_date: date | None
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class RejectedBatchFile:
    path: Path
    reason: str


@dataclass
class BatchSessionPlan:
    session_id: str
    animal_id: str
    session_date: date
    day: int
    system: str = "TDT"
    paradigm: str = "abr"
    files: list[BatchFile] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        if not self.files:
            return "empty"
        if self.warnings or any(file.warnings for file in self.files):
            return "warning"
        return "ready"

    def files_for_ear(self, ear: Literal["left", "right"]) -> list[BatchFile]:
        return [file for file in self.files if file.ear == ear]


@dataclass(frozen=True)
class BatchDiscovery:
    root: Path
    sessions: list[BatchSessionPlan]
    rejected_files: list[RejectedBatchFile]

    def to_dataframe(self) -> pd.DataFrame:
        rows: list[dict[str, object]] = []
        for plan in self.sessions:
            counts = Counter((file.stimulus, file.ear) for file in plan.files)
            warnings = _unique_warnings(
                [*plan.warnings, *(warning for file in plan.files for warning in file.warnings)]
            )
            rows.append(
                {
                    "session_id": plan.session_id,
                    "animal_id": plan.animal_id,
                    "day": plan.day,
                    "session_date": plan.session_date,
                    "status": plan.status,
                    "files": len(plan.files),
                    "click_left": counts.get(("ClickABR", "left"), 0),
                    "click_right": counts.get(("ClickABR", "right"), 0),
                    "tone_left": counts.get(("ToneABR", "left"), 0),
                    "tone_right": counts.get(("ToneABR", "right"), 0),
                    "warnings": "; ".join(warnings),
                }
            )
        return pd.DataFrame(rows)


@dataclass(frozen=True)
class BatchSessionResult:
    plan: BatchSessionPlan
    session: SessionData | None
    write: StorageWriteResult | None
    status: str
    error: str | None = None


@dataclass(frozen=True)
class BatchRunResult:
    discovery: BatchDiscovery
    results: list[BatchSessionResult]

    def to_dataframe(self) -> pd.DataFrame:
        rows = []
        for result in self.results:
            rows.append(
                {
                    "session_id": result.plan.session_id,
                    "status": result.status,
                    "files": len(result.plan.files),
                    "rows_written": None
                    if result.write is None
                    else int(result.write.rows_written),
                    "parquet_path": None
                    if result.write is None
                    else str(result.write.parquet_path),
                    "error": result.error,
                }
            )
        return pd.DataFrame(rows)


def discover_tdt_tree(root: str | Path, *, paradigm: str = "abr") -> BatchDiscovery:
    root = Path(root)
    plans_by_session: dict[str, BatchSessionPlan] = {}
    rejected: list[RejectedBatchFile] = []

    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        if path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue

        parsed = _parse_tdt_file(path=path, root=root)
        if isinstance(parsed, RejectedBatchFile):
            rejected.append(parsed)
            continue

        plan = plans_by_session.get(parsed.session_id)
        if plan is None:
            plan = BatchSessionPlan(
                session_id=parsed.session_id,
                animal_id=parsed.animal_id,
                session_date=parsed.session_date,
                day=parsed.day,
                paradigm=paradigm,
            )
            plans_by_session[parsed.session_id] = plan
        plan.files.append(parsed)

    sessions = sorted(
        plans_by_session.values(),
        key=lambda item: (item.animal_id, item.day, item.session_date, item.session_id),
    )
    for plan in sessions:
        plan.files.sort(key=lambda file: (file.ear, file.stimulus, file.stimulus_label, str(file.path)))
        plan.warnings.extend(_session_warnings(plan))

    return BatchDiscovery(root=root, sessions=sessions, rejected_files=rejected)


def ingest_tdt_tree(
    *,
    root: str | Path,
    toolbox: NeuroAudioToolbox,
    overwrite: bool = False,
    on_existing: ExistingSessionMode | None = None,
    dry_run: bool = False,
    stop_on_error: bool = False,
    paradigm: str = "abr",
) -> BatchRunResult:
    discovery = discover_tdt_tree(root, paradigm=paradigm)
    results: list[BatchSessionResult] = []
    existing_mode = on_existing or ("overwrite" if overwrite else "fail")
    if existing_mode not in {"fail", "skip", "overwrite"}:
        raise ValueError("on_existing must be one of: fail, skip, overwrite.")

    for plan in discovery.sessions:
        if dry_run:
            results.append(
                BatchSessionResult(
                    plan=plan,
                    session=None,
                    write=None,
                    status=plan.status,
                )
            )
            continue

        try:
            if existing_mode == "skip" and toolbox.session_exists(plan.session_id):
                results.append(
                    BatchSessionResult(
                        plan=plan,
                        session=None,
                        write=None,
                        status="skipped",
                        error="Session already exists.",
                    )
                )
                continue

            session = _ingest_session_plan(toolbox=toolbox, plan=plan)
            write = toolbox.save(session, overwrite=(existing_mode == "overwrite"))
            results.append(
                BatchSessionResult(
                    plan=plan,
                    session=session,
                    write=write,
                    status="written",
                )
            )
        except Exception as exc:
            results.append(
                BatchSessionResult(
                    plan=plan,
                    session=None,
                    write=None,
                    status="error",
                    error=str(exc),
                )
            )
            if stop_on_error:
                break

    return BatchRunResult(discovery=discovery, results=results)


def _ingest_session_plan(*, toolbox: NeuroAudioToolbox, plan: BatchSessionPlan) -> SessionData:
    side_sessions: list[SessionData] = []
    labels_by_path = {str(file.path): file.stimulus_label for file in plan.files}

    for ear in ("left", "right"):
        ear_files = plan.files_for_ear(ear)
        if not ear_files:
            continue

        session = toolbox.ingest_files(
            system=plan.system,
            files=[file.path for file in ear_files],
            animal_id=plan.animal_id,
            session_date=plan.session_date,
            paradigm=plan.paradigm,
            day=plan.day,
            session_id=plan.session_id,
            tdt_ear=ear,
        )
        rows = session.rows.copy()
        rows["stimulus_label"] = rows["source_file"].map(labels_by_path).fillna(
            rows["stimulus_label"]
        )
        side_sessions.append(
            SessionData(
                session_id=session.session_id,
                system=session.system,
                animal_id=session.animal_id,
                session_date=session.session_date,
                paradigm=session.paradigm,
                rows=rows,
            )
        )

    if not side_sessions:
        raise ValueError(f"No ingestible left/right files for {plan.session_id}.")
    return _combine_session_data(side_sessions, session_id=plan.session_id)


def _combine_session_data(sessions: list[SessionData], *, session_id: str) -> SessionData:
    base = sessions[0]
    rows = pd.concat([session.rows for session in sessions], ignore_index=True)
    if not (rows["session_id"] == session_id).all():
        rows = rows.copy()
        rows["session_id"] = session_id
    return SessionData(
        session_id=session_id,
        system=base.system,
        animal_id=base.animal_id,
        session_date=base.session_date,
        paradigm=base.paradigm,
        rows=rows,
    )


def _parse_tdt_file(*, path: Path, root: Path) -> BatchFile | RejectedBatchFile:
    try:
        relative = path.relative_to(root)
    except ValueError:
        relative = path

    parts = relative.parts
    if len(parts) < 3:
        return RejectedBatchFile(path=path, reason="expected animal/session/file tree")

    animal_dir = parts[-3]
    session_dir = parts[-2]
    folder_match = SESSION_DIR_RE.match(session_dir)
    if folder_match is None:
        return RejectedBatchFile(path=path, reason="session folder must match <animal>_d<day>_<YYYYMMDD>")

    folder_animal = folder_match.group("animal_id")
    day = int(folder_match.group("day"))
    session_date = _date_from_ymd(folder_match.group("date_ymd"))
    parsed_name = _parse_tdt_filename(path.stem)
    if parsed_name is None:
        return RejectedBatchFile(path=path, reason="filename did not expose animal/stimulus/ear/date")

    warnings: list[str] = []
    if animal_dir != folder_animal:
        warnings.append(f"animal directory {animal_dir!r} differs from session folder {folder_animal!r}")
    if parsed_name["animal_id"] != folder_animal:
        warnings.append(
            f"filename animal {parsed_name['animal_id']!r} differs from session folder {folder_animal!r}"
        )
    filename_date = parsed_name["filename_date"]
    if filename_date is not None and filename_date != session_date:
        warnings.append(f"filename date {filename_date:%Y%m%d} differs from folder date {session_date:%Y%m%d}")
    warnings.extend(parsed_name["warnings"])

    return BatchFile(
        path=path,
        animal_id=folder_animal,
        session_id=session_dir,
        session_date=session_date,
        day=day,
        stimulus=parsed_name["stimulus"],
        ear=parsed_name["ear"],
        stimulus_label=parsed_name["stimulus_label"],
        filename_date=filename_date,
        warnings=tuple(warnings),
    )


def _parse_tdt_filename(stem: str) -> dict[str, object] | None:
    tokens = [token for token in re.split(r"[_\s]+", stem) if token]
    if len(tokens) < 4:
        return None

    animal_id = tokens[0]
    stimulus = STIMULUS_TOKENS.get(tokens[1].lower())
    if stimulus is None:
        return None

    ear_idx: int | None = None
    ear: Literal["left", "right"] | None = None
    warnings: list[str] = []
    for idx, token in enumerate(tokens[2:], start=2):
        key = token.lower()
        if key in EAR_TOKENS:
            ear_idx = idx
            ear = EAR_TOKENS[key]
            break
        if key in EAR_ALIASES:
            ear_idx = idx
            ear = EAR_ALIASES[key]
            warnings.append(f"ear token {token!r} treated as {ear!r}")
            break

    date_idx: int | None = None
    filename_date: date | None = None
    for idx, token in enumerate(tokens[2:], start=2):
        if re.fullmatch(r"\d{8}", token):
            date_idx = idx
            filename_date = _date_from_ymd(token)
            break

    if ear_idx is None or ear is None or date_idx is None:
        return None

    variant_tokens = [
        token
        for idx, token in enumerate(tokens[2:], start=2)
        if idx not in {ear_idx, date_idx}
    ]
    stimulus_label = _stimulus_label(stimulus=stimulus, variant_tokens=variant_tokens)
    return {
        "animal_id": animal_id,
        "stimulus": stimulus,
        "ear": ear,
        "filename_date": filename_date,
        "stimulus_label": stimulus_label,
        "warnings": warnings,
    }


def _stimulus_label(*, stimulus: str, variant_tokens: list[str]) -> str:
    if not variant_tokens:
        return stimulus
    variant = " ".join(token.replace("-", "-") for token in variant_tokens)
    return f"{stimulus} {variant}"


def _session_warnings(plan: BatchSessionPlan) -> list[str]:
    warnings: list[str] = []
    counts = Counter((file.stimulus, file.ear) for file in plan.files)
    for stimulus in ("ClickABR", "ToneABR"):
        sides = {ear for (stim, ear), count in counts.items() if stim == stimulus and count > 0}
        if sides and sides != {"left", "right"}:
            warnings.append(f"{stimulus} has only {', '.join(sorted(sides))} file(s)")
    for (stimulus, ear), count in sorted(counts.items()):
        if count > 1:
            warnings.append(f"{stimulus} {ear} has {count} files; they will be merged")
    return warnings


def _unique_warnings(warnings: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for warning in warnings:
        if warning in seen:
            continue
        seen.add(warning)
        unique.append(warning)
    return unique


def _date_from_ymd(value: str) -> date:
    return datetime.strptime(value, "%Y%m%d").date()

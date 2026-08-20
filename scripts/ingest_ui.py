from __future__ import annotations

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import streamlit as st

from neuro_ingest import settings as app_settings
from neuro_ingest.batch import discover_tdt_tree, ingest_tdt_tree
from neuro_ingest.toolbox import NeuroAudioToolbox
from neuro_ingest.storage.parquet_store import ParquetStore
from neuro_ingest.ui.settings import (
    IngestUISettings,
    LOCAL_UI_SETTINGS_FILENAME,
    build_session_id,
    load_ui_settings,
)
from neuro_ingest.ui.style import (
    inject_css,
    render_command_panel,
    render_header,
    render_sidebar_brand,
    render_status_row,
)
from neuro_ingest.ui.tables import display_dataframe, show_collapsible_table
from neuro_ingest.ui.workflow import (
    VIEWER_SOURCE_OPTIONS,
    combine_sessions,
    default_viewer_source_index,
    discover_duckdb_paths,
    format_frequency_label,
    parse_day_filter,
    stage_uploaded_files,
)


def _current_settings() -> dict:
    if "app_user_settings" not in st.session_state:
        st.session_state.app_user_settings = app_settings.load_settings()
    return dict(st.session_state.app_user_settings)


def _setting(path: str, fallback=None):
    return app_settings.get_setting(_current_settings(), path, fallback)


def _add_settings_panel(ui_settings: IngestUISettings) -> None:
    with st.expander("Settings", expanded=False):
        st.caption("Saved defaults are personal and are not committed to Git.")
        with st.form("app_settings_form"):
            trace_spacing_mode = st.selectbox(
                "Default trace density",
                ["compact", "readable", "wide", "custom"],
                index=_plot_density_options().index(
                    _default_density_choice()
                ),
            )
            trace_spacing_uv = st.number_input(
                "Custom trace spacing (uV)",
                min_value=0.0,
                max_value=1000.0,
                value=float(_setting("plot.trace_spacing_uv", 5.0)),
                step=0.25,
            )
            amplitude_scale = st.number_input(
                "Default amplitude scale",
                min_value=0.1,
                max_value=10.0,
                value=float(_setting("plot.amplitude_scale", 1.0)),
                step=0.1,
            )
            relation_mode = st.selectbox(
                "Default relation mode",
                ["ipsi", "ipsi_contra"],
                index=(
                    0 if _setting("plot.relation_mode", "ipsi") == "ipsi" else 1
                ),
                format_func=lambda value: (
                    "ipsi only" if value == "ipsi" else "ipsi + contra"
                ),
            )
            viewer_row_limit = st.number_input(
                "Default viewer row limit",
                min_value=100,
                max_value=500000,
                value=int(_setting("viewer.row_limit", ui_settings.viewer_row_limit)),
                step=1000,
            )
            editor_trace_limit = st.number_input(
                "Default editor trace limit",
                min_value=100,
                max_value=100000,
                value=int(_setting("editor.trace_limit", ui_settings.editor_trace_limit)),
                step=100,
            )
            create_backup = st.checkbox(
                "Create editor backups by default",
                value=bool(_setting("editor.create_backup", True)),
            )
            save_settings = st.form_submit_button("Save defaults")

        if save_settings:
            updated = app_settings.default_settings()
            updated["plot"]["trace_spacing_mode"] = trace_spacing_mode
            updated["plot"]["trace_spacing_uv"] = float(trace_spacing_uv)
            updated["plot"]["amplitude_scale"] = float(amplitude_scale)
            updated["plot"]["relation_mode"] = relation_mode
            updated["viewer"]["row_limit"] = int(viewer_row_limit)
            updated["editor"]["trace_limit"] = int(editor_trace_limit)
            updated["editor"]["create_backup"] = bool(create_backup)
            saved_path = app_settings.save_settings(updated)
            st.session_state.app_user_settings = updated
            st.success(f"Saved {saved_path.relative_to(app_settings.PROJECT_ROOT)}")
            st.rerun()

        if st.button("Reset defaults", use_container_width=True):
            app_settings.reset_user_settings()
            st.session_state.app_user_settings = app_settings.default_settings()
            st.success("Reset to shipped defaults.")
            st.rerun()

        settings_path = app_settings.user_settings_path()
        st.caption(str(settings_path.relative_to(app_settings.PROJECT_ROOT)))


def _default_amplitude_scale() -> float:
    configured = float(_setting("plot.amplitude_scale", 1.0))
    return float(max(0.1, min(configured, 10.0)))


def _plot_density_options() -> list[str]:
    return ["compact", "readable", "wide", "custom"]


def _default_density_choice() -> str:
    choice = str(_setting("plot.trace_spacing_mode", "readable"))
    if choice == "auto":
        return "readable"
    if choice == "manual":
        return "custom"
    if choice not in _plot_density_options():
        return "readable"
    return choice


def _spacing_for_density(choice: str, *, max_spacing: float) -> float:
    if choice == "compact":
        return float(max_spacing * 0.45)
    if choice == "wide":
        return float(max_spacing * 1.35)
    if choice == "custom":
        configured = float(_setting("plot.trace_spacing_uv", 5.0))
        return float(max(0.0, configured))
    return float(max_spacing)


def _scale_preset_options() -> list[str]:
    return ["0.5x", "0.75x", "1x", "1.5x", "2x", "3x", "custom"]


def _scale_from_choice(choice: str, *, custom_scale: float | None = None) -> float:
    if choice == "custom":
        return _default_amplitude_scale() if custom_scale is None else float(custom_scale)
    return float(choice.removesuffix("x"))


def _duckdb_path_picker(
    *,
    label: str,
    default_path: str,
    parquet_dir: str,
    key_prefix: str,
) -> str:
    available_paths = discover_duckdb_paths(
        [Path(parquet_dir), Path("normalized"), Path("data")],
        fallback=default_path,
    )
    custom_label = "Custom DuckDB path"
    options = [*available_paths, custom_label]
    default_index = (
        options.index(default_path)
        if default_path in options
        else 0
        if available_paths
        else len(options) - 1
    )
    choice = st.selectbox(
        label,
        options=options,
        index=default_index,
        key=f"{key_prefix}_choice",
    )
    if choice == custom_label:
        return st.text_input(
            "DuckDB path",
            value=default_path,
            key=f"{key_prefix}_custom",
        )
    return str(choice)


def _choose_folder_dialog(*, initial_dir: str | Path = ".") -> str | None:
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        selected = filedialog.askdirectory(
            initialdir=str(Path(initial_dir).expanduser()),
            title="Choose TDT folder tree",
        )
        root.destroy()
    except Exception:
        return None
    return selected or None


def main() -> None:
    scripts_dir = Path(__file__).resolve().parent
    try:
        ui_settings, config_warnings = load_ui_settings(scripts_dir)
    except ValueError as exc:
        ui_settings = IngestUISettings()
        config_warnings = []
        config_error = f"Could not load {LOCAL_UI_SETTINGS_FILENAME}: {exc}"
    else:
        config_error = None

    st.set_page_config(page_title="Neuro Ingest UI", layout="wide")
    inject_css()
    render_header(
        title="Neuro-Audio Ingest Workbench",
        subtitle="Normalize TDT and IHS exports, persist sessions, and inspect ABR traces.",
    )
    if config_error is not None:
        st.error(config_error)
    for warning in config_warnings:
        st.warning(warning)
    with st.sidebar:
        render_sidebar_brand()
        _add_settings_panel(ui_settings)
        st.markdown('<div class="ni-section-label">Session</div>', unsafe_allow_html=True)
        system_options = ["TDT", "IHS"]
        system_choice = st.selectbox(
            "System (required)",
            system_options,
            index=system_options.index(ui_settings.system_choice),
        )
        animal_id = st.text_input("Animal ID", value=ui_settings.animal_id)
        session_date = st.date_input("Session date", value=date.today())
        paradigm = st.text_input("Paradigm", value=ui_settings.paradigm)
        day_text = st.text_input("Day (optional)", value=ui_settings.day_text)
        session_id = st.text_input("Session ID (optional)", value=ui_settings.session_id)

        st.markdown('<div class="ni-section-label">Storage</div>', unsafe_allow_html=True)
        parquet_dir = st.text_input("Parquet output dir", value=ui_settings.parquet_dir)
        available_db_paths = discover_duckdb_paths(
            [Path(parquet_dir), Path("normalized"), Path("data")],
            fallback=ui_settings.db_path,
        )
        db_options = [*available_db_paths, "New / custom DuckDB path"]
        db_default_index = (
            db_options.index(ui_settings.db_path)
            if ui_settings.db_path in db_options
            else 0
            if available_db_paths
            else len(db_options) - 1
        )
        db_choice = st.selectbox(
            "DuckDB target",
            options=db_options,
            index=db_default_index,
        )
        if db_choice == "New / custom DuckDB path":
            db_path = st.text_input("DuckDB path", value=ui_settings.db_path)
        else:
            db_path = db_choice
        overwrite = st.checkbox("Overwrite existing session", value=ui_settings.overwrite)

    target_session = session_id.strip() or build_session_id(
        template=ui_settings.session_id_template,
        animal_id=animal_id.strip() or "animal",
        session_date=session_date,
        day=int(day_text) if day_text.strip().lstrip("-").isdigit() else None,
    )
    render_status_row(
        [
            ("System", system_choice),
            ("Session", target_session),
            ("Parquet", parquet_dir),
            ("DuckDB", db_path),
        ]
    )

    ingest_tab, mass_tab, viewer_tab, editor_tab = st.tabs(["Ingest", "Mass Ingest", "Viewer", "Database"])

    with ingest_tab:
        tdt_left_files = []
        tdt_right_files = []
        ihs_files = []
        if system_choice == "TDT":
            st.subheader("TDT Upload")
            left_uploader, right_uploader = st.columns(2)
            with left_uploader:
                tdt_left_files = st.file_uploader(
                    "Left ear files",
                    accept_multiple_files=True,
                    type=["txt", "asc", "csv"],
                    key="tdt_left_files",
                )
            with right_uploader:
                tdt_right_files = st.file_uploader(
                    "Right ear files",
                    accept_multiple_files=True,
                    type=["txt", "asc", "csv"],
                    key="tdt_right_files",
                )
            render_command_panel(
                title="Ready check",
                subtitle="Current upload selection.",
                items=[
                    ("Left files", len(tdt_left_files)),
                    ("Right files", len(tdt_right_files)),
                    ("Total files", len(tdt_left_files) + len(tdt_right_files)),
                ],
            )
        else:
            st.subheader("IHS Upload")
            ihs_files = st.file_uploader(
                "IHS acquisition files",
                accept_multiple_files=True,
                type=["txt", "asc", "csv"],
                key="ihs_files",
            )
            render_command_panel(
                title="IHS batch",
                subtitle="Uploaded acquisition files will be normalized into one session.",
                items=[
                    ("IHS files", len(ihs_files)),
                    ("Overwrite", "yes" if overwrite else "no"),
                    ("Target", target_session),
                ],
            )

        if st.button("Ingest", type="primary"):
            if not animal_id.strip():
                st.error("Animal ID is required.")
                return
            if system_choice == "TDT":
                if not tdt_left_files and not tdt_right_files:
                    st.error("Upload at least one TDT file (left or right).")
                    return
            else:
                if not ihs_files:
                    st.error("Upload at least one IHS file.")
                    return

            day = None
            if day_text.strip():
                try:
                    day = int(day_text.strip())
                except ValueError:
                    st.error("Day must be an integer if provided.")
                    return

            try:
                toolbox = NeuroAudioToolbox(
                    db_path=Path(db_path),
                    parquet_dir=Path(parquet_dir),
                )
                sessions = []
                write = None

                with TemporaryDirectory(prefix="neuro_ingest_ui_") as tmpdir:
                    if system_choice == "TDT":
                        base_session_id = session_id.strip() or build_session_id(
                            template=ui_settings.session_id_template,
                            animal_id=animal_id.strip(),
                            session_date=session_date,
                            day=day,
                        )

                        if tdt_left_files:
                            left_dir = Path(tmpdir) / "left"
                            stage_uploaded_files(tdt_left_files, left_dir)
                            left_session = toolbox.ingest(
                                system="TDT",
                                input_path=left_dir,
                                animal_id=animal_id.strip(),
                                session_date=session_date,
                                paradigm=paradigm.strip() or "abr",
                                day=day,
                                session_id=base_session_id,
                                tdt_ear="left",
                            )
                            sessions.append(left_session)

                        if tdt_right_files:
                            right_dir = Path(tmpdir) / "right"
                            stage_uploaded_files(tdt_right_files, right_dir)
                            right_session = toolbox.ingest(
                                system="TDT",
                                input_path=right_dir,
                                animal_id=animal_id.strip(),
                                session_date=session_date,
                                paradigm=paradigm.strip() or "abr",
                                day=day,
                                session_id=base_session_id,
                                tdt_ear="right",
                            )
                            sessions.append(right_session)
                        merged_session = combine_sessions(sessions)
                        write = toolbox.save(merged_session, overwrite=overwrite)
                    else:
                        ihs_dir = Path(tmpdir) / "ihs"
                        stage_uploaded_files(ihs_files, ihs_dir)
                        ihs_session = toolbox.ingest(
                            system="IHS",
                            input_path=ihs_dir,
                            animal_id=animal_id.strip(),
                            session_date=session_date,
                            paradigm=paradigm.strip() or "abr",
                            day=day,
                            session_id=session_id.strip() or None,
                            tdt_ear=None,
                        )
                        sessions.append(ihs_session)
                        merged_session = ihs_session
                        write = toolbox.save(merged_session, overwrite=overwrite)

                if write is None:
                    raise RuntimeError("Ingest completed without any writable session.")

                st.session_state["last_session_rows"] = merged_session.rows
                st.session_state["last_session_id"] = merged_session.session_id
                st.session_state["last_session_title"] = f"{merged_session.session_id} ABR"
                st.session_state["last_parquet_path"] = str(write.parquet_path)
                st.session_state["last_db_path"] = str(write.db_path)
                st.session_state["viewer_rows"] = merged_session.rows
                st.session_state["viewer_title"] = f"{merged_session.session_id} ABR"

                st.success("Ingest completed.")
                m1, m2, m3 = st.columns(3)
                m1.metric("System", system_choice)
                m2.metric("Input Batches", len(sessions))
                m3.metric("Rows Written", int(write.rows_written))
                st.write(f"Parquet: `{write.parquet_path}`")
                st.write(f"DuckDB: `{write.db_path}`")
            except Exception as exc:
                st.error(f"Ingest failed: {exc}")
                st.exception(exc)


    with mass_tab:
        st.subheader("Mass TDT Tree Ingest")
        if "mass_root" not in st.session_state:
            st.session_state["mass_root"] = ""
        browse_col, path_col = st.columns([0.18, 0.82])
        with browse_col:
            if st.button("Browse", key="mass_browse_folder", use_container_width=True):
                selected_folder = _choose_folder_dialog(
                    initial_dir=st.session_state.get("mass_root") or "data"
                )
                if selected_folder:
                    st.session_state["mass_root"] = selected_folder
                    st.rerun()
                else:
                    st.info("No folder selected.")
        with path_col:
            mass_root = st.text_input(
                "Folder tree",
                key="mass_root",
                placeholder="Choose or paste the animal/session folder tree root",
            )
        target_mode = st.radio(
            "DuckDB target",
            options=["Merge into existing DuckDB", "Create new DuckDB"],
            horizontal=True,
            key="mass_target_mode",
        )
        if target_mode == "Merge into existing DuckDB":
            mass_available_db_paths = discover_duckdb_paths(
                [Path(parquet_dir), Path("normalized"), Path("data")],
                fallback=db_path,
            )
            if mass_available_db_paths:
                mass_db_path = st.selectbox(
                    "Existing DuckDB",
                    options=mass_available_db_paths,
                    index=(
                        mass_available_db_paths.index(db_path)
                        if db_path in mass_available_db_paths
                        else 0
                    ),
                    key="mass_existing_db_path",
                )
            else:
                mass_db_path = st.text_input(
                    "Existing DuckDB",
                    value=db_path,
                    key="mass_existing_db_path_text",
                )
                st.info("No existing DuckDB files were found in the usual project folders.")
        else:
            mass_db_path = st.text_input(
                "New DuckDB path",
                value=str(Path(parquet_dir) / "mass_export.duckdb"),
                key="mass_new_db_path",
            )

        mass_parquet_dir = st.text_input(
            "Parquet output dir",
            value=parquet_dir,
            key="mass_parquet_dir",
        )
        existing_label = st.selectbox(
            "When session already exists",
            options=[
                "Skip existing sessions",
                "Stop with an error",
                "Overwrite existing sessions",
            ],
            index=0,
            key="mass_existing_policy",
        )
        existing_mode = {
            "Skip existing sessions": "skip",
            "Stop with an error": "fail",
            "Overwrite existing sessions": "overwrite",
        }[existing_label]
        stop_on_error = st.checkbox("Stop on first ingest error", value=False, key="mass_stop_on_error")

        dry_col, run_col = st.columns([1, 1])
        with dry_col:
            dry_run_clicked = st.button("Dry run tree", key="mass_dry_run")
        with run_col:
            run_clicked = st.button("Run mass ingest", type="primary", key="mass_run")

        if dry_run_clicked:
            try:
                if not mass_root.strip():
                    st.error("Choose a folder tree first.")
                    return
                discovery = discover_tdt_tree(mass_root)
                st.session_state["mass_discovery_rows"] = discovery.to_dataframe()
                st.session_state["mass_rejected_rows"] = [
                    {"path": str(item.path), "reason": item.reason}
                    for item in discovery.rejected_files
                ]
                st.success(
                    f"Found {len(discovery.sessions)} sessions and {len(discovery.rejected_files)} rejected files."
                )
            except Exception as exc:
                st.error(f"Mass discovery failed: {exc}")
                st.exception(exc)

        if run_clicked:
            try:
                if not mass_root.strip():
                    st.error("Choose a folder tree first.")
                    return
                mass_toolbox = NeuroAudioToolbox(
                    db_path=Path(mass_db_path),
                    parquet_dir=Path(mass_parquet_dir),
                )
                result = ingest_tdt_tree(
                    root=mass_root,
                    toolbox=mass_toolbox,
                    on_existing=existing_mode,
                    stop_on_error=stop_on_error,
                )
                st.session_state["mass_run_rows"] = result.to_dataframe()
                st.session_state["last_db_path"] = str(mass_db_path)
                st.success(
                    f"Mass ingest finished: {len(result.results)} sessions processed."
                )
            except Exception as exc:
                st.error(f"Mass ingest failed: {exc}")
                st.exception(exc)

        if "mass_discovery_rows" in st.session_state:
            with st.expander("Mass discovery manifest", expanded=True):
                st.dataframe(st.session_state["mass_discovery_rows"], width="stretch")
        if st.session_state.get("mass_rejected_rows"):
            with st.expander("Rejected files", expanded=True):
                st.dataframe(st.session_state["mass_rejected_rows"], width="stretch")
        if "mass_run_rows" in st.session_state:
            with st.expander("Mass ingest report", expanded=True):
                st.dataframe(st.session_state["mass_run_rows"], width="stretch")


    with viewer_tab:
        source_mode = st.radio(
            "Choose rows for plotting",
            options=VIEWER_SOURCE_OPTIONS,
            horizontal=True,
            index=default_viewer_source_index(
                has_last_ingested_session="last_session_rows" in st.session_state
            ),
            label_visibility="collapsed",
        )
        default_parquet_path = st.session_state.get("last_parquet_path", "")
        default_db_path = st.session_state.get("last_db_path", db_path)
        query_sql = ui_settings.viewer_query_sql

        with st.expander("Load Viewer Data", expanded="viewer_rows" not in st.session_state):
            if source_mode == "Parquet file":
                parquet_path_input = st.text_input("Parquet path", value=default_parquet_path)
            elif source_mode == "DuckDB filters (no SQL)":
                db_filter_path = _duckdb_path_picker(
                    label="DuckDB path (filter mode)",
                    default_path=str(default_db_path),
                    parquet_dir=parquet_dir,
                    key_prefix="viewer_filter_db",
                )
                filter_options = {"animal_ids": [], "days": []}
                try:
                    option_toolbox = NeuroAudioToolbox(
                        db_path=Path(db_filter_path.strip()),
                        parquet_dir=Path(parquet_dir),
                    )
                    filter_options = option_toolbox.list_sample_filter_values()
                except Exception:
                    st.info("Choose an existing DuckDB file to populate filter dropdowns.")

                animal_options = ["(any)", *filter_options["animal_ids"]]
                f1, f2, f3 = st.columns(3)
                with f1:
                    filter_animal_id_choice = st.selectbox(
                        "animal_id",
                        options=animal_options,
                        index=0,
                    )
                    filter_animal_id = (
                        None
                        if filter_animal_id_choice == "(any)"
                        else filter_animal_id_choice
                    )
                    if filter_animal_id is not None:
                        try:
                            filter_options = option_toolbox.list_sample_filter_values(
                                animal_id=filter_animal_id
                            )
                        except Exception:
                            filter_options = {"animal_ids": [], "days": []}
                with f2:
                    filter_session_id = st.text_input("session_id (optional)", value="")
                with f3:
                    day_options = ["(any)", *[f"d{day}" for day in filter_options["days"]]]
                    filter_day_choice = st.selectbox("day", options=day_options, index=0)
                f4, f5, f6 = st.columns(3)
                with f4:
                    filter_system = st.selectbox("system", options=["(any)", "TDT", "IHS"], index=0)
                with f5:
                    filter_paradigm = st.text_input("paradigm (optional)", value="")
                with f6:
                    filter_limit = int(
                        st.number_input(
                            "row limit",
                            min_value=100,
                            max_value=500000,
                            value=int(
                                _setting("viewer.row_limit", ui_settings.viewer_row_limit)
                            ),
                            step=1000,
                        )
                    )
            elif source_mode == "DuckDB query":
                db_query_path = _duckdb_path_picker(
                    label="DuckDB path (viewer)",
                    default_path=str(default_db_path),
                    parquet_dir=parquet_dir,
                    key_prefix="viewer_query_db",
                )
                query_sql = st.text_area("SQL", value=query_sql, height=120)

            if st.button("Load data for viewer", key="load_viewer_rows", type="primary"):
                try:
                    if source_mode == "Last ingested session":
                        if "last_session_rows" not in st.session_state:
                            st.warning("No last-ingested session available yet.")
                        else:
                            st.session_state["viewer_rows"] = st.session_state["last_session_rows"]
                            st.session_state["viewer_title"] = st.session_state.get("last_session_title", "ABR Traces")
                            st.success("Loaded last ingested session rows.")
                    elif source_mode == "Parquet file":
                        if not parquet_path_input.strip():
                            st.error("Parquet path is required.")
                        else:
                            loaded = ParquetStore.load(parquet_path_input.strip())
                            if loaded.empty:
                                st.warning("Parquet loaded but no rows found.")
                            else:
                                st.session_state["viewer_rows"] = loaded
                                st.session_state["viewer_title"] = f"{Path(parquet_path_input).name} ABR"
                                st.success(f"Loaded {len(loaded)} rows from parquet.")
                    elif source_mode == "DuckDB filters (no SQL)":
                        if not db_filter_path.strip():
                            st.error("DuckDB path is required.")
                        else:
                            day_value = (
                                None
                                if filter_day_choice == "(any)"
                                else parse_day_filter(filter_day_choice)
                            )

                            if day_value != "invalid":
                                filter_toolbox = NeuroAudioToolbox(
                                    db_path=Path(db_filter_path.strip()),
                                    parquet_dir=Path(parquet_dir),
                                )
                                loaded = filter_toolbox.get_samples(
                                    animal_id=filter_animal_id,
                                    session_id=filter_session_id.strip() or None,
                                    day=day_value,
                                    system=None if filter_system == "(any)" else filter_system,
                                    paradigm=filter_paradigm.strip() or None,
                                    limit=filter_limit,
                                )
                                if loaded.empty:
                                    st.warning("No rows found for selected filters.")
                                else:
                                    title_bits = ["DuckDB Filters"]
                                    if filter_animal_id:
                                        title_bits.append(filter_animal_id)
                                    if filter_session_id.strip():
                                        title_bits.append(filter_session_id.strip())
                                    if day_value is not None:
                                        title_bits.append(f"day {day_value}")
                                    st.session_state["viewer_rows"] = loaded
                                    st.session_state["viewer_title"] = " | ".join(title_bits)
                                    st.success(f"Loaded {len(loaded)} rows from DuckDB filters.")
                    else:
                        if not db_query_path.strip():
                            st.error("DuckDB path is required.")
                        elif not query_sql.strip():
                            st.error("SQL query is required.")
                        else:
                            query_toolbox = NeuroAudioToolbox(
                                db_path=Path(db_query_path.strip()),
                                parquet_dir=Path(parquet_dir),
                            )
                            loaded = query_toolbox.query(query_sql.strip())
                            if loaded.empty:
                                st.warning("Query returned no rows.")
                            else:
                                st.session_state["viewer_rows"] = loaded
                                st.session_state["viewer_title"] = "DuckDB Query ABR"
                                st.success(f"Loaded {len(loaded)} rows from DuckDB query.")
                except Exception as exc:
                    st.error(f"Could not load viewer data: {exc}")
                    st.exception(exc)


    with editor_tab:
        st.subheader("DuckDB Editor")
        with st.expander("Edit existing DB traces", expanded=False):
            editor_db_path = st.text_input("DuckDB path (editor)", value=default_db_path, key="editor_db_path")
            create_backup = st.checkbox(
                "Create backup before edit",
                value=bool(_setting("editor.create_backup", True)),
                key="editor_create_backup",
            )
            backup_dir_input = st.text_input(
                "Backup directory (optional)",
                value="",
                key="editor_backup_dir",
                help="If empty, backups are stored next to the DB file in a 'backups' folder.",
            )
            backup_dir = backup_dir_input.strip() or None

            try:
                editor_toolbox = NeuroAudioToolbox(
                    db_path=Path(editor_db_path),
                    parquet_dir=Path(parquet_dir),
                )
                sessions_df = editor_toolbox.list_sessions()
            except Exception as exc:
                sessions_df = None
                st.error(f"Could not open DB for editing: {exc}")

            if sessions_df is not None and sessions_df.empty:
                st.info("No sessions found in this DuckDB file.")
            elif sessions_df is not None:
                session_options = sessions_df["session_id"].astype(str).tolist()
                selected_session = st.selectbox("Session", options=session_options, key="editor_session_id")
                trace_limit = int(
                    st.number_input(
                        "Trace summary limit",
                        min_value=100,
                        max_value=100000,
                        value=int(
                            _setting("editor.trace_limit", ui_settings.editor_trace_limit)
                        ),
                        step=100,
                        key="editor_trace_limit",
                    )
                )
                trace_df = editor_toolbox.list_trace_summaries(session_id=selected_session, limit=trace_limit)
                if trace_df.empty:
                    st.warning("No traces found for selected session.")
                else:
                    st.caption(f"Loaded {len(trace_df)} traces from session `{selected_session}`.")
                    show_collapsible_table(
                        "Trace summary",
                        display_dataframe(trace_df.head(500)),
                        expanded=False,
                        key="editor_trace_summary_preview",
                    )

                    label_to_trace: dict[str, str] = {}
                    trace_labels: list[str] = []
                    for row in trace_df.itertuples(index=False):
                        stim_ear = row.stim_ear if row.stim_ear is not None else "-"
                        rel_ear = row.rel_ear if row.rel_ear is not None else "-"
                        label = f"{row.trace_uid} | {format_frequency_label(row.freq_hz)} | {float(row.level_db):g} dB | {stim_ear}/{rel_ear}"
                        label_to_trace[label] = str(row.trace_uid)
                        trace_labels.append(label)

                    selected_labels = st.multiselect(
                        "Select traces",
                        options=trace_labels,
                        key="editor_selected_traces",
                    )
                    selected_trace_uids = [label_to_trace[x] for x in selected_labels]

                    action = st.radio(
                        "Edit action",
                        options=["Set ear metadata", "Delete traces"],
                        horizontal=True,
                        key="editor_action",
                    )
                    if action == "Set ear metadata":
                        choices = ["(keep)", "left", "right", "(clear)"]
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            stim_choice = st.selectbox("stim_ear", options=choices, key="editor_stim_choice")
                        with c2:
                            rec_choice = st.selectbox("rec_ear", options=choices, key="editor_rec_choice")
                        with c3:
                            rel_choice = st.selectbox("rel_ear", options=["(keep)", "ipsi", "contra", "(clear)"], key="editor_rel_choice")

                        updates: dict[str, object] = {}
                        if stim_choice != "(keep)":
                            updates["stim_ear"] = None if stim_choice == "(clear)" else stim_choice
                        if rec_choice != "(keep)":
                            updates["rec_ear"] = None if rec_choice == "(clear)" else rec_choice
                        if rel_choice != "(keep)":
                            updates["rel_ear"] = None if rel_choice == "(clear)" else rel_choice

                        if st.button("Apply metadata edit", key="editor_apply_metadata"):
                            if not selected_trace_uids:
                                st.error("Select at least one trace to edit.")
                            elif not updates:
                                st.error("Choose at least one field to update.")
                            else:
                                result = editor_toolbox.update_trace_fields(
                                    session_id=selected_session,
                                    trace_uids=selected_trace_uids,
                                    updates=updates,
                                    create_backup=create_backup,
                                    backup_dir=backup_dir,
                                )
                                st.success(f"Updated {result.rows_affected} sample rows.")
                                if result.backup_path is not None:
                                    st.write(f"Backup: `{result.backup_path}`")
                    else:
                        confirm = st.text_input(
                            "Type DELETE to confirm trace deletion",
                            value="",
                            key="editor_delete_confirm",
                        )
                        delete_disabled = confirm.strip() != "DELETE"
                        if st.button("Delete selected traces", key="editor_delete", disabled=delete_disabled):
                            if not selected_trace_uids:
                                st.error("Select at least one trace to delete.")
                            else:
                                result = editor_toolbox.delete_traces(
                                    session_id=selected_session,
                                    trace_uids=selected_trace_uids,
                                    create_backup=create_backup,
                                    backup_dir=backup_dir,
                                )
                                st.success(f"Deleted {result.rows_affected} sample rows.")
                                if result.backup_path is not None:
                                    st.write(f"Backup: `{result.backup_path}`")


    with viewer_tab:
        if "viewer_rows" in st.session_state:
            rows = st.session_state["viewer_rows"]
            plot_title = st.session_state.get("viewer_title", "ABR Traces")

            with st.expander("Preview rows", expanded=False):
                st.dataframe(display_dataframe(rows.head(300)), width="stretch")

            freq_values = sorted(float(v) for v in rows["freq_hz"].dropna().unique())
            if not freq_values:
                st.warning("No frequency values available for plotting.")
                return

            plot_control_left, plot_control_right = st.columns([1.2, 1])
            with plot_control_left:
                selected_freq = st.selectbox(
                    "Frequency (Hz)",
                    options=freq_values,
                    format_func=format_frequency_label,
                )
            with plot_control_right:
                relation_label = st.radio(
                    "Relation",
                    options=["ipsi only", "ipsi + contra"],
                    index=(
                        1 if _setting("plot.relation_mode", "ipsi") == "ipsi_contra" else 0
                    ),
                    horizontal=True,
                )
            relation_mode = "ipsi_contra" if relation_label == "ipsi + contra" else "ipsi"

            abs_amp = np.abs(rows["amplitude_uv"].to_numpy(dtype=float))
            p95 = float(np.percentile(abs_amp, 95)) if len(abs_amp) else 1.0
            if not np.isfinite(p95) or p95 <= 0:
                p95 = 1.0
            max_spacing = max(1.0, 2.0 * p95)
            step = max(0.01, max_spacing / 100.0)

            freq_rows = rows[np.isclose(rows["freq_hz"].astype(float), float(selected_freq))]
            side_values = sorted(
                s for s in freq_rows["stim_ear"].dropna().astype(str).str.lower().unique().tolist() if s in {"left", "right"}
            )
            if not side_values:
                side_values = ["all"]

            toolbox = NeuroAudioToolbox(
                db_path=Path(db_path),
                parquet_dir=Path(parquet_dir),
            )

            def view_controls(*, key_prefix: str) -> tuple[float, float]:
                control_left, control_right = st.columns(2)
                with control_left:
                    density_choice = st.selectbox(
                        "Density",
                        options=_plot_density_options(),
                        index=_plot_density_options().index(_default_density_choice()),
                        key=f"{key_prefix}_density",
                    )
                density_choice = str(density_choice or _default_density_choice())
                spacing_value = _spacing_for_density(
                    density_choice,
                    max_spacing=float(max_spacing),
                )
                if density_choice == "custom":
                    spacing_value = float(
                        st.number_input(
                            "Trace spacing (uV)",
                            min_value=0.0,
                            max_value=1000.0,
                            value=float(spacing_value),
                            step=max(0.1, float(step)),
                            key=f"{key_prefix}_spacing_uv",
                        )
                    )

                default_scale = _default_amplitude_scale()
                default_scale_label = f"{default_scale:g}x"
                scale_default = (
                    default_scale_label
                    if default_scale_label in _scale_preset_options()
                    else "custom"
                )
                with control_right:
                    scale_choice = st.selectbox(
                        "Size",
                        options=_scale_preset_options(),
                        index=_scale_preset_options().index(scale_default),
                        key=f"{key_prefix}_scale",
                    )
                scale_choice = str(scale_choice or scale_default)
                if scale_choice == "custom":
                    scale_value = float(
                        st.number_input(
                            "Waveform scale",
                            min_value=0.1,
                            max_value=10.0,
                            value=float(default_scale),
                            step=0.1,
                            key=f"{key_prefix}_custom_scale",
                        )
                    )
                else:
                    scale_value = _scale_from_choice(scale_choice)

                return spacing_value, scale_value

            if len(side_values) == 1:
                spacing_uv, amplitude_scale = view_controls(key_prefix="global_view")

                side = side_values[0]
                if side == "all":
                    side_rows = rows
                    side_title = plot_title
                else:
                    side_rows = rows[rows["stim_ear"].fillna("").astype(str).str.lower() == side]
                    side_title = f"{plot_title} | {side}"

                side_freq_rows = side_rows[np.isclose(side_rows["freq_hz"].astype(float), float(selected_freq))]
                if relation_mode == "ipsi_contra" and not (side_freq_rows["rel_ear"].fillna("ipsi") == "contra").any():
                    st.info(f"No contra rows for {side}; viewer will show ipsi only.")

                fig = toolbox.plot(
                    side_rows,
                    color_by="level_db",
                    title=side_title,
                    frequency_hz=float(selected_freq),
                    relation_mode=relation_mode,
                    spacing_uv=float(spacing_uv),
                    amplitude_scale=float(amplitude_scale),
                    intensity_order="desc",
                )
                st.plotly_chart(fig, width="stretch", theme=None)
            else:
                left_col, right_col = st.columns(2)
                for side, col in [("left", left_col), ("right", right_col)]:
                    with col:
                        side_rows = rows[rows["stim_ear"].fillna("").astype(str).str.lower() == side]
                        st.markdown(f'<div class="ni-plot-side-title">{side.title()}</div>', unsafe_allow_html=True)
                        if side_rows.empty:
                            st.info("No rows for this side.")
                            continue

                        side_freq_rows = side_rows[np.isclose(side_rows["freq_hz"].astype(float), float(selected_freq))]
                        if relation_mode == "ipsi_contra" and not (side_freq_rows["rel_ear"].fillna("ipsi") == "contra").any():
                            st.info("No contra rows for this side; viewer will show ipsi only.")

                        side_spacing_uv, side_amplitude_scale = view_controls(
                            key_prefix=f"{side}_view"
                        )

                        fig = toolbox.plot(
                            side_rows,
                            color_by="level_db",
                            title=f"{plot_title} | {side}",
                            frequency_hz=float(selected_freq),
                            relation_mode=relation_mode,
                            spacing_uv=float(side_spacing_uv),
                            amplitude_scale=float(side_amplitude_scale),
                            intensity_order="desc",
                        )
                        st.plotly_chart(fig, width="stretch", theme=None)


if __name__ == "__main__":
    main()

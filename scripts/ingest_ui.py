from __future__ import annotations

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import streamlit as st

from neuro_ingest.toolbox import NeuroAudioToolbox
from neuro_ingest.storage.parquet_store import ParquetStore
from neuro_ingest.ui.workflow import (
    combine_sessions,
    stage_uploaded_files,
)


def main() -> None:
    st.set_page_config(page_title="Neuro Ingest UI", layout="wide")
    st.title("Neuro-Audio Drag-and-Drop Ingest")
    st.caption("Upload one or more files, fill metadata, then ingest to Parquet + DuckDB.")

    left, right = st.columns(2)
    with left:
        system_choice = st.selectbox("System (required)", ["TDT", "IHS"], index=0)
        animal_id = st.text_input("Animal ID", value="")
        session_date = st.date_input("Session date", value=date.today())
        paradigm = st.text_input("Paradigm", value="abr")
        day_text = st.text_input("Day (optional)", value="")
        session_id = st.text_input("Session ID (optional)", value="")

    with right:
        parquet_dir = st.text_input("Parquet output dir", value="normalized")
        db_path = st.text_input("DuckDB path", value="normalized/neuro_audio.duckdb")
        overwrite = st.checkbox("Overwrite existing session", value=False)

    tdt_left_files = []
    tdt_right_files = []
    ihs_files = []
    if system_choice == "TDT":
        st.subheader("TDT Upload")
        st.caption("Drop left and right ear files separately. Each side is ingested in one batch.")
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
    else:
        st.subheader("IHS Upload")
        ihs_files = st.file_uploader(
            "IHS acquisition files",
            accept_multiple_files=True,
            type=["txt", "asc", "csv"],
            key="ihs_files",
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
                    base_session_id = session_id.strip() or f"{animal_id.strip()}_{session_date:%Y%m%d}"

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

    st.subheader("Viewer Data Source")
    source_mode = st.radio(
        "Choose rows for plotting",
        options=["Last ingested session", "Parquet file", "DuckDB filters (no SQL)", "DuckDB query"],
        horizontal=True,
        index=0,
    )
    default_parquet_path = st.session_state.get("last_parquet_path", "")
    default_db_path = st.session_state.get("last_db_path", db_path)
    query_sql = "SELECT * FROM samples ORDER BY session_date DESC, session_id DESC LIMIT 100000"

    with st.expander("Load Viewer Data", expanded=False):
        if source_mode == "Parquet file":
            parquet_path_input = st.text_input("Parquet path", value=default_parquet_path)
        elif source_mode == "DuckDB filters (no SQL)":
            db_filter_path = st.text_input("DuckDB path (filter mode)", value=default_db_path)
            f1, f2, f3 = st.columns(3)
            with f1:
                filter_animal_id = st.text_input("animal_id (optional)", value="")
            with f2:
                filter_session_id = st.text_input("session_id (optional)", value="")
            with f3:
                filter_day_text = st.text_input("day (optional)", value="")
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
                        value=100000,
                        step=1000,
                    )
                )
        elif source_mode == "DuckDB query":
            db_query_path = st.text_input("DuckDB path (viewer)", value=default_db_path)
            query_sql = st.text_area("SQL", value=query_sql, height=120)

        if st.button("Load data for viewer", key="load_viewer_rows"):
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
                        day_value = None
                        if filter_day_text.strip():
                            try:
                                day_value = int(filter_day_text.strip())
                            except ValueError:
                                st.error("day must be an integer.")
                                day_value = "invalid"

                        if day_value != "invalid":
                            filter_toolbox = NeuroAudioToolbox(
                                db_path=Path(db_filter_path.strip()),
                                parquet_dir=Path(parquet_dir),
                            )
                            loaded = filter_toolbox.get_samples(
                                animal_id=filter_animal_id.strip() or None,
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
                                if filter_animal_id.strip():
                                    title_bits.append(filter_animal_id.strip())
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

    st.subheader("DuckDB Editor")
    with st.expander("Edit existing DB traces", expanded=False):
        editor_db_path = st.text_input("DuckDB path (editor)", value=default_db_path, key="editor_db_path")
        create_backup = st.checkbox("Create backup before edit", value=True, key="editor_create_backup")
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
                    value=5000,
                    step=100,
                    key="editor_trace_limit",
                )
            )
            trace_df = editor_toolbox.list_trace_summaries(session_id=selected_session, limit=trace_limit)
            if trace_df.empty:
                st.warning("No traces found for selected session.")
            else:
                st.caption(f"Loaded {len(trace_df)} traces from session `{selected_session}`.")
                with st.expander("Trace summary preview", expanded=False):
                    st.dataframe(trace_df.head(500), width='stretch')

                label_to_trace: dict[str, str] = {}
                trace_labels: list[str] = []
                for row in trace_df.itertuples(index=False):
                    stim_ear = row.stim_ear if row.stim_ear is not None else "-"
                    rel_ear = row.rel_ear if row.rel_ear is not None else "-"
                    label = f"{row.trace_uid} | {float(row.freq_hz):g} Hz | {float(row.level_db):g} dB | {stim_ear}/{rel_ear}"
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

    if "viewer_rows" in st.session_state:
        rows = st.session_state["viewer_rows"]
        plot_title = st.session_state.get("viewer_title", "ABR Traces")

        with st.expander("Preview rows", expanded=False):
            st.dataframe(rows.head(300), width='stretch')

        st.subheader("ABR Viewer Controls")
        freq_values = sorted(float(v) for v in rows["freq_hz"].dropna().unique())
        if not freq_values:
            st.warning("No frequency values available for plotting.")
            return

        selected_freq = st.selectbox(
            "Frequency (Hz)",
            options=freq_values,
            format_func=lambda x: f"{x:g}",
        )
        relation_label = st.radio(
            "Relation mode",
            options=["ipsi only", "ipsi + contra"],
            index=0,
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

        def amplitude_scale_log_slider(*, label: str, key: str) -> float:
            log10_scale = st.slider(
                f"{label} (log10)",
                min_value=-1.0,
                max_value=1.0,
                value=0.0,
                step=0.01,
                key=key,
                help="Log-scaled amplitude multiplier from x0.1 to x10.",
            )
            scale_value = float(10 ** float(log10_scale))
            st.caption(f"{label}: x{scale_value:.2f}")
            return scale_value

        if len(side_values) == 1:
            spacing_uv = st.slider(
                "Trace spacing (uV)",
                min_value=0.0,
                max_value=float(max_spacing),
                value=max_spacing,
                step=float(step),
            )
            amplitude_scale = amplitude_scale_log_slider(
                label="Amplitude scale",
                key="global_amplitude_scale_log10",
            )

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
            st.plotly_chart(fig, width='stretch')
        else:
            st.subheader("Separated by Stim Ear")
            st.caption("Left and right plots have independent spacing and amplitude controls.")
            left_col, right_col = st.columns(2)
            for side, col in [("left", left_col), ("right", right_col)]:
                with col:
                    side_rows = rows[rows["stim_ear"].fillna("").astype(str).str.lower() == side]
                    st.markdown(f"**{side.title()}**")
                    if side_rows.empty:
                        st.info("No rows for this side.")
                        continue

                    side_freq_rows = side_rows[np.isclose(side_rows["freq_hz"].astype(float), float(selected_freq))]
                    if relation_mode == "ipsi_contra" and not (side_freq_rows["rel_ear"].fillna("ipsi") == "contra").any():
                        st.info("No contra rows for this side; viewer will show ipsi only.")

                    side_spacing_uv = st.slider(
                        f"{side.title()} trace spacing (uV)",
                        min_value=0.0,
                        max_value=float(max_spacing),
                        value=float(max_spacing),
                        step=float(step),
                        key=f"{side}_trace_spacing_uv",
                    )
                    side_amplitude_scale = amplitude_scale_log_slider(
                        label=f"{side.title()} amplitude scale",
                        key=f"{side}_amplitude_scale_log10",
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
                    st.plotly_chart(fig, width='stretch')


if __name__ == "__main__":
    main()

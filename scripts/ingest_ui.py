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
        options=["Last ingested session", "Parquet file", "DuckDB query"],
        horizontal=True,
        index=0,
    )
    default_parquet_path = st.session_state.get("last_parquet_path", "")
    default_db_path = st.session_state.get("last_db_path", db_path)
    query_sql = "SELECT * FROM samples ORDER BY session_date DESC, session_id DESC LIMIT 50000"

    with st.expander("Load Viewer Data", expanded=False):
        if source_mode == "Parquet file":
            parquet_path_input = st.text_input("Parquet path", value=default_parquet_path)
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

    if "viewer_rows" in st.session_state:
        rows = st.session_state["viewer_rows"]
        plot_title = st.session_state.get("viewer_title", "ABR Traces")

        with st.expander("Preview rows", expanded=False):
            st.dataframe(rows.head(300), use_container_width=True)

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
        spacing_uv = st.slider(
            "Trace spacing (uV)",
            min_value=0.0,
            max_value=float(max_spacing),
            value=0.0,
            step=float(step),
        )
        amplitude_scale = st.slider(
            "Amplitude scale (x)",
            min_value=1.0,
            max_value=10.0,
            value=1.0,
            step=0.1,
            help="Multiplies waveform amplitude for display only. Stored data remains unchanged.",
        )

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

        if len(side_values) == 1:
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
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.subheader("Separated by Stim Ear")
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

                    fig = toolbox.plot(
                        side_rows,
                        color_by="level_db",
                        title=f"{plot_title} | {side}",
                        frequency_hz=float(selected_freq),
                        relation_mode=relation_mode,
                        spacing_uv=float(spacing_uv),
                        amplitude_scale=float(amplitude_scale),
                        intensity_order="desc",
                    )
                    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()

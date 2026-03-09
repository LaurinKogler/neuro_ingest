from __future__ import annotations

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd
import streamlit as st

from neuro_ingest.toolbox import NeuroAudioToolbox
from neuro_ingest.ui.workflow import (
    ingest_and_save,
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
            writes = []

            with TemporaryDirectory(prefix="neuro_ingest_ui_") as tmpdir:
                if system_choice == "TDT":
                    base_session_id = session_id.strip() or f"{animal_id.strip()}_{session_date:%Y%m%d}"

                    if tdt_left_files:
                        left_dir = Path(tmpdir) / "left"
                        stage_uploaded_files(tdt_left_files, left_dir)
                        left_session, left_write = ingest_and_save(
                            toolbox=toolbox,
                            system="TDT",
                            input_dir=left_dir,
                            animal_id=animal_id.strip(),
                            session_date=session_date,
                            paradigm=paradigm.strip() or "abr",
                            day=day,
                            session_id=f"{base_session_id}_L",
                            overwrite=overwrite,
                            tdt_ear="left",
                        )
                        sessions.append(left_session)
                        writes.append(left_write)

                    if tdt_right_files:
                        right_dir = Path(tmpdir) / "right"
                        stage_uploaded_files(tdt_right_files, right_dir)
                        right_session, right_write = ingest_and_save(
                            toolbox=toolbox,
                            system="TDT",
                            input_dir=right_dir,
                            animal_id=animal_id.strip(),
                            session_date=session_date,
                            paradigm=paradigm.strip() or "abr",
                            day=day,
                            session_id=f"{base_session_id}_R",
                            overwrite=overwrite,
                            tdt_ear="right",
                        )
                        sessions.append(right_session)
                        writes.append(right_write)
                else:
                    ihs_dir = Path(tmpdir) / "ihs"
                    stage_uploaded_files(ihs_files, ihs_dir)
                    ihs_session, ihs_write = ingest_and_save(
                        toolbox=toolbox,
                        system="IHS",
                        input_dir=ihs_dir,
                        animal_id=animal_id.strip(),
                        session_date=session_date,
                        paradigm=paradigm.strip() or "abr",
                        day=day,
                        session_id=session_id.strip() or None,
                        overwrite=overwrite,
                        tdt_ear=None,
                    )
                    sessions.append(ihs_session)
                    writes.append(ihs_write)

            merged_rows = pd.concat([s.rows for s in sessions], ignore_index=True)
            merged_session_ids = ", ".join(s.session_id for s in sessions)
            st.session_state["last_session_rows"] = merged_rows
            st.session_state["last_session_id"] = merged_session_ids
            st.session_state["last_session_title"] = f"{merged_session_ids} ABR"

            st.success("Ingest completed.")
            m1, m2, m3 = st.columns(3)
            m1.metric("System", system_choice)
            m2.metric("Sessions Written", len(sessions))
            m3.metric("Rows Written", int(sum(w.rows_written for w in writes)))
            for idx, write in enumerate(writes, start=1):
                st.write(f"Write {idx} Parquet: `{write.parquet_path}`")
            if writes:
                st.write(f"DuckDB: `{writes[0].db_path}`")
        except Exception as exc:
            st.error(f"Ingest failed: {exc}")
            st.exception(exc)

    if "last_session_rows" in st.session_state:
        rows = st.session_state["last_session_rows"]
        plot_title = st.session_state.get("last_session_title", "ABR Traces")

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

        freq_rows = rows[np.isclose(rows["freq_hz"].astype(float), float(selected_freq))]
        if relation_mode == "ipsi_contra" and not (freq_rows["rel_ear"].fillna("ipsi") == "contra").any():
            st.info("No contra rows for this frequency; viewer will show ipsi only.")

        toolbox = NeuroAudioToolbox(
            db_path=Path(db_path),
            parquet_dir=Path(parquet_dir),
        )
        fig = toolbox.plot(
            rows,
            color_by="level_db",
            title=plot_title,
            frequency_hz=float(selected_freq),
            relation_mode=relation_mode,
            spacing_uv=float(spacing_uv),
            intensity_order="desc",
        )
        st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()

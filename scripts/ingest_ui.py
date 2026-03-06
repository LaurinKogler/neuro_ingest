from __future__ import annotations

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import streamlit as st

from neuro_ingest.toolbox import NeuroAudioToolbox
from neuro_ingest.ui.workflow import (
    infer_tdt_ear_from_upload_names,
    ingest_and_save,
    resolve_system,
    stage_uploaded_files,
)


def main() -> None:
    st.set_page_config(page_title="Neuro Ingest UI", layout="wide")
    st.title("Neuro-Audio Drag-and-Drop Ingest")
    st.caption("Upload one or more files, fill metadata, then ingest to Parquet + DuckDB.")

    uploaded_files = st.file_uploader(
        "Drag and drop acquisition files",
        accept_multiple_files=True,
        type=["txt", "asc", "csv"],
    )
    inferred_tdt_ear = infer_tdt_ear_from_upload_names(uploaded_files) if uploaded_files else None

    left, right = st.columns(2)
    with left:
        system_choice = st.selectbox("System", ["Auto", "TDT", "IHS"], index=0)
        animal_id = st.text_input("Animal ID", value="")
        session_date = st.date_input("Session date", value=date.today())
        paradigm = st.text_input("Paradigm", value="abr")
        day_text = st.text_input("Day (optional)", value="")
        session_id = st.text_input("Session ID (optional)", value="")

    with right:
        parquet_dir = st.text_input("Parquet output dir", value="normalized")
        db_path = st.text_input("DuckDB path", value="normalized/neuro_audio.duckdb")
        overwrite = st.checkbox("Overwrite existing session", value=False)

    with st.expander("TDT ear metadata (required for TDT)", expanded=True):
        if inferred_tdt_ear is None:
            st.info("Filename inference: no unambiguous TDT ear found.")
            default_idx = 0
        else:
            st.success(f"Filename inference suggests TDT ear: {inferred_tdt_ear}")
            default_idx = 1 if inferred_tdt_ear == "right" else 0

        tdt_ear = st.radio(
            "Confirm TDT ear side",
            options=["left", "right"],
            index=default_idx,
            horizontal=True,
        )
        confirm_tdt_ear = st.checkbox(
            "I confirm this TDT ear selection is correct",
            value=False,
        )

    if st.button("Ingest", type="primary"):
        if not uploaded_files:
            st.error("Upload at least one file.")
            return
        if not animal_id.strip():
            st.error("Animal ID is required.")
            return

        day = None
        if day_text.strip():
            try:
                day = int(day_text.strip())
            except ValueError:
                st.error("Day must be an integer if provided.")
                return

        try:
            with TemporaryDirectory(prefix="neuro_ingest_ui_") as tmpdir:
                staged_paths = stage_uploaded_files(uploaded_files, tmpdir)
                system = resolve_system(system_choice, staged_paths)
                selected_tdt_ear = tdt_ear if system == "TDT" else None

                if system == "TDT" and not confirm_tdt_ear:
                    st.error("TDT ingest requires explicit ear confirmation before saving.")
                    return

                toolbox = NeuroAudioToolbox(
                    db_path=Path(db_path),
                    parquet_dir=Path(parquet_dir),
                )

                session, result = ingest_and_save(
                    toolbox=toolbox,
                    system=system,
                    input_dir=Path(tmpdir),
                    animal_id=animal_id.strip(),
                    session_date=session_date,
                    paradigm=paradigm.strip() or "abr",
                    day=day,
                    session_id=session_id.strip() or None,
                    overwrite=overwrite,
                    tdt_ear=selected_tdt_ear,
                )

            st.session_state["last_session_rows"] = session.rows
            st.session_state["last_session_id"] = session.session_id
            st.session_state["last_session_title"] = f"{session.session_id} ABR"

            st.success("Ingest completed.")
            m1, m2, m3 = st.columns(3)
            m1.metric("System", session.system)
            m2.metric("Session ID", session.session_id)
            m3.metric("Rows Written", int(result.rows_written))
            st.write(f"Parquet: `{result.parquet_path}`")
            st.write(f"DuckDB: `{result.db_path}`")
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

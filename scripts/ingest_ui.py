from __future__ import annotations

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

import streamlit as st

from neuro_ingest.toolbox import NeuroAudioToolbox
from neuro_ingest.ui.workflow import ingest_and_save, resolve_system, stage_uploaded_files


def main() -> None:
    st.set_page_config(page_title="Neuro Ingest UI", layout="wide")
    st.title("Neuro-Audio Drag-and-Drop Ingest")
    st.caption("Upload one or more files, fill metadata, then ingest to Parquet + DuckDB.")

    uploaded_files = st.file_uploader(
        "Drag and drop acquisition files",
        accept_multiple_files=True,
        type=["txt", "asc", "csv"],
    )

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
                )

            st.success("Ingest completed.")
            m1, m2, m3 = st.columns(3)
            m1.metric("System", session.system)
            m2.metric("Session ID", session.session_id)
            m3.metric("Rows Written", int(result.rows_written))
            st.write(f"Parquet: `{result.parquet_path}`")
            st.write(f"DuckDB: `{result.db_path}`")

            with st.expander("Preview rows", expanded=True):
                st.dataframe(session.rows.head(300), use_container_width=True)

            fig = toolbox.plot(session.rows, color_by="level_db", title=f"{session.session_id} ABR")
            st.plotly_chart(fig, use_container_width=True)
        except Exception as exc:
            st.error(f"Ingest failed: {exc}")
            st.exception(exc)


if __name__ == "__main__":
    main()

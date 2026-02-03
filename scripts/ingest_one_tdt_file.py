from pathlib import Path
from datetime import date

from neuro_ingest.ingest.tdt import TDTIngestor
from neuro_ingest.io import save_session_parquet


def main():
    # 1) change this to your real file
    path = Path(r"E:\data_noise\AC04\AC04_d0_20251017\AC04_ClickABR_left_20251017.txt")

    # 2) output folder (create if missing)
    out_dir = Path(r"E:\data_noise\normalized")

    # 3) session metadata
    animal_id = "AC04"
    session_date_ = date(2025, 10, 17)
    session_id = f"{animal_id}_{session_date_:%Y%m%d}"

    ing = TDTIngestor()

    df = ing.ingest(
        paths=[path],
        animal_id=animal_id,
        session_date=session_date_,
        paradigm="abr",
        day=0,
        session_id=session_id,
    )

    print("Rows:", len(df))
    print("Unique file_uid / trace_uid / sample_uid:")
    print(df[["file_uid", "trace_uid", "sample_uid"]].nunique())

    out_path = save_session_parquet(
        df,
        out_dir=out_dir,
        system=ing.system,
        session_id=session_id,
        overwrite=True,
    )

    print("Saved:", out_path)


if __name__ == "__main__":
    main()

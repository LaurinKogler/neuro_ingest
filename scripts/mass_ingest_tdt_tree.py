from __future__ import annotations

import argparse
from pathlib import Path

from neuro_ingest.batch import discover_tdt_tree, ingest_tdt_tree
from neuro_ingest.toolbox import NeuroAudioToolbox


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover or ingest a TDT ABR folder tree.")
    parser.add_argument("root", type=Path, help="Root folder containing animal/session folders.")
    parser.add_argument("--db-path", type=Path, default=Path("normalized/neuro_audio.duckdb"))
    parser.add_argument("--parquet-dir", type=Path, default=Path("normalized"))
    parser.add_argument("--overwrite", action="store_true", help="Alias for --on-existing overwrite.")
    parser.add_argument(
        "--on-existing",
        choices=["fail", "skip", "overwrite"],
        default="fail",
        help="What to do when a session_id already exists in the target DuckDB.",
    )
    parser.add_argument("--write", action="store_true", help="Write to Parquet and DuckDB. Omit for dry run.")
    parser.add_argument("--stop-on-error", action="store_true")
    parser.add_argument("--report", type=Path, help="Optional CSV report path.")
    args = parser.parse_args()

    if not args.write:
        discovery = discover_tdt_tree(args.root)
        report = discovery.to_dataframe()
        print(report.to_string(index=False))
        print(f"\nSessions: {len(discovery.sessions)}")
        print(f"Rejected files: {len(discovery.rejected_files)}")
        if discovery.rejected_files:
            print("\nRejected:")
            for item in discovery.rejected_files[:50]:
                print(f"- {item.path}: {item.reason}")
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            report.to_csv(args.report, index=False)
        return

    toolbox = NeuroAudioToolbox(db_path=args.db_path, parquet_dir=args.parquet_dir)
    result = ingest_tdt_tree(
        root=args.root,
        toolbox=toolbox,
        on_existing="overwrite" if args.overwrite else args.on_existing,
        dry_run=False,
        stop_on_error=args.stop_on_error,
    )
    report = result.to_dataframe()
    print(report.to_string(index=False))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        report.to_csv(args.report, index=False)


if __name__ == "__main__":
    main()

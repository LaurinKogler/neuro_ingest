from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Optional


from neuro_ingest.ingest.base import BaseIngestor


class TDTIngestor(BaseIngestor):
    system = "TDT"

    def parse_file(self, path: Path) -> List[Dict]:
        rows: List[Dict] = []

        record_no: Optional[int] = None
        duration_ms: Optional[float] = None
        n_points: Optional[int] = None
        level_db: Optional[float] = None
        in_variables = False
        in_waveform = False
        wf: List[float] = []

        def flush_record():
            nonlocal rows, record_no, duration_ms, n_points, level_db, wf
            if record_no is None or duration_ms is None or n_points is None or level_db is None:
                return
            if len(wf) != n_points:
                raise ValueError(f"Record {record_no} expected {n_points} points but got {len(wf)}")

            dt = duration_ms / n_points
            for i, v in enumerate(wf):
                rows.append(
                    {
                        "freq_hz": 0.0,
                        "level_db": float(level_db),
                        "trace_id": str(record_no),
                        "sample_idx": int(i),
                        "time_ms": float(i * dt),
                        "amplitude_uv": float(v * 1e6),
                    }
                )

            record_no = None
            duration_ms = None
            n_points = None
            level_db = None
            wf = []

        with path.open("r", encoding="utf-8", errors="ignore") as f:
            for raw in f:
                line = raw.strip()

                if line.startswith("Record Number:"):
                    flush_record()
                    record_no = int(line.split(":", 1)[1].strip())
                    in_variables = False
                    in_waveform = False
                    wf = []
                    continue

                if record_no is None:
                    continue

                if line.startswith("Aqu. Duration:"):
                    duration_ms = float(line.split(":", 1)[1].replace("ms", "").strip())
                    continue

                if line.startswith("No. Points:"):
                    n_points = int(line.split(":", 1)[1].strip())
                    continue

                if line.startswith("Variables:"):
                    in_variables = True
                    continue

                if in_variables and "Level =" in line and "dB" in line:
                    part = line.split("Level =", 1)[1].strip()
                    level_db = float(part.split("dB", 1)[0].strip())
                    continue

                try:
                    v = float(line)
                    wf.append(v)
                    in_waveform = True
                    in_variables = False
                    continue
                except ValueError:
                    pass


        flush_record()
        return rows

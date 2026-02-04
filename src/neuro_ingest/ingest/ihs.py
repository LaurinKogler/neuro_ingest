from pathlib import Path
from neuro_ingest.ingest.base import BaseIngestor


class IHSIngestor(BaseIngestor):
    system = "IHS"

    def can_parse(self, path: Path) -> bool:
        if not path.suffix.lower() in {".txt", ".csv"}:
            return False

        try:
            with path.open("r", errors="ignore") as f:
                header = f.read(2000)
                return "Intensity" in header and "Stim" in header
        except Exception:
            return False

    def parse_file(self, path: Path) -> list[dict]:
        rows = []

        with path.open("r", encoding="utf-8", errors="ignore") as f:
            lines = [ln.strip() for ln in f if ln.strip()]

        # --- 1) Header parsen ---
        intensities = []
        stim_freqs = []
        channels = []
        smp_period_us = None
        stim_ear = None

        data_start = None

        for i, ln in enumerate(lines):
            if ln.startswith("Intensity"):
                intensities = [float(x) for x in ln.split(",")[1:] if x]
            elif ln.startswith("Stim. Freq"):
                stim_freqs = []
                for x in ln.split(",")[1:]:
                    x = x.strip()
                    if not x:
                        continue
                    stim_freqs.append(float(x))
            elif ln.startswith("Channel"):
                channels = ln.split(",")[1:]
            elif ln.startswith("Smp. Period"):
                smp_period_us = float(ln.split(",")[1])
            elif ln.startswith("Ear"):
                stim_ear = ln.split(",")[1].lower()
            elif ln.startswith("Data Pnt"):
                data_start = i + 1
                break

        if data_start is None:
            raise ValueError("Could not find data block in IHS file")

        if smp_period_us is None:
            raise ValueError("Missing sampling period")

        # --- 2) Trace-Metadaten vorbereiten ---
        n_traces = len(intensities)

        trace_meta = []
        for idx in range(n_traces):
            ch = channels[idx].strip().upper()
            rec_ear = "right" if ch == "A" else "left"

            trace_meta.append({
                "source_record_id": f"{idx}",
                "level_db": intensities[idx],
                "freq_hz": stim_freqs[idx] if stim_freqs else 0.0,
                "stim_ear": stim_ear,
                "rec_ear": rec_ear,
            })

        # --- 3) Datenblock parsen ---
        for ln in lines[data_start:]:
            parts = ln.split(",")

            sample_idx = int(parts[0]) - 1
            time_ms = sample_idx * smp_period_us / 1000.0

            values = parts[1::6]  # Average(uV) liegt hier

            for i, val in enumerate(values):
                if not val:
                    continue

                meta = trace_meta[i]

                rows.append({
                    "source_record_id": meta["source_record_id"],
                    "freq_hz": meta["freq_hz"],
                    "level_db": meta["level_db"],
                    "stim_ear": meta["stim_ear"],
                    "rec_ear": meta["rec_ear"],
                    "sample_idx": sample_idx,
                    "time_ms": time_ms,
                    "amplitude_uv": float(val),
                })

        return rows

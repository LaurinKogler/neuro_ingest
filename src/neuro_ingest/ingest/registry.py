from pathlib import Path
from neuro_ingest.ingest.tdt import TDTIngestor
from neuro_ingest.ingest.ihs import IHSIngestor


INGESTORS = [
    TDTIngestor(),
    IHSIngestor(),
]


def detect_ingestor(path: Path):
    for ing in INGESTORS:
        if ing.can_parse(path):
            return ing
    raise ValueError(f"Unsupported file format: {path}")

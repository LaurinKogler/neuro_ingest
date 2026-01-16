from pathlib import Path
import pandas as pd

from neuro_ingest.ingest.base import BaseIngestor


class TDTIngestor(BaseIngestor):
    system = "TDT"

    def parse_file(self, path: Path) -> list[dict]:
        raise NotImplementedError

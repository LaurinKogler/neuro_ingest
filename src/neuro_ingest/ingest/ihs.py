from pathlib import Path
from neuro_ingest.ingest.base import BaseIngestor

class IHSIngestor(BaseIngestor):
    system = "IHS"

    def parse_file(self, path: Path) -> list[dict]:
        raise NotImplementedError

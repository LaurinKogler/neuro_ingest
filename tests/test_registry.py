from pathlib import Path
from neuro_ingest.ingest.registry import detect_ingestor
from neuro_ingest.ingest.tdt import TDTIngestor
from neuro_ingest.ingest.ihs import IHSIngestor


def test_detects_tdt_ascii():
    path = Path("tests/data/AC04_ClickABR_right_20251017.txt")
    ing = detect_ingestor(path)
    assert isinstance(ing, TDTIngestor)


def test_detects_ihs_ascii():
    path = Path("tests/data/X48_d0_Click.TXT")
    ing = detect_ingestor(path)
    assert isinstance(ing, IHSIngestor)
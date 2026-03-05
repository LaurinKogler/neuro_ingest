# neuro_ingest

`neuro_ingest` is now a modular neuro-audio toolbox for:
- ingestion and normalization of vendor exports
- local persistence (Parquet + DuckDB)
- interactive ABR plotting in Jupyter

Full guide: [docs/USER_GUIDE.md](docs/USER_GUIDE.md)

## Module Map

- `neuro_ingest.ingest`: vendor parsers + ingestion orchestration
- `neuro_ingest.data`: typed in-memory session model (`SessionData`)
- `neuro_ingest.storage`: Parquet and DuckDB stores + storage service
- `neuro_ingest.plot`: interactive ABR plotting service
- `neuro_ingest.toolbox`: single facade for notebook workflows

## Quick Workflow

```python
from datetime import date
from neuro_ingest.toolbox import NeuroAudioToolbox

toolbox = NeuroAudioToolbox(
    db_path="normalized/neuro_audio.duckdb",
    parquet_dir="normalized",
)

session = toolbox.ingest(
    system="TDT",
    input_path="raw/TDT/session_001",
    animal_id="AC04",
    session_date=date(2025, 10, 17),
)
toolbox.save(session, overwrite=False)

df = toolbox.query("SELECT * FROM samples WHERE animal_id = ?", ["AC04"])
fig = toolbox.plot(df, color_by="level_db")
fig.show()
```

## Backward Compatibility

The lab-facing function `neuro_ingest.lab.ingest_session(...)` is still available.
It now delegates to the new services and writes both Parquet and DuckDB outputs.

## Test Runner

Use the project script:

```powershell
scripts/run_tests.ps1
```

If Conda is not on PATH, set:

```powershell
$env:NEURO_INGEST_CONDA_EXE = "C:\path\to\conda.exe"
```

Or bypass Conda discovery entirely:

```powershell
$env:NEURO_INGEST_ENV_PREFIX = "C:\Users\Admin\miniconda3\envs\neuro-ingest"
# or
$env:NEURO_INGEST_PYTHON_EXE = "C:\Users\Admin\miniconda3\envs\neuro-ingest\python.exe"
```

Or pass custom pytest arguments:

```powershell
scripts/run_tests.ps1 tests/test_lab_api.py -q
```

## Environment

```bash
conda env create -f environment.yml
conda activate neuro-ingest
```

If your existing environment already has NumPy 2.x and crashes on import on Windows, run:

```powershell
conda install -n neuro-ingest "numpy<2"
```

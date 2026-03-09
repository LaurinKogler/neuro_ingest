# neuro_ingest User Guide

This guide explains how to use the current `0.2.x` toolbox end-to-end.

## 1. What This Toolbox Does

`neuro_ingest` provides a local workflow for neuro-audio data:
- ingest vendor files (`TDT`, `IHS`) into a canonical sample table
- save to both Parquet and DuckDB
- query across sessions via SQL
- plot ABR traces interactively in Jupyter

Main modules:
- `neuro_ingest.ingest`
- `neuro_ingest.data`
- `neuro_ingest.storage`
- `neuro_ingest.plot`
- `neuro_ingest.toolbox`

## 2. Environment Setup

```bash
conda env create -f environment.yml
conda activate neuro-ingest
```

If you have a Windows NumPy import crash with NumPy 2.x:

```powershell
conda install -n neuro-ingest "numpy<2"
```

## 3. Main Entry Point

Use `NeuroAudioToolbox` for the full workflow:

```python
from datetime import date
from neuro_ingest.toolbox import NeuroAudioToolbox

toolbox = NeuroAudioToolbox(
    db_path="normalized/neuro_audio.duckdb",
    parquet_dir="normalized",
)
```

Constructor parameters:
- `db_path`: path to local DuckDB file (`.duckdb`)
- `parquet_dir`: folder for per-session Parquet outputs

## 4. Ingest Data

```python
session = toolbox.ingest(
    system="TDT",                    # "TDT" or "IHS"
    input_path="raw/TDT/session_001",# file or folder
    animal_id="AC04",
    session_date=date(2025, 10, 17),
    paradigm="abr",                  # default
    day=0,                           # optional
    session_id=None,                 # optional; auto: AC04_20251017
    pattern="*",                     # optional glob used for folder scan
)
```

Output:
- `SessionData` object with:
  - `session_id`
  - `system`
  - `animal_id`
  - `session_date`
  - `paradigm`
  - `rows` (`pandas.DataFrame`)

Common ingest errors:
- `ValueError: Unsupported system`
- `FileNotFoundError: No <SYSTEM>-compatible files...`
- parser/schema validation errors from ingestors

## 5. Save Data (Dual Write)

```python
result = toolbox.save(session, overwrite=False)
print(result.parquet_path)
print(result.db_path)
print(result.rows_written)
```

`save(...)` always writes:
- Parquet file: one file per `session_id x system`
- DuckDB rows into:
  - `samples` table (canonical rows)
  - `sessions` table (session index metadata)

Overwrite behavior:
- `overwrite=False` raises if target session already exists
- `overwrite=True` replaces existing session in DB and Parquet

## 6. Query Data

Query all canonical rows for one animal:

```python
df = toolbox.query(
    "SELECT * FROM samples WHERE animal_id = ?",
    ["AC04"],
)
```

Query specific sessions:

```python
sessions = toolbox.list_sessions(
    animal_id="AC04",
    system="TDT",
    paradigm="abr",
)
```

`list_sessions(...)` returns a DataFrame with:
- `session_id`
- `system`
- `animal_id`
- `session_date`
- `paradigm`
- `row_count`
- `created_at`

## 7. Plot ABR Traces

Plot from a query result:

```python
fig = toolbox.plot(
    df,
    frequency_hz=0.0,        # mandatory if >1 frequency present
    relation_mode="ipsi",    # "ipsi" or "ipsi_contra"
    spacing_uv=0.0,          # vertical offset in uV between intensity groups
    intensity_order="desc",  # "desc" or "asc"
    color_by="level_db",     # default; also e.g. "freq_hz"
    group_by="trace_uid",    # default trace grouping
    filters={"system": "TDT"},
    title="AC04 ABR",
)
fig.show()
```

Plot behavior:
- interactive Plotly figure
- one-frequency-at-a-time view
- ipsi-only default mode
- optional ipsi/contra side-by-side layout (ipsi left, contra right)
- fixed X-axis (time) to prioritize Y-axis amplitude zoom
- Y-axis remains zoomable
- configurable vertical spacing per intensity
- legend toggles for trace visibility
- color mapping by selected column

Supported `filters`:
- any existing DataFrame column, for example:
  - `animal_id`
  - `session_id`
  - `system`
  - `freq_hz`
  - `level_db`
  - `stim_ear`
  - `rec_ear`

Filter values can be:
- single value (`{"system": "TDT"}`)
- list/set/tuple (`{"level_db": [70, 80, 90]}`)

## 8. Full Example (Notebook Style)

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

subset = toolbox.query(
    "SELECT * FROM samples WHERE session_id = ? AND level_db >= ?",
    [session.session_id, 70],
)

fig = toolbox.plot(subset, frequency_hz=0.0, relation_mode="ipsi", color_by="level_db")
fig.show()
```

## 9. Backward-Compatible API

If you still use the old one-call API:

```python
from datetime import date
from neuro_ingest.lab import ingest_session

df, parquet_path = ingest_session(
    system="TDT",
    input_path="raw/TDT/session_001",
    out_dir="normalized",
    animal_id="AC04",
    session_date=date(2025, 10, 17),
    overwrite=False,
)
```

Notes:
- this now delegates internally to new services
- it also writes DuckDB (default DB path: `<out_dir>/neuro_audio.duckdb`)

## 10. Running Tests

Preferred:

```powershell
scripts/run_tests.ps1
```

Single file:

```powershell
scripts/run_tests.ps1 tests/test_lab_api.py -q
```

If discovery fails on your machine, set one of:

```powershell
$env:NEURO_INGEST_PYTHON_EXE = "C:\Users\Admin\miniconda3\envs\neuro-ingest\python.exe"
$env:NEURO_INGEST_ENV_PREFIX = "C:\Users\Admin\miniconda3\envs\neuro-ingest"
$env:NEURO_INGEST_CONDA_EXE = "C:\Users\Admin\miniconda3\Scripts\conda.exe"
```

## 11. Drag-and-Drop Ingest UI

You can ingest files without writing code via Streamlit UI.

Start it:

```powershell
scripts/run_ingest_ui.ps1
```

The launcher sets safer defaults:
- `--server.address localhost` (local-only binding)
- `--browser.gatherUsageStats false` (no Streamlit telemetry)

Workflow:
- choose `System` (`TDT` or `IHS`) explicitly
- if `TDT`: upload left files and right files in separate drop zones
- if `IHS`: upload files in the IHS drop zone
- fill required metadata (`Animal ID`, `Session date`)
- optionally set `Day`, `Session ID`, and overwrite mode
- set output paths (`Parquet output dir`, `DuckDB path`)
- click **Ingest**

After ingest, the UI shows:
- status + write locations
- row preview
- ABR viewer controls:
  - frequency dropdown (single frequency selection)
  - relation mode (`ipsi only` or `ipsi + contra`)
  - spacing slider (`uV`)
  - separate left/right plots automatically when both stim sides are present

## 12. Current Scope (0.2.x)

Included:
- ingest/normalize
- dual persistence (Parquet + DuckDB)
- SQL querying
- ABR plotting in Jupyter

Not included yet:
- peak/annotation workflows
- feature extraction pipeline
- remote/multi-user database backends

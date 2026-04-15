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

For a completely blank Windows PC, use standard Python plus a local virtual environment.
You do not need Anaconda.

Assumptions:
- Windows 10 or Windows 11
- internet access
- a web browser
- PowerShell

Step 1. Install Python 3.11.
- open `https://www.python.org/downloads/windows/`
- download Python 3.11 x64
- run the installer
- enable `Add python.exe to PATH`
- finish installation

Step 2. Confirm Python is installed.
Open PowerShell and run:

```powershell
py --version
```

Expected result:
- Python 3.11.x

Step 3. Decide how to get this repository onto the PC.

Option A: install Git and clone the repo.

Step 3A-1. Install Git for Windows.
- open `https://git-scm.com/download/win`
- download the installer
- run it with default options

Step 3A-2. Confirm Git works:

```powershell
git --version
```

Step 3A-3. Clone the repository:

```powershell
git clone https://github.com/LaurinKogler/neuro_ingest.git
cd neuro_ingest
```

Option B: do not install Git, download the repository ZIP.

Step 3B-1. Open:
- `https://github.com/LaurinKogler/neuro_ingest`

Step 3B-2. Download:
- click `Code`
- click `Download ZIP`

Step 3B-3. Extract the ZIP to a folder you can access easily.

Step 3B-4. Open PowerShell in the extracted `neuro_ingest` folder.

Step 4. Create a virtual environment inside the repository:

```powershell
py -3.11 -m venv .venv
```

Step 5. Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

If activation is blocked in PowerShell, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then run the activation command again.

Step 6. Upgrade `pip`:

```powershell
python -m pip install --upgrade pip
```

Step 7. Install this project:

```powershell
pip install .
```

What Step 7 does:
- installs `neuro_ingest` from the repository folder on your PC
- downloads dependencies from PyPI using `pip`

Step 8. Start the local UI:

```powershell
scripts/run_ingest_ui.ps1
```

For a simpler repeat-use launch, you can also double-click:

```text
start_neuro_ingest_ui.bat
```

Step 9. Open the local URL shown in the terminal.
Usually:
- `http://localhost:8501`

Alternative to Step 8:

```powershell
python -m streamlit run scripts/ingest_ui.py --browser.gatherUsageStats false --server.address localhost
```

After first-time setup, the easiest repeat-use path is usually:
- double-click `start_neuro_ingest_ui.bat`
- leave the PowerShell window open while the UI is running
- press `Ctrl+C` in that window to stop it

Summary of what must be installed:
- Python 3.11
- Git for Windows, only if you want to use `git clone`

Not required:
- Anaconda
- Miniconda
- VS Code
- Visual Studio

Recommended folder layout:

```text
C:\Users\YourName\Projects\neuro_ingest
C:\Users\YourName\Projects\neuro_ingest\.venv
C:\Users\YourName\NeuroIngestData\normalized
C:\Users\YourName\NeuroIngestData\neuro_audio.duckdb
```

What goes where:
- the repo folder contains the source code
- `.venv` contains the Python environment for this project
- `normalized` stores output Parquet files
- `neuro_audio.duckdb` stores the local DuckDB database

How to decide install locations:
- `git clone ...` puts the repo in the folder you are currently in
- `py -3.11 -m venv .venv` creates the environment in the current repo folder
- `pip install .` installs into the active virtual environment

Example:

```powershell
mkdir C:\Users\YourName\Projects
cd C:\Users\YourName\Projects
git clone https://github.com/LaurinKogler/neuro_ingest.git
cd neuro_ingest
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install .
```

If you prefer Conda, this still works too:

```bash
conda env create -f environment.yml
conda activate neuro-ingest
```

If you have a Windows NumPy import crash with NumPy 2.x:

```powershell
pip install "numpy<2"
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

No-SQL alternative for common filters:

```python
df = toolbox.get_samples(
    animal_id="AC04",
    session_id="AC04_20251017",
    day=1,
    system="TDT",
    paradigm="abr",
    limit=50000,
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

The launcher now works with:
- an active virtualenv
- a repo-local `.venv`
- `NEURO_INGEST_PYTHON_EXE`
- `NEURO_INGEST_ENV_PREFIX`
- existing Conda env discovery

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
- viewer data source modes:
  - last ingested session
  - parquet file path
  - DuckDB filter mode (`animal_id`, `session_id`, `day`, `system`, `paradigm`)
  - DuckDB SQL query
- DuckDB editor mode:
  - load session trace summary
  - select traces
  - apply ear metadata edits
  - delete selected traces (confirmation required)
  - optional DB backup before changes
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

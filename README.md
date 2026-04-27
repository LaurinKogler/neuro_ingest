# neuro_ingest

`neuro_ingest` is now a modular neuro-audio toolbox for:
- ingestion and normalization of vendor exports
- local persistence (Parquet + DuckDB)
- interactive ABR plotting in Jupyter
- drag-and-drop ingestion UI for local use

Full guide: [docs/USER_GUIDE.md](docs/USER_GUIDE.md)

## Module Map

- `neuro_ingest.ingest`: vendor parsers + ingestion orchestration
- `neuro_ingest.data`: typed in-memory session model (`SessionData`)
- `neuro_ingest.storage`: Parquet and DuckDB stores + storage service
- `neuro_ingest.plot`: interactive ABR plotting service
- `neuro_ingest.toolbox`: single facade for notebook workflows
- `scripts/ingest_ui.py`: Streamlit drag-and-drop ingest app

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
fig = toolbox.plot(
    df,
    frequency_hz=0.0,         # required if dataset contains >1 frequency
    relation_mode="ipsi",     # or "ipsi_contra"
    spacing_uv=0.0,           # vertical trace spacing in uV
    color_by="level_db",
)
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

## Drag-and-Drop UI

Start the local ingest UI:

```powershell
scripts/run_ingest_ui.ps1
```

Then open the local Streamlit URL shown in the terminal, drag files in, fill metadata, and press **Ingest**.
System is explicit in UI (`TDT` or `IHS`); no system auto-detection is used.
For TDT uploads, use separate left/right upload fields; each side is ingested as its own batch.
Machine-specific UI defaults live in `scripts/ingest_ui.local.toml`.
Use `scripts/ingest_ui.local.example.toml` as the template; the `.local.toml` file is git-ignored so local paths and naming defaults are not overwritten by pulls.
After ingest, use ABR viewer controls for:
- viewer data source selection:
  - last ingested session
  - parquet file path
  - DuckDB filters (no SQL): `animal_id`, `session_id`, `day`, `system`, `paradigm`
  - DuckDB SQL query
- DuckDB editor:
  - select session and traces
  - edit ear metadata (`stim_ear`, `rec_ear`, `rel_ear`)
  - delete selected traces
  - optional backup before edit
- single-frequency selection
- ipsi only vs ipsi+contra layout
- vertical spacing slider (uV)
- automatic side separation when both left/right stim ears are present

Security defaults in this launcher:
- binds to `localhost` only
- disables Streamlit usage telemetry (`browser.gatherUsageStats=false`)

## Environment

For a completely blank Windows PC, use standard Python plus a local virtual environment.
You do not need Anaconda.

Assumptions:
- the PC is running Windows 10 or Windows 11
- the PC has internet access
- you can open a web browser and PowerShell

### Blank-PC Setup

Step 1. Install Python 3.11.
- open `https://www.python.org/downloads/windows/`
- download Python 3.11 x64
- run the installer
- enable `Add python.exe to PATH`
- finish the install

Step 2. Confirm Python works.
Open PowerShell and run:

```powershell
py --version
```

You should see Python 3.11.x.

Step 3. Decide how you want to get this repository onto the PC.

Option A: install Git, then clone the repo.

Step 3A-1. Install Git for Windows.
- open `https://git-scm.com/download/win`
- download and run the installer
- the default install options are fine

Step 3A-2. Confirm Git works.

```powershell
git --version
```

Step 3A-3. Clone the repo and enter it.

```powershell
git clone https://github.com/LaurinKogler/neuro_ingest.git
cd neuro_ingest
```

Option B: do not install Git, use a ZIP instead.

Step 3B-1. Open:
- `https://github.com/LaurinKogler/neuro_ingest`

Step 3B-2. Download the ZIP.
- click `Code`
- click `Download ZIP`

Step 3B-3. Extract the ZIP somewhere convenient.
Example:
- `C:\Users\YourName\Documents\neuro_ingest`

Step 3B-4. Open PowerShell in the extracted `neuro_ingest` folder.
One easy way:
- open the folder in File Explorer
- click the address bar
- type `powershell`
- press Enter

Step 4. Create a local virtual environment inside the repo folder.

```powershell
py -3.11 -m venv .venv
```

Step 5. Activate that virtual environment.

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run this once in that PowerShell window:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

Step 6. Upgrade `pip` inside the virtual environment.

```powershell
python -m pip install --upgrade pip
```

Step 7. Install this project.

```powershell
pip install .
```

What Step 7 does:
- installs the `neuro_ingest` package from the repo folder on your PC
- downloads the Python dependencies listed in `pyproject.toml` from PyPI

Step 8. Start the UI.

```powershell
scripts\run_ingest_ui.ps1
```

If you want a simpler day-to-day launch, you can also double-click:

```text
start_neuro_ingest_ui.bat
```

Step 9. Open the local URL shown in the terminal.
It will usually look like:

```text
http://localhost:8501
```

Alternative to Step 8:

```powershell
python -m streamlit run scripts/ingest_ui.py --browser.gatherUsageStats false --server.address localhost
```

After first-time setup, the easiest repeat-use path is usually:
- double-click `start_neuro_ingest_ui.bat`
- keep the PowerShell window open while using the UI
- press `Ctrl+C` in that window when you want to stop it

### Summary Of What Must Be Installed

Required:
- Python 3.11

Required for one repo-download method:
- Git for Windows, only if you want to use `git clone`

Not required:
- Anaconda
- Miniconda
- VS Code
- Visual Studio

### Recommended Folder Layout

If you want an easy-to-remember setup on Windows, use something like:

```text
C:\Users\YourName\Projects\neuro_ingest
C:\Users\YourName\Projects\neuro_ingest\.venv
C:\Users\YourName\NeuroIngestData\normalized
C:\Users\YourName\NeuroIngestData\neuro_audio.duckdb
```

What goes where:
- the repo lives in `C:\Users\YourName\Projects\neuro_ingest`
- the virtual environment lives inside the repo as `.venv`
- the output Parquet files live in a separate data folder
- the DuckDB database file lives in that same separate data folder

Why this layout helps:
- code and dependencies stay together
- data stays separate from the repo
- you can update or re-clone the repo without mixing it with saved outputs

How to control install locations:
- `git clone ...` creates the repo in whatever folder PowerShell is currently in
- `py -3.11 -m venv .venv` creates the virtual environment in the current repo folder
- `pip install .` installs the package into the active virtual environment, not system-wide

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

If you prefer Conda, the old setup still works:

```bash
conda env create -f environment.yml
conda activate neuro-ingest
```

If your existing environment already has NumPy 2.x and crashes on import on Windows, pin NumPy below 2:

```powershell
pip install "numpy<2"
```

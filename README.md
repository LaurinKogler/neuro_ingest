# neuro_ingest

`neuro_ingest` is a local workbench for neuro-audio data. It ingests TDT and
IHS exports, normalizes them into one sample-table shape, writes Parquet files
and DuckDB databases, and gives you an interactive ABR viewer for checking
traces and thresholds.

The main rule is simple: raw vendor files stay untouched. Normalized data,
DuckDB indexes, edits, backups, and personal settings are written separately.

For the full walkthrough, see [docs/USER_GUIDE.md](docs/USER_GUIDE.md).

## Quick Start

On a Windows PC with Python 3.11 installed:

```powershell
git clone https://github.com/LaurinKogler/neuro_ingest.git
cd neuro_ingest
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install .
scripts\run_ingest_ui.ps1
```

Then open the local Streamlit URL shown in the terminal. It is usually:

```text
http://localhost:8501
```

For day-to-day use after setup, double-click:

```text
start_neuro_ingest_ui.bat
```

To update an already configured PC, double-click:

```text
update_neuro_ingest.bat
```

If PowerShell blocks virtual-environment activation, run this once in the same
PowerShell window and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## What The App Does

The Streamlit app has four main areas:

- **Ingest**: manually upload left/right TDT files or IHS exports, add session
  metadata, and write Parquet plus DuckDB output.
- **Mass Ingest**: scan a folder tree, preview what will be imported, review
  warnings, and then write many sessions at once.
- **Viewer**: load traces from the last ingest, a Parquet file, DuckDB filters,
  or a DuckDB SQL query. DuckDB filters are the normal default when no file was
  just uploaded.
- **Database**: inspect stored sessions and edit trace metadata such as
  `stim_ear`, `rec_ear`, and `rel_ear`.

The sidebar controls the default session metadata and storage target. The
in-app **Settings** panel stores personal defaults such as trace density,
waveform size, viewer row limits, and editor backup behavior.

## Manual Ingest

Use the **Ingest** tab when you have a small set of files for one session.

1. Choose `TDT` or `IHS`.
2. Fill in animal ID, session date, paradigm, and optional day/session ID.
3. For TDT, drop left-ear and right-ear files into the separate upload boxes.
4. Press **Ingest**.
5. Check the viewer or database output.

The app writes:

- Parquet output in the selected Parquet directory.
- A DuckDB database at the selected DuckDB target.

## Mass Ingest

Use **Mass Ingest** when you have a whole folder tree of TDT exports.

The expected folder pattern is:

```text
<animal_id>\<animal_id>_d<day>_<YYYYMMDD>\...
```

Example:

```text
AC04\AC04_d42_20260820\
```

Files can contain labels such as `ClickABR`, `ToneABR`, `left`, `right`, extra
frequency/level notes, or redo markers. Split measurements for the same
animal/day/date can be merged into the same session, which is useful when you
recorded a few extra louder or quieter traces outside the main file.

Recommended workflow:

1. Pick the folder tree with **Browse**.
2. Run a dry run.
3. Read the warnings and discovered sessions.
4. Choose whether to create a new DuckDB or merge into an existing one.
5. Choose the existing-session policy:
   - **Skip existing sessions** keeps old data and imports only new sessions.
   - **Stop with error** aborts if a session already exists.
   - **Overwrite** replaces matching existing sessions.
6. Run the write import.

Backups are hidden from the DuckDB dropdowns so old backup files do not clutter
normal choices.

## Viewer Notes

The ABR viewer is designed for threshold inspection:

- Frequency `0` is shown as `Click`.
- Trace intensity is labeled directly on the stacked Y axis when possible.
- The plot colors use a plasma-style palette for readable trace separation.
- Left and right ears get independent density and waveform-size controls.
- Day filters accept either `d14` or `14`.
- Animal and day filters are dropdowns based on what is available in the
  selected DuckDB.

## Settings And Local Files

Personal UI defaults are stored here:

```text
data/processed/settings/user_settings.json
```

Machine-specific launcher defaults can live here:

```text
scripts/ingest_ui.local.toml
```

Both files are ignored by Git, so your local paths and preferences are not
overwritten when you pull updates.

Generated data and databases are local working files. Keep them outside Git
unless you deliberately want to archive a small test fixture.

## Python API

The UI is the normal path, but the toolbox can also be used from Python:

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
    session_date=date(2026, 8, 20),
    day=42,
)

toolbox.save(session, overwrite=False)
df = toolbox.query("SELECT * FROM samples WHERE animal_id = ?", ["AC04"])
fig = toolbox.plot(df, frequency_hz=0.0, relation_mode="ipsi")
fig.show()
```

## Project Map

- `app/streamlit_app.py`: Streamlit entrypoint.
- `scripts/ingest_ui.py`: main UI implementation.
- `src/neuro_ingest/ingest`: vendor parsers and ingest orchestration.
- `src/neuro_ingest/batch.py`: folder-tree discovery and mass ingest planning.
- `src/neuro_ingest/storage`: Parquet and DuckDB storage.
- `src/neuro_ingest/plot`: ABR plotting.
- `src/neuro_ingest/toolbox.py`: notebook/Python facade.
- `docs/USER_GUIDE.md`: longer setup and usage guide.

## Development

Install the optional development tools when you want tests, formatting, and
linting:

```powershell
pip install -e ".[dev]"
```

Run tests:

```powershell
scripts\run_tests.ps1
```

Run linting and formatting checks:

```powershell
ruff check .
black --check .
```

## Requirements

Required:

- Windows 10 or Windows 11 for the provided launcher scripts.
- Python 3.11.

Optional:

- Git for Windows, if you want easy cloning and updates.
- Conda or Miniconda, if you prefer that environment style.

Not required:

- Anaconda.
- VS Code.
- Visual Studio.

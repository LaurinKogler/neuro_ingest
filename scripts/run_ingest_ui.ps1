param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ExtraArgs
)

$ErrorActionPreference = "Stop"

function Resolve-PythonCommand {
    if ($env:NEURO_INGEST_PYTHON_EXE -and (Test-Path $env:NEURO_INGEST_PYTHON_EXE)) {
        return $env:NEURO_INGEST_PYTHON_EXE
    }

    if ($env:NEURO_INGEST_ENV_PREFIX) {
        $prefixPython = Join-Path $env:NEURO_INGEST_ENV_PREFIX "python.exe"
        if (Test-Path $prefixPython) {
            return $prefixPython
        }
    }

    $candidates = @(
        "$env:USERPROFILE\miniconda3\envs\neuro-ingest\python.exe",
        "$env:USERPROFILE\anaconda3\envs\neuro-ingest\python.exe",
        "$env:USERPROFILE\mambaforge\envs\neuro-ingest\python.exe",
        "C:\ProgramData\miniconda3\envs\neuro-ingest\python.exe",
        "C:\ProgramData\anaconda3\envs\neuro-ingest\python.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return $null
}

$pythonExe = Resolve-PythonCommand
if (-not $pythonExe) {
    Write-Host "Python env not found. Set NEURO_INGEST_PYTHON_EXE or NEURO_INGEST_ENV_PREFIX."
    exit 1
}

$cmd = @(
    "-m", "streamlit", "run", "scripts/ingest_ui.py",
    "--browser.gatherUsageStats", "false",
    "--server.address", "localhost"
)
if ($ExtraArgs.Count -gt 0) {
    $cmd += $ExtraArgs
}

& $pythonExe @cmd
exit $LASTEXITCODE

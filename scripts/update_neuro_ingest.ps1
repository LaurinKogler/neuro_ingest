param()

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Resolve-PythonCommand {
    if ($env:NEURO_INGEST_PYTHON_EXE -and (Test-Path $env:NEURO_INGEST_PYTHON_EXE)) {
        return $env:NEURO_INGEST_PYTHON_EXE
    }

    if ($env:NEURO_INGEST_ENV_PREFIX) {
        $prefixCandidates = @(
            (Join-Path $env:NEURO_INGEST_ENV_PREFIX "Scripts\python.exe"),
            (Join-Path $env:NEURO_INGEST_ENV_PREFIX "python.exe")
        )

        foreach ($candidate in $prefixCandidates) {
            if (Test-Path $candidate) {
                return $candidate
            }
        }
    }

    if ($env:VIRTUAL_ENV) {
        $venvCandidates = @(
            (Join-Path $env:VIRTUAL_ENV "Scripts\python.exe"),
            (Join-Path $env:VIRTUAL_ENV "python.exe")
        )

        foreach ($candidate in $venvCandidates) {
            if (Test-Path $candidate) {
                return $candidate
            }
        }
    }

    $candidates = @(
        (Join-Path $repoRoot ".venv\Scripts\python.exe"),
        (Join-Path $repoRoot "venv\Scripts\python.exe"),
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

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        return $pythonCmd.Source
    }

    return $null
}

$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitCmd) {
    Write-Host "Git was not found on PATH. Install Git for Windows first."
    exit 1
}

$pythonExe = Resolve-PythonCommand
if (-not $pythonExe) {
    Write-Host "Python env not found. Activate a virtualenv, create .venv, or set NEURO_INGEST_PYTHON_EXE / NEURO_INGEST_ENV_PREFIX."
    exit 1
}

Push-Location $repoRoot
try {
    Write-Host "Updating repo from origin/main..."
    & $gitCmd.Source pull origin main
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }

    Write-Host ""
    Write-Host "Reinstalling neuro_ingest into the selected Python environment..."
    & $pythonExe -m pip install .
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}

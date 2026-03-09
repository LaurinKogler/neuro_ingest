param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PytestArgs
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

function Resolve-CondaCommand {
    if ($env:NEURO_INGEST_CONDA_EXE -and (Test-Path $env:NEURO_INGEST_CONDA_EXE)) {
        return $env:NEURO_INGEST_CONDA_EXE
    }
    if ($env:CONDA_EXE -and (Test-Path $env:CONDA_EXE)) {
        return $env:CONDA_EXE
    }

    $cmd = Get-Command conda -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    $candidates = @(
        "$env:USERPROFILE\miniconda3\Scripts\conda.exe",
        "$env:USERPROFILE\miniconda3\condabin\conda.bat",
        "$env:USERPROFILE\anaconda3\Scripts\conda.exe",
        "$env:USERPROFILE\anaconda3\condabin\conda.bat",
        "$env:USERPROFILE\mambaforge\Scripts\conda.exe",
        "$env:USERPROFILE\mambaforge\condabin\conda.bat",
        "C:\ProgramData\miniconda3\Scripts\conda.exe",
        "C:\ProgramData\miniconda3\condabin\conda.bat",
        "C:\ProgramData\anaconda3\Scripts\conda.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return $null
}

$pythonExe = Resolve-PythonCommand
$condaExe = Resolve-CondaCommand

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$testRuntimeDir = Join-Path $repoRoot "test_runtime"
$tmpDir = Join-Path $testRuntimeDir "tmp"

New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null

# Keep pytest temp files in a known writable project-local location.
$env:TMP = $tmpDir
$env:TEMP = $tmpDir

$pytestCommonArgs = @("-p", "no:cacheprovider", "-p", "no:tmpdir")
if ($PytestArgs.Count -eq 0) {
    $pytestCommonArgs += "-q"
} else {
    $pytestCommonArgs += $PytestArgs
}

if ($pythonExe) {
    $pythonCmd = @("-m", "pytest") + $pytestCommonArgs
    & $pythonExe @pythonCmd
    $exitCode = $LASTEXITCODE
} elseif ($condaExe) {
    $cmd = @("run", "-n", "neuro-ingest", "pytest") + $pytestCommonArgs
    & $condaExe @cmd
    $exitCode = $LASTEXITCODE
} else {
    Write-Host "No Python/Conda override found. Set NEURO_INGEST_PYTHON_EXE or NEURO_INGEST_ENV_PREFIX or NEURO_INGEST_CONDA_EXE. Falling back to pytest from active shell."
    try {
        pytest @pytestCommonArgs
        $exitCode = $LASTEXITCODE
    } catch {
        Write-Host "Could not run pytest from active shell either."
        Write-Host "Set NEURO_INGEST_CONDA_EXE to your conda executable path and retry."
        exit 1
    }
}

if ($exitCode -ne 0) {
    Write-Host "Tests failed. Re-run with: scripts/run_tests.ps1 tests/test_lab_api.py -q"
}

exit $exitCode

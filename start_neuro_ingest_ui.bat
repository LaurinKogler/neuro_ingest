@echo off
setlocal

set "REPO_ROOT=%~dp0"
set "POWERSHELL_EXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"

"%POWERSHELL_EXE%" -ExecutionPolicy Bypass -NoExit -File "%REPO_ROOT%scripts\run_ingest_ui.ps1"


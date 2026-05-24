# Wrapper for Windows Task Scheduler
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..
& ".\.venv\Scripts\python.exe" -m src.main

# register_scheduler.ps1
# Registers the ky-platform nightly (daily 02:00) + weekly (Sunday 04:00)
# runners with Windows Task Scheduler.
#
# Run from an elevated PowerShell. Idempotent: /F overwrites an existing task
# with the same name, so running the script twice is a no-op in effect.
#
# Usage:
#     pwsh -File scripts\register_scheduler.ps1
# or
#     powershell -ExecutionPolicy Bypass -File scripts\register_scheduler.ps1

$ErrorActionPreference = "Stop"

$repoRoot   = Split-Path -Parent $PSScriptRoot
$python     = (Get-Command python).Source
$nightlyPy  = Join-Path $repoRoot "scripts\nightly.py"
$weeklyPy   = Join-Path $repoRoot "scripts\weekly.py"

if (-not (Test-Path $nightlyPy)) { throw "nightly.py not found at $nightlyPy" }
if (-not (Test-Path $weeklyPy))  { throw "weekly.py not found at $weeklyPy" }

Write-Host "Registering ky-platform-nightly (daily 02:00) ..."
schtasks /Create `
    /TN "ky-platform-nightly" `
    /TR "`"$python`" `"$nightlyPy`"" `
    /SC DAILY `
    /ST 02:00 `
    /F | Out-Null

Write-Host "Registering ky-platform-weekly (Sunday 04:00) ..."
schtasks /Create `
    /TN "ky-platform-weekly" `
    /TR "`"$python`" `"$weeklyPy`"" `
    /SC WEEKLY `
    /D SUN `
    /ST 04:00 `
    /F | Out-Null

Write-Host ""
Write-Host "Done. Installed tasks:"
schtasks /Query /TN "ky-platform-nightly" | Select-Object -First 4
schtasks /Query /TN "ky-platform-weekly"  | Select-Object -First 4
Write-Host ""
Write-Host "To remove:"
Write-Host "    schtasks /Delete /TN ky-platform-nightly /F"
Write-Host "    schtasks /Delete /TN ky-platform-weekly  /F"

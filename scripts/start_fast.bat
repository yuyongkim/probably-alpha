@echo off
REM Fast start: API + Frontend only (no pipeline, no backfill)
REM Use this for development / quick access to dashboard
powershell -ExecutionPolicy Bypass -Command ^
  "Set-Location '%~dp0..'; ^
   $env:SEPA_RUN_AFTER_CLOSE='0'; ^
   $env:SEPA_BACKFILL_DAYS='0'; ^
   $env:SEPA_KILL_EXISTING_PORTS='1'; ^
   & '%~dp0start_local.ps1'"

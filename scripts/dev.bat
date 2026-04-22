@echo off
REM ky-platform dev runner (Windows) — api 8300 + web 8380
REM Load order: shared.env -> apps/api/.env (via config.py) -> shell env

setlocal enabledelayedexpansion
set "ROOT=%~dp0.."
pushd "%ROOT%"

REM 1. shared.env (optional)
set "SHARED=%USERPROFILE%\.ky-platform\shared.env"
if exist "%SHARED%" (
  echo [dev.bat] loading %SHARED%
  for /f "usebackq eol=# tokens=1,* delims==" %%A in ("%SHARED%") do (
    if not "%%A"=="" set "%%A=%%B"
  )
) else (
  echo [dev.bat] note: %SHARED% not found - external API calls will be skipped
)

REM 2. defaults
if not defined API_HOST set "API_HOST=127.0.0.1"
if not defined API_PORT set "API_PORT=8300"
if not defined WEB_HOST set "WEB_HOST=127.0.0.1"
if not defined WEB_PORT set "WEB_PORT=8380"

REM 3. launch in two windows
echo [dev.bat] starting api on :%API_PORT%
start "ky-api" cmd /k "cd /d %ROOT%\apps\api && uvicorn main:app --reload --host %API_HOST% --port %API_PORT%"

echo [dev.bat] starting web on :%WEB_PORT%
start "ky-web" cmd /k "cd /d %ROOT%\apps\web && npm run dev -- -p %WEB_PORT% -H %WEB_HOST%"

popd
endlocal

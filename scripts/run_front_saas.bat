@echo on
setlocal
cd /d C:\Users\USER\Desktop\Company_Credit

echo ===== SEPA START =====
echo CWD: %CD%

echo [1] Python launcher check
where py
if errorlevel 1 (
  where python
  if errorlevel 1 (
    echo [FATAL] python/py not found
    pause
    exit /b 1
  ) else (
    set PY=python
  )
) else (
  set PY=py
)

echo Using: %PY%

echo [2] Run after-close pipeline
%PY% -m sepa.pipeline.run_after_close
if errorlevel 1 (
  echo [FATAL] pipeline failed
  pause
  exit /b 1
)

echo [3] Kill old 8000/8080
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /PID %%a /F
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8080') do taskkill /PID %%a /F

echo [4] Start API window
start "SEPA_API" cmd /k "cd /d C:\Users\USER\Desktop\Company_Credit && %PY% -m uvicorn sepa.api.app:app --host 127.0.0.1 --port 8000"

echo [5] Wait API 3 sec
timeout /t 3 /nobreak

echo [6] Start FRONT window
start "SEPA_FRONT" cmd /k "cd /d C:\Users\USER\Desktop\Company_Credit && %PY% -m http.server 8080 --bind 127.0.0.1 --directory sepa/frontend"

echo [7] Open browser
start "" http://127.0.0.1:8080

echo ===== DONE =====
echo If page still not open, check SEPA_API window errors.
pause
endlocal

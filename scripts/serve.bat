@echo off
REM SEPA Server: API + Frontend + auto browser open
REM Restarts automatically if either server dies
python "%~dp0serve.py" %*

@echo off
setlocal enableextensions
cd /d "%~dp0"
title Continuum 2026 Chinese Patch - Restore English
echo ============================================================
echo   Continuum 2026 - restore original English
echo ============================================================
echo.
set N=0
for %%F in ("Continuum*.exe") do set /A N+=1
if not "%N%"=="1" (
  echo [ERROR] Expected exactly one Continuum*.exe next to this file,
  echo         found %N%. Run Restore-English.bat instead.
  echo.
  pause
  goto :eof
)
echo Starting the restore tool - a UAC dialog will appear ...
echo.
for %%F in ("Continuum*.exe") do "%%~fF" /restore
endlocal

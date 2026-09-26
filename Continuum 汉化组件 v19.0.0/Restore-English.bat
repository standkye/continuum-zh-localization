@echo off
setlocal enableextensions
title BorisFX Continuum 2026 - Restore English

fltmc >nul 2>&1
if errorlevel 1 (
  echo Requesting administrator rights, please click "Yes" on the UAC dialog...
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs -Wait"
  exit /b
)

set CONT=C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum
set LIB=C:\Program Files\BorisFX\ContinuumAE\19\lib
set BAK=C:\Program Files\BorisFX\ContinuumAE\19\Backup-English
set FAILCNT=0

echo ============================================================
echo   Restore original English BorisFX Continuum files
echo ============================================================
echo.

tasklist /NH | findstr /I "AfterFX.exe" >nul
if not errorlevel 1 (
  echo [ERROR] After Effects is running. Quit it first.
  goto end
)

if not exist "%BAK%" (echo [ERROR] Backup folder not found: %BAK% & goto end)

echo [1/2] restoring 6 engine dlls ...
for %%F in (Continuum_AE_Float.dll Continuum_AE_8Bit.dll Continuum_AE_16Bit.dll Continuum_Common_AE.dll Continuum_3DObjects_AE.dll) do (
  copy /Y "%BAK%\%%F" "%LIB%\%%F" >nul
  if errorlevel 1 (echo       FAIL %%F & set /A FAILCNT+=1) else (echo       OK   %%F)
)
copy /Y "%BAK%\BCCPlus.dll" "%CONT%\BCCPlus.dll" >nul
if errorlevel 1 (echo       FAIL BCCPlus.dll & set /A FAILCNT+=1) else (echo       OK   BCCPlus.dll)

echo [2/2] restoring 488 .aex files ...
for %%F in ("%BAK%\aex\*.aex") do (
  copy /Y "%%F" "%CONT%\%%~nxF" >nul
  if errorlevel 1 (echo       FAIL %%~nxF & set /A FAILCNT+=1)
)
echo       done.

echo.
if "%FAILCNT%"=="0" (
  echo SUCCESS - back to English. Restart After Effects.
) else (
  echo %FAILCNT% files failed.
)

:end
echo.
pause
endlocal

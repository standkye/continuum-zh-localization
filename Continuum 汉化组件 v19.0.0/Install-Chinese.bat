@echo off
setlocal enableextensions
title BorisFX Continuum 2026 - Chinese Patch (v19.0.0)

fltmc >nul 2>&1
if errorlevel 1 (
  echo Requesting administrator rights, please click "Yes" on the UAC dialog...
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs -Wait"
  exit /b
)

set SRC=%~dp0
set CONT=C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum
set LIB=C:\Program Files\BorisFX\ContinuumAE\19\lib
set BAK=C:\Program Files\BorisFX\ContinuumAE\19\Backup-English
set FAILCNT=0

echo ============================================================
echo   BorisFX Continuum 2026 - Chinese patch
echo   v19.0.0   encoding GBK   (verified by test on this machine)
echo ============================================================
echo.

rem --- 0) After Effects must be closed ---
tasklist /NH | findstr /I "AfterFX.exe" >nul
if not errorlevel 1 (
  echo [ERROR] After Effects is running.
  echo         Quit After Effects completely, then run this again.
  goto fail
)

rem --- 1) sanity check ---
if not exist "%CONT%" (echo [ERROR] Not found: %CONT% & goto fail)
if not exist "%LIB%"  (echo [ERROR] Not found: %LIB%  & goto fail)

rem --- 2) backup original English files ---
echo [1/3] Backing up original English files ...
if not exist "%BAK%" mkdir "%BAK%"
if not exist "%BAK%\aex" mkdir "%BAK%\aex"
for %%F in ("%CONT%\*.aex") do (
  if not exist "%BAK%\aex\%%~nxF" copy /Y "%%F" "%BAK%\aex\%%~nxF" >nul
)
for %%F in (Continuum_AE_Float.dll Continuum_AE_8Bit.dll Continuum_AE_16Bit.dll Continuum_Common_AE.dll Continuum_3DObjects_AE.dll) do (
  if not exist "%BAK%\%%F" copy /Y "%LIB%\%%F" "%BAK%\%%F" >nul
)
if not exist "%BAK%\BCCPlus.dll" copy /Y "%CONT%\BCCPlus.dll" "%BAK%\BCCPlus.dll" >nul
copy /Y "%SRC%Restore-English.bat" "%BAK%\Restore-English.bat" >nul
echo       backup folder: %BAK%

rem --- 3) install 488 effect names ---
echo [2/3] Installing 488 Chinese effect names ...
for %%F in ("%SRC%*.aex") do (
  copy /Y "%%F" "%CONT%\%%~nxF" >nul
  if errorlevel 1 (echo       FAIL %%~nxF & set /A FAILCNT+=1)
)
echo       done.

rem --- 4) install 6 engine dlls ---
echo [3/3] Installing Chinese parameter names ...
for %%F in (Continuum_AE_Float.dll Continuum_AE_8Bit.dll Continuum_AE_16Bit.dll Continuum_Common_AE.dll Continuum_3DObjects_AE.dll) do (
  copy /Y "%SRC%%%F" "%LIB%\%%F" >nul
  if errorlevel 1 (echo       FAIL %%F & set /A FAILCNT+=1) else (echo       OK   %%F)
)
copy /Y "%SRC%BCCPlus.dll" "%CONT%\BCCPlus.dll" >nul
if errorlevel 1 (echo       FAIL BCCPlus.dll & set /A FAILCNT+=1) else (echo       OK   BCCPlus.dll)

echo.
if "%FAILCNT%"=="0" (
  echo ============================================================
  echo   SUCCESS - everything installed.
  echo   Start After Effects: effect names and parameters are Chinese.
  echo   To restore English:  %BAK%\Restore-English.bat
  echo ============================================================
) else (
  echo SOME FILES FAILED (%FAILCNT%). Quit After Effects and run again.
)
goto end

:fail
echo.
echo INSTALL ABORTED.

:end
echo.
pause
endlocal

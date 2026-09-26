# -*- coding: utf-8 -*-
"""生成扁平化安装包：所有文件同一层，文件名纯 ASCII"""
import os, shutil

WORK = r"D:\Programming project\插件汉化\_work"
PKG = r"D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0"
SRC_AEX = os.path.join(WORK, 'patched_aex')
SRC_DLL = os.path.join(WORK, 'patched_dll')

if os.path.isdir(PKG):
    shutil.rmtree(PKG)
os.makedirs(PKG)

n = 0
for f in sorted(os.listdir(SRC_AEX)):
    if f.lower().endswith('.aex'):
        shutil.copy2(os.path.join(SRC_AEX, f), os.path.join(PKG, f)); n += 1
d = 0
for f in sorted(os.listdir(SRC_DLL)):
    if f.lower().endswith('.dll'):
        shutil.copy2(os.path.join(SRC_DLL, f), os.path.join(PKG, f)); d += 1
print(f"aex {n}  dll {d}")

install = r'''@echo off
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
echo   v19.0.0   encoding GBK   (After Effects 25.1 and older)
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
'''

restore = r'''@echo off
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
'''


def write_bat(path, text):
    text = text.replace('\r\n', '\n').replace('\n', '\r\n')
    open(path, 'wb').write(text.encode('ascii'))


write_bat(os.path.join(PKG, 'Install-Chinese.bat'), install)
write_bat(os.path.join(PKG, 'Restore-English.bat'), restore)

readme = """BorisFX Continuum 2026 (v19.0.0) - Chinese patch
================================================
(Chinese below / 中文见下)

WHAT IT CHANGES
  - 488 effect names (shown in the Effects menu)
  - parameter names inside 6 engine DLLs, about 13,500 strings:
    Continuum_AE_Float / _8Bit / _16Bit / _Common_AE / _3DObjects_AE / BCCPlus

HOW TO INSTALL
  1. Quit After Effects completely
  2. Double-click  Install-Chinese.bat  and click "Yes" on the UAC dialog
  3. After SUCCESS, start After Effects

HOW TO RESTORE
  Run  Restore-English.bat
  (also copied to C:\\Program Files\\BorisFX\\ContinuumAE\\19\\Backup-English)

SAFETY
  - Every file is patched IN PLACE: file size, PE structure and all offsets
    are unchanged. Nothing is added, removed or moved.
  - The installer backs up the English originals to
    C:\\Program Files\\BorisFX\\ContinuumAE\\19\\Backup-English
  - Presets (.bsp/.bap) index parameters by numeric ID, so changing display
    names does not break them.
  - No After Effects program file is touched.

REQUIREMENTS / LIMITS
  - Continuum 2026 Adobe v19.0.0 (this machine: build 19.0.0.327)
  - After Effects 25.1 or older uses GBK - this patch is GBK.
    On AE 26.2+ names will look like garbage; ask for a UTF-8 build.
  - Parameter names are Chinese only: the string slots were sized for the
    English text, so a second language does not fit.
  - A few rare words / abbreviations (Cb, Cr, CA, PixelChooser) stay English.
  - Re-apply after any Continuum update.

================================================
BorisFX Continuum 2026 (v19.0.0) 汉化组件 —— 中文说明

改了什么
  - 488 个效果名（Effects 菜单里的名字）
  - 6 个引擎 DLL 里的参数名，共约 13500 处

怎么装
  1. 完全退出 After Effects
  2. 双击 Install-Chinese.bat，UAC 点"是"
  3. 看到 SUCCESS 后启动 After Effects

怎么还原
  运行 Restore-English.bat（也会备份到
  C:\\Program Files\\BorisFX\\ContinuumAE\\19\\Backup-English）

安全性
  - 全部"就地替换"：文件大小、PE 结构、偏移一律不变
  - 自动备份英文原版
  - 预设按数字 ID 索引参数，改显示名不会破坏预设
  - 不碰 After Effects 自己的任何文件

限制
  - 适用 AE 25.1 及更早（GBK）。AE 26.2 起要用 UTF-8 版
  - 参数名只有中文（槽位按英文长度分配，放不下第二种语言）
  - 极少数缩写保留英文
  - Continuum 升级后需重新打补丁
"""
open(os.path.join(PKG, 'Readme.txt'), 'w', encoding='utf-8').write(readme)

# 对照表（ASCII 文件名，内容中文）
import json
eff = json.load(open(os.path.join(WORK, 'effect_zh.json'), encoding='utf-8'))
pz = json.load(open(os.path.join(WORK, 'param_zh.json'), encoding='utf-8'))
lines = ["Continuum effect names  Chinese -> English", "=" * 52, ""]
rows = sorted({(zh, en.strip()) for its in eff.values()
               for (en, zh, sz, off, cap) in its})
for zh, en in sorted(rows, key=lambda r: r[0]):
    lines.append(f"{zh:<24s} {en}")
open(os.path.join(PKG, 'EffectNameTable.txt'), 'w', encoding='utf-8').write("\n".join(lines))

lines2 = ["Continuum parameter names  Chinese -> English", f"total {len(pz)}", "=" * 52, ""]
for en, zh in sorted(pz.items(), key=lambda kv: kv[1]):
    lines2.append(f"{zh:<20s} {en}")
open(os.path.join(PKG, 'ParamNameTable.txt'), 'w', encoding='utf-8').write("\n".join(lines2))

print("PKG ready:", PKG, len(os.listdir(PKG)), "files")

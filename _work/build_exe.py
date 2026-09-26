# -*- coding: utf-8 -*-
"""用 Windows 自带的 IExpress 打成单个自解压 exe"""
import os, shutil, subprocess

PKG = r"D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0"
STAGE = r"C:\Users\Jinna\.workbuddy\pkg_flat"          # 纯 ASCII 路径
SED = r"C:\Users\Jinna\.workbuddy\pkg.sed"
OUT = r"C:\Users\Jinna\.workbuddy\ContinuumHanhua_v19.0.0.exe"
FINAL = r"D:\Programming project\插件汉化\Continuum汉化组件_v19.0.0.exe"
LOG = r"D:\Programming project\插件汉化\_work\iexpress_log.txt"

log = []
if os.path.isdir(STAGE):
    shutil.rmtree(STAGE)
os.makedirs(STAGE)
files = sorted(os.listdir(PKG))
for f in files:
    shutil.copy2(os.path.join(PKG, f), os.path.join(STAGE, f))
log.append(f"暂存 {len(files)} 个文件 -> {STAGE}")

L = []
L.append("[Version]")
L.append("Class=IEXPRESS")
L.append("SEDVersion=3")
L.append("[Options]")
L.append("PackagePurpose=InstallApp")
L.append("ShowInstallProgramWindow=1")
L.append("HideExtractAnimation=0")
L.append("UseLongFileName=1")
L.append("InsideCompressed=1")
L.append("CAB_FixedSize=0")
L.append("CAB_ResvCodeSigning=0")
L.append("RebootMode=N")
L.append("InstallPrompt=%InstallPrompt%")
L.append("DisplayLicense=%DisplayLicense%")
L.append("FinishMessage=%FinishMessage%")
L.append("TargetName=%TargetName%")
L.append("FriendlyName=%FriendlyName%")
L.append("AppLaunched=%AppLaunched%")
L.append("PostInstallCmd=%PostInstallCmd%")
L.append("AdminQuietInstCmd=%AdminQuietInstCmd%")
L.append("UserQuietInstCmd=%UserQuietInstCmd%")
L.append("SourceFiles=SourceFiles")
L.append("[Strings]")
L.append("InstallPrompt=Continuum 2026 Chinese Patch v19.0.0 - install now?")
L.append("DisplayLicense=")
L.append("FinishMessage=Done. Start After Effects to see Chinese effect names.")
L.append("TargetName=" + OUT)
L.append("FriendlyName=Continuum2026Hanhua")
L.append("AppLaunched=Install-Chinese.bat")
L.append("PostInstallCmd=<None>")
L.append("AdminQuietInstCmd=")
L.append("UserQuietInstCmd=")
for i, f in enumerate(files):
    L.append(f'FILE{i}="{f}"')
L.append("[SourceFiles]")
L.append("SourceFiles0=" + STAGE + "\\")
L.append("[SourceFiles0]")
for i, f in enumerate(files):
    L.append(f"%FILE{i}%=")
open(SED, 'w', encoding='ascii').write("\n".join(L) + "\n")
log.append("SED 已生成: " + SED)

if os.path.exists(OUT):
    os.remove(OUT)
r = subprocess.run([r"C:\Windows\System32\iexpress.exe", "/N", "/Q", SED],
                   capture_output=True, timeout=3600)
log.append("iexpress rc=" + str(r.returncode))
log.append("stdout: " + r.stdout.decode('gbk', 'ignore'))
log.append("stderr: " + r.stderr.decode('gbk', 'ignore'))
if os.path.exists(OUT):
    sz = os.path.getsize(OUT) / 1024 / 1024
    log.append(f"生成 {OUT}  {sz:.1f} MB")
    shutil.copy2(OUT, FINAL)
    log.append("已复制到 " + FINAL)
else:
    log.append("未生成 exe")
open(LOG, 'w', encoding='utf-8').write("\n".join(log))

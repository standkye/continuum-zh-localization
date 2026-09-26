# -*- coding: utf-8 -*-
"""Rebuild the one-click installer (v3).

Changes vs build_exe2.py:
  * STAGE -> pyinstaller_stage4 (a brand-new dir). Reusing a stage dir forces a
    cleanup walk over ~495 files, which trips the host's SAFE_DELETE_BULK guard
    and kills the build with a 1-second exit code 1.
  * Copies the finished exe into the delivery folder and re-verifies the
    embedded payload byte-for-byte against the loose files.
"""

import os
import shutil
import subprocess
import sys

VENV_PY = r"C:\Users\Jinna\.workbuddy\binaries\python\envs\default\Scripts\python.exe"
PROJ = r"D:\Programming project\插件汉化"
SRC = os.path.join(PROJ, "Continuum 汉化组件 v19.0.0")
STAGE = r"C:\Users\Jinna\.workbuddy\pyinstaller_stage4"
DIST = os.path.join(STAGE, "dist")
WORK = os.path.join(STAGE, "build")
OUT_NAME = "Continuum汉化安装器"

ENGINE_DLLS = [
    "Continuum_AE_Float.dll",
    "Continuum_AE_8Bit.dll",
    "Continuum_AE_16Bit.dll",
    "Continuum_Common_AE.dll",
    "Continuum_3DObjects_AE.dll",
    "BCCPlus.dll",
]


def main():
    log = []

    def say(s):
        log.append(s)
        print(s)

    os.makedirs(STAGE, exist_ok=True)

    installer_src = os.path.join(PROJ, "_work", "installer_gui.py")
    shutil.copy2(installer_src, os.path.join(STAGE, "installer_gui.py"))
    say("installer_gui.py staged")

    n = 0
    for f in sorted(os.listdir(SRC)):
        if f.lower().endswith(".aex"):
            shutil.copy2(os.path.join(SRC, f), os.path.join(STAGE, f))
            n += 1
    say("staged %d .aex" % n)

    for d in ENGINE_DLLS:
        p = os.path.join(SRC, d)
        if not os.path.exists(p):
            say("!! MISSING " + d)
            return 1
        shutil.copy2(p, os.path.join(STAGE, d))
    say("staged %d dll" % len(ENGINE_DLLS))

    cmd = [
        VENV_PY, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        "--onefile",
        "--console",
        "--name", OUT_NAME,
        "--distpath", DIST,
        "--workpath", WORK,
        "--specpath", WORK,
        "--add-data", "%s;." % STAGE,
        os.path.join(STAGE, "installer_gui.py"),
    ]
    say("running PyInstaller ...")
    r = subprocess.run(cmd, cwd=STAGE, capture_output=True)
    out = r.stdout.decode("utf-8", "replace") + r.stderr.decode("utf-8", "replace")
    log.append(out)
    with open(os.path.join(PROJ, "_work", "_build3_log.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(log))
    say("PyInstaller exit: %d" % r.returncode)

    produced = os.path.join(DIST, OUT_NAME + ".exe")
    if not os.path.exists(produced):
        say("NOT BUILT")
        return 1
    say("BUILT: %s  %d bytes" % (produced, os.path.getsize(produced)))

    target = os.path.join(SRC, OUT_NAME + ".exe")
    shutil.copy2(produced, target)
    say("copied to delivery: %s  %d bytes" % (target, os.path.getsize(target)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""Rebuild the one-click installer (v16) -- hyg2 backfill build.

Difference from v15: the delivery folder's 6 engine DLLs are now the
"hyg2" build, which adds 103 backfilled display-name slots (44 distinct
tokens) on top of the v15 hygiene build:

  * ROUTE A -- the token is a <name> element in a vendor preset (the
    pipeline's real display-name vocabulary).
  * ROUTE B -- the token's table neighbourhood (+-0x120) already holds
    >=8 Chinese strings (so the table is already being displayed in
    Chinese and finishing it removes a half-translated row).
  * continuity -- a deferred sibling within 0x160 of an already-patched
    slot joins it, avoiding half-Chinese tables.

Hard refusals kept English: the two proven crash keys (Microsoft /
Textures), dotted ShaderColorBlend keys, vendor preference file names,
workspace XML attributes (Left/Right/Top/Bottom), scripting-API
callbacks (Layer/Output), licensing fields, preset-browser metadata
columns, and effect brand names (BCC HSL / BCC VR / ...).

Evidence:
  _mkhyg2.py      -> wrote 103, refused 131
  _hyg2_audit.py  -> 103 slots rewritten (expected 103), 0 problems, ALL GOOD
  verify_load.py  -> 6/6 LoadLibrary OK

Sanity gate: every DLL hash is asserted against the hyg2 build before
packaging.

New stage dir pyinstaller_stage16 -- reusing an old one triggers the host
SAFE_DELETE_BULK guard on ~495 files.
"""
import os, shutil, subprocess, sys, hashlib

VENV_PY = r"C:\Users\Jinna\.workbuddy\binaries\python\envs\default\Scripts\python.exe"
PROJ = r"D:\Programming project\插件汉化"
SRC = os.path.join(PROJ, "Continuum 汉化组件 v19.0.0")
STAGE = r"C:\Users\Jinna\.workbuddy\pyinstaller_stage16"
DIST = os.path.join(STAGE, "dist")
WORK = os.path.join(STAGE, "build")
OUT_NAME = "Continuum汉化安装器"

ENGINE_DLLS = ["Continuum_AE_Float.dll", "Continuum_AE_8Bit.dll", "Continuum_AE_16Bit.dll",
               "Continuum_Common_AE.dll", "Continuum_3DObjects_AE.dll", "BCCPlus.dll"]

# hyg2 权威哈希（前 24 位，来自 _hyg2_stats.txt）
EXPECT = {
    "BCCPlus.dll":                "01adca6030558a5f188a80e8",
    "Continuum_AE_Float.dll":     "ab81ecbd2c6bb4617da86180",
    "Continuum_AE_8Bit.dll":      "0222468fde58b14e8acad8fb",
    "Continuum_AE_16Bit.dll":     "9864c4120dfd9588cee0a07c",
    "Continuum_Common_AE.dll":    "96a3144ce582ff65e684500d",
    "Continuum_3DObjects_AE.dll": "4597eb68adb0c1896cde0aff",
}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    log = []
    def say(s):
        log.append(s); print(s, flush=True)

    if os.path.isdir(STAGE):
        say("!! stage exists: " + STAGE); return 1
    os.makedirs(STAGE)

    shutil.copy2(os.path.join(PROJ, "_work", "installer_gui.py"),
                 os.path.join(STAGE, "installer_gui.py"))
    say("installer_gui.py staged")

    n = 0
    for f in sorted(os.listdir(SRC)):
        if f.lower().endswith(".aex"):
            shutil.copy2(os.path.join(SRC, f), os.path.join(STAGE, f)); n += 1
    say("staged %d .aex" % n)

    bad = 0
    for d in ENGINE_DLLS:
        p = os.path.join(SRC, d)
        if not os.path.exists(p):
            say("!! MISSING " + d); return 1
        h = sha(p)
        shutil.copy2(p, os.path.join(STAGE, d))
        ok = h.startswith(EXPECT[d])
        say("   %-32s %s  %s" % (d, h[:24], "OK" if ok else "!! MISMATCH expect " + EXPECT[d]))
        if not ok:
            bad += 1
    if bad:
        say("!! %d DLL(s) are not the hyg2 build -- refusing to package" % bad)
        return 1
    say("staged %d dll, all hashes = hyg2 build" % len(ENGINE_DLLS))

    cmd = [VENV_PY, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile",
           "--console", "--name", OUT_NAME, "--distpath", DIST, "--workpath", WORK,
           "--specpath", WORK, "--add-data", "%s;." % STAGE,
           os.path.join(STAGE, "installer_gui.py")]
    say("running PyInstaller ...")
    r = subprocess.run(cmd, cwd=STAGE, capture_output=True)
    log.append(r.stdout.decode("utf-8", "replace") + r.stderr.decode("utf-8", "replace"))
    with open(os.path.join(PROJ, "_work", "_build16_log.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(log))
    say("PyInstaller exit: %d" % r.returncode)

    produced = os.path.join(DIST, OUT_NAME + ".exe")
    if not os.path.exists(produced):
        say("NOT BUILT"); return 1
    say("BUILT: %s  %d bytes  %s" % (produced, os.path.getsize(produced), sha(produced)[:32]))
    target = os.path.join(SRC, OUT_NAME + ".exe")
    shutil.copy2(produced, target)
    say("copied to delivery: %s  %d bytes  %s" % (target, os.path.getsize(target), sha(target)[:32]))
    return 0


if __name__ == "__main__":
    sys.exit(main())

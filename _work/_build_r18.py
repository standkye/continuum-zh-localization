# -*- coding: utf-8 -*-
"""Production build (r18). Payload now lives on C: -- D:\\ root is being swept
by something outside this session, so nothing here is written there.
"""
import hashlib
import os
import shutil
import subprocess
import sys

VENV_PY = r"C:\Users\Jinna\.workbuddy\binaries\python\envs\default\Scripts\python.exe"
SRC = r"D:\Programming project\continuum-zh-localization\_work\installer_gui.py"
PAYLOAD = r"C:\Users\Jinna\.workbuddy\bcc_r18\payload"
OUTDIR = r"C:\Users\Jinna\.workbuddy\bcc_r18"
DELIVERY = r"D:\Programming project\插件汉化\Continuum汉化安装器.exe"
NAME = "Continuum汉化安装器"

EXPECT = {
    "BCCPlus.dll":                "55e2cca985a6aeec501ad31f",
    "Continuum_AE_Float.dll":     "ab81ecbd2c6bb4617da86180",
    "Continuum_AE_8Bit.dll":      "0222468fde58b14e8acad8fb",
    "Continuum_AE_16Bit.dll":     "9864c4120dfd9588cee0a07c",
    "Continuum_Common_AE.dll":    "96a3144ce582ff65e684500d",
    "Continuum_3DObjects_AE.dll": "4597eb68adb0c1896cde0aff",
}

LOG = []


def say(s):
    LOG.append(s)
    print(s, flush=True)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def pick_stage():
    for cand in (r"C:\Users\Jinna\.workbuddy\pyinstaller_stage18",
                 r"C:\Users\Jinna\.workbuddy\pyinstaller_stage18b"):
        if not os.path.isdir(cand):
            return cand
    raise SystemExit("no free stage dir")


def main():
    os.makedirs(OUTDIR, exist_ok=True)

    # ---- payload gate -------------------------------------------------
    files = os.listdir(PAYLOAD)
    aex = [f for f in files if f.lower().endswith(".aex")]
    dll = [f for f in files if f.lower().endswith(".dll")]
    say("payload: aex=%d dll=%d" % (len(aex), len(dll)))
    bad = 0
    for k, v in sorted(EXPECT.items()):
        got = sha(os.path.join(PAYLOAD, k))
        ok = got.startswith(v)
        say("   %-30s %s %s" % (k, got[:24], "OK" if ok else "!! want " + v))
        bad += 0 if ok else 1
    if bad or len(aex) != 488 or len(dll) != 6:
        say("!! payload gate failed")
        return 1

    # ---- stage --------------------------------------------------------
    stage = pick_stage()
    os.makedirs(stage)
    for f in sorted(files):
        if f.lower().endswith((".aex", ".dll")):
            shutil.copy2(os.path.join(PAYLOAD, f), os.path.join(stage, f))
    source = open(SRC, encoding="utf-8").read()
    with open(os.path.join(stage, "installer_gui.py"), "w", encoding="utf-8") as f:
        f.write(source)
    say("stage %s : %d files, source %d bytes sha256 %s"
        % (stage, len(os.listdir(stage)), len(source), sha(SRC)[:24]))

    # ---- build --------------------------------------------------------
    dist = os.path.join(stage, "dist")
    work = os.path.join(stage, "build")
    cmd = [VENV_PY, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile",
           "--console", "--name", NAME, "--distpath", dist, "--workpath", work,
           "--specpath", work, "--add-data", "%s;." % stage,
           os.path.join(stage, "installer_gui.py")]
    say("PyInstaller running ...")
    r = subprocess.run(cmd, cwd=stage, capture_output=True)
    tail = r.stdout.decode("utf-8", "replace") + r.stderr.decode("utf-8", "replace")
    LOG.append(tail[-4000:])
    produced = os.path.join(dist, NAME + ".exe")
    if r.returncode != 0 or not os.path.exists(produced):
        say("!! build failed rc=%d" % r.returncode)
        say(tail[-3000:])
        return 1
    say("built: %d bytes  sha256 %s" % (os.path.getsize(produced), sha(produced)[:32]))

    # ---- verify the archive ------------------------------------------
    from PyInstaller.archive.readers import CArchiveReader
    ar = CArchiveReader(produced)
    toc = getattr(ar, "toc", None) or ar._parse_toc()
    names = sorted(toc.keys() if hasattr(toc, "keys") else toc)
    n_aex = len([n for n in names if n.lower().endswith(".aex")])
    say("archive: %d entries, %d .aex" % (len(names), n_aex))
    ok = n_aex == 488
    for k, v in sorted(EXPECT.items()):
        data = ar.extract(k)
        if isinstance(data, tuple):
            data = data[1]
        got = hashlib.sha256(data).hexdigest()
        good = got.startswith(v)
        say("   %-30s %s %s" % (k, got[:24], "OK" if good else "!! MISMATCH"))
        ok = ok and good

    raw = open(produced, "rb").read()
    for marker in ("汉化 / 还原 工具", "看不懂", "按默认动作继续", "已取消，未做任何改动"):
        hit = marker.encode("utf-8") in raw
        say("   marker %-22s %s" % (marker, "found" if hit else "!! MISSING"))
        ok = ok and hit
    if not ok:
        say("!! production verification failed")
        return 1

    # ---- publish ------------------------------------------------------
    out = os.path.join(OUTDIR, NAME + ".exe")
    shutil.copy2(produced, out)
    say("kept copy: %s  %s" % (out, sha(out)[:32]))
    shutil.copy2(produced, DELIVERY)
    say("delivered: %s  %d bytes  %s"
        % (DELIVERY, os.path.getsize(DELIVERY), sha(DELIVERY)[:32]))
    with open(os.path.join(OUTDIR, "_build18_prod_log.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(LOG))
    say("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())

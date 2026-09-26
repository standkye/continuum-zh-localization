# -*- coding: utf-8 -*-
"""
Continuum 2026 (BCC) Chinese patch - one-click installer.

Design notes (why it looks like this):
  * Single PyInstaller --onefile exe. All 494 patched files ride inside the exe
    itself, so the installer never depends on an external folder being present.
    (IExpress self-extractors delete their temp dir the moment the first script
    process exits, which is exactly what broke the previous attempt.)
  * Re-launch-once for UAC. The exe starts unelevated, asks for elevation,
    then the elevated copy runs and unpacks its OWN payload into its OWN
    _MEIPASS -- so the payload is always reachable.
    Never hand the child a _MEIPASS that the *parent* owns: the parent exits
    right after ShellExecuteW and PyInstaller wipes its temp dir, leaving the
    elevated child pointing at a deleted folder. That is why elevate() clears
    the env var instead of forwarding it.
  * Every file gets its own OK/FAIL line. Swallowing copy errors is what made
    an earlier round silently install only half the patch.
"""

import ctypes
import hashlib
import os
import subprocess
import sys

# ---------------------------------------------------------------- paths

PATCH_ROOT = os.environ.get("CONTINUUM_PATCH_ROOT", "")

CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"
LIB = r"C:\Program Files\BorisFX\ContinuumAE\19\lib"
BAK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"

ENGINE_DLLS = [
    "Continuum_AE_Float.dll",
    "Continuum_AE_8Bit.dll",
    "Continuum_AE_16Bit.dll",
    "Continuum_Common_AE.dll",
    "Continuum_3DObjects_AE.dll",
]

MODE = "install"          # install | restore
QUIET = "/quiet" in sys.argv or "/q" in sys.argv


# ---------------------------------------------------------------- helpers

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def elevate():
    """Re-run this exe elevated.

    The elevated instance re-unpacks the payload itself, so it must NOT
    inherit a _MEIPASS path owned by this (soon-to-die) process -- clear it.
    """
    params = "--elevated"
    if QUIET:
        params += " /quiet"
    if MODE == "restore":
        params += " /restore"
    if PATCH_ROOT and PATCH_ROOT == getattr(sys, "_MEIPASS", ""):
        os.environ.pop("CONTINUUM_PATCH_ROOT", None)
    rc = ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, params,
        os.path.dirname(sys.executable), 1
    )
    # >32 only means "the UAC dialog was shown". Never treat it as consent.
    sys.exit(0 if rc > 32 else 1)


def aftereffects_running():
    try:
        out = subprocess.run(["tasklist", "/NH"], capture_output=True).stdout
    except Exception:
        return False
    return b"afterfx.exe" in out.lower()


def pause(msg="Press Enter to close ..."):
    try:
        input(msg)
    except Exception:
        pass


def ask(prompt):
    try:
        return input(prompt).strip().lower()
    except Exception:
        return ""


# ---------------------------------------------------------------- core

def restore_from_backup():
    print("=" * 64)
    print("  Restore original English BorisFX Continuum files")
    print("=" * 64)
    print()

    if not os.path.isdir(BAK):
        print("[ERROR] Backup folder not found:")
        print("        " + BAK)
        print("        Nothing to restore from.")
        return 2

    fail = 0
    print("[1/2] restoring 6 engine dlls ...")
    for name in ENGINE_DLLS + ["BCCPlus.dll"]:
        src = os.path.join(BAK, name)
        dst = os.path.join(LIB if name in ENGINE_DLLS else CONT, name)
        try:
            with open(src, "rb") as f:
                data = f.read()
            with open(dst, "wb") as f:
                f.write(data)
            if sha256(dst) != sha256(src):
                raise IOError("verification mismatch")
            print("      OK   " + name)
        except Exception as e:
            fail += 1
            print("      FAIL %s  (%s)" % (name, e))

    aex_bak = os.path.join(BAK, "aex")
    print("[2/2] restoring .aex effect shells ...")
    if not os.path.isdir(aex_bak):
        print("      [WARN] no aex backup folder -- skipped")
    else:
        n = 0
        for name in sorted(os.listdir(aex_bak)):
            if not name.lower().endswith(".aex"):
                continue
            src = os.path.join(aex_bak, name)
            dst = os.path.join(CONT, name)
            try:
                with open(src, "rb") as f:
                    data = f.read()
                with open(dst, "wb") as f:
                    f.write(data)
                n += 1
            except Exception as e:
                fail += 1
                print("      FAIL %s  (%s)" % (name, e))
        print("      restored %d .aex files" % n)

    print()
    if fail == 0:
        print("SUCCESS - back to English. Restart After Effects.")
        return 0
    print("%d file(s) FAILED." % fail)
    return 1


def install():
    print("=" * 64)
    print("  BorisFX Continuum 2026 - Chinese patch  v19.0.0")
    print("  effect names + parameter names   (UTF-8)")
    print("=" * 64)
    print()
    print("  source : " + PATCH_ROOT)
    print()

    # --- 0) sanity ------------------------------------------------------
    if not os.path.isdir(PATCH_ROOT):
        print("[ERROR] Patch payload folder not found:")
        print("        " + PATCH_ROOT)
        print("        The Chinese files are packed inside this exe; this")
        print("        message means the exe could not unpack itself.")
        return 2

    aex_src = sorted(f for f in os.listdir(PATCH_ROOT) if f.lower().endswith(".aex"))
    print("  payload: %d .aex + %d engine dll" % (len(aex_src), len(ENGINE_DLLS)))
    print()

    if not os.path.isdir(CONT):
        print("[ERROR] Continuum folder not found:")
        print("        " + CONT)
        print("        Is BorisFX Continuum 2026 (v19) installed?")
        return 2
    if not os.path.isdir(LIB):
        print("[ERROR] Continuum engine folder not found:")
        print("        " + LIB)
        return 2

    # --- 1) AE must be closed -------------------------------------------
    if aftereffects_running():
        print("[ERROR] After Effects is running.")
        print("        Quit After Effects COMPLETELY, then run this again.")
        print("        (A running AE keeps the plugin files locked, which")
        print("         makes the copy fail halfway.)")
        return 3

    # --- 2) backup ------------------------------------------------------
    print("[1/3] backing up original English files ...")
    os.makedirs(os.path.join(BAK, "aex"), exist_ok=True)

    n_bak = 0
    for name in aex_src:
        dst = os.path.join(BAK, "aex", name)
        if os.path.exists(dst):
            continue
        try:
            with open(os.path.join(CONT, name), "rb") as f:
                data = f.read()
            with open(dst, "wb") as f:
                f.write(data)
            n_bak += 1
        except Exception:
            pass
    for name in ENGINE_DLLS:
        dst = os.path.join(BAK, name)
        if os.path.exists(dst):
            continue
        try:
            with open(os.path.join(LIB, name), "rb") as f:
                data = f.read()
            with open(dst, "wb") as f:
                f.write(data)
            n_bak += 1
        except Exception:
            pass
    dst = os.path.join(BAK, "BCCPlus.dll")
    if not os.path.exists(dst):
        try:
            with open(os.path.join(CONT, "BCCPlus.dll"), "rb") as f:
                data = f.read()
            with open(dst, "wb") as f:
                f.write(data)
            n_bak += 1
        except Exception:
            pass

    print("      %d file(s) backed up to" % n_bak)
    print("      " + BAK)
    print()

    # --- 3) install -----------------------------------------------------
    fail = 0

    print("[2/3] installing %d Chinese effect names ..." % len(aex_src))
    for name in aex_src:
        src = os.path.join(PATCH_ROOT, name)
        dst = os.path.join(CONT, name)
        try:
            with open(src, "rb") as f:
                data = f.read()
            with open(dst, "wb") as f:
                f.write(data)
        except Exception as e:
            fail += 1
            print("      FAIL %s  (%s)" % (name, e))
    if fail == 0:
        print("      all %d OK" % len(aex_src))
    print()

    print("[3/3] installing Chinese parameter names ...")
    for name in ENGINE_DLLS + ["BCCPlus.dll"]:
        src = os.path.join(PATCH_ROOT, name)
        dst = os.path.join(LIB if name in ENGINE_DLLS else CONT, name)
        try:
            with open(src, "rb") as f:
                data = f.read()
            with open(dst, "wb") as f:
                f.write(data)
            print("      OK   " + name)
        except Exception as e:
            fail += 1
            print("      FAIL %s  (%s)" % (name, e))

    # --- 4) verify ------------------------------------------------------
    print()
    print("verifying ...")
    bad = 0
    for name in aex_src:
        try:
            if sha256(os.path.join(PATCH_ROOT, name)) != sha256(os.path.join(CONT, name)):
                bad += 1
        except Exception:
            bad += 1
    for name in ENGINE_DLLS + ["BCCPlus.dll"]:
        a = os.path.join(PATCH_ROOT, name)
        b = os.path.join(LIB if name in ENGINE_DLLS else CONT, name)
        try:
            if sha256(a) != sha256(b):
                bad += 1
        except Exception:
            bad += 1

    print()
    print("=" * 64)
    if fail == 0 and bad == 0:
        print("  SUCCESS - everything installed and verified.")
        print("  Start After Effects: effect names and parameter names")
        print("  are now in Chinese.")
        print()
        print("  To go back to English, run this exe with /restore")
        print("  Backup: " + BAK)
    else:
        print("  copy failures: %d    verification failures: %d" % (fail, bad))
        print("  Quit After Effects completely and run again.")
    print("=" * 64)
    return 0 if (fail == 0 and bad == 0) else 1


# ---------------------------------------------------------------- main

def payload_root(exe_dir):
    """Where the patched files live.

    Priority: explicit env (debug) > this process's own unpacked payload >
    the loose files sitting next to the exe.
    """
    env = os.environ.get("CONTINUUM_PATCH_ROOT", "")
    if env and os.path.isdir(env):
        return env
    meipass = getattr(sys, "_MEIPASS", "")
    if meipass and os.path.isdir(meipass):
        try:
            if any(f.lower().endswith(".aex") for f in os.listdir(meipass)):
                return meipass
        except OSError:
            pass
    return exe_dir


def main():
    global PATCH_ROOT, MODE

    if "/restore" in sys.argv:
        MODE = "restore"

    if not PATCH_ROOT:
        if getattr(sys, "frozen", False):
            PATCH_ROOT = payload_root(os.path.dirname(sys.executable))
        else:
            PATCH_ROOT = os.path.dirname(os.path.abspath(__file__))

    if not is_admin():
        print("Requesting administrator rights ...")
        print("Click \"Yes\" on the UAC dialog that just appeared.")
        elevate()
        return

    try:
        rc = restore_from_backup() if MODE == "restore" else install()
    except Exception:
        import traceback
        traceback.print_exc()
        rc = 9

    if not QUIET:
        print()
        pause()
    sys.exit(rc)


if __name__ == "__main__":
    main()

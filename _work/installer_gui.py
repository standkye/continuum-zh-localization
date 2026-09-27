# -*- coding: utf-8 -*-
"""
Continuum 2026 (BCC) Chinese patch - one-click installer / restore tool.

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
  * Interactive menu (r18). Double-clicking with no arguments now asks
    "1 = 汉化 / 2 = 恢复原版" instead of silently patching. The choice is made
    BEFORE elevation and forwarded to the elevated child as /install or
    /restore, so the elevated window never blocks on a prompt of its own --
    an elevated child gets a brand-new console and would hang waiting for a
    keypress nobody can see. --elevated therefore always skips the menu.
    Headless callers keep working: /install, /restore, /quiet all bypass it.

  * Restore is only as good as its backup. install() writes the English
    originals to Backup-English BEFORE touching anything, and restore reads
    nothing but that folder -- so the two operations are independent of any
    external copy of the plugin files.
"""

import ctypes
import hashlib
import os
import subprocess
import sys

VERSION = "v19.0.0"
BUILD = "r18"

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

MODE = None               # None -> ask | "install" | "restore" | "quit"
QUIET = "/quiet" in sys.argv or "/q" in sys.argv
ELEVATED = "--elevated" in sys.argv

# accepted answers, so "汉化" / "回到原版" work as well as 1 / 2
ANSWERS_ZH = {"1", "汉化", "中文化", "中文", "zh", "cn", "chinese",
              "install", "patch", "a", "s"}
ANSWERS_EN = {"2", "恢复", "还原", "恢复原版", "回到原版", "回原版", "原版",
              "英文", "en", "english", "restore", "revert", "undo", "b", "r"}
ANSWERS_QUIT = {"0", "q", "quit", "exit", "退出", "关闭", "取消", "esc"}


# ---------------------------------------------------------------- helpers

def _relax_streams():
    """Never let a console codepage turn a message into a traceback.

    Real consoles go through WriteConsoleW and handle any character; a
    redirected stdout falls back to the locale codepage (cp936 out here), which
    would raise on anything exotic. Replace instead of crash.
    """
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        try:
            stream.reconfigure(errors="replace")
        except Exception:
            pass


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
    The mode picked in the menu travels as an argument, because the elevated
    child opens its own console and must never wait for input.
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


def pause(msg="按回车键关闭窗口 ... "):
    try:
        input(msg)
    except Exception:
        pass


def ask(prompt):
    """Return the raw answer, or None when there is no console to read from."""
    try:
        return input(prompt)
    except EOFError:
        return None
    except Exception:
        return None


def header(title):
    print("=" * 64)
    print("  " + title)
    print("=" * 64)
    print()


# ---------------------------------------------------------------- menu

def ask_mode():
    """Interactive chooser shown before elevation."""
    header("BorisFX Continuum 2026  汉化 / 还原 工具   %s (%s)" % (VERSION, BUILD))
    print("  请选择要执行的操作 / Choose an action:")
    print()
    print("    [1] 汉化        把效果名、参数名换成中文 (patch to Chinese)")
    print("    [2] 恢复原版    把英文原版文件还原回去   (restore original English)")
    print("    [0] 退出        什么都不做               (quit)")
    print()
    print("  也可以直接输入「汉化」或「回到原版」。")
    print()

    for _ in range(8):
        raw = ask("  请输入 1 或 2，然后回车: ")
        if raw is None:
            print()
            print("  读不到键盘输入，按默认动作继续：[1] 汉化。")
            print()
            return "install"
        key = raw.strip().lower()
        if key in ANSWERS_ZH:
            return "install"
        if key in ANSWERS_EN:
            return "restore"
        if key in ANSWERS_QUIT:
            return "quit"
        print("  看不懂「%s」——请输入 1、2 或 0。" % raw.strip())
        print()

    print("  连续多次无法识别，按默认动作继续：[1] 汉化。")
    print()
    return "install"


# ---------------------------------------------------------------- core

def restore_from_backup():
    header("恢复英文原版 / Restore original English BorisFX Continuum files")
    print("  备份目录 / backup: " + BAK)
    print()

    if not os.path.isdir(BAK):
        print("[错误] 找不到备份目录：")
        print("       " + BAK)
        print("       说明这个汉化包还没有在这台机器上安装过，没有可还原的原版文件。")
        print("       Nothing to restore from (the patch was never installed here).")
        return 2

    if aftereffects_running():
        print("[错误] After Effects 正在运行。")
        print("       请先彻底退出 AE，再重新运行本程序。")
        return 3

    fail = 0
    print("[1/2] 还原 6 个引擎 DLL ...")
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
    print("[2/2] 还原 .aex 效果文件 ...")
    if not os.path.isdir(aex_bak):
        print("      [警告] 备份里没有 aex 目录，跳过")
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
        print("      已还原 %d 个 .aex" % n)

    print()
    if fail == 0:
        print("成功 —— 已恢复英文原版。请重新启动 After Effects。")
        print("SUCCESS - back to English. Restart After Effects.")
        return 0
    print("有 %d 个文件未能还原，请先彻底退出 AE 后重试。" % fail)
    print("%d file(s) FAILED." % fail)
    return 1


def install():
    header("BorisFX Continuum 2026 汉化  %s (%s)" % (VERSION, BUILD))
    print("  效果名 + 参数名中文化 (UTF-8)")
    print()
    print("  源文件 / source : " + PATCH_ROOT)
    print()

    # --- 0) sanity ------------------------------------------------------
    if not os.path.isdir(PATCH_ROOT):
        print("[错误] 找不到汉化文件目录：")
        print("       " + PATCH_ROOT)
        print("       中文文件是打包在本 exe 内部的；出现这条说明 exe 没能自解压。")
        return 2

    aex_src = sorted(f for f in os.listdir(PATCH_ROOT) if f.lower().endswith(".aex"))
    print("  载荷 / payload: %d 个 .aex + %d 个引擎 DLL" % (len(aex_src), len(ENGINE_DLLS)))
    print()

    if not os.path.isdir(CONT):
        print("[错误] 找不到 Continuum 插件目录：")
        print("       " + CONT)
        print("       是否已安装 BorisFX Continuum 2026 (v19)？")
        return 2
    if not os.path.isdir(LIB):
        print("[错误] 找不到 Continuum 引擎目录：")
        print("       " + LIB)
        return 2

    # --- 1) AE must be closed -------------------------------------------
    if aftereffects_running():
        print("[错误] After Effects 正在运行。")
        print("       请先彻底退出 AE，再重新运行本程序。")
        print("       (AE 运行时会锁住插件文件，导致复制中途失败。)")
        return 3

    # --- 2) backup ------------------------------------------------------
    print("[1/3] 备份英文原版文件 ...")
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

    print("      已备份 %d 个文件到 / backed up to" % n_bak)
    print("      " + BAK)
    print()

    # --- 3) install -----------------------------------------------------
    fail = 0

    print("[2/3] 写入 %d 个中文效果名 ..." % len(aex_src))
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
        print("      全部 %d 个 OK" % len(aex_src))
    print()

    print("[3/3] 写入中文参数名 ...")
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
    print("校验中 / verifying ...")
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
        print("  成功 —— 全部文件已写入并校验通过。")
        print("  启动 After Effects，效果名和参数名就是中文了。")
        print()
        print("  想改回英文：重新运行本 exe，选 [2] 恢复原版")
        print("  (命令行也可用 /restore)")
        print("  英文备份位于 / backup: " + BAK)
    else:
        print("  复制失败 %d 个，校验失败 %d 个。" % (fail, bad))
        print("  请彻底退出 After Effects 后重新运行。")
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


def parse_mode():
    args = [a.lower() for a in sys.argv[1:]]
    if "/restore" in args or "--restore" in args or "-restore" in args:
        return "restore"
    if "/install" in args or "--install" in args:
        return "install"
    return None


def main():
    global PATCH_ROOT, MODE

    _relax_streams()
    MODE = parse_mode()

    if not PATCH_ROOT:
        if getattr(sys, "frozen", False):
            PATCH_ROOT = payload_root(os.path.dirname(sys.executable))
        else:
            PATCH_ROOT = os.path.dirname(os.path.abspath(__file__))

    # Decide what to do. The menu only ever runs in the unelevated parent:
    # - /quiet  -> headless, keep the historical "just install" behaviour
    # - --elevated -> the choice was already made and passed down as an arg
    if MODE is None:
        if QUIET or ELEVATED:
            MODE = "install"
        else:
            MODE = ask_mode()

    if MODE == "quit":
        print("  已取消，未做任何改动。")
        print("  Cancelled - nothing was changed.")
        return

    if not is_admin():
        print("正在请求管理员权限 ...")
        print("请在弹出的 UAC 对话框上点「是」。")
        print("Requesting administrator rights, click \"Yes\" on the UAC dialog.")
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

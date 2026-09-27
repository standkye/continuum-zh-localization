# -*- coding: utf-8 -*-
"""Sandbox test for the menu-enabled installer.

Loads _work/installer_gui.py as a module, redirects the three install paths
(CONT / LIB / BAK) into a temp sandbox, stubs out admin + AE detection, then
drives main() with scripted keyboard input and inspects what happened on disk.

Nothing here touches the real Continuum installation.
"""
import builtins
import importlib.util
import io
import os
import shutil
import sys
import traceback

SRC = r"D:\Programming project\continuum-zh-localization\_work\installer_gui.py"
SANDBOX = r"C:\Users\Jinna\AppData\Local\Temp\_menutest"
PAYLOAD = os.path.join(SANDBOX, "payload")

FAKE_AEX = ["Alpha.aex", "Beta.aex", "Gamma.aex"]
FAKE_DLL = ["Continuum_AE_Float.dll", "Continuum_AE_8Bit.dll", "Continuum_AE_16Bit.dll",
            "Continuum_Common_AE.dll", "Continuum_3DObjects_AE.dll", "BCCPlus.dll"]

results = []


def check(name, condition, detail=""):
    results.append((name, bool(condition), detail))
    print("  %-52s %s%s" % (name, "PASS" if condition else "FAIL",
                            ("  | " + detail) if detail else ""))


def build_sandbox():
    if os.path.isdir(SANDBOX):
        shutil.rmtree(SANDBOX)
    cont = os.path.join(SANDBOX, "cont")
    lib = os.path.join(SANDBOX, "lib")
    os.makedirs(cont)
    os.makedirs(lib)
    os.makedirs(PAYLOAD)
    # "installed English" files on the fake machine
    for f in FAKE_AEX[:2]:
        open(os.path.join(cont, f), "wb").write(b"EN-ORIGINAL-AEX:" + f.encode())
    open(os.path.join(cont, "BCCPlus.dll"), "wb").write(b"EN-ORIGINAL-BCCPlus")
    for f in FAKE_DLL[:5]:
        open(os.path.join(lib, f), "wb").write(b"EN-ORIGINAL-DLL:" + f.encode())
    # the Chinese payload that would ride inside the exe
    for f in FAKE_AEX:
        open(os.path.join(PAYLOAD, f), "wb").write(b"ZH-PATCHED-AEX:" + f.encode())
    for f in FAKE_DLL:
        open(os.path.join(PAYLOAD, f), "wb").write(b"ZH-PATCHED-DLL:" + f.encode())
    return cont, lib


def load_module():
    spec = importlib.util.spec_from_file_location("ig_test", SRC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Keyboard:
    """Scripted keyboard: yields the queued lines, then empty lines forever."""
    def __init__(self, lines):
        self.lines = list(lines)
        self.prompts = []

    def __call__(self, prompt=""):
        self.prompts.append(prompt)
        if self.lines:
            return self.lines.pop(0)
        return ""


def run(mod, argv, keys=(), eof=False):
    """Drive main(); return (rc_or_None, stdout_text, keyboard)."""
    old_argv = sys.argv
    old_input = builtins.input
    # QUIET / ELEVATED are module-level constants read at import time, so a
    # fresh argv has to be pushed into them explicitly.
    args = [a.lower() for a in argv]
    mod.QUIET = "/quiet" in args or "/q" in args
    mod.ELEVATED = "--elevated" in args
    kb = Keyboard(keys)

    def scripted(prompt=""):
        if eof:
            raise EOFError
        return kb(prompt)

    sys.argv = ["ContinuumHanhua.exe"] + list(argv)
    builtins.input = scripted
    buf = io.StringIO()
    old_out = sys.stdout
    sys.stdout = buf
    rc = "no-exit"
    try:
        mod.main()
    except SystemExit as e:
        rc = e.code
    except Exception:
        rc = "EXC:" + traceback.format_exc().splitlines()[-1]
    finally:
        sys.stdout = old_out
        sys.argv = old_argv
        builtins.input = old_input
    return rc, buf.getvalue(), kb


def read(path):
    try:
        with open(path, "rb") as f:
            return f.read()
    except Exception:
        return None


def main():
    print("=" * 72)
    print("menu installer - sandbox test")
    print("=" * 72)

    cont, lib = build_sandbox()
    mod = load_module()

    # redirect the three real paths into the sandbox
    mod.CONT = cont
    mod.LIB = lib
    mod.BAK = os.path.join(SANDBOX, "backup-english")
    mod.is_admin = lambda: True
    mod.aftereffects_running = lambda: False
    mod.PATCH_ROOT = PAYLOAD

    # ---- 1) menu shows up, "1" installs -------------------------------
    print("\n[1] 双击（无参数）选 1 = 汉化")
    rc, out, kb = run(mod, [], keys=["1"])
    check("菜单被打印", "汉化 / 还原 工具" in out and "[1] 汉化" in out and "[2] 恢复原版" in out)
    check("询问了选择", any("请输入 1 或 2" in p for p in kb.prompts))
    check("执行的是汉化（退出码 0）", rc == 0, "rc=%r" % (rc,))
    check("aex 已替换为中文",
          read(os.path.join(cont, "Alpha.aex")) == b"ZH-PATCHED-AEX:Alpha.aex")
    check("引擎 DLL 已替换为中文",
          read(os.path.join(lib, "Continuum_AE_Float.dll")) == b"ZH-PATCHED-DLL:Continuum_AE_Float.dll")
    check("BCCPlus.dll 写到了插件目录",
          read(os.path.join(cont, "BCCPlus.dll")) == b"ZH-PATCHED-DLL:BCCPlus.dll")
    check("英文原版已备份",
          read(os.path.join(mod.BAK, "aex", "Alpha.aex")) == b"EN-ORIGINAL-AEX:Alpha.aex"
          and read(os.path.join(mod.BAK, "Continuum_AE_Float.dll")) == b"EN-ORIGINAL-DLL:Continuum_AE_Float.dll")

    # ---- 2) "2" restores ---------------------------------------------
    print("\n[2] 再运行选 2 = 恢复原版")
    rc, out, kb = run(mod, [], keys=["2"])
    check("执行的是还原（退出码 0）", rc == 0, "rc=%r" % (rc,))
    check("aex 已还原成英文",
          read(os.path.join(cont, "Alpha.aex")) == b"EN-ORIGINAL-AEX:Alpha.aex")
    check("引擎 DLL 已还原成英文",
          read(os.path.join(lib, "Continuum_AE_Float.dll")) == b"EN-ORIGINAL-DLL:Continuum_AE_Float.dll")
    check("BCCPlus.dll 已还原", read(os.path.join(cont, "BCCPlus.dll")) == b"EN-ORIGINAL-BCCPlus")
    check("提示重启 AE", "Restart After Effects" in out)

    # ---- 3) 中文关键词也能识别 ----------------------------------------
    print("\n[3] 直接输入中文「汉化」/「回到原版」")
    rc, out, kb = run(mod, [], keys=["汉化"])
    check("「汉化」-> install", rc == 0 and read(os.path.join(cont, "Alpha.aex")).startswith(b"ZH-"))
    rc, out, kb = run(mod, [], keys=["回到原版"])
    check("「回到原版」-> restore", rc == 0 and read(os.path.join(cont, "Alpha.aex")).startswith(b"EN-"))

    # ---- 4) 输入 0 退出，不动任何文件 ---------------------------------
    print("\n[4] 输入 0 = 退出")
    rc, out, kb = run(mod, [], keys=["0"])
    check("退出返回 None（没有 sys.exit）", rc == "no-exit", "rc=%r" % (rc,))
    check("提示未做改动", "未做任何改动" in out)
    check("文件保持原样", read(os.path.join(cont, "Alpha.aex")).startswith(b"EN-"))

    # ---- 5) 无效输入后重试 -------------------------------------------
    print("\n[5] 先乱输再选 1")
    rc, out, kb = run(mod, [], keys=["随便", "3", "1"])
    check("提示无法识别", "看不懂" in out)
    check("最终仍执行汉化", rc == 0 and read(os.path.join(cont, "Alpha.aex")).startswith(b"ZH-"))

    # ---- 6) 无键盘输入时走默认 ---------------------------------------
    print("\n[6] 读不到键盘（EOF）")
    rc, out, kb = run(mod, [], eof=True)
    check("按默认汉化继续", rc == 0 and "按默认动作继续" in out)

    # ---- 7) /restore /quiet 不弹菜单 ---------------------------------
    print("\n[7] 命令行参数仍然直接生效、不弹菜单")
    rc, out, kb = run(mod, ["/restore"])
    check("/restore 直接还原", rc == 0 and read(os.path.join(cont, "Alpha.aex")).startswith(b"EN-"))
    check("/restore 没问菜单", not any("请输入 1 或 2" in p for p in kb.prompts))
    rc, out, kb = run(mod, ["/quiet"])
    check("/quiet 静默汉化", rc == 0 and read(os.path.join(cont, "Alpha.aex")).startswith(b"ZH-"))
    check("/quiet 没问菜单", not kb.prompts)

    # ---- 8) 没装过就还原 -> 明确报错 ---------------------------------
    print("\n[8] 没有备份时还原")
    shutil.move(mod.BAK, mod.BAK + "_hidden")
    rc, out, kb = run(mod, ["/restore"])
    check("给出「没有可还原文件」的提示", "找不到备份目录" in out, "rc=%r" % (rc,))
    shutil.move(mod.BAK + "_hidden", mod.BAK)

    # ---- 9) AE 在跑时 -> 拦住 ---------------------------------------
    print("\n[9] After Effects 在运行时")
    mod.aftereffects_running = lambda: True
    rc, out, kb = run(mod, ["/install"])
    check("汉化被拦住并提示退出 AE", "After Effects 正在运行" in out, "rc=%r" % (rc,))
    rc, out, kb = run(mod, ["/restore"])
    check("还原也被拦住并提示退出 AE", "After Effects 正在运行" in out, "rc=%r" % (rc,))
    mod.aftereffects_running = lambda: False

    # ---- summary ------------------------------------------------------
    passed = sum(1 for _, ok, _ in results if ok)
    print("\n" + "=" * 72)
    print("结果: %d/%d PASS" % (passed, len(results)))
    failed = [n for n, ok, _ in results if not ok]
    if failed:
        print("失败项:")
        for n in failed:
            print("  - " + n)
    print("=" * 72)
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())

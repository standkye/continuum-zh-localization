# -*- coding: utf-8 -*-
"""End-to-end test of the FROZEN test build (_test18.exe).

The test build has CONT/LIB/BAK rewritten to a sandbox and admin/AE checks
stubbed, so we can drive the real onefile binary with real keystrokes and watch
what it does to disk -- without going anywhere near the user's Continuum.

Sandbox files are the real payload with b"EN" appended, so "did the swap
happen" is decidable byte-for-byte.
"""
import hashlib
import os
import shutil
import subprocess
import sys

EXE = r"C:\Users\Jinna\.workbuddy\bcc_r18\_test18.exe"
PAYLOAD = r"C:\Users\Jinna\.workbuddy\bcc_r18\payload"
SB = r"C:\Users\Jinna\AppData\Local\Temp\_menutest"
CONT = os.path.join(SB, "cont")
LIB = os.path.join(SB, "lib")
BAK = os.path.join(SB, "backup-english")

ENGINE = ["Continuum_AE_Float.dll", "Continuum_AE_8Bit.dll", "Continuum_AE_16Bit.dll",
          "Continuum_Common_AE.dll", "Continuum_3DObjects_AE.dll"]
TAG = b"EN"

results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print("  %-50s %s%s" % (name, "PASS" if cond else "FAIL", ("  | " + detail) if detail else ""))


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def build_sandbox():
    if os.path.isdir(SB):
        shutil.rmtree(SB)
    os.makedirs(CONT)
    os.makedirs(LIB)
    aex = [f for f in os.listdir(PAYLOAD) if f.lower().endswith(".aex")]
    for f in aex:
        with open(os.path.join(PAYLOAD, f), "rb") as s, open(os.path.join(CONT, f), "wb") as d:
            d.write(s.read() + TAG)
    for f in ENGINE:
        with open(os.path.join(PAYLOAD, f), "rb") as s, open(os.path.join(LIB, f), "wb") as d:
            d.write(s.read() + TAG)
    with open(os.path.join(PAYLOAD, "BCCPlus.dll"), "rb") as s, open(os.path.join(CONT, "BCCPlus.dll"), "wb") as d:
        d.write(s.read() + TAG)
    return len(aex)


def run_exe(answer, timeout=420):
    inp = (answer + "\n").encode("ascii") + b"\n\n\n"
    p = subprocess.run([EXE], input=inp, capture_output=True, timeout=timeout)
    out = p.stdout.decode("utf-8", "replace")
    if "\ufffd" in out:
        out = p.stdout.decode("gbk", "replace")
    return p.returncode, out


def compare_dir(disk_dir, payload_dir, expected_tag, names):
    """All files must match payload+tag (or payload exactly when tag is b'')."""
    bad = []
    for f in names:
        with open(os.path.join(payload_dir, f), "rb") as fh:
            want = fh.read() + expected_tag
        try:
            with open(os.path.join(disk_dir, f), "rb") as fh:
                got = fh.read()
        except Exception as e:
            bad.append((f, "unreadable %s" % e))
            continue
        if got != want:
            bad.append((f, "len %d vs %d" % (len(got), len(want))))
    return bad


def main():
    print("=" * 72)
    print("frozen-exe end-to-end test:", EXE)
    print("=" * 72)

    aex = [f for f in os.listdir(PAYLOAD) if f.lower().endswith(".aex")]
    all_dll = ENGINE + ["BCCPlus.dll"]
    n = build_sandbox()
    print("\nsandbox: %d aex + %d dll originals marked with %r" % (n, len(all_dll), TAG))

    # ---------------- install ----------------
    print("\n[1] 运行 _test18.exe，输入 1（汉化）")
    rc, out = run_exe("1")
    check("进程正常结束 (rc=0)", rc == 0, "rc=%d" % rc)
    check("打印了菜单", "汉化 / 还原 工具" in out)
    check("汉化成功提示", "成功 —— 全部文件已写入并校验通过" in out)
    check("校验 0 失败", "校验失败 0" not in out)

    bad = compare_dir(CONT, PAYLOAD, b"", aex)
    check("488 个 aex 全部换成中文版（逐字节）", not bad, "%d bad: %s" % (len(bad), bad[:3]))
    bad = compare_dir(LIB, PAYLOAD, b"", ENGINE)
    check("5 个引擎 DLL 换成中文版", not bad, str(bad[:3]))
    bad = compare_dir(CONT, PAYLOAD, b"", ["BCCPlus.dll"])
    check("BCCPlus.dll 换成中文版", not bad, str(bad[:3]))

    bad = compare_dir(os.path.join(BAK, "aex"), PAYLOAD, TAG, aex)
    check("488 个英文原版已备份到 Backup-English\\aex", not bad, "%d bad" % len(bad))
    bad = compare_dir(BAK, PAYLOAD, TAG, all_dll)
    check("7 个 DLL 英文原版已备份", not bad, str(bad[:3]))

    # ---------------- restore ----------------
    print("\n[2] 再运行 _test18.exe，输入 2（恢复原版）")
    rc, out = run_exe("2")
    check("进程正常结束 (rc=0)", rc == 0, "rc=%d" % rc)
    check("打印了还原标题", "恢复英文原版" in out)
    check("还原成功提示", "SUCCESS - back to English" in out)

    bad = compare_dir(CONT, PAYLOAD, TAG, aex)
    check("488 个 aex 已还原成英文", not bad, "%d bad: %s" % (len(bad), bad[:3]))
    bad = compare_dir(LIB, PAYLOAD, TAG, ENGINE)
    check("5 个引擎 DLL 已还原成英文", not bad, str(bad[:3]))
    bad = compare_dir(CONT, PAYLOAD, TAG, ["BCCPlus.dll"])
    check("BCCPlus.dll 已还原成英文", not bad, str(bad[:3]))

    # ---------------- quit ----------------
    print("\n[3] 运行 _test18.exe，输入 0（退出）")
    rc, out = run_exe("0")
    check("提示未做改动", "未做任何改动" in out, "rc=%s" % rc)

    passed = sum(1 for _, ok, _ in results if ok)
    print("\n" + "=" * 72)
    print("结果: %d/%d PASS" % (passed, len(results)))
    for name, ok, _ in results:
        if not ok:
            print("  FAILED: " + name)
    print("=" * 72)
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())

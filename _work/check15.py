# -*- coding: utf-8 -*-
"""Check: for the 15 skipped slots, is the string a standalone NUL-terminated
slot at that offset, or a fragment of a longer string?"""
import json, os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

W = r"D:\Programming project\插件汉化\_work"
LIB = r"C:\Program Files\BorisFX\ContinuumAE\19\lib"
CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"

ch = json.load(open(os.path.join(W, "dll_chains.json"), encoding="utf-8"))
pz = json.load(open(os.path.join(W, "param_zh.json"), encoding="utf-8"))
for e in ("hand_all.json", "hand_other.json", "hand_other2.json"):
    pz.update(json.load(open(os.path.join(W, e), encoding="utf-8")))

TARGETS = ["Use Alpha", "Pin", "Hue", "Alpha", "Opacity FX", "Cam Pos XY",
           "Cam Pos Z", "Cam Spin", "Map", "Alpha Mix", "FG Opacity",
           "BG Opacity", "Use Map Alpha", "End Opacity", "Boost MB"]

for name, base in (("Continuum_AE_8Bit.dll", LIB), ("BCCPlus.dll", CONT)):
    path = os.path.join(base, name)
    if not os.path.exists(path):
        continue
    d = open(path, "rb").read()
    print("==== %s ====" % name)
    for off_s, arr in ch.get(name, {}).items():
        cur = int(off_s)
        for s in arr:
            slot = max(8, ((len(s) + 1 + 7) // 8) * 8)
            if s in TARGETS:
                tail = d[cur + len(s):cur + slot]
                before = d[cur - 1] if cur > 0 else 0
                zh = pz.get(s)
                print("  %-14s off=%-10d slot=%-3d before=%3d tail=%s  zh=%s"
                      % (s, cur, slot, before, list(tail[:8]), zh))
            cur += slot
    print()

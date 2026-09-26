# -*- coding: utf-8 -*-
"""Verify the patched DLLs: read back the Chinese for a sample of strings."""
import json, os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

W = r"D:\Programming project\插件汉化\_work"
PD = os.path.join(W, "patched_dll")
ch = json.load(open(os.path.join(W, "dll_chains.json"), encoding="utf-8"))
pz = json.load(open(os.path.join(W, "param_zh.json"), encoding="utf-8"))
for e in ("hand_all.json", "hand_other.json", "hand_other2.json"):
    pz.update(json.load(open(os.path.join(W, e), encoding="utf-8")))

name = "Continuum_AE_8Bit.dll"
d = open(os.path.join(PD, name), "rb").read()

TARGETS = ["Use Alpha", "Pin", "Hue", "Alpha", "Opacity FX", "Cam Pos XY",
           "Cam Pos Z", "Cam Spin", "Map", "Alpha Mix", "FG Opacity",
           "BG Opacity", "Use Map Alpha", "End Opacity", "Boost MB",
           "Opacity", "Position XY", "Radius", "Brightness"]

for off_s, arr in ch[name].items():
    cur = int(off_s)
    for s in arr:
        slot = max(8, ((len(s) + 1 + 7) // 8) * 8)
        if s in TARGETS:
            raw = d[cur:cur + slot]
            txt = raw.split(b"\x00")[0]
            try:
                dec = txt.decode("gbk")
            except UnicodeDecodeError:
                dec = "<%s>" % txt
            print("  %-14s slot=%-3d -> %r   (want %s)"
                  % (s, slot, dec, pz.get(s, "-")))
        cur += slot

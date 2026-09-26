# -*- coding: utf-8 -*-
"""Targeted probe: are the things the user complained about actually translated?"""
import os, json, re

WORK = r"D:\Programming project\插件汉化\_work"
PATCHED = os.path.join(WORK, "patched_dll")
BAK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
pz = json.load(open(os.path.join(WORK, "param_zh.json"), encoding="utf-8"))

DLLS = ["Continuum_AE_8Bit.dll", "Continuum_AE_Float.dll", "Continuum_AE_16Bit.dll",
        "Continuum_Common_AE.dll", "Continuum_3DObjects_AE.dll", "BCCPlus.dll"]

q_gbk = lambda s: s.encode("gbk")

print("=== 1) is 'Match Move' (group header) present + translated? ===")
for d in DLLS:
    po = open(os.path.join(PATCHED, d), "rb").read()
    bo = open(os.path.join(BAK, d), "rb").read()
    print("  %-30s patched has EN 'Match Move': %s | has CN 运动匹配: %s | orig has EN: %s"
          % (d, b"Match Move\x00" in po, q_gbk("运动匹配") in po, b"Match Move\x00" in bo))

print()
print("=== 2) Channel Blur style params ===")
probe = ["Channel Blur", "Blur Red", "Blur Green", "Blur Blue", "Blur Alpha",
         "Red Blur", "Green Blur", "Blue Blur", "Alpha Blur", "Blur Amount",
         "Blur X", "Blur Y", "Matte Blur", "Clip Black", "Clip White"]
for p in probe:
    zh = pz.get(p, "<not in dict>")
    print("  %-16s -> %-18s" % (p, zh))

print()
print("=== 3) how many param_zh entries never landed in ANY patched dll? ===")
patched_data = {d: open(os.path.join(PATCHED, d), "rb").read() for d in DLLS}
orig_data = {d: open(os.path.join(BAK, d), "rb").read() for d in DLLS}

never_zh, not_in_any = [], []
for en, zh in pz.items():
    try:
        zb = zh.encode("gbk")
    except Exception:
        never_zh.append((en, zh, "gbk fail")); continue
    if not any(zb in v for v in patched_data.values()):
        # did it exist in english in the originals?
        eb = en.encode("latin-1") + b"\x00"
        existed = any(eb in v for v in orig_data.values())
        never_zh.append((en, zh, "existed" if existed else "absent"))
print("never applied: %d / %d" % (len(never_zh), len(pz)))
for en, zh, why in never_zh[:60]:
    print("  %-44s -> %-24s (%s)" % (en, zh, why))

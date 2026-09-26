# -*- coding: utf-8 -*-
import json, os, re

WORK = r"D:\Programming project\插件汉化\_work"

ef = json.load(open(os.path.join(WORK, "effect_zh.json"), encoding="utf-8"))
print("effect_zh type:", type(ef).__name__, "len:", len(ef))
if isinstance(ef, dict):
    items = list(ef.items())
else:
    items = [(d.get("en"), d.get("zh")) for d in ef]

print()
print("=== ALL 488 effect translations ===")
for e, z in items:
    print("%-52s -> %s" % (e, z))

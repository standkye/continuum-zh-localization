# -*- coding: utf-8 -*-
import json, os, re

WORK = r"D:\Programming project\插件汉化\_work"
BAK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"

chains = json.load(open(os.path.join(WORK, "dll_chains.json"), encoding="utf-8"))
d0 = list(chains)[0]
ch = chains[d0]
print("--- dll_chains[%s]: dict len=%d ---" % (d0, len(ch)))
ks = list(ch)[:3]
for k in ks:
    print("  key:", repr(k), "->", str(ch[k])[:300])
print()

target = b"Match Move\x00"
for dll in ["Continuum_AE_8Bit.dll", "BCCPlus.dll", "Continuum_AE_Float.dll"]:
    data = open(os.path.join(BAK, dll), "rb").read()
    print("=== %s ===" % dll)
    hits = list(re.finditer(re.escape(target), data))
    print("  occurrences:", len(hits))
    for m in hits[:6]:
        s = m.start()
        slen = len(target)
        slot = max(8, -(-slen // 8) * 8)
        print("  off=0x%x slot=%d pad=%r nxt=%r"
              % (s, slot, data[s+slen:s+slot], data[s+slot:s+slot+16]))

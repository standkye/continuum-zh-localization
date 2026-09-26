# -*- coding: utf-8 -*-
"""Diagnose what the current patch actually looks like:
   1. effect names  (PiPL 'eman')
   2. category names (PiPL 'gtac')  <- user says these are still English
   3. how many params are still English
"""
import json, os, re, struct, collections

PROJ = r"D:\Programming project\插件汉化"
WORK = os.path.join(PROJ, "_work")

def read_records(data):
    """Yield (key, value_bytes) for each PiPL record."""
    out = []
    i = 0
    while True:
        j = data.find(b"MIB8", i)
        if j < 0:
            break
        key = data[j+4:j+8]
        size = struct.unpack("<I", data[j+12:j+16])[0]
        val = data[j+16:j+16+size]
        out.append((key, val, j))
        i = j + 4
    return out

def strval(val):
    if not val:
        return ""
    n = val[0]
    s = val[1:1+n]
    return s.split(b"\x00")[0].decode("latin-1")

# ---- 1 & 2 : scan the ORIGINAL aex backup to know what names/categories exist
BAK_AEX = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English\aex"
if not os.path.isdir(BAK_AEX):
    BAK_AEX = None

cats = collections.Counter()
names = []
if BAK_AEX:
    for f in sorted(os.listdir(BAK_AEX)):
        if not f.lower().endswith(".aex"):
            continue
        data = open(os.path.join(BAK_AEX, f), "rb").read()
        for key, val, off in read_records(data):
            if key == b"eman":
                names.append(strval(val).strip())
            elif key == b"gtac":
                cats[strval(val).strip()] += 1

print("=== CATEGORY (gtac) values found on disk - %d distinct ===" % len(cats))
for c, n in cats.most_common(60):
    print("  %-40s x%d" % (repr(c), n))

print()
print("=== effect names sample ===")
print(names[:15])

# ---- 3 : param translation coverage
pz = json.load(open(os.path.join(WORK, "param_zh.json"), encoding="utf-8"))
print()
print("param_zh.json type:", type(pz).__name__, "len:", len(pz))
if isinstance(pz, dict):
    items = list(pz.items())
elif isinstance(pz, list):
    items = [(d.get("en"), d.get("zh")) for d in pz]
else:
    items = []

def has_cjk(s):
    return bool(re.search(r"[\u4e00-\u9fff]", s or ""))

untranslated = [(e, z) for e, z in items if not has_cjk(z or "")]
print("total params:", len(items), " still fully-English:", len(untranslated))

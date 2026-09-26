# -*- coding: utf-8 -*-
"""Check the manual name table: coverage + whether each fits its byte budget."""
import os, struct, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from names_manual import NAMES, CATS, KEEP_LATIN

BAK_AEX = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English\aex"

def read_records(data):
    out, i = [], 0
    while True:
        j = data.find(b"MIB8", i)
        if j < 0: break
        key = data[j+4:j+8]
        size = struct.unpack("<I", data[j+12:j+16])[0]
        out.append((key, data[j+16:j+16+size], size, j))
        i = j + 4
    return out

def strval(val):
    if not val: return ""
    return val[1:1+val[0]].split(b"\x00")[0].decode("latin-1")

names, cats = {}, {}
for f in sorted(os.listdir(BAK_AEX)):
    if not f.lower().endswith(".aex"): continue
    data = open(os.path.join(BAK_AEX, f), "rb").read()
    for key, val, size, off in read_records(data):
        s = strval(val).strip()
        if key == b"eman":
            names.setdefault(s, []).append((f, size - 2))
        elif key == b"gtac":
            cats.setdefault(s, []).append((f, size - 2))

def gbk_len(s):
    try:
        return len(s.encode("gbk"))
    except UnicodeEncodeError:
        return -1

print("=== EFFECT NAMES ===")
missing, over = [], []
for en, files in sorted(names.items()):
    zh = NAMES.get(en)
    if zh is None:
        missing.append(en); continue
    n = gbk_len(zh)
    if n < 0:
        print("  !! GBK-encodable fail:", en, "->", zh); continue
    budget = min(b for _, b in files)
    if n > budget:
        over.append((en, zh, n, budget))
print("total %d | missing %d | over budget %d" % (len(names), len(missing), len(over)))
for en in missing: print("  MISSING:", en)
for en, zh, n, b in over: print("  OVER: %-46s %s  %d > %d" % (en, zh, n, b))

print()
print("=== CATEGORIES ===")
cmiss, cover = [], []
for en, files in sorted(cats.items()):
    zh = CATS.get(en)
    if zh is None:
        cmiss.append(en); continue
    n = gbk_len(zh)
    budget = min(b for _, b in files)
    if n > budget:
        cover.append((en, zh, n, budget))
print("total %d | missing %d | over budget %d" % (len(cats), len(cmiss), len(cover)))
for en in cmiss: print("  MISSING:", en)
for en, zh, n, b in cover: print("  OVER: %-24s %s  %d > %d" % (en, zh, n, b))

# any leftover Latin in the Chinese results?
print()
print("=== leftover Latin (excluding legit abbreviations) ===")
for en, zh in sorted(NAMES.items()):
    for m in re.findall(r"[A-Za-z][A-Za-z0-9\.\-/']*", zh):
        if m not in KEEP_LATIN:
            print("  %-46s -> %s   [%s]" % (en, zh, m))
for en, zh in sorted(CATS.items()):
    for m in re.findall(r"[A-Za-z][A-Za-z0-9\.\-/']*", zh):
        if m not in KEEP_LATIN:
            print("  CAT %-24s -> %s   [%s]" % (en, zh, m))

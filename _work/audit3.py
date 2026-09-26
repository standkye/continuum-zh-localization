# -*- coding: utf-8 -*-
import json, os, re, struct, collections

WORK = r"D:\Programming project\插件汉化\_work"
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

# ---------- categories with byte budget ----------
catbudget = {}
namebudget = {}
for f in sorted(os.listdir(BAK_AEX)):
    if not f.lower().endswith(".aex"): continue
    data = open(os.path.join(BAK_AEX, f), "rb").read()
    for key, val, size, off in read_records(data):
        s = strval(val).strip()
        if key == b"gtac":
            catbudget.setdefault(s, set()).add(size - 2)
        elif key == b"eman":
            namebudget.setdefault(s, set()).add(size - 2)

print("=== CATEGORIES: available bytes (GBK: 2 bytes/char) ===")
for c in sorted(catbudget, key=lambda x: -len(x)):
    b = sorted(catbudget[c])
    print("  %-26s  len=%2d  avail=%s  -> max %d CJK chars" %
          (c, len(c), b, min(b)//2))

# ---------- effect name leftovers ----------
ef = json.load(open(os.path.join(WORK, "effect_zh.json"), encoding="utf-8"))
items = list(ef.items()) if isinstance(ef, dict) else [(d.get("en"), d.get("zh")) for d in ef]

def zh_of(v):
    return v[0][1] if isinstance(v, list) else v

bad = []
for e, v in items:
    z = zh_of(v)
    if re.search(r"[A-Za-z]{2,}", z):
        bad.append((e, z))
print()
print("=== effect names still containing Latin letters: %d ===" % len(bad))
for e, z in bad:
    print("  %-46s -> %s" % (e, z))

# ---------- find the phrase the user complained about ----------
print()
print("=== search for '生成阿尔法键控' ===")
for e, v in items:
    z = zh_of(v)
    if "生成" in z or "键控" in z and "阿尔法" in z:
        print("  %-46s -> %s" % (e, z))

# ---------- param coverage ----------
pz = json.load(open(os.path.join(WORK, "param_zh.json"), encoding="utf-8"))
pitems = list(pz.items()) if isinstance(pz, dict) else []
def has_cjk(s): return bool(re.search(r"[\u4e00-\u9fff]", s or ""))
leftover = [(e, z) for e, z in pitems if re.search(r"[A-Za-z]{2,}", z or "")]
print()
print("=== params whose translation still has Latin letters: %d / %d ===" % (len(leftover), len(pitems)))
for e, z in leftover[:80]:
    print("  %-42s -> %s" % (e, z))

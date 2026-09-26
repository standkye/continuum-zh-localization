# -*- coding: utf-8 -*-
"""Dump everything that needs a human-quality translation."""
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

name_files = collections.defaultdict(list)
name_budget = {}
cat_files = collections.defaultdict(list)
cat_budget = {}

for f in sorted(os.listdir(BAK_AEX)):
    if not f.lower().endswith(".aex"): continue
    data = open(os.path.join(BAK_AEX, f), "rb").read()
    for key, val, size, off in read_records(data):
        s = strval(val).strip()
        if key == b"eman":
            name_files[s].append(f)
            name_budget.setdefault(s, set()).add(size - 2)
        elif key == b"gtac":
            cat_files[s].append(f)
            cat_budget.setdefault(s, set()).add(size - 2)

out = []
out.append("### EFFECT NAMES (%d unique) ###" % len(name_files))
for s in sorted(name_files):
    b = min(name_budget[s])
    out.append("%d\t%s\t%s" % (b, s, ",".join(name_files[s])[:60]))
out.append("")
out.append("### CATEGORIES (%d unique) ###" % len(cat_files))
for s in sorted(cat_files):
    b = min(cat_budget[s])
    out.append("%d\t%s" % (b, s))

# param leftover tokens
pz = json.load(open(os.path.join(WORK, "param_zh.json"), encoding="utf-8"))
items = list(pz.items()) if isinstance(pz, dict) else []
leftover = [(e, z) for e, z in items if re.search(r"[A-Za-z]{2,}", z or "")]
tok = collections.Counter()
for e, z in leftover:
    for m in re.findall(r"[A-Za-z][A-Za-z\.\-/']*", z):
        tok[m] += 1
out.append("")
out.append("### PARAM leftover tokens (%d distinct, from %d params) ###" % (len(tok), len(leftover)))
for t, n in tok.most_common():
    out.append("%d\t%s" % (n, t))

open(os.path.join(WORK, "todo_list.txt"), "w", encoding="utf-8").write("\n".join(out))
print("written todo_list.txt")
print("names:", len(name_files), "cats:", len(cat_files), "param tokens:", len(tok))

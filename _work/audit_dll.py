# -*- coding: utf-8 -*-
"""Scan the PATCHED engine DLLs and list any label-looking English strings
that survived, plus report which param_zh entries never landed."""
import os, re, json, collections, struct

WORK = r"D:\Programming project\插件汉化\_work"
PATCHED = os.path.join(WORK, "patched_dll")
pz = json.load(open(os.path.join(WORK, "param_zh.json"), encoding="utf-8"))

def slot_strings(data):
    """8-byte-aligned NUL-terminated slot chain scanner."""
    out = []
    n = len(data)
    for m in re.finditer(rb"[ -~]{2,}\x00", data):
        s = m.start()
        slen = len(m.group())          # includes the NUL
        slot = max(8, -(-slen // 8) * 8)
        end = s + slot
        if end > n: continue
        if any(b != 0 for b in data[s + slen:end]):
            continue
        out.append((s, m.group()[:-1].decode("latin-1"), slot))
    return out

files = sorted(f for f in os.listdir(PATCHED) if f.lower().endswith(".dll"))
print("patched dll files:", files)

all_eng = collections.Counter()
all_zh = set()
for f in files:
    data = open(os.path.join(PATCHED, f), "rb").read()
    strings = slot_strings(data)
    print("%-32s slots=%d" % (f, len(strings)))
    for off, s, slot in strings:
        if re.search(r"[\u4e00-\u9fff]", s):
            continue
        # label-looking English that survived
        if not (2 <= len(s) <= 40): continue
        if not re.match(r"^[A-Za-z][A-Za-z0-9 \-\./'\(\)%&,:\+]*$", s): continue
        if not re.search(r"[A-Za-z]{2,}", s): continue
        if "_" in s: continue
        letters = sum(c.isalpha() for c in s)
        if letters < len(s) * 0.6: continue
        all_eng[s] += 1

print()
print("=== English labels surviving in patched DLLs: %d distinct ===" % len(all_eng))
for s, n in sorted(all_eng.items()):
    in_dict = "IN-DICT" if s in pz else "--not-in-dict--"
    print("  x%-4d %-46s %s" % (n, s, in_dict))

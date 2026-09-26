# -*- coding: utf-8 -*-
"""Find label-looking DLL strings that never got translated."""
import json, os, re, collections

WORK = r"D:\Programming project\插件汉化\_work"
chains = json.load(open(os.path.join(WORK, "dll_chains.json"), encoding="utf-8"))
pz = json.load(open(os.path.join(WORK, "param_zh.json"), encoding="utf-8"))
covered = set(pz.keys())

# collect every string from every chain of every dll
allstr = collections.Counter()
for dll, chs in chains.items():
    for ch in chs:
        for s in (ch if isinstance(ch, list) else [ch]):
            if isinstance(s, str):
                allstr[s] += 1

print("distinct strings in chains:", len(allstr))
print("param_zh covers:", len(covered))

def looks_like_label(s):
    if not (2 <= len(s) <= 40): return False
    if not re.match(r"^[A-Za-z0-9][A-Za-z0-9 \-\./'\(\)%&,:\+]*$", s): return False
    if not re.search(r"[A-Za-z]{2,}", s): return False
    # internal ids / code-ish
    if "_" in s or s.startswith("gl") or s.startswith("rlm"): return False
    if s.isdigit(): return False
    if s.lower().startswith("bcc-"): return False
    if "/" in s and " " not in s: return False     # e.g. paths, mime-ish
    if re.match(r"^[a-z]+$", s) and len(s) < 6: return False
    # must contain a letter and mostly letters/spaces
    letters = sum(c.isalpha() for c in s)
    if letters < len(s) * 0.6: return False
    return True

miss = collections.Counter()
for s, n in allstr.items():
    if s in covered: continue
    if looks_like_label(s):
        miss[s] = n

print()
print("=== label-looking strings NOT in param_zh: %d ===" % len(miss))
for s, n in sorted(miss.items()):
    print("  %d  %s" % (n, s))

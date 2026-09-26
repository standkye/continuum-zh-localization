# -*- coding: utf-8 -*-
"""Correctly list DLL chain strings that the preset-derived dict does NOT cover."""
import json, os, re, collections

WORK = r"D:\Programming project\插件汉化\_work"
chains = json.load(open(os.path.join(WORK, "dll_chains.json"), encoding="utf-8"))
pz = json.load(open(os.path.join(WORK, "param_zh.json"), encoding="utf-8"))
covered = set(pz.keys())

allstr = collections.Counter()
where = collections.defaultdict(set)
for dll, chmap in chains.items():
    for off, lst in chmap.items():          # chmap: offset -> [strings]
        for s in lst:
            if isinstance(s, str):
                allstr[s] += 1
                where[s].add(dll)

print("distinct chain strings:", len(allstr))
print("covered by param_zh  :", len([s for s in allstr if s in covered]))
print("NOT covered          :", len([s for s in allstr if s not in covered]))
print()
print("'Match Move' in chains?", "Match Move" in allstr, "| in dict?", "Match Move" in covered)
print("'Channel Blur' in chains?", "Channel Blur" in allstr)

def junk(s):
    if len(s) < 3: return True
    if not re.search(r"[A-Za-z]{3,}", s): return True
    if re.match(r"^[\d\.\-]+$", s): return True
    if "_" in s: return True
    if re.match(r"^(gl|GL_|rlm|bcc-|BCC_|com\.)", s): return True
    if "://" in s or ".dll" in s or ".exe" in s or ".txt" in s: return True
    if re.search(r"[{}<>;=\\]", s): return True
    if len(s) > 44: return True
    if re.match(r"^[a-f0-9]{8,}$", s): return True
    if re.match(r"^[a-z]+$", s) and " " not in s and len(s) < 12: return True
    return False

notcov = sorted(s for s in allstr if s not in covered and not junk(s))
print()
print("=== plausible UI strings NOT covered: %d ===" % len(notcov))
for s in notcov:
    mark = "  <<< Match Move" if s == "Match Move" else ""
    print("  %-46s %s%s" % (s, ",".join(sorted(where[s]))[:34], mark))

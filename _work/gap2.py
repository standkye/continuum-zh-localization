# -*- coding: utf-8 -*-
"""Real param/group labels are shared by Float/8Bit/16Bit. Use that to filter."""
import json, os, re, collections

WORK = r"D:\Programming project\插件汉化\_work"
chains = json.load(open(os.path.join(WORK, "dll_chains.json"), encoding="utf-8"))
pz = json.load(open(os.path.join(WORK, "param_zh.json"), encoding="utf-8"))
covered = set(pz.keys())

MAIN = ["Continuum_AE_Float.dll", "Continuum_AE_8Bit.dll", "Continuum_AE_16Bit.dll"]
where = collections.defaultdict(set)
for dll, chmap in chains.items():
    for off, lst in chmap.items():
        for s in lst:
            if isinstance(s, str):
                where[s].add(dll)

def junk(s):
    if len(s) < 3: return True
    if not re.search(r"[A-Za-z]{3,}", s): return True
    if "_" in s: return True
    if "://" in s or ".dll" in s or ".exe" in s or ".txt" in s or ".log" in s: return True
    if re.search(r"[{}<>;=\\]", s): return True
    if len(s) > 40: return True
    if re.match(r"^[a-f0-9]{8,}$", s): return True
    if re.match(r"^[\d\.\-]+$", s): return True
    if re.match(r"^(gl|GL_|rlm|bcc-|BCC_|com\.|nv|cu|cl)", s): return True
    return False

# how many of the 3789 known params live in all 3 main dlls?
in3 = sum(1 for k in covered if len(where.get(k, set()) & set(MAIN)) == 3)
print("known params present in all 3 main dlls: %d / %d" % (in3, len(covered)))

cand = []
for s, dls in where.items():
    if s in covered: continue
    if junk(s): continue
    nmain = len(dls & set(MAIN))
    cand.append((nmain, s, sorted(dls)))

cand.sort(key=lambda t: (-t[0], t[1]))
for n in (3, 2, 1):
    c = [t for t in cand if t[0] == n]
    print("candidates in %d main dll(s): %d" % (n, len(c)))

print()
print("=== in ALL 3 main dlls (highest confidence) ===")
for n, s, dls in cand:
    if n != 3: break
    print("  %s" % s)

open(os.path.join(WORK, "gap3.txt"), "w", encoding="utf-8").write(
    "\n".join(s for n, s, _ in cand if n == 3))
print()
print("wrote gap3.txt")

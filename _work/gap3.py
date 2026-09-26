# -*- coding: utf-8 -*-
"""Identify real UI labels among the uncovered chain strings.

Two signals, both conservative:
  A) the string sits next to a KNOWN param (from presets) in the same slot chain
  B) it is a plain word/phrase (no camelCase identifier shapes), not an AEGP suite
Strings failing both are left alone - replacing an internal name that the
plugin looks up by string (e.g. "AEGP Effect Suite") would break it.
"""
import json, os, re, collections

WORK = r"D:\Programming project\插件汉化\_work"
chains = json.load(open(os.path.join(WORK, "dll_chains.json"), encoding="utf-8"))
pz = json.load(open(os.path.join(WORK, "param_zh.json"), encoding="utf-8"))
covered = set(pz.keys())

FORBID = re.compile(r"(^AEGP|Suite$|^PF[ _]|^gl|^GL_|^rlm|^bcc-|^BCC_|^com\.|"
                    r"\.dll$|\.exe$|\.txt$|\.log$|://|[_\\{}<>;=])")

def camel_identifier(s):
    """True for AddMediaDataRef / addMovieResource style code names."""
    if " " in s:
        return False
    return bool(re.match(r"^[A-Za-z][A-Za-z0-9]*([A-Z][a-z0-9]*)+$", s))

def plainish(s):
    """Looks like human-readable label text."""
    if " " in s:
        return all(re.match(r"^[A-Za-z0-9\-\./'\(\)%&,\+:]+$", w) for w in s.split())
    return bool(re.match(r"^[A-Z][a-z]+$|^[A-Z]+$|^[a-z]+$", s))

adj, plain_only = {}, set()
for dll, chmap in chains.items():
    for off, lst in chmap.items():
        for i, s in enumerate(lst):
            if not isinstance(s, str) or s in covered:
                continue
            nb = False
            for j in (i - 1, i + 1):
                if 0 <= j < len(lst) and lst[j] in covered:
                    nb = True
            if nb:
                adj.setdefault(s, set()).add(dll)
            elif plainish(s):
                plain_only.add(s)

def ok(s):
    if FORBID.search(s): return False
    if camel_identifier(s): return False
    if not plainish(s): return False
    if len(s) < 3 or len(s) > 40: return False
    if not re.search(r"[A-Za-z]{3,}", s): return False
    return True

trusted = sorted(s for s in adj if ok(s))
print("A) adjacent to a known param : %d  (after filters %d)" % (len(adj), len(trusted)))

# B) plain-looking, in >=2 of the 3 main dlls (shared => real UI), minus forbidden
MAIN = {"Continuum_AE_Float.dll", "Continuum_AE_8Bit.dll", "Continuum_AE_16Bit.dll"}
where = collections.defaultdict(set)
for dll, chmap in chains.items():
    for off, lst in chmap.items():
        for s in lst:
            if isinstance(s, str):
                where[s].add(dll)
shared = sorted(s for s in plain_only
                if ok(s) and len(where.get(s, set()) & MAIN) >= 2)
print("B) plain + shared by >=2 main dlls: %d" % len(shared))

final = sorted(set(trusted) | set(shared))
print()
print("TOTAL new strings to translate: %d" % len(final))

with open(os.path.join(WORK, "gap_final.txt"), "w", encoding="utf-8") as f:
    for s in final:
        f.write(s + "\n")
print("wrote gap_final.txt")
for s in final[:60]:
    print("  " + s)

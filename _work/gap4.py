# -*- coding: utf-8 -*-
"""Final, conservative selection of UI labels to translate.

Kept only if:
  * adjacent to a KNOWN param in the same slot chain (strongest signal), OR
    plain + shared by >=2 main engine dlls
  * AND shaped like a label: no printf specifiers, no sentence-like lowercase
    words, no known error-message vocabulary.

Anything else is left in English on purpose - replacing an internal string the
plugin looks up by name would break it.
"""
import json, os, re, sys, collections

WORK = r"D:\Programming project\插件汉化\_work"
sys.path.insert(0, WORK)
from names_manual import NAMES

chains = json.load(open(os.path.join(WORK, "dll_chains.json"), encoding="utf-8"))
pz = json.load(open(os.path.join(WORK, "param_zh.json"), encoding="utf-8"))
covered = set(pz.keys())

MAIN = {"Continuum_AE_Float.dll", "Continuum_AE_8Bit.dll", "Continuum_AE_16Bit.dll"}

# lowercase particles that are fine inside a Title-Case label
PARTICLES = {"to", "from", "by", "with", "of", "in", "on", "at", "and", "or",
             "for", "the", "a", "an", "per", "vs", "via", "as"}

BADWORDS = re.compile(
    r"\b(is|not|too|has|was|are|be|been|can|could|should|must|does|do|did|"
    r"error|failed|invalid|bogus|unsupported|unknown|assertion|null|"
    r"pointer|array|matrix|header|sequence|table|index|code|request|"
    r"please|file|data|input|output|type|value|no|here|occured|contains|"
    r"defined|allowed|supported|change|access|read|open|set|get|"
    r"cvmat|iplimage|opencv|jpeg|huffman|dac|coi|roi|bfxd|ack)\b", re.I)

FORBID = re.compile(r"(^AEGP|Suite$|^PF[ _]|^gl|^GL_|^rlm|^bcc-|^BCC_|^com\.|"
                    r"\.dll$|\.exe$|\.txt$|\.log$|://|[_\\{}<>;=])")

def shape_ok(s):
    if "%" in s: return False
    if BADWORDS.search(s): return False
    words = re.split(r"[\s\-/]+", s.strip())
    for w in words:
        w = w.strip(".,'()")
        if not w: continue
        if w[0].islower() and w.lower() not in PARTICLES:
            return False
        if not re.match(r"^[A-Za-z0-9\.\-\+']+$", w):
            return False
    return True

def plain(s):
    if len(s) < 3 or len(s) > 40: return False
    if not re.search(r"[A-Za-z]{3,}", s): return False
    if FORBID.search(s): return False
    if re.match(r"^[A-Za-z][A-Za-z0-9]*([A-Z][a-z0-9]*)+$", s) and " " not in s:
        return False          # camelCase identifier
    return shape_ok(s)

where = collections.defaultdict(set)
adjacent = set()
for dll, chmap in chains.items():
    for off, lst in chmap.items():
        for i, s in enumerate(lst):
            if not isinstance(s, str): continue
            where[s].add(dll)
            if s in covered: continue
            for j in (i - 1, i + 1):
                if 0 <= j < len(lst) and lst[j] in covered:
                    adjacent.add(s)

cand = set()
for s in adjacent:
    if plain(s): cand.add(s)
for s, dls in where.items():
    if s in covered: continue
    if plain(s) and len(dls & MAIN) >= 2:
        cand.add(s)

cand = sorted(cand)
print("candidates:", len(cand))
print("of which also appear as effect names (handled separately):",
      len([s for s in cand if s in NAMES]))

# split into: real new labels vs effect-name strings
labels = [s for s in cand if s not in NAMES]
print("new UI labels to translate:", len(labels))

with open(os.path.join(WORK, "gap_final.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(labels))
print("wrote gap_final.txt")
for s in labels[:70]:
    print("  " + s)

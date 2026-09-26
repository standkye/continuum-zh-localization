# -*- coding: utf-8 -*-
"""Which words in the newly-found strings does the existing dictionary miss?"""
import os, re, sys, collections, importlib

WORK = r"D:\Programming project\插件汉化\_work"
sys.path.insert(0, WORK)

D = {}
for mod in ("dict_zh", "dict_extra", "dict_extra2", "dict_fix"):
    try:
        m = importlib.import_module(mod)
    except Exception as e:
        print("load fail", mod, e); continue
    for attr in ("TOKENS", "FIX", "EXTRA", "EXTRA2", "DICT", "D"):
        d = getattr(m, attr, None)
        if isinstance(d, dict):
            D.update(d)
            print("  %s.%s -> %d" % (mod, attr, len(d)))
print("combined dict size:", len(D))

new = [l.rstrip("\n") for l in open(os.path.join(WORK, "gap_final.txt"), encoding="utf-8") if l.strip()]
print("new strings:", len(new))

# effect-name strings are already handled by NAMES - drop them
from names_manual import NAMES
new = [s for s in new if s not in NAMES]
print("after dropping effect names:", len(new))

def split_words(s):
    s = re.sub(r"\s*\(\s*", " ", s).replace(")", " ")
    out = []
    for p in re.split(r"[\s\-/]+", s):
        p = p.strip(".,'")
        if not p: continue
        p = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", p)
        p = re.sub(r"(?<=[A-Za-z])(?=\d)", " ", p)
        for w in p.split():
            if w: out.append(w)
    return out

unk = collections.Counter()
unk_ex = collections.defaultdict(list)
for s in new:
    for w in split_words(s):
        if w in D or w.lower() in D: continue
        if re.match(r"^[\d%]+$", w): continue
        if len(w) == 1: continue
        unk[w] += 1
        if len(unk_ex[w]) < 3:
            unk_ex[w].append(s)

print()
print("unknown words: %d distinct" % len(unk))
with open(os.path.join(WORK, "unknown_words.txt"), "w", encoding="utf-8") as f:
    for w, n in unk.most_common():
        f.write("%d\t%s\t%s\n" % (n, w, " | ".join(unk_ex[w])))
print("wrote unknown_words.txt")
for w, n in unk.most_common(70):
    print("  %-22s x%-4d  %s" % (w, n, unk_ex[w][0]))

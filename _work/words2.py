# -*- coding: utf-8 -*-
"""Words missing from the dictionary, for the final 1718-label list."""
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
        if isinstance(d, dict): D.update(d)
print("dict size:", len(D))

labels = [l.rstrip("\n") for l in open(os.path.join(WORK, "gap_final.txt"), encoding="utf-8") if l.strip()]
print("labels:", len(labels))

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
ex = collections.defaultdict(list)
for s in labels:
    for w in split_words(s):
        if w in D or w.lower() in D: continue
        if re.match(r"^[\d%]+$", w) or len(w) == 1: continue
        unk[w] += 1
        if len(ex[w]) < 2: ex[w].append(s)

print("unknown: %d distinct" % len(unk))
with open(os.path.join(WORK, "unknown_words.txt"), "w", encoding="utf-8") as f:
    for w, n in unk.most_common():
        f.write("%d\t%s\t%s\n" % (n, w, " | ".join(ex[w])))
print("wrote unknown_words.txt")

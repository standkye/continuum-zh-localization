# -*- coding: utf-8 -*-
"""Find residual Latin words in the composed translations, ranked by frequency."""
import json, os, re, collections

WORK = r"D:\Programming project\插件汉化\_work"
zh = json.load(open(os.path.join(WORK, "zh_all.json"), encoding="utf-8"))
pz = json.load(open(os.path.join(WORK, "param_zh.json"), encoding="utf-8"))

cnt = collections.Counter()
examples = {}
param_bad = 0
param_total = 0
for en, out in zh.items():
    ms = re.findall(r"[A-Za-z]{3,}", out)
    if not ms:
        continue
    if en in pz:
        param_total += 1
        for m in ms:
            cnt[m] += 1
            examples.setdefault(m, (en, out))
    else:
        param_bad += 1

print("params (preset-derived) with Latin:", param_total, "/", len(pz))
print("other strings with Latin:", param_bad)
print()
lines = ["=== residual latin words in PARAMS (ranked) ==="]
for w, c in cnt.most_common():
    ex, out = examples[w]
    lines.append("%5d  %-22s  e.g. %-40s -> %s" % (c, w, ex, out))
open(os.path.join(WORK, "latin_rank.txt"), "w", encoding="utf-8").write("\n".join(lines))
print("wrote latin_rank.txt  (%d distinct words)" % len(cnt))

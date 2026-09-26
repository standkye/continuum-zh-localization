# -*- coding: utf-8 -*-
"""Rebuild effect_zh.json from the new hand-written tables, then patch.

effect_zh.json entry: [en_text, zh_text, size, off, cap]
"""
import os, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

W = r"D:\Programming project\插件汉化\_work"
sys.path.insert(0, W)
from names_manual import NAMES, CATS

old = json.load(open(os.path.join(W, "effect_zh.json"), encoding="utf-8"))
zh_all = json.load(open(os.path.join(W, "zh_all.json"), encoding="utf-8"))

rep, missing = [], []
nfile, nitem = 0, 0
new = {}
for fn, items in sorted(old.items()):
    out = []
    for (en, old_zh, size, off, cap) in items:
        raw = en.strip()
        zh = NAMES.get(raw) or NAMES.get(en) or CATS.get(raw) or CATS.get(en)
        if zh is None:
            zh = zh_all.get(en) or zh_all.get(raw) or old_zh
            if zh is None:
                missing.append("%-40s %r" % (fn, en))
                zh = old_zh
        b = zh.encode("gbk", "ignore")
        if len(b) > cap:
            b = b[:cap]
            while b:
                try:
                    b.decode("gbk")
                    break
                except UnicodeDecodeError:
                    b = b[:-1]
            zh = b.decode("gbk", "ignore")
        out.append([en, zh, size, off, cap])
        nitem += 1
    new[fn] = out
    nfile += 1

json.dump(new, open(os.path.join(W, "effect_zh_new.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=0)

print("files      :", nfile)
print("entries    :", nitem)
print("unresolved :", len(missing))
for m in missing[:20]:
    print("   ", m)

# 抽样对比新旧
print()
print("--- 抽样（旧 -> 新）---")
shown = 0
for fn, items in sorted(new.items()):
    for i, (en, zh, size, off, cap) in enumerate(items):
        o = old[fn][i][1]
        if o != zh:
            print("  %-30s %-34s -> %s" % (fn[:30], o, zh))
            shown += 1
            if shown >= 40:
                break
    if shown >= 40:
        break

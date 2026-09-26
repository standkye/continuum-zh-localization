# -*- coding: utf-8 -*-
"""导出本轮还没翻的 UI 标签候选，按频次分组，方便分批手写。"""
import os, json

W = r'D:\Programming project\插件汉化\_work'
rows = open(os.path.join(W, '_ui_miss.tsv'), encoding='utf-8').read().splitlines()[1:]
with open(os.path.join(W, 'batch7_miss.json'), encoding='utf-8') as f:
    done = json.load(f)

rest = []
for r in rows:
    p = r.split('\t')
    if len(p) < 3:
        continue
    en, cap, c = p[0], int(p[1]), int(p[2])
    if en in done:
        continue
    rest.append((c, cap, en))

rest.sort(key=lambda x: (-x[0], x[2]))
g = {3: [], 2: [], 1: []}
for c, cap, en in rest:
    g[3 if c >= 3 else c].append((en, cap, c))

out = []
out.append('剩余候选总计 %d 条' % len(rest))
for k in (3, 2, 1):
    out.append('  x%s 组: %d 条' % ('>=3' if k == 3 else k, len(g[k])))
out.append('')
for k in (3, 2, 1):
    out.append('=' * 70)
    out.append('x%s 组 (%d 条)' % ('>=3' if k == 3 else k, len(g[k])))
    out.append('=' * 70)
    for i, (en, cap, c) in enumerate(g[k], 1):
        out.append('%4d. x%-2d cap=%-3d | %s' % (i, c, cap, en))
    out.append('')

open(os.path.join(W, '_rest_all.txt'), 'w', encoding='utf-8').write('\n'.join(out))
# 机器可读
tsv = ['English\tCap\tCount']
for c, cap, en in rest:
    tsv.append('%s\t%d\t%d' % (en, cap, c))
open(os.path.join(W, '_rest_all.tsv'), 'w', encoding='utf-8').write('\n'.join(tsv))
print('rest=%d  -> _rest_all.txt / _rest_all.tsv' % len(rest))

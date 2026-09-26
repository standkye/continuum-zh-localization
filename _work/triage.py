# -*- coding: utf-8 -*-
"""从独立复核报告里抽出 NO_DICT 名单，做成可批量翻译的工作表。
输出：
  _nodict_all.tsv   全部名字 + 频次 + 首处上下文（制表符分隔，供后续补词）
  _nodict_top.txt   频次最高的 260 个，人能直接读、判类
"""
import os, re, collections

W = r'D:\Programming project\插件汉化\_work'
t = open(os.path.join(W, '_resid_patched_dll_d.txt'), encoding='utf-8').read()
i = t.index('【NO_DICT】')
j = t.index('【OV】')
nd = t[i:j]

blocks = re.split(r'\n(?=  \S)', nd)
recs = []
for blk in blocks:
    lines = blk.split('\n')
    m = re.match(r'^  (.*?)  (\d+) 处 \(([^)]*)\)\s*$', lines[0])
    if not m:
        continue
    name, cnt, dlls = m.group(1), int(m.group(2)), m.group(3)
    pre = ''
    for ln in lines[1:]:
        if '前:' in ln:
            pre = ln.split('前:', 1)[1].strip()
            break
    recs.append((name, cnt, dlls, pre))

recs.sort(key=lambda r: (-r[1], r[0]))
with open(os.path.join(W, '_nodict_all.tsv'), 'w', encoding='utf-8') as f:
    f.write('name\tcount\tdlls\tcontext\n')
    for name, cnt, dlls, pre in recs:
        f.write('%s\t%d\t%s\t%s\n' % (name, cnt, dlls, pre))

lines = ['NO_DICT 总数 %d 个' % len(recs), '']
for name, cnt, dlls, pre in recs[:260]:
    lines.append('%-38s %3d  %-8s %s' % (name, cnt, dlls[:8], pre[:78]))
open(os.path.join(W, '_nodict_top.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
print('total', len(recs))

# -*- coding: utf-8 -*-
"""从 _fix4_writes.json 重新生成 ParamNameTable.txt（中文 -> 英文原名）"""
import os, json, io

W = r'D:\Programming project\插件汉化\_work'
DEL = r'D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0'

w = json.load(open(os.path.join(W, '_fix4_writes.json'), encoding='utf-8'))
pairs = {}
for dll, off, en, zh, sec, kind, av, nb in w:
    if not zh:
        continue
    # 只保留真正含 CJK 的写入
    if not any('一' <= c <= '鿿' for c in zh):
        continue
    if zh in pairs:
        if en not in pairs[zh]:
            pairs[zh] = pairs[zh] + ' / ' + en
    else:
        pairs[zh] = en

out = io.StringIO()
out.write('Continuum parameter names  Chinese -> English\n')
out.write('total %d\n' % len(pairs))
out.write('=' * 52 + '\n\n')

def width(s):
    """按显示宽度估算：CJK 记 2，其它记 1"""
    n = 0
    for c in s:
        n += 2 if ord(c) > 0x2E80 else 1
    return n

for zh in sorted(pairs):
    pad = max(1, 22 - width(zh))
    out.write('%s%s%s\n' % (zh, ' ' * pad, pairs[zh]))

tgt = os.path.join(DEL, 'ParamNameTable.txt')
open(tgt, 'w', encoding='utf-8').write(out.getvalue())
print('ParamNameTable.txt:', len(pairs), '条', os.path.getsize(tgt), 'bytes')

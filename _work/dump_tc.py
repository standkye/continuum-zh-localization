# -*- coding: utf-8 -*-
import os, json, io, sys
W = r'D:\Programming project\插件汉化\_work'
c = json.load(open(os.path.join(W, 'cand9b.json'), encoding='utf-8'))
out = io.StringIO()
lst = c['C']
print('TIER C', len(lst))
for i, (name, cnt, dlls, avail, pre, post) in enumerate(lst, 1):
    out.write('%3d. %-42s cap=%-3d %s\n' % (i, name, avail, dlls.replace('.dll', '')))
    if pre:
        out.write('      pre : %s\n' % pre[:100])
    if post:
        out.write('      post: %s\n' % post[:100])
open(os.path.join(W, '_tc_dump.txt'), 'w', encoding='utf-8').write(out.getvalue())
print('ok')

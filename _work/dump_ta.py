# -*- coding: utf-8 -*-
"""导出 TIER A / B 的「名字 + 上下文」清单，供逐条手写翻译"""
import os, json, io, sys
W = r'D:\Programming project\插件汉化\_work'
c = json.load(open(os.path.join(W, 'cand9b.json'), encoding='utf-8'))
out = io.StringIO()
def p(s=''):
    out.write(str(s) + '\n')

for tier in ('A', 'B'):
    p('#' * 96)
    p('# TIER %s   %d 条' % (tier, len(c[tier])))
    p('#' * 96)
    for i, (name, cnt, dlls, avail, pre, post) in enumerate(c[tier], 1):
        p('%3d. %-40s x%-3d cap=%-3d %s' % (i, name, cnt, avail, dlls.replace('.dll', '')))
        if pre:
            p('      pre : %s' % pre[:120])
        if post:
            p('      post: %s' % post[:120])
    p()

open(os.path.join(W, '_ta_dump.txt'), 'w', encoding='utf-8').write(out.getvalue())
print('TOTAL A=%d B=%d' % (len(c['A']), len(c['B'])))

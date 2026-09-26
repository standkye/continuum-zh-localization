# -*- coding: utf-8 -*-
import os, json, io
W = r'D:\Programming project\插件汉化\_work'
c = json.load(open(os.path.join(W, 'cand9b.json'), encoding='utf-8'))
lst = c['C']
print('TIER C', len(lst))
out = io.StringIO()
for i, (name, cnt, dlls, avail, pre, post) in enumerate(lst, 1):
    out.write('%4d\t%s\t%d\t%s\n' % (i, repr(name), avail, dlls.replace('.dll','')))
open(os.path.join(W, '_tc_list.txt'), 'w', encoding='utf-8').write(out.getvalue())
# also dump pre/post context compact
out2 = io.StringIO()
for i, (name, cnt, dlls, avail, pre, post) in enumerate(lst, 1):
    out2.write('%4d %s | pre=%s | post=%s\n' % (i, repr(name), (pre or '')[:70], (post or '')[:70]))
open(os.path.join(W, '_tc_ctx.txt'), 'w', encoding='utf-8').write(out2.getvalue())
print('ok')

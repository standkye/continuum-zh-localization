# -*- coding: utf-8 -*-
"""把 batch9_miss.json 的键对齐到 cand9b 里的**精确 token**（可能带尾随空格），
并修掉超容的两条。"""
import os, json, io, sys

W = r'D:\Programming project\插件汉化\_work'
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

d = json.load(open(os.path.join(W, 'batch9_miss.json'), encoding='utf-8'))
c = json.load(open(os.path.join(W, 'cand9b.json'), encoding='utf-8'))

exact = {}
for tier in ('A', 'B', 'C'):
    for (name, cnt, dlls, avail, pre, post) in c[tier]:
        exact[name.strip()] = name

out = io.StringIO()
def p(s=''):
    print(s, flush=True); out.write(str(s) + '\n')

new = {}
nosp = []
for k, v in d.items():
    e = exact.get(k)
    if e is None:
        nosp.append(k)
        new[k] = v
    else:
        new[e] = v

# 超容修正
new['Extras'] = '附加项'        # need 7 <= 8
new['Hide UI'] = '隐藏UI'       # need 7 <= 8

p('对齐到精确 token: %d 条（其中带尾随空格的 %d 条）'
  % (len(new) - len(nosp), sum(1 for k in new if k != k.strip())))
p('未在 cand9b 里找到（保留原键）: %d  %s' % (len(nosp), nosp[:15]))
p()
for k in sorted(new):
    if k != k.strip():
        p('   尾部空格键: %r -> %r' % (k, new[k]))

json.dump(new, open(os.path.join(W, 'batch9_miss.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
open(os.path.join(W, '_rekey9.txt'), 'w', encoding='utf-8').write(out.getvalue())
p('DONE  -> batch9_miss.json  %d 条' % len(new))

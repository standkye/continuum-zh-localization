# -*- coding: utf-8 -*-
"""交付刷新 + 抽样自检：
  1) 从写入清单里抽 60 条新增译名，人眼过一遍
  2) 把 patched_dll_d 的 6 支 DLL 覆盖到交付目录
  3) 打印每支的 sha256 与大小，作为交付记录
"""
import os, json, random, hashlib, shutil

W = r'D:\Programming project\插件汉化\_work'
SRC = os.path.join(W, 'patched_dll_d')
DST = r'D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0'
writes = json.load(open(os.path.join(W, '_fix4_writes.json'), encoding='utf-8'))

out = []
new = [r for r in writes if r[5] == 'new']
random.seed(20260925)
sample = random.sample(new, min(60, len(new)))
out.append('=== 新增译名抽样（%d / %d）===' % (len(sample), len(new)))
for r in sorted(sample, key=lambda x: (x[0], x[1])):
    out.append('  %-28s %-32r -> %r' % (r[0][9:], r[2], r[3]))
out.append('')

# BCC / BCC+ 效果名抽样
eff = [r for r in new if r[2].startswith(('BCC ', 'BCC+', 'FEC '))]
sample2 = random.sample(eff, min(30, len(eff)))
out.append('=== 效果名表抽样（%d / %d）===' % (len(sample2), len(eff)))
for r in sorted(sample2, key=lambda x: x[2]):
    out.append('  %-28s %-40r -> %r' % (r[0][9:], r[2], r[3]))
out.append('')

out.append('=== 交付覆盖 ===')
tot = 0
for name in sorted(os.listdir(SRC)):
    s = os.path.join(SRC, name)
    d = os.path.join(DST, name)
    if not name.lower().endswith('.dll'):
        continue
    if os.path.exists(d):
        old = hashlib.sha256(open(d, 'rb').read()).hexdigest()[:16]
    else:
        old = '（交付目录原本没有）'
    shutil.copy2(s, d)
    h = hashlib.sha256(open(d, 'rb').read()).hexdigest()
    tot += 1
    out.append('  %-32s %10d  旧 %s -> 新 %s' % (name, os.path.getsize(d), old, h[:16]))
out.append('  覆盖 %d 支 DLL' % tot)

open(os.path.join(W, '_deliver_now.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('DONE')

# -*- coding: utf-8 -*-
import os, collections, subprocess
ROOT = r'D:\Programming project\插件汉化'
raw = open(os.path.join(ROOT, '_work', '_gitdry.txt'), encoding='utf-8', errors='replace').read()
files = []
for l in raw.split('\n'):
    if l.startswith('add '):
        f = l[4:].strip().strip("'")
        files.append(f)

groups = collections.OrderedDict([
    ('交付·aex',        lambda f: f.startswith('Continuum 汉化组件') and f.lower().endswith('.aex')),
    ('交付·文档/bat',   lambda f: f.startswith('Continuum 汉化组件') and not f.lower().endswith(('.aex', '.dll', '.exe'))),
    ('_work 中间 aex',  lambda f: f.startswith('_work/patched_aex')),
    ('_work · py 脚本', lambda f: f.lower().endswith('.py')),
    ('_work · json 词典', lambda f: f.lower().endswith('.json')),
    ('_work · _xxx 日志/报告', lambda f: '_work/_' in f and f.lower().endswith(('.txt', '.tsv'))),
    ('其它',            lambda f: True),
])
seen = set()
res = collections.OrderedDict((k, [0, 0]) for k in groups)
for f in files:
    for k, pred in groups.items():
        if pred(f):
            res[k][0] += 1
            p = os.path.join(ROOT, f)
            try: res[k][1] += os.path.getsize(p)
            except OSError: pass
            break
tot_n = tot_s = 0
for k, (n, s) in res.items():
    tot_n += n; tot_s += s
    print('  %-24s %5d 个   %8.1f MB' % (k, n, s / 1048576.0))
print('  %-24s %5d 个   %8.1f MB' % ('合计', tot_n, tot_s / 1048576.0))
print()
over1 = []
for f in files:
    p = os.path.join(ROOT, f)
    try: s = os.path.getsize(p)
    except OSError: continue
    if s > 1048576:
        over1.append((s, f))
over1.sort(reverse=True)
print('== 其中 >1MB 的文件 %d 个 ==' % len(over1))
for s, f in over1[:18]:
    print('   %8.1f MB  %s' % (s / 1048576.0, f))
print('   ... 这些合计 %.1f MB' % (sum(o[0] for o in over1) / 1048576.0))

# -*- coding: utf-8 -*-
"""扫 BCC.log，找 Licensed render / BCCnt / TiBCC 等线索 + 崩溃时间点上下文"""
import os, io, sys, glob
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

out = io.StringIO()
def p(*a):
    s = ' '.join(str(x) for x in a)
    print(s, flush=True); out.write(s + '\n')

cands = []
base = os.environ.get('LOCALAPPDATA', '')
for pat in (os.path.join(base, 'BorisFX', 'Continuum', '*.log'),
            os.path.join(base, 'BorisFX', 'Continuum', '*', '*.log'),
            os.path.join(base, 'BorisFX', '*', 'BCC.log')):
    cands += glob.glob(pat)
cands = sorted(set(cands))
p('候选日志: %s' % cands)

KEYS = ['Licensed render', 'BCCnt', 'BCC+Ti', '8BitLib', 'Textures', '纹理', 'crash', 'Crash', 'Exception']
for f in cands:
    try:
        t = open(f, 'rb').read().decode('utf-8', 'replace')
    except Exception as e:
        p('  读不了 %s: %s' % (f, e)); continue
    lines = t.splitlines()
    p()
    p('=== %s  (%d 行, %d bytes) ===' % (f, len(lines), len(t)))
    hit = [(i, l) for i, l in enumerate(lines) if any(k in l for k in KEYS)]
    p('   命中 %d 行' % len(hit))
    for i, l in hit[:40]:
        p('   %5d | %s' % (i, l[:160]))
    if hit:
        # 打印最后一批命中行的上下文
        last = hit[-1][0]
        p('   --- 末尾上下文 ---')
        for i in range(max(0, last - 6), min(len(lines), last + 7)):
            p('   %5d | %s' % (i, lines[i][:160]))
    p('   --- 文件最后 12 行 ---')
    for i in range(max(0, len(lines) - 12), len(lines)):
        p('   %5d | %s' % (i, lines[i][:160]))

open(os.path.join(r'D:\Programming project\插件汉化\_work', '_log_scan.txt'),
     'w', encoding='utf-8').write(out.getvalue())
p('DONE')

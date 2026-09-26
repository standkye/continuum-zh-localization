# -*- coding: utf-8 -*-
"""上下文取样：把指定偏移附近 40 个独立记号排出来看，判断这个池子到底是什么。"""
import os, re

BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"
TOKEN_RE = re.compile(rb'[\x20-\x7e]+')

TARGETS = [
    ('Continuum_AE_8Bit.dll', 0x0194948C, 'rsrc 池 A'),
    ('Continuum_AE_8Bit.dll', 0x00FB3170, 'Red/Combustion/OpenFX 一带'),
    ('Continuum_AE_8Bit.dll', 0x00FB31A8, 'Corel 一带'),
    ('Continuum_AE_8Bit.dll', 0x00FCDF80, 'Quantel/Natron 一带'),
    ('Continuum_AE_8Bit.dll', 0x01015200, 'Channel 池（已改）'),
    ('Continuum_AE_8Bit.dll', 0x01097750, 'Channel 池 2（已改）'),
    ('Continuum_3DObjects_AE.dll', 0x01398AF0, '3D rsrc Material 一带'),
    ('Continuum_3DObjects_AE.dll', 0x0128CE28, 'Use Comp Lights 一带'),
]

out = []
def p(s=''):
    out.append(str(s))
    print(s, flush=True)

def section_at(d, off):
    pe = d.find(b'PE\x00\x00')
    nsec = int.from_bytes(d[pe + 6:pe + 8], 'little')
    optsz = int.from_bytes(d[pe + 20:pe + 22], 'little')
    base = pe + 24 + optsz
    for i in range(nsec):
        o = base + i * 40
        nm = d[o:o + 8].rstrip(b'\x00').decode('ascii', 'replace')
        rsize = int.from_bytes(d[o + 16:o + 20], 'little')
        roff = int.from_bytes(d[o + 20:o + 24], 'little')
        if roff <= off < roff + rsize:
            return nm, roff, rsize, roff - int.from_bytes(d[o + 12:o + 16], 'little')  # rva差
    return '?', 0, 0, 0

for dll, off, label in TARGETS:
    src = os.path.join(BK, dll)
    if not os.path.exists(src):
        src = os.path.join(CONT, dll)
    d = open(src, 'rb').read()
    nm, roff, rsize, _ = section_at(d, off)
    p('=' * 100)
    p('%s @ 0x%08X   节=%s (raw 0x%08X..0x%08X, size %d)   备注: %s'
      % (dll, off, nm, roff, roff + rsize, rsize, label))
    p('=' * 100)
    # 收集该节内全部记号
    toks = []
    for m in TOKEN_RE.finditer(d):
        s, e = m.span()
        if s > 0 and d[s - 1] != 0:
            continue
        if not (roff <= s < roff + rsize):
            continue
        toks.append((s, e, m.group().decode('ascii', 'replace')))
    # 找最近的记号
    k = min(range(len(toks)), key=lambda i: abs(toks[i][0] - off))
    lo = max(0, k - 20)
    hi = min(len(toks), k + 20)
    p('  （该节共 %d 个记号；下面显示目标附近的 %d 个，★ = 目标位置）' % (len(toks), hi - lo))
    for i in range(lo, hi):
        s, e, t = toks[i]
        star = '  ★' if i == k or abs(s - off) < 16 else '   '
        gap = (s - toks[i - 1][1]) if i > lo else 0
        p('%s 0x%08X (+%3d) %r' % (star, s, gap, t))
    p()

open(os.path.join(os.path.expanduser('~'), '..', '..', 'dev', 'null'), 'a').close() if False else None
open(r"D:\Programming project\插件汉化\_work\_ctx_dump.txt", 'w', encoding='utf-8').write('\n'.join(out))
print('DONE')

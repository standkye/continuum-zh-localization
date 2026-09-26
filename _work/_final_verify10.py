# -*- coding: utf-8 -*-
"""v10 交付前最终体检（针对"纹理效果崩溃"这个具体 bug）

硬指标 A：任何以 '|' 分隔的选项段里出现非 ASCII（中文）字节 ==> 0
         这种串就是被写坏的下拉选项表（None|Bounce|Stick|Disappear）
硬指标 B：崩溃现场那批效果标识串必须完好（BCC+Tint 等）

性能：用 bytes.split(b'\x00') 在 C 层切串，别用 find 循环（190MB 会跑到超时）。
"""
import os, io, sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

DELIV = r'D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0'
DLLS = ["Continuum_AE_Float.dll", "Continuum_AE_8Bit.dll", "Continuum_AE_16Bit.dll",
        "Continuum_Common_AE.dll", "Continuum_3DObjects_AE.dll", "BCCPlus.dll"]

out = io.StringIO()
def p(*a):
    s = ' '.join(str(x) for x in a)
    print(s, flush=True)
    out.write(s + '\n')


def scan(path):
    b = open(path, 'rb').read()
    toks = b.split(b'\x00')
    nb = 0
    bad = []
    for t in toks:
        if b'\x7c' not in t:
            continue
        nb += t.count(b'\x7c')
        if t and max(t) > 0x7f:
            bad.append(t[:80])
    return len(toks), nb, bad


tot = 0
for d in DLLS:
    ntok, nb, bad = scan(os.path.join(DELIV, d))
    tot += len(bad)
    p('%-30s 串 %7d   "|" %6d   被中文污染的选项串: %d' % (d, ntok, nb, len(bad)))
    for s in bad[:5]:
        p('    ! %s' % s.decode('gbk', 'replace'))
p()
p('==> A. 被污染的下拉选项串总数: %d  %s' % (tot, 'OK' if tot == 0 else '*** FAIL ***'))
p()

probe = [b'BCC+Tint', b'BCC+Texture', b'BCC+Textures', b'BCC+Multi-Star',
         b'BCC+Streaks', b'BCC+Gels', b'BCC+Haze', b'BCC+Rays']
p('==> B. 效果标识串完好性')
for d in DLLS:
    b = open(os.path.join(DELIV, d), 'rb').read()
    hits = [(x.decode('ascii'), b.count(x)) for x in probe if x in b]
    p('  %-30s %s' % (d, hits if hits else '（无命中）'))

open(os.path.join(r'D:\Programming project\插件汉化\_work', '_final_verify10.txt'),
     'w', encoding='utf-8').write(out.getvalue())
p('DONE')

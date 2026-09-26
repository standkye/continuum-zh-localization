# -*- coding: utf-8 -*-
"""三方对比：英文备份 / 已装坏版 / 新修复版，定位 BCC+Tint 那一处到底怎么烂的"""
import os, io, sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

W = r'D:\Programming project\插件汉化\_work'
BAK = r'C:\Program Files\BorisFX\ContinuumAE\19\Backup-English'
INST = r'C:\Program Files\BorisFX\ContinuumAE\19\lib'
NEW = r'D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0'
DLL = 'Continuum_AE_8Bit.dll'
KEY = b'BCC+Tint'

out = io.StringIO()
def p(*a):
    s = ' '.join(str(x) for x in a)
    print(s, flush=True); out.write(s + '\n')

def load(pth):
    if not os.path.exists(pth):
        return None
    return open(pth, 'rb').read()

b_bak = load(os.path.join(BAK, DLL))
b_ins = load(os.path.join(INST, DLL))
b_new = load(os.path.join(NEW, DLL))
p('英文备份 %s   已装 %s   新版 %s' % (bool(b_bak), bool(b_ins), bool(b_new)))
p('已装 == 新版 ? %s' % (b_ins == b_new if b_ins and b_new else 'NA'))
p()

if b_bak:
    offs = []
    pos = 0
    while True:
        i = b_bak.find(KEY, pos)
        if i < 0: break
        offs.append(i)
        pos = i + 1
    p('英文备份里 %r 出现 %d 次' % (KEY.decode(), len(offs)))
    for i in offs[:12]:
        seg_b = b_bak[i:i+32].split(b'\x00')[0]
        seg_i = b_ins[i:i+32].split(b'\x00')[0] if b_ins else b''
        seg_n = b_new[i:i+32].split(b'\x00')[0] if b_new else b''
        def d(s):
            try: return s.decode('gbk')
            except Exception: return repr(s)
        p('  off=%d' % i)
        p('     英文 : %s' % d(seg_b))
        p('     已装 : %s   %r' % (d(seg_i), seg_i))
        p('     新版 : %s   %r' % (d(seg_n), seg_n))
p()

# 已装坏版里有没有 BCC+Ti 开头的怪串
if b_ins:
    pos = 0; n = 0
    while n < 10:
        i = b_ins.find(b'BCC+Ti', pos)
        if i < 0: break
        seg = b_ins[i:i+24].split(b'\x00')[0]
        p('  [已装] BCC+Ti @%d : %r  -> %s' % (i, seg, seg.decode('gbk', 'replace')))
        pos = i + 1; n += 1
    p('  [已装] BCC+Ti 命中数(截断 10): %d' % n)
if b_new:
    pos = 0; n = 0
    while n < 10:
        i = b_new.find(b'BCC+Ti', pos)
        if i < 0: break
        seg = b_new[i:i+24].split(b'\x00')[0]
        p('  [新版] BCC+Ti @%d : %r  -> %s' % (i, seg, seg.decode('gbk', 'replace')))
        pos = i + 1; n += 1
    p('  [新版] BCC+Ti 命中数(截断 10): %d' % n)

open(os.path.join(W, '_tint_trip.txt'), 'w', encoding='utf-8').write(out.getvalue())
p('DONE')

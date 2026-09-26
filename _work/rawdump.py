# -*- coding: utf-8 -*-
"""把关键区域的原始终极字节 dump 出来，判断 BCCPlus 那张表到底是
   「JSON 键表」还是「键 + 显示名交替表」。"""
import os, re

WORK = r"D:\Programming project\插件汉化\_work"
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
PATCH = os.path.join(WORK, 'patched_dll_c')

CASES = [
    ('BCCPlus.dll',  0x025BE3F0, 0x025BE520, 'Channel/Amount/Scale/Width/Height 一带'),
    ('BCCPlus.dll',  0x025D9AE0, 0x025D9B40, 'Matte/Blur 一带'),
    ('BCCPlus.dll',  0x025BE840, 0x025BE8A0, 'Tumble/Spin/Rotate 一带'),
    ('BCCPlus.dll',  0x0260E2A0, 0x0260E300, 'light.ambientLight/Ambient Light 一带'),
    ('Continuum_AE_8Bit.dll', 0x00FC08C0, 0x00FC0920, 'Pref_* 类型名表'),
    ('Continuum_3DObjects_AE.dll', 0x012C07F0, 0x012C0850, '.cng/Rotate 一带'),
    ('Continuum_AE_8Bit.dll', 0x01096870, 0x010968D0, 'Rad. Position Seed/Fog On 一带'),
]

out = []
def p(s=''):
    out.append(str(s))
    print(s, flush=True)

for dll, lo, hi, note in CASES:
    a = open(os.path.join(BK, dll), 'rb').read()
    b = open(os.path.join(PATCH, dll), 'rb').read()
    p('=' * 104)
    p('%s  0x%08X..0x%08X   %s' % (dll, lo, hi, note))
    p('=' * 104)
    p('  英文原文:')
    p('    %r' % bytes(a[lo:hi]))
    p('  本版补丁:')
    p('    %r' % bytes(b[lo:hi]))
    p()

open(os.path.join(WORK, '_rawdump.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('DONE')

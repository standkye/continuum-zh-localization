# -*- coding: utf-8 -*-
"""实证：已装的坏版里，英文原文件中"含 | 的枚举选项表"被写进了中文。
三方对照：英文备份(BAK) / 已装坏版(INST) / 新修复版(NEW)
"""
import os, re, io, sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

BAK = r'C:\Program Files\BorisFX\ContinuumAE\19\Backup-English'
INST = r'C:\Program Files\BorisFX\ContinuumAE\19\lib'
NEW = r'D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0'
DLLS = ['Continuum_AE_8Bit.dll', 'Continuum_AE_16Bit.dll', 'Continuum_AE_Float.dll']

# 英文备份是纯 ASCII，用简单字符类即可（带 GBK 分支的交替正则扫 26MB 会跑到超时）
PRINT = re.compile(rb'[\x20-\x7e]{6,}\x00')

out = io.StringIO()
def p(*a):
    s = ' '.join(str(x) for x in a)
    print(s, flush=True); out.write(s + '\n')

def dec(s):
    try: return s.decode('gbk')
    except Exception: return repr(s)

grand_i = grand_n = 0
for dll in DLLS:
    fb = os.path.join(BAK, dll)
    if not os.path.exists(fb):
        p('!! 无备份 ' + dll); continue
    b = open(fb, 'rb').read()
    try:
        i_ = open(os.path.join(INST, dll), 'rb').read()
    except Exception:
        i_ = None
    n_ = open(os.path.join(NEW, dll), 'rb').read()

    bad_i, bad_n = [], []
    for m in PRINT.finditer(b):
        s = m.group()[:-1]
        if b'\x7c' not in s or len(s) < 4:
            continue
        a, z = m.start(), m.start() + len(s)
        ci = i_[a:z] if i_ else b''
        cn = n_[a:z]
        if ci and max(ci) > 0x7f:
            bad_i.append((a, s, ci))
        if max(cn) > 0x7f:
            bad_n.append((a, s, cn))
    grand_i += len(bad_i); grand_n += len(bad_n)
    p('=== %s ===' % dll)
    p('  英文原文件里含 "|" 的选项表: 扫描完成')
    p('  已装坏版中被写进中文的: %d' % len(bad_i))
    p('  新修复版中被写进中文的: %d' % len(bad_n))
    for a, s, c in bad_i[:6]:
        p('    off %d' % a)
        p('      英文 : %s' % dec(s))
        p('      坏版 : %s   %r' % (dec(c), c))
        # 新版同位置
        p('      新版 : %s' % dec(n_[a:a+len(s)]))
    p()
p('==> 合计：坏版 %d 处 / 新版 %d 处' % (grand_i, grand_n))

open(os.path.join(r'D:\Programming project\插件汉化\_work', '_enum_evidence.txt'),
     'w', encoding='utf-8').write(out.getvalue())
p('DONE')

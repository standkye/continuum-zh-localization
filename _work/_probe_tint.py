# -*- coding: utf-8 -*-
"""定位 BCC.log 里 "Licensed render 8BitLib: BCC+TiBCCnt" 这个串的出处"""
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
    print(s, flush=True); out.write(s + '\n')

# 1) DLL 里所有 BCC+ 开头的串
for d in DLLS:
    b = open(os.path.join(DELIV, d), 'rb').read()
    hits = []
    pos = 0
    while len(hits) < 12:
        i = b.find(b'BCC+', pos)
        if i < 0: break
        j = b.find(b'\x00', i)
        hits.append(b[i:j][:40])
        pos = i + 1
    p('%-28s BCC+ 串 %d 例: %s' % (d, len(hits), [h.decode('gbk', 'replace') for h in hits[:6]]))

# 2) 搜 'Tint' 与 'TiBCCnt'
p()
for d in DLLS:
    b = open(os.path.join(DELIV, d), 'rb').read()
    for key in (b'Tint', b'TiBCCnt', b'Texture'):
        n = b.count(key)
        if n:
            p('  %-28s %-10s x%d' % (d, key.decode(), n))

# 3) .aex 里搜 Tint / Textures
p()
aex = [f for f in os.listdir(DELIV) if f.lower().endswith('.aex')]
for f in aex:
    if 'Tint' in f or 'Texture' in f:
        b = open(os.path.join(DELIV, f), 'rb').read()
        j = b.find(b'MIB8eman')
        seg = b[j+16:j+60] if j >= 0 else b''
        p('  %-24s eman=%r' % (f, seg[:40]))

# 4) 已装目录里其它 dll 搜 BCC+Tint
p()
inst = r'C:\Program Files\BorisFX\ContinuumAE\19\lib'
if os.path.isdir(inst):
    for f in sorted(os.listdir(inst)):
        fp = os.path.join(inst, f)
        if not os.path.isfile(fp): continue
        try:
            b = open(fp, 'rb').read()
        except Exception as e:
            p('  skip', f, e); continue
        if b'BCC+Tint' in b:
            p('  [HIT BCC+Tint]', f)
        if b'TiBCCnt' in b:
            p('  [HIT TiBCCnt]', f)

open(os.path.join(r'D:\Programming project\插件汉化\_work', '_probe_tint.txt'),
     'w', encoding='utf-8').write(out.getvalue())
p('DONE')

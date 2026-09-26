# -*- coding: utf-8 -*-
"""列出 gtac（类型栏）仍为纯 ASCII 的 .aex 及原因"""
import os, struct

BK_AEX = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English\aex"
CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"
DELIV = r"D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0"
OUT = r"D:\Programming project\插件汉化\_work\_gtac_left.txt"

def recs(d, key):
    res = []
    i = 0
    while True:
        j = d.find(key, i)
        if j < 0: break
        if d[j-4:j] == b'MIB8':
            base = j-4
            size = struct.unpack_from('<I', d, base+12)[0]
            if 0 < size < 4096:
                res.append((base, size, base+16))
        i = j+4
    return res

lines = []
n_ascii = 0
for fn in sorted(os.listdir(BK_AEX)):
    if not fn.lower().endswith('.aex'): continue
    a = open(os.path.join(BK_AEX, fn), 'rb').read()
    b = open(os.path.join(CONT, fn), 'rb').read()
    ra = recs(a, b'gtac'); rb = recs(b, b'gtac')
    if not ra or not rb: 
        lines.append('%-40s NO_GTAC rec=%d/%d' % (fn, len(ra), len(rb))); continue
    base, size, val = ra[0]
    src = a[val+1:val+size].split(b'\x00')[0]
    cur = b[val+1:val+size].split(b'\x00')[0]
    if cur and max(cur) <= 127:
        n_ascii += 1
        cap = size - 2
        lines.append('%-40s cap=%2d  EN=%-14r  now=%r' % (fn, cap, src.decode('ascii','replace'), cur.decode('ascii','replace')))

hdr = ['gtac 仍为纯 ASCII 的文件: %d' % n_ascii, '']
open(OUT, 'w', encoding='utf-8').write('\n'.join(hdr + lines))
print('still ascii gtac:', n_ascii)

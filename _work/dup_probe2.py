# -*- coding: utf-8 -*-
"""对照探针：某个名字在补丁版里到底有几份、哪份翻了、都在哪个节、邻居是什么。
用来判断「.rdata 里剩下的英文拷贝」是不是 AE 真正显示的那一份。
"""
import os, re

W = r'D:\Programming project\插件汉化\_work'
PATCH = os.path.join(W, 'patched_dll_d')
BK = r'C:\Program Files\BorisFX\ContinuumAE\19\Backup-English'
DLLS = ['Continuum_AE_8Bit.dll', 'BCCPlus.dll', 'Continuum_Common_AE.dll',
        'Continuum_3DObjects_AE.dll']
PAIRS = [('Chromatic Aberration', '色差'),
         ('Light Flicker', '光闪烁'),
         ('Rad. Position Seed', '位置种子')]


def sections(d):
    pe = d.find(b'PE\x00\x00')
    nsec = int.from_bytes(d[pe + 6:pe + 8], 'little')
    optsz = int.from_bytes(d[pe + 20:pe + 22], 'little')
    base = pe + 24 + optsz
    r = []
    for i in range(nsec):
        o = base + i * 40
        nm = d[o:o + 8].rstrip(b'\x00').decode('ascii', 'replace')
        r.append((nm, int.from_bytes(d[o + 20:o + 24], 'little'),
                  int.from_bytes(d[o + 16:o + 20], 'little')))
    return r


def sec_of(secs, off):
    for nm, roff, rsize in secs:
        if roff <= off < roff + rsize:
            return nm
    return '?'


def ctx(b, off, n=48):
    pre = b[max(0, off - n):off].replace(b'\x00', b'|')
    post = b[off:off + n].replace(b'\x00', b'|')
    return (pre.decode('latin-1'), post.decode('latin-1'))


out = []
for dll in DLLS:
    p = os.path.join(PATCH, dll)
    if not os.path.exists(p):
        continue
    b = open(p, 'rb').read()
    secs = sections(b)
    for en, zh in PAIRS:
        eb, zb = en.encode('ascii'), zh.encode('gbk')
        # 英文份
        i, n = 0, 0
        while True:
            k = b.find(eb, i)
            if k < 0:
                break
            n += 1
            if n <= 4:
                a, c = ctx(b, k)
                out.append('  [EN] %-14s %-24s @0x%08X %-8s ...%s' % (dll[9:], en, k, sec_of(secs, k), a[-70:]))
            i = k + 1
        # 中文份
        j, m = 0, 0
        while True:
            k = b.find(zb, j)
            if k < 0:
                break
            m += 1
            if m <= 4:
                a, c = ctx(b, k)
                out.append('  [ZH] %-14s %-24s @0x%08X %-8s ...%s' % (dll[9:], zh, k, sec_of(secs, k), a[-70:]))
            j = k + 1
        out.append('  >> %s : 英文份 %d 处 / 中文份(%s) %d 处' % (en, n, zh, m))
        out.append('')

open(os.path.join(W, '_dup_probe.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('DONE')

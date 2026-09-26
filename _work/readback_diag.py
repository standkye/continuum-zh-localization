# -*- coding: utf-8 -*-
"""诊断 accept4 报的 3 处「回读不符」：看原始字节、改写后的字节、以及写入清单里附近的条目。"""
import os, json

W = r'D:\Programming project\插件汉化\_work'
BK = r'C:\Program Files\BorisFX\ContinuumAE\19\Backup-English'
PATCH = os.path.join(W, 'patched_dll_d')
writes = json.load(open(os.path.join(W, '_fix4_writes.json'), encoding='utf-8'))

CASES = [('Continuum_AE_16Bit.dll', 0x01088EDC),
         ('Continuum_AE_8Bit.dll', 0x010850EC),
         ('Continuum_AE_Float.dll', 0x010B39CC)]

out = []
for dll, off in CASES:
    a = open(os.path.join(BK, dll), 'rb').read()
    b = open(os.path.join(PATCH, dll), 'rb').read()
    out.append('=== %s @ 0x%08X ===' % (dll, off))
    out.append('  原始字节 : %r' % a[off - 24:off + 40])
    out.append('  改后字节 : %r' % b[off - 24:off + 40])
    out.append('  原始串   : %r' % a[off - 24:off + 40].split(b'\x00')[0])
    # 附近写入
    near = [(r[0], r[1], r[2], r[3], r[7] if len(r) > 7 else None)
            for r in writes if r[0] == dll and abs(r[1] - off) < 200]
    for n in sorted(near, key=lambda x: x[1]):
        out.append('    write @0x%08X .. +%s  %-24r -> %r' % (n[1], n[4], n[2], n[3]))
    out.append('')

open(os.path.join(W, '_readback_diag.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('DONE')

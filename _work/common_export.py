# -*- coding: utf-8 -*-
"""查 Continuum_Common_AE.dll 的导出名表，和我们新写进去的字符串有没有撞上。
DLL 的导出名也在 .rdata 里 —— 改掉它就等于把导出的函数改名，宿主按名导入就找不到（WinError 127）。
"""
import os, json, struct

W = r'D:\Programming project\插件汉化\_work'
BK = r'C:\Program Files\BorisFX\ContinuumAE\19\Backup-English'
NAME = 'Continuum_Common_AE.dll'

writes = json.load(open(os.path.join(W, '_fix4_writes.json'), encoding='utf-8'))
mine = [r for r in writes if r[0] == NAME]
out = ['%s 写入 %d 处，其中新增(独立记号) %d 处' % (NAME, len(mine),
                                                sum(1 for r in mine if r[5] == 'new'))]
out.append('')
out.append('--- 本 DLL 全部写入（最多列 60）---')
for r in sorted(mine, key=lambda x: x[1])[:60]:
    out.append('  0x%08X %-4s av=%-3d %-30r -> %r' % (r[1], r[5], r[6], r[2], r[3]))
out.append('')

# ---- 解析导出目录 ----
d = open(os.path.join(BK, NAME), 'rb').read()
pe = d.find(b'PE\x00\x00')
opt = pe + 24
magic = int.from_bytes(d[opt:opt + 2], 'little')
ddoff = opt + (112 if magic == 0x20b else 96)
exp_rva, exp_sz = struct.unpack_from('<II', d, ddoff)
secs = []
nsec = int.from_bytes(d[pe + 6:pe + 8], 'little')
optsz = int.from_bytes(d[pe + 20:pe + 22], 'little')
base = pe + 24 + optsz
for i in range(nsec):
    o = base + i * 40
    nm = d[o:o + 8].rstrip(b'\x00').decode('ascii', 'replace')
    vsz, va, rsz, ra = struct.unpack_from('<IIII', d, o + 8)
    secs.append((nm, va, vsz, ra, rsz))


def rva2off(rva):
    for nm, va, vsz, ra, rsz in secs:
        if va <= rva < va + max(vsz, rsz):
            return ra + (rva - va)
    return None


out.append('导出目录 RVA=0x%X，节表: %s' % (exp_rva, [s[0] for s in secs]))
if exp_rva:
    eo = rva2off(exp_rva)
    nfun, nnam = struct.unpack_from('<II', d, eo + 20)
    addr_names = struct.unpack_from('<I', d, eo + 32)[0]
    no = rva2off(addr_names)
    names = []
    for i in range(nnam):
        nrva = struct.unpack_from('<I', d, no + i * 4)[0]
        off = rva2off(nrva)
        s = d[off:d.find(b'\x00', off)].decode('ascii', 'replace')
        names.append((s, off))
    out.append('导出函数 %d 个，具名 %d 个' % (nfun, nnam))
    out.append('前 30 个导出名: %s' % [n for n, o in names[:30]])

    hit = []
    for (s, off) in names:
        for r in mine:
            if r[1] == off or (r[1] <= off < r[1] + (r[7] if len(r) > 7 else 0)):
                hit.append((s, hex(off), r[2], r[3]))
    out.append('')
    out.append('★ 撞上导出名的写入: %s' % (hit if hit else '无'))

open(os.path.join(W, '_common_export.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('DONE')

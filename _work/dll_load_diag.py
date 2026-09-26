# -*- coding: utf-8 -*-
"""定位 Continuum_AE_8Bit.dll 加载失败的真因

思路：修改必须落在「PE 数据目录之外」才算安全。
若改动落进 Import / Export / IAT / Reloc / Security 等目录区间，LoadLibrary 必失败。
"""
import os, struct, json, hashlib

OUT = r"D:\Programming project\插件汉化\_work\_dll_load_diag.txt"
lines = []
def p(s=''):
    lines.append(str(s))

BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
LIB = r"C:\Program Files\BorisFX\ContinuumAE\19\lib"
CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"

DIRNAMES = ['Export', 'Import', 'Resource', 'Exception', 'Security', 'BaseReloc',
            'Debug', 'Arch', 'GlobalPtr', 'TLS', 'LoadConfig', 'BoundImport',
            'IAT', 'DelayImport', 'CLR', 'Reserved']

def parse_pe(d):
    if d[:2] != b'MZ':
        return None
    pe = struct.unpack_from('<I', d, 0x3C)[0]
    if d[pe:pe + 4] != b'PE\x00\x00':
        return None
    nsec = struct.unpack_from('<H', d, pe + 6)[0]
    optsz = struct.unpack_from('<H', d, pe + 20)[0]
    magic = struct.unpack_from('<H', d, pe + 24)[0]
    is64 = (magic == 0x20b)
    dd = pe + 24 + (112 if is64 else 96)
    dirs = []
    for i in range(16):
        rva, size = struct.unpack_from('<II', d, dd + i * 8)
        dirs.append((DIRNAMES[i], rva, size))
    secs = []
    for i in range(nsec):
        s = pe + 24 + optsz + i * 40
        nm = d[s:s + 8].rstrip(b'\x00').decode('ascii', 'replace')
        vsz, va, rsz, ra = struct.unpack_from('<IIII', d, s + 8)
        secs.append((nm, va, vsz, ra, rsz))
    # checksum 字段偏移（optional header 内 +64）
    cksum_off = pe + 24 + 64
    chksum = struct.unpack_from('<I', d, cksum_off)[0]
    return dict(pe=pe, nsec=nsec, optsz=optsz, is64=is64, dirs=dirs,
                secs=secs, chksum=chksum, cksum_off=cksum_off)

def rva2off(rva, secs):
    for nm, va, vsz, ra, rsz in secs:
        if va <= rva < va + max(vsz, rsz):
            return ra + (rva - va)
    return None

p('=' * 76)
p('Continuum DLL 加载失败定位')
p('=' * 76)

targets = ['Continuum_AE_Float.dll', 'Continuum_AE_8Bit.dll', 'Continuum_AE_16Bit.dll',
           'Continuum_Common_AE.dll', 'Continuum_3DObjects_AE.dll']

for name in targets:
    sp = os.path.join(BK, name)
    dp = os.path.join(LIB, name)
    if not (os.path.exists(sp) and os.path.exists(dp)):
        p('\n%s : 文件缺失' % name); continue
    a = open(sp, 'rb').read()
    b = open(dp, 'rb').read()
    info = parse_pe(b)
    p()
    p('-' * 76)
    p('%s' % name)
    p('-' * 76)
    if info is None:
        p('  !! 不是有效 PE'); continue
    p('  文件大小 %d（备份 %d）%s' % (len(b), len(a), 'OK' if len(a) == len(b) else '!! 不一致'))
    p('  PE 偏移 0x%X  machine=0x%X  64bit=%s  节数=%d  checksum=0x%X'
      % (info['pe'], struct.unpack_from('<H', b, info['pe'] + 4)[0], info['is64'],
         info['nsec'], info['chksum']))

    # 数据目录区间（转成文件偏移）
    dir_ranges = []
    p('  --- 数据目录 ---')
    for nm, rva, size in info['dirs']:
        if rva == 0 or size == 0:
            continue
        off = rva2off(rva, info['secs'])
        if off is None:
            p('    %-12s rva=0x%-8X size=%-8d -> 映射不到文件偏移' % (nm, rva, size))
            continue
        dir_ranges.append((nm, off, off + size))
        p('    %-12s rva=0x%-8X size=%-8d -> off 0x%X..0x%X' % (nm, rva, size, off, off + size))

    # 节区间
    p('  --- 节 ---')
    for nm, va, vsz, ra, rsz in info['secs']:
        p('    %-10s va=0x%-8X vsz=0x%-8X raw=0x%-8X rsz=0x%-8X' % (nm, va, vsz, ra, rsz))

    # 全部改动位置
    diffs = [i for i in range(len(a)) if a[i] != b[i]]
    p('  --- 改动 ---')
    p('    改动字节总数: %d' % len(diffs))
    if diffs:
        p('    首个改动偏移 0x%X   最后改动偏移 0x%X' % (diffs[0], diffs[-1]))
        # 落在哪个数据目录？
        from collections import Counter
        hit = Counter()
        for i in diffs:
            t = None
            for nm, lo, hi in dir_ranges:
                if lo <= i < hi:
                    t = nm; break
            hit[t if t else '<数据目录外>'] += 1
        for k, v in hit.most_common():
            p('      %-16s %d 字节' % (k, v))
        # 落在哪个节？
        hit2 = Counter()
        for i in diffs:
            t = '<header>'
            for nm, va, vsz, ra, rsz in info['secs']:
                if ra <= i < ra + rsz:
                    t = nm; break
            hit2[t] += 1
        p('    节分布: %s' % dict(hit2))
        # 与文件尾签名区（Security）重叠？
        for nm, lo, hi in dir_ranges:
            if nm == 'Security':
                ov = sum(1 for i in diffs if lo <= i < hi)
                p('    !! Security(签名) 区间 0x%X..0x%X 内改动 %d 字节' % (lo, hi, ov))

# ---------------- LoadLibrary 实测 ----------------
p()
p('=' * 76)
p('LoadLibrary 实测（每支开独立子进程，防崩）')
p('=' * 76)

TEST = r'''
import ctypes, sys
p = sys.argv[1]
try:
    h = ctypes.WinDLL(p, mode=0)
    print("OK   loaded handle=%s" % h._handle)
except OSError as e:
    print("FAIL err=%s msg=%s" % (getattr(e, 'winerror', '?'), e))
except Exception as e:
    print("FAIL %s" % e)
'''

tf = os.path.join(r"D:\Programming project\插件汉化\_work", "_ll_test.py")
open(tf, 'w', encoding='utf-8').write(TEST)

import subprocess
PY = r'C:\Users\Jinna\.workbuddy\binaries\python\versions\3.13.12\python.exe'

for name in targets + ['BCCPlus.dll']:
    for tag, d in (('备份原版', BK), ('当前装机', LIB if name != 'BCCPlus.dll' else CONT)):
        fp = os.path.join(d, name)
        if not os.path.exists(fp):
            p('  %-28s %-8s 文件不存在' % (name, tag)); continue
        r = subprocess.run([PY, tf, fp], capture_output=True)
        o = (r.stdout + r.stderr).decode('utf-8', 'replace').strip().replace('\n', ' | ')
        p('  %-28s %-8s %s' % (name, tag, o))

open(OUT, 'w', encoding='utf-8').write('\n'.join(lines))
print('done')

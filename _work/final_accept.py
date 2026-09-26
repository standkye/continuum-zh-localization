# -*- coding: utf-8 -*-
"""★ 最终验收：英文备份 vs 【实际装到系统里的文件】

与补丁逻辑完全分离的只读复算。判据：
  aex  : 长度不变 / 改动只落在 eman+gtac 的 value 区间 / 新片段合法 UTF-8 / 未碰 .text
  dll  : 长度不变 / 改动只落在槽位链内 / 新片段合法 UTF-8 / .text 零改动
输出 _work/_final_accept.txt
"""
import os, json, struct
from collections import Counter

BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
BK_AEX = os.path.join(BK, 'aex')
CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"
LIB = r"C:\Program Files\BorisFX\ContinuumAE\19\lib"
WORK = r"D:\Programming project\插件汉化\_work"
DELIV = r"D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0"

out = []
def p(s=''):
    out.append(str(s))

# ============================================================ AEX
def find_records(d, key):
    res = []
    i = 0
    while True:
        j = d.find(key, i)
        if j < 0:
            break
        if d[j - 4:j] == b'MIB8':
            base = j - 4
            size = struct.unpack_from('<I', d, base + 12)[0]
            if 0 < size < 4096:
                res.append((base, size, base + 16))
        i = j + 4
    return res

def pe_sections(d):
    pe = struct.unpack_from('<I', d, 0x3C)[0]
    nsec = struct.unpack_from('<H', d, pe + 6)[0]
    optsz = struct.unpack_from('<H', d, pe + 20)[0]
    secs = []
    for i in range(nsec):
        s = pe + 24 + optsz + i * 40
        name = d[s:s + 8].rstrip(b'\x00').decode('ascii', 'replace')
        vsz, va, rsz, ra = struct.unpack_from('<IIII', d, s + 8)
        secs.append((name, ra, ra + rsz))
    return secs

p('=' * 72)
p('★ 最终验收（装机文件 vs 英文备份）')
p('  源 = %s' % BK)
p('  目标 = 系统安装目录')
p('=' * 72)
p()
p('--- 1) .aex 效果外壳（488 个）---')

files = sorted(f for f in os.listdir(BK_AEX) if f.lower().endswith('.aex'))
bad_len = bad_utf8 = out_of_target = total_changed = 0
sec_hits = Counter()
still_ascii = []
name_cnt = cat_cnt = 0
missing = []

for fn in files:
    sp = os.path.join(BK_AEX, fn)
    dp = os.path.join(CONT, fn)
    if not os.path.exists(dp):
        missing.append(fn); continue
    a = open(sp, 'rb').read()
    b = open(dp, 'rb').read()
    if len(a) != len(b):
        bad_len += 1; continue

    targets = set()
    for key in (b'eman', b'gtac'):
        for (base, size, val) in find_records(a, key):
            targets.update(range(val, val + size))
    for i in range(len(a)):
        if a[i] != b[i]:
            total_changed += 1
            if i not in targets:
                out_of_target += 1

    # 名字/分类是否已中文化
    for key, is_name in ((b'eman', True), (b'gtac', False)):
        for (base, size, val) in find_records(b, key):
            frag = b[val + 1:val + size].split(b'\x00')[0]
            if not frag:
                continue
            if max(frag) > 127:
                if is_name: name_cnt += 1
                else: cat_cnt += 1
            else:
                if is_name and frag.strip() and frag.strip() != b'':
                    still_ascii.append((fn, frag.decode('ascii', 'replace')))
            try:
                frag.decode('utf-8')
            except UnicodeDecodeError:
                bad_utf8 += 1

    for i in range(len(a)):
        if a[i] != b[i]:
            tag = '<header>'
            for sn, lo, hi in pe_sections(a):
                if lo <= i < hi:
                    tag = sn; break
            sec_hits[tag] += 1

p('  文件数            : %d（缺失 %d）' % (len(files), len(missing)))
p('  长度不一致        : %d' % bad_len)
p('  改动字节总数      : %d' % total_changed)
p('  改动落在目标外    : %d   <-- 必须 0' % out_of_target)
p('  新片段非法 UTF-8  : %d   <-- 必须 0' % bad_utf8)
p('  改动所在节分布    : %s' % dict(sec_hits))
p('  已中文化 效果名   : %d / %d' % (name_cnt, len(files)))
p('  已中文化 类型栏   : %d / %d' % (cat_cnt, len(files)))
p('  效果名仍纯 ASCII  : %d' % len(still_ascii))
for fn, s in still_ascii[:20]:
    p('        - %-36s %s' % (fn, s))

# ============================================================ DLL
p()
p('--- 2) 引擎 DLL（6 支）---')
chains = json.load(open(os.path.join(WORK, 'dll_chains.json'), encoding='utf-8'))

for name, ch in sorted(chains.items()):
    sp = os.path.join(BK, name)
    dp = os.path.join(CONT if name == 'BCCPlus.dll' else LIB, name)
    if not os.path.exists(sp):
        p('  %s : 备份缺失，跳过' % name); continue
    if not os.path.exists(dp):
        p('  %s : !! 装机缺失' % name); continue
    a = open(sp, 'rb').read()
    b = open(dp, 'rb').read()
    if len(a) != len(b):
        p('  %s : !! 长度不一致 %d vs %d' % (name, len(a), len(b))); continue
    targets = set()
    for off_s, arr in ch.items():
        cur = int(off_s)
        for s in arr:
            slot = max(8, ((len(s) + 1 + 7) // 8) * 8)
            targets.update(range(cur, cur + slot))
            cur += slot
    changed = outside = 0
    for i in range(len(a)):
        if a[i] != b[i]:
            changed += 1
            if i not in targets:
                outside += 1
    bad_utf8 = checked = 0
    for off_s, arr in ch.items():
        cur = int(off_s)
        for s in arr:
            slot = max(8, ((len(s) + 1 + 7) // 8) * 8)
            if a[cur:cur + slot] != b[cur:cur + slot]:
                frag = b[cur:cur + slot].split(b'\x00')[0]
                checked += 1
                try:
                    frag.decode('utf-8')
                except UnicodeDecodeError:
                    bad_utf8 += 1
            cur += slot
    hits = Counter()
    for i in range(len(a)):
        if a[i] != b[i]:
            tag = '<header>'
            for sn, lo, hi in pe_sections(a):
                if lo <= i < hi:
                    tag = sn; break
            hits[tag] += 1
    p('  %s' % name)
    p('      长度               : %d (与备份%s)' % (len(b), '相等' if len(a) == len(b) else '不等'))
    p('      改动字节 / 链外    : %d / %d   <-- 链外必须 0' % (changed, outside))
    p('      被改槽位 / 非法UTF8: %d / %d' % (checked, bad_utf8))
    p('      节分布             : %s   <-- .text 必须无' % dict(hits))

# ============================================================ 交付一致性
p()
p('--- 3) 装机 vs 交付目录 一致性 ---')
import hashlib
def sha(fp):
    h = hashlib.sha256()
    with open(fp, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()
d = 0; t = 0
for f in sorted(os.listdir(DELIV)):
    if f.lower().endswith('.aex'):
        tgt = os.path.join(CONT, f)
    elif f.lower().endswith('.dll') and f in chains:
        tgt = os.path.join(CONT if f == 'BCCPlus.dll' else LIB, f)
    else:
        continue
    t += 1
    if not os.path.exists(tgt) or sha(os.path.join(DELIV, f)) != sha(tgt):
        d += 1
p('  TOTAL_DIFF = %d / %d' % (d, t))

open(os.path.join(WORK, '_final_accept.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('done')

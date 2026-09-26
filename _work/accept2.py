# -*- coding: utf-8 -*-
"""★ 修复版独立验收（源=英文备份，目标=新补丁产物 patched_aex_b / patched_dll_b）"""
import os, json, struct
from collections import Counter

WORK = r"D:\Programming project\插件汉化\_work"
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
BK_AEX = os.path.join(BK, 'aex')
PA = os.path.join(WORK, 'patched_aex_b')
PD = os.path.join(WORK, 'patched_dll_b')

out = []
def p(s=''):
    out.append(str(s))

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
        nm = d[s:s + 8].rstrip(b'\x00').decode('ascii', 'replace')
        vsz, va, rsz, ra = struct.unpack_from('<IIII', d, s + 8)
        secs.append((nm, ra, ra + rsz))
    return secs

p('=' * 76)
p('★ 修复版验收（GBK）')
p('=' * 76)

# ---------------- aex ----------------
p()
p('--- 1) .aex（488 个）---')
files = sorted(f for f in os.listdir(BK_AEX) if f.lower().endswith('.aex'))
bad_len = out_of_range = bad_enc = 0
nname = ncat = 0
secs = Counter()
still_ascii_name = []
still_ascii_cat = []

for fn in files:
    a = open(os.path.join(BK_AEX, fn), 'rb').read()
    fp = os.path.join(PA, fn)
    if not os.path.exists(fp):
        p('  !! 缺失 ' + fn); continue
    b = open(fp, 'rb').read()
    if len(a) != len(b):
        bad_len += 1; continue
    target = set()
    for key in (b'eman', b'gtac'):
        for (base, size, val) in find_records(a, key):
            target.update(range(val, val + size))
    for i in range(len(a)):
        if a[i] != b[i]:
            if i not in target:
                out_of_range += 1
            for nm, lo, hi in pe_sections(a):
                if lo <= i < hi:
                    secs[nm] += 1; break
    # 回读
    for key, isname in ((b'eman', True), (b'gtac', False)):
        for (base, size, val) in find_records(b, key):
            frag = b[val + 1:val + size].split(b'\x00')[0]
            if not frag:
                continue
            try:
                frag.decode('gbk')
            except UnicodeDecodeError:
                bad_enc += 1
            if max(frag) > 127:
                if isname: nname += 1
                else: ncat += 1
            else:
                if isname: still_ascii_name.append((fn, frag.decode('ascii', 'replace')))

p('  文件数 %d   长度不一致 %d' % (len(files), bad_len))
p('  改动落在 eman/gtac 区间外 %d   <-- 必须 0' % out_of_range)
p('  新片段非法 GBK %d               <-- 必须 0' % bad_enc)
p('  改动所在节 %s' % dict(secs))
p('  效果名中文化 %d / %d' % (nname, len(files)))
p('  类型栏中文化 %d / %d' % (ncat, len(files)))
p('  效果名仍纯 ASCII %d' % len(still_ascii_name))
for fn, s in still_ascii_name[:10]:
    p('      - %-34s %s' % (fn, s))

# ---------------- dll ----------------
p()
p('--- 2) 引擎 DLL（6 支）---')
chains = json.load(open(os.path.join(WORK, 'dll_chains.json'), encoding='utf-8'))
tot_changed = 0
for name in sorted(chains):
    sp = os.path.join(BK, name)
    dp = os.path.join(PD, name)
    if not (os.path.exists(sp) and os.path.exists(dp)):
        p('  %s : 缺失' % name); continue
    a = open(sp, 'rb').read()
    b = open(dp, 'rb').read()
    if len(a) != len(b):
        p('  %s : !! 长度不一致' % name); continue
    targets = set()
    for off_s, arr in chains[name].items():
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
    bad_utf = checked = 0
    for off_s, arr in chains[name].items():
        cur = int(off_s)
        for s in arr:
            slot = max(8, ((len(s) + 1 + 7) // 8) * 8)
            if a[cur:cur + slot] != b[cur:cur + slot]:
                frag = b[cur:cur + slot].split(b'\x00')[0]
                checked += 1
                try:
                    frag.decode('gbk')
                except UnicodeDecodeError:
                    bad_utf += 1
            cur += slot
    hits = Counter()
    for i in range(len(a)):
        if a[i] != b[i]:
            tag = '<header>'
            for nm, lo, hi in pe_sections(a):
                if lo <= i < hi:
                    tag = nm; break
            hits[tag] += 1
    tot_changed += changed
    p('  %-30s 长度一致=True  改动 %5d  链外 %d  被改槽位 %4d  非法GBK %d  节 %s'
      % (name, changed, outside, checked, bad_utf, dict(hits)))

p()
p('DLL 改动字节合计: %d' % tot_changed)

open(os.path.join(WORK, '_accept2.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('done')

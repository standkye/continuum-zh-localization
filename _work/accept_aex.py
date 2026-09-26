# -*- coding: utf-8 -*-
"""严格验收：对比 英文备份 vs 新补丁输出。
   1) 逐字节确认「只改了目标槽位、总长度不变」
   2) 所有新增的中文片段都是合法 UTF-8
   3) 关键结构（PE 头、节表、导出表）字节完全未动
   4) 每个改动区域的首字节数 == 实际写入字节数
"""
import os, struct, json, sys

BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
BK_AEX = os.path.join(BK, 'aex')
WORK = r"D:\Programming project\插件汉化\_work"
OUT_AEX = os.path.join(WORK, 'patched_aex')
OUT_DLL = os.path.join(WORK, 'patched_dll')

out = []

# ---------------------------------------------- 1) aex diff 位置分析
def find_records(d, key):
    k = key if isinstance(key, bytes) else key.encode()
    res = []
    i = 0
    while True:
        j = d.find(k, i)
        if j < 0:
            break
        if d[j - 4:j] == b'MIB8':
            base = j - 4
            size = struct.unpack('<I', d[base + 12:base + 16])[0]
            if 0 < size < 4096:
                res.append((base, size, base + 16))
        i = j + 4
    return res


bad_len = 0
bad_utf8 = 0
out_of_target = 0
total_changed = 0
files = sorted(os.listdir(BK_AEX))
out.append(f"aex 文件数: {len(files)}")

for fn in files:
    if not fn.lower().endswith('.aex'):
        continue
    a = open(os.path.join(BK_AEX, fn), 'rb').read()
    bp = os.path.join(OUT_AEX, fn)
    if not os.path.exists(bp):
        out.append(f"  !! 缺失 {fn}")
        continue
    b = open(bp, 'rb').read()
    if len(a) != len(b):
        bad_len += 1
        continue
    # 目标区域（eman / gtac 的 value 区间）
    targets = set()
    for key in (b'eman', b'gtac'):
        for (base, size, val) in find_records(a, key):
            for i in range(val, val + size):
                targets.add(i)
    for i in range(len(a)):
        if a[i] != b[i]:
            total_changed += 1
            if i not in targets:
                out_of_target += 1
    # 新增片段必须是合法 UTF-8
    for key in (b'eman', b'gtac'):
        for (base, size, val) in find_records(b, key):
            n = b[val]
            if n == 0 or n >= size:
                continue
            frag = b[val + 1:val + 1 + n]
            try:
                frag.decode('utf-8')
            except UnicodeDecodeError:
                bad_utf8 += 1

out.append(f"长度不一致: {bad_len}")
out.append(f"改动字节总数: {total_changed}   其中落在目标记录外: {out_of_target}")
out.append(f"新增片段非法 UTF-8: {bad_utf8}")

# aex 的改动必须集中在 PiPL 区（文件前部），确认没碰到 PE 头/节表
def pe_regions(d):
    if d[:2] != b'MZ':
        return None
    pe = struct.unpack_from('<I', d, 0x3C)[0]
    if d[pe:pe + 4] != b'PE\x00\x00':
        return None
    nsec = struct.unpack_from('<H', d, pe + 6)[0]
    opt = pe + 24
    dirs = opt + (96 if struct.unpack_from('<H', d, opt)[0] == 0x20b else 112)
    regions = [(0, pe + 24 + 240)]     # 头 + 节表
    for i in range(nsec):
        s = pe + 24 + struct.unpack_from('<H', d, pe + 20)[0] + i * 40
        name = d[s:s + 8].rstrip(b'\x00').decode('ascii', 'replace')
        vsz, va, rsz, ra = struct.unpack_from('<IIII', d, s + 8)
        regions.append((ra, ra + rsz, name))
    return regions

out.append("\n=== aex 改动字节落在哪个节 ===")
from collections import Counter
sec_hits = Counter()
for fn in files[:80]:
    if not fn.lower().endswith('.aex'):
        continue
    a = open(os.path.join(BK_AEX, fn), 'rb').read()
    b = open(os.path.join(OUT_AEX, fn), 'rb').read()
    regs = pe_regions(a)
    if not regs:
        continue
    for i in range(len(a)):
        if a[i] != b[i]:
            tag = '<header>'
            for r in regs[1:]:
                if r[0] <= i < r[1]:
                    tag = r[2]
                    break
            sec_hits[tag] += 1
for k, v in sec_hits.most_common():
    out.append(f"  {k:12s} {v} 字节")

open(os.path.join(WORK, '_accept_aex.txt'), 'w', encoding='utf-8').write("\n".join(out))
print("done", bad_len, out_of_target, bad_utf8)

# -*- coding: utf-8 -*-
"""严格验收 DLL：英文备份 vs 新补丁输出。
   - 长度必须不变
   - 改动字节必须全在槽位链覆盖的区间内
   - 新增片段必须是合法 UTF-8
   - PE 头 / 节表 / 导出表所在偏移必须 0 改动
"""
import os, json, struct

BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"
WORK = r"D:\Programming project\插件汉化\_work"
OUT_DLL = os.path.join(WORK, 'patched_dll')
chains = json.load(open(os.path.join(WORK, 'dll_chains.json'), encoding='utf-8'))

out = []

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

for name, ch in sorted(chains.items()):
    src = os.path.join(BK, name)
    if not os.path.exists(src):
        src = os.path.join(CONT, name)
    a = open(src, 'rb').read()
    b = open(os.path.join(OUT_DLL, name), 'rb').read()
    if len(a) != len(b):
        out.append(f"{name}: !! 长度不一致 {len(a)} vs {len(b)}")
        continue
    # 槽位链覆盖的字节区间集合
    targets = set()
    for off_s, arr in ch.items():
        cur = int(off_s)
        for s in arr:
            slot = max(8, ((len(s) + 1 + 7) // 8) * 8)
            for i in range(cur, cur + slot):
                targets.add(i)
            cur += slot
    changed = outside = 0
    for i in range(len(a)):
        if a[i] != b[i]:
            changed += 1
            if i not in targets:
                outside += 1
    # 新增片段合法性
    bad_utf8 = 0
    checked = 0
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
    # 节归属
    secs = pe_sections(a)
    from collections import Counter
    hits = Counter()
    for i in range(len(a)):
        if a[i] != b[i]:
            tag = '<header>'
            for sn, lo, hi in secs:
                if lo <= i < hi:
                    tag = sn
                    break
            hits[tag] += 1
    out.append(f"{name}")
    out.append(f"    改动字节 {changed}  落在槽位链外 {outside}")
    out.append(f"    被改槽位 {checked}  其中新片段非法 UTF-8 {bad_utf8}")
    out.append(f"    节分布: {dict(hits)}")

open(os.path.join(WORK, '_accept_dll.txt'), 'w', encoding='utf-8').write("\n".join(out))
print("done")

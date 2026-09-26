# -*- coding: utf-8 -*-
"""最终人工目检：随机抽若干 .aex 和 DLL 槽位，看中文是否可读、UTF-8 是否干净。"""
import os, struct, json, random

BK_AEX = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English\aex"
OUT_AEX = r"D:\Programming project\插件汉化\_work\patched_aex"
WORK = r"D:\Programming project\插件汉化\_work"
OUT_DLL = os.path.join(WORK, 'patched_dll')
chains = json.load(open(os.path.join(WORK, 'dll_chains.json'), encoding='utf-8'))

out = []

def records(d, key):
    k = key if isinstance(key, bytes) else key.encode()
    res = []; i = 0
    while True:
        j = d.find(k, i)
        if j < 0: break
        if d[j - 4:j] == b'MIB8':
            size = struct.unpack('<I', d[j + 8:j + 12])[0]
            if 0 < size < 4096:
                res.append((size, j + 12))
        i = j + 4
    return res

random.seed(20260925)
files = sorted(f for f in os.listdir(OUT_AEX) if f.lower().endswith('.aex'))
sample = random.sample(files, 30)
out.append("=== .aex 效果名 / 类型栏（随机 30 个）===")
for fn in sample:
    d = open(os.path.join(OUT_AEX, fn), 'rb').read()
    em = []
    for (size, val) in records(d, 'eman'):
        n = d[val]
        frag = d[val + 1:val + 1 + n].split(b'\x00')[0] if n else b''
        em.append(frag.decode('utf-8', 'replace'))
    ct = []
    for (size, val) in records(d, 'gtac'):
        n = d[val]
        frag = d[val + 1:val + 1 + n].split(b'\x00')[0] if n else b''
        ct.append(frag.decode('utf-8', 'replace'))
    out.append(f"  {fn[:34]:36s} {em}  [{ct}]")

out.append("\n=== DLL 参数名（随机槽位，只看被改过的）===")
for name in ['Continuum_AE_Float.dll', 'Continuum_AE_8Bit.dll',
             'Continuum_3DObjects_AE.dll', 'BCCPlus.dll']:
    src = os.path.join(r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English", name)
    a = open(src, 'rb').read()
    b = open(os.path.join(OUT_DLL, name), 'rb').read()
    ch = chains[name]
    got = []
    # 找若干「中文（含非 ASCII）」的槽位
    for off_s, arr in ch.items():
        cur = int(off_s)
        for s in arr:
            slot = max(8, ((len(s) + 1 + 7) // 8) * 8)
            seg = b[cur:cur + slot]
            if seg != a[cur:cur + slot]:
                frag = seg.split(b'\x00')[0]
                try:
                    t = frag.decode('utf-8')
                    if any(ord(c) > 127 for c in t):
                        got.append((s, t))
                except UnicodeDecodeError:
                    got.append((s, '!!INVALID UTF-8!!'))
            cur += slot
        if len(got) > 400:
            break
    out.append(f"\n  {name}  （共 {len(got)}+ 个已汉化槽位，抽样 24）")
    for i in range(0, min(len(got), 24 * 8), 8):
        out.append("    " + " | ".join(f"{a0}→{b0}" for a0, b0 in got[i:i + 8]))

open(os.path.join(WORK, '_final_readback.txt'), 'w', encoding='utf-8').write("\n".join(out))
print("done")

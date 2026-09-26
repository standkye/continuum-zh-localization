# -*- coding: utf-8 -*-
import os, re, json, struct

WORK = r"D:\Programming project\插件汉化\_work"
OUT_AEX = os.path.join(WORK, 'patched_aex')
OUT_DLL = os.path.join(WORK, 'patched_dll')
out = []

def pipl_names(path):
    d = open(path, 'rb').read()
    res = []
    for m in re.finditer(rb'MIB8', d):
        p = m.start()
        key = d[p + 4:p + 8]
        if key != b'eman':
            continue
        size = struct.unpack_from('<I', d, p + 12)[0]
        val = d[p + 16:p + 16 + size]
        s = val[1:].split(b'\x00')[0]
        res.append(s)
    return res

out.append("=== 回读 .aex 效果名（UTF-8 解码）===")
files = sorted(os.listdir(OUT_AEX))
for fn in files[:12] + files[200:206] + files[-6:]:
    ns = pipl_names(os.path.join(OUT_AEX, fn))
    out.append(f"  {fn[:34]:36s} -> {[n.decode('utf-8','replace') for n in ns]}")

out.append("\n=== 回读 DLL 参数名 ===")
chains = json.load(open(os.path.join(WORK, 'dll_chains.json'), encoding='utf-8'))
for name in ['Continuum_AE_Float.dll', 'BCCPlus.dll', 'Continuum_3DObjects_AE.dll']:
    p = os.path.join(OUT_DLL, name)
    if not os.path.exists(p):
        continue
    d = open(p, 'rb').read()
    ch = chains[name]
    best = max(ch.items(), key=lambda kv: len(kv[1]))
    off = int(best[0]); arr = best[1]
    read = []
    cur = off
    for s in arr[:14]:
        slot = max(8, ((len(s) + 1 + 7) // 8) * 8)
        raw = d[cur:cur + slot].split(b'\x00')[0]
        read.append(raw.decode('utf-8', 'replace'))
        cur += slot
    out.append(f"  {name}: {read}")
    # 再取一条中等链
    mid = sorted(ch.items(), key=lambda kv: -len(kv[1]))[3]
    off = int(mid[0]); arr = mid[1]
    read = []
    cur = off
    for s in arr[:12]:
        slot = max(8, ((len(s) + 1 + 7) // 8) * 8)
        read.append(d[cur:cur + slot].split(b'\x00')[0].decode('utf-8', 'replace'))
        cur += slot
    out.append(f"      {read}")

open(os.path.join(WORK, 'verify_report.txt'), 'w', encoding='utf-8').write("\n".join(out))

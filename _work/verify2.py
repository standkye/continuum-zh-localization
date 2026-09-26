# -*- coding: utf-8 -*-
import os, json
WORK = r"D:\Programming project\插件汉化\_work"
OUT_DLL = os.path.join(WORK, 'patched_dll')
hits = json.load(open(os.path.join(WORK, 'chain_hits.json'), encoding='utf-8'))
out = []
for name, rows in hits.items():
    p = os.path.join(OUT_DLL, name)
    if not os.path.exists(p) or not rows:
        continue
    d = open(p, 'rb').read()
    out.append(f"\n=== {name} ===")
    for off, n, k, arr in rows[:3]:
        read = []
        cur = int(off)
        for s in arr[:16]:
            slot = max(8, ((len(s) + 1 + 7) // 8) * 8)
            read.append(d[cur:cur + slot].split(b'\x00')[0].decode('gbk', 'ignore'))
            cur += slot
        out.append(f"  链@{off} (长{n}, 参数名命中{k}):")
        out.append(f"    原: {arr[:16]}")
        out.append(f"    新: {read}")
open(os.path.join(WORK, 'verify_report.txt'), 'w', encoding='utf-8').write("\n".join(out))

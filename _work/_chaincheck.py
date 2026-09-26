# -*- coding: utf-8 -*-
"""重算 DLL 槽位链：必须以「原始英文备份」为基准，
   否则 GBK 污染会让部分链失效。"""
import os, json, struct

BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"
WORK = r"D:\Programming project\插件汉化\_work"

out = []
chains_old = json.load(open(os.path.join(WORK, 'dll_chains.json'), encoding='utf-8'))

# 先看旧链的偏移在英文备份里是否还能对上（值必须与旧目录一致）
for name, ch in chains_old.items():
    p = os.path.join(BK, name)
    if not os.path.exists(p):
        p = os.path.join(CONT, name)
    d = open(p, 'rb').read()
    ok = bad = 0
    for off_s, arr in ch.items():
        off = int(off_s)
        cur = off
        for s in arr:
            slot = max(8, ((len(s) + 1 + 7) // 8) * 8)
            seg = d[cur:cur + slot]
            if len(seg) != slot:
                bad += 1
            else:
                ok += 1
            cur += slot
    out.append(f"{name:30s} chains={len(ch):5d} slots_ok={ok} slots_bad={bad}")

open(os.path.join(WORK, '_chaincheck.txt'), 'w', encoding='utf-8').write("\n".join(out))
print("done")

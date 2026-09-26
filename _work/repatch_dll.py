# -*- coding: utf-8 -*-
"""从「原始英文备份」重建 DLL 参数名补丁（UTF-8）。"""
import os, json, sys

BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"
WORK = r"D:\Programming project\插件汉化\_work"
OUT_DLL = os.path.join(WORK, 'patched_dll')
os.makedirs(OUT_DLL, exist_ok=True)

param_zh = json.load(open(os.path.join(WORK, 'param_zh.json'), encoding='utf-8'))
for extra in ('hand_all.json', 'hand_other.json', 'hand_other2.json'):
    p = os.path.join(WORK, extra)
    if os.path.exists(p):
        param_zh.update(json.load(open(p, encoding='utf-8')))

chains = json.load(open(os.path.join(WORK, 'dll_chains.json'), encoding='utf-8'))
out = [f"param_zh entries: {len(param_zh)}"]
out.append("\n=== DLL（源：Backup-English，UTF-8）===")

skip_overflow = 0
skip_unsafe = 0
for name, ch in sorted(chains.items()):
    src = os.path.join(BK, name)
    if not os.path.exists(src):
        src = os.path.join(CONT, name)
    d = bytearray(open(src, 'rb').read())
    orig_len = len(d)
    n = 0
    ov = us = 0
    for off_s, arr in ch.items():
        cur = int(off_s)
        for s in arr:
            slot = max(8, ((len(s) + 1 + 7) // 8) * 8)
            zh = param_zh.get(s)
            if zh:
                b = zh.encode('utf-8')
                if len(b) <= slot - 1:
                    raw = d[cur:cur + slot]
                    nul = raw.find(b'\x00')
                    # 源槽位必须是 [文本][连续 NUL 填充]
                    safe = (nul > 0 and not any(raw[nul:]) and len(raw) == slot)
                    if safe:
                        d[cur:cur + slot] = b'\x00' * slot
                        d[cur:cur + len(b)] = b
                        n += 1
                    else:
                        us += 1
                else:
                    ov += 1
            cur += slot
    assert len(d) == orig_len
    open(os.path.join(OUT_DLL, name), 'wb').write(bytes(d))
    skip_overflow += ov
    skip_unsafe += us
    out.append(f"{name:28s} 替换 {n:5d} 处  容量不足保留英文 {ov:4d}  槽位存疑 {us:3d}  大小一致=True")

out.append(f"\n合计：容量不足保留英文 {skip_overflow}，槽位存疑跳过 {skip_unsafe}")
open(os.path.join(WORK, '_repatch_dll.txt'), 'w', encoding='utf-8').write("\n".join(out))
print("dll done")

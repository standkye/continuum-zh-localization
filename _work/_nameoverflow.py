# -*- coding: utf-8 -*-
"""统计 UTF-8 下放不下的效果名/类型栏，并给出可用的紧凑译名候选。"""
import os, struct, sys
sys.path.insert(0, r"D:\Programming project\插件汉化\_work")
import names_manual

BK_AEX = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English\aex"

def records(d, key):
    k = key.encode(); res = []; i = 0
    while True:
        j = d.find(k, i)
        if j < 0: break
        if d[j - 4:j] == b'MIB8':
            base = j - 4
            size = struct.unpack('<I', d[base + 12:base + 16])[0]
            if 0 < size < 4096:
                res.append((base, size, base + 16))
        i = j + 4
    return res

out = []
over = []
for fn in sorted(os.listdir(BK_AEX)):
    if not fn.lower().endswith('.aex'):
        continue
    d = open(os.path.join(BK_AEX, fn), 'rb').read()
    for (base, size, val) in records(d, 'eman'):
        n = d[val]
        payload = d[val + 1:val + 1 + n].split(b'\x00')[0] if n else b''
        if not payload:
            continue
        try:
            en = payload.decode('utf-8')
        except UnicodeDecodeError:
            continue
        zh = names_manual.NAMES.get(en) or names_manual.NAMES.get(en.strip())
        if not zh:
            continue
        pre = 'BCC ' if en.startswith('BCC ') else ('BCC+' if en.startswith('BCC+') else '')
        text = pre + zh
        b = text.encode('utf-8')
        cap = size - 2
        if len(b) > cap:
            over.append((fn, en, zh, text, len(b), cap, size))

out.append(f"eman 放不下（UTF-8 超容）共 {len(over)} 条")
out.append(f"{'文件':34s} {'英文名':32s} {'中文':16s} {'需':>4s} {'可用':>4s} {'size':>5s}")
for fn, en, zh, text, need, cap, size in over:
    worst = (need - cap + 2) // 3      # 需再砍几个汉字
    out.append(f"{fn[:32]:34s} {en:32s} {zh:16s} {need:4d} {cap:4d} {size:5d}   需砍 {worst} 字")

open(r"D:\Programming project\插件汉化\_work\_nameoverflow.txt", 'w', encoding='utf-8').write("\n".join(out))
print("done", len(over))

# -*- coding: utf-8 -*-
"""为什么这 24 条「明明放得下」却没被改？逐条打印 patch 里的判定中间值。"""
import os, struct, sys
sys.path.insert(0, r"D:\Programming project\插件汉化\_work")
import names_manual as M

BK_AEX = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English\aex"

def find_records(d, key):
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

targets = ['BCC 3 Way Color Grade', 'BCC 3D Image Shatter', 'BCC Bulge',
           'BCC Color Balance', 'BCC Levels Gamma', 'BCC Warp', 'BCC Trails']

o = []
for fn in sorted(os.listdir(BK_AEX)):
    if not fn.lower().endswith('.aex'): continue
    d = open(os.path.join(BK_AEX, fn), 'rb').read()
    for (base, size, val) in find_records(d, 'eman'):
        n = d[val]
        if n == 0 or n >= size:
            o.append(f"{fn[:30]:32s} n={n} size={size}  -> n 越界, 被 continue 跳过")
            continue
        payload = d[val + 1:val + 1 + n].split(b'\x00')[0]
        if not payload:
            o.append(f"{fn[:30]:32s} n={n} payload 空")
            continue
        try:
            en = payload.decode('utf-8')
        except UnicodeDecodeError as e:
            o.append(f"{fn[:30]:32s} n={n} UTF8 解码失败 {e}  payload={payload!r}")
            continue
        if en not in targets: continue
        zh = M.NAMES.get(en) or M.NAMES.get(en.strip()) or M.NAMES.get('BCC ' + en)
        pre = 'BCC+' if en.startswith('BCC+') else ('BCC ' if en.startswith('BCC ') else '')
        cap = size - 2
        cands = []
        if pre and not zh.startswith('BCC'): cands.append(pre + zh)
        cands.append(zh)
        sh = M.SHORT.get(en) or M.SHORT.get(en.strip())
        if sh:
            if pre and not sh.startswith('BCC'): cands.append(pre + sh)
            cands.append(sh)
        ok = any(len(c.encode('utf-8')) <= cap and len(c.encode('utf-8')) <= 255 for c in cands)
        o.append(f"{fn[:30]:32s} n={n} size={size} cap={cap} en={en!r}")
        o.append(f"      zh={zh!r} pre={pre!r} cands={[(c, len(c.encode('utf-8'))) for c in cands]} -> 应可改={ok}")

open(r"D:\Programming project\插件汉化\_work\_why24.txt", 'w', encoding='utf-8').write("\n".join(o))
print("done")

# -*- coding: utf-8 -*-
"""准确统计：补丁后仍完全为 ASCII（真·未汉化）的效果名，并给出原因。
   判定必须复现 patch 的候选顺序：full -> short -> 保留英文。"""
import os, struct, sys
sys.path.insert(0, r"D:\Programming project\插件汉化\_work")
import names_manual as M

OUT = r"D:\Programming project\插件汉化\_work\patched_aex"
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English\aex"

def rec(d, key):
    k = key.encode(); res = []; i = 0
    while True:
        j = d.find(k, i)
        if j < 0: break
        if d[j - 4:j] == b'MIB8':
            size = struct.unpack('<I', d[j + 8:j + 12])[0]
            if 0 < size < 4096: res.append((size, j + 12))
        i = j + 4
    return res

still = []
counted = 0
for fn in sorted(os.listdir(OUT)):
    if not fn.lower().endswith('.aex'): continue
    d = open(os.path.join(OUT, fn), 'rb').read()
    for size, val in rec(d, 'eman'):
        n = d[val]
        frag = d[val + 1:val + 1 + n].split(b'\x00')[0] if n else b''
        if not frag: continue
        try: t = frag.decode('utf-8')
        except UnicodeDecodeError: continue
        counted += 1
        if any(ord(c) > 127 for c in t):
            continue                      # 已成功汉化
        zh = M.NAMES.get(t) or M.NAMES.get(t.strip())
        cap = size - 2
        if not zh:
            still.append((fn, t, '<词典无此键>', None, cap))
        else:
            pre = 'BCC ' if t.startswith('BCC ') else ('BCC+' if t.startswith('BCC+') else '')
            sh = M.SHORT.get(t) or M.SHORT.get(t.strip())
            opts = [pre + zh if pre and not zh.startswith('BCC') else zh]
            if sh: opts.append(pre + sh if pre and not sh.startswith('BCC') else sh)
            best = min(len(o.encode('utf-8')) for o in opts)
            still.append((fn, t, zh, best, cap))

o = [f"eman 总数 {counted}，其中仍为纯 ASCII（未汉化）{len(still)} 条"]
o.append(f"{'文件':34s} {'英文名':34s} {'词典':16s} {'最短需':>6s} {'可用':>5s} 原因")
for fn, t, zh, best, cap in still:
    if best is None: why = '词典缺键'
    elif best > cap: why = f'超容 {best - cap} 字节'
    else: why = '??? 不该发生'
    o.append(f"{fn[:32]:34s} {t[:32]:34s} {str(zh)[:14]:16s} {str(best):>6s} {cap:5d} {why}")
open(r"D:\Programming project\插件汉化\_work\_still_en2.txt", 'w', encoding='utf-8').write("\n".join(o))
print("still ascii:", len(still), "of", counted)

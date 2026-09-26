# -*- coding: utf-8 -*-
"""逐字节看这 4 个文件里 eman 记录的真实结构，找出为何没改。"""
import os, struct, sys
sys.path.insert(0, r"D:\Programming project\插件汉化\_work")

BK_AEX = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English\aex"
OUT_AEX = r"D:\Programming project\插件汉化\_work\patched_aex"

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
for fn in ['BCC3WayColorGrade.aex', 'BCCPosterize.aex', 'BCCAlphaProcess.aex',
           'BCCAlphaPixelNoise.aex', 'BCCBlur.aex', 'BCCHalftone.aex',
           'BCCMatchMove.aex', 'BCCBeatReactor.aex']:
    for tag, base_dir in (('EN', BK_AEX), ('OUT', OUT_AEX)):
        p = os.path.join(base_dir, fn)
        if not os.path.exists(p):
            out.append(f"{fn} [{tag}] 不存在")
            continue
        d = open(p, 'rb').read()
        for (base, size, val) in records(d, 'eman'):
            n = d[val]
            raw = d[val:val + size]
            payload = raw[1:1 + n]
            out.append(f"{fn} [{tag}] base={base} size={size} val={val} n={n}")
            out.append(f"      raw    = {raw!r}")
            out.append(f"      payload= {payload!r}")
            for enc in ('utf-8', 'gbk'):
                try:
                    out.append(f"      {enc} 解 = {payload.decode(enc)!r}")
                except UnicodeDecodeError as e:
                    out.append(f"      {enc} 解失败: {e}")
        out.append("")

open(r"D:\Programming project\插件汉化\_work\_emnprobe.txt", 'w', encoding='utf-8').write("\n".join(out))
print("done")

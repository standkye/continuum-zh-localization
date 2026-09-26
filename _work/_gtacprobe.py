# -*- coding: utf-8 -*-
"""诊断 gtac：源内容、解码、_CATS 匹配情况。"""
import os, struct, sys
sys.path.insert(0, r"D:\Programming project\插件汉化\_work")
from names_manual import CATS as _CATS

CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"
WORK = r"D:\Programming project\插件汉化\_work"
out = []

def find_records(d, key):
    k = key.encode()
    res = []
    i = 0
    while True:
        j = d.find(k, i)
        if j < 0:
            break
        if d[j - 4:j] == b'MIB8':
            base = j - 4
            size = struct.unpack('<I', d[base + 12:base + 16])[0]
            if 0 < size < 4096:
                res.append((base, size, base + 16))
        i = j + 4
    return res

files = sorted(os.listdir(CONT))
files = [f for f in files if f.lower().endswith('.aex')]
out.append(f"aex 数量: {len(files)}")

from collections import Counter
cnt = Counter()
samples = []
nomatch = []
for fn in files:
    d = open(os.path.join(CONT, fn), 'rb').read()
    for (base, size, val) in find_records(d, 'gtac'):
        raw = d[val:val + size]
        n = raw[0]
        payload = raw[1:1 + n]
        dec = None
        for enc in ('utf-8', 'gbk'):
            try:
                dec = (enc, payload.decode(enc))
                break
            except UnicodeDecodeError:
                pass
        if dec is None:
            cnt['<undecodable>'] += 1
            continue
        enc, txt = dec
        cnt[f"{enc}:{txt}"] += 1
        if len(samples) < 10:
            samples.append((fn, enc, txt, size, n))
        if txt not in _CATS and not txt.startswith('BCC'):
            nomatch.append((fn, txt))

out.append("\n=== 源 gtac 解码分布（前 40）===")
for k, v in cnt.most_common(40):
    out.append(f"  {v:5d}  {k}")

out.append("\n=== 样例 ===")
for s in samples:
    out.append(f"  {s[0][:30]:32s} enc={s[1]:6s} size={s[3]} n={s[4]} text={s[2]!r}")

out.append(f"\n=== 不在 _CATS 键里的（前 30 / 共 {len(nomatch)}）===")
for fn, t in nomatch[:30]:
    out.append(f"  {fn[:30]:32s} {t!r}")

open(os.path.join(WORK, '_gtacprobe.txt'), 'w', encoding='utf-8').write("\n".join(out))
print("done")

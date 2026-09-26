# -*- coding: utf-8 -*-
"""1) 修正 PiPL 解析，拿到全部 488 个效果名
   2) 用预设 <name> 反查 DLL 槽位链，定位真正的参数名表"""
import os, re, json, struct
from collections import Counter

CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"
LIB = r"C:\Program Files\BorisFX\ContinuumAE\19\lib"
WORK = r"D:\Programming project\插件汉化\_work"
out = []

# ---------- 1. 效果名（修正：val[1:] 截到第一个 NUL） ----------
def pipl(path):
    with open(path, 'rb') as f:
        d = f.read()
    res = []
    for m in re.finditer(rb'MIB8', d):
        p = m.start()
        key = d[p + 4:p + 8]
        if key not in (b'eman', b'gtac'):
            continue
        size = struct.unpack_from('<I', d, p + 12)[0]
        if size == 0 or size > 512:
            continue
        val = d[p + 16:p + 16 + size]
        if len(val) < 2:
            continue
        s = val[1:].split(b'\x00')[0]
        if not s:
            continue
        try:
            t = s.decode('ascii')
        except Exception:
            continue
        res.append((key.decode(), t, size, p, len(val)))
    return res

aex = {}
nmiss = []
for fn in sorted(f for f in os.listdir(CONT) if f.lower().endswith('.aex')):
    recs = pipl(os.path.join(CONT, fn))
    names = [(t, sz, p) for k, t, sz, p, vl in recs if k == 'eman']
    catgs = [t for k, t, sz, p, vl in recs if k == 'gtac']
    if not names:
        nmiss.append(fn)
    aex[fn] = {'names': [[t, sz, p] for t, sz, p in names], 'catgs': catgs}
out.append("=== 效果名（修正后） ===")
out.append(f"文件数 {len(aex)}  仍缺名字 {len(nmiss)} {nmiss[:5]}")
allnames = sorted(set(t for v in aex.values() for t, sz, p in v['names']))
out.append(f"唯一效果名 {len(allnames)}")
out.append("示例: " + ", ".join(allnames[:10]))
json.dump(aex, open(os.path.join(WORK, 'aex_names2.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

# ---------- 2. 预设 <name> 全集 ----------
out.append("\n=== 预设 <name> 全集 ===")
P = Counter()
root = r"C:\ProgramData\BorisFX\Continuum\19\Presets"
cnt = 0
for dp, dns, fns in os.walk(root):
    for fn in fns:
        if not fn.lower().endswith(('.bsp', '.bap')):
            continue
        cnt += 1
        try:
            t = open(os.path.join(dp, fn), 'rb').read().decode('utf-8', 'ignore')
        except Exception:
            continue
        for m in re.finditer(r'<name>(.*?)</name>', t, re.S):
            s = m.group(1).strip()
            if 1 <= len(s) <= 60 and all(32 <= ord(c) < 127 for c in s):
                P[s] += 1
out.append(f"解析预设 {cnt} 个，不同 <name> {len(P)} 个")
bogus = [s for s in P if s in ('?', 'AE', 'Hidden') or len(s) <= 1]
out.append(f"过滤掉的无效项: {bogus}")
Pset = set(s for s in P if s not in bogus)
out.append(f"有效参数名候选 {len(Pset)}")
json.dump(sorted(Pset), open(os.path.join(WORK, 'param_candidates.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

# ---------- 3. 反查 DLL 槽位链 ----------
out.append("\n=== 槽位链 × 参数名候选 命中 ===")
chains = json.load(open(os.path.join(WORK, 'dll_chains.json'), encoding='utf-8'))
hits = {}
for dll, ch in chains.items():
    rows = []
    for off, arr in ch.items():
        inter = [s for s in arr if s in Pset]
        if inter:
            rows.append((int(off), len(arr), len(inter), arr))
    rows.sort(key=lambda r: -r[2])
    total = sum(r[2] for r in rows)
    out.append(f"\n{dll}: 命中链 {len(rows)}，命中串 {total}")
    for off, n, k, arr in rows[:4]:
        out.append(f"   链@{off} 长{n} 命中{k}  前12: {arr[:12]}")
    hits[dll] = rows
json.dump({d: [[o, n, k, a] for o, n, k, a in r] for d, r in hits.items()},
          open(os.path.join(WORK, 'chain_hits.json'), 'w', encoding='utf-8'),
          ensure_ascii=False)

open(os.path.join(WORK, 'parse_report.txt'), 'w', encoding='utf-8').write("\n".join(out))

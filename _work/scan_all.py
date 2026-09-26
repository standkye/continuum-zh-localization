# -*- coding: utf-8 -*-
"""扫描 Continuum：.aex 效果名（PiPL）+ 引擎 DLL 参数名（8 字节对齐槽位链）"""
import os, re, json, struct

CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"
LIB = r"C:\Program Files\BorisFX\ContinuumAE\19\lib"
WORK = r"D:\Programming project\插件汉化\_work"
os.makedirs(WORK, exist_ok=True)

report = []

# ---------- A. .aex 效果名 ----------
def pipl_records(path):
    with open(path, 'rb') as f:
        d = f.read()
    out = []
    for m in re.finditer(rb'MIB8', d):
        p = m.start()
        key = d[p + 4:p + 8]
        if key not in (b'eman', b'gtac', b'eNAM'):
            continue
        try:
            size = struct.unpack_from('<I', d, p + 12)[0]
        except Exception:
            continue
        if size == 0 or size > 512:
            continue
        val = d[p + 16:p + 16 + size]
        if len(val) < 2:
            continue
        L = val[0]
        if L == 0 or L > len(val) - 1:
            continue
        text = val[1:1 + L]
        try:
            s = text.decode('ascii')
        except Exception:
            continue
        if not all(32 <= ord(c) < 127 for c in s):
            continue
        out.append((key.decode('ascii'), s, size, p))
    return out

aex = {}
files = sorted(f for f in os.listdir(CONT) if f.lower().endswith('.aex'))
report.append("=== A. .aex 效果名 ===")
report.append("文件数: %d" % len(files))
nname = ncatg = 0
bad = []
for f in files:
    recs = pipl_records(os.path.join(CONT, f))
    names = [s for k, s, sz, p in recs if k == 'eman']
    catgs = [s for k, s, sz, p in recs if k == 'gtac']
    if not names:
        bad.append(f)
    aex[f] = {'names': names, 'catgs': catgs,
              'sizes': [sz for k, s, sz, p in recs if k == 'eman'],
              'offs': [p for k, s, sz, p in recs if k == 'eman']}
    nname += len(names)
    ncatg += len(catgs)
report.append("eman(效果名) 记录数: %d" % nname)
report.append("gtac(分类名) 记录数: %d" % ncatg)
report.append("没读到名字的文件: %d %s" % (len(bad), bad[:5]))
from collections import Counter
report.append("eman size 分布: %s" % sorted(Counter(
    sz for v in aex.values() for sz in v['sizes']).items()))
allnames = sorted(set(s for v in aex.values() for s in v['names']))
report.append("唯一效果名: %d" % len(allnames))
report.append("示例: %s" % allnames[:8])
json.dump(aex, open(os.path.join(WORK, 'aex_names.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

# ---------- B. DLL 参数名：8 字节对齐槽位链 ----------
def slot_chains(data, min_chain=4, maxlen=48):
    n = len(data)
    printable = re.compile(rb'^[A-Za-z][A-Za-z0-9 _\-+./()%&:,\'#]*$')
    ok = bytearray(n)          # 该偏移是否是一个合法槽位起点
    slot_of = {}
    i = 0
    while i + 8 <= n:
        j = data.find(b'\x00', i, i + 64)
        if j < 0:
            i += 8
            continue
        L = j - i
        s = data[i:j]
        if 2 <= L <= maxlen and printable.match(s):
            need = max(8, ((L + 1 + 7) // 8) * 8)
            if i + need <= n and all(b == 0 for b in data[i + L:i + need]):
                ok[i] = 1
                slot_of[i] = need
                i += need
                continue
        i += 8
    # 串成链
    chains = []
    keys = sorted(slot_of)
    used = set()
    for k in keys:
        if k in used:
            continue
        chain = []
        cur = k
        while cur in slot_of and cur not in used:
            used.add(cur)
            j = data.find(b'\x00', cur, cur + 64)
            chain.append(data[cur:j].decode('ascii'))
            cur += slot_of[cur]
        if len(chain) >= min_chain:
            chains.append((k, chain))
    return chains

dlls = ['Continuum_AE_Float.dll', 'Continuum_AE_8Bit.dll', 'Continuum_AE_16Bit.dll',
        'Continuum_Common_AE.dll', 'Continuum_3DObjects_AE.dll']
dlls += ['BCCPlus.dll']
report.append("\n=== B. DLL 参数名槽位链 ===")
labels = {}
for n in dlls:
    p = os.path.join(LIB, n)
    if not os.path.exists(p):
        p = os.path.join(CONT, n)
    if not os.path.exists(p):
        report.append(f"{n}: 不存在")
        continue
    with open(p, 'rb') as f:
        d = f.read()
    ch = slot_chains(d)
    tot = sum(len(c[1]) for c in ch)
    big = sorted(ch, key=lambda x: -len(x[1]))[:3]
    report.append(f"{n:28s} 链数={len(ch):5d} 串数={tot:6d} "
                  f"最长链={[len(b[1]) for b in big]}")
    labels[n] = {str(off): c for off, c in ch}
json.dump(labels, open(os.path.join(WORK, 'dll_chains.json'), 'w', encoding='utf-8'),
          ensure_ascii=False)

# ---------- C. 找预设文件（用于校验哪些是真参数名） ----------
report.append("\n=== C. 预设/元数据文件 ===")
roots = [r"C:\Program Files\BorisFX\ContinuumAE\19",
         r"C:\ProgramData\BorisFX",
         os.path.join(os.path.expanduser('~'), 'Documents'),
         r"C:\Users\Public\Documents"]
exts = ('.bsp', '.bap', '.ffx', '.xml')
found = {}
for r in roots:
    if not os.path.isdir(r):
        continue
    for dp, dns, fns in os.walk(r):
        if dp.count(os.sep) - r.count(os.sep) > 4:
            dns[:] = []
        for fn in fns:
            if fn.lower().endswith(exts):
                found.setdefault(fn.lower().split('.')[-1], []).append(os.path.join(dp, fn))
for k, v in found.items():
    report.append(f"  .{k}: {len(v)} 个，例: {v[0] if v else ''}")

open(os.path.join(WORK, 'scan_report.txt'), 'w', encoding='utf-8').write("\n".join(report))
print("done")

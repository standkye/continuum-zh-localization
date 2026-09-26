# -*- coding: utf-8 -*-
import os, re, json, struct
from collections import Counter

CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"
LIB = r"C:\Program Files\BorisFX\ContinuumAE\19\lib"
WORK = r"D:\Programming project\插件汉化\_work"
PL = os.path.join(LIB, 'Resources', 'PLists')
out = []

# 1. PLists 目录
out.append("=== PLists 目录 ===")
if os.path.isdir(PL):
    for f in sorted(os.listdir(PL)):
        p = os.path.join(PL, f)
        out.append(f"  {f}  {os.path.getsize(p)/1024:.0f} KB" if os.path.isfile(p) else f"  [D] {f}")
else:
    out.append("  不存在")

# 2. BCC_Menus.xml 结构
f = os.path.join(PL, 'BCC_Menus.xml')
if os.path.exists(f):
    d = open(f, 'rb').read()
    enc = 'utf-8'
    try:
        t = d.decode('utf-8')
    except Exception:
        t = d.decode('latin1'); enc = 'latin1'
    out.append(f"\n=== BCC_Menus.xml ({enc}, {len(t)} 字符) 前 1500 字符 ===")
    out.append(t[:1500])

# 3. 预设里的 <name>
out.append("\n=== 预设 <name> 提取 ===")
names = Counter()
dirs = Counter()
files_seen = 0
root = r"C:\ProgramData\BorisFX\Continuum\19\Presets"
if os.path.isdir(root):
    for dp, dns, fns in os.walk(root):
        for fn in fns:
            if not fn.lower().endswith(('.bsp', '.bap')):
                continue
            files_seen += 1
            dirs[os.path.basename(dp)] += 1
            if files_seen > 400:
                continue
            try:
                t = open(os.path.join(dp, fn), 'rb').read().decode('utf-8', 'ignore')
            except Exception:
                continue
            for m in re.finditer(r'<name>(.*?)</name>', t, re.S):
                s = m.group(1).strip()
                if 1 <= len(s) <= 60 and all(32 <= ord(c) < 127 for c in s):
                    names[s] += 1
out.append(f"扫了 {files_seen} 个预设（实际解析 400 个）")
out.append(f"不同 <name> 值: {len(names)}")
out.append("出现次数最多的 30 个:")
for s, c in names.most_common(30):
    out.append(f"  {c:5d}  {s}")
json.dump({k: v for k, v in names.items()}, open(os.path.join(WORK, 'preset_names.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# 4. 36 个没读到名字的 .aex 排查
out.append("\n=== 没读到名字的 .aex 排查 ===")
aex = json.load(open(os.path.join(WORK, 'aex_names.json'), encoding='utf-8'))
bad = [k for k, v in aex.items() if not v['names']]
out.append(f"共 {len(bad)} 个")
for b in bad[:3]:
    p = os.path.join(CONT, b)
    d = open(p, 'rb').read()
    out.append(f"\n--- {b} ({len(d)} B) ---")
    keys = Counter()
    for m in re.finditer(rb'MIB8', d):
        keys[d[m.start()+4:m.start()+8]] += 1
    out.append("  MIB8 各 key: " + ", ".join(
        f"{k.decode('latin1')}={v}" for k, v in keys.most_common(20)))
    i = d.find(b'eman')
    if i >= 0:
        out.append("  eman 附近: " + repr(d[i-8:i+40]))

open(os.path.join(WORK, 'dig_report.txt'), 'w', encoding='utf-8').write("\n".join(out))

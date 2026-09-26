# -*- coding: utf-8 -*-
"""交付前最终体检：一次性确认交付目录里每个文件都是对的。"""
import os, struct, sys, hashlib, json

W = r"D:\Programming project\插件汉化"
SRC = os.path.join(W, "Continuum 汉化组件 v19.0.0")
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
BK_AEX = os.path.join(BK, "aex")

o = []

def _rec(path, key):
    """MIB8 的 base = j-4（key 前还有 'MIB8' 4 字节），
       value 从 base+16 开始，size 在 base+12。"""
    d = open(path, 'rb').read()
    k = key.encode()
    j = d.find(k)
    while j >= 0:
        if d[j - 4:j] == b'MIB8':
            base = j - 4
            size = struct.unpack('<I', d[base + 12:base + 16])[0]
            if 0 < size < 4096:
                val = base + 16
                return d[val + 1:val + size].split(b'\x00')[0]
        j = d.find(k, j + 4)
    return None

def eman(path):
    return _rec(path, 'eman')

def gtac(path):
    return _rec(path, 'gtac')

names = sorted(f for f in os.listdir(SRC) if f.lower().endswith('.aex'))
o.append(f"交付 .aex 数量: {len(names)}")

# 1) 长度与英文源一致
bad = [f for f in names
       if os.path.getsize(os.path.join(SRC, f)) != os.path.getsize(os.path.join(BK_AEX, f))]
o.append(f"1) 长度与英文源不一致: {len(bad)}  {bad[:5]}")

# 2) 全部 nam 是合法 UTF-8 且含中文
nonutf8 = []
ascii_only = []
for f in names:
    e = eman(os.path.join(SRC, f))
    if e is None:
        nonutf8.append((f, '无 eman'))
        continue
    try:
        t = e.decode('utf-8')
    except UnicodeDecodeError:
        nonutf8.append((f, e[:30]))
        continue
    if not any(ord(c) > 127 for c in t):
        ascii_only.append((f, t))
o.append(f"2) eman 非法 UTF-8: {len(nonutf8)}  {nonutf8[:5]}")
o.append(f"   eman 仍为纯 ASCII: {len(ascii_only)}  {ascii_only[:5]}")

# 3) gtac 合法 UTF-8（源已是中文，能解出来就行）
gbad = 0
gcn = 0
for f in names:
    g = gtac(os.path.join(SRC, f))
    if g is None:
        continue
    try:
        t = g.decode('utf-8')
    except UnicodeDecodeError:
        gbad += 1
        continue
    if any(ord(c) > 127 for c in t):
        gcn += 1
o.append(f"3) gtac 非法 UTF-8: {gbad}   含中文的 gtac: {gcn}/{len(names)}")

# 4) DLL 长度一致 + 中文可读
for d in ['Continuum_AE_Float.dll', 'Continuum_AE_8Bit.dll', 'Continuum_AE_16Bit.dll',
          'Continuum_Common_AE.dll', 'Continuum_3DObjects_AE.dll', 'BCCPlus.dll']:
    a = os.path.getsize(os.path.join(BK, d))
    b = os.path.getsize(os.path.join(SRC, d))
    o.append(f"4) {d:30s} 英文={a:>12,}  交付={b:>12,}  相等={a==b}")

# 5) 抽样目检
o.append("\n5) 抽样目检（eman / gtac）")
for f in ['BCC3WayColorGrade.aex', 'BCCLevels.aex', 'BCCWarping.aex', 'BCCBlur.aex',
          'BCCColorMatch.aex', 'BCCCube.aex', 'Sepia.aex', 'BCCAlphaProcess.aex',
          'BCCTrails.aex', 'BCCWitnessProtection.aex']:
    p = os.path.join(SRC, f)
    if not os.path.exists(p):
        continue
    e = eman(p).decode('utf-8', 'replace')
    g = gtac(p).decode('utf-8', 'replace')
    o.append(f"   {f[:32]:34s} {e!r:26s}  [{g}]")

# 6) exe sha256
exe = os.path.join(SRC, 'Continuum汉化安装器.exe')
o.append(f"\n6) 安装器 exe: {os.path.getsize(exe):,} bytes")
o.append(f"   sha256 {hashlib.sha256(open(exe,'rb').read()).hexdigest()}")

# 7) 说明.txt BOM
t = os.path.join(SRC, '说明.txt')
raw = open(t, 'rb').read()
o.append(f"\n7) 说明.txt {len(raw)} bytes, UTF-8 BOM = {raw[:3]==b'\xef\xbb\xbf'}")

open(os.path.join(W, "_work", "_final_health.txt"), 'w', encoding='utf-8').write("\n".join(o))
print("done")

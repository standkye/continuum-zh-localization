# -*- coding: utf-8 -*-
"""把最新的 UTF-8 补丁输出刷新到交付目录（就地覆盖，不删除）。"""
import os, shutil, hashlib

W = r"D:\Programming project\插件汉化"
STAGE = os.path.join(W, "Continuum 汉化组件 v19.0.0")
PAEX = os.path.join(W, "_work", "patched_aex")
PDLL = os.path.join(W, "_work", "patched_dll")

BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
LIB = r"C:\Program Files\BorisFX\ContinuumAE\19\lib"
CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"

o = []
n = 0
for f in sorted(os.listdir(PAEX)):
    if f.lower().endswith('.aex'):
        shutil.copy2(os.path.join(PAEX, f), os.path.join(STAGE, f))
        n += 1
o.append(f"aex 覆盖 {n} 个")

n = 0
for f in sorted(os.listdir(PDLL)):
    if f.lower().endswith('.dll'):
        shutil.copy2(os.path.join(PDLL, f), os.path.join(STAGE, f))
        n += 1
o.append(f"dll 覆盖 {n} 个")

# 校验：交付目录里每个文件必须与 patched 输出（或英文源）逐字节一致
bad = []
for f in sorted(os.listdir(PAEX)):
    if not f.lower().endswith('.aex'):
        continue
    a = open(os.path.join(PAEX, f), 'rb').read()
    b = open(os.path.join(STAGE, f), 'rb').read()
    if a != b:
        bad.append(f)
o.append(f"aex 校验不一致: {len(bad)} {bad[:6]}")
bad = []
for f in sorted(os.listdir(PDLL)):
    if not f.lower().endswith('.dll'):
        continue
    a = open(os.path.join(PDLL, f), 'rb').read()
    b = open(os.path.join(STAGE, f), 'rb').read()
    if a != b:
        bad.append(f)
o.append(f"dll 校验不一致: {len(bad)} {bad}")

# 确认 dll 是「在英文源基础上改的」：与英文备份逐字节比对长度
o.append("\n=== 与英文源的长度比对 ===")
for f in sorted(os.listdir(PDLL)):
    s = os.path.join(BK, f)
    if not os.path.exists(s):
        s = os.path.join(CONT, f)
    o.append(f"{f:30s} 英文={os.path.getsize(s):>12,}  汉化={os.path.getsize(os.path.join(PDLL,f)):>12,}  "
             f"相等={os.path.getsize(s)==os.path.getsize(os.path.join(PDLL,f))}")

open(os.path.join(W, "_work", "_stage_refresh.txt"), 'w', encoding='utf-8').write("\n".join(o))
print("done")

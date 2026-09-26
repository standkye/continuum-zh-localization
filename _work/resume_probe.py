# -*- coding: utf-8 -*-
"""续做前的现场勘查：交付物完整性 + 装机状态 + 进程状态"""
import os, sys, hashlib, subprocess, io

OUT = io.StringIO()
def p(*a):
    print(*a)
    print(*a, file=OUT)

BASE = r'D:\Programming project\插件汉化'
DELIV = os.path.join(BASE, 'Continuum 汉化组件 v19.0.0')
EXE = os.path.join(DELIV, 'Continuum汉化安装器.exe')
SRC_AEX = os.path.join(DELIV, 'aex') if os.path.isdir(os.path.join(DELIV, 'aex')) else DELIV
SRC_DLL = os.path.join(DELIV, 'dll') if os.path.isdir(os.path.join(DELIV, 'dll')) else DELIV
MOD = r'C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum'
LIB = r'C:\Program Files\BorisFX\ContinuumAE\19\lib'
BK = r'C:\Program Files\BorisFX\ContinuumAE\19\Backup-English'

def sha(fp):
    h = hashlib.sha256()
    with open(fp, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

p('=' * 70)
p('1) 安装器 exe')
p('=' * 70)
if os.path.exists(EXE):
    h = sha(EXE)
    p('  path   :', EXE)
    p('  size   :', os.path.getsize(EXE))
    p('  sha256 :', h)
    EXP = '72b2bbf1e075919f1be87ef8731751466461adb863149d61a830b7663fc33e65'
    p('  expect :', EXP)
    p('  MATCH  :', 'YES' if h == EXP else 'NO  <-- 不是最新的 UTF-8 打包')
else:
    p('  !! exe 不存在:', EXE)

p()
p('=' * 70)
p('2) 交付目录散装载荷')
p('=' * 70)
aexs = [f for f in os.listdir(DELIV) if f.lower().endswith('.aex')]
dlls = [f for f in os.listdir(DELIV) if f.lower().endswith('.dll')]
p('  .aex 数量:', len(aexs))
p('  .dll 数量:', len(dlls))
tgt = os.path.join(DELIV, 'BCCBlur.aex')
if os.path.exists(tgt):
    d = open(tgt, 'rb').read()
    j = d.find(b'MIB8eman')
    p('  交付 BCCBlur eman:', d[j+16:j+30])
    p('    期望 UTF-8 = b\'\\x0aBCC \\xe6\\xa8\\xa1\\xe7\\xb3\\x8a\' (BCC 模糊)')

p()
p('=' * 70)
p('3) 装机状态（当前）')
p('=' * 70)
cur = os.path.join(MOD, 'BCCBlur.aex')
if os.path.exists(cur):
    d = open(cur, 'rb').read()
    j = d.find(b'MIB8eman')
    seg = d[j+16:j+30]
    p('  已装 BCCBlur eman:', seg)
    if seg.startswith(b'\x0aBCC \xe6\xa8\xa1'):
        p('  => UTF-8 新版（已修好）')
    elif seg.startswith(b'\x04\xc4\xa3'):
        p('  => GBK 旧版（坏的，需要重装）')
    else:
        p('  => 英文原版 或 未知')

# 全量 diff 统计
tot = 0; diff = 0
for f in sorted(os.listdir(MOD)):
    if f.lower().endswith('.aex'):
        tot += 1
        a, b = os.path.join(MOD, f), os.path.join(DELIV, f)
        if not os.path.exists(b) or sha(a) != sha(b):
            diff += 1
for f in sorted(os.listdir(LIB)):
    if f.lower().endswith('.dll'):
        tot += 1
        a, b = os.path.join(LIB, f), os.path.join(DELIV, f)
        if not os.path.exists(b) or sha(a) != sha(b):
            diff += 1
p('  TOTAL_DIFF = %d / %d' % (diff, tot))
if diff == 0:
    p('  => 已全部落地（新版已装好）')
else:
    p('  => 未落地，需要安装')

p()
p('=' * 70)
p('4) 备份是否就绪（还原用）')
p('=' * 70)
if os.path.isdir(BK):
    n_aex = len(os.listdir(os.path.join(BK, 'aex'))) if os.path.isdir(os.path.join(BK, 'aex')) else -1
    n_dll = len([f for f in os.listdir(BK) if f.lower().endswith('.dll')])
    p('  Backup-English 存在, aex=%d dll=%d' % (n_aex, n_dll))
else:
    p('  !! Backup-English 不存在')

p()
p('=' * 70)
p('5) 进程状态')
p('=' * 70)
try:
    r = subprocess.run(['tasklist', '/FO', 'CSV', '/NH'], capture_output=True)
    txt = r.stdout.decode('gbk', errors='ignore')
    for key in ('AfterFX.exe', 'Premiere.exe', 'consent.exe'):
        hit = [l for l in txt.splitlines() if key.lower() in l.lower()]
        p('  %-14s : %s' % (key, 'RUNNING (%d)' % len(hit) if hit else 'none'))
except Exception as e:
    p('  tasklist 失败:', e)

with open(os.path.join(BASE, '_work', 'resume_probe_out.txt'), 'w', encoding='utf-8') as f:
    f.write(OUT.getvalue())

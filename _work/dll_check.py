# -*- coding: utf-8 -*-
"""补验：exe 内 6 个引擎 DLL == 交付目录；并修正版 TOTAL_DIFF 统计
   用 venv 解释器运行（需 PyInstaller）
"""
import os, hashlib, io

OUT = io.StringIO()
def p(*a):
    print(*a)
    print(*a, file=OUT)

BASE = r'D:\Programming project\插件汉化'
DELIV = os.path.join(BASE, 'Continuum 汉化组件 v19.0.0')
EXE = os.path.join(DELIV, 'Continuum汉化安装器.exe')
MOD = r'C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum'
LIB = r'C:\Program Files\BorisFX\ContinuumAE\19\lib'

from PyInstaller.archive.readers import CArchiveReader
r = CArchiveReader(EXE)

ENGINES = ['Continuum_AE_Float.dll', 'Continuum_AE_8Bit.dll', 'Continuum_AE_16Bit.dll',
           'Continuum_Common_AE.dll', 'Continuum_3DObjects_AE.dll', 'BCCPlus.dll']

p('=' * 70)
p('A) exe 归档内 6 个引擎 DLL vs 交付目录')
p('=' * 70)
allok = True
for n in ENGINES:
    if n not in r.toc:
        p('  %-30s 归档内缺失 ❌' % n); allok = False; continue
    a = r.extract(n)
    b_path = os.path.join(DELIV, n)
    b = open(b_path, 'rb').read() if os.path.exists(b_path) else None
    if b is None:
        p('  %-30s 交付目录缺失' % n); allok = False
    elif a == b:
        p('  %-30s 一致 ✅  (%d bytes)' % (n, len(a)))
    else:
        p('  %-30s 不一致 ❌' % n); allok = False
p('  =>', '全部通过' if allok else '有问题')

p()
p('=' * 70)
p('B) 装机差异（只统计交付目录里有的文件）')
p('=' * 70)
def sha(fp):
    h = hashlib.sha256()
    with open(fp, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()

first_diff = []
tot = 0; diff = 0
for f in sorted(os.listdir(DELIV)):
    if not (f.lower().endswith('.aex') or f.lower().endswith('.dll')):
        continue
    src = os.path.join(DELIV, f)
    dst = os.path.join(MOD, f) if f.lower().endswith('.aex') else os.path.join(LIB, f)
    tot += 1
    if not os.path.exists(dst):
        diff += 1; first_diff.append((f, '目标不存在')); continue
    if sha(src) != sha(dst):
        diff += 1
        if len(first_diff) < 12:
            first_diff.append((f, '不等'))
p('  TOTAL_DIFF = %d / %d' % (diff, tot))
for f, why in first_diff:
    p('    -', f, why)
if diff == 0:
    p('  => ✅ 已全部落地')
else:
    p('  => ❌ 未落地，需要跑安装器')

p()
p('=' * 70)
p('C) 已装 6 DLL vs 英文备份（判断当前是英文版还是 GBK 坏版）')
p('=' * 70)
BK = r'C:\Program Files\BorisFX\ContinuumAE\19\Backup-English'
for n in ENGINES:
    cur = os.path.join(LIB, n) if n != 'BCCPlus.dll' else os.path.join(MOD, n)
    en = os.path.join(BK, n)
    new = os.path.join(DELIV, n)
    s_cur = sha(cur) if os.path.exists(cur) else None
    s_en = sha(en) if os.path.exists(en) else None
    s_new = sha(new) if os.path.exists(new) else None
    tag = []
    if s_cur and s_en and s_cur == s_en: tag.append('==英文原版')
    if s_cur and s_new and s_cur == s_new: tag.append('==UTF8新版')
    if not tag: tag.append('==其它(可能是GBK旧补丁)')
    p('  %-30s %s' % (n, ' '.join(tag)))

with open(os.path.join(BASE, '_work', 'dll_check_out.txt'), 'w', encoding='utf-8') as f:
    f.write(OUT.getvalue())

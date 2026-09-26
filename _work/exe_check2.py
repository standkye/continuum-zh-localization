# -*- coding: utf-8 -*-
"""校验安装器 exe 内嵌载荷 == 交付目录（含 6 个引擎 DLL 逐字节比对）
   必须用装了 PyInstaller 的 venv 解释器运行
"""
import os, hashlib, io, sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

OUT = io.StringIO()
def p(*a):
    print(*a)
    print(*a, file=OUT)

BASE = r'D:\Programming project\插件汉化'
DELIV = os.path.join(BASE, 'Continuum 汉化组件 v19.0.0')
EXE = os.path.join(DELIV, 'Continuum汉化安装器.exe')

ENGINE_DLLS = [
    "Continuum_AE_Float.dll",
    "Continuum_AE_8Bit.dll",
    "Continuum_AE_16Bit.dll",
    "Continuum_Common_AE.dll",
    "Continuum_3DObjects_AE.dll",
    "BCCPlus.dll",
]

def sha_b(b):
    return hashlib.sha256(b).hexdigest()

try:
    from PyInstaller.archive.readers import CArchiveReader
except Exception as e:
    p('!! 无法导入 CArchiveReader:', e)
    p('   请用 venv 解释器:', r'C:\Users\Jinna\.workbuddy\binaries\python\envs\default\Scripts\python.exe')
    open(os.path.join(BASE, '_work', 'exe_check2_out.txt'), 'w', encoding='utf-8').write(OUT.getvalue())
    sys.exit(1)

p('=' * 74)
p('安装器 exe 载荷校验 (v2 · 含引擎 DLL)')
p('=' * 74)
p('exe:', EXE)
p('     %d bytes   sha256 %s' % (os.path.getsize(EXE), sha_b(open(EXE, 'rb').read())))
p()

r = CArchiveReader(EXE)
toc = list(r.toc)
p('归档条目总数:', len(toc))

name_of = {}
for n in toc:
    name_of[os.path.basename(n)] = n

# ---------- [1] .aex 逐字节 ----------
aex_names = [n for n in toc if n.lower().endswith('.aex')]
bad = []
for n in aex_names:
    base = os.path.basename(n)
    src = os.path.join(DELIV, base)
    if not os.path.exists(src):
        bad.append((base, '交付目录无此文件'))
        continue
    if r.extract(n) != open(src, 'rb').read():
        bad.append((base, '与交付目录不一致'))
missing = [f for f in os.listdir(DELIV) if f.lower().endswith('.aex') and f not in name_of]
p('[1] .aex 逐字节比对 vs 交付目录 —— 归档 %d / 交付 %d'
  % (len(aex_names), len([f for f in os.listdir(DELIV) if f.lower().endswith('.aex')])))
p('    不一致: %d    交付有归档缺: %d' % (len(bad), len(missing)))
for n, why in bad[:10]:
    p('      -', n, why)
for f in missing[:10]:
    p('      - missing', f)
p()

# ---------- [2] 6 个引擎 DLL 逐字节 ----------
p('[2] 6 个引擎 DLL 逐字节比对')
allok = True
for d in ENGINE_DLLS:
    arc = name_of.get(d)
    src = os.path.join(DELIV, d)
    if arc is None:
        p('   %-32s 归档缺失' % d); allok = False; continue
    if not os.path.exists(src):
        p('   %-32s 交付缺失' % d); allok = False; continue
    eb = r.extract(arc)
    sb = open(src, 'rb').read()
    ok = (eb == sb)
    allok &= ok
    p('   %-32s %s  n=%d  sha=%s' % (d, 'OK ' if ok else 'BAD',
                                     len(eb), sha_b(sb)[:32]))
p('    => 引擎 DLL 全部一致:', allok)
p()

# ---------- [3] 与源 patched_dll_d 比对 ----------
pd = os.path.join(BASE, '_work', 'patched_dll_d')
p('[3] 交付 DLL == patched_dll_d ?')
for d in ENGINE_DLLS:
    a = os.path.join(DELIV, d); b = os.path.join(pd, d)
    if os.path.exists(a) and os.path.exists(b):
        p('   %-32s %s' % (d, '一致' if open(a, 'rb').read() == open(b, 'rb').read() else '不一致'))
p()

# ---------- [4] 抽样校验 .aex 内嵌效果名的中文编码 ----------
# 约定：.aex 内嵌效果名用 GBK（zh-CN 宿主 ANSI 代码页），与已装文件一致。
# 旧脚本按 UTF-8 判断是错的，见 _work/_aex_enc.txt。
probe = 'BCCBlur.aex'
if probe in name_of:
    dd = r.extract(name_of[probe])
    j = dd.find(b'MIB8eman')
    k = j + 16
    n = dd[k]
    seg = dd[k+1:k+1+n]
    p('[4] 归档内 %s eman: %r' % (probe, seg))
    try:
        zh = seg.decode('gbk')
    except Exception as e:
        zh = None
        p('    => GBK 解码失败: %s' % e)
    if zh is not None:
        okc = all((ord(c) < 0x80) or ('\u4e00' <= c <= '\u9fff') for c in zh)
        p('    => GBK 解码 = %r   中文/ASCII = %s' % (zh, 'OK' if okc else '含异常字符'))
    # 与已装文件对比
    inst = r'C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum\BCCBlur.aex'
    if os.path.exists(inst):
        p('    => 与已装文件逐字节相同: %s' % (r.extract(name_of[probe]) == open(inst, 'rb').read()))
p()

# ---------- [5] 全量 .aex 中文编码健康度 ----------
p('[5] 交付目录 488 个 .aex 内嵌效果名 GBK 可解码性')
bad5 = 0
for f in sorted(os.listdir(DELIV)):
    if not f.lower().endswith('.aex'):
        continue
    dd = open(os.path.join(DELIV, f), 'rb').read()
    j = dd.find(b'MIB8eman')
    if j < 0:
        bad5 += 1; p('      - 无 eman 段: ' + f); continue
    k = j + 16
    if k >= len(dd):
        bad5 += 1; p('      - eman 截断: ' + f); continue
    n = dd[k]
    body = dd[k+1:k+1+n]
    try:
        body.decode('gbk')
    except Exception as e:
        bad5 += 1
        p('      - GBK 解码失败: %s  %r  (%s)' % (f, body, e))
p('    异常: %d / 488' % bad5)

open(os.path.join(BASE, '_work', 'exe_check2_out.txt'), 'w', encoding='utf-8').write(OUT.getvalue())

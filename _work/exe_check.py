# -*- coding: utf-8 -*-
"""校验安装器 exe 内嵌载荷 == 交付目录（UTF-8 新版）
   必须用装了 PyInstaller 的 venv 解释器运行
"""
import os, hashlib, io, sys

OUT = io.StringIO()
def p(*a):
    print(*a)
    print(*a, file=OUT)

BASE = r'D:\Programming project\插件汉化'
DELIV = os.path.join(BASE, 'Continuum 汉化组件 v19.0.0')
EXE = os.path.join(DELIV, 'Continuum汉化安装器.exe')

try:
    from PyInstaller.archive.readers import CArchiveReader
except Exception as e:
    p('!! 无法导入 CArchiveReader:', e)
    p('   请用 venv 解释器:', r'C:\Users\Jinna\.workbuddy\binaries\python\envs\default\Scripts\python.exe')
    with open(os.path.join(BASE, '_work', 'exe_check_out.txt'), 'w', encoding='utf-8') as f:
        f.write(OUT.getvalue())
    sys.exit(1)

p('=' * 70)
p('安装器 exe 载荷校验')
p('=' * 70)
p('exe:', EXE, os.path.getsize(EXE), 'bytes')
p()

r = CArchiveReader(EXE)
toc = list(r.toc)
p('归档条目总数:', len(toc))

aex_names = [n for n in toc if n.lower().endswith('.aex')]
dll_names = [n for n in toc if n.lower().endswith('.dll') and 'python' not in n.lower()
             and 'vcruntime' not in n.lower() and 'api-ms' not in n.lower()]
p('归档内 .aex:', len(aex_names))
p('归档内 引擎 .dll:', len(dll_names), sorted(dll_names))
p()

def sha_b(b):
    return hashlib.sha256(b).hexdigest()

# 1) 全部 aex 逐字节比对
bad = []
for n in aex_names:
    src = os.path.join(DELIV, n)
    if not os.path.exists(src):
        bad.append((n, '交付目录无此文件'))
        continue
    if r.extract(n) != open(src, 'rb').read():
        bad.append((n, '与交付目录不一致'))
p('[1] 全部 %d 个 .aex 逐字节比对 vs 交付目录' % len(aex_names))
p('    不一致:', len(bad))
for n, why in bad[:10]:
    p('      -', n, why)
p()

# 2) 交付目录有但归档没有的
missing = [f for f in os.listdir(DELIV) if f.lower().endswith('.aex') and f not in set(aex_names)]
p('[2] 交付目录有但归档缺失的 .aex:', len(missing))
for f in missing[:10]:
    p('      -', f)
p()

# 3) 抽样看 BCCBlur 的 eman 段
probe = 'BCCBlur.aex'
if probe in toc:
    d = r.extract(probe)
    j = d.find(b'MIB8eman')
    p('[3] 归档内 %s 的 eman 段:' % probe, d[j+16:j+40])
    seg = d[j+16:j+30]
    if seg.startswith(b'\x0aBCC \xe6\xa8\xa1'):
        p('    => UTF-8 中文「BCC 模糊」  ✅ 是修好的新版')
    elif seg.startswith(b'\x04\xc4\xa3'):
        p('    => GBK「模糊」  ❌ 还是坏的那版')
    else:
        p('    => 无法判定')

# 4) 与已装的 GBK 坏版对比
cur = r'C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum\BCCBlur.aex'
if os.path.exists(cur):
    cd = open(cur, 'rb').read()
    same = (cd == r.extract(probe)) if probe in toc else None
    p('[4] 归档内 BCCBlur 与【已装】文件相同?', same, '（True 表示装上去还是坏版）')

with open(os.path.join(BASE, '_work', 'exe_check_out.txt'), 'w', encoding='utf-8') as f:
    f.write(OUT.getvalue())

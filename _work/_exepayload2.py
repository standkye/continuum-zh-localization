# -*- coding: utf-8 -*-
"""全量（不抽样）校验重建后的 EXE 内嵌载荷 == 交付目录里的 UTF-8 文件。"""
import os, sys, hashlib

EXE = r"D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0\Continuum汉化安装器.exe"
SRC = r"D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0"

o = []
try:
    from PyInstaller.archive.readers import CArchiveReader
except Exception as e:
    o.append("CArchiveReader 不可用: %s" % e)
    open(r"D:\Programming project\插件汉化\_work\_exepayload2.txt", 'w',
         encoding='utf-8').write("\n".join(o))
    sys.exit(1)

o.append("exe 大小: %d" % os.path.getsize(EXE))
o.append("exe sha256: %s" % hashlib.sha256(open(EXE, 'rb').read()).hexdigest())

r = CArchiveReader(EXE)
names = sorted(r.toc.keys())
o.append("归档条目数: %d" % len(names))

aex = [n for n in names if n.lower().endswith('.aex')]
dll = [n for n in names if n.lower().endswith('.dll') and not n.lower().startswith(('api-', 'python', 'vcruntime', 'ucrt', 'msvcp', 'libcrypto', 'libssl', 'qt5', 'zlib'))]
o.append("归档内 .aex %d 个 / .dll %d 个" % (len(aex), len(dll)))

WANT = ["Continuum_AE_Float.dll", "Continuum_AE_8Bit.dll", "Continuum_AE_16Bit.dll",
        "Continuum_Common_AE.dll", "Continuum_3DObjects_AE.dll", "BCCPlus.dll"]

bad = []
checked = 0
for n in aex:
    base = os.path.basename(n)
    p = os.path.join(SRC, base)
    if not os.path.exists(p):
        bad.append((n, '交付目录缺失')); continue
    try:
        data = r.extract(n)
    except Exception as e:
        bad.append((n, '解出失败 %s' % e)); continue
    if data != open(p, 'rb').read():
        bad.append((n, '内容不一致'))
    checked += 1
o.append("== .aex 全量比对 %d 个，不一致 %d ==" % (checked, len(bad)))
for m in bad[:10]:
    o.append("   %s" % (m,))

bad2 = []
ok2 = []
for w in WANT:
    hit = [n for n in names if os.path.basename(n) == w]
    if not hit:
        bad2.append((w, '归档内没有')); continue
    n = hit[0]
    p = os.path.join(SRC, w)
    try:
        data = r.extract(n)
    except Exception as e:
        bad2.append((w, '解出失败 %s' % e)); continue
    if data == open(p, 'rb').read():
        ok2.append(w)
    else:
        bad2.append((w, '内容不一致'))
o.append("== 引擎 DLL 比对: OK %d / BAD %d ==" % (len(ok2), len(bad2)))
for w in ok2:
    o.append("   OK  " + w)
for m in bad2:
    o.append("   BAD %s" % (m,))

o.append("")
o.append("结论: %s" % ("PAYLOAD OK" if not bad and not bad2 else "PAYLOAD 有问题"))

open(r"D:\Programming project\插件汉化\_work\_exepayload2.txt", 'w',
     encoding='utf-8').write("\n".join(o))
print("done")

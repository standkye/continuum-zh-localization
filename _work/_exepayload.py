# -*- coding: utf-8 -*-
"""校验打进 EXE 里的 488 个 .aex + 6 个 dll 就是最新的 UTF-8 版，
   而不是上一版 GBK 的残留。做法：在 EXE 字节流里搜关键标记串。

PyInstaller 是把 --add-data 的目录原样压进归档，所以每个文件的字节
会（压缩后）出现在 exe 里。压缩后无法直接逐字节比对，但可以验证：
  1) 新版本才有的 UTF-8 中文串（如 三路调色 / 色阶伽马 / 立方）
     的**任何**压缩形态都无从搜起 → 换个思路：
  2) 直接在 EXE 里数 "MIB8" 出现次数（未压缩的 PiPL 头可能被拆散）。
更可靠：用 PyInstaller 自带的归档读取器把 payload 解出来比对 sha256。
"""
import os, sys, hashlib

EXE = r"D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0\Continuum汉化安装器.exe"
SRC = r"D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0"

o = []

# PyInstaller onefile 归档可从 exe 尾部读取。用 PyInstaller 自己的 API。
try:
    from PyInstaller.archive.readers import CArchiveReader
    o.append("使用 CArchiveReader")
except Exception as e:
    o.append(f"CArchiveReader 不可用: {e}")
    CArchiveReader = None

if CArchiveReader:
    r = CArchiveReader(EXE)
    names = sorted(r.toc.keys())
    o.append(f"归档条目数: {len(names)}")

    def extract(name):
        # CArchiveReader.extract 返回 bytes
        return r.extract(name)

    # 找出 .aex / .dll 条目名（PyInstaller 会加前缀，如 "Ambient Light.aex"）
    aex = [n for n in names if n.lower().endswith('.aex')]
    dll = [n for n in names if n.lower().endswith('.dll')]
    o.append(f"归档内 .aex {len(aex)} 个， .dll {len(dll)} 个")
    o.append(f"样例条目名: {aex[:3]} {dll[:3]}")

    mismatch = []
    checked = 0
    for n in aex[:40] + aex[-20:]:
        base = os.path.basename(n)
        p = os.path.join(SRC, base)
        if not os.path.exists(p):
            mismatch.append((n, '源缺失'))
            continue
        try:
            data = extract(n)
        except Exception as e:
            mismatch.append((n, f'解出失败 {e}'))
            continue
        on_disk = open(p, 'rb').read()
        if data != on_disk:
            mismatch.append((n, '内容不一致'))
        checked += 1
    o.append(f".aex 抽样比对 {checked} 个，不一致 {len(mismatch)}")
    for m in mismatch[:10]:
        o.append(f"    {m}")

    mismatch = []
    checked = 0
    for n in dll:
        base = os.path.basename(n)
        p = os.path.join(SRC, base)
        if not os.path.exists(p):
            mismatch.append((n, '源缺失'))
            continue
        try:
            data = extract(n)
        except Exception as e:
            mismatch.append((n, f'解出失败 {e}'))
            continue
        if data != open(p, 'rb').read():
            mismatch.append((n, '内容不一致'))
        checked += 1
    o.append(f".dll 抽样比对 {checked} 个，不一致 {len(mismatch)}")
    for m in mismatch[:10]:
        o.append(f"    {m}")

open(r"D:\Programming project\插件汉化\_work\_exepayload.txt", 'w', encoding='utf-8').write("\n".join(o))
print("done")

# -*- coding: utf-8 -*-
"""从「原始英文备份」重建干净的 UTF-8 补丁基线。
   .aex -> Backup-English\aex\*.aex
   .dll -> Backup-English\*.dll
所有取值（off / size / cap / 槽位链）必须重新从英文源重新计算，
绝不能沿用之前基于「已被 GBK 污染的文件」测出来的坐标。
"""
import os, struct, json, shutil, sys, re

sys.path.insert(0, r"D:\Programming project\插件汉化\_work")
from names_manual import CATS as _CATS

BK_DIR = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
BK_AEX = os.path.join(BK_DIR, 'aex')
WORK = r"D:\Programming project\插件汉化\_work"
OUT_AEX = os.path.join(WORK, 'patched_aex')
OUT_DLL = os.path.join(WORK, 'patched_dll')

for p in (OUT_AEX, OUT_DLL):
    os.makedirs(p, exist_ok=True)

out = []

# ------------------------------------------------- 词典
param_zh = json.load(open(os.path.join(WORK, 'param_zh.json'), encoding='utf-8'))
for extra in ('hand_all.json', 'hand_other.json', 'hand_other2.json'):
    p = os.path.join(WORK, extra)
    if os.path.exists(p):
        param_zh.update(json.load(open(p, encoding='utf-8')))
out.append(f"param_zh entries: {len(param_zh)}")

names_py = {}
import names_manual
for k, v in names_manual.NAMES.items():
    names_py[k] = v
shorts = dict(getattr(names_manual, 'SHORT', {}))
out.append(f"names_manual.NAMES: {len(names_py)}  SHORT: {len(shorts)}  CATS: {len(_CATS)}")

# ------------------------------------------------- .aex
def find_records(d, key):
    k = key.encode()
    res = []
    i = 0
    while True:
        j = d.find(k, i)
        if j < 0:
            break
        if d[j - 4:j] == b'MIB8':
            base = j - 4
            size = struct.unpack('<I', d[base + 12:base + 16])[0]
            if 0 < size < 4096:
                res.append((base, size, base + 16))
        i = j + 4
    return res


def enc_fit(text, cap):
    """UTF-8 编码并在 cap 内按字符边界收尾；返回 b'' 表示放不下。"""
    b = text.encode('utf-8')
    if len(b) > cap:
        return b''          # 放不下就保留英文，不做截断（截断会出半个字）
    if len(b) > 255:
        return b''
    return b


out.append("\n=== .aex（源：Backup-English）===")
nname = ncat = 0
unmatched_names = []
unmatched_cats = []
overflow_names = []
shortened = []
size_bad = 0
rec_count = 0

for fn in sorted(os.listdir(BK_AEX)):
    if not fn.lower().endswith('.aex'):
        continue
    src = os.path.join(BK_AEX, fn)
    dst = os.path.join(OUT_AEX, fn)
    shutil.copy2(src, dst)
    d = bytearray(open(dst, 'rb').read())
    orig_len = len(d)
    changed = False

    recs = find_records(bytes(d), 'eman')
    rec_count += len(recs)
    for (base, size, val) in recs:
        # 长度字节 n 有两种写法：多数记录 n = 文本字节数，但有一批（BCC Warp /
        # BCC Trails / BCC Bulge …）把 n 写成了**整个 value 长度**，于是
        # n >= size。所以绝不能拿 n 当上界去 continue —— 那样会漏掉 29 个效果名。
        # 唯一可靠的文本边界是那个 NUL 终止符。
        n = d[val]
        payload = d[val + 1:val + size].split(b'\x00')[0]
        if not payload:
            continue
        try:
            en = payload.decode('utf-8')
        except UnicodeDecodeError:
            continue
        # 词典键：源码里 NAMES 的键是英文名；同时试去掉前导空格/尾随空格
        zh = names_py.get(en) or names_py.get(en.strip()) or names_py.get('BCC ' + en)
        if not zh:
            unmatched_names.append((fn, en))
            continue
        # 前缀沿用原文（BCC / BCC+）
        pre = 'BCC+' if en.startswith('BCC+') else ('BCC ' if en.startswith('BCC ') else '')
        cap = size - 2
        # 候选顺序：完整译名 -> 短译名 -> （都放不下就保留英文）
        cands = []
        if pre and not zh.startswith('BCC'):
            cands.append(pre + zh)
        cands.append(zh)
        sh = shorts.get(en) or shorts.get(en.strip())
        if sh:
            if pre and not sh.startswith('BCC'):
                cands.append(pre + sh)
            cands.append(sh)
        b = b''
        used = None
        for cand in cands:
            bb = cand.encode('utf-8')
            if len(bb) <= cap and len(bb) <= 255:
                b = bb
                used = cand
                break
        if not b:
            overflow_names.append((fn, en, zh, len((pre + zh).encode('utf-8')), cap))
            continue
        if used != cands[0]:
            shortened.append((en, cands[0], used))
        d[val:val + size] = b'\x00' * size
        d[val] = len(b)
        d[val + 1:val + 1 + len(b)] = b
        nname += 1
        changed = True

    for (base, size, val) in find_records(bytes(d), 'gtac'):
        # 同 eman：以 NUL 终止符为准，不要相信长度字节。
        payload = d[val + 1:val + size].split(b'\x00')[0]
        if not payload:
            continue
        try:
            cat = payload.decode('utf-8')
        except UnicodeDecodeError:
            continue
        tr = _CATS.get(cat)
        if not tr:
            unmatched_cats.append((fn, cat))
            continue
        b = enc_fit(tr, size - 2)
        if not b:
            continue
        d[val:val + size] = b'\x00' * size
        d[val] = len(b)
        d[val + 1:val + 1 + len(b)] = b
        ncat += 1
        changed = True

    if len(d) != orig_len:
        size_bad += 1
    if changed:
        open(dst, 'wb').write(bytes(d))

out.append(f"扫描到 eman 记录 {rec_count} 条 / 488 文件")
out.append(f"效果名替换 {nname} 处，类型栏替换 {ncat} 处，长度异常 {size_bad}")
out.append(f"未匹配效果名 {len(unmatched_names)} 条：")
for fn, en in unmatched_names[:40]:
    out.append(f"    {fn[:32]:34s} {en!r}")
out.append(f"未匹配类型栏 {len(unmatched_cats)} 条：")
for fn, c in unmatched_cats[:20]:
    out.append(f"    {fn[:32]:34s} {c!r}")

out.append(f"\n用短译名替换 {len(shortened)} 条：")
for en, full, use in shortened:
    out.append(f"    {en[:36]:38s} {full}  ->  {use}")

out.append(f"\n连短译名都放不下、保留英文 {len(overflow_names)} 条：")
for fn, en, zh, need, cap in overflow_names:
    out.append(f"    {fn[:32]:34s} {en[:30]:32s} 需{need}字节/可用{cap}")

open(os.path.join(WORK, '_repatch_aex.txt'), 'w', encoding='utf-8').write("\n".join(out))
print("aex done", nname, ncat)

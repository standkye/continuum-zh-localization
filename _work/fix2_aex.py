# -*- coding: utf-8 -*-
"""修复版 .aex 补丁（GBK 编码）

2026-09-25 第二次修复：
  * 编码 UTF-8 -> GBK。证据：装机 UTF-8 版后中文显示为「妯＄硦」类乱码，
    说明宿主按系统 ANSI(GBK) 解释；且 09-24 的 GBK 效果名版曾由用户实测确认显示正常。
  * 排除内部键（Resources / Documentation 等）—— 这些不是显示标签，
    改掉会让插件初始化失败。详见 _work/_bisect_log.txt
"""
import os, struct, json, shutil, sys

sys.path.insert(0, r"D:\Programming project\插件汉化\_work")
import names_manual
from names_manual import CATS as _CATS

BK_DIR = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
BK_AEX = os.path.join(BK_DIR, 'aex')
WORK = r"D:\Programming project\插件汉化\_work"
OUT_AEX = os.path.join(WORK, 'patched_aex_b')
os.makedirs(OUT_AEX, exist_ok=True)

ENC = 'gbk'
names_py = dict(names_manual.NAMES)
shorts = dict(getattr(names_manual, 'SHORT', {}))

out = []
def p(s=''):
    out.append(str(s))
    print(s, flush=True)

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

def try_enc(t):
    try:
        return t.encode(ENC)
    except UnicodeEncodeError:
        return None

def decode_src(payload):
    for e in ('ascii', 'utf-8', 'gbk'):
        try:
            return payload.decode(e)
        except Exception:
            continue
    return None

p('=== .aex 修复版（编码 %s）===' % ENC)
p('NAMES=%d SHORT=%d CATS=%d' % (len(names_py), len(shorts), len(_CATS)))
p()

nname = ncat = 0
unmatched_names, unmatched_cats, overflow, shortened = [], [], [], []
size_bad = 0

for fn in sorted(os.listdir(BK_AEX)):
    if not fn.lower().endswith('.aex'):
        continue
    src = os.path.join(BK_AEX, fn)
    dst = os.path.join(OUT_AEX, fn)
    shutil.copy2(src, dst)
    d = bytearray(open(dst, 'rb').read())
    orig_len = len(d)
    changed = False

    for (base, size, val) in find_records(bytes(d), 'eman'):
        payload = d[val + 1:val + size].split(b'\x00')[0]
        if not payload:
            continue
        en = decode_src(payload)
        if not en:
            continue
        zh = names_py.get(en) or names_py.get(en.strip()) or names_py.get('BCC ' + en)
        if not zh:
            unmatched_names.append((fn, en))
            continue
        pre = 'BCC+' if en.startswith('BCC+') else ('BCC ' if en.startswith('BCC ') else '')
        cap = size - 2
        cands = []
        if pre and not zh.startswith('BCC'):
            cands.append(pre + zh)
        cands.append(zh)
        sh = shorts.get(en) or shorts.get(en.strip())
        if sh:
            if pre and not sh.startswith('BCC'):
                cands.append(pre + sh)
            cands.append(sh)
        b = None
        used = None
        for cand in cands:
            bb = try_enc(cand)
            if bb is not None and len(bb) <= cap and len(bb) <= 255:
                b, used = bb, cand
                break
        if b is None:
            overflow.append((fn, en, zh, len((pre + zh).encode(ENC, 'replace')), cap))
            continue
        if used != cands[0]:
            shortened.append((en, cands[0], used))
        d[val:val + size] = b'\x00' * size
        d[val] = len(b)
        d[val + 1:val + 1 + len(b)] = b
        nname += 1
        changed = True

    for (base, size, val) in find_records(bytes(d), 'gtac'):
        payload = d[val + 1:val + size].split(b'\x00')[0]
        if not payload:
            continue
        cat = decode_src(payload)
        if not cat:
            continue
        tr = _CATS.get(cat)
        if not tr:
            unmatched_cats.append((fn, cat))
            continue
        b = try_enc(tr)
        if b is None or len(b) > size - 2:
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

p('效果名替换 %d 处，类型栏替换 %d 处，长度异常 %d' % (nname, ncat, size_bad))
p('未匹配效果名 %d 条' % len(unmatched_names))
for fn, en in unmatched_names[:30]:
    p('    %-34s %r' % (fn[:32], en))
p('未匹配类型栏 %d 条' % len(unmatched_cats))
for fn, c in unmatched_cats[:20]:
    p('    %-34s %r' % (fn[:32], c))
p('用短译名 %d 条（前 20）' % len(shortened))
for en, full, use in shortened[:20]:
    p('    %-36s %s -> %s' % (en[:36], full, use))
p('连短译名都放不下、保留英文 %d 条（前 20）' % len(overflow))
for fn, en, zh, need, cap in overflow[:20]:
    p('    %-32s %-30s 需%d/可用%d' % (fn[:32], en[:30], need, cap))

open(os.path.join(WORK, '_fix2_aex.txt'), 'w', encoding='utf-8').write('\n'.join(out))

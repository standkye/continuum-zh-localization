# -*- coding: utf-8 -*-
"""从 NO_DICT 桶里筛出「真的 UI 标签」候选，按频次分层输出，供手写翻译。

筛法（沿用前几轮口径）：
  ① 附近 256 字节内已有中文  => 它躺在一张活的参数名表里
  ② 剔内部符号：XML DTD / WinAPI / AE-SDK suite / 3D 对象名 / 格式化串
  ③ 剔二进制碎片：含控制字符、驼峰类名、全大写常量
"""
import os, re, json, collections, io, sys

W = r'D:\Programming project\插件汉化\_work'
PATCH = os.path.join(W, 'patched_dll_d')
TSV = os.path.join(W, '_buckets_patched_dll_d.tsv')

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

# ---- 黑名单（翻了毫无意义或会坏事）----
XMLDTD = {'NMTOKENS', 'IDREFS', 'PCDATA', 'NDATA', 'NOTATION', 'PUBLIC', 'SYSTEM',
          'IMPLIED', 'REQUIRED', 'INCLUDE', 'CDATA', 'ENTITY', 'ATTLIST', 'ELEMENT',
          'IDREF', 'NMTOKEN', 'ANY'}
WINAPI = re.compile(r'^(Sleep|Wake|Free|New|Get|Set|Create|Delete|Open|Close|Query|'
                    r'Initialize|InitializeCritical|Enter|Leave|Try|Wait|Reset|'
                    r'Release|Acquire|Interlocked|Co|Ole|SH|Reg|Win|Nt|Rtl|Lsa|'
                    r'Crypt|Cert|Net|Wsa|Http|WinHttp|Url|Path|Shell|Task|Av)', re.I)
SUITE = re.compile(r'(Suite|Suite$|AEGP|PF |VDS |PICA|SPBasic)', re.I)
OBJ3D = re.compile(r'(Shader|Deformer|Object|Tag|Material|Channel Tag|Cinema)', re.I)

CJK = re.compile(rb'[\x81-\xFE][\x40-\xFE]')

# 读 TSV
rows = []
with open(TSV, encoding='utf-8') as f:
    head = f.readline()
    for line in f:
        parts = line.rstrip('\n').split('\t')
        if len(parts) < 7:
            continue
        bucket, name, cnt, dlls, avail, pre, post = parts[:7]
        if bucket == 'NO_DICT':
            rows.append((name, int(cnt), dlls, int(avail), pre, post))

# 每个 DLL 的中文位置（用于判"活的 UI 表"）
zh_pos = {}
DLLS = ['Continuum_AE_8Bit.dll', 'Continuum_AE_16Bit.dll', 'Continuum_AE_Float.dll',
        'Continuum_Common_AE.dll', 'Continuum_3DObjects_AE.dll', 'BCCPlus.dll']
for d in DLLS:
    b = open(os.path.join(PATCH, d), 'rb').read()
    zh_pos[d] = [m.start() for m in CJK.finditer(b)]

# 需要 offset 才能判"附近有中文" —— TSV 没存 offset，重新扫一遍拿 name->offsets
# 只扫 .rdata 里前后都是 NUL 的独立记号（与 verify_resid 同判据）
TOKEN_RE = re.compile(rb'[\x20-\x7e]+')
offmap = collections.defaultdict(list)
for d in DLLS:
    b = open(os.path.join(PATCH, d), 'rb').read()
    for m in TOKEN_RE.finditer(b):
        s, e = m.span()
        if s > 0 and b[s - 1] != 0:
            continue
        if e >= len(b) or b[e] != 0:
            continue
        offmap[(d, m.group().decode('ascii', 'replace'))].append(s)

out = io.StringIO()
def p(s=''):
    print(s, flush=True)
    out.write(str(s) + '\n')


def near_zh(dll, off, span=256):
    lst = zh_pos.get(dll)
    if not lst:
        return False
    import bisect
    i = bisect.bisect_left(lst, off - span)
    return i < len(lst) and lst[i] <= off + span


def looks_internal(tok):
    if tok in XMLDTD:
        return True
    if '%' in tok:
        return True
    if SUITE.search(tok):
        return True
    # 无空格 + 多个大写 = 类名/函数名（SleepConditionVariableCS / PF_GET_AUDIO）
    if ' ' not in tok and sum(c.isupper() for c in tok) >= 2:
        return True
    # 全大写 = 常量
    letters = [c for c in tok if c.isalpha()]
    if letters and all(c.isupper() for c in letters) and len(letters) >= 3:
        return True
    if WINAPI.match(tok) and (' ' not in tok):
        return True
    if OBJ3D.search(tok) and ' ' in tok and tok.split()[0] in ('Surface', 'Bend', 'Vertex'):
        return True
    return False


tiers = {'A': [], 'B': [], 'C': []}
skipped = collections.Counter()
for name, cnt, dlls, avail, pre, post in rows:
    if looks_internal(name):
        skipped['internal'] += 1
        continue
    keys = [(d, name) for d in DLLS]
    offs = []
    for d in DLLS:
        offs += [(d, o) for o in offmap.get((d, name), [])]
    if not offs:
        skipped['noff'] += 1
        continue
    if not any(near_zh(d, o) for d, o in offs):
        skipped['nozh'] += 1
        continue
    if avail < 5:
        skipped['tiny'] += 1
        continue
    t = 'A' if cnt >= 3 else ('B' if cnt == 2 else 'C')
    tiers[t].append((name, cnt, dlls, avail, pre, post))

for t in tiers:
    tiers[t].sort(key=lambda r: (-r[1], r[0]))
p('候选分层（已剔内部符号 / 无中文邻居 / 容量<5）')
for t in ('A', 'B', 'C'):
    p('  %s (出现>=%s): %d 个名字 / %d 处'
      % (t, {'A': 3, 'B': 2, 'C': 1}[t], len(tiers[t]), sum(r[1] for r in tiers[t])))
p('  剔除: %s' % dict(skipped))
p()

json.dump({'A': tiers['A'], 'B': tiers['B'], 'C': tiers['C']},
          open(os.path.join(W, 'cand9.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

for t in ('A', 'B', 'C'):
    p('=' * 100)
    p('TIER %s  (%d 个)' % (t, len(tiers[t])))
    p('=' * 100)
    for name, cnt, dlls, avail, pre, post in tiers[t]:
        p('%-40s x%-3d cap=%-3d [%s]' % (name, cnt, avail, dlls))
        p('        前: %s' % pre[:110])
        if post:
            p('        后: %s' % post[:110])
    p()

open(os.path.join(W, '_cand9.txt'), 'w', encoding='utf-8').write(out.getvalue())
p('DONE')

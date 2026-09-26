# -*- coding: utf-8 -*-
"""批量补词 · 第 5 批：DLL 里那张「效果名表」（BCC ... / BCC+... / FEC ...）。
译文来源与 .aex 菜单里的效果名完全同一张表（names_manual.NAMES / CATS / zh_all.json），
所以 DLL 里显示的名字和 AE 效果菜单里的中文名字是一致的。
前缀约定沿用 hand_other2.json：ASCII 前缀照旧，只把后面的英文名换成中文。
"""
import os, re, json, sys, collections

W = r"D:\Programming project\插件汉化\_work"
sys.path.insert(0, W)
from names_manual import NAMES, CATS
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
DLLS = ['Continuum_AE_8Bit.dll', 'Continuum_AE_16Bit.dll', 'Continuum_AE_Float.dll',
        'Continuum_Common_AE.dll', 'Continuum_3DObjects_AE.dll', 'BCCPlus.dll']
TOKEN_RE = re.compile(rb'[\x20-\x7e]+')

NAMES = dict(NAMES)
NAMES.update(CATS)
zh_all = json.load(open(os.path.join(W, 'zh_all.json'), encoding='utf-8'))


def has_cjk(s):
    return any('\u4e00' <= c <= '\u9fff' for c in s)


def variants(t):
    seen = []

    def add(x):
        if x and x not in seen:
            seen.append(x)

    add(t)
    add(t + ' OBSOLETE')
    add(t + ' OBS')
    add(re.sub(r'\bOBS\b', 'OBSOLETE', t))
    base = re.sub(r'\s*(OBS|OBSOLETE)\s*$', '', t).strip()
    if base != t:
        add(base)
        add(base + ' OBSOLETE')
    return seen


def lookup(t):
    for k in variants(t):
        if k in NAMES and NAMES[k]:
            return NAMES[k]
        if k in zh_all and has_cjk(zh_all[k]):
            return zh_all[k]
    return None


rows = []
with open(os.path.join(W, '_buckets_patched_dll_d.tsv'), encoding='utf-8') as f:
    next(f)
    for ln in f:
        p = ln.rstrip('\n').split('\t')
        if len(p) >= 3 and p[0] == 'NO_DICT':
            rows.append((p[1], int(p[2])))

CAND, nores = {}, []
for name, cnt in rows:
    m = re.match(r'^(BCC\+|BCC|FEC)[ ]?(.+)$', name)
    if not m:
        continue
    pre, rest = m.group(1), m.group(2)
    zh = None
    for key in (pre + rest, 'BCC ' + rest, 'BCC+' + rest, rest):
        zh = lookup(key)
        if zh:
            break
    if not zh:
        nores.append((name, cnt))
        continue
    zh = zh.strip()
    # 短名（原串里没写 OBS/OBSOLETE）不该带「旧版」——旧版是 OBSOLETE 变体的翻译
    if not re.search(r'OBS', name):
        zh = re.sub(r'旧版$', '', zh).strip()
    if not zh or not has_cjk(zh):
        nores.append((name, cnt))
        continue
    cands = []
    prefixed = (pre + zh) if pre != 'BCC' else ('BCC ' + zh)
    if prefixed != name:
        cands.append(prefixed)
    if zh != prefixed and zh != name:          # 窄槽退路：去掉 ASCII 前缀只留中文
        cands.append(zh)
    if cands:
        CAND[name] = cands

print('效果名表候选 %d 条（%d 条对不上译文）' % (len(CAND), len(nores)))

# 容量自检
occ = collections.defaultdict(list)
for dll in DLLS:
    p = os.path.join(BK, dll)
    if not os.path.exists(p):
        continue
    d = open(p, 'rb').read()
    for mt in TOKEN_RE.finditer(d):
        s, e = mt.span()
        if s > 0 and d[s - 1] != 0:
            continue
        if e >= len(d) or d[e] != 0:
            continue
        t = mt.group().decode('ascii', 'replace')
        if t in CAND:
            j = e
            while j < len(d) and d[j] == 0:
                j += 1
            occ[t].append(j - s)

good, bad = {}, []
for t, cands in sorted(CAND.items()):
    av = occ.get(t)
    if not av:
        continue
    picked = None
    for zh in cands:
        if len(zh.encode('gbk')) + 1 <= min(av):
            picked = zh
            break
    if picked:
        good[t] = picked
    else:
        bad.append((t, '/'.join(cands), len(cands[0].encode('gbk')) + 1, min(av)))

print('容量 OK %d 条，放不下 %d 条' % (len(good), len(bad)))
for t, zh, need, av in bad[:40]:
    print('   ! %-42s %-22s need=%d avail=%d' % (t, zh, need, av))

json.dump(good, open(os.path.join(W, 'batch5_ename.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=0)
print('写出 batch5_ename.json  %d 条' % len(good))

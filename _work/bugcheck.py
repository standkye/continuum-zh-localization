# -*- coding: utf-8 -*-
"""针对若干可疑位置，逐条复现 fix3_dll.py 的判定流程，打印
  · 是否在写入清单里
  · 三道闸门各自是否触发
  · 容量是否够
目的：分清「闸门拦的」和「补丁漏的 bug」。
"""
import os, re, json, bisect

WORK = r"D:\Programming project\插件汉化\_work"
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
PATCH = os.path.join(WORK, 'patched_dll_c')
NEW_SECTIONS = {'.rdata', '_RDATA'}
TOKEN_RE = re.compile(rb'[\x20-\x7e]+')

writes = json.load(open(os.path.join(WORK, '_fix3_writes.json'), encoding='utf-8'))
by_off = {}
for row in writes:
    by_off[(row[0], row[1])] = row

NEVER = set(json.load(open(os.path.join(WORK, '_never.json'), encoding='utf-8'))) \
    if os.path.exists(os.path.join(WORK, '_never.json')) else set()

import importlib.util
src = open(os.path.join(WORK, 'fix3_dll.py'), encoding='utf-8').read()
ns = {}
# 只取固定字面量，避免执行整个脚本
exec(re.search(r'NEVER = \{(.*?)\n\}', src, re.S).group(0), ns)
exec(re.search(r'HOST = \{(.*?)\n\}', src, re.S).group(0), ns)
NEVER, HOST = ns['NEVER'], ns['HOST']

param_zh = json.load(open(os.path.join(WORK, 'param_zh.json'), encoding='utf-8'))
for extra in ('hand_all.json', 'hand_other.json', 'hand_other2.json', 'gap_zh.json'):
    fp = os.path.join(WORK, extra)
    if os.path.exists(fp):
        param_zh.update(json.load(open(fp, encoding='utf-8')))
SHORT = json.load(open(os.path.join(WORK, 'gap_zh_short.json'), encoding='utf-8'))

def sections(d):
    pe = d.find(b'PE\x00\x00')
    nsec = int.from_bytes(d[pe + 6:pe + 8], 'little')
    optsz = int.from_bytes(d[pe + 20:pe + 22], 'little')
    base = pe + 24 + optsz
    r = []
    for i in range(nsec):
        o = base + i * 40
        nm = d[o:o + 8].rstrip(b'\x00').decode('ascii', 'replace')
        rsize = int.from_bytes(d[o + 16:o + 20], 'little')
        roff = int.from_bytes(d[o + 20:o + 24], 'little')
        r.append((nm, roff, rsize))
    return r

def sec_of(secs, off):
    for nm, roff, rsize in secs:
        if roff <= off < roff + rsize:
            return nm
    return '?'

def ident_like(t):
    return ('_' in t or '.' in t) or (bool(t) and t[0].islower())

def shape_ok(t):
    if len(t) < 2 or len(t) > 60:
        return False
    if not t.isascii():
        return False
    if not (t[0].isupper() or t[0].isdigit()):
        return False
    if '_' in t or '::' in t:
        return False
    return True

out = []
def p(s=''):
    out.append(str(s))
    print(s, flush=True)

dll = 'Continuum_AE_8Bit.dll'
a = open(os.path.join(BK, dll), 'rb').read()
b = open(os.path.join(PATCH, dll), 'rb').read()
secs = sections(a)

toks = []
for m in TOKEN_RE.finditer(bytes(a)):
    s, e = m.span()
    if s > 0 and a[s - 1] != 0:
        continue
    if e >= len(a) or a[e] != 0:
        continue
    sec = sec_of(secs, s)
    if sec not in NEW_SECTIONS:
        continue
    toks.append((s, e, m.group().decode('ascii', 'replace'), sec))
offs = [t[0] for t in toks]

p('=' * 108)
p('可疑位置逐条复现（%s）' % dll)
p('=' * 108)
p()
TARGET_TOKENS = ['Rad. Position Seed', 'Fog On', 'On Flare', 'Intensity', 'Color', 'Polygons']
p('--- ① 该簇附近 .rdata 里的记号全貌（原始英文文件）---')
for (s, e, tok, sec) in toks:
    if 0x01096800 <= s <= 0x01096920:
        w = by_off.get((dll, s))
        p('    0x%08X len=%-3d avail=%-3d %-26r  写入清单=%s' %
          (s, e - s, 0, tok, ('是 → ' + w[3]) if w else '否'))
p()
p('--- ② 对每个候选逐关卡复现 ---')
for (s, e, tok, sec) in toks:
    if tok not in TARGET_TOKENS:
        continue
    if 0x01096800 > s or s > 0x01096920:
        continue
    i = offs.index(s)
    zh = param_zh.get(tok)
    gates = []
    if tok.strip().lower() in NEVER:
        gates.append('NEVER')
    if not shape_ok(tok):
        gates.append('SHAPE')
    j0 = bisect.bisect_left(offs, s - 96)
    nb = [toks[k][2] for k in range(j0, i) if ident_like(toks[k][2])]
    if nb:
        gates.append('NB(%s)' % ','.join(nb[:2]))
    j1 = bisect.bisect_right(offs, s + 128)
    hs = [toks[k][2] for k in range(j0, j1) if k != i and toks[k][2] in HOST]
    if hs:
        gates.append('HOST(%s)' % ','.join(hs[:2]))
    j = e
    while j < len(a) and a[j] == 0:
        j += 1
    avail = j - s
    cap = None
    if zh:
        try:
            cap = len(zh.encode('gbk')) + 1
        except UnicodeEncodeError:
            cap = -1
    if zh is None:
        gates.append('无译文')
    elif cap > avail:
        sh = SHORT.get(tok)
        if sh and len(sh.encode('gbk')) + 1 <= avail:
            gates.append('容量不足但短译名可用(%s)' % sh)
        else:
            gates.append('容量不足 %d>%d' % (cap, avail))
    p('  0x%08X %-26r avail=%-3d 译文=%-14s 卡在: %s'
      % (s, tok, avail, zh, ' , '.join(gates) if gates else '★ 无闸门 → 本该写入！'))
p()
p('--- ③ 前后记号的原始字节（看分隔符到底是什么）---')
i0 = [k for k, t in enumerate(toks) if 0x01096800 <= t[0] <= 0x01096920]
if i0:
    lo = toks[i0[0]][0] - 24
    hi = toks[i0[-1]][1] + 24
    p('    区间 0x%08X..0x%08X' % (lo, hi))
    p('    原始字节: %r' % bytes(a[lo:hi]))
    p('    补丁字节: %r' % bytes(b[lo:hi]))

open(os.path.join(WORK, '_bugcheck.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\nDONE')

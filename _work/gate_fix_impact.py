# -*- coding: utf-8 -*-
"""量化：把邻居闸的 ident_like 判据从「含点号」改成「点号且无空格」后，
   (a) 能救回 243 个名字里的多少；
   (b) 会新放开哪些记号（风险评估：列出所有「大写开头 + 含点号 + 无空格」的池内记号）。"""
import os, re, json, bisect, collections

WORK = r"D:\Programming project\插件汉化\_work"
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
PATCH = os.path.join(WORK, 'patched_dll_c')
NEW_SECTIONS = {'.rdata', '_RDATA'}
TOKEN_RE = re.compile(rb'[\x20-\x7e]+')

src = open(os.path.join(WORK, 'fix3_dll.py'), encoding='utf-8').read()
ns = {}
exec(re.search(r'NEVER = \{(.*?)\n\}', src, re.S).group(0), ns)
exec(re.search(r'HOST = \{(.*?)\n\}', src, re.S).group(0), ns)
NEVER, HOST = ns['NEVER'], ns['HOST']

param_zh = json.load(open(os.path.join(WORK, 'param_zh.json'), encoding='utf-8'))
for extra in ('hand_all.json', 'hand_other.json', 'hand_other2.json', 'gap_zh.json'):
    fp = os.path.join(WORK, extra)
    if os.path.exists(fp):
        param_zh.update(json.load(open(fp, encoding='utf-8')))
KEYS = set(k for k in param_zh if k.isascii() and len(k) >= 3)

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

def ident_old(t):
    return ('_' in t or '.' in t) or (bool(t) and t[0].islower())

def ident_new(t):
    """修正版：点号只有在**没有空格**时才算「配置键样」（pcfo.depth.rm.mode）。
       参数标签里的点号很常见（Rad. Position Seed / Ang. Channel / Pos. X）。"""
    if '_' in t:
        return True
    if t and t[0].islower():
        return True
    if '.' in t and ' ' not in t:
        return True
    return False

def shape_ok(t):
    return (2 <= len(t) <= 60) and t.isascii() and (t[0].isupper() or t[0].isdigit()) \
        and '_' not in t and '::' not in t

DLLS = ['Continuum_AE_8Bit.dll', 'Continuum_AE_16Bit.dll', 'Continuum_AE_Float.dll',
        'Continuum_Common_AE.dll', 'Continuum_3DObjects_AE.dll', 'BCCPlus.dll']

out = []
def p(s=''):
    out.append(str(s))
    print(s, flush=True)

blocked_old = collections.Counter()   # 旧判据卡住的名字
blocked_new = collections.Counter()
newly_open = collections.Counter()    # 新判据放开的（旧判据卡住的）名字
dot_tokens = collections.Counter()    # 大写开头 + 含点号 + 无空格 的池内记号

for dll in DLLS:
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
        tok = m.group().decode('ascii', 'replace')
        if tok[0].isupper() and '.' in tok and ' ' not in tok:
            dot_tokens[(dll.replace('Continuum_', ''), tok)] += 1
        toks.append((s, e, tok, sec))
    offs = [t[0] for t in toks]

    for i, (s, e, tok, sec) in enumerate(toks):
        if tok not in KEYS or not shape_ok(tok):
            continue
        if tok.strip().lower() in NEVER:
            continue
        if b[s:e] != a[s:e]:
            continue                     # 已改
        zh = param_zh[tok]
        j = e
        while j < len(a) and a[j] == 0:
            j += 1
        avail = j - s
        try:
            if len(zh.encode('gbk')) + 1 > avail:
                continue                 # 容量不足 → 不算闸门问题
        except UnicodeEncodeError:
            continue
        j0 = bisect.bisect_left(offs, s - 96)
        pre = [toks[k][2] for k in range(j0, i)]
        j1 = bisect.bisect_right(offs, s + 128)
        win = pre + [toks[k][2] for k in range(i + 1, j1)]
        if any(x in HOST for x in win):
            continue                     # 宿主名单拦的，另算
        if any(ident_old(x) for x in pre):
            blocked_old[tok] += 1
        if any(ident_new(x) for x in pre):
            blocked_new[tok] += 1
        if any(ident_old(x) for x in pre) and not any(ident_new(x) for x in pre):
            newly_open[tok] += 1

p('=' * 100)
p('修正 ident_like 的影响（只统计「.rdata / 词典有译文 / 未改 / 容量够 / 非宿主名单」的记号）')
p('=' * 100)
p('  旧判据（含点号即算键）卡住        : %4d 处 / %3d 个名字' % (sum(blocked_old.values()), len(blocked_old)))
p('  新判据（点号且无空格才算键）卡住  : %4d 处 / %3d 个名字' % (sum(blocked_new.values()), len(blocked_new)))
p('  ★ 仅靠这条修正就能放开          : %4d 处 / %3d 个名字' % (sum(newly_open.values()), len(newly_open)))
p()
p('  能放开的名字（前 120）：')
line = []
for nm in sorted(newly_open):
    line.append('%-30s' % nm)
    if len(line) == 3:
        p('     ' + ' '.join(line)); line = []
if line:
    p('     ' + ' '.join(line))
p()
p('  修正后**仍然**被卡的（需人工判断）：')
line = []
for nm in sorted(blocked_new):
    line.append('%-30s' % nm)
    if len(line) == 3:
        p('     ' + ' '.join(line)); line = []
if line:
    p('     ' + ' '.join(line))
p()
p('=' * 100)
p('风险评估：池内所有「大写开头 + 含点号 + 无空格」的记号（新判据会判为配置键、旧判据也判为键）')
p('=' * 100)
for (d, t), n in dot_tokens.most_common(60):
    p('   %-14s %-34s x%d' % (d, t, n))
p('   合计 %d 个（这类串新判据仍视为键，不会被翻）' % len(dot_tokens))

open(os.path.join(WORK, '_gate_fix_impact.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\nDONE')

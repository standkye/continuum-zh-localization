# -*- coding: utf-8 -*-
"""揪出真正拦路的那一个记号：对代表性参数名，打印每个出现位置前面的 6 个记号，
并标出其中被判为「标识符样」的是哪几个。"""
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

def ident_new(t):
    if '_' in t:
        return '有下划线'
    if t and t[0].islower():
        return '小写开头'
    if '.' in t and ' ' not in t:
        return '点号无空格'
    return None

DLLS = ['Continuum_AE_8Bit.dll', 'Continuum_3DObjects_AE.dll', 'BCCPlus.dll']
TARGETS = ['Blur', 'Width', 'Height', 'Rotate', 'Scale', 'Channel', 'Opacity',
           'Amount', 'Alpha Contrast', 'Anchor', 'Ambient Light']

out = []
def p(s=''):
    out.append(str(s))
    print(s, flush=True)

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
        toks.append((s, e, m.group().decode('ascii', 'replace'), sec))
    offs = [t[0] for t in toks]
    p('=' * 104)
    p(dll)
    p('=' * 104)
    for tgt in TARGETS:
        occ = [(i, t) for i, t in enumerate(toks) if t[2] == tgt]
        occ = [(i, t) for i, t in occ if b[t[0]:t[1]] == a[t[0]:t[1]]]
        if not occ:
            continue
        p()
        p('### %-20s 仍英文 %d 处' % (tgt, len(occ)))
        for i, (s, e, tok, sec) in occ[:2]:
            j0 = bisect.bisect_left(offs, s - 96)
            pre = [(toks[k][2], ident_new(toks[k][2])) for k in range(j0, i)]
            blocked = [x for x in pre if x[1]]
            p('    0x%08X  前 %d 个记号:' % (s, len(pre)))
            p('         %s' % ' | '.join('%s%s' % (x[0][:26], '' if not x[1] else '«%s»' % x[1]) for x in pre))
            p('         → 拦路者: %s' % (blocked[:3] if blocked else '（无）'))
    p()

open(os.path.join(WORK, '_blocker.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('DONE')

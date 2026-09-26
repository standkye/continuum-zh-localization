# -*- coding: utf-8 -*-
"""追问：为何这些"看着就是参数名"的词在第 3 版里仍是英文？
对每个名字列出它在本版 DLL 里的**全部独立记号位置**（节 + 是否已改 + 被哪道闸拦）。"""
import os, re, json, bisect

WORK = r"D:\Programming project\插件汉化\_work"
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
PATCH = os.path.join(WORK, 'patched_dll_c')
NEW_SECTIONS = {'.rdata', '_RDATA'}
TOKEN_RE = re.compile(rb'[\x20-\x7e]+')

NEVER = {
    'resources', 'documentation', 'filter version', 'creation date', 'category',
    'preset name', 'filter name', 'preset type', 'file path', 'description', 'author',
    'client', 'presetname', 'filtername', 'filterversion', 'datetime', 'duration',
    'debug logging', 'version update check previous', 'bcc avx licensing', 'bcc effects list',
    'bcc motion tracker fcp', 'bcc motion tracker prm', 'bcc motion tracker avid',
    'bcc motion tracker vegas', 'bcc motion tracker resolve', 'launch mocha mask',
    'launch mocha track', 'mocha init - render', 'pixelchooser mocha preset load dummy',
    'load pixelchooser and mocha with preset', 'hide disabled parameters',
    'use 4k gpu buffers', 'gpu anti alias buffer level', 'borisplugins', 'filtersets',
    'utilities', 'bin', 'stringmap', 'stringpair', 'stringid', 'stringvalue',
    'borisfxdirect', 'bfx-license-tool', 'bfx-version-update', 'mocha continuum.app',
    'pref_type', 'pref_value', 'alpha type', 'pointcount',
    'string', 'int', 'float', 'bool', 'double', 'long', 'void',
    'application', 'key', 'value', 'id', 'name', 'type',
}
HOST = {
    'Final Cut Pro', 'FinalCutPro', 'Motion', 'Red', 'Combustion', 'OpenFX',
    'Cyberlink PowerDirector', 'Corel', 'Edius Title Generator',
    'PF Pixel Format Suite', ' OBSOLETE', 'Optics', 'Silhouette',
    'AfterEffects', 'After Effects', 'PremierePro', 'Premiere',
    'SonyVegas', 'Sony Vegas', 'MagixMovieStudio', 'MagixVideoProX',
    'SonyCatalyst', 'EyeonFusion', 'AssimilateScratch', 'Quantel', 'Natron',
    'HitFilm', 'HITFILM', 'HitFilmVegasEffects', 'SGOMambaFX', 'Nucoda',
    'WondershareFilmora', 'Lightworks', 'Autograph', 'AutodeskFlame',
    'Baselight', 'Mistika', 'Avid Media Composer', 'Vegas Pro', 'Vegas Pro 13.0',
    'Motion4', 'Nuke', 'Resolve', 'DaVinci Resolve', 'BFX_PROFILE_OPENCL',
}

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

def ident_like(t):
    return ('_' in t or '.' in t) or (bool(t) and t[0].islower())

out = []
def p(s=''):
    out.append(str(s))
    print(s, flush=True)

TARGETS = ['Blur', 'Amount', 'Blue Amount', 'Border Width', 'Angle Subtlety',
           'Anchor', 'Blur 1', 'Blur Threshold', 'Bias', 'Base Color',
           'Background Color', 'Black Point', 'Adjustment', 'Air Resistance']

dll = 'Continuum_AE_8Bit.dll'
a = open(os.path.join(BK, dll), 'rb').read()
b = open(os.path.join(PATCH, dll), 'rb').read()
secs = sections(a)

toks = []
for m in TOKEN_RE.finditer(a):
    s, e = m.span()
    if s > 0 and a[s - 1] != 0:
        continue
    toks.append((s, e, m.group().decode('ascii', 'replace'), sec_of(secs, s)))
offs = [t[0] for t in toks]

p('=' * 96)
p('这些名字在 %s 里的全部独立记号位置' % dll)
p('=' * 96)
for tgt in TARGETS:
    zh = param_zh.get(tgt, '(词典无译文)')
    occ = [(i, tok) for i, tok in enumerate(toks) if tok[2] == tgt]
    p()
    p('### %-20s 词典译文=%s   独立记号 %d 处' % (tgt, zh, len(occ)))
    import collections
    bysec = collections.Counter(t[3] for i, t in occ)
    p('    节分布: %r' % dict(bysec))
    for (i, (s, e, tok, sec)) in occ[:6]:
        changed = b[s:e] != a[s:e]
        if changed:
            r = '已改'
        elif sec not in NEW_SECTIONS:
            r = '未扫（节=%s）' % sec
        elif e >= len(a) or a[e] != 0:
            r = 'NUL_BOUND（数据块碎片）'
        elif tok.strip().lower() in NEVER:
            r = 'NEVER 内部键'
        elif len(tok) < 2 or len(tok) > 60 or not (tok[0].isupper() or tok[0].isdigit()) \
                or '_' in tok or '::' in tok:
            r = '形状闸'
        else:
            j0 = bisect.bisect_left(offs, s - 96)
            nb = [toks[k][2] for k in range(j0, i) if ident_like(toks[k][2])]
            if nb:
                r = '邻居闸  近邻编号串=%r' % nb[:3]
            else:
                j1 = bisect.bisect_right(offs, s + 128)
                hh = [toks[k][2] for k in range(j0, j1) if k != i and toks[k][2] in HOST]
                if hh:
                    r = '宿主名单闸  近邻=%r' % hh[:3]
                else:
                    j = e
                    while j < len(a) and a[j] == 0:
                        j += 1
                    avail = j - s
                    if len(zh.encode('gbk')) + 1 > avail:
                        r = '容量不足 avail=%d' % avail
                    else:
                        r = '★ 未知（本该能改！）'
        p('    0x%08X %-8s %s' % (s, sec, r))

open(os.path.join(WORK, '_why_remain.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\nDONE')

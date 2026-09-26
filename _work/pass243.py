# -*- coding: utf-8 -*-
"""把新版里「词典有译文、却被安全闸门拦下」的 .rdata 英文记号全部导出，带上下文。

对每个名字给出：出现在哪几支 DLL、每个位置的节、可用容量、
以及**最近的邻居记号**（前 6 / 后 3）—— 靠邻居串才能判断它到底是参数标签还是配置键。
"""
import os, re, json, bisect, collections, sys

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

DLLS = ['Continuum_AE_8Bit.dll', 'Continuum_AE_16Bit.dll', 'Continuum_AE_Float.dll',
        'Continuum_Common_AE.dll', 'Continuum_3DObjects_AE.dll', 'BCCPlus.dll']
SHORT_DLL = {d: d.replace('Continuum_', '').replace('_AE.dll', '') for d in DLLS}

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

def ident_like(t):
    return ('_' in t or '.' in t) or (bool(t) and t[0].islower())

def shape_ok(t):
    return (2 <= len(t) <= 60) and t.isascii() and (t[0].isupper() or t[0].isdigit()) \
        and '_' not in t and '::' not in t

out = []
def p(s=''):
    out.append(str(s))
    print(s, flush=True)

# 收集：名字 -> [(dll, off, avail, 原因, 前文, 后文)]
rec = collections.defaultdict(list)

for dll in DLLS:
    a = open(os.path.join(BK, dll), 'rb').read()
    b = open(os.path.join(PATCH, dll), 'rb').read()
    secs = sections(a)
    toks = []
    for m in TOKEN_RE.finditer(b):
        s, e = m.span()
        if s > 0 and b[s - 1] != 0:
            continue
        if e >= len(b) or b[e] != 0:
            continue
        toks.append((s, e, m.group().decode('ascii', 'replace'), sec_of(secs, s)))
    offs = [t[0] for t in toks]

    for i, (s, e, tok, sec) in enumerate(toks):
        if sec not in NEW_SECTIONS:
            continue
        if tok not in KEYS or not shape_ok(tok):
            continue
        if tok.strip().lower() in NEVER:
            continue
        # 已被改过的不算
        if b[s:e] != a[s:e]:
            continue
        j0 = bisect.bisect_left(offs, s - 128)
        j1 = bisect.bisect_right(offs, s + 128)
        pre = [toks[k][2][:26] for k in range(j0, i)][-6:]
        post = [toks[k][2][:26] for k in range(i + 1, j1)][:3]
        j = e
        while j < len(a) and a[j] == 0:
            j += 1
        avail = j - s
        nb = [x for x in pre if ident_like(x)]
        hs = [x for x in pre + post if x in HOST]
        why = []
        if nb:
            why.append('NB:' + '|'.join(nb[:2]))
        if hs:
            why.append('HOST:' + '|'.join(hs[:2]))
        rec[tok].append((SHORT_DLL[dll], s, avail, why, pre, post))

p('=' * 110)
p('新版仍英文、词典有译文、被闸门拦下的 .rdata 记号 —— 共 %d 个名字 / %d 处'
  % (len(rec), sum(len(v) for v in rec.values())))
p('=' * 110)
p()

for tok in sorted(rec, key=lambda t: (-len(rec[t]), t)):
    zh = param_zh.get(tok, '?')
    lst = rec[tok]
    p('### %-32s → %-16s  %d 处 (%s)' % (tok, zh, len(lst),
        ','.join(sorted(set(x[0] for x in lst)))))
    for (d, s, avail, why, pre, post) in lst[:2]:
        p('    [%s] 0x%08X avail=%-3d %s' % (d, s, avail, ' '.join(why) if why else ''))
        p('        前: %s' % ' | '.join(pre))
        p('        后: %s' % ' | '.join(post))
    p()

open(os.path.join(WORK, '_pass243.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('DONE  名字数 %d' % len(rec))

# -*- coding: utf-8 -*-
"""精确口径：本版(patched_dll_c)还在英文的**参数名候选**，按节与原因拆开。

要点：
  · 只数「NUL 分隔的独立记号」；
  · 分成 .rdata（真参数名池所在）与 .rsrc（命令/菜单表，不是参数名）两块分别报；
  · .rdata 里再按「被哪道闸拦住 / 词典压根没这个词」归因。
"""
import os, re, json, bisect, collections, sys

WORK = r"D:\Programming project\插件汉化\_work"
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
PATCH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WORK, 'patched_dll_c')
CONT = r'C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum'
LIB = r'C:\Program Files\BorisFX\ContinuumAE\19\lib'
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

GRAND = collections.Counter()
grand_names = collections.defaultdict(set)

p('=' * 100)
p('本版 patched_dll_c：**仍在英文的参数名候选**，按节拆开')
p('=' * 100)
p('  说明：.rdata = 真参数名池所在；.rsrc = 命令/菜单表 + 3DObjects 自带 UI（不是参数名）；')
p('        .data 等 = 数据块碎片（内部 ID，翻了危险）')
p()

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
    seccnt = collections.Counter(t[3] for t in toks)

    # .rdata 里仍是英文的：分「词典有译文但被闸拦」与「词典没有这个词」
    cnt = collections.Counter()
    samples = collections.defaultdict(set)
    for t in toks:
        s, e, tok, sec = t
        if sec not in NEW_SECTIONS:
            continue
        if tok in KEYS:
            if tok.strip().lower() in NEVER:
                r = 'NEVER 内部键'
            elif not shape_ok(tok):
                r = '形状闸'
            else:
                cnt['_tmp'] = 1
                r = 'UNKNOWN'
            cnt[r] += 1
            samples[r].add(tok)
            GRAND[r] += 1
            grand_names[r].add(tok)
        else:
            if not shape_ok(tok):
                continue
            cnt['NOT_IN_DICT'] += 1
            samples['NOT_IN_DICT'].add(tok)
            GRAND['NOT_IN_DICT'] += 1
            grand_names['NOT_IN_DICT'].add(tok)
    cnt.pop('_tmp', None)

    p('%-30s' % dll.replace('Continuum_', ''))
    p('    独立英文记号总数（含 .rsrc 等）: %s' % dict(seccnt))
    p('    .rdata 里仍是英文: %s' % dict(cnt))
    for r in ('NEVER 内部键', '形状闸', 'UNKNOWN', 'NOT_IN_DICT'):
        if samples.get(r):
            p('      %-14s 样本: %s' % (r, ', '.join(sorted(samples[r])[:14])))
    p()

p('=' * 100)
p('合计（6 支 DLL、.rdata 内、仍是英文）')
p('=' * 100)
for r, n in GRAND.most_common():
    p('   %-16s %5d 处 / %4d 个名字' % (r, n, len(grand_names[r])))
p()

open(os.path.join(WORK, '_precise_remain.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\nDONE')

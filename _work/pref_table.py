# -*- coding: utf-8 -*-
"""① 定位每支 DLL 里的「Pref_Type 类型名表」字节范围（这些位置要排除）
   ② 打印若干含糊名字的上下文，判断是标签还是内部标识。"""
import os, re, json, bisect, collections

WORK = r"D:\Programming project\插件汉化\_work"
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
PATCH = os.path.join(WORK, 'patched_dll_c')
NEW_SECTIONS = {'.rdata', '_RDATA'}
TOKEN_RE = re.compile(rb'[\x20-\x7e]+')

param_zh = json.load(open(os.path.join(WORK, 'param_zh.json'), encoding='utf-8'))
for extra in ('hand_all.json', 'hand_other.json', 'hand_other2.json', 'gap_zh.json'):
    fp = os.path.join(WORK, extra)
    if os.path.exists(fp):
        param_zh.update(json.load(open(fp, encoding='utf-8')))
KEYS = set(k for k in param_zh if k.isascii() and len(k) >= 3)

DLLS = ['Continuum_AE_8Bit.dll', 'Continuum_AE_16Bit.dll', 'Continuum_AE_Float.dll',
        'Continuum_Common_AE.dll', 'Continuum_3DObjects_AE.dll', 'BCCPlus.dll']

out = []
def p(s=''):
    out.append(str(s))
    print(s, flush=True)

p('=' * 100)
p('① 「Pref_Type 类型名表」位置定位（含 Pref_Type / Pref_Value / PrefsOption / Options_Map 的簇）')
p('=' * 100)
MARKERS = {'Pref_Type', 'Pref_Value', 'Pref_Name', 'PrefID', 'PrefsOption', 'Options_Map'}
for dll in DLLS:
    a = open(os.path.join(BK, dll), 'rb').read()
    hits = []
    for m in TOKEN_RE.finditer(bytes(a)):
        s, e = m.span()
        if s > 0 and a[s - 1] != 0:
            continue
        if e < len(a) and a[e] == 0 and m.group().decode('ascii', 'replace') in MARKERS:
            hits.append((s, m.group().decode('ascii')))
    if not hits:
        p('  %-30s 无标记' % dll); continue
    # 把位置聚簇（间隔 < 512B 视为同一簇）
    clusters = []
    for s, t in hits:
        if clusters and s - clusters[-1][-1][0] < 512:
            clusters[-1].append((s, t))
        else:
            clusters.append([(s, t)])
    p('  %-30s %d 个簇' % (dll.replace('Continuum_', ''), len(clusters)))
    for c in clusters:
        lo = min(x[0] for x in c)
        hi = max(x[0] for x in c)
        p('      0x%08X..0x%08X  (%d 个标记: %s)' %
          (lo, hi, len(c), ', '.join(sorted(set(x[1] for x in c)))))
        p('        原始: %r' % bytes(a[max(0, lo - 8):hi + 120]))
p()

p('=' * 100)
p('② 含糊名字的上下文（判断是标签还是内部标识）')
p('=' * 100)
AMB = ['Master', 'Process', 'Presets', 'Rehostable', 'Dongle', 'Both', 'Hidden',
       'Input', 'Output', 'Style', 'Blend', 'Camera', 'Layer', 'Weight', 'Seed',
       'Master Opacity', 'Master Scale', 'Ripple', 'Ring', 'Twi' , 'Inverse', 'Path Direction']
for dll in DLLS:
    a = open(os.path.join(BK, dll), 'rb').read()
    b = open(os.path.join(PATCH, dll), 'rb').read()
    toks = []
    for m in TOKEN_RE.finditer(bytes(a)):
        s, e = m.span()
        if s > 0 and a[s - 1] != 0:
            continue
        if e >= len(a) or a[e] != 0:
            continue
        toks.append((s, e, m.group().decode('ascii', 'replace')))
    offs = [t[0] for t in toks]
    shown = False
    for i, (s, e, tok) in enumerate(toks):
        if tok not in AMB or tok not in KEYS:
            continue
        if b[s:e] != a[s:e]:
            continue
        if not shown:
            p(); p('--- %s ---' % dll)
            shown = True
        j0 = bisect.bisect_left(offs, s - 112)
        j1 = bisect.bisect_right(offs, s + 112)
        pre = [toks[k][2][:24] for k in range(j0, i)]
        post = [toks[k][2][:24] for k in range(i + 1, j1)]
        p('  %-22s 0x%08X  前: %s' % (tok, s, ' | '.join(pre)))
        p('  %-22s %8s  后: %s' % ('', '', ' | '.join(post)))

open(os.path.join(WORK, '_pref_table.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\nDONE')

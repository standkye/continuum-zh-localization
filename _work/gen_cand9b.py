# -*- coding: utf-8 -*-
"""候选 v2：在 gen_cand9 基础上再剔三类噪声
   ① 串里含 '|'        -> 枚举选项表，不能拆词翻（v10 崩溃教训）
   ② 邻居是内部串      -> JPEG/GL 报错、遥测埋点、授权、Cinema4D 对象、字体、日期
   ③ 纯碎片/人名/版本  -> P291 之类
输出"干净候选"的紧凑清单，供手写翻译。
"""
import os, re, json, collections, io, sys, bisect

W = r'D:\Programming project\插件汉化\_work'
PATCH = os.path.join(W, 'patched_dll_d')
DLLS = ['Continuum_AE_8Bit.dll', 'Continuum_AE_16Bit.dll', 'Continuum_AE_Float.dll',
        'Continuum_Common_AE.dll', 'Continuum_3DObjects_AE.dll', 'BCCPlus.dll']

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

cand = json.load(open(os.path.join(W, 'cand9.json'), encoding='utf-8'))

# ---- 邻居黑名单（命中即判为"内部串区"，整条丢弃）----
MARK = re.compile(
    r'(JPEG|jpeglib|glGet|glShader|glLink|glProgram|GL_|gl[A-Z]|'
    r'Shader|Sketch|Toon|Vertex Map|Subsurface|C\.o\.f\.f\.e\.e|'
    r'BFX|BFXD|Registration|License|licens|Preferences|PLists|Mocha|'
    r'PixelChooser|Autotrace|scanline|Corrupt|corrupt|Premature|'
    r'Bogus|Invalid|Insufficient|Internal error|Null pointer|Division by|'
    r'Bad argument|Occured|occured|obsolete|OBSOLETE|'
    r'Continuum19|Version Update|Error|error|Warning|warning|'
    r'Oct 27|build date|build time|%d|%s|%u|%02d)', re.I)

FONTS = re.compile(r'^(Arial|Helvetica|Times|Courier|Verdana|Tahoma|Impact|Georgia|'
                   r'Palatino|Comic|Trebuchet|MS Sans|MS Serif|Symbol|Wingdons|'
                   r'Segoe|Calibri|Cambria|Consolas|Monaco|Lucida)( .+)?$', re.I)
DATE = re.compile(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b')
JUNKNOUN = re.compile(r'^[A-Z][a-z]?[0-9]{1,4}$')      # P291 / X12
PERSON = {'Banji', 'Banzi', 'Cheen', 'Danel', 'Mabel', 'Nukei', 'Mg', 'Banjo'}

out = io.StringIO()
def p(s=''):
    print(s, flush=True)
    out.write(str(s) + '\n')

clean = {'A': [], 'B': [], 'C': []}
drop = collections.Counter()
for tier in ('A', 'B', 'C'):
    for (name, cnt, dlls, avail, pre, post) in cand[tier]:
        ctx = (pre or '') + ' | ' + (post or '')
        if '|' in name:
            drop['enum'] += 1; continue
        if MARK.search(name) or MARK.search(ctx):
            drop['marker'] += 1; continue
        if FONTS.match(name):
            drop['font'] += 1; continue
        if DATE.match(name):
            drop['date'] += 1; continue
        if JUNKNOUN.match(name):
            drop['junknoun'] += 1; continue
        if name in PERSON:
            drop['person'] += 1; continue
        if not any(c.isalpha() for c in name):
            drop['noalpha'] += 1; continue
        clean[tier].append((name, cnt, dlls, avail, pre, post))

p('二次过滤后：')
for t in ('A', 'B', 'C'):
    p('  %s: %d 个名字 / %d 处' % (t, len(clean[t]), sum(r[1] for r in clean[t])))
p('  丢弃: %s' % dict(drop))
p()

json.dump(clean, open(os.path.join(W, 'cand9b.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

# 紧凑清单：名字 | 次数 | 容量 | DLL
for t in ('A', 'B', 'C'):
    p('#' * 90)
    p('# TIER %s  (%d)' % (t, len(clean[t])))
    p('#' * 90)
    for name, cnt, dlls, avail, pre, post in clean[t]:
        p('%-42s|%-3d|%-3d|%s' % (name, cnt, avail, dlls))
    p()

open(os.path.join(W, '_cand9b.txt'), 'w', encoding='utf-8').write(out.getvalue())
p('DONE')

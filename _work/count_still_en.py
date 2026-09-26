# -*- coding: utf-8 -*-
"""英文残留计数：英文备份 / 上一版补丁(patched_dll_b, 当前装机) / 本版(patched_dll_c)

判据：只数**独立 NUL 记号**（前字节=NUL 且后字节=NUL），且该串在词典里有译文。
      长串里的子串不算（例如 "Frame Scale X" 里的 "Scale X" 不是独立标签）。
"""
import os, re, json

WORK = r"D:\Programming project\插件汉化\_work"
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"

DLLS = ['Continuum_AE_8Bit.dll', 'Continuum_AE_16Bit.dll', 'Continuum_AE_Float.dll',
        'Continuum_Common_AE.dll', 'Continuum_3DObjects_AE.dll', 'BCCPlus.dll']

TOKEN_RE = re.compile(rb'[\x20-\x7e]+')

param_zh = json.load(open(os.path.join(WORK, 'param_zh.json'), encoding='utf-8'))
for extra in ('hand_all.json', 'hand_other.json', 'hand_other2.json', 'gap_zh.json'):
    fp = os.path.join(WORK, extra)
    if os.path.exists(fp):
        param_zh.update(json.load(open(fp, encoding='utf-8')))

KEYS = set(k for k in param_zh if k.isascii() and len(k) >= 3)

out = []
def p(s=''):
    out.append(str(s))
    print(s, flush=True)

def count(path):
    """返回 (独立英文残留处数, 去重名字数, 每支明细)"""
    tot = 0
    names = set()
    det = {}
    for dll in DLLS:
        fp = os.path.join(path, dll)
        if not os.path.exists(fp):
            fp = os.path.join(CONT, dll)
        d = open(fp, 'rb').read()
        c = 0
        for m in TOKEN_RE.finditer(d):
            s, e = m.span()
            if s > 0 and d[s - 1] != 0:
                continue
            if e >= len(d) or d[e] != 0:
                continue
            t = m.group().decode('ascii', 'replace')
            if t in KEYS:
                c += 1
                names.add(t)
        det[dll] = c
        tot += c
    return tot, len(names), det

p('=' * 92)
p('英文残留（独立记号，且词典里有译文）')
p('=' * 92)
p()

for tag, path in (('英文原版', BK),
                  ('上一版 patched_dll_b（= 当前装机）', os.path.join(WORK, 'patched_dll_b')),
                  ('本版 patched_dll_c', os.path.join(WORK, 'patched_dll_c'))):
    if not os.path.isdir(path):
        p('%-40s !! 目录不存在' % tag); continue
    tot, n, det = count(path)
    p('%-40s 残留 %5d 处 / %4d 个名字' % (tag, tot, n))
    for k, v in det.items():
        p('      %-30s %5d' % (k, v))
    p()

open(os.path.join(WORK, '_still_en.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('DONE')

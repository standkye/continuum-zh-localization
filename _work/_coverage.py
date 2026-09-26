# -*- coding: utf-8 -*-
"""实测交付目录 488 个 .aex 的 eman（效果名）/ gtac（分组）中文覆盖率。"""
import os

D = r'D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0'
out = []
def say(*a):
    out.append(' '.join(str(x) for x in a))

CATS = {}
def rec(k, v):
    CATS[k] = CATS.get(k, 0) + 1

files = sorted(f for f in os.listdir(D) if f.lower().endswith('.aex'))
bad = []
for f in files:
    d = open(os.path.join(D, f), 'rb').read()
    for key in (b'eman', b'gtac'):
        mk = b'MIB8' + key
        j = d.find(mk)
        if j < 0:
            rec(key.decode() + '_MISSING', 1)
            bad.append((f, key.decode(), 'no-record'))
            continue
        k = j + 16
        if k >= len(d):
            rec(key.decode() + '_TRUNC', 1)
            bad.append((f, key.decode(), 'trunc'))
            continue
        n = d[k]
        body = d[k+1:k+1+n]
        is_zh = any(b >= 0x80 for b in body)
        rec(key.decode() + ('_ZH' if is_zh else '_EN'), 1)
        if key == b'gtac' and not is_zh:
            bad.append((f, 'gtac', body))

say('交付目录 .aex: %d 个' % len(files))
say('')
say('eman（效果名）:  中文 %d / 英文 %d / 其他 %d'
    % (CATS.get('eman_ZH', 0), CATS.get('eman_EN', 0),
       CATS.get('eman_MISSING', 0) + CATS.get('eman_TRUNC', 0)))
say('gtac（分组）  :  中文 %d / 英文 %d / 其他 %d'
    % (CATS.get('gtac_ZH', 0), CATS.get('gtac_EN', 0),
       CATS.get('gtac_MISSING', 0) + CATS.get('gtac_TRUNC', 0)))
say('')
say('原始计数: %r' % CATS)
say('')
say('--- 仍为英文的 gtac 明细（前 40）---')
for f, k, b in bad[:40]:
    try:
        s = b.decode('ascii')
    except Exception:
        s = repr(b)
    say('   %-32s %s' % (f, s))

open(r'D:\Programming project\插件汉化\_work\_coverage.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('done')

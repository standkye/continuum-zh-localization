# -*- coding: utf-8 -*-
"""刷新交付目录（GBK 修复版）"""
import os, shutil, io

W = r"D:\Programming project\插件汉化"
STAGE = os.path.join(W, "Continuum 汉化组件 v19.0.0")
PAEX = os.path.join(W, "_work", "patched_aex_b")
PDLL = os.path.join(W, "_work", "patched_dll_b")

o = []
def p(s=''):
    o.append(str(s))
    print(s, flush=True)

p('=== 刷新前：交付目录现有条目 ===')
for f in sorted(os.listdir(STAGE)):
    fp = os.path.join(STAGE, f)
    if os.path.isdir(fp):
        p('  [DIR ] %-44s %d 项' % (f, len(os.listdir(fp))))
    else:
        p('  [FILE] %-44s %s' % (f, format(os.path.getsize(fp), ',')))

p()
p('=== 覆盖 aex / dll ===')
n = 0
for f in sorted(os.listdir(PAEX)):
    if f.lower().endswith('.aex'):
        shutil.copy2(os.path.join(PAEX, f), os.path.join(STAGE, f))
        n += 1
p('  aex 覆盖 %d 个' % n)

n = 0
for f in sorted(os.listdir(PDLL)):
    if f.lower().endswith('.dll'):
        shutil.copy2(os.path.join(PDLL, f), os.path.join(STAGE, f))
        n += 1
p('  dll 覆盖 %d 个' % n)

p()
p('=== 校验（交付目录 vs 补丁产物）===')
bad = []
for f in sorted(os.listdir(PAEX)):
    if not f.lower().endswith('.aex'):
        continue
    a = open(os.path.join(PAEX, f), 'rb').read()
    b = open(os.path.join(STAGE, f), 'rb').read()
    if a != b:
        bad.append(f)
p('  aex 不一致: %d %s' % (len(bad), bad[:6]))
bad = []
for f in sorted(os.listdir(PDLL)):
    if not f.lower().endswith('.dll'):
        continue
    a = open(os.path.join(PDLL, f), 'rb').read()
    b = open(os.path.join(STAGE, f), 'rb').read()
    if a != b:
        bad.append(f)
p('  dll 不一致: %d %s' % (len(bad), bad))

p()
p('=== 抽样：交付目录里的字节 ===')
d = open(os.path.join(STAGE, 'BCCBlur.aex'), 'rb').read()
j = d.find(b'MIB8eman')
seg = d[j + 16:j + 40]
L = seg[0]
body = seg[1:1 + L]
p('  BCCBlur.aex eman L=%d body=%r' % (L, body))
for enc in ('gbk', 'utf-8'):
    try:
        p('    按 %-6s -> %r' % (enc, body.decode(enc)))
    except Exception as e:
        p('    按 %-6s -> 解码失败' % enc)

dl = open(os.path.join(STAGE, 'Continuum_AE_8Bit.dll'), 'rb').read()
p('  8Bit.dll 含 GBK「主不透明度」: %s' % ('主不透明度'.encode('gbk') in dl))
p('  8Bit.dll 含 UTF-8「主不透明度」: %s' % ('主不透明度'.encode('utf-8') in dl))
p('  8Bit.dll 仍保留英文 Resources: %s' % (b'Resources\x00' in dl))

open(os.path.join(W, '_work', '_stage_refresh2.txt'), 'w', encoding='utf-8').write('\n'.join(o))

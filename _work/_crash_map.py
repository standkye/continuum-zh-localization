# -*- coding: utf-8 -*-
"""排查「纹理」效果崩溃嫌疑：查 *Map* / Texture 相关写入的上下文，
   看它们到底是不是 UI 显示名。"""
import os, json

BASE = r'D:\Programming project\插件汉化'
PD = os.path.join(BASE, '_work', 'patched_dll_d')
out = []
def say(*a):
    out.append(' '.join(str(x) for x in a))

with open(os.path.join(BASE, '_work', '_fix4_writes.json'), encoding='utf-8') as f:
    writes = json.load(f)

# 按 file 索引
byfile = {}
for w in writes:
    byfile.setdefault(w[0], []).append(w)

SUSPECT = ['Map', 'Maps', 'Bump Map', 'Displacement Map', 'Height Maps',
           'Z Map', 'Target Map Layer', 'Texture', 'Texture Flow Direction',
           'Pattern', 'Style', 'Mode']

for fn in sorted(byfile):
    if not fn.lower().endswith('.dll'):
        continue
    hits = [w for w in byfile[fn] if any(w[2].lower() == s.lower() for s in SUSPECT)]
    if not hits:
        continue
    d = open(os.path.join(PD, fn), 'rb').read()
    say('=' * 74)
    say('%s   — %d 条可疑写入' % (fn, len(hits)))
    for w in hits:
        off, old, zh = w[1], w[2], w[3]
        lo = max(0, off - 72); hi = min(len(d), off + 72)
        chunks = []; cur = b''; pos = lo
        for q in range(lo, hi):
            c = d[q]
            if 32 <= c < 127 or c >= 0x80:
                if not cur: pos = q
                cur += bytes([c])
            else:
                if len(cur) >= 2: chunks.append((pos, cur))
                cur = b''
        if len(cur) >= 2: chunks.append((pos, cur))
        say('')
        say('  [%s] -> [%s]  off=%#x avail=%s' % (old, zh, off, w[6] if len(w) > 6 else '?'))
        for p_, c_ in chunks:
            try: t = c_.decode('gbk')
            except Exception: t = repr(c_)
            mark = '  <<< 本次写入' if p_ == off else ''
            say('      @%#x %s%s' % (p_, t, mark))

open(os.path.join(BASE, '_work', '_crash_probe.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('done')

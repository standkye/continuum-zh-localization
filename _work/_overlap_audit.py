# -*- coding: utf-8 -*-
"""全量体检：每个写入点在【英文原文件】里是否真的是"独立记号"
   （前一个字节必须是 NUL）。不是 => 它写进了别的字符串内部 => 会破坏那个字符串。"""
import os, json

BASE = r'D:\Programming project\插件汉化'
PD = os.path.join(BASE, '_work', 'patched_dll_d')
BK = r'C:\Program Files\BorisFX\ContinuumAE\19\Backup-English'
out = []
def say(*a):
    out.append(' '.join(str(x) for x in a))

with open(os.path.join(BASE, '_work', '_fix4_writes.json'), encoding='utf-8') as f:
    writes = json.load(f)

# 英文备份文件名 -> 路径映射（有的 DLL 在 MediaCore）
MAP = {
    'Continuum_AE_8Bit.dll': os.path.join(BK, 'Continuum_AE_8Bit.dll'),
    'Continuum_AE_16Bit.dll': os.path.join(BK, 'Continuum_AE_16Bit.dll'),
    'Continuum_AE_Float.dll': os.path.join(BK, 'Continuum_AE_Float.dll'),
    'Continuum_Common_AE.dll': os.path.join(BK, 'Continuum_Common_AE.dll'),
    'Continuum_3DObjects_AE.dll': os.path.join(BK, 'Continuum_3DObjects_AE.dll'),
    'BCCPlus.dll': os.path.join(BK, 'BCCPlus.dll'),
}

cache = {}
def src(fn):
    if fn not in cache:
        p = MAP.get(fn)
        cache[fn] = open(p, 'rb').read() if p and os.path.exists(p) else None
    return cache[fn]

bad = []
for w in writes:
    fn, off, old, zh = w[0], w[1], w[2], w[3]
    s = src(fn)
    if s is None:
        continue
    if off == 0 or off >= len(s):
        bad.append((fn, off, old, zh, '越界'))
        continue
    prev = s[off - 1]
    if prev != 0:
        # 不是独立记号：往前找它所属的完整字符串
        st = off - 1
        while st > 0 and s[st - 1] != 0:
            st -= 1
        en = off
        while en < len(s) and s[en] != 0:
            en += 1
        host = s[st:en]
        try:
            hs = host.decode('gbk')
        except Exception:
            hs = repr(host)
        bad.append((fn, off, old, zh, '宿主串=[%s]' % hs))

say('=== 写入点落在【别的字符串内部】的坏写入 ===')
say('（判定：英文原文件里 off-1 不是 NUL）')
say('')
say('共 %d 条' % len(bad))
for fn, off, old, zh, why in bad:
    say('  %-28s off=%#x  [%s] -> [%s]' % (fn, off, old, zh))
    say('        %s' % why)
say('')

# 额外：统计每支 DLL 的分布
import collections
c = collections.Counter(x[0] for x in bad)
say('--- 按 DLL 统计 ---')
for k, v in c.items():
    say('   %-30s %d' % (k, v))

open(os.path.join(BASE, '_work', '_overlap_audit.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('done  bad=%d' % len(bad))

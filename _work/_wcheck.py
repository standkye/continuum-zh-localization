# -*- coding: utf-8 -*-
"""核查 accept3 报的「野改动」是否就是尾清零（tail-zero）落入未声明区间，
   并列出 .rsrc 里的写入点内容。"""
import os, json

WORK = r"D:\Programming project\插件汉化\_work"
writes = json.load(open(os.path.join(WORK, '_fix3_writes.json'), encoding='utf-8'))
print('写入点总数', len(writes))
print('字段数', len(writes[0]), writes[0])
print()

# 1) 野改动定位
loc = {
    'BCCPlus.dll': 0x025BB121,
    'Continuum_3DObjects_AE.dll': 0x0126B9E1,
    'Continuum_AE_16Bit.dll': 0x00FB6F51,
    'Continuum_AE_8Bit.dll': 0x00FB3199,
    'Continuum_AE_Float.dll': 0x00FE1D69,
    'Continuum_Common_AE.dll': 0x00AB5954,
}
print('=== 野改动定位（该位置落在哪个写入点里）===')
for dll, off in loc.items():
    hit = None
    for w in writes:
        if w[0] != dll:
            continue
        o = w[1]
        zb = w[3].encode('gbk')
        nz = max(len(zb), len(w[2])) + 1
        if o <= off < o + nz:
            hit = (o, w[2], w[3], len(zb) + 1, nz, w[6], off - o)
            break
    if hit:
        o, old, zh, n1, nz, avail, rel = hit
        print('  %-28s 0x%08X 在写入点 0x%08X(相对+%d)  n(声明)=%d  nz(实写)=%d  avail=%d'
              % (dll, off, o, rel, n1, nz, avail))
        print('     原文 %r -> 译名 %r  ; 是否「越出 n 但仍在 nz 内」= %s'
              % (old, zh, n1 <= rel < nz))
    else:
        print('  %-28s 0x%08X 未命中任何写入点 !!' % (dll, off))
print()

# 2) .rsrc 写入点
print('=== .rsrc 内的写入点 ===')
n = 0
for w in writes:
    if w[4] == '.rsrc':
        n += 1
        print('  %-28s 0x%08X avail=%-3d %-30r -> %r' % (w[0], w[1], w[6], w[2][:30], w[3]))
print('  .rsrc 合计 %d 处' % n)
print()

# 3) 各 DLL 写入点分布
import collections
c = collections.Counter((w[0], w[4]) for w in writes)
print('=== 各 DLL x 节 分布 ===')
for k in sorted(c):
    print('  %-30s %-8s %d' % (k[0], k[1], c[k]))

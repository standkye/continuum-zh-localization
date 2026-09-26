# -*- coding: utf-8 -*-
import os
ROOT = r'D:\Programming project\插件汉化'
def size(p):
    t = 0
    for dp, dn, fn in os.walk(p):
        for f in fn:
            try: t += os.path.getsize(os.path.join(dp, f))
            except OSError: pass
    return t
def mb(n): return '%.1f MB' % (n / 1048576.0)

rows = []
for name in sorted(os.listdir(ROOT)):
    p = os.path.join(ROOT, name)
    if os.path.isdir(p):
        rows.append((size(p), name + '/'))
    else:
        try: rows.append((os.path.getsize(p), name))
        except OSError: pass
rows.sort(reverse=True)
print('== 一级目录/文件大小 TOP ==')
for s, n in rows[:25]:
    print('  %12s  %s' % (mb(s), n))
print()
print('== 总计 ==')
print('  ', mb(sum(r[0] for r in rows)))
print()
DEL = os.path.join(ROOT, 'Continuum 汉化组件 v19.0.0')
print('== 交付目录构成 ==')
print('   总', mb(size(DEL)))
ext = {}
for f in os.listdir(DEL):
    e = os.path.splitext(f)[1].lower() or '(noext)'
    ext[e] = ext.get(e, 0) + os.path.getsize(os.path.join(DEL, f))
for e, s in sorted(ext.items(), key=lambda x: -x[1]):
    print('   %-8s %6d 个  %s' % (e, sum(1 for f in os.listdir(DEL) if (os.path.splitext(f)[1].lower() or '(noext)') == e), mb(s)))
print()
W = os.path.join(ROOT, '_work')
big = []
for dp, dn, fn in os.walk(W):
    for f in fn:
        p = os.path.join(dp, f)
        try: big.append((os.path.getsize(p), os.path.relpath(p, ROOT)))
        except OSError: pass
big.sort(reverse=True)
print('== _work 里最大的 20 个文件 ==')
for s, f in big[:20]:
    print('   %12s  %s' % (mb(s), f))
print('   _work 文件数', len(big), ' 合计', mb(sum(b[0] for b in big)))

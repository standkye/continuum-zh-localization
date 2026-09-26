# -*- coding: utf-8 -*-
"""batch9 容量自检：每个译名在其所有出现位置上都得放得下（GBK）
   need = len(zh.encode('gbk')) + 1  必须 <= avail（到下一个非 NUL 字节的距离）
"""
import os, re, json, collections, io, sys

W = r'D:\Programming project\插件汉化\_work'
BK = r'C:\Program Files\BorisFX\ContinuumAE\19\Backup-English'
DLLS = ['Continuum_AE_8Bit.dll', 'Continuum_AE_16Bit.dll', 'Continuum_AE_Float.dll',
        'Continuum_Common_AE.dll', 'Continuum_3DObjects_AE.dll', 'BCCPlus.dll']
TOKEN_RE = re.compile(rb'[\x20-\x7e]+')

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

d = json.load(open(os.path.join(W, 'batch9_miss.json'), encoding='utf-8'))
# 与已有词典冲突检查
old = json.load(open(os.path.join(W, 'param_zh.json'), encoding='utf-8'))
for extra in ('hand_all.json', 'hand_other.json', 'hand_other2.json', 'gap_zh.json',
              'batch5_ename.json', 'batch6_ui.json', 'batch7_miss.json',
              'batch8_miss.json'):
    fp = os.path.join(W, extra)
    if os.path.exists(fp):
        old.update(json.load(open(fp, encoding='utf-8')))

out = io.StringIO()
def p(s=''):
    print(s, flush=True)
    out.write(str(s) + '\n')

clash = [(k, v, old[k]) for k, v in d.items() if k in old and old[k] != v]
p('与已有词典冲突(会被本表覆盖): %d' % len(clash))
for k, v, o in clash[:20]:
    p('   %-38s 旧 %r -> 新 %r' % (k, o, v))

# 收集：英文备份里每个 token 的所有 (dll, off, avail)
info = collections.defaultdict(list)
for dll in DLLS:
    a = open(os.path.join(BK, dll), 'rb').read()
    n = len(a)
    for m in TOKEN_RE.finditer(a):
        s, e = m.span()
        if s > 0 and a[s - 1] != 0:
            continue
        if e >= n or a[e] != 0:
            continue
        j = e
        while j < n and a[j] == 0:
            j += 1
        info[m.group().decode('ascii', 'replace')].append((dll, s, j - s))

over = []
miss = []
for k, v in sorted(d.items()):
    if k not in info:
        miss.append(k)
        continue
    try:
        nb = len(v.encode('gbk'))
    except UnicodeEncodeError as ex:
        p('  !! GBK 编码失败 %s -> %s (%s)' % (k, v, ex))
        continue
    need = nb + 1
    worst = min(x[2] for x in info[k])
    if need > worst:
        over.append((k, v, need, worst, len(info[k])))

p()
p('batch9 共 %d 条' % len(d))
p('  在英文备份里找不到: %d  %s' % (len(miss), miss[:10]))
p('  最小容量不足（装不下）: %d' % len(over))
for k, v, need, worst, cnt in sorted(over, key=lambda r: -(r[2] - r[3])):
    p('    %-38s %-22r need=%-3d min_avail=%-3d 出现%d次' % (k, v, need, worst, cnt))
    # 给个可行长度建议
    fit = (worst - 1) // 2
    p('        -> 最多 %d 个汉字' % fit)

open(os.path.join(W, '_check9.txt'), 'w', encoding='utf-8').write(out.getvalue())
p('DONE')

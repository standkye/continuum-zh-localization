# -*- coding: utf-8 -*-
"""对账：为什么 count_still_en 与 diag_remain 报的 8Bit 残留数差很多。
逐个列出 count_still_en 判定为「残留」的记号，并给出它在英文版里的前后文，
再人工看几个是否真的是「未被改动的独立标签」。
"""
import os, re, json

WORK = r"D:\Programming project\插件汉化\_work"
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
PATCH = os.path.join(WORK, 'patched_dll_c')
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

dll = 'Continuum_AE_8Bit.dll'
a = open(os.path.join(BK, dll), 'rb').read()
b = open(os.path.join(PATCH, dll), 'rb').read()

# --- 方法 1：count_still_en 的口径（NUL 起点 + NUL 结尾） ---
res1 = []
for m in TOKEN_RE.finditer(b):
    s, e = m.span()
    if s > 0 and b[s - 1] != 0:
        continue
    if e >= len(b) or b[e] != 0:
        continue
    t = m.group().decode('ascii', 'replace')
    if t in KEYS:
        res1.append((s, t))
p('方法1（当前补丁文件 b）残留 %d 处' % len(res1))

# --- 方法 2：拿英文版枚举，再看补丁文件同位是否变了 ---
res2 = []
for m in TOKEN_RE.finditer(a):
    s, e = m.span()
    if s > 0 and a[s - 1] != 0:
        continue
    if e >= len(a) or a[e] != 0:
        continue
    t = m.group().decode('ascii', 'replace')
    if t in KEYS and a[s:e] == b[s:e]:
        res2.append((s, t))
p('方法2（英文版枚举 + 同位未变）残留 %d 处' % len(res2))

# --- 方法 3：进一步筛「补丁文件里该位置现在仍是纯 ASCII」 ---
res3 = [(s, t) for s, t in res2 if b[s:s + len(t)] == t.encode()]
p('方法3（同位仍是同一串 ASCII）残留 %d 处' % len(res3))

# --- 方法 4：补丁文件里「凭空多出来的」英文记号（原文里同位置不是干净记号）---
orig_clean = set()
for m in TOKEN_RE.finditer(a):
    s, e = m.span()
    if s > 0 and a[s - 1] != 0 and True:
        pass
    if (s == 0 or a[s - 1] == 0) and e < len(a) and a[e] == 0:
        orig_clean.add(s)
newjunk = []
for m in TOKEN_RE.finditer(b):
    s, e = m.span()
    if s > 0 and b[s - 1] != 0:
        continue
    if e >= len(b) or b[e] != 0:
        continue
    if s not in orig_clean:
        newjunk.append((s, m.group().decode('ascii', 'replace')))
p('方法4（补丁里新出现的英文记号 = 残尾垃圾）%d 处' % len(newjunk))

set1 = set(o for o, t in res1)
set3 = set(o for o, t in res3)
p('只在方法1里出现的 %d 处' % len(set1 - set3))
p('只在方法3里出现的 %d 处' % len(set3 - set1))
p()

def ctx(x, off, n=48):
    lo = max(0, off - n)
    pre = x[lo:off]
    return pre

p('=' * 90)
p('方法1 独有的前 40 处（很可能是方法1 口径出了问题）')
p('=' * 90)
for s, t in [x for x in res1 if x[0] in (set1 - set3)][:40]:
    p('  0x%08X %-24r  前:%r  补丁同位:%r' % (s, t, ctx(a, s), b[s:s + len(t) + 1]))
p()

p('=' * 90)
p('方法3 独有的前 40 处（真·残留）')
p('=' * 90)
for s, t in [x for x in res3 if x[0] in (set3 - set1)][:40]:
    p('  0x%08X %-24r  前:%r' % (s, t, ctx(a, s)))
p()

p('=' * 90)
p('方法3（真残留）按名字聚合 Top 40')
p('=' * 90)
import collections
c = collections.Counter(t for s, t in res3)
for t, n in c.most_common(40):
    p('   %-40s %4d' % (t, n))
p('真残留名字数 %d，处数 %d' % (len(c), len(res3)))

open(os.path.join(WORK, '_reconcile.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('DONE')

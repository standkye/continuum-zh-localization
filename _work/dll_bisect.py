# -*- coding: utf-8 -*-
"""二分法定位：3DObjects.dll 里哪一处改动导致 DllMain 失败 (err=1114)

以「槽位」为单位（不是字节），逐个叠加改动测加载。
"""
import os, sys, json, subprocess, shutil, io

BASE = r'D:\Programming project\插件汉化'
WORK = os.path.join(BASE, '_work')
TMP = r'C:\Users\Jinna\.workbuddy\dlldbg'
os.makedirs(TMP, exist_ok=True)

BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
LIB = r"C:\Program Files\BorisFX\ContinuumAE\19\lib"
PY = r'C:\Users\Jinna\.workbuddy\binaries\python\versions\3.13.12\python.exe'

LOG = os.path.join(WORK, '_bisect_log.txt')
lines = []
def p(s=''):
    lines.append(str(s))
    print(s, flush=True)

TEST_SRC = r'''
import ctypes, sys, os
p = os.path.abspath(sys.argv[1])
try:
    h = ctypes.WinDLL(p, winmode=0)
    print("OK")
except OSError as e:
    print("FAIL %s" % getattr(e, 'winerror', '?'))
except Exception as e:
    print("FAIL other %s" % e)
'''
TESTPY = os.path.join(TMP, '_load_test.py')
open(TESTPY, 'w', encoding='utf-8').write(TEST_SRC)

TARGET = 'Continuum_3DObjects_AE.dll'

chains = json.load(open(os.path.join(WORK, 'dll_chains.json'), encoding='utf-8'))
ch = chains[TARGET]

bk = open(os.path.join(BK, TARGET), 'rb').read()
cur = open(os.path.join(LIB, TARGET), 'rb').read()

# ---- 收集所有有改动的槽位 ----
slots = []
for off_s, arr in ch.items():
    o = int(off_s)
    for s in arr:
        slot = max(8, ((len(s) + 1 + 7) // 8) * 8)
        if bk[o:o + slot] != cur[o:o + slot]:
            slots.append((o, slot, bk[o:o + slot], cur[o:o + slot], s))
        o += slot
slots.sort()

p('=' * 74)
p('%s 二分定位' % TARGET)
p('=' * 74)
p('改动槽位总数: %d' % len(slots))
p('文件大小: 备份 %d / 装机 %d' % (len(bk), len(cur)))
p()

def build(k, tag):
    """从备份出发，应用前 k 个槽位的改动"""
    d = bytearray(bk)
    for (o, slot, old, new, s) in slots[:k]:
        d[o:o + slot] = new
    fp = os.path.join(TMP, 'dbg_%s.dll' % tag)
    with open(fp, 'wb') as f:
        f.write(d)
    return fp

def try_load(fp):
    r = subprocess.run([PY, TESTPY, fp], capture_output=True)
    o = (r.stdout + r.stderr).decode('utf-8', 'replace').strip()
    return o.startswith('OK'), o

# ---- 0) 基线：原版 / 全量 ----
fp0 = build(0, 'k0000')
ok0, o0 = try_load(fp0)
p('[基线] k=0（纯原版）      : %s' % o0)
fpn = build(len(slots), 'kfull')
okn, on = try_load(fpn)
p('[基线] k=%d（全部改动）: %s' % (len(slots), on))
p()

if ok0 is False:
    p('!! 原版基线都加载失败，测试环境有问题（依赖缺失？），二分无意义。')
    open(LOG, 'w', encoding='utf-8').write('\n'.join(lines))
    sys.exit(1)

if okn is True:
    p('!! 全部改动竟然能加载 —— 说明失败与字节改动无单调关系，'
      '可能需要在真实 AE 环境下才复现（或存在交互效应）。')
    open(LOG, 'w', encoding='utf-8').write('\n'.join(lines))
    sys.exit(2)

# ---- 二分 ----
lo, hi = 0, len(slots)          # lo: 已知 OK, hi: 已知 FAIL
step = 0
while lo + 1 < hi:
    mid = (lo + hi) // 2
    step += 1
    fp = build(mid, 'b%02d_%d' % (step, mid))
    ok, o = try_load(fp)
    p('  第%2d步  k=%3d  ->  %s' % (step, mid, o))
    if ok:
        lo = mid
    else:
        hi = mid
    try:
        os.remove(fp)
    except Exception:
        pass

p()
p('=' * 74)
p('结论：第 %d 个改动槽位是罪魁（k=%d 能加载，k=%d 失败）' % (hi, lo, hi))
o, slot, old, new, s = slots[hi - 1]
p('  偏移 0x%X   槽位大小 %d 字节' % (o, slot))
p('  原始字符串键: %r' % s)
p('  原字节: %r' % old)
p('  新字节: %r' % new)
try:
    body = new.split(b'\x00')[0]
    p('  新内容按 UTF-8: %r' % body.decode('utf-8'))
except Exception as e:
    p('  新内容 UTF-8 解码失败: %s' % e)
try:
    body = new.split(b'\x00')[0]
    p('  新内容按 GBK  : %r' % body.decode('gbk'))
except Exception as e:
    p('  新内容 GBK 解码失败: %s' % e)
p()
p('  附近 6 个改动槽位（按偏移）:')
idx = hi - 1
for j in range(max(0, idx - 3), min(len(slots), idx + 3)):
    o2, sl2, old2, new2, s2 = slots[j]
    mark = ' <<< 罪魁' if j == idx else ''
    p('    #%d off=0x%-9X slot=%-3d  %-28r -> %r%s' % (j, o2, sl2, s2, new2.split(b'\x00')[0], mark))

open(LOG, 'w', encoding='utf-8').write('\n'.join(lines))

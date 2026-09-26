# -*- coding: utf-8 -*-
"""第三次修正：用 PATH 注入 lib 目录，让依赖能被解析"""
import os, json, subprocess

WORK = r'D:\Programming project\插件汉化\_work'
TMP = r'C:\Users\Jinna\.workbuddy\dlldbg'
os.makedirs(TMP, exist_ok=True)
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
LIB = r"C:\Program Files\BorisFX\ContinuumAE\19\lib"
CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"
PY = r'C:\Users\Jinna\.workbuddy\binaries\python\versions\3.13.12\python.exe'

TESTPY = os.path.join(TMP, '_lt4.py')
open(TESTPY, 'w', encoding='utf-8').write('''
import ctypes, sys, os
p = os.path.abspath(sys.argv[1])
try:
    ctypes.WinDLL(p, winmode=0)
    print("OK")
except OSError as e:
    print("FAIL winerror=%s %s" % (getattr(e, "winerror", None), e))
except Exception as e:
    print("FAIL other %s" % e)
''')

ENV = os.environ.copy()
ENV['PATH'] = LIB + os.pathsep + CONT + os.pathsep + ENV.get('PATH', '')

def load_ok(data, tag):
    fp = os.path.join(TMP, 'p_%s.dll' % tag)
    with open(fp, 'wb') as f:
        f.write(data)
    r = subprocess.run([PY, TESTPY, fp], capture_output=True, env=ENV)
    o = (r.stdout + r.stderr).decode('utf-8', 'replace').strip()
    try:
        os.remove(fp)
    except Exception:
        pass
    return o

chains = json.load(open(os.path.join(WORK, 'dll_chains.json'), encoding='utf-8'))
out = []
def p(s=''):
    out.append(str(s))
    print(s, flush=True)

TARGETS = ['Continuum_3DObjects_AE.dll', 'Continuum_AE_8Bit.dll',
           'Continuum_AE_Float.dll', 'Continuum_AE_16Bit.dll',
           'Continuum_Common_AE.dll', 'BCCPlus.dll']

p('=' * 78)
p('基线（PATH 注入后）  依赖目录: %s' % LIB)
p('=' * 78)
base = {}
for T in TARGETS:
    bkp = os.path.join(BK, T)
    curp = os.path.join(LIB if T != 'BCCPlus.dll' else CONT, T)
    bk = open(bkp, 'rb').read()
    cur = open(curp, 'rb').read()
    o0 = load_ok(bk, 'b')
    o1 = load_ok(cur, 'c')
    base[T] = (o0.startswith('OK'), o1.startswith('OK'))
    p('  %-30s 备份原版: %-12s   当前装机: %s'
      % (T, 'OK' if o0.startswith('OK') else o0[:60], 'OK' if o1.startswith('OK') else o1[:60]))

p()
if not base['Continuum_AE_8Bit.dll'][0]:
    p('!! 备份原版 8Bit 仍加载失败，测试环境依然有问题，后续结论不可信。')
    open(os.path.join(WORK, '_layer_test3.txt'), 'w', encoding='utf-8').write('\n'.join(out))
    raise SystemExit(1)

p('=' * 78)
p('分层 revert')
p('=' * 78)

L1 = {'resources', 'documentation'}
L2 = L1 | {'filter version', 'creation date', 'category', 'preset name',
           'filter name', 'preset type', 'file path', 'description',
           'author', 'client'}
L3 = L2 | {'debug logging', 'version update check previous',
           'bcc avx licensing', 'bcc effects list'}
L4 = L3 | {'bcc motion tracker fcp', 'bcc motion tracker prm',
           'bcc motion tracker avid', 'bcc motion tracker vegas',
           'bcc motion tracker resolve', 'launch mocha mask',
           'launch mocha track', 'mocha init - render',
           'pixelchooser mocha preset load dummy',
           'load pixelchooser and mocha with preset',
           'hide disabled parameters', 'use 4k gpu buffers',
           'gpu anti alias buffer level'}
LAYERS = [('L1(2)', L1), ('L2(11)', L2), ('L3(15)', L3), ('L4(28)', L4)]

for T in TARGETS:
    ch = chains.get(T)
    bkp = os.path.join(BK, T)
    curp = os.path.join(LIB if T != 'BCCPlus.dll' else CONT, T)
    bk = open(bkp, 'rb').read()
    cur = open(curp, 'rb').read()
    changed = []
    for off_s, arr in ch.items():
        o = int(off_s)
        for s in arr:
            slot = max(8, ((len(s) + 1 + 7) // 8) * 8)
            if bk[o:o + slot] != cur[o:o + slot]:
                changed.append((o, slot, s.strip()))
            o += slot
    p()
    p('%s   （改动槽位 %d）' % (T, len(changed)))
    for label, S in LAYERS:
        d = bytearray(cur)
        hit = 0
        for (o, sl, s) in changed:
            if s.lower() in S:
                d[o:o + sl] = bk[o:o + sl]
                hit += 1
        o2 = load_ok(d, 'x')
        p('    %-8s 恢复 %3d 槽 -> %s' % (label, hit, o2[:70]))

open(os.path.join(WORK, '_layer_test3.txt'), 'w', encoding='utf-8').write('\n'.join(out))

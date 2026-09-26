# -*- coding: utf-8 -*-
"""分层 revert 测试：找出「够用的最小排除集」

从装机文件出发，把候选槽位恢复成英文，测 LoadLibrary。
逐层扩大候选集，直到加载成功。
"""
import os, json, subprocess

WORK = r'D:\Programming project\插件汉化\_work'
TMP = r'C:\Users\Jinna\.workbuddy\dlldbg'
os.makedirs(TMP, exist_ok=True)
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
LIB = r"C:\Program Files\BorisFX\ContinuumAE\19\lib"
CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"
PY = r'C:\Users\Jinna\.workbuddy\binaries\python\versions\3.13.12\python.exe'
TESTPY = os.path.join(TMP, '_lt2.py')
open(TESTPY, 'w', encoding='utf-8').write(
    "import ctypes,sys,os\n"
    "p=os.path.abspath(sys.argv[1])\n"
    "try:\n"
    "    ctypes.WinDLL(p, winmode=0); print('OK')\n"
    "except OSError as e:\n"
    "    print('FAIL %s' % getattr(e,'winerror','?'))\n"
    "except Exception as e:\n"
    "    print('FAIL other %s' % e)\n")

def load_ok(data, tag):
    fp = os.path.join(TMP, 'lv_%s.dll' % tag)
    with open(fp, 'wb') as f:
        f.write(data)
    r = subprocess.run([PY, TESTPY, fp], capture_output=True)
    o = (r.stdout + r.stderr).decode('utf-8', 'replace').strip()
    try:
        os.remove(fp)
    except Exception:
        pass
    return o.startswith('OK'), o

# ---- 分层候选集（按「确定性」从高到低）----
L1 = {'resources', 'documentation'}                      # 找目录 / 帮助文件
L2 = L1 | {'filter version', 'creation date', 'category',
           'preset name', 'filter name', 'preset type', 'file path',
           'description', 'author', 'client'}            # 预设元数据字段
L3 = L2 | {'debug logging', 'version update check previous',
           'bcc avx licensing', 'bcc effects list'}      # 设置/子程序名
L4 = L3 | {'bcc motion tracker fcp', 'bcc motion tracker prm',
           'bcc motion tracker avid', 'bcc motion tracker vegas',
           'bcc motion tracker resolve', 'launch mocha mask',
           'launch mocha track', 'mocha init - render',
           'pixelchooser mocha preset load dummy',
           'load pixelchooser and mocha with preset',
           'hide disabled parameters', 'use 4k gpu buffers',
           'gpu anti alias buffer level'}                # 其余可疑

LAYERS = [('L1(2项)', L1), ('L2(11项)', L2), ('L3(15项)', L3), ('L4(28项)', L4)]

chains = json.load(open(os.path.join(WORK, 'dll_chains.json'), encoding='utf-8'))
out = []
def p(s=''):
    out.append(str(s))
    print(s, flush=True)

for T in ['Continuum_3DObjects_AE.dll', 'Continuum_AE_8Bit.dll',
          'Continuum_AE_Float.dll', 'Continuum_AE_16Bit.dll']:
    ch = chains.get(T)
    bkp = os.path.join(BK, T)
    curp = os.path.join(LIB, T)
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

    p('=' * 78)
    p(T + '   改动槽位 %d' % len(changed))
    p('=' * 78)
    for label, S in LAYERS:
        d = bytearray(cur)
        hit = 0
        for (o, sl, s) in changed:
            if s.lower() in S:
                d[o:o + sl] = bk[o:o + sl]
                hit += 1
        ok, o2 = load_ok(d, 'x')
        p('    %-10s 恢复 %3d 个槽位 -> %s' % (label, hit, o2))
    p()

open(os.path.join(WORK, '_layer_test.txt'), 'w', encoding='utf-8').write('\n'.join(out))

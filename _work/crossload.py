# -*- coding: utf-8 -*-
"""定位加载失败到底是「哪一支」引起的：交叉组合 插件 × 依赖目录。
用 4 组组合分别起独立进程 LoadLibrary，把结论钉死。
"""
import os, subprocess

W = r'D:\Programming project\插件汉化\_work'
TMP = r'C:\Users\Jinna\.workbuddy\dlldbg'
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
LIB = r"C:\Program Files\BorisFX\ContinuumAE\19\lib"
CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"
PY = r'C:\Users\Jinna\.workbuddy\binaries\python\versions\3.13.12\python.exe'
os.makedirs(TMP, exist_ok=True)
TESTPY = os.path.join(TMP, '_vl2.py')
open(TESTPY, 'w', encoding='utf-8').write('''
import ctypes, sys, os
p = os.path.abspath(sys.argv[1])
try:
    ctypes.WinDLL(p, winmode=0)
    print("OK")
except OSError as e:
    print("FAIL winerror=%s %s" % (getattr(e, "winerror", None), e))
''')


def load(src, pathdir):
    fp = os.path.join(TMP, 'x_' + os.path.basename(src))
    open(fp, 'wb').write(open(src, 'rb').read())
    env = os.environ.copy()
    env['PATH'] = pathdir + os.pathsep + LIB + os.pathsep + CONT + os.pathsep + env.get('PATH', '')
    r = subprocess.run([PY, TESTPY, fp], capture_output=True, env=env)
    os.remove(fp)
    return (r.stdout + r.stderr).decode('utf-8', 'replace').strip()[:60]


DIRS = {'c': os.path.join(W, 'patched_dll_c'),
        'd': os.path.join(W, 'patched_dll_d'),
        'bk': BK,
        'lib': LIB}
ENG = ['Continuum_AE_8Bit.dll', 'Continuum_Common_AE.dll']

out = []
for e in ENG:
    out.append('=== %s ===' % e)
    for tag, pdir in DIRS.items():
        src = os.path.join(pdir, e)
        if not os.path.exists(src):
            out.append('   %-24s 缺文件' % tag); continue
        out.append('   插件取自 %-3s 依赖目录=%s -> %s' % (tag, tag, load(src, pdir)))
    out.append('')
    # 交叉：插件固定取 d，依赖目录换成 c
    src = os.path.join(DIRS['d'], e)
    out.append('   插件取自 d   依赖目录=c  -> %s' % load(src, DIRS['c']))
    out.append('   插件取自 c   依赖目录=d  -> %s' % load(os.path.join(DIRS['c'], e), DIRS['d']))
    out.append('')

open(os.path.join(W, '_crossload.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('DONE')

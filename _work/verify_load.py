# -*- coding: utf-8 -*-
"""★ 修复版验收：6 支 DLL 必须全部能 LoadLibrary 成功（DllMain 不失败）

这是本次事故后新增的**强制验收环节** —— 结构检查全过、字节 diff 全 0，
都不代表宿主能加载它。唯一可信的代理指标就是真的 LoadLibrary 一次。
"""
import os, subprocess, sys

WORK = r'D:\Programming project\插件汉化\_work'
TMP = r'C:\Users\Jinna\.workbuddy\dlldbg'
os.makedirs(TMP, exist_ok=True)
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
LIB = r"C:\Program Files\BorisFX\ContinuumAE\19\lib"
CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"
PY = r'C:\Users\Jinna\.workbuddy\binaries\python\versions\3.13.12\python.exe'
# 可传参指定待验目录：python verify_load.py [目录] [--baseline]
PATCH = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else os.path.join(WORK, 'patched_dll_c')
BASELINE = '--baseline' in sys.argv          # 加 --baseline 则验证英文备份（阴性对照）

TESTPY = os.path.join(TMP, '_vl.py')
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

def load(fp, pathdir):
    env = os.environ.copy()
    env['PATH'] = pathdir + os.pathsep + LIB + os.pathsep + CONT + os.pathsep + env.get('PATH', '')
    r = subprocess.run([PY, TESTPY, fp], capture_output=True, env=env)
    return (r.stdout + r.stderr).decode('utf-8', 'replace').strip()

def cp_to_tmp(name, src):
    fp = os.path.join(TMP, 'vl_' + name)
    with open(fp, 'wb') as f:
        f.write(open(src, 'rb').read())
    return fp

ENGINES = ['Continuum_AE_Float.dll', 'Continuum_AE_8Bit.dll', 'Continuum_AE_16Bit.dll',
           'Continuum_Common_AE.dll', 'Continuum_3DObjects_AE.dll', 'BCCPlus.dll']

out = []
def p(s=''):
    out.append(str(s))
    print(s, flush=True)

p('=' * 78)
p('★ DLL 加载验收   目录=%s%s' % (PATCH, '  (英文备份/阴性对照)' if BASELINE else ''))
p('=' * 78)
p()

allok = True
for name in ENGINES:
    src = os.path.join(BK if BASELINE else PATCH, name)
    if not os.path.exists(src):
        p('  %-30s !! 补丁产物缺失' % name); allok = False; continue
    fp = cp_to_tmp(name, src)
    o = load(fp, PATCH if not BASELINE else LIB)
    ok = o.startswith('OK')
    if not ok:
        allok = False
    p('  %-30s %s' % (name, o[:70]))
    try:
        os.remove(fp)
    except Exception:
        pass

p()
p('  => %s' % ('★ 全部 6 支通过，可以打包' if allok else '!! 有 DLL 仍加载失败，禁止打包'))

# 顺便抽样回读中文
p()
p('--- 抽样回读 ---')
for name in ('Continuum_AE_8Bit.dll', 'Continuum_3DObjects_AE.dll', 'BCCPlus.dll'):
    fp = os.path.join(PATCH, name)
    if not os.path.exists(fp):
        continue
    d = open(fp, 'rb').read()
    for probe in ('主不透明度', '关键帧输出', '模糊数量',
                  '通道', '宽度', '旋转', '完成百分比', '使用合成运动模糊',
                  '像素选取目标', '轴心点', '传播模式'):
        try:
            b = probe.encode('gbk')
        except Exception:
            continue
        hit = b in d
        if hit or probe in ('主不透明度', '关键帧输出'):
            p('  %-30s 含 %-16s : %s' % (name, probe, hit))
    # 内部键必须还是英文
    for must in (b'Resources\x00', b'Documentation\x00'):
        p('  %-30s 仍保留英文 %-20s : %s' % (name, must[:-1].decode(), must in d))

open(os.path.join(WORK, '_verify_load.txt'), 'w', encoding='utf-8').write('\n'.join(out))

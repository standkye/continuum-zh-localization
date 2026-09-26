# -*- coding: utf-8 -*-
"""触发 v10 安装器（UAC 自提权，DETACHED_PROCESS 分离）+ 轮询 sha256 验收"""
import os, sys, time, hashlib, subprocess, ctypes

DELIV = r'D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0'
EXE = os.path.join(DELIV, 'Continuum汉化安装器.exe')
CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"
LIB = r"C:\Program Files\BorisFX\ContinuumAE\19\lib"
LOG = r'D:\Programming project\插件汉化\_work\_install10.txt'

LIB_DLLS = ["Continuum_AE_Float.dll", "Continuum_AE_8Bit.dll", "Continuum_AE_16Bit.dll",
            "Continuum_Common_AE.dll", "Continuum_3DObjects_AE.dll"]

out = []
def p(s):
    print(s, flush=True)
    out.append(s)
    try:
        open(LOG, 'w', encoding='utf-8').write('\n'.join(out))
    except Exception:
        pass

def sha(path):
    m = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            m.update(b)
    return m.hexdigest()

# 期望值（交付目录）
want = {d: sha(os.path.join(DELIV, d)) for d in LIB_DLLS}
want['BCCPlus.dll'] = sha(os.path.join(DELIV, 'BCCPlus.dll'))
aex = [f for f in os.listdir(DELIV) if f.lower().endswith('.aex')]
p('交付: %d aex + 6 dll' % len(aex))
p('exe: %s  %d bytes' % (EXE, os.path.getsize(EXE)))

# 提权触发（DETACHED_PROCESS 分离，避免被工具超时掐死）
code = ("import sys,ctypes;"
        "rc=ctypes.windll.shell32.ShellExecuteW(None,'runas',sys.argv[1],None,None,1);"
        "open(sys.argv[2],'w').write('rc=%d'%rc)")
rcfile = r'D:\Programming project\插件汉化\_work\_uac10.txt'
if os.path.exists(rcfile):
    os.remove(rcfile)
subprocess.Popen([sys.executable, "-c", code, EXE, rcfile],
                 creationflags=0x00000008, close_fds=True)
p('UAC 已触发，等待用户批准 ...')

deadline = time.time() + 600
last = None
while time.time() < deadline:
    state = []
    ok = 0
    for d in LIB_DLLS:
        fp = os.path.join(LIB, d)
        if not os.path.exists(fp):
            state.append((d, 'MISSING')); continue
        h = sha(fp)
        if h == want[d]: ok += 1; state.append((d, 'OK'))
        else: state.append((d, 'OLD'))
    fp = os.path.join(CONT, 'BCCPlus.dll')
    if os.path.exists(fp) and sha(fp) == want['BCCPlus.dll']:
        ok += 1; state.append(('BCCPlus.dll', 'OK'))
    else:
        state.append(('BCCPlus.dll', '?'))
    sig = ' '.join('%s=%s' % s for s in state)
    if sig != last:
        p('[%3ds] %d/6  %s' % (time.time() - (deadline - 600), ok, sig))
        last = sig
    if ok == 6:
        # 再核对 aex
        bad = []
        for f in aex:
            fp = os.path.join(CONT, f)
            if not os.path.exists(fp) or sha(fp) != sha(os.path.join(DELIV, f)):
                bad.append(f)
        p('==> 6/6 DLL 已更新；aex 不一致 %d / %d' % (len(bad), len(aex)))
        for f in bad[:10]:
            p('    - ' + f)
        if not bad:
            p('==> SUCCESS：全部文件已与交付目录一致')
        break
    time.sleep(4)
else:
    p('==> 超时（10 分钟）未完成，最后状态: %s' % last)

if os.path.exists(rcfile):
    p('ShellExecuteW rc: ' + open(rcfile).read())

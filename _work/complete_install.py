# -*- coding: utf-8 -*-
"""等 AE 关闭 -> 自动触发 UAC 安装 -> 轮询 sha256 直到落地

阶段 1：轮询 tasklist，等 AfterFX.exe 退出（用户手动关；最多等 40 分钟）
阶段 2：DETACHED 方式触发 ShellExecuteW(runas, 安装器 exe)（只弹一次 UAC）
阶段 3：轮询 494 个文件的 sha256，落地即报成功
"""
import os, sys, time, subprocess, hashlib

BASE = r'D:\Programming project\插件汉化'
DELIV = os.path.join(BASE, 'Continuum 汉化组件 v19.0.0')
EXE = os.path.join(DELIV, 'Continuum汉化安装器.exe')
LIB = r'C:\Program Files\BorisFX\ContinuumAE\19\lib'
CONT = r'C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum'
LOG = os.path.join(BASE, '_work', 'complete_install_log.txt')
LAUNCHLOG = os.path.join(BASE, '_work', '_launch_rc2.txt')

logf = open(LOG, 'w', encoding='utf-8')
def p(*a):
    line = ' '.join(str(x) for x in a)
    try:
        print(line, flush=True)
    except Exception:
        pass
    logf.write(line + '\n')
    logf.flush()

def sha(fp):
    h = hashlib.sha256()
    try:
        with open(fp, 'rb') as f:
            for c in iter(lambda: f.read(1 << 20), b''):
                h.update(c)
        return h.hexdigest()
    except Exception as e:
        return 'ERR:' + str(e)

TARGETS = []
for f in sorted(os.listdir(DELIV)):
    if f.lower().endswith('.aex'):
        TARGETS.append((f, os.path.join(CONT, f)))
    elif f.lower().endswith('.dll') and f in (
            'Continuum_AE_Float.dll', 'Continuum_AE_8Bit.dll', 'Continuum_AE_16Bit.dll',
            'Continuum_Common_AE.dll', 'Continuum_3DObjects_AE.dll'):
        TARGETS.append((f, os.path.join(LIB, f)))
    elif f == 'BCCPlus.dll':
        TARGETS.append((f, os.path.join(CONT, f)))
SRC_HASH = {n: sha(os.path.join(DELIV, n)) for n, _ in TARGETS}
TOTAL = len(TARGETS)

def count_diff():
    d = 0
    for n, dst in TARGETS:
        if not os.path.exists(dst) or sha(dst) != SRC_HASH[n]:
            d += 1
    return d

def procs():
    try:
        return subprocess.run(['tasklist', '/NH'], capture_output=True).stdout.lower()
    except Exception:
        return b''

p('=' * 70)
p('Continuum 汉化（GBK 修复版）安装收尾')
p('时间:', time.strftime('%Y-%m-%d %H:%M:%S'))
p('待落地 %d 个文件' % TOTAL)
p('=' * 70)

d0 = count_diff()
p('当前 TOTAL_DIFF = %d / %d' % (d0, TOTAL))
if d0 == 0:
    p('已经是修复版，无需安装。')
    logf.close(); sys.exit(0)

# ---------------- 阶段 1：等 AE 退出 ----------------
p()
p('[1] 等待 After Effects 关闭 ...')
p('    >>> 请彻底退出 AE（窗口全部关掉）<<<')
deadline = time.time() + 2400        # 40 分钟
waited = 0
while time.time() < deadline:
    if b'afterfx.exe' not in procs():
        p('    AE 已退出（等了 %d 秒）' % waited)
        break
    if waited % 30 == 0:
        p('    仍在等待... 已等 %d 秒' % waited)
    time.sleep(5)
    waited += 5
else:
    p('    超时：40 分钟内 AE 未关闭，脚本退出。')
    p('    关掉 AE 后请手动双击：')
    p('    ' + EXE)
    logf.close(); sys.exit(3)

# ---------------- 阶段 2：触发 UAC ----------------
if os.path.exists(LAUNCHLOG):
    os.remove(LAUNCHLOG)
code = (
    "import sys,ctypes;"
    "rc=ctypes.windll.shell32.ShellExecuteW(None,'runas',sys.argv[1],None,sys.argv[2],1);"
    "open(sys.argv[3],'w').write('ShellExecuteW rc=%d'%rc)"
)
subprocess.Popen(
    [sys.executable, '-c', code, EXE, DELIV, LAUNCHLOG],
    creationflags=0x00000008,
    close_fds=True,
)
p()
p('[2] 已发出提权请求 —— 桌面弹出 UAC')
p('    >>> 请点「是」<<<')

# ---------------- 阶段 3：轮询 ----------------
p()
p('[3] 轮询 sha256 ...')
deadline2 = time.time() + 900
last = None
t0 = time.time()
seen = False
while time.time() < deadline2:
    try:
        d = count_diff()
    except Exception:
        d = -1
    el = int(time.time() - t0)
    if d != last:
        p('    t=%3ds  TOTAL_DIFF = %d / %d' % (el, d, TOTAL))
        last = d
    if d == 0:
        p()
        p('  *** 安装成功：%d / %d 全部落地 ***' % (TOTAL, TOTAL))
        break
    if not seen and b'consent.exe' in procs():
        seen = True
        p('    (检测到 consent.exe —— UAC 框在桌面上等你点)')
    time.sleep(5)
else:
    p()
    p('  超时：15 分钟未落地，TOTAL_DIFF 停在 %s / %d' % (last, TOTAL))
    p('  请手动双击安装器：' + EXE)

# ---------------- 抽样复核 ----------------
if count_diff() == 0:
    p()
    p('  抽样回读（装机文件）：')
    for f, dst in (('BCCBlur.aex', os.path.join(CONT, 'BCCBlur.aex')),
                   ('BCC3WayColorGrade.aex', os.path.join(CONT, 'BCC3WayColorGrade.aex'))):
        try:
            d = open(dst, 'rb').read()
            j = d.find(b'MIB8eman')
            seg = d[j + 16:j + 40]
            L = seg[0]
            body = seg[1:1 + L]
            try:
                txt = body.decode('gbk')
            except Exception:
                txt = repr(body)
            p('    %-24s GBK 解码 -> %r' % (f, txt))
        except Exception as e:
            p('    %-24s 读取失败 %s' % (f, e))
    try:
        dl = os.path.join(LIB, 'Continuum_AE_8Bit.dll')
        dd = open(dl, 'rb').read()
        p('    Continuum_AE_8Bit.dll 含 GBK「主不透明度」: %s' % ('主不透明度'.encode('gbk') in dd))
        p('    Continuum_AE_8Bit.dll 仍保留英文 Resources : %s' % (b'Resources\x00' in dd))
    except Exception as e:
        p('    DLL 抽样失败', e)

p()
p('日志结束', time.strftime('%H:%M:%S'))
logf.close()

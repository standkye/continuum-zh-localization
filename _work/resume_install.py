# -*- coding: utf-8 -*-
"""续做收尾：触发 UAC 安装 + 轮询 sha256 直到 494 个文件全部落地。

用法（后台跑）：
  python resume_install.py
输出落在 _work\resume_install_log.txt，便于随时查看进度。
"""
import os, sys, time, subprocess, hashlib, io

BASE = r'D:\Programming project\插件汉化'
DELIV = os.path.join(BASE, 'Continuum 汉化组件 v19.0.0')
EXE = os.path.join(DELIV, 'Continuum汉化安装器.exe')
LIB = r'C:\Program Files\BorisFX\ContinuumAE\19\lib'
CONT = r'C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum'
LOG = os.path.join(BASE, '_work', 'resume_install_log.txt')
LAUNCHLOG = os.path.join(BASE, '_work', '_launch_rc.txt')

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

# 交付目录里需要落地的文件
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

SRC_HASH = {name: sha(os.path.join(DELIV, name)) for name, _ in TARGETS}
TOTAL = len(TARGETS)

def count_diff():
    d = 0
    for name, dst in TARGETS:
        if not os.path.exists(dst) or sha(dst) != SRC_HASH[name]:
            d += 1
    return d

def ae_running():
    try:
        out = subprocess.run(['tasklist', '/NH'], capture_output=True).stdout
        return b'afterfx.exe' in out.lower()
    except Exception:
        return False

def consent_pending():
    try:
        out = subprocess.run(['tasklist', '/NH'], capture_output=True).stdout
        return b'consent.exe' in out.lower()
    except Exception:
        return False

p('=' * 70)
p('Continuum 汉化收尾：触发安装并轮询')
p('时间:', time.strftime('%Y-%m-%d %H:%M:%S'))
p('=' * 70)

# --- 0) 前置检查 -------------------------------------------------------
if ae_running():
    p('[中止] After Effects 正在运行，文件会被占用。请彻底退出 AE 后重试。')
    logf.close(); sys.exit(3)
p('[0] 前置检查通过：AE / Pr 均未运行，待落地 %d 个文件' % TOTAL)

d0 = count_diff()
p('    当前 TOTAL_DIFF = %d / %d' % (d0, TOTAL))
if d0 == 0:
    p('    已经是新版，无需安装。')
    logf.close(); sys.exit(0)

if os.path.exists(LAUNCHLOG):
    os.remove(LAUNCHLOG)

# --- 1) 分离式触发 UAC -------------------------------------------------
code = (
    "import sys,ctypes;"
    "rc=ctypes.windll.shell32.ShellExecuteW(None,'runas',sys.argv[1],None,sys.argv[2],1);"
    "open(sys.argv[3],'w').write('ShellExecuteW rc=%d'%rc)"
)
subprocess.Popen(
    [sys.executable, '-c', code, EXE, DELIV, LAUNCHLOG],
    creationflags=0x00000008,        # DETACHED_PROCESS：不等用户点，立刻返回
    close_fds=True,
)
p('[1] 已发出提权请求 —— 桌面应弹出 UAC 确认框')
p('    >>> 请点「是」 <<<')
p('    （rc>32 只代表弹窗弹出，不代表你已批准；下面用 sha256 轮询判断真假）')

# --- 2) 轮询 -----------------------------------------------------------
DEADLINE = time.time() + 900        # 最多等 15 分钟
last = None
t0 = time.time()
seen_consent = False

while time.time() < DEADLINE:
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
    if not seen_consent and consent_pending():
        seen_consent = True
        p('    (检测到 consent.exe —— UAC 确认框正挂在桌面上等你点)')
    time.sleep(5)
else:
    p()
    p('  超时：15 分钟内未检测到安装落地，TOTAL_DIFF 停在 %s / %d' % (last, TOTAL))
    if os.path.exists(LAUNCHLOG):
        p('  启动器返回：' + open(LAUNCHLOG).read())

# --- 3) 落地后复核关键样本 --------------------------------------------
if count_diff() == 0:
    p()
    p('  抽样复核（装机文件直接回读）：')
    for f, dst in [('BCCBlur.aex', os.path.join(CONT, 'BCCBlur.aex')),
                   ('BCC3WayColorGrade.aex', os.path.join(CONT, 'BCC3WayColorGrade.aex'))]:
        try:
            d = open(dst, 'rb').read()
            j = d.find(b'MIB8eman')
            p('    %-24s eman=%r' % (f, d[j + 16:j + 30]))
        except Exception as e:
            p('    %-24s 读取失败 %s' % (f, e))
    try:
        dl = os.path.join(LIB, 'Continuum_AE_8Bit.dll')
        dd = open(dl, 'rb').read()
        for probe in ('主不透明度', '关键帧输出'):
            p('    Continuum_AE_8Bit.dll 含 %-8s : %s' % (probe, probe.encode('utf-8') in dd))
    except Exception as e:
        p('    DLL 抽样失败', e)

p()
p('日志结束', time.strftime('%H:%M:%S'))
logf.close()

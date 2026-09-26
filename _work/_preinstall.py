# -*- coding: utf-8 -*-
"""安装前环境预检：宿主是否在跑 / 是否有待处理 UAC / 装机现状。"""
import os, subprocess, hashlib

out = []
def say(*a):
    out.append(' '.join(str(x) for x in a))

# 1) 进程检查
try:
    r = subprocess.run(['tasklist', '/NH'], capture_output=True)
    txt = r.stdout.decode('gbk', 'ignore')
except Exception as e:
    txt = ''
    say('tasklist 失败:', e)

watch = ['AfterFX', 'After Effects', 'Premiere', 'consent', 'Continuum', 'BCC',
         'Adobe Desktop', 'CCXProcess', 'node.exe']
say('--- 关键进程 ---')
for line in txt.splitlines():
    for w in watch:
        if w.lower() in line.lower():
            say('   ' + line.strip())
            break
say('')

# 2) 装机现状 sha256
PATHS = {
    'Continuum_AE_Float.dll':  r'C:\Program Files\BorisFX\ContinuumAE\19\lib\Continuum_AE_Float.dll',
    'Continuum_AE_8Bit.dll':   r'C:\Program Files\BorisFX\ContinuumAE\19\lib\Continuum_AE_8Bit.dll',
    'Continuum_AE_16Bit.dll':  r'C:\Program Files\BorisFX\ContinuumAE\19\lib\Continuum_AE_16Bit.dll',
    'Continuum_Common_AE.dll': r'C:\Program Files\BorisFX\ContinuumAE\19\lib\Continuum_Common_AE.dll',
    'Continuum_3DObjects_AE.dll': r'C:\Program Files\BorisFX\ContinuumAE\19\lib\Continuum_3DObjects_AE.dll',
    'BCCPlus.dll':             r'C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum\BCCPlus.dll',
}
DELIV = r'D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0'

def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()

say('--- 装机现状 vs 交付目录 ---')
for name, p in PATHS.items():
    if not os.path.exists(p):
        say('   %-30s 未找到: %s' % (name, p)); continue
    h_inst = sha(p)
    h_deliv = sha(os.path.join(DELIV, name))
    m = '一致(已是新版)' if h_inst == h_deliv else '不同(待更新)'
    mt = ''
    try:
        import time
        mt = time.strftime('%m-%d %H:%M:%S', time.localtime(os.path.getmtime(p)))
    except Exception:
        pass
    say('   %-30s %s  inst=%s deliv=%s  mtime=%s'
        % (name, m, h_inst[:12], h_deliv[:12], mt))
say('')

# 3) 还原脚本在不在
say('--- 交付目录关键文件 ---')
for f in ['Continuum汉化安装器.exe', '还原英文（双击这个）.bat', 'Install-Chinese.bat',
          'Restore-English.bat', '说明.txt']:
    p = os.path.join(DELIV, f)
    say('   %-30s %s %s' % (f, '有' if os.path.exists(p) else '缺',
                            os.path.getsize(p) if os.path.exists(p) else ''))

# 4) 英文备份目录
bk = r'C:\Program Files\BorisFX\ContinuumAE\19\Backup-English'
say('')
say('--- 英文备份 ---')
say('   %s 存在=%s' % (bk, os.path.isdir(bk)))
if os.path.isdir(bk):
    say('   文件数 %d' % len(os.listdir(bk)))

open(r'D:\Programming project\插件汉化\_work\_preinstall.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('done')

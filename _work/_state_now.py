# -*- coding: utf-8 -*-
import os, glob, hashlib

out = []
def say(s):
    out.append(str(s))

say('--- stage dirs ---')
for p in glob.glob(r'C:\Users\Jinna\.workbuddy\pyinstaller_stage*'):
    say('%s  isdir=%s' % (p, os.path.isdir(p)))

d = r'D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0'
fs = sorted(os.listdir(d))
aex = [f for f in fs if f.lower().endswith('.aex')]
dll = [f for f in fs if f.lower().endswith('.dll')]
say('--- delivery dir: total %d  aex %d  dll %d' % (len(fs), len(aex), len(dll)))
for f in fs:
    if not f.lower().endswith('.aex'):
        say('   %-40s %d' % (f, os.path.getsize(os.path.join(d, f))))

say('--- delivery DLL sha256 ---')
for f in dll:
    h = hashlib.sha256(open(os.path.join(d, f), 'rb').read()).hexdigest()
    say('   %-34s %s' % (f, h[:32]))

pd = r'D:\Programming project\插件汉化\_work\patched_dll_d'
say('--- patched_dll_d sha256 ---')
if os.path.isdir(pd):
    for f in sorted(os.listdir(pd)):
        if f.lower().endswith('.dll'):
            h = hashlib.sha256(open(os.path.join(pd, f), 'rb').read()).hexdigest()
            say('   %-34s %s' % (f, h[:32]))

open(r'D:\Programming project\插件汉化\_work\_state_now.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('done')

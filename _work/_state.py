import os, sys, hashlib

out = open(r'D:\Programming project\插件汉化\_work\_state.txt', 'w', encoding='utf-8')
def p(*a): out.write(' '.join(str(x) for x in a) + '\n')

DELIV = r'D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0'
SYS = r'C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum'

def emen(d):
    j = d.find(b'MIB8eman')
    if j < 0: return None
    base = j - 4
    size = int.from_bytes(d[base+12:base+16], 'little')
    val = base + 16
    return d[val+1:val+size].split(b'\x00')[0]

def find_all(base, ext):
    res = {}
    for dp, dn, fn in os.walk(base):
        for f in fn:
            if f.lower().endswith(ext):
                res[f] = os.path.join(dp, f)
    return res

daex = find_all(DELIV, '.aex')
p('交付 aex:', len(daex))
ddll = find_all(DELIV, '.dll')
p('交付 dll:', len(ddll), sorted(ddll)[:8])

sysaex = find_all(SYS, '.aex')
p('系统 dir aex:', len(sysaex))

same = diff = miss = 0
still_en = []
for name in sorted(daex):
    sp = os.path.join(SYS, name)
    if not os.path.exists(sp):
        miss += 1; continue
    a = open(sp, 'rb').read(); b = open(daex[name], 'rb').read()
    if a == b: same += 1
    else:
        diff += 1
        if len(still_en) < 6:
            still_en.append((name, emen(a), emen(b)))
p('---- aex: 一致', same, ' 不同', diff, ' 缺失', miss)

# DLL
sysdll = find_all(SYS, '.dll')
p('系统 dir dll:', len(sysdll))
dsame = ddiff = dmiss = 0
dllist = []
for name, dp in sorted(ddll.items()):
    if name in sysdll:
        sp = sysdll[name]
    else:
        sp = os.path.join(SYS, name)
    if not os.path.exists(sp):
        dmiss += 1; dllist.append((name, 'MISSING')); continue
    if open(sp,'rb').read() == open(dp,'rb').read():
        dsame += 1; dllist.append((name, 'SAME'))
    else:
        ddiff += 1; dllist.append((name, 'DIFF'))
p('---- dll: 一致', dsame, ' 不同', ddiff, ' 缺失', dmiss)
for n, s in dllist:
    p('   ', s, n)
p('==== TOTAL_DIFF:', diff + ddiff, '(应为 0)')

p('---- 系统效果名目检 ----')
for n in ['BCCBlur.aex','BCC3WayColorGrade.aex','BCCLevelsGamma.aex','BCCChromaKey.aex','BCCCube.aex','BCCWarp.aex','BCCTrails.aex']:
    sp = os.path.join(SYS, n)
    if os.path.exists(sp):
        raw = emen(open(sp,'rb').read())
        try: s = raw.decode('utf-8')
        except Exception: s = '!!非法UTF8 ' + repr(raw)
        p(' ', n, '->', s)
    else:
        p(' ', n, '-> 系统不存在')

out.close()
print('done')

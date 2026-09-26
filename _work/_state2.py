import os, sys

out = open(r'D:\Programming project\插件汉化\_work\_state2.txt', 'w', encoding='utf-8')
def p(*a): out.write(' '.join(str(x) for x in a) + '\n')

SYS = r'C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum'
LIB = r'C:\Program Files\BorisFX\ContinuumAE\19\lib'
DELIV = r'D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0'

def rec(d, key):
    """MIB8 | key(4B) | pad(4B) | size(u32) | value ; 返回 (base,size,val)"""
    kb = key.encode() if isinstance(key, str) else key
    i = 0
    while True:
        j = d.find(b'MIB8' + kb, i)
        if j < 0: return None
        size = int.from_bytes(d[j+12:j+16], 'little')
        if 0 < size < 4096:
            return (j, size, j+16)
        i = j + 4

def txt(d, key):
    r = rec(d, key)
    if not r: return None
    base, size, val = r
    return d[val+1:val+size].split(b'\x00')[0]

def show(raw):
    if raw is None: return '<无记录>'
    try: return repr(raw.decode('utf-8'))
    except Exception: return '非法UTF8 ' + repr(raw)

# A. 系统 aex 目检
p('== 系统 aex 效果名/类型栏目检 ==')
for n in ['BCCBlur.aex','BCC3WayColorGrade.aex','BCCChromaKey.aex','BCCCube.aex','BCCTrails.aex']:
    sp = os.path.join(SYS, n)
    if not os.path.exists(sp):
        p(' ', n, '系统不存在'); continue
    d = open(sp,'rb').read()
    p(' ', n, 'eman=', show(txt(d,'eman')), ' gtac=', show(txt(d,'gtac')))

p('== 交付 aex 目检 ==')
for n in ['BCCBlur.aex','BCC3WayColorGrade.aex','BCCChromaKey.aex','BCCCube.aex','BCCTrails.aex']:
    sp = os.path.join(DELIV, n)
    if not os.path.exists(sp):
        p(' ', n, '交付不存在'); continue
    d = open(sp,'rb').read()
    p(' ', n, 'eman=', show(txt(d,'eman')), ' gtac=', show(txt(d,'gtac')))

# B. lib DLL 对比
p('== lib DLL 状态 ==')
need = ['BCCPlus.dll','Continuum_3DObjects_AE.dll','Continuum_AE_16Bit.dll',
        'Continuum_AE_8Bit.dll','Continuum_AE_Float.dll','Continuum_Common_AE.dll']
for n in need:
    sp = os.path.join(LIB, n)
    dp = os.path.join(DELIV, n)
    if not os.path.exists(dp):
        # 交付里可能在子目录
        cand = None
        for dd, dn2, fn2 in os.walk(DELIV):
            if n in fn2: cand = os.path.join(dd, n); break
        dp = cand
    if not os.path.exists(sp):
        p(' ', n, '系统不存在 (lib)'); continue
    if dp is None or not os.path.exists(dp):
        p(' ', n, '交付不存在'); continue
    a = open(sp,'rb').read(); b = open(dp,'rb').read()
    same = (a == b)
    dc = sum(1 for i in range(min(len(a),len(b))) if a[i] != b[i])
    p(' ', n, '一致' if same else '不同', 'sys', len(a), 'deliv', len(b), 'diffbytes', dc)

# C. BCCPlus.dll 在 MediaCore
p('== BCCPlus.dll (MediaCore) ==')
sp = os.path.join(SYS, 'BCCPlus.dll'); dp = os.path.join(DELIV, 'BCCPlus.dll')
if os.path.exists(sp) and os.path.exists(dp):
    a = open(sp,'rb').read(); b = open(dp,'rb').read()
    dc = sum(1 for i in range(min(len(a),len(b))) if a[i] != b[i])
    p('  一致' if a==b else '  不同', 'sys', len(a), 'deliv', len(b), 'diffbytes', dc)

out.close()
print('done')

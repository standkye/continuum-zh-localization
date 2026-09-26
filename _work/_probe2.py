import os, sys

out = open(r'D:\Programming project\插件汉化\_work\_probe2.txt', 'w', encoding='utf-8')
def p(*a): out.write(' '.join(str(x) for x in a) + '\n')

SYS = r'C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum'
DELIV = r'D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0'

# A. 系统目录里的 dll 清单
p('== 系统目录 DLL ==')
for f in sorted(os.listdir(SYS)):
    if f.lower().endswith('.dll'):
        p('  ', f, os.path.getsize(os.path.join(SYS, f)))

# B. 找 Continuum_AE_8Bit.dll 全盘（限定几个根）
need = ['Continuum_AE_8Bit.dll','Continuum_AE_16Bit.dll','Continuum_AE_Float.dll',
        'Continuum_Common_AE.dll','Continuum_3DObjects_AE.dll']
roots = [r'C:\Program Files\BorisFX', r'C:\Program Files\Adobe',
         r'C:\Program Files\Common Files\BorisFX', r'C:\Program Files (x86)\BorisFX']
p('== 定位 Continuum_*.dll ==')
seen = set()
for r in roots:
    if not os.path.isdir(r):
        p('  根不存在:', r); continue
    for dp, dn, fn in os.walk(r):
        for f in fn:
            if f in need:
                fp = os.path.join(dp, f)
                if fp in seen: continue
                seen.add(fp)
                p('  ', fp, os.path.getsize(fp))
missing = [n for n in need if n not in {os.path.basename(x) for x in seen}]
p('  未找到:', missing)

# C. 系统 BCCBlur.aex 的 eman 记录原始字节
sp = os.path.join(SYS, 'BCCBlur.aex')
d = open(sp, 'rb').read()
p('== 系统 BCCBlur.aex eman 原始 ==')
j = d.find(b'MIB8eman')
p('  MIB8eman @', j, ' 文件大小', len(d))
if j >= 0:
    base = j - 4
    p('  base', base, ' hdr', d[base:base+16].hex())
    size = int.from_bytes(d[base+12:base+16],'little')
    val = base + 16
    p('  size', size, 'val', val)
    p('  raw[val:val+size] =', d[val:val+size])
    p('  前 80 字节:', d[base:base+80])

# D. 对比交付
dd = os.path.join(DELIV, 'BCCBlur.aex')
b = open(dd,'rb').read()
j2 = b.find(b'MIB8eman')
p('== 交付 BCCBlur.aex eman 原始 ==')
if j2 >= 0:
    base2 = j2-4
    size2 = int.from_bytes(b[base2+12:base2+16],'little')
    val2 = base2+16
    p('  size', size2, ' raw =', b[val2:val2+size2])

# E. 系统 vs 交付 有多大差异？
p('== BCCBlur.aex 差异字节数 ==')
n = min(len(d), len(b))
diffcnt = sum(1 for i in range(n) if d[i] != b[i])
p('  长度 sys', len(d), ' deliv', len(b), ' 不同字节', diffcnt)

out.close()
print('done')

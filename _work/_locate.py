import os, sys

out = open(r'D:\Programming project\插件汉化\_work\_locate.txt', 'w', encoding='utf-8')
def p(*a): out.write(' '.join(str(x) for x in a) + '\n')

# 1. 全盘（限定 Adobe 相关）找 BCCBlur.aex
targets = set()
searches = [
    r'C:\Program Files\Adobe',
    r'C:\Program Files\BorisFX',
    r'C:\Program Files\Common Files\Adobe',
]
found = []
for root in searches:
    if not os.path.isdir(root):
        p('不存在:', root); continue
    for dp, dn, fn in os.walk(root):
        for f in fn:
            if f == 'BCCBlur.aex' or f == 'BCCFilters.dll':
                found.append(os.path.join(dp, f))
p('== 定位结果 ==')
for f in found:
    p(' ', f, os.path.getsize(f))

# 2. 列出 MediaCore 下的子目录
mc = r'C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore'
if os.path.isdir(mc):
    p('== MediaCore 子项 ==')
    for e in sorted(os.listdir(mc))[:60]:
        p(' ', e)

# 3. 交付目录结构
DELIV = r'D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0'
p('== 交付目录顶层 ==')
for e in sorted(os.listdir(DELIV))[:60]:
    fp = os.path.join(DELIV, e)
    p('  ', '[D]' if os.path.isdir(fp) else '[F]', e, os.path.getsize(fp) if os.path.isfile(fp) else '')

out.close()
print('done')

import os

out = open(r'D:\Programming project\插件汉化\_work\_list.txt', 'w', encoding='utf-8')
def p(*a): out.write(' '.join(str(x) for x in a) + '\n')

D = r'D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0'
p('== 交付目录 非 aex/dll 文件 ==')
for f in sorted(os.listdir(D)):
    fp = os.path.join(D, f)
    if os.path.isdir(fp):
        p('  [D]', f)
        for g in sorted(os.listdir(fp))[:40]:
            p('       ', g, os.path.getsize(os.path.join(fp, g)))
    elif not (f.lower().endswith('.aex') or f.lower().endswith('.dll')):
        p('  [F]', f, os.path.getsize(fp))

p('')
p('== _work 脚本 ==')
W = r'D:\Programming project\插件汉化\_work'
if os.path.isdir(W):
    for f in sorted(os.listdir(W)):
        fp = os.path.join(W, f)
        if os.path.isfile(fp):
            p('  ', f, os.path.getsize(fp))

out.close()
print('done')

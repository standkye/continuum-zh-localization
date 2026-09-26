import ctypes, os, sys, tempfile

out = open(r'D:\Programming project\插件汉化\_work\_admintest.txt', 'w', encoding='utf-8')
def p(*a): out.write(' '.join(str(x) for x in a) + '\n')

try:
    admin = bool(ctypes.windll.shell32.IsUserAnAdmin())
except Exception as e:
    admin = 'ERR ' + str(e)
p('IsUserAnAdmin:', admin)

# 实测能否写 Program Files
test = r'C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum\_wb_write_test.tmp'
try:
    with open(test, 'w') as f:
        f.write('x')
    p('写入 Program Files: 成功')
    os.remove(test)
    p('删除测试文件: 成功')
except Exception as e:
    p('写入 Program Files: 失败 ->', type(e).__name__, e)

test2 = r'C:\Program Files\BorisFX\ContinuumAE\19\lib\_wb_write_test.tmp'
try:
    with open(test2, 'w') as f:
        f.write('x')
    p('写入 BorisFX lib: 成功')
    os.remove(test2)
except Exception as e:
    p('写入 BorisFX lib: 失败 ->', type(e).__name__, e)

# integrity level
try:
    import subprocess
    r = subprocess.run(['whoami', '/groups'], capture_output=True)
    s = r.stdout.decode('gbk', errors='replace')
    for line in s.splitlines():
        if 'Mandatory' in line or 'Integrity' in line or 'administrat' in line.lower():
            p('GROUP:', line.strip()[:110])
except Exception as e:
    p('whoami err', e)

out.close()
print('done')

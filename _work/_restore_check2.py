# -*- coding: utf-8 -*-
"""全量核对：把 git ls-files 的八进制转义路径正确解码后再比对"""
import os, hashlib, subprocess, re

SRC = r'D:\Programming project\插件汉化'
DST = os.path.join(SRC, '_work', '_restore_test')

def h(p):
    m = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            m.update(b)
    return m.hexdigest()

def unquote(s):
    """git 会把非 ASCII 路径输出成 "\\\\346\\\\261\\\\211..." 的八进制转义形式。
       那些数字是 UTF-8 的**字节**，必须先拼成 bytes 再 decode，
       不能直接 chr() —— 否则得到的是 latin-1 乱码，拼出来的路径根本不存在。"""
    if s.startswith('"') and s.endswith('"'):
        body = s[1:-1]
        out = bytearray()
        i = 0
        while i < len(body):
            if body[i] == '\\' and i + 3 < len(body) and body[i + 1:i + 4].isdigit():
                out.append(int(body[i + 1:i + 4], 8))
                i += 4
            elif body[i] == '\\' and i + 1 < len(body):
                out.extend(body[i + 1].encode('utf-8'))
                i += 2
            else:
                out.extend(body[i].encode('utf-8'))
                i += 1
        return out.decode('utf-8')
    return s

r = subprocess.run(['git', 'ls-files'], cwd=SRC, capture_output=True)
raw = r.stdout.decode('utf-8', 'replace').split('\n')
tracked = [unquote(l.strip()) for l in raw if l.strip()]
print('仓库跟踪文件数:', len(tracked))

bad, missing, checked = [], [], 0
for rel in tracked:
    a = os.path.join(SRC, rel)
    b = os.path.join(DST, rel)
    if not os.path.exists(a):
        missing.append('SRC? ' + rel); continue
    if not os.path.exists(b):
        missing.append('DST? ' + rel); continue
    if h(a) != h(b):
        bad.append(rel)
    checked += 1

print('已比对: %d / %d' % (checked, len(tracked)))
print('缺失  : %d' % len(missing))
for x in missing[:10]: print('   -', x)
print('不一致: %d' % len(bad))
for x in bad[:10]: print('   -', x)
print()
print('==> ✅ 全部一致：这份仓库可以完整还原' if not bad and not missing
      else '==> ❌ 有问题')

tot = 0
for dp, dn, fn in os.walk(DST):
    for f in fn:
        tot += os.path.getsize(os.path.join(dp, f))
print('克隆体积: %.1f MB' % (tot / 1048576.0))

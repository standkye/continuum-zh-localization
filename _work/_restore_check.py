# -*- coding: utf-8 -*-
"""核对：从本仓库克隆出来的文件 是否与原项目逐文件一致"""
import os, hashlib

SRC = r'D:\Programming project\插件汉化'
DST = os.path.join(SRC, '_work', '_restore_test')
skip_dirs = {'.git', '_restore_test', 'patched_dll', 'patched_dll_b', 'patched_dll_c',
             'patched_dll_d', 'patched_aex', 'patched_aex_b', '.workbuddy', '__pycache__'}
# 源 <-> 目标 名字映射时的额外跳过：mysqld none

def rel_files(root, base):
    out = []
    for dp, dn, fn in os.walk(base):
        dn[:] = [d for d in dn if d not in skip_dirs]
        for f in fn:
            p = os.path.join(dp, f)
            out.append(os.path.relpath(p, base))
    return out

# git 已跟踪的路径才是「能恢复」的；直接用源目录里的同名文件比对
import subprocess
r = subprocess.run(['git', 'ls-files'], cwd=SRC, capture_output=True)
tracked = [l for l in r.stdout.decode('utf-8', 'replace').split('\n') if l.strip()]
print('仓库跟踪文件数:', len(tracked))

def h(p):
    m = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            m.update(b)
    return m.hexdigest()

bad = []
missing = []
checked = 0
for rel in tracked:
    rel = rel.strip('"')
    try:
        rel = rel.encode('latin-1').decode('utf-8') if rel.startswith('\\') else rel
    except Exception:
        pass
    a = os.path.join(SRC, rel)
    b = os.path.join(DST, rel)
    if not os.path.exists(a):
        continue
    if not os.path.exists(b):
        missing.append(rel); continue
    try:
        if h(a) != h(b):
            bad.append(rel)
    except OSError as e:
        bad.append(rel + '  <读不了: %s>' % e)
    checked += 1

print('已比对: %d 个文件' % checked)
print('缺失  : %d' % len(missing))
for x in missing[:10]: print('   -', x)
print('不一致: %d' % len(bad))
for x in bad[:10]: print('   -', x)
print()
if not bad and not missing:
    print('==> ✅ 全部一致：克隆出来的东西可以原样用')
else:
    print('==> ❌ 有问题，不能直接依赖这份备份')

# LFS 是否正确 smudge 成真文件
for dll in ['BCCPlus.dll', 'Continuum_AE_8Bit.dll']:
    p = os.path.join(DST, 'Continuum 汉化组件 v19.0.0', dll)
    if os.path.exists(p):
        head = open(p, 'rb').read(2)
        print('  %-24s %8.1f MB  开头=%r  %s' %
              (dll, os.path.getsize(p) / 1048576.0, head,
               '真DLL' if head == b'MZ' else '**LFS指针，不能加载**'))

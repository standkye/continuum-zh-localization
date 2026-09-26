# -*- coding: utf-8 -*-
"""验证：git 里存的字节 == 磁盘上的字节（字节级补丁项目的生命线）"""
import os, subprocess, hashlib, sys

ROOT = r'D:\Programming project\插件汉化'
os.chdir(ROOT)

def git(args, binary=False):
    r = subprocess.run(['git'] + args, capture_output=True)
    return (r.stdout if binary else r.stdout.decode('utf-8', 'replace')), r.stderr, r.returncode

# 挑几类代表性文件：LFS 管理的 DLL、很可能是二进制混杂的 dump txt、普通脚本、UTF-8 文档
targets = [
    r'Continuum 汉化组件 v19.0.0\BCCPlus.dll',
    r'Continuum 汉化组件 v19.0.0\Continuum_AE_8Bit.dll',
    r'Continuum 汉化组件 v19.0.0\Continuum汉化安装器.exe',
    r'_work\_resid_run_d.txt',
    r'_work\_fix4_writes.json',
    r'_work\fix4_dll.py',
    r'_work\batch10_miss.json',
    r'Continuum 汉化组件 v19.0.0\说明.txt',
    r'Continuum 汉化组件 v19.0.0\BCCBlur.aex',
]

print('%-52s %-10s %-10s %s' % ('file', 'HEAD blob', 'disk', 'match'))
ok = 0
for t in targets:
    spec = 'HEAD:' + t.replace('\\', '/')
    out, err, rc = git(['cat-file', 'blob', spec], binary=True)
    if rc != 0:
        print('%-52s  读取失败 %s' % (t[:52], err.decode('utf-8', 'replace').strip()[:40]))
        continue
    h_git = hashlib.sha256(out).hexdigest()[:8]
    try:
        h_disk = hashlib.sha256(open(os.path.join(ROOT, t), 'rb').read()).hexdigest()[:8]
    except OSError as e:
        print('%-52s  磁盘读取失败 %s' % (t[:52], e)); continue
    good = (h_git == h_disk)
    ok += good
    print('%-52s %-10s %-10s %s   (%d bytes)' % (t[:52], h_git, h_disk, 'OK' if good else '**MISMATCH**', len(out)))

print()
print('字节一致: %d / %d' % (ok, len(targets)))

# LFS 指针检查：DLL 在工作区应是完整文件而非指针
p = os.path.join(ROOT, r'Continuum 汉化组件 v19.0.0\BCCPlus.dll')
head = open(p, 'rb').read(60)
print('BCCPlus.dll 开头 8 字节:', head[:8])
print('  -> 是完整 PE 文件(非 LFS 指针):', head[:2] == b'MZ')

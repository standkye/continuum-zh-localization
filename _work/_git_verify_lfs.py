# -*- coding: utf-8 -*-
"""验证 LFS 文件内容完整性：
   指针里的 oid -> .git/lfs/objects 里的真实文件 -> 与磁盘文件 sha256 比对
"""
import os, subprocess, hashlib, json

ROOT = r'D:\Programming project\插件汉化'
os.chdir(ROOT)

def git(args):
    r = subprocess.run(['git'] + args, capture_output=True)
    return r.stdout, r.returncode

targets = [
    r'Continuum 汉化组件 v19.0.0\BCCPlus.dll',
    r'Continuum 汉化组件 v19.0.0\Continuum_AE_8Bit.dll',
    r'Continuum 汉化组件 v19.0.0\Continuum_AE_16Bit.dll',
    r'Continuum 汉化组件 v19.0.0\Continuum_AE_Float.dll',
    r'Continuum 汉化组件 v19.0.0\Continuum_Common_AE.dll',
    r'Continuum 汉化组件 v19.0.0\Continuum_3DObjects_AE.dll',
    r'Continuum 汉化组件 v19.0.0\Continuum汉化安装器.exe',
]

LFSOBJ = os.path.join(ROOT, '.git', 'lfs', 'objects')
print('%-46s %-10s %-10s %-10s %s' % ('file', '指针oid', 'LFS对象', '磁盘', '结论'))
allok = 0
for t in targets:
    spec = 'HEAD:' + t.replace('\\', '/')
    out, rc = git(['cat-file', 'blob', spec])
    if rc != 0:
        print('%-46s 读取失败' % t[:46]); continue
    txt = out.decode('utf-8', 'replace')
    oid = size = None
    for line in txt.split('\n'):
        if line.startswith('oid sha256:'):
            oid = line.split(':', 1)[1].strip()
        if line.startswith('size '):
            size = int(line.split()[1])
    if not oid:
        print('%-46s 不是 LFS 指针！（属性没生效）' % t[:46]); continue
    obj = os.path.join(LFSOBJ, oid[0:2], oid[2:4], oid)
    h_obj = hashlib.sha256(open(obj, 'rb').read()).hexdigest() if os.path.exists(obj) else 'MISSING'
    disk = os.path.join(ROOT, t)
    h_disk = hashlib.sha256(open(disk, 'rb').read()).hexdigest()
    good = (h_obj == h_disk == oid)
    allok += good
    print('%-46s %-10s %-10s %-10s %s  size=%d' %
          (os.path.basename(t)[:46], oid[:8], h_obj[:8], h_disk[:8],
           'OK' if good else '**BAD**', size))

print()
print('LFS 内容完整: %d / %d' % (allok, len(targets)))
tot = sum(os.path.getsize(os.path.join(LFSOBJ, dp, f))
          for dp, dn, fn in os.walk(LFSOBJ) for f in fn)
print('.git/lfs/objects 占用: %.1f MB' % (tot / 1048576.0))

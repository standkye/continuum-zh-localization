# -*- coding: utf-8 -*-
"""★ 装机版最终验收：对系统里实际文件做结构复算 + 真实 LoadLibrary 测试"""
import os, struct, json, hashlib, subprocess
from collections import Counter

WORK = r"D:\Programming project\插件汉化\_work"
DELIV = r"D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0"
TMP = r"C:\Users\Jinna\.workbuddy\dlldbg"
os.makedirs(TMP, exist_ok=True)
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
BK_AEX = os.path.join(BK, 'aex')
LIB = r"C:\Program Files\BorisFX\ContinuumAE\19\lib"
CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"
PY = r'C:\Users\Jinna\.workbuddy\binaries\python\versions\3.13.12\python.exe'

out = []
def p(s=''):
    out.append(str(s))
    print(s, flush=True)

def sha(fp):
    h = hashlib.sha256()
    with open(fp, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()

def pe_sections(d):
    pe = struct.unpack_from('<I', d, 0x3C)[0]
    nsec = struct.unpack_from('<H', d, pe + 6)[0]
    optsz = struct.unpack_from('<H', d, pe + 20)[0]
    secs = []
    for i in range(nsec):
        s = pe + 24 + optsz + i * 40
        nm = d[s:s + 8].rstrip(b'\x00').decode('ascii', 'replace')
        vsz, va, rsz, ra = struct.unpack_from('<IIII', d, s + 8)
        secs.append((nm, ra, ra + rsz))
    return secs

def find_records(d, key):
    res = []
    i = 0
    while True:
        j = d.find(key, i)
        if j < 0:
            break
        if d[j - 4:j] == b'MIB8':
            base = j - 4
            size = struct.unpack_from('<I', d, base + 12)[0]
            if 0 < size < 4096:
                res.append((base, size, base + 16))
        i = j + 4
    return res

p('=' * 78)
p('★ 装机版最终验收   ' + __import__('time').strftime('%Y-%m-%d %H:%M:%S'))
p('=' * 78)

# ---------- 0) 装机 vs 交付目录 ----------
p()
p('--- 0) 装机 vs 交付目录 ---')
d = t = 0
for f in sorted(os.listdir(DELIV)):
    if f.lower().endswith('.aex'):
        tgt = os.path.join(CONT, f)
    elif f.lower().endswith('.dll') and f in (
            'Continuum_AE_Float.dll', 'Continuum_AE_8Bit.dll', 'Continuum_AE_16Bit.dll',
            'Continuum_Common_AE.dll', 'Continuum_3DObjects_AE.dll', 'BCCPlus.dll'):
        tgt = os.path.join(CONT if f == 'BCCPlus.dll' else LIB, f)
    else:
        continue
    t += 1
    if not os.path.exists(tgt) or sha(os.path.join(DELIV, f)) != sha(tgt):
        d += 1
p('  TOTAL_DIFF = %d / %d' % (d, t))

# ---------- 1) aex ----------
p()
p('--- 1) .aex（%d 个）---' % len([f for f in os.listdir(BK_AEX) if f.lower().endswith('.aex')]))
files = sorted(f for f in os.listdir(BK_AEX) if f.lower().endswith('.aex'))
bad_len = out_of = bad_enc = 0
nname = ncat = 0
secs = Counter()
ascii_name = []
for fn in files:
    a = open(os.path.join(BK_AEX, fn), 'rb').read()
    fp = os.path.join(CONT, fn)
    b = open(fp, 'rb').read()
    if len(a) != len(b):
        bad_len += 1; continue
    tg = set()
    for key in (b'eman', b'gtac'):
        for (base, size, val) in find_records(a, key):
            tg.update(range(val, val + size))
    for i in range(len(a)):
        if a[i] != b[i]:
            if i not in tg:
                out_of += 1
            for nm, lo, hi in pe_sections(a):
                if lo <= i < hi:
                    secs[nm] += 1; break
    for key, isname in ((b'eman', True), (b'gtac', False)):
        for (base, size, val) in find_records(b, key):
            frag = b[val + 1:val + size].split(b'\x00')[0]
            if not frag: continue
            try:
                frag.decode('gbk')
            except UnicodeDecodeError:
                bad_enc += 1
            if max(frag) > 127:
                if isname: nname += 1
                else: ncat += 1
            elif isname:
                ascii_name.append((fn, frag.decode('ascii', 'replace')))
p('  长度不一致 %d   改动落在 eman/gtac 外 %d   非法 GBK %d' % (bad_len, out_of, bad_enc))
p('  改动所在节 %s' % dict(secs))
p('  效果名中文化 %d / %d' % (nname, len(files)))
p('  类型栏中文化 %d / 488' % ncat)
p('  效果名仍纯 ASCII %d' % len(ascii_name))
for fn, s in ascii_name[:8]:
    p('      - %-32s %s' % (fn, s))

# ---------- 2) dll 结构 ----------
p()
p('--- 2) DLL 结构复算 ---')
chains = json.load(open(os.path.join(WORK, 'dll_chains.json'), encoding='utf-8'))
for name in sorted(chains):
    a = open(os.path.join(BK, name), 'rb').read()
    dp = os.path.join(CONT if name == 'BCCPlus.dll' else LIB, name)
    b = open(dp, 'rb').read()
    tg = set()
    for off_s, arr in chains[name].items():
        cur = int(off_s)
        for s in arr:
            slot = max(8, ((len(s) + 1 + 7) // 8) * 8)
            tg.update(range(cur, cur + slot)); cur += slot
    ch = outs = 0
    for i in range(len(a)):
        if a[i] != b[i]:
            ch += 1
            if i not in tg: outs += 1
    hits = Counter()
    for i in range(len(a)):
        if a[i] != b[i]:
            tag = '<header>'
            for nm, lo, hi in pe_sections(a):
                if lo <= i < hi:
                    tag = nm; break
            hits[tag] += 1
    p('  %-30s 长度=%s  改动 %5d  链外 %d  节 %s'
      % (name, '同' if len(a) == len(b) else '**不同**', ch, outs, dict(hits)))

# ---------- 3) 关键内部键必须仍是英文 ----------
p()
p('--- 3) 内部键保留检查（必须全 True）---')
for name in ('Continuum_AE_8Bit.dll', 'Continuum_AE_Float.dll', 'Continuum_3DObjects_AE.dll'):
    fp = os.path.join(LIB, name)
    dd = open(fp, 'rb').read()
    p('  %-30s Resources=%s  Documentation=%s'
      % (name, b'Resources\x00' in dd, b'Documentation\x00' in dd))

# ---------- 4) ★ 真实 LoadLibrary ----------
p()
p('--- 4) ★ 装机的 6 支 DLL 实际加载测试 ---')
TESTPY = os.path.join(TMP, '_final.py')
open(TESTPY, 'w', encoding='utf-8').write('''
import ctypes, sys, os
p = sys.argv[1]
try:
    ctypes.WinDLL(p, winmode=0)
    print("OK")
except OSError as e:
    print("FAIL winerror=%s %s" % (getattr(e, "winerror", None), e))
except Exception as e:
    print("FAIL other %s" % e)
''')
env = os.environ.copy()
env['PATH'] = LIB + os.pathsep + CONT + os.pathsep + env.get('PATH', '')
allok = True
for name in ('Continuum_AE_Float.dll', 'Continuum_AE_8Bit.dll', 'Continuum_AE_16Bit.dll',
             'Continuum_Common_AE.dll', 'Continuum_3DObjects_AE.dll', 'BCCPlus.dll'):
    fp = os.path.join(CONT if name == 'BCCPlus.dll' else LIB, name)
    r = subprocess.run([PY, TESTPY, fp], capture_output=True, env=env)
    o = (r.stdout + r.stderr).decode('utf-8', 'replace').strip()
    if not o.startswith('OK'):
        allok = False
    p('  %-30s %s' % (name, o[:70]))
p()
p('  => %s' % ('★ 6/6 全部可加载 —— 引擎这次真的能起来了' if allok else '!! 仍有加载失败'))

open(os.path.join(WORK, '_final_accept_installed.txt'), 'w', encoding='utf-8').write('\n'.join(out))

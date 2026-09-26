# -*- coding: utf-8 -*-
"""乱码诊断：读 AE 日志 + BCC 引擎日志，判断插件到底加载到哪一步"""
import os, time, io

OUT = r"D:\Programming project\插件汉化\_work\_glyph_diag.txt"
lines = []
def p(s=''):
    lines.append(str(s))

AE_LOG = r"C:\Users\Jinna\AppData\Roaming\Adobe\After Effects\25.1\Plugin Loading.log"
BCC_LOG = r"C:\Users\Jinna\AppData\Local\BorisFX\Continuum\BCC.log"
PREF = r"C:\Users\Jinna\AppData\Roaming\Adobe\After Effects\25.1"

def tail(path, n=40, enc='utf-8', err='replace'):
    if not os.path.exists(path):
        return None, None, None
    st = os.stat(path)
    with open(path, 'rb') as f:
        data = f.read()
    txt = data.decode(enc, errors=err)
    return st, txt.splitlines()[-n:], txt

p('=' * 74)
p('乱码诊断  ' + time.strftime('%Y-%m-%d %H:%M:%S'))
p('=' * 74)

# ---------- 1) AE Plugin Loading.log ----------
p()
p('--- 1) AE Plugin Loading.log ---')
st, tl, full = tail(AE_LOG, 60)
if st is None:
    p('  不存在: ' + AE_LOG)
else:
    p('  mtime : %s   size=%d' % (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(st.st_mtime)), st.st_size))
    p('  最后 60 行:')
    for l in tl:
        p('    ' + l)

# ---------- 2) BCC.log ----------
p()
p('--- 2) BorisFX BCC.log（引擎是否被拉起）---')
st2, tl2, _ = tail(BCC_LOG, 30)
if st2 is None:
    p('  不存在: ' + BCC_LOG)
else:
    p('  mtime : %s   size=%d' % (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(st2.st_mtime)), st2.st_size))
    p('  最后 30 行:')
    for l in tl2:
        p('    ' + l)

# ---------- 3) 关键：日志里 Continuum 的加载结果 ----------
p()
p('--- 3) Plugin Loading.log 里 Continuum 相关统计 ---')
if full:
    cnt_load = cnt_ignore = cnt_noloader = 0
    cont_lines = []
    for l in full.splitlines():
        if 'Continuum' in l or 'BorisFX' in l:
            cont_lines.append(l)
    p('  含 Continuum/BorisFX 的行数: %d' % len(cont_lines))
    import re
    c_load = sum(1 for l in full.splitlines() if 'Continuum' in l and 'added' in l)
    c_ign = sum(1 for l in full.splitlines() if 'Continuum' in l and 'Ignore' in l)
    p('  ...added(被识别): %d' % c_load)
    p('  ...Ignore(被忽略): %d' % c_ign)
    p('  最后 25 行 Continuum 相关:')
    for l in cont_lines[-25:]:
        p('    ' + l)

# ---------- 4) AE 版本与语言设置 ----------
p()
p('--- 4) AE 语言/编码相关配置 ---')
for rel in ('AMT/application.xml',):
    fp = os.path.join(r'D:\APP\DesignMedia\Adobe\Ae\Adobe After Effects 2025', rel)
    if os.path.exists(fp):
        t = open(fp, 'r', encoding='utf-8', errors='replace').read()
        import re
        m = re.search(r'installedLanguages\s*=\s*"([^"]*)"', t)
        p('  installedLanguages = %s' % (m.group(1) if m else '?'))
if os.path.isdir(PREF):
    fs = sorted(os.listdir(PREF))
    p('  25.1 首选项目录条目数: %d' % len(fs))
    for f in fs:
        if 'cache' in f.lower() or 'plugin' in f.lower():
            fp = os.path.join(PREF, f)
            p('    - %-40s %s' % (f, time.strftime('%Y-%m-%d %H:%M', time.localtime(os.path.getmtime(fp)))))

# ---------- 5) 当前装机版本复核 ----------
p()
p('--- 5) 当前装机文件（确认是不是 UTF-8 版）---')
CONT = r'C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum'
LIB = r'C:\Program Files\BorisFX\ContinuumAE\19\lib'
for f, d in (('BCCBlur.aex', CONT), ('Continuum_AE_8Bit.dll', LIB)):
    fp = os.path.join(d, f)
    if os.path.exists(fp):
        st3 = os.stat(fp)
        p('  %-26s mtime=%s size=%d' % (f, time.strftime('%Y-%m-%d %H:%M', time.localtime(st3.st_mtime)), st3.st_size))
d = open(os.path.join(CONT, 'BCCBlur.aex'), 'rb').read()
j = d.find(b'MIB8eman')
seg = d[j + 16:j + 40]
p('  BCCBlur eman 原始字节: %r' % seg)
txt = seg.split(b'\x00')[0]
# 第 1 字节是长度
n = txt[0]
body = txt[1:1 + n]
p('  -> L=%d  body=%r' % (n, body))
try:
    p('  -> 按 UTF-8 解释: %r' % body.decode('utf-8'))
except Exception as e:
    p('  -> 按 UTF-8 解释: 失败 %s' % e)
try:
    p('  -> 按 GBK  解释: %r' % body.decode('gbk'))
except Exception as e:
    p('  -> 按 GBK  解释: 失败 %s' % e)

open(OUT, 'w', encoding='utf-8').write('\n'.join(lines))
print('done')

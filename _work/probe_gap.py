# -*- coding: utf-8 -*-
"""漏翻定位 probe：
   1) 列目录结构 + dll_chains.json 结构
   2) 对一批"词典缺译文"的名字，在装机 DLL / .aex 里找 **独立 NUL 记号** 出现
   3) 统计：有多少是独立记号（可安全改），多少是长串子串（不可改）
"""
import os, json, re

WORK = r"D:\Programming project\插件汉化\_work"
LIB = r"C:\Program Files\BorisFX\ContinuumAE\19\lib"
CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"

out = []
def p(s=''):
    out.append(str(s))
    print(s, flush=True)

# ---------- 1) 目录结构 ----------
for d in (LIB, CONT, BK):
    p('=' * 88)
    p('DIR ' + d)
    p('=' * 88)
    if not os.path.isdir(d):
        p('  不存在'); continue
    cnt = {}
    items = []
    for f in sorted(os.listdir(d)):
        fp = os.path.join(d, f)
        if os.path.isfile(fp):
            ext = os.path.splitext(f)[1].lower()
            cnt[ext] = cnt.get(ext, 0) + 1
            items.append((f, os.path.getsize(fp)))
    p('  扩展名统计: ' + repr(cnt))
    for f, s in items[:40]:
        p('    %-46s %10s' % (f, '{:,}'.format(s)))
    if len(items) > 40:
        p('    ... 共 %d 个文件' % len(items))

# ---------- 2) chains 结构 ----------
p()
p('=' * 88)
p('dll_chains.json 结构')
p('=' * 88)
chains = json.load(open(os.path.join(WORK, 'dll_chains.json'), encoding='utf-8'))
for dll, ch in chains.items():
    tot = sum(len(v) for v in ch.values())
    p('  %-32s 链 %4d 条, 槽位合计 %5d' % (dll, len(ch), tot))
    k0 = list(ch.keys())[:3]
    for k in k0:
        p('      链@%s 前 4 项: %r' % (k, ch[k][:4]))
    break

# ---------- 3) 独立记号 vs 子串 ----------
param_zh = json.load(open(os.path.join(WORK, 'param_zh.json'), encoding='utf-8'))
for extra in ('hand_all.json', 'hand_other.json', 'hand_other2.json'):
    fp = os.path.join(WORK, extra)
    if os.path.exists(fp):
        param_zh.update(json.load(open(fp, encoding='utf-8')))

# ground truth: 预设名字
names = set()
pat = re.compile(rb'<name>(.*?)</name>', re.S)
PD = r"C:\ProgramData\BorisFX\Continuum\19\Presets"
for root, dirs, fs in os.walk(PD):
    for f in fs:
        if not f.lower().endswith(('.bsp', '.bap')):
            continue
        raw = open(os.path.join(root, f), 'rb').read()
        for m in pat.findall(raw):
            try:
                t = m.decode('utf-8')
            except Exception:
                try:
                    t = m.decode('gbk')
                except Exception:
                    continue
            t = t.strip()
            if t:
                names.add(t)

miss = sorted(n for n in names if n not in param_zh and n.isascii() and n.strip())

def toks(buf, needle):
    """返回 (独立记号数, 子串数, 位置列表)"""
    nb = needle.encode('ascii') + b'\x00'
    standalone, sub = [], 0
    i = 0
    while True:
        j = buf.find(nb, i)
        if j < 0:
            break
        i = j + 1
        if j == 0 or buf[j - 1] == 0:
            standalone.append(j)
        else:
            sub += 1
    return standalone, sub

p()
p('=' * 88)
p('3) 缺译文名字在装机 DLL 里的「独立记号」出现情况')
p('=' * 88)
targets = ['Width', 'Height', 'Blur', 'Channel', 'Rotate', 'Strength', 'Blur Quality',
           'Blur X', 'Blur Y', 'Pivot Point', 'View', 'Layer Mode', 'Bump Strength']
dlls = ['Continuum_AE_8Bit.dll', 'Continuum_Common_AE.dll', 'BCCPlus.dll',
        'Continuum_3DObjects_AE.dll']
for dll in dlls:
    path = os.path.join(LIB if dll != 'BCCPlus.dll' else CONT, dll)
    if not os.path.exists(path):
        p('  !! 缺 %s' % dll); continue
    buf = open(path, 'rb').read()
    p()
    p('  %s  (%s bytes)' % (dll, '{:,}'.format(len(buf))))
    for t in targets:
        st, sub = toks(buf, t)
        inchain = 0
        ch = chains.get(dll, {})
        sset = set()
        for off_s, arr in ch.items():
            sset.update(arr)
        if t in sset:
            inchain = 1
        p('     %-16s 独立记号 %3d   子串 %3d   chains内=%d' % (t, len(st), sub, inchain))

# ---------- 4) .aex 里有没有参数名 ----------
p()
p('=' * 88)
p('4) .aex 里有没有参数名字符串（抽样）')
p('=' * 88)
aexdir = os.path.join(CONT, 'Continuum AE.aex') if os.path.isdir(os.path.join(CONT, 'Continuum AE.aex')) else CONT
aexs = [f for f in os.listdir(aexdir) if f.lower().endswith('.aex')][:0]
# 找 .aex 所在目录
cand_dirs = []
for root, dirs, fs in os.walk(r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore"):
    if any(f.lower().endswith('.aex') for f in fs):
        cand_dirs.append(root)
    if len(cand_dirs) > 6:
        break
p('  含 .aex 的目录: %r' % cand_dirs[:6])
if cand_dirs:
    d0 = cand_dirs[0]
    fs0 = [f for f in os.listdir(d0) if f.lower().endswith('.aex')][:3]
    for f in fs0:
        buf = open(os.path.join(d0, f), 'rb').read()
        rep = []
        for t in ('Scale X', 'Intensity', 'Opacity', 'Width', 'Blur'):
            st, sub = toks(buf, t)
            if st or sub:
                rep.append('%s:独立%d/子串%d' % (t, len(st), sub))
        p('    %-44s %9s  %s' % (f, '{:,}'.format(len(buf)), ' | '.join(rep) or '(无)'   ))

open(os.path.join(WORK, '_probe_gap.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('DONE')

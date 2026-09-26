# -*- coding: utf-8 -*-
"""现状核查：系统里现在装的到底是哪一版？参数名汉化了多少、还剩多少英文？

三方对账：英文备份 / 已装机目录 / patched_dll_b（上一版产物） / patched_dll_c（本版产物）
口径：**NUL 分隔的独立记号**（长度 2~120）。ASCII 记号里若在词典中有译文 = 仍是英文的参数名。
"""
import os, re, json, hashlib

WORK = r"D:\Programming project\插件汉化\_work"
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"
LIB = r"C:\Program Files\BorisFX\ContinuumAE\19\lib"

DLLS = ['Continuum_AE_8Bit.dll', 'Continuum_AE_16Bit.dll', 'Continuum_AE_Float.dll',
        'Continuum_Common_AE.dll', 'Continuum_3DObjects_AE.dll', 'BCCPlus.dll']

# ★ 真实装机路径不是同一个目录：5 支引擎 DLL 在 19\lib\，
#   而 BCCPlus.dll 在 Adobe 的 MediaCore\BorisFX\Continuum\ 下。（脚本踩过这个坑）
def installed_path(dll):
    if dll == 'BCCPlus.dll':
        return os.path.join(CONT, dll)
    return os.path.join(LIB, dll)

param_zh = json.load(open(os.path.join(WORK, 'param_zh.json'), encoding='utf-8'))
for extra in ('hand_all.json', 'hand_other.json', 'hand_other2.json', 'gap_zh.json'):
    fp = os.path.join(WORK, extra)
    if os.path.exists(fp):
        param_zh.update(json.load(open(fp, encoding='utf-8')))
KEYS = set(k for k in param_zh if k.isascii() and len(k) >= 3)

out = []
def p(s=''):
    out.append(str(s))
    print(s, flush=True)

def sha(fp):
    return hashlib.sha256(open(fp, 'rb').read()).hexdigest()[:16]

def loc(path, dll):
    """path 为 None 时表示「真实装机目录」（5 支在 lib，BCCPlus 在 MediaCore）"""
    if path is None:
        return installed_path(dll)
    fp = os.path.join(path, dll)
    if os.path.exists(fp):
        return fp
    return installed_path(dll)

def segments(d):
    """产出 (off, seg) —— NUL 之间的独立记号"""
    i = 0
    n = len(d)
    while True:
        j = d.find(b'\x00', i)
        if j < 0:
            j = n
        seg = d[i:j]
        if 2 <= len(seg) <= 120:
            yield i, seg
        i = j + 1
        if i >= n:
            return

def analyze(path):
    """返回 (中文标签种数, 中文标签处数, 仍是英文的参数名处数, 英文名字集合, 每支明细)"""
    cn_n = cn_c = en_c = 0
    en_names = set()
    det = {}
    for dll in DLLS:
        d = open(loc(path, dll), 'rb').read()
        a = b = c = 0
        for off, seg in segments(d):
            if all(0x20 <= x <= 0x7e for x in seg):
                t = seg.decode('ascii')
                if t in KEYS:
                    b += 1
                    en_names.add(t)
                continue
            try:
                s = seg.decode('gbk')
            except UnicodeDecodeError:
                continue
            if any('\u4e00' <= ch <= '\u9fff' for ch in s):
                a += 1
        det[dll] = (a, b)
        cn_c += a
        en_c += b
    return cn_c, en_c, en_names, det

p('=' * 96)
p('① 系统里现在装的到底是哪一版？  （sha256 前 16 位三方比对）')
p('=' * 96)
p('%-30s %-18s %-18s %-18s %s' % ('DLL', '英文备份', 'patched_dll_b', 'patched_dll_c', '装机目录 = 哪版'))
installed_ver = {}
for dll in DLLS:
    h_bk = sha(os.path.join(BK, dll))
    h_b = sha(os.path.join(WORK, 'patched_dll_b', dll)) if os.path.exists(
        os.path.join(WORK, 'patched_dll_b', dll)) else '-'
    h_c = sha(os.path.join(WORK, 'patched_dll_c', dll)) if os.path.exists(
        os.path.join(WORK, 'patched_dll_c', dll)) else '-'
    h_i = sha(installed_path(dll)) if os.path.exists(installed_path(dll)) else '-'
    if h_i == h_b:
        v = '= patched_dll_b（上一版）'
    elif h_i == h_c:
        v = '= patched_dll_c（本版，已装！）'
    elif h_i == h_bk:
        v = '= 英文原版'
    else:
        v = '!! 都不是'
    installed_ver[dll] = v
    p('%-30s %-18s %-18s %-18s %s' % (dll, h_bk, h_b, h_c, v))
p()

p('=' * 96)
p('② 参数名汉化了多少 / 还剩多少英文（NUL 独立记号口径）')
p('=' * 96)
p('%-34s %14s %14s' % ('版本', '中文标签(处)', '仍是英文的参数名(处)'))
res = {}
for tag, path in (('英文原版（对照）', BK),
                  ('上一版 patched_dll_b（产物目录）', os.path.join(WORK, 'patched_dll_b')),
                  ('★ 真实装机（当前状态）', None),
                  ('本版 patched_dll_c（未装）', os.path.join(WORK, 'patched_dll_c'))):
    if path is not None and not os.path.isdir(path):
        continue
    cn, en, names, det = analyze(path)
    res[tag] = (cn, en, names, det)
    p('%-34s %14d %14d   （%d 个英文名字）' % (tag, cn, en, len(names)))
p()
p('分 DLL 明细（中文处数 / 仍英文处数）：')
tags = list(res)
p('%-30s %s' % ('DLL', ''.join('%20s' % t[:16] for t in tags)))
for dll in DLLS:
    p('%-30s %s' % (dll.replace('Continuum_', ''),
                    ''.join('%20s' % ('%d / %d' % res[t][3][dll]) for t in tags)))
p()

# ---------- ③ 装机版还英文、本版已修好 的名单 ----------
inst_tag = [t for t in tags if 'patched_dll_b' in t]
c_tag = '本版 patched_dll_c（未装）'
if inst_tag and c_tag in res:
    en_inst = res[inst_tag[0]][2]
    en_new = res[c_tag][2]
    fixed = sorted(en_inst - en_new)
    still = sorted(en_new)
    p('=' * 96)
    p('③ A. 装机版还是英文、**本版已修好**的参数名：%d 个（这就是用户现在看到英文的那批）' % len(fixed))
    p('=' * 96)
    line = []
    for nm in fixed:
        line.append('%-26s' % (nm + ' → ' + param_zh.get(nm, '?')))
        if len(line) == 3:
            p('   ' + ' '.join(line)); line = []
    if line:
        p('   ' + ' '.join(line))
    p()
    p('=' * 96)
    p('③ B. 本版**仍然保留英文**的参数名：%d 个（绝大部分是故意不翻）' % len(still))
    p('=' * 96)
    line = []
    for nm in still[:120]:
        line.append('%-24s' % nm)
        if len(line) == 3:
            p('   ' + ' '.join(line)); line = []
    if line:
        p('   ' + ' '.join(line))

open(os.path.join(WORK, '_state_check.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\nDONE')

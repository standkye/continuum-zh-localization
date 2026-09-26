# -*- coding: utf-8 -*-
"""最后一问：词典「压根没译文」的参数名，在第四版里还有多少是英文显示？

ground truth = 预设语料 (.bsp/.bap 的 <name>) 4451 条唯一参数名。
取其中词典未覆盖的 —— 这些是**真的还没有中文**的参数名。
再看它们在 patched_dll_d 里是否仍以独立英文记号存在（= 用户会看到英文）。
"""
import os, re, json, collections

WORK = r"D:\Programming project\插件汉化\_work"
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
PATCH = os.path.join(WORK, 'patched_dll_d')
PRESET = r"C:\ProgramData\BorisFX\Continuum\19\Presets"
NEW_SECTIONS = {'.rdata', '_RDATA'}
TOKEN_RE = re.compile(rb'[\x20-\x7e]+')

DLLS = ['Continuum_AE_8Bit.dll', 'Continuum_AE_16Bit.dll', 'Continuum_AE_Float.dll',
        'Continuum_Common_AE.dll', 'Continuum_3DObjects_AE.dll', 'BCCPlus.dll']

param_zh = json.load(open(os.path.join(WORK, 'param_zh.json'), encoding='utf-8'))
for extra in ('hand_all.json', 'hand_other.json', 'hand_other2.json', 'gap_zh.json'):
    fp = os.path.join(WORK, extra)
    if os.path.exists(fp):
        param_zh.update(json.load(open(fp, encoding='utf-8')))

# ---- 语料 ----
corpus = collections.Counter()
pat = re.compile(rb'<name>(.*?)</name>', re.S)
for root, dirs, fs in os.walk(PRESET):
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
                corpus[t] += 1
uncovered = sorted(n for n in corpus if n not in param_zh)

# ---- 在第四版里找这些词是否仍以英文独立记号出现 ----
def sections(d):
    pe = d.find(b'PE\x00\x00')
    nsec = int.from_bytes(d[pe + 6:pe + 8], 'little')
    optsz = int.from_bytes(d[pe + 20:pe + 22], 'little')
    base = pe + 24 + optsz
    r = []
    for i in range(nsec):
        o = base + i * 40
        nm = d[o:o + 8].rstrip(b'\x00').decode('ascii', 'replace')
        rsize = int.from_bytes(d[o + 16:o + 20], 'little')
        roff = int.from_bytes(d[o + 20:o + 24], 'little')
        r.append((nm, roff, rsize))
    return r

def sec_of(secs, off):
    for nm, roff, rsize in secs:
        if roff <= off < roff + rsize:
            return nm
    return '?'

still = collections.Counter()
where = collections.defaultdict(set)
for dll in DLLS:
    d = open(os.path.join(PATCH, dll), 'rb').read()
    secs = sections(d)
    for m in TOKEN_RE.finditer(bytes(d)):
        s, e = m.span()
        if s > 0 and d[s - 1] != 0:
            continue
        if e >= len(d) or d[e] != 0:
            continue
        t = m.group().decode('ascii', 'replace')
        if t in param_zh:
            continue
        sec = sec_of(secs, s)
        if sec not in NEW_SECTIONS:
            continue
        still[t] += 1
        where[t].add(dll.replace('Continuum_', ''))

hit = [(n, still[n], corpus[n]) for n in uncovered if n in still]

out = []
def p(s=''):
    out.append(str(s))
    print(s, flush=True)

p('=' * 100)
p('词典未覆盖的语料参数名 —— 在第四版里仍以英文出现')
p('=' * 100)
p('  语料唯一名 %d 条；词典未覆盖 %d 条；其中**在 DLL 里仍以英文独立记号存在** %d 条'
  % (len(corpus), len(uncovered), len(hit)))
p('  （其余 %d 条未覆盖词，在 DLL 里根本不作为独立标签出现 → 不会显示给用户）'
  % (len(uncovered) - len(hit)))
p()
p('  仍出现的，按在预设里被引用的次数排序（次数越高 = 用户越可能碰到）：')
for n, c, k in sorted(hit, key=lambda x: -x[2])[:200]:
    p('     %-42s 预设引用 %4d 次   记号 %4d 处   %s' % (n, k, c, ','.join(sorted(where[n]))))
p()
p('=' * 100)
p('  未出现的那 %d 条（不在 DLL 独立标签里，用户看不到）—— 列出前 80 条' % (len(uncovered) - len(hit)))
p('=' * 100)
rest = [n for n in uncovered if n not in still]
line = []
for n in rest[:80]:
    line.append('%-30s' % n)
    if len(line) == 3:
        p('     ' + ' '.join(line)); line = []
if line:
    p('     ' + ' '.join(line))

open(os.path.join(WORK, '_dict_gap_d.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\nDONE')

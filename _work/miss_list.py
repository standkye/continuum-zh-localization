# -*- coding: utf-8 -*-
"""产出「待补译」清单：漏翻参数名里，哪些在 DLL 只读节里有可安全替换的独立记号。

安全闸门（三层）：
  A. 节：只认 .rdata / _RDATA / .rsrc —— 与上一轮成功补丁的落点一致
  B. 形状：首字符必须是大写字母；不含 '_'；不含 '::' —— 挡掉 camelCase / dotted / snake_case 配置键
     注意：'/' 和 '.' 在真标签里合法（'Position X/Y'、'Sat. Rolloff Start'），不拦
  C. 邻居：往前 6 个记号内若出现「标识符样」的串（含 '_'、含 '.'、或首字符小写），
     判定为配置区，整条跳过 —— 例如 8Bit 的 `Pref_Type/Pref_Value` 后面那个 `Color`

产出：_work/_need_translate.txt
"""
import os, re, json

WORK = r"D:\Programming project\插件汉化\_work"
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"
PRESET = r"C:\ProgramData\BorisFX\Continuum\19\Presets"

ENGINE = ['Continuum_AE_8Bit.dll', 'Continuum_AE_16Bit.dll', 'Continuum_AE_Float.dll',
          'Continuum_Common_AE.dll', 'Continuum_3DObjects_AE.dll', 'BCCPlus.dll']
RO_SECTIONS = {'.rdata', '_RDATA', '.rsrc'}

TOKEN_RE = re.compile(rb'[\x20-\x7e]+')

out = []
def p(s=''):
    out.append(str(s))
    print(s, flush=True)

param_zh = json.load(open(os.path.join(WORK, 'param_zh.json'), encoding='utf-8'))
for extra in ('hand_all.json', 'hand_other.json', 'hand_other2.json'):
    fp = os.path.join(WORK, extra)
    if os.path.exists(fp):
        param_zh.update(json.load(open(fp, encoding='utf-8')))

corpus = {}
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
                corpus[t] = corpus.get(t, 0) + 1

miss = sorted([n for n in corpus if n not in param_zh], key=lambda x: -corpus[x])
p('缺译文 %d 条' % len(miss))

def sections(d):
    pe = d.find(b'PE\x00\x00')
    if pe < 0:
        return []
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

def ident_like(t):
    """『标识符样』= 不像显示标签：含 '_'、含 '.'、或首字符小写"""
    if '_' in t or '.' in t:
        return True
    return bool(t) and t[0].islower()

def shape_ok(t):
    if len(t) < 3 or len(t) > 60:
        return False
    if not t.isascii():
        return False
    if not t[0].isupper():
        return False
    if '_' in t or '::' in t:
        return False
    return True

# 预先建好每支 DLL 的记号序列（只读节内）
studied = []
for dll in ENGINE:
    src = os.path.join(BK, dll)
    key = dll
    if not os.path.exists(src):
        src = os.path.join(CONT, dll)
    d = open(src, 'rb').read()
    secs = sections(d)
    toks = []          # (off, text, avail)
    for m in TOKEN_RE.finditer(d):
        s, e = m.span()
        if s > 0 and d[s - 1] != 0:
            continue
        sec = sec_of(secs, s)
        if sec not in RO_SECTIONS:
            continue
        j = e
        while j < len(d) and d[j] == 0:
            j += 1
        toks.append((s, m.group().decode('ascii', 'replace'), j - s, sec))
    studied.append((dll, toks))
    p('%s 只读节独立记号 %d 个' % (dll, len(toks)))

alltext = set()
for dll, toks in studied:
    for off, t, av, sec in toks:
        alltext.add(t)

p()
p('=' * 92)
p('待补译清单（有可安全替换位置的）')
p('=' * 92)

need, skip_no_pos, skip_gate = [], [], []
for n in miss:
    if not shape_ok(n):
        skip_gate.append((n, '形状拦截'))
        continue
    hits = []
    for dll, toks in studied:
        for i, (off, t, av, sec) in enumerate(toks):
            if t != n:
                continue
            # C. 邻居闸门
            nb = [toks[j][1] for j in range(max(0, i - 6), i)]
            if any(ident_like(x) for x in nb):
                continue
            if av < 5:
                continue
            hits.append((dll, off, av, sec, nb[-1] if nb else ''))
    if not hits:
        skip_no_pos.append(n)
        continue
    best = max(h[2] for h in hits)
    need.append((n, corpus[n], len(hits), best, hits[0][0], hits[0][4]))

p('待补译 %d 条；无可用位置 %d 条；形状拦截 %d 条' %
  (len(need), len(skip_no_pos), len(skip_gate)))
p()
p('%-40s %8s %6s %6s' % ('英文原文', '预设次数', '位置数', '最大可用'))
p('-' * 92)
for n, c, k, best, dll, prev in sorted(need):
    p('%-40s %8d %6d %6d' % (n, c, k, best))

p()
p('=' * 92)
p('无可用位置（DLL 里没有独立记号，本次放弃）%d 条' % len(skip_no_pos))
p('=' * 92)
for i in range(0, len(skip_no_pos), 3):
    p('    ' + ' | '.join('%-34s' % x for x in skip_no_pos[i:i + 3]))

p()
p('形状拦截 %d 条：' % len(skip_gate))
for n, why in skip_gate[:40]:
    p('    %-40s %s' % (n, why))

open(os.path.join(WORK, '_need_translate.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('DONE')

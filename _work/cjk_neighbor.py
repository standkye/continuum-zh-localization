# -*- coding: utf-8 -*-
"""活性判据：某个英文记号周围有没有「已经翻好的中文」。
已经有中文的邻居 => 它处在一张「活的、AE 真会读的标签表」里 => 该翻、可以放心翻。
周围全是 ASCII 的孤立表   => 多半是内部名单/ID 表/库字符串 => 不动。

输出 _cjk_live.tsv : name / 总出现 / 带中文邻居的出现数 / 样例上下文
"""
import os, re, json, collections, bisect

WORK = r"D:\Programming project\插件汉化\_work"
PATCH = os.path.join(WORK, 'patched_dll_d')
TOKEN_RE = re.compile(rb'[\x20-\x7e]+')
DLLS = ['Continuum_AE_8Bit.dll', 'Continuum_AE_16Bit.dll', 'Continuum_AE_Float.dll',
        'Continuum_Common_AE.dll', 'Continuum_3DObjects_AE.dll', 'BCCPlus.dll']
SECTS = {'.rdata', '_RDATA'}
NEAR = 200          # 看前后各 200 字节里有没有 GBK 中文


def sections(d):
    pe = d.find(b'PE\x00\x00')
    nsec = int.from_bytes(d[pe + 6:pe + 8], 'little')
    optsz = int.from_bytes(d[pe + 20:pe + 22], 'little')
    base = pe + 24 + optsz
    r = []
    for i in range(nsec):
        o = base + i * 40
        nm = d[o:o + 8].rstrip(b'\x00').decode('ascii', 'replace')
        r.append((nm, int.from_bytes(d[o + 20:o + 24], 'little'),
                  int.from_bytes(d[o + 16:o + 20], 'little')))
    return r


def sec_of(secs, off):
    for nm, roff, rsize in secs:
        if roff <= off < roff + rsize:
            return nm
    return '?'


def has_cjk(buf):
    i = 0
    n = len(buf)
    while i < n:
        c = buf[i]
        if 0x81 <= c <= 0xFE and i + 1 < n and 0x40 <= buf[i + 1] <= 0xFE and buf[i + 1] != 0x7F:
            return True
        i += 1
    return False


def cand_ok(t):
    if not (4 <= len(t) <= 48):
        return False
    if not t.isascii() or not t[0].isalpha() or not t[0].isupper():
        return False
    return all((c.isalnum() or c in ' -+.%&') for c in t)


param_zh = json.load(open(os.path.join(WORK, 'param_zh.json'), encoding='utf-8'))
for extra in ('hand_all.json', 'hand_other.json', 'hand_other2.json', 'gap_zh.json'):
    fp = os.path.join(WORK, extra)
    if os.path.exists(fp):
        param_zh.update(json.load(open(fp, encoding='utf-8')))

rec = collections.defaultdict(lambda: [0, 0, ''])
for dll in DLLS:
    p = os.path.join(PATCH, dll)
    if not os.path.exists(p):
        continue
    b = open(p, 'rb').read()
    secs = sections(b)
    for m in TOKEN_RE.finditer(b):
        s, e = m.span()
        if s > 0 and b[s - 1] != 0:
            continue
        if e >= len(b) or b[e] != 0:
            continue
        if sec_of(secs, s) not in SECTS:
            continue
        t = m.group().decode('ascii', 'replace')
        if not cand_ok(t) or t in param_zh:
            continue
        rec[t][0] += 1
        win = b[max(0, s - NEAR):e + NEAR]
        live = has_cjk(win)
        if live:
            rec[t][1] += 1
            if not rec[t][2]:
                rec[t][2] = (b[max(0, s - 60):s].replace(b'\x00', b'|')).decode('latin-1')[-58:]

rows = sorted(rec.items(), key=lambda kv: (-kv[1][1], -kv[1][0], kv[0]))
with open(os.path.join(WORK, '_cjk_live.tsv'), 'w', encoding='utf-8') as f:
    f.write('name\ttotal\tlive_occ\tcjk_context\n')
    for t, (tot, live, ctx) in rows:
        f.write('%s\t%d\t%d\t%s\n' % (t, tot, live, ctx))

live_only = [r for r in rows if r[1][1] > 0]
lines = ['带中文邻居（活表）名字 %d 个 / NO_DICT 总 %d 个' % (len(live_only), len(rows)), '']
for t, (tot, live, ctx) in live_only[:300]:
    lines.append('%-36s 总%2d 活%2d  %s' % (t, tot, live, ctx[-60:]))
open(os.path.join(WORK, '_cjk_live_top.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
print('live names', len(live_only), 'of', len(rows))

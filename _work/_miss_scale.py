# -*- coding: utf-8 -*-
"""统计"仍在界面上的漏翻"规模：仍是英文的独立记号 + 通过闸门 + 有中文邻居
   + 容量足够，按出现频次排序。"""
import os, json, collections

ENC = 'gbk'
BASE = r'D:\Programming project\插件汉化'
PD = os.path.join(BASE, '_work', 'patched_dll_d')

out = []
def say(*a):
    out.append(' '.join(str(x) for x in a))

# ---- 词典 ----
DICT = {}
for name in ['hand_all', 'hand_other', 'hand_other2', 'gap_zh',
             'gap_zh_short', 'batch5_ename', 'batch6_ui']:
    p = os.path.join(BASE, '_work', name + '.json')
    if os.path.exists(p):
        try:
            d = json.load(open(p, encoding='utf-8'))
            if isinstance(d, dict):
                DICT.update(d)
        except Exception:
            pass
say('词典合计 %d 条' % len(DICT))

NEVER = {'Resources', 'Documentation', 'Duration'}
HOST = {'Final Cut Pro', 'Motion', 'Red', 'Combustion', 'OpenFX', 'Corel',
        'Quantel', 'Natron', 'Baselight', 'Lightworks', 'Resolve', 'Premiere'}

def sections(d):
    pe = d.find(b'PE\x00\x00')
    nsec = int.from_bytes(d[pe+6:pe+8], 'little')
    optsz = int.from_bytes(d[pe+20:pe+22], 'little')
    sb = pe + 24 + optsz
    secs = []
    for i in range(nsec):
        o = sb + i * 40
        n = d[o:o+8].rstrip(b'\x00').decode('ascii', 'replace')
        vsz = int.from_bytes(d[o+8:o+12], 'little')
        va = int.from_bytes(d[o+12:o+16], 'little')
        rsz = int.from_bytes(d[o+16:o+20], 'little')
        ro = int.from_bytes(d[o+20:o+24], 'little')
        secs.append((n, va, max(vsz, rsz), ro))
    return secs

def sec_of(secs, off):
    for n, va, sz, ro in secs:
        if ro <= off < ro + sz:
            return n
    return '?'

def ident_like(s):
    return ('_' in s) or ('.' in s) or (s[:1].islower())

cnt = collections.Counter()
where = collections.defaultdict(list)
cap = {}

for fn in sorted(os.listdir(PD)):
    if not fn.lower().endswith('.dll'):
        continue
    d = open(os.path.join(PD, fn), 'rb').read()
    secs = sections(d)
    i = 0
    n = len(d)
    while i < n:
        c = d[i]
        if not (65 <= c <= 90 or 48 <= c <= 57):
            i += 1
            continue
        # 收集一个可打印串
        j = i
        buf = bytearray()
        while j < n and (32 <= d[j] < 127):
            buf.append(d[j]); j += 1
        if j >= n or d[j] != 0:
            i = j + 1; continue
        s = buf.decode('ascii', 'replace')
        # 必须是 "独立记号"：前一个字节也要是 NUL
        left_ok = (i == 0) or d[i-1] == 0
        # 到下一个非 NUL 的距离 = 容量
        k = j
        while k < n and d[k] == 0:
            k += 1
        avail = k - i
        i = j + 1
        if not left_ok:
            continue
        # 形状闸
        s = s.rstrip()
        if not (2 <= len(s) <= 60):
            continue
        if '_' in s or '::' in s or '/' in s or '\\' in s:
            continue
        if not all(ch.isalnum() or ch in ' -+.%&' for ch in s):
            continue
        if s in NEVER or s in HOST:
            continue
        # 只看 .rdata
        if sec_of(secs, i - 1) != '.rdata':
            continue
        # 只看仍英文（全 ASCII）
        if any(ord(ch) > 127 for ch in s):
            continue
        if s in DICT:
            continue
        # 邻居闸：往前 96 字节找标识符样串
        lo = max(0, i - 96)
        win = d[lo:i]
        bad = False
        for m in win.split(b'\x00'):
            if len(m) >= 2:
                t = m.decode('ascii', 'ignore')
                if t and ident_like(t):
                    bad = True; break
        if bad:
            continue
        # 邻居：附近要有中文（说明它在活的 UI 表里）
        saw_cjk = False
        wlo = max(0, i - 256); whi = min(n, i + 256)
        for q in range(wlo, whi):
            if d[q] >= 0x80:
                saw_cjk = True; break
        if not saw_cjk:
            continue
        # 容量：至少能放 2 个汉字 = 5 字节
        if avail < 5:
            continue
        cnt[s] += 1
        where[s].append((fn, i, avail))
        cap[s] = min(cap.get(s, 10**9), avail)

say('')
say('=== "活 UI 表里、词典缺键、容量 >= 5 字节" 的英文独立记号 ===')
say('名字数: %d   出现总次数: %d' % (len(cnt), sum(cnt.values())))
say('')
ordered = cnt.most_common()
tot = sum(cnt.values())
acc = 0
for idx, (s, c) in enumerate(ordered, 1):
    acc += c
    if idx in (100, 300, 500, 1000, 2000):
        say('  前 %-5d 个名字   覆盖出现次数 %6d   占 %5.1f%%'
            % (idx, acc, acc * 100.0 / tot))
say('')
say('--- 出现频次 TOP 120（这些最容易被看到）---')
for idx, (s, c) in enumerate(ordered[:120], 1):
    say('  %3d. %-34s x%-3d  容量%3d  %s'
        % (idx, s, c, cap[s], where[s][0][0]))

open(os.path.join(BASE, '_work', '_miss_scale.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('done')

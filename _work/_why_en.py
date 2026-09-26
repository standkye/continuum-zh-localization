# -*- coding: utf-8 -*-
"""给定若干英文字符串，定位它在 patched_dll_d 里的每一处出现，
   并打印所在节 / 前后邻居 / 容量 / 是否被否道闸门拦下。"""
import os, sys, json

ENC = 'gbk'
BASE = r'D:\Programming project\插件汉化'
PD = os.path.join(BASE, '_work', 'patched_dll_d')
BK = r'C:\Program Files\BorisFX\ContinuumAE\19\Backup-English'
BUILTIN = os.path.join(BASE, '_work')

TARGETS = sys.argv[1:] or ['Curves', 'Allow Resizing', 'Allow Realizing']

out = []
def say(*a):
    out.append(' '.join(str(x) for x in a))


# ---------- 载入全部词典 ----------
DICT = {}
LOAD_ORDER = ['hand_all', 'hand_other', 'hand_other2', 'gap_zh',
              'gap_zh_short', 'batch5_ename', 'batch6_ui']
for name in LOAD_ORDER:
    p = os.path.join(BUILTIN, name + '.json')
    if os.path.exists(p):
        try:
            d = json.load(open(p, encoding='utf-8'))
            if isinstance(d, dict):
                DICT.update(d)
                say('载入词典 %-16s %d 条' % (name, len(d)))
        except Exception as e:
            say('词典载入失败 %s: %s' % (name, e))
say('词典合计 %d 条' % len(DICT))
say('')


# ---------- PE 节表 ----------
def sections(d):
    pe = d.find(b'PE\x00\x00')
    nsec = int.from_bytes(d[pe+6:pe+8], 'little')
    optsz = int.from_bytes(d[pe+20:pe+22], 'little')
    secbase = pe + 24 + optsz
    secs = []
    for i in range(nsec):
        o = secbase + i * 40
        name = d[o:o+8].rstrip(b'\x00').decode('ascii', 'replace')
        vsz = int.from_bytes(d[o+8:o+12], 'little')
        va = int.from_bytes(d[o+12:o+16], 'little')
        rsz = int.from_bytes(d[o+16:o+20], 'little')
        roff = int.from_bytes(d[o+20:o+24], 'little')
        secs.append((name, va, max(vsz, rsz), roff))
    return secs


def sec_of(secs, off):
    for n, va, sz, ro in secs:
        if ro <= off < ro + sz:
            return n
    return '?'


def show_ctx(d, s, ln, before=64, after=64):
    """把 s..e 前后的可打印串打出来（含中文），用于判断邻居。"""
    lo = max(0, s - before)
    hi = min(len(d), s + ln + after)
    # 抽取可打印串
    chunks = []
    cur = b''
    pos = lo
    for i in range(lo, hi):
        c = d[i]
        if 32 <= c < 127 or c >= 0x80:
            if not cur:
                pos = i
            cur += bytes([c])
        else:
            if len(cur) >= 2:
                chunks.append((pos, cur))
            cur = b''
    if len(cur) >= 2:
        chunks.append((pos, cur))
    res = []
    for p_, c in chunks:
        try:
            t = c.decode(ENC)
        except Exception:
            t = repr(c)
        res.append('@%#x %s' % (p_, t))
    return res


FILES = sorted(f for f in os.listdir(PD) if f.lower().endswith('.dll'))

for tgt in TARGETS:
    say('=' * 78)
    say('目标: %r' % tgt)
    say('  词典里有吗: %s' % (('是 -> %s' % DICT[tgt]) if tgt in DICT else '** 没有 **'))
    tb = tgt.encode('ascii')
    tbz = tb + b'\x00'
    hits = 0
    for fn in FILES:
        d = open(os.path.join(PD, fn), 'rb').read()
        secs = sections(d)
        start = 0
        while True:
            i = d.find(tbz, start)
            if i < 0:
                break
            start = i + 1
            # 前一个字节必须是 NUL（才是独立记录的开头）
            left_ok = (i == 0) or d[i-1] == 0
            # 到下一个非 NUL 的距离 = 可用容量
            j = i + len(tbz)
            while j < len(d) and d[j] == 0:
                j += 1
            avail = j - i
            sec = sec_of(secs, i)
            flag = '独立' if left_ok else '子串'
            say('')
            say('  %s  off=%#x  %s  节=%s  可用=%d' % (fn, i, flag, sec, avail))
            zh = DICT.get(tgt)
            if zh:
                need = len(zh.encode(ENC)) + 1
                say('     词典译文 %r  需要 %d 字节  -> %s'
                    % (zh, need, '放得下' if need <= avail else '★ 放不下'))
            else:
                say('     ** 词典缺键 **')
            if hits < 6:
                for line in show_ctx(d, i, len(tb), 56, 56):
                    say('       ' + line)
            hits += 1
    if hits == 0:
        say('  !! 在 patched_dll_d 里**完全找不到**这个独立记号')
    say('')

say('===== 汇总 =====')
for tgt in TARGETS:
    say('  %-20s 词典命中=%s' % (tgt, '是' if tgt in DICT else '否'))

open(os.path.join(BASE, '_work', '_why_en.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('done')

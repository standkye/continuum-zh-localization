# -*- coding: utf-8 -*-
"""从漏翻候选里筛出真正的 UI 参数标签（剔掉各种内部符号）。"""
import os, json, collections, re

ENC = 'gbk'
BASE = r'D:\Programming project\插件汉化'
PD = os.path.join(BASE, '_work', 'patched_dll_d')

out = []
def say(*a):
    out.append(' '.join(str(x) for x in a))

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

# ---- 内部符号判据 ----
XML_DTD = {'NMTOKEN','NMTOKENS','IDREF','IDREFS','PCDATA','CDATA','NDATA','NOTATION',
           'PUBLIC','SYSTEM','IMPLIED','REQUIRED','IGNORE','INCLUDE','ENTITY','ELEMENT',
           'ATTLIST','DOCTYPE','ANY','EMPTY','FIXED'}
TECH_WORDS = ('Suite','AEGP','PF ','VDS','PrSDK','BFC','BFX','CBFX','GStreamer',
              'Shader','Deformer','Cinema','C4D','OpenGL','OpenCL','CUDA','Metal',
              'DirectX','QuickTime','Redshift','Octane','Arnold')
def looks_internal(s):
    if s in XML_DTD:
        return True
    if '%' in s:                                  # 格式化串
        return True
    for w in TECH_WORDS:
        if w.lower() in s.lower():
            # Shader/Deformer 只在 "xxx Surface Shader" 这种宿主材质名里出现
            return True
    words = s.split()
    # 无空格 + 驼峰(>=2个大写且含小写) => 类名/函数名/内部符号
    if len(words) == 1:
        uppers = sum(1 for c in s if c.isupper())
        if uppers >= 2 and any(c.islower() for c in s) and not s.isupper():
            return True
        if s.isupper() and len(s) >= 4:           # 全大写缩写/常量
            return True
    # 以小写开头的驼峰
    if s[:1].islower():
        return True
    # 全大写短语
    alpha = [c for c in s if c.isalpha()]
    if alpha and all(c.isupper() for c in alpha):
        return True
    return False

NEVER = {'Resources','Documentation','Duration'}
HOST = {'Final Cut Pro','Motion','Red','Combustion','OpenFX','Corel','Quantel',
        'Natron','Baselight','Lightworks','Resolve','Premiere'}

cnt = collections.Counter()
cap = {}
where = collections.defaultdict(list)
internal_cnt = collections.Counter()

for fn in sorted(os.listdir(PD)):
    if not fn.lower().endswith('.dll'):
        continue
    d = open(os.path.join(PD, fn), 'rb').read()
    secs = sections(d)
    i = 0; n = len(d)
    while i < n:
        c = d[i]
        if not (65 <= c <= 90 or 48 <= c <= 57):
            i += 1; continue
        j = i; buf = bytearray()
        while j < n and 32 <= d[j] < 127:
            buf.append(d[j]); j += 1
        if j >= n or d[j] != 0:
            i = j + 1; continue
        s = buf.decode('ascii','replace').rstrip()
        left_ok = (i == 0) or d[i-1] == 0
        k = j
        while k < n and d[k] == 0: k += 1
        avail = k - i
        i = j + 1
        if not left_ok: continue
        if not (2 <= len(s) <= 60): continue
        if '_' in s or '::' in s or '/' in s or '\\' in s: continue
        if not all(ch.isalnum() or ch in ' -+.%&' for ch in s): continue
        if s in NEVER or s in HOST: continue
        if sec_of(secs, i-1) != '.rdata': continue
        if any(ord(ch) > 127 for ch in s): continue
        if s in DICT: continue
        lo = max(0, i-96); bad = False
        for m in d[lo:i].split(b'\x00'):
            if len(m) >= 2:
                t = m.decode('ascii','ignore')
                if t and (('_' in t) or ('.' in t) or t[:1].islower()):
                    bad = True; break
        if bad: continue
        wlo = max(0,i-256); whi = min(n,i+256)
        if not any(d[q] >= 0x80 for q in range(wlo, whi)): continue
        if avail < 5: continue
        if looks_internal(s):
            internal_cnt[s] += 1
            continue
        cnt[s] += 1
        cap[s] = min(cap.get(s, 10**9), avail)
        where[s].append((fn, i, avail))

say('=== 筛选结果 ===')
say('词典 %d 条' % len(DICT))
say('判定为内部符号（保留英文）: %d 个名字 / %d 次' % (len(internal_cnt), sum(internal_cnt.values())))
say('判定为 UI 标签（可以翻）  : %d 个名字 / %d 次' % (len(cnt), sum(cnt.values())))
say('')
say('--- 内部符号 TOP 40（确认过滤得对不对）---')
for s, c in internal_cnt.most_common(40):
    say('   %-42s x%d' % (s, c))
say('')
say('--- UI 标签候选：按频次排序（前 300）---')
ordered = cnt.most_common()
for idx, (s, c) in enumerate(ordered[:300], 1):
    say('  %3d. %-40s x%-3d cap=%-3d %s' % (idx, s, c, cap[s], where[s][0][0]))

# 机器可读清单
tsv = ['English\tCap\tCount\tFile']
for s, c in ordered:
    tsv.append('%s\t%d\t%d\t%s' % (s, cap[s], c, where[s][0][0]))
open(os.path.join(BASE,'_work','_ui_miss.tsv'),'w',encoding='utf-8').write('\n'.join(tsv))
say('')
say('机器可读清单 -> _work\\_ui_miss.tsv  (%d 条)' % len(ordered))

open(os.path.join(BASE, '_work', '_ui_miss.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('done')

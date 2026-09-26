# -*- coding: utf-8 -*-
"""参数名漏翻诊断：
   1) 从 BorisFX 预设里抽全部 <name>（ground truth 参数名）
   2) 与词典比对，看有多少没有译文
   3) 与各 DLL 的槽位链比对，看有多少压根不在可改范围内
"""
import os, re, json, io
from collections import Counter

WORK = r"D:\Programming project\插件汉化\_work"
PRESET_DIRS = [
    r"C:\ProgramData\BorisFX\Continuum\19\Presets",
]
LIB = r"C:\Program Files\BorisFX\ContinuumAE\19\lib"
CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"

out = []
def p(s=''):
    out.append(str(s))
    print(s, flush=True)

# ---------------- 1) 预设里的参数名 ----------------
p('=' * 78)
p('1) 从预设抽 <name>（ground truth）')
p('=' * 78)

names = Counter()
files = 0
pat = re.compile(rb'<name>(.*?)</name>', re.S)
for d in PRESET_DIRS:
    if not os.path.isdir(d):
        p('  !! 目录不存在: ' + d); continue
    for root, dirs, fs in os.walk(d):
        for f in fs:
            if not f.lower().endswith(('.bsp', '.bap')):
                continue
            files += 1
            try:
                raw = open(os.path.join(root, f), 'rb').read()
            except Exception:
                continue
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
                    names[t] += 1

p('  预设文件 %d 个，抽出唯一 <name> %d 条' % (files, len(names)))

# ---------------- 2) 词典 ----------------
param_zh = json.load(open(os.path.join(WORK, 'param_zh.json'), encoding='utf-8'))
src_counts = ['param_zh.json:%d' % len(param_zh)]
for extra in ('hand_all.json', 'hand_other.json', 'hand_other2.json'):
    fp = os.path.join(WORK, extra)
    if os.path.exists(fp):
        j = json.load(open(fp, encoding='utf-8'))
        param_zh.update(j)
        src_counts.append('%s:%d' % (extra, len(j)))
p('  词典合计 %d 条  (%s)' % (len(param_zh), ', '.join(src_counts)))
p()

# ---------------- 3) 覆盖率 ----------------
have = []
miss = []
for n, c in names.most_common():
    if n in param_zh:
        have.append((n, c, param_zh[n]))
    else:
        miss.append((n, c))

p('=' * 78)
p('2) 词典覆盖')
p('=' * 78)
p('  有译文 %d / %d  (%.1f%%)' % (len(have), len(names), 100.0 * len(have) / max(1, len(names))))
p('  缺译文 %d 条' % len(miss))
p()
p('  缺译文 Top 80（按在预设里出现的次数排序）：')
for n, c in miss[:80]:
    p('      %-46s x%d' % (n[:46], c))

# ---------------- 4) 缺译文的名字在哪个 DLL 里出现 ----------------
p()
p('=' * 78)
p('3) 缺译文的名字分布在哪些 DLL（判断是不是漏扫了某支）')
p('=' * 78)

chains = json.load(open(os.path.join(WORK, 'dll_chains.json'), encoding='utf-8'))
# 建立 DLL -> 槽位字符串集合
dll_slots = {}
for name, ch in chains.items():
    s = set()
    for off_s, arr in ch.items():
        for x in arr:
            s.add(x)
    dll_slots[name] = s

miss_names = set(n for n, _ in miss)
hit_stat = Counter()
for name, s in dll_slots.items():
    hit_stat[name] = len(miss_names & s)
p('  各 DLL 的槽位总数 与 "缺译文名字"命中数：')
for name, s in sorted(dll_slots.items()):
    p('    %-30s 槽位 %5d   缺译文命中 %4d' % (name, len(s), hit_stat[name]))

# ---------------- 5) 词典里有译文、但没被替换的 ----------------
p()
p('=' * 78)
p('4) 抽查：词典有译文 但装机 DLL 里仍是英文的例子')
p('=' * 78)
for dll in ('Continuum_AE_8Bit.dll', 'Continuum_Common_AE.dll', 'BCCPlus.dll',
            'Continuum_3DObjects_AE.dll'):
    fp = os.path.join(LIB, dll)
    if not os.path.exists(fp):
        continue
    dd = open(fp, 'rb').read()
    still = []
    for n, c, zh in have:
        try:
            nb = n.encode('ascii')
        except Exception:
            continue
        if len(nb) < 3:
            continue
        # 只找槽位形式：字符串 + NUL
        if nb + b'\x00' in dd:
            still.append((n, zh, c))
    still.sort(key=lambda x: -x[2])
    p('  %-30s 仍有英文原文的（词典里有译文）: %d 条' % (dll, len(still)))
    for n, zh, c in still[:25]:
        p('      %-40s -> %-20s x%d' % (n[:40], zh[:20], c))

open(os.path.join(WORK, '_param_gap.txt'), 'w', encoding='utf-8').write('\n'.join(out))

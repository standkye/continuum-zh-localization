# -*- coding: utf-8 -*-
"""定位：同一个参数名在 DLL 里出现几次？哪些位置被改过？extra 位置是什么结构？"""
import os, json, struct

WORK = r"D:\Programming project\插件汉化\_work"
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
LIB = r"C:\Program Files\BorisFX\ContinuumAE\19\lib"

out = []
def p(s=''):
    out.append(str(s))
    print(s, flush=True)

chains = json.load(open(os.path.join(WORK, 'dll_chains.json'), encoding='utf-8'))

DLL = 'Continuum_AE_8Bit.dll'
a = open(os.path.join(BK, DLL), 'rb').read()
b = open(os.path.join(LIB, DLL), 'rb').read()

# chains 覆盖区间
cover = set()
slot_map = {}      # offset -> (slot, s)
for off_s, arr in chains[DLL].items():
    cur = int(off_s)
    for s in arr:
        slot = max(8, ((len(s) + 1 + 7) // 8) * 8)
        slot_map[cur] = (slot, s)
        for i in range(cur, cur + slot):
            cover.add(i)
        cur += slot

p('=' * 78)
p('%s   chains 覆盖槽位 %d 个，覆盖字节 %d' % (DLL, len(slot_map), len(cover)))
p('=' * 78)
p()

def find_all(hay, needle):
    r = []
    i = 0
    while True:
        j = hay.find(needle, i)
        if j < 0:
            break
        r.append(j)
        i = j + 1
    return r

for probe in ('Scale X', 'Color', 'Falloff', 'Intensity', 'Shape', 'Opacity'):
    nb = probe.encode() + b'\x00'
    pos_a = find_all(a, nb)
    pos_b = find_all(b, nb)
    p('%-12s 备份里出现 %2d 次，装机里仍有 %2d 次' % (probe, len(pos_a), len(pos_b)))
    # 逐个位置判断
    for pos in pos_a[:8]:
        inc = pos in cover
        changed = (a[pos:pos + len(nb)] != b[pos:pos + len(nb)])
        ctx = ''
        if not inc:
            # 看看前面有什么
            back = a[max(0, pos - 40):pos]
            ctx = repr(back[-30:])
        p('    0x%08X  在chains内=%-5s 已改=%-5s  %s' % (pos, inc, changed, ctx))
    p()

# 统计：所有"词典有译文但装机仍是英文"的串，它们的出现位置有多少在 chains 外
param_zh = json.load(open(os.path.join(WORK, 'param_zh.json'), encoding='utf-8'))
for extra in ('hand_all.json', 'hand_other.json', 'hand_other2.json'):
    fp = os.path.join(WORK, extra)
    if os.path.exists(fp):
        param_zh.update(json.load(open(fp, encoding='utf-8')))

stat = {'in_cover': 0, 'out_cover': 0, 'keys': 0}
samples_out = []
for k in param_zh:
    try:
        nb = k.encode('ascii') + b'\x00'
    except Exception:
        continue
    if len(nb) < 4:
        continue
    pos_list = find_all(b, nb)
    if not pos_list:
        continue
    stat['keys'] += 1
    for pos in pos_list:
        if pos in cover:
            stat['in_cover'] += 1
        else:
            stat['out_cover'] += 1
            if len(samples_out) < 40:
                samples_out.append((k, pos, repr(a[max(0, pos - 24):pos])))

p('=' * 78)
p('统计：装机 DLL 里"仍是英文"的 词典键')
p('=' * 78)
p('  涉及键 %d 个' % stat['keys'])
p('  出现位置：在 chains 内 %d 处，在 chains 外 %d 处' % (stat['in_cover'], stat['out_cover']))
p()
p('  chains 外的样例（看它们前面是什么，推断结构）：')
for k, pos, ctx in samples_out[:40]:
    p('    %-34s 0x%08X  ...%s' % (k[:34], pos, ctx))

open(os.path.join(WORK, '_dupe_probe.txt'), 'w', encoding='utf-8').write('\n'.join(out))

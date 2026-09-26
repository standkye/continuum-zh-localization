# -*- coding: utf-8 -*-
"""分析槽位池结构：元数据键区 vs 显示标签区"""
import os, json

WORK = r'D:\Programming project\插件汉化\_work'
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
LIB = r"C:\Program Files\BorisFX\ContinuumAE\19\lib"
CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"

chains = json.load(open(os.path.join(WORK, 'dll_chains.json'), encoding='utf-8'))
out = []
def p(s=''):
    out.append(str(s))

TARGETS = ['Continuum_3DObjects_AE.dll', 'Continuum_AE_8Bit.dll']
# 已知罪魁区域
HOT = (0x126F4B8, 0x126FE00)

for T in TARGETS:
    ch = chains[T]
    bk = open(os.path.join(BK, T), 'rb').read()
    cur = open(os.path.join(LIB, T), 'rb').read()

    p('=' * 78)
    p(T)
    p('=' * 78)

    all_slots = []
    for off_s, arr in ch.items():
        o = int(off_s)
        for s in arr:
            slot = max(8, ((len(s) + 1 + 7) // 8) * 8)
            all_slots.append((o, slot, s))
            o += slot
    all_slots.sort()

    p('chains 里槽位总数: %d' % len(all_slots))
    changed = [(o, sl, s) for (o, sl, s) in all_slots if bk[o:o + sl] != cur[o:o + sl]]
    p('实际被改动: %d' % len(changed))

    # 槽位大小分布
    from collections import Counter
    c_all = Counter(sl for _, sl, _ in all_slots)
    c_chg = Counter(sl for _, sl, _ in changed)
    p('  全部槽位大小分布: %s' % dict(sorted(c_all.items())))
    p('  改动槽位大小分布: %s' % dict(sorted(c_chg.items())))

    # 偏移聚簇：按 64KB 分段统计
    p()
    p('  --- 改动槽位按 64KB 段分布（重点看是否有独立的小聚簇）---')
    seg_all = Counter()
    seg_chg = Counter()
    for o, sl, s in all_slots:
        seg_all[o >> 16] += 1
    for o, sl, s in changed:
        seg_chg[o >> 16] += 1
    for k in sorted(seg_all):
        mk = ' <== 含元数据区' if (k << 16) <= HOT[0] < ((k + 1) << 16) else ''
        p('    0x%02X0000 - 0x%02XFFFF : 全部 %3d  改动 %3d%s'
          % (k, k, seg_all[k], seg_chg[k], mk))

    # 罪魁附近区域详细列出
    p()
    p('  --- 0x126F400 ~ 0x126FF00 区域全部槽位 ---')
    for o, sl, s in all_slots:
        if 0x126F400 <= o < 0x126FF00:
            tag = ''
            if bk[o:o + sl] != cur[o:o + sl]:
                nb = cur[o:o + sl].split(b'\x00')[0]
                try:
                    nb = nb.decode('utf-8')
                except Exception:
                    nb = repr(nb)
                tag = '  ->  改成了 %r' % nb
            else:
                tag = '  (未改)'
            p('    0x%08X slot=%-3d %-24r%s' % (o, sl, s, tag))

    # 罪魁前后最近的其他改动槽位（判断区域边界）
    p()
    p('  --- 罪魁 0x126F7C8 前后最近的改动槽位 ---')
    idx = next((i for i, (o, sl, s) in enumerate(changed) if o == 0x126F7C8), None)
    if idx is not None:
        for j in range(max(0, idx - 8), min(len(changed), idx + 9)):
            o, sl, s = changed[j]
            mk = ' <<<' if j == idx else ''
            p('    #%-4d 0x%08X slot=%-3d %r%s' % (j, o, sl, s, mk))
    p()

open(os.path.join(WORK, '_slotmap.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('done')

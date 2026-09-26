# -*- coding: utf-8 -*-
"""精确对比：同一参数名的"已改位置"与"未改位置"在结构上的区别"""
import os, json

WORK = r"D:\Programming project\插件汉化\_work"
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
LIB = r"C:\Program Files\BorisFX\ContinuumAE\19\lib"
CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"

out = []
def p(s=''):
    out.append(str(s))
    print(s, flush=True)

chains = json.load(open(os.path.join(WORK, 'dll_chains.json'), encoding='utf-8'))

def find_all(h, nd):
    r = []
    i = 0
    while True:
        j = h.find(nd, i)
        if j < 0:
            break
        r.append(j)
        i = j + 1
    return r

for DLL in ('Continuum_AE_8Bit.dll', 'BCCPlus.dll'):
    a = open(os.path.join(BK, DLL), 'rb').read()
    b = open(os.path.join(LIB if DLL != 'BCCPlus.dll' else CONT, DLL), 'rb').read()
    slot_starts = {}
    for off_s, arr in chains.get(DLL, {}).items():
        cur = int(off_s)
        for s in arr:
            slot = max(8, ((len(s) + 1 + 7) // 8) * 8)
            slot_starts[cur] = (slot, s)
            cur += slot

    p('=' * 90)
    p(DLL + '   chains 槽位起点 %d 个' % len(slot_starts))
    p('=' * 90)

    for probe in ('Scale X', 'Color', 'Opacity', 'Intensity'):
        nb = probe.encode() + b'\x00'
        pos_a = find_all(a, nb)
        pos_b = find_all(b, nb)
        p()
        p('### %r   备份 %d 处，装机仍有 %d 处' % (probe, len(pos_a), len(pos_b)))
        changed_n = 0
        for pos in pos_a:
            changed = a[pos:pos + len(nb)] != b[pos:pos + len(nb)]
            if changed:
                changed_n += 1
                continue          # 已改的先不打印明细
        p('    已改 %d，未改 %d' % (changed_n, len(pos_a) - changed_n))
        p('    --- 未改位置的上下文（前 32 / 后 40 字节）---')
        shown = 0
        for pos in pos_a:
            if a[pos:pos + len(nb)] == b[pos:pos + len(nb)]:
                pre = a[max(0, pos - 32):pos]
                post = a[pos + len(nb):pos + len(nb) + 40]
                is_start = (pos in slot_starts)
                p('     0x%08X slot起点=%-5s' % (pos, is_start))
                p('        前: %r' % pre)
                p('        后: %r' % post)
                shown += 1
                if shown >= 4:
                    break
        p('    --- 已改位置的上下文（对照，最多 4 个）---')
        shown = 0
        for pos in pos_a:
            if a[pos:pos + len(nb)] != b[pos:pos + len(nb)]:
                pre = a[max(0, pos - 32):pos]
                post = a[pos + len(nb):pos + len(nb) + 40]
                p('     0x%08X slot起点=%-5s' % (pos, pos in slot_starts))
                p('        前: %r' % pre)
                p('        后: %r' % post)
                shown += 1
                if shown >= 4:
                    break
        p()

open(os.path.join(WORK, '_cmp_ctx.txt'), 'w', encoding='utf-8').write('\n'.join(out))

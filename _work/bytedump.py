# -*- coding: utf-8 -*-
"""把某段字节在 英文版 / 补丁版 里都 dump 出来，直接看补丁做了什么。"""
import os, json

WORK = r"D:\Programming project\插件汉化\_work"
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
PATCH = os.path.join(WORK, 'patched_dll_c')

writes = json.load(open(os.path.join(WORK, '_fix3_writes.json'), encoding='utf-8'))

out = []
def p(s=''):
    out.append(str(s))
    print(s, flush=True)

def dump(dll, lo, hi):
    a = open(os.path.join(BK, dll), 'rb').read()
    b = open(os.path.join(PATCH, dll), 'rb').read()
    p('--- %s  0x%08X..0x%08X ---' % (dll, lo, hi))
    p('  英文: %r' % a[lo:hi])
    p('  补丁: %r' % b[lo:hi])

dump('Continuum_AE_8Bit.dll', 0x00FB7FD0, 0x00FB8020)
dump('Continuum_AE_8Bit.dll', 0x00FB3160, 0x00FB31C0)

# 找出所有落在该区间的写入
p()
p('该区间的写入记录：')
for dll, off, old, zh, sec, kind, avail in writes:
    if dll == 'Continuum_AE_8Bit.dll' and 0x00FB7FD0 <= off < 0x00FB8020:
        p('   0x%08X %-28r -> %-14r avail=%d kind=%s' % (off, old, zh, avail, kind))
for dll, off, old, zh, sec, kind, avail in writes:
    if dll == 'Continuum_AE_8Bit.dll' and 0x00FB3160 <= off < 0x00FB31C0:
        p('   0x%08X %-28r -> %-14r avail=%d kind=%s' % (off, old, zh, avail, kind))

# 统计：补丁文件里出现的「英文尾巴」——即某写入点之后仍残留的 ASCII
p()
p('=' * 90)
p('残留尾巴扫描：写入点之后、到下一个明显边界之间是否还有 ASCII 非 NUL 字节')
p('=' * 90)
susp = 0
for dll, off, old, zh, sec, kind, avail in writes:
    if susp >= 20:
        break
    b = open(os.path.join(PATCH, dll), 'rb').read()
    zb = zh.encode('gbk')
    tail = b[off + len(zb): off + min(avail, len(zb) + 24)]
    if any(0x20 <= c <= 0x7e for c in tail):
        susp += 1
        p('   %s 0x%08X %r -> %r  avail=%d 尾巴=%r' % (dll, off, old, zh, avail, tail))
p('发现带 ASCII 尾巴的写入: %d（上限 20）' % susp)

open(os.path.join(WORK, '_bytedump.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('DONE')

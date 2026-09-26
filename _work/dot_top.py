# -*- coding: utf-8 -*-
"""定位 patched_dll_d 中单词 Top 的所有出现，附上下文与可用容量"""
import os, re, sys, struct

D = r'D:\Programming project\插件汉化\_work\patched_dll_d'
TARGET = b'Top'
out = []

for fn in sorted(os.listdir(D)):
    p = os.path.join(D, fn)
    if not os.path.isfile(p):
        continue
    b = open(p, 'rb').read()
    i = 0
    while True:
        j = b.find(TARGET, i)
        if j < 0:
            break
        # 只取严格 NUL 包围（前边界也可能在头部）
        left_ok = (j == 0) or (b[j-1] == 0)
        right_ok = (j + len(TARGET) < len(b)) and (b[j+len(TARGET)] == 0)
        if left_ok and right_ok:
            pre = b[max(0, j-40):j].replace(b'\x00', b'|').decode('latin-1')
            post = b[j+len(TARGET)+1: j+len(TARGET)+1+40].replace(b'\x00', b'|').decode('latin-1')
            # 可用容量：向后找下一个 NUL 的剩余空间？实际 avail = 原始槽长
            # 原位是 'Top\0'，槽长至少 4
            out.append('%s @ %d\n   pre : %s\n   post: %s' % (fn, j, pre, post))
        i = j + 1

t = '\n'.join(out)
open(os.path.join(D, '..', '_dot_top.txt'), 'w', encoding='utf-8').write(t)
print('hits', len(out))

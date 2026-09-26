# -*- coding: utf-8 -*-
"""把 NO_DICT 里「明显是内部实现」的串滤掉，剩下的按频次列出来 —— 人工过一遍这些就够。
内部实现特征：AE SDK 套件名 / libjpeg 报错 / libxml 词法 / Win32 与 CRT 符号 /
HASP 授权字段 / 带 %d %s 0x 的格式化串 / 文件与注册表路径 / 纯大写常量。
"""
import os, re

W = r"D:\Programming project\插件汉化\_work"
BAD = re.compile(
    r'(AEGP|AE Plugin|PF [A-Z][a-z]+ Suite|PF Effect|PF Fill|PF Handle|PF Path|DRAWBOT|'
    r'Bogus|Huffman|JPEG|Quantiz|DCT|SOS|DHT|DQT|DAC|EMS|XMS|RST%d|'
    r'temporary file|Virtual array|Not implemented|not implemented|'
    r'HASP|SL-User|SL-Admin|AdminMode|NetworkSeat|SuperDog|'
    r'CDATA|ENTITY|IDREF|NMTOKEN|INCLUDE|SYSTEM|ATTLIST|US-ASCII|UTF-16|'
    r'WSA|WakeAll|SleepCondition|FreeSid|ADVAPI32|kernel32|gethost|hton|ntoh|'
    r'%[dsux]|0x|\\\\\.|SOFTWARE|\.dll|\.bwsx|\.tsws|\.bap|'
    r'^\d|^\W|CvMat|IplImage|Assertion|Seek failed|Read failed|Write failed|'
    r'Closed |Opened |Freed |Obtained |Invalid |Unsupported |Improper |Premature|'
    r'^\s*[A-Z0-9_ .-]{2,}$)')

rows = []
with open(os.path.join(W, '_buckets_patched_dll_d.tsv'), encoding='utf-8') as f:
    next(f)
    for ln in f:
        p = ln.rstrip('\n').split('\t')
        if len(p) >= 4 and p[0] == 'NO_DICT':
            rows.append((p[1], int(p[2]), p[4], p[5]))

ui = [r for r in rows if not BAD.search(r[0])]
ui.sort(key=lambda x: (-x[1], x[0]))
with open(os.path.join(W, '_ui_tail.txt'), 'w', encoding='utf-8') as f:
    f.write('NO_DICT %d 条，滤掉内部实现后剩 %d 条\n\n' % (len(rows), len(ui)))
    for n, c, av, ctx in ui:
        f.write('%-42s %3d avail=%-3s %s\n' % (n, c, av, ctx[:60]))
print('ui tail', len(ui), 'of', len(rows))

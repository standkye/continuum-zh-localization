# -*- coding: utf-8 -*-
"""最后一批「人工过一遍」的候选：NO_DICT 去掉
  - 已被 batch5 覆盖的效果名（BCC / BCC+ / FEC 家族）
  - BCC3*/BCC4*/BCC6*/BCC8* 这类**旧版本名**（可能是老预设按名索引的表，风险高，不动）
  - libjpeg / AE SDK / libxml / Win32 / HASP / 格式化串 / 文件名
剩下的按频次列出来，这些就是要手写译文的。
"""
import os, re, json

W = r"D:\Programming project\插件汉化\_work"
BAD = re.compile(
    r'(AEGP|AE Plugin|PF [A-Z][a-z]+ Suite|PF Effect|PF Fill|PF Handle|PF Path|DRAWBOT|'
    r'Bogus|Huffman|JPEG(?! Damage)|Quantiz|DCT|SOS|DHT|DQT|DAC|EMS|XMS|RST%d|'
    r'temporary file|Virtual array|Not implemented|not implemented|'
    r'HASP|SL-User|SL-Admin|AdminMode|NetworkSeat|SuperDog|'
    r'CDATA|ENTITY|IDREF|NMTOKEN|INCLUDE|SYSTEM|ATTLIST|US-ASCII|UTF-16|'
    r'WSA|WakeAll|SleepCondition|FreeSid|ADVAPI32|kernel32|gethost|hton|ntoh|'
    r'%[dsux]|0x|\\\\\.|SOFTWARE|\.dll|\.bwsx|\.tsws|\.bap|\.txt|\.ini|'
    r'^\d|^\W|CvMat|IplImage|Assertion|Seek failed|Read failed|Write failed|'
    r'Closed |Opened |Freed |Obtained |Invalid |Unsupported |Improper |Premature|'
    r'^\s*[A-Z0-9_ .-]{2,}$)')

b5 = json.load(open(os.path.join(W, 'batch5_ename.json'), encoding='utf-8'))
rows = []
with open(os.path.join(W, '_buckets_patched_dll_d.tsv'), encoding='utf-8') as f:
    next(f)
    for ln in f:
        p = ln.rstrip('\n').split('\t')
        if len(p) >= 6 and p[0] == 'NO_DICT':
            rows.append((p[1], int(p[2]), p[4], p[5]))

keep = []
for n, c, av, ctx in rows:
    if n in b5:
        continue
    if re.match(r'^(BCC|FEC)[0-9]', n):
        continue
    if BAD.search(n):
        continue
    keep.append((n, c, av, ctx))

keep.sort(key=lambda x: (-x[1], x[0]))
with open(os.path.join(W, '_ui_final.txt'), 'w', encoding='utf-8') as f:
    f.write('待人工定夺 %d 条（NO_DICT %d － batch5 %d － 旧版名 － 内部实现）\n\n'
            % (len(keep), len(rows), len(b5)))
    for n, c, av, ctx in keep:
        f.write('%-44s %3d av=%-3s %s\n' % (n, c, av, ctx[:56]))
print('final ui candidates', len(keep))

# -*- coding: utf-8 -*-
"""正确解析 .aex 的 MIB8eman 段，判定中文编码；并与本机已装文件对比。"""
import os

D = r'D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0'
INST = r'C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum'
out = []
def say(*a):
    out.append(' '.join(str(x) for x in a))

MARK = b'MIB8eman'

def find_seg(d):
    """返回 (name_bytes, tag_or_None)。"""
    j = d.find(MARK)
    if j < 0:
        return None, None
    # j+16 是长度字节 + 字符串
    k = j + 16
    if k >= len(d):
        return None, None
    n = d[k]
    body = d[k+1:k+1+n]
    return body, d[j:j+16]

def classify(seg):
    has_u8 = has_gbk = False
    for i in range(len(seg)):
        ch = seg[i]
        if ch < 0x80:
            continue
        if 0xE4 <= ch <= 0xE9 and i+2 < len(seg) and 0x80 <= seg[i+1] <= 0xBF and 0x80 <= seg[i+2] <= 0xBF:
            has_u8 = True
        if 0xB0 <= ch <= 0xF7 and i+1 < len(seg) and 0xA1 <= seg[i+1] <= 0xFE:
            has_gbk = True
    if has_u8 and not has_gbk: return 'UTF8'
    if has_gbk and not has_u8: return 'GBK'
    if has_u8 and has_gbk: return 'MIX?'
    return 'ASCII'

files = sorted(f for f in os.listdir(D) if f.lower().endswith('.aex'))
stat = {}
samples = {}
for f in files:
    d = open(os.path.join(D, f), 'rb').read()
    body, tag = find_seg(d)
    if body is None:
        stat['NO_SEG'] = stat.get('NO_SEG', 0) + 1
        continue
    c = classify(body)
    stat[c] = stat.get(c, 0) + 1
    samples.setdefault(c, [])
    if len(samples[c]) < 10:
        samples[c].append((f, body))

say('交付目录 .aex: %d 个' % len(files))
say('分类统计: %r' % stat)
say('')
for k in sorted(samples):
    say('--- %s 样例 ---' % k)
    for f, b in samples[k]:
        try:
            g = b.decode('gbk')
        except Exception:
            g = '<gbk fail>'
        try:
            u = b.decode('utf-8')
        except Exception:
            u = '<utf8 fail>'
        say('   %-30s raw=%r  gbk=%r  utf8=%r' % (f, b, g, u))
    say('')

# 与已装文件对比 3 个样例
say('=== 与已装文件对比 ===')
for f in ['BCCBlur.aex']:
    ip = os.path.join(INST, f)
    dp = os.path.join(D, f)
    say('已装存在:', os.path.exists(ip), ip)
    if os.path.exists(ip):
        di = open(ip, 'rb').read(); dd = open(dp, 'rb').read()
        say('  已装 size=%d  交付 size=%d' % (len(di), len(dd)))
        bi, _ = find_seg(di); bd, _ = find_seg(dd)
        say('  已装 seg=%r' % bi)
        say('  交付 seg=%r' % bd)

open(r'D:\Programming project\插件汉化\_work\_aex_enc.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('done')

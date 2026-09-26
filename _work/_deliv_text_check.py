# -*- coding: utf-8 -*-
"""交付目录文本文件收尾：补 BOM / 校验编码 / 检查 bat 是否纯 ASCII。"""
import os

D = r'D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0'
out = []
def say(*a):
    out.append(' '.join(str(x) for x in a))

# 1) 说明.txt 补回 UTF-8 BOM（原版有 BOM；Write 工具不带 BOM。
#    中文 Windows 记事本会把无 BOM 的 UTF-8 当 GBK → 乱码）
p = os.path.join(D, '说明.txt')
b = open(p, 'rb').read()
if not b.startswith(b'\xef\xbb\xbf'):
    open(p, 'wb').write(b'\xef\xbb\xbf' + b)
    say('说明.txt: 已补 UTF-8 BOM')

# 2) 逐个报告文本文件的编码判定
say('')
say('--- 交付目录文本文件编码 ---')
for f in sorted(os.listdir(D)):
    if not f.lower().endswith(('.txt', '.bat')):
        continue
    p = os.path.join(D, f)
    b = open(p, 'rb').read()
    bom = b[:3] == b'\xef\xbb\xbf'
    verdict = []
    for enc in ('utf-8-sig', 'gbk', 'ascii'):
        try:
            t = b.decode(enc)
            # 判定是否"像正常中文文本"
            ok = not any('\ufffd' in t for _ in [0])
            verdict.append(enc)
        except Exception:
            pass
    ascii_only = all(c < 0x80 for c in b)
    say('   %-28s BOM=%-5s 纯ASCII=%-5s 可解码=%r'
        % (f, bom, ascii_only, verdict))

# 3) bat 必须纯 ASCII（否则 cmd 按字节拆行会崩）——逐行找非 ASCII
say('')
say('--- .bat 非 ASCII 行检查 ---')
for f in sorted(os.listdir(D)):
    if not f.lower().endswith('.bat'):
        continue
    p = os.path.join(D, f)
    b = open(p, 'rb').read()
    bad = []
    for i, line in enumerate(b.split(b'\r\n')):
        if any(c >= 0x80 for c in line):
            bad.append((i + 1, line[:70]))
    say('   %-30s 非ASCII行 %d' % (f, len(bad)))
    for i, l in bad[:6]:
        say('        L%d: %r' % (i, l))

open(r'D:\Programming project\插件汉化\_work\_deliv_text_check.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('done')

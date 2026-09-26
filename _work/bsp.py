# -*- coding: utf-8 -*-
import os, re
from collections import Counter
root = r"C:\ProgramData\BorisFX\Continuum\19\Presets"
out = []
f = None
for dp, dns, fns in os.walk(root):
    for fn in fns:
        if fn.lower().endswith('.bsp'):
            f = os.path.join(dp, fn); break
    if f: break
out.append("样本: " + f)
t = open(f, 'rb').read().decode('utf-8', 'ignore')
out.append("前 1800 字符:")
out.append(t[:1800])
out.append("\n标签统计（取 200 个文件）:")
c = Counter(); n = 0
for dp, dns, fns in os.walk(root):
    for fn in fns:
        if not fn.lower().endswith(('.bsp', '.bap')): continue
        n += 1
        if n > 200: break
        try:
            s = open(os.path.join(dp, fn), 'rb').read().decode('utf-8', 'ignore')
        except Exception: continue
        for m in re.finditer(r'<(/?[A-Za-z_][A-Za-z0-9_]*)', s):
            c[m.group(1)] += 1
for k, v in c.most_common(40):
    out.append(f"  {k:24s} {v}")
open(r"D:\Programming project\插件汉化\_work\bsp_report.txt", "w", encoding='utf-8').write("\n".join(out))

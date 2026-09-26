# -*- coding: utf-8 -*-
"""词素统计 + 排除枚举值 + 输出待翻译参数名"""
import os, re, json
from collections import Counter

WORK = r"D:\Programming project\插件汉化\_work"
root = r"C:\ProgramData\BorisFX\Continuum\19\Presets"
out = []

params = json.load(open(os.path.join(WORK, 'param_ok.json'), encoding='utf-8'))

# 枚举值（<parameter ...>值</parameter>）—— 改了会破坏预设，必须排除
E = Counter()
NAME = Counter()
for dp, dns, fns in os.walk(root):
    for fn in fns:
        if not fn.lower().endswith(('.bsp', '.bap')):
            continue
        try:
            t = open(os.path.join(dp, fn), 'rb').read().decode('utf-8', 'ignore')
        except Exception:
            continue
        for m in re.finditer(r'<parameter[^>]*>(.*?)</parameter>', t, re.S):
            v = m.group(1).strip()
            if 1 <= len(v) <= 60 and all(32 <= ord(c) < 127 for c in v):
                E[v] += 1
out.append(f"枚举值集合大小: {len(E)}")
both = [s for s in params if s in E]
out.append(f"既是参数名又是枚举值的: {len(both)}")
out.append("  例: " + ", ".join(both[:25]))

final = [s for s in params if s not in E]
out.append(f"\n最终待翻译参数名: {len(final)}")
json.dump(final, open(os.path.join(WORK, 'params_to_translate.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

# 词素统计
tok = Counter()
for s in final:
    for t in s.split():
        tok[t] += 1
out.append(f"\n不同词素: {len(tok)}")
out.append("高频词素（前 300）:")
for t, c in tok.most_common(300):
    out.append(f"  {c:5d}  {t}")

json.dump({t: c for t, c in tok.most_common()},
          open(os.path.join(WORK, 'tokens.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
open(os.path.join(WORK, 'tok_report.txt'), 'w', encoding='utf-8').write("\n".join(out))

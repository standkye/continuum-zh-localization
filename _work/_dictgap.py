# -*- coding: utf-8 -*-
"""查这 4 个仍为英文的效果名在词典里到底缺什么键。"""
import sys
sys.path.insert(0, r"D:\Programming project\插件汉化\_work")
import names_manual

targets = ['BCC 3 Way Color Grade', 'BCC Posterize', 'BCC Alpha Process',
           'BCC Alpha Pixel Noise OBS', 'BCC Extruded EPS', 'BCC Halftone',
           'BCC Match Grain', 'BCC Match Move', 'BCC Pan and Zoom',
           'BCC Title Studio', 'BCC Beat Reactor']

out = []
for t in targets:
    hits = [k for k in names_manual.NAMES if k.strip() == t.strip() or k.strip() == t.strip() + ' OBSOLETE']
    out.append(f"{t!r}")
    for h in hits:
        out.append(f"     键 {h!r} -> {names_manual.NAMES[h]!r}")
    if not hits:
        # 模糊找
        cand = [k for k in names_manual.NAMES if t.split()[-1].lower() in k.lower()]
        out.append(f"     无精确键；模糊候选 {cand[:6]}")

out.append(f"\nNAMES 总键数 {len(names_manual.NAMES)}")
out.append("含 'Process' 的键: " + repr([k for k in names_manual.NAMES if 'Process' in k]))
out.append("含 'Posterize' 的键: " + repr([k for k in names_manual.NAMES if 'Posterize' in k]))
out.append("含 '3 Way' 的键: " + repr([k for k in names_manual.NAMES if '3 Way' in k]))
out.append("含 'OBS' 的键: " + repr([k for k in names_manual.NAMES if 'OBS' in k][:12]))

open(r"D:\Programming project\插件汉化\_work\_dictgap.txt", 'w', encoding='utf-8').write("\n".join(out))
print("done")

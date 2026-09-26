# -*- coding: utf-8 -*-
import os, json
WORK = r"D:\Programming project\插件汉化\_work"
PKG = r"D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0"

eff = json.load(open(os.path.join(WORK, 'effect_zh.json'), encoding='utf-8'))
pz = json.load(open(os.path.join(WORK, 'param_zh.json'), encoding='utf-8'))

# 效果名：中文 -> 英文
lines = ["Continuum 效果名 中英对照表（中文 -> 英文原名）",
         "=" * 56, ""]
rows = []
seen = set()
for fn, items in sorted(eff.items()):
    for (en, zh, size, off, cap) in items:
        key = (zh, en.strip())
        if key in seen:
            continue
        seen.add(key)
        rows.append((zh, en.strip()))
rows.sort(key=lambda r: (len(r[0]), r[0]))
for zh, en in rows:
    lines.append(f"{zh:<24s} {en}")
open(os.path.join(PKG, '效果名对照表.txt'), 'w', encoding='utf-8').write("\n".join(lines))

# 参数名：中文 -> 英文
lines2 = ["Continuum 参数名 中英对照表（中文 -> 英文原名）",
          f"共 {len(pz)} 条",
          "=" * 56, ""]
rows2 = sorted(pz.items(), key=lambda kv: (len(kv[1]), kv[1]))
for en, zh in rows2:
    lines2.append(f"{zh:<20s} {en}")
open(os.path.join(PKG, '参数名对照表.txt'), 'w', encoding='utf-8').write("\n".join(lines2))

# 统计
rep = [f"效果名 {len(rows)} 条", f"参数名 {len(pz)} 条"]
open(os.path.join(WORK, 'tables_log.txt'), 'w', encoding='utf-8').write("\n".join(rep))

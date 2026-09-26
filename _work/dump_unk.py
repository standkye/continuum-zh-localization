# -*- coding: utf-8 -*-
import json, os
WORK = r"D:\Programming project\插件汉化\_work"
unk = json.load(open(os.path.join(WORK, 'unknown_tokens.json'), encoding='utf-8'))
items = sorted(unk.items(), key=lambda x: -x[1])
lines = []
buf = []
for i, (w, c) in enumerate(items):
    buf.append(f"{w}({c})")
    if len(buf) == 5:
        lines.append("  " + "  ".join(buf)); buf = []
if buf:
    lines.append("  " + "  ".join(buf))
open(os.path.join(WORK, 'unk_list.txt'), 'w', encoding='utf-8').write(
    f"共 {len(items)} 个未登录词\n" + "\n".join(lines))

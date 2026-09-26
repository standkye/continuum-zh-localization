# -*- coding: utf-8 -*-
import os, sys, re
sys.path.insert(0, r"D:\Programming project\插件汉化\_work")
from dict_zh import TOKENS as T1, EFFECT_OVERRIDE
from dict_extra import EXTRA
TOKENS = {}
TOKENS.update(T1)
TOKENS.update(EXTRA)
lines = []
for w in ["Pixel", "Sub", "SW", "Add", "Sampler", "CA", "Frames", "Var", "Rot", "Tuning"]:
    lines.append(f"{w:10s} dict_zh={T1.get(w)!r}  合并后={TOKENS.get(w)!r}")
lines.append("")
lines.append("词典里含 Pixel 的键: " + str([k for k in TOKENS if 'Pix' in k]))
lines.append("词典里含 Sub 的键: " + str([k for k in TOKENS if k.lower().startswith('sub')]))
lines.append("词典里含 SW 的键: " + str([k for k in TOKENS if k.upper() == 'SW']))
lines.append("")
import trans_probe  # noqa
open(r"D:\Programming project\插件汉化\_work\dbg_out.txt", "w", encoding='utf-8').write("\n".join(lines))

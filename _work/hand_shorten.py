# -*- coding: utf-8 -*-
"""Shorten the hand translations that overflow their DLL slot."""
import io, os
W = r"D:\Programming project\插件汉化\_work"

FIX = {
    # 8-byte slot -> 7 GBK bytes = 3 汉字 (+1)
    "BG Hue": "背景色",
    "FG Blur": "前景糊",
    "FG Hue": "前景色",
    "Opacity": "不透明",
    "PreBlur": "前模糊",
    "Repeats": "重复数",
    "Size FX": "大小FX",
    "HV Bias": "HV偏移",
    # 16-byte slot -> 15 GBK bytes
    "Fade Start - CL": "合灯淡出起点",
    "Opacity FX Wipe": "不透特效擦除",
    "Wrap Apply Mode": "光融应用模式",
    "L1 Spin": "灯1自旋",
    "L1 Type": "灯1类型",
    "L2 Spin": "灯2自旋",
    "L2 Type": "灯2类型",
    "L3 Spin": "灯3自旋",
    "L3 Type": "灯3类型",
}

def slot_of(s):
    return max(8, -(-(len(s) + 1) // 8) * 8)

for i in range(1, 11):
    p = os.path.join(W, "hand_%02d.txt" % i)
    lines = io.open(p, encoding="utf-8").read().split("\n")
    out, n = [], 0
    for line in lines:
        if "|" in line:
            en, zh = line.split("|", 1)
            if en in FIX:
                line = en + "|" + FIX[en]
                n += 1
        out.append(line)
    if n:
        io.open(p, "w", encoding="utf-8").write("\n".join(out))
        print("hand_%02d.txt: %d lines shortened" % (i, n))

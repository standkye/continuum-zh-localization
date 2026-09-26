# -*- coding: utf-8 -*-
"""最终覆盖（优先级最高）+ 词组规则"""

FIX = {
    "Type": "类型",          # 参数里的 Type = 类型（不是"打字"）
    "Specular": "镜面",       # 与 Highlight(高光) 区分
    "Advance": "前进",
    "Value": "值",
    "More": "更多",
    "Settings": "设置",
    "Sub": "减",             # (Sub) = 减去
    "Off": "关",
    "On": "开",
    "Points": "点",
    "Layer": "图层",
    "Group": "组",
    "Random": "随机",
}

# 双词组合规则：(前一个词, 当前词) -> 译文（"" 表示省略）
BIGRAM = {
    ("Fall", "Off"): "",
    ("Far", "Off"): "",
    ("Cut", "Off"): "",
    ("Add", "To"): "",
    ("Apply", "To"): "",
    ("Apply", "From"): "",
    ("To", "Checkbox"): "",
    ("Motion", "Blur"): "模糊",
    ("Light", "Strobe"): "频闪",
}

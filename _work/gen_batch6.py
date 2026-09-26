# -*- coding: utf-8 -*-
"""批量补词 · 第 6 批：BCC 光晕（Lens Flare 3D）/ 节拍反应器 / 光学 / 杂项里
**确实是 AE 界面标签**、但词典一直没收的那批名字。全部手写，逐个做容量自检。
"""
import os, re, json, collections

W = r"D:\Programming project\插件汉化\_work"
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
DLLS = ['Continuum_AE_8Bit.dll', 'Continuum_AE_16Bit.dll', 'Continuum_AE_Float.dll',
        'Continuum_Common_AE.dll', 'Continuum_3DObjects_AE.dll', 'BCCPlus.dll']
TOKEN_RE = re.compile(rb'[\x20-\x7e]+')

# ---- 手写译文（只收确定是界面标签的；内部实现串一律不收）----
UI = {
    # 节拍反应器 / 音频
    "Beat Reactor": "节拍反应器",
    "Effect Presets & Docs": "效果预设与文档",
    "Single Path": "单路径",
    "Inverse Path": "反向路径",
    "Audio Graph Options": "音频曲线选项",
    "Audio Spectrum Options": "音频频谱选项",
    "Audio Apply Options A": "音频应用选项A",
    "Audio Apply Options B": "音频应用选项B",
    "Audio Apply Options C": "音频应用选项C",
    "Host Sound Layer": "宿主声音图层",
    "External File": "外部文件",
    "Host Layer": "宿主图层",
    "Auto-Shimmer": "自动微光",
    # 三维镜头光晕：元素类型 / 贴图 / 光源
    "Flare": "光晕",
    "Light Flicker": "光闪烁",
    "Chromatic Aberration": "色差",
    "Orbs": "光球",
    "Rays": "光线",
    "Glows": "辉光",
    "Hollows": "空环",
    "Polygons": "多边形",
    "Discs": "圆盘",
    "Stripe": "条纹",
    "Chroma Fan": "色度扇",
    "Chroma Hoop": "色度环",
    "Elliptical Caustic": "椭圆焦散",
    "Star Caustic": "星形焦散",
    "Faded Ring": "渐隐环",
    "Flare Trigger": "光晕触发",
    "Texture Custom Layer": "纹理自定义图层",
    "Orb Custom Layer": "光球自定义图层",
    "Background Map Layer": "背景贴图图层",
    "Obscuration Map Layer": "遮挡贴图图层",
    "Location Map Layer": "位置贴图图层",
    "Luma Map": "亮度贴图",
    "Edge Map": "边缘贴图",
    "Scale By Distance": "按距离缩放",
    "Built-in Camera": "内置相机",
    "Built-in": "内置",
    "Light Source 1": "光源1",
    "Light Source 2": "光源2",
    "Light Source 3": "光源3",
    # 光学 / 通道 / 常用短标签
    "Edge": "边缘",
    "Luminance": "亮度",
    "Optical Flow": "光流",
    "Lens Correction": "镜头校正",
    "Spill": "溢色",
    "Text Color": "文字颜色",
    "Transform": "变换",
    "Geometry": "几何",
    "Gradient": "渐变",
    "Colorize": "着色",
    "Composite": "合成",
    "Display": "显示",
    "Circle": "圆形",
    "Chaos": "混沌",
    "Back": "背面",
    "Advanced": "高级",
    "Absolute": "绝对",
    "Current": "当前",
    "Main": "主",
    "None": "无",
    "Time": "时间",
    "Comp": "合成",
    "Point": "点",
    "Crop": "裁切",
    "Corner Pins": "边角钉",
    "Source Pins": "源钉",
    "AE Mask": "AE遮罩",
    "Host Mask": "宿主遮罩",
    "Apply Parameter": "应用参数",
    "Animation Tuning": "动画微调",
    "Auto Analyze": "自动分析",
    "Analyzing Motion": "正在分析运动",
    "XPosition": "X位置",
    "YPosition": "Y位置",
    "Clip": "裁切",
    # 少数漏掉的 BCC 名（属于 2026 版新增，.aex 名字表里没有）
    "BCC Presets": "BCC 预设",
    "BCC Keyboard Shortcuts": "BCC 键盘快捷键",
    "BCC Error": "BCC 错误",
    "BCC Fast Blur": "BCC 快速模糊",
    "BCC Light Rays": "BCC 光线",
    "BCC Card Array": "BCC 卡片阵列",
    "BCC Film Glow Fast": "BCC 快速胶片辉光",
    "BCC Wipes and Patterns": "BCC 擦除与图案",
    "BCC JPEG Damage": "BCC JPEG 损伤",
    "BCC Composite Tester": "BCC 合成测试",
    "BCC Lens Flare 3D Ray Type": "BCC 三维光晕光线类型",
}

# 窄槽退路
SHORT = {
    "Effect Presets & Docs": "预设与文档",
    "Audio Graph Options": "音频曲线",
    "Audio Spectrum Options": "音频频谱",
    "Audio Apply Options A": "音频应用A",
    "Audio Apply Options B": "音频应用B",
    "Audio Apply Options C": "音频应用C",
    "Texture Custom Layer": "纹理图层",
    "Orb Custom Layer": "光球图层",
    "Background Map Layer": "背景图层",
    "Obscuration Map Layer": "遮挡图层",
    "Location Map Layer": "位置图层",
    "Scale By Distance": "距离缩放",
    "Chromatic Aberration": "色差",
    "Elliptical Caustic": "椭圆焦散",
    "Star Caustic": "星形焦散",
    "Built-in Camera": "内置相机",
    "Light Source 1": "光源1",
    "Light Source 2": "光源2",
    "Light Source 3": "光源3",
    "Lens Correction": "镜头校正",
    "BCC Keyboard Shortcuts": "BCC 快捷键",
    "BCC Lens Flare 3D Ray Type": "BCC 光晕光线",
    "BCC Wipes and Patterns": "BCC 擦除图案",
    "Analyzing Motion": "分析运动",
    "Animation Tuning": "动画微调",
}

# ---- 容量自检 ----
occ = collections.defaultdict(list)
for dll in DLLS:
    p = os.path.join(BK, dll)
    if not os.path.exists(p):
        continue
    d = open(p, 'rb').read()
    for m in TOKEN_RE.finditer(d):
        s, e = m.span()
        if s > 0 and d[s - 1] != 0:
            continue
        if e >= len(d) or d[e] != 0:
            continue
        t = m.group().decode('ascii', 'replace')
        if t in UI:
            j = e
            while j < len(d) and d[j] == 0:
                j += 1
            occ[t].append(j - s)

good, bad, miss = {}, [], []
for t, zh in sorted(UI.items()):
    av = occ.get(t)
    if not av:
        miss.append(t)
        continue
    if len(zh.encode('gbk')) + 1 <= min(av):
        good[t] = zh
        continue
    sh = SHORT.get(t)
    if sh and len(sh.encode('gbk')) + 1 <= min(av):
        good[t] = sh
        continue
    bad.append((t, zh, len(zh.encode('gbk')) + 1, min(av)))

print('手写 %d 条；写入 %d 条，源里找不到 %d 条，容量放不下 %d 条'
      % (len(UI), len(good), len(miss), len(bad)))
for t in miss:
    print('   ? 源里无此串: %s' % t)
for t, zh, need, av in bad:
    print('   ! 放不下 %-42s %-18s need=%d avail=%d' % (t, zh, need, av))

json.dump(good, open(os.path.join(W, 'batch6_ui.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=0)
print('写出 batch6_ui.json  %d 条' % len(good))

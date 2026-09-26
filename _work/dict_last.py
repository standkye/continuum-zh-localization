# -*- coding: utf-8 -*-
"""Last-mile dictionary (Continuum AE plugin Chinese patch).

Covers the words that the earlier layers (dict_zh / dict_extra / dict_extra2 /
dict_fix / dict_more) never got around to -- found by ranking the residual
Latin words in the composed output (_work/latin_rank.txt).

LAST      : single morphemes.  Highest priority, overrides every other layer.
PHRASES2  : whole-string translations where word-by-word composition reads
            like machine translation.  Also highest priority.
"""

LAST = {
    # ---------- 括号 / 标点（作为独立 token 参与拼接）----------
    "(": "(", ")": ")",

    # ---------- 小词 ----------
    "for": "", "at": "", "as": "为", "with": "为", "per": "每",
    "Do": "执行", "Used": "已用", "Apart": "间隔", "On": "开",

    # ---------- 尺寸 / 形状 ----------
    "Width": "宽度", "Height": "高度", "Frames": "帧", "Fields": "场",
    "Elliptical": "椭圆", "Uniform": "均匀", "Partial": "部分",
    "Arc": "圆弧", "Contour": "轮廓", "Form": "形状",
    "Completeness": "完整度", "Horizontally": "水平", "Scaler": "缩放器",
    "Spat": "空间", "secs": "秒", "Vertically": "垂直",

    # ---------- 颜色 / 电平 ----------
    "Bright": "亮度", "WhiteLevel": "白电平", "BlackLevel": "黑电平",
    "Knee": "拐点", "Highlights": "高光", "Highlight": "高光",
    "Space": "空间", "Loops": "循环", "Cloudiness": "云量",

    # ---------- 抠像 / 通道 ----------
    "Holdout": "遮挡", "Erode": "腐蚀", "Chokes": "收缩",
    "Centers": "中心", "Convergence": "汇聚",

    # ---------- 三维 / 变换 ----------
    "axis": "轴", "Axis": "轴", "Sided": "面", "sided": "面",
    "Card": "卡片", "Cards": "卡片", "Screen": "屏幕", "System": "系统",
    "Origin": "原点", "Facing": "朝向", "Texture": "纹理",
    "Latitude": "纬度", "Longitude": "经度", "Vectors": "矢量",
    "Translate": "平移", "Create": "创建", "Cut": "剪切",
    "Tiles": "平铺", "Duplication": "复制", "Handling": "处理",

    # ---------- 粒子 ----------
    "Spawn": "生成", "Spawned": "已生成", "Probability": "概率",
    "Interact": "交互", "Interaction": "交互", "Independent": "独立",
    "Seeds": "种子", "Knots": "节点", "Knot": "节点",
    "Luminance": "亮度", "Strands": "丝线", "Sources": "源",
    "Producer": "发生器", "Shard": "碎片", "Resize": "缩放",
    "Multiple": "多个", "Materials": "材质", "Numbers": "数值",
    "Beam": "光束", "Plank": "木板", "Sampler": "采样器",
    "Flares": "光晕", "Gust": "阵风",

    # ---------- 运动 / 时间 ----------
    "Keyframes": "关键帧", "Repeat": "重复", "Scroll": "滚动",
    "Follows": "跟随", "Increase": "增加", "Faster": "更快",
    "Analysis": "分析", "Stabilization": "稳定", "Optimize": "优化",
    "Algorithm": "算法", "Fadein": "淡入", "Fadeout": "淡出",
    "sec": "秒", "second": "秒", "frames": "帧", "prog": "进度",
    "evolve": "演化", "bpm": "拍/分", "lengths": "长度",

    # ---------- 程度 / 比较 ----------
    "Closest": "最近", "Farthest": "最远", "Largest": "最大",
    "Smallest": "最小", "Harder": "更强", "Fractional": "小数",
    "Blurs": "模糊", "Pixelation": "像素化", "Wipes": "擦除",
    "Diffs": "差异", "Wild": "通配", "Guides": "参考线",
    "Scope": "示波器", "Media": "媒介", "Data": "数据",
    "Log": "日志", "Open": "打开", "Correct": "校正",
    "Non": "非", "Square": "方形", "Sub": "减", "Add": "加",
    "Spreading": "扩散", "Smokiness": "烟雾浓度", "Gustiness": "阵风强度",
    "Softess": "柔和度", "Spirality": "螺旋度", "Taffiness": "黏稠度",
    "Smoke": "烟雾", "Pull": "拉力", "Inward": "向内",
    "Around": "绕", "Unwrap": "展开", "Egde": "边缘",
    "Edge": "边缘", "Remove": "移除", "Name": "名称",
    "Starts": "起始", "Parameter": "参数", "Around2": "绕",

    # ---------- BCC Cast Shadow 的分组后缀（旧词典错翻成"低"/"色差"）----------
    # IP = Image Plane 图像平面 / SP = Shadow Plane 阴影平面
    # LT = Light 灯光 / CL = Comp Light 合成灯光
    "IP": "图像平面", "SP": "阴影平面", "LT": "灯光", "CL": "合成灯光",

    # ---------- 保留拉丁（行业标准缩写 / 品牌）----------
    "RGB": "RGB", "LED": "LED", "IRE": "IRE", "FOV": "视场角",
    "ROI": "区域", "HSL": "HSL", "XYZ": "XYZ", "Mocha": "Mocha",
    "Primatte": "Primatte", "Mipmap": "Mipmap", "OpenFX": "OpenFX",
}

# ---------------------------------------------------------------------------
# 整串翻译：逐词拼出来会像机翻的，这里手写
# ---------------------------------------------------------------------------
PHRASES2 = {
    # BCC Cast Shadow 四个分组（位置/旋转/不透明度/衰减）
    "Position XY - LT": "灯光位置XY",
    "Position Z - LT": "灯光位置Z",
    "Opacity - LT": "灯光不透明度",
    "Opacity - IP": "图像不透明度",
    "Position XY - IP": "图像平面位置XY",
    "Position Z - IP": "图像平面位置Z",
    "Rotate X - IP": "图像平面旋转X",
    "Rotate Y - IP": "图像平面旋转Y",
    "Rotate Z - IP": "图像平面旋转Z",
    "Position XY - SP": "阴影平面位置XY",
    "Position Z - SP": "阴影平面位置Z",
    "Rotate X - SP": "阴影平面旋转X",
    "Rotate Y - SP": "阴影平面旋转Y",
    "Rotate Z - SP": "阴影平面旋转Z",
    "Color - CL": "合成灯光颜色",
    "Fade Start - CL": "合成灯光淡出开始",
    "Fade Length - CL": "合成灯光淡出长度",
    "Transmission - CL": "合成灯光透射",
    "Softness Y Ratio - CL": "合成灯光柔和度Y比率",
    "Sub Beam Count": "子光束数量",
    "Rotate Around Shape Center": "绕形状中心旋转",
    "Soften Inward": "向内柔化",
    "Steps Used": "已用步数",
    "Smoke Spreading Angle": "烟雾扩散角度",
    "Wind Gustiness": "阵风强度",
    "Wild Cards": "通配符",
    "WaveForm": "波形",
    "Create Rays From": "光线来源",
    "Channel for B&W": "黑白通道",
    "Effect on Parameter": "效果作用于参数",
    "Use Alpha for Blur": "使用阿尔法进行模糊",
    "Lock to Whole Numbers": "锁定为整数",
    "Num Keyframes per second": "每秒关键帧数",
    "Name Starts With": "名称开头为",
    "Highlight On Scope": "示波器高光",
    "Inter-band Radius Scale": "带间半径缩放",
    "Enable Bright/Contrast": "启用亮度/对比度",
    "Do Remove Effect": "执行移除效果",
    "Lock Centers to Outgoing": "锁定中心到出射",
    "Two-sided Lighting": "双面光照",
    "Double Sided Lighting": "双面光照",
    "Auto Evolve Speed (evolve/sec)": "自动演化速度(演化/秒)",
    "Move Speed (prog/sec)": "移动速度(进度/秒)",
    "Time Resolution (frames/sec)": "时间分辨率(帧/秒)",
    "Wind Gust: XYZ Individual": "阵风:XYZ独立",
    "PixelChooser / Mocha": "像素选取/Mocha",
    "Mocha Data0": "Mocha数据0",
    "Primatte Data": "Primatte数据",
    "Open Log File": "打开日志文件",
    "Optimize Algorithm": "优化算法",
}

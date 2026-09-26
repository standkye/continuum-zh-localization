# -*- coding: utf-8 -*-
"""第五轮补词：预设语料里「词典没收录、却仍以英文标签出现」的 89 个参数名。
手写译文 → 合并进 gap_zh.json / gap_zh_short.json（fix4_dll.py 已加载这两个文件，
所以不需要改动补丁脚本），并逐个做容量自检。
"""
import os, re, json, collections

WORK = r"D:\Programming project\插件汉化\_work"
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
TOKEN_RE = re.compile(rb'[\x20-\x7e]+')
DLLS = ['Continuum_AE_8Bit.dll', 'Continuum_AE_16Bit.dll', 'Continuum_AE_Float.dll',
        'Continuum_Common_AE.dll', 'Continuum_3DObjects_AE.dll', 'BCCPlus.dll']

GAP2 = {
    "Edge Enhancement": "边缘增强",
    "View": "视图",
    "3D Slice Resolution": "三维切片分辨率",
    "3D Stack Resolution": "三维堆叠分辨率",
    "Composite Style": "合成样式",
    "Particle Illusion Data": "粒子幻象数据",
    "Edge Type": "边缘类型",
    "Flicker On": "闪烁开",
    "Shake X": "抖动X",
    "Shake Y": "抖动Y",
    "Displacement Map on": "置换贴图开",
    "Start on Frame": "起始帧",
    "Overdrive Soften": "过驱动柔化",
    "Brightness Variance": "亮度变化",
    "Overdrive Amount": "过驱动数量",
    "Sweep": "扫掠",
    "Sweep Field": "扫掠场",
    "Glow Offset": "光晕偏移",
    "Glow Channel": "光晕通道",
    "Blue Offset": "蓝偏移",
    "Green Offset": "绿偏移",
    "Red Offset": "红偏移",
    "Wipe": "擦除",
    "Frame Separation": "帧分离",
    "Glow Scale": "光晕缩放",
    "Map Behavior": "贴图行为",
    "Opaque Glow": "不透明光晕",
    "Emboss On": "浮雕开",
    "PixelChooser Interaction": "像素选取交互",
    "Scale Borders": "缩放边框",
    "Position Clamp": "位置钳制",
    "Shake Speed": "抖动速度",
    "Link": "链接",
    "Path Scale": "路径缩放",
    "Separation": "分离",
    "Particle Velocity Variance": "粒子速度变化",
    "Reverse Transition": "反向过渡",
    "Drop Shape": "水滴形状",
    "Affects": "影响",
    "Black Source": "黑色源",
    "3D Layer Rotates Emitter": "三维图层旋转发射器",
    "Emboss Channel": "浮雕通道",
    "Filter Apply Mix": "滤镜应用混合",
    "Highlight Balance": "高光平衡",
    "Image Roll": "图像滚动",
    "Invert Luma": "反相亮度",
    "Layer A Type": "图层A类型",
    "Lens Type": "镜头类型",
    "Softer Cartoon": "柔和卡通",
    "3D Velocity": "三维速度",
    "Color Remapping": "颜色重映射",
    "Light Cone Width": "光锥宽度",
    "Remap Mixing": "重映射混合",
    "Position Offset Feedback": "位置偏移反馈",
    "Reflect Edges": "反射边缘",
    "Render Misalignment": "渲染错位",
    "3D Stroke": "三维描边",
    "Alpha From Channel": "从通道取阿尔法",
    "White Boost": "白色提升",
    "End Jitter 1": "末端抖动1",
    "Reverse Effect": "反向效果",
    "Start Jitter 1": "起始抖动1",
    "View Iris Shape": "查看光圈形状",
    "Composite on Original": "合成到原图",
    "Final Apply Mode": "最终应用模式",
    "Ray Center": "光线中心",
    "Remove Area": "移除区域",
    "Make Key From": "生成遮罩源",
    "Region of Interest Bot-Right": "感兴趣区右下",
    "Region of Interest Top-Left": "感兴趣区左上",
    "Shadow Direction": "阴影方向",
    "Shadow Elevation": "阴影仰角",
    "Clip to Output Black": "裁切到输出黑",
    "Clip to Output White": "裁切到输出白",
    "Glow Aspect": "光晕宽高比",
    "Hard Clip": "硬裁切",
    "Soft Clip": "软裁切",
    "Threshold Soften": "阈值柔化",
    "View Current Matte": "查看当前遮罩",
    "Dropout Field": "丢帧场",
    "Dropout Length": "丢帧长度",
    "Dropout Start Frame": "丢帧起始帧",
    "Lights Cast Shadows": "灯光投射阴影",
    "Scale Plane 3": "缩放平面3",
    "Spotlight 1 On": "聚光灯1开",
    "Top": "顶",
    "On": "开",
}

# 长词短译名（放不下时回退）
SHORT2 = {
    "3D Layer Rotates Emitter": "三维发射器",
    "Particle Velocity Variance": "粒子速度变化",
    "Region of Interest Bot-Right": "感兴趣区右下",
    "Region of Interest Top-Left": "感兴趣区左上",
    "Position Offset Feedback": "位置偏移反馈",
    "PixelChooser Interaction": "像素选取交互",
    "3D Slice Resolution": "三维切片分辨率",
    "3D Stack Resolution": "三维堆叠分辨率",
    "Composite on Original": "合成到原图",
    "Light Cone Width": "光锥宽度",
    "Clip to Output Black": "裁切到输出黑",
    "Clip to Output White": "裁切到输出白",
    "Dropout Start Frame": "丢帧起始帧",
    "Lights Cast Shadows": "灯光投射阴影",
    "Start on Frame": "起始帧",
    "Overdrive Soften": "过驱动柔化",
    "Overdrive Amount": "过驱动数量",
    "Brightness Variance": "亮度变化",
    "Frame Separation": "帧分离",
    "Particle Illusion Data": "粒子幻象数据",
    "Reverse Transition": "反向过渡",
    "Displacement Map on": "置换贴图开",
    "Alpha From Channel": "从通道取阿尔法",
    "View Current Matte": "查看当前遮罩",
    "View Iris Shape": "查看光圈形状",
    "Filter Apply Mix": "滤镜应用混合",
    "Render Misalignment": "渲染错位",
    "Threshold Soften": "阈值柔化",
    "Highlight Balance": "高光平衡",
    "Color Remapping": "颜色重映射",
    "Scene Camera": "场景相机",
    # 4 字节窄槽专用的一字译名（Left/Right/Top 在 3D 光晕表里只有 'Left\\0' 那么宽）
    "Top": "顶",
    "Left": "左",
    "Right": "右",
}

# ---- 容量自检：对每个词在英文源 DLL 里的每个独立出现位置算可用字节 ----
def sections(d):
    pe = d.find(b'PE\x00\x00')
    nsec = int.from_bytes(d[pe + 6:pe + 8], 'little')
    optsz = int.from_bytes(d[pe + 20:pe + 22], 'little')
    base = pe + 24 + optsz
    r = []
    for i in range(nsec):
        o = base + i * 40
        nm = d[o:o + 8].rstrip(b'\x00').decode('ascii', 'replace')
        rsize = int.from_bytes(d[o + 16:o + 20], 'little')
        roff = int.from_bytes(d[o + 20:o + 24], 'little')
        r.append((nm, roff, rsize))
    return r

def sec_of(secs, off):
    for nm, roff, rsize in secs:
        if roff <= off < roff + rsize:
            return nm
    return '?'

out = []
def p(s=''):
    out.append(str(s))
    print(s, flush=True)

p('=' * 96)
p('第五轮补词：容量自检')
p('=' * 96)
bad = []
occ = collections.defaultdict(list)
for dll in DLLS:
    d = open(os.path.join(BK, dll), 'rb').read()
    secs = sections(d)
    for m in TOKEN_RE.finditer(bytes(d)):
        s, e = m.span()
        if s > 0 and d[s - 1] != 0:
            continue
        if e >= len(d) or d[e] != 0:
            continue
        t = m.group().decode('ascii', 'replace')
        if t not in GAP2:
            continue
        j = e
        while j < len(d) and d[j] == 0:
            j += 1
        occ[t].append((dll.replace('Continuum_', ''), s, sec_of(secs, s), j - s))

for t in sorted(GAP2):
    zh = GAP2[t]
    need = len(zh.encode('gbk')) + 1
    lst = occ.get(t, [])
    if not lst:
        p('  %-30s → %-14s   ★ 源文件里找不到独立记号（无法写入）' % (t, zh))
        bad.append((t, 'NO_OCCUR'))
        continue
    avails = sorted(set(x[3] for x in lst))
    if min(avails) < need:
        sh = SHORT2.get(t)
        oksh = sh and len(sh.encode('gbk')) + 1 <= min(avails)
        p('  %-30s → %-14s 需要 %2d 字节，可用最小 %2d  → %s'
          % (t, zh, need, min(avails),
             ('短译名「%s」可用' % sh) if oksh else '★ 放不下！'))
        if not oksh:
            bad.append((t, 'OVERFLOW avail=%d need=%d' % (min(avails), need)))
    else:
        p('  %-30s → %-14s 需要 %2d 字节，可用最小 %2d  ✓' % (t, zh, need, min(avails)))

p()
p('放不下的：%d 个  %s' % (len(bad), bad if bad else ''))
p()

if not bad or all(b[1] == 'NO_OCCUR' for b in bad):
    # 合并进词典
    gz = json.load(open(os.path.join(WORK, 'gap_zh.json'), encoding='utf-8'))
    before = len(gz)
    gz.update(GAP2)
    json.dump(gz, open(os.path.join(WORK, 'gap_zh.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=0)
    gs = json.load(open(os.path.join(WORK, 'gap_zh_short.json'), encoding='utf-8'))
    b2 = len(gs)
    gs.update(SHORT2)
    json.dump(gs, open(os.path.join(WORK, 'gap_zh_short.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=0)
    p('✅ gap_zh.json  %d → %d 条' % (before, len(gz)))
    p('✅ gap_zh_short.json %d → %d 条' % (b2, len(gs)))
else:
    p('⚠️ 有放不下的词，未合并（先修词表）')

open(os.path.join(WORK, '_gap2_check.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\nDONE')

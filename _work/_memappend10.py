# -*- coding: utf-8 -*-
p = r'D:\Programming project\插件汉化\.workbuddy\memory\2026-09-25.md'

BAR = chr(124)   # '|'  —— 避免源码里出现裸竖线被 shell 吞掉

add = "\n---\n\n" + \
"""## 第 8 轮（v10）：修「纹理效果一用就崩 AE」—— 枚举选项表被写坏

### 用户报障
「其他的都可以，纹理那个效果为什么一用就崩溃 ae。」

### 根因（已字节级实证）
补丁把中文写进了 **`{B}` 分隔的下拉选项表**内部。这种表是**一整个 C 串**
（`None{B}Bounce{B}Stick{B}Slide{B}Disappear`），翻其中一个单词 = 把整张表写坏，
AE 读到非法枚举值就崩。更毒的是**尾清零链式破坏**：写 `Disappear`→`消失`
时把后面的 `{B}` 覆盖成 NUL，于是 `Slide` 也变成「前邻是 NUL 的独立记号」，
再被翻 → 整张表从头烂到尾，一次误判指数扩散。

实证（`_enum_evidence.py`，英文备份 / 已装坏版 / 新版 三方同偏移对照）：
```
off 16829464
  英文 : None{B}Bounce{B}Stick{B}Slide{B}Disappear
  坏版 : None{B}Bounce{B}Stick{B}Slide{B}消失\\0\\0\\0\\0\\0
  新版 : None{B}Bounce{B}Stick{B}Slide{B}Disappear
off 16823112  …|Magic Smooth|Magic Sharp  ->  …|Magic Smooth|智能锐化
off 16839584  …|Green Folded|Blue Folded  ->  …|Green Folded|蓝色折痕
```
**已装坏版 81 张表被写坏（8Bit 28 / 16Bit 27 / Float 26），新版 0 张。**

### 修复（fix4_dll.py 两处）
1. 提取/判定一律打在**英文原文件快照** `base = bytes(d)` 上
   （用正在改写的 `d` 判 → 分隔符已变 NUL → 自己制造假独立记号）。
2. 落盘前统一闸门（两个名字池都过）：
   `base[off-1] == 0` 且往前摸到的第一个可见字符 `!= 0x7C`。

写入 23289→**23156**，覆盖 6035→**6012**（少的正是被正确跳过的选项表单词）。
复算全 0，`verify_load` 6/6 OK。

### ⚠️ 为什么之前所有验收都全绿（最贵的教训）
独立复算只查「是否在声明区间内 + 回读是否匹配」。坏写入**当然全绿** ——
它们是按同一套（错误的）判据选出来的。**复算复用补丁判据 = 系统性盲点。**
⇒ 必须再加一条**与 pipeline 判据无关**的体检：直接扫输出，
找「同时含分隔符和非 ASCII 的 C 串」，必须为 0。这条一次抓出 133 条坏写入。

### ⚠️ 我自己的一个错：凭记忆写进文档的"证据"是假的
一度在说明里写「BCC.log 显示 `BCC+TiBCCnt`（正常应是 `BCC+Tint`）」，
**回原始日志 grep 发现根本没有这个串**（真实那行是
`Licensed render 8BitLib:  BCC+Tint`，BCC+ 前两个空格是正常格式）。
⇒ 二手转述的"证据"写进交付文档前，必须回原始日志 grep 一遍。

### 交付
- `deliver_now.py` 刷新 6 DLL（实际只有 8Bit/16Bit/Float 三支变化）
- `build_exe10.py`（stage10）重打包 → `Continuum汉化安装器.exe` 72443001 B sha `9eb542a3`
- `exe_check2.py`：523 条目，488 aex + 6 DLL 逐字节 0 不一致
- 触发 UAC 重装，**8 秒内 6/6 DLL 更新 + 488 aex 全部一致 = SUCCESS**
- 说明.txt / Readme.txt 数字同步为 23156 / 6012，并新增 FAQ 第 5 条（崩溃原因）

### 性能坑（扫 190 MB DLL 三连踩）
① `CJK.findall(bytes)` 生成百万级列表 → 内存爆 + SIGTERM；
② 带 GBK 分支的交替正则扫 26 MB 要 5 分钟以上；
③ 正解：**只在英文备份上用纯 ASCII 类** `[\\x20-\\x7e]{6,}\\x00` 取值（1 分钟扫完 3 支），
   另外两版只做**同偏移切片比对**。

### 剩余
约 917 条 x1 组专属参数未翻（用户未要求）。
""".replace('{B}', BAR)

with open(p, 'a', encoding='utf-8') as f:
    f.write(add)
print('appended', len(add))

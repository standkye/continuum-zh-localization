# Continuum 汉化工具链

**BorisFX Continuum 2026 (v19.0.0) 的 AE / Premiere 中文本地化 —— 方法、工具与译名表**

> ⚠️ **本仓库不包含 BorisFX 的任何文件。** 没有 DLL、没有 `.aex`、没有安装器。
> 这里是**汉化工具的源码 + 译名对照表 + 踩坑记录**，不是可以直接双击使用的成品补丁。
> Continuum 是 BorisFX 的商业软件，请自行购买正版并自行完成汉化。

[English summary ↓](#english-summary)

---

## 它是什么 / 它不是什么

| | |
|---|---|
| ✅ 是一套**完整的汉化工具链** | 从二进制里定位可翻译字符串 → 判定哪些不能翻 → 写回中文 → 校验覆盖率 → 打包安装器，每个环节都有脚本 |
| ✅ 是一份**经实测的译名对照表** | 488 个效果名（全部）+ 6997 个参数名的中英对照 |
| ✅ 是一份**踩坑记录** | 三批导致宿主崩溃的字符串、`.aex` 资源格式细节、PowerShell/SHFileOperation 等环境坑 |
| ❌ 不是**一键汉化器** | 需要在已装正版 Continuum 的机器上装 Python、按顺序跑若干脚本 |
| ❌ 不能**跨版本直接复用** | Continuum 换版本后字节偏移全变，脚本里的地址常量要重新定位 |
| ❌ 不是**通用插件汉化框架** | 全部逻辑是按 Continuum 2026 的 PE 结构与 PiPL 资源写的，其他插件最多只能借鉴思路 |

---

## 汉化成果（最终版 v17 实测数字）

| 项目 | 结果 |
|---|---|
| 效果名（AE 效果菜单里那一项） | **488 / 488** 全部中文 |
| 效果分类（效果名上方的分组标题） | **483 / 488**（余下 5 个是厂家的品牌名 `BCC VR`，按规则不翻） |
| 引擎 DLL 中文写入点 | **25,479 处**，覆盖 **7,353 个**不同英文原文 |
| 参数名覆盖率 | **91.4%**（按出现次数统计，6 支 DLL，分母 19,560） |
| 有意保留英文 | 285 处宿主名单 + 142 处参数名 + 243 处位于 `.rsrc` 的其他 UI |
| 崩溃 | **0**（v17 经实机验证，AE / Pr 均不再闪退） |

**有意保留英文的原因**（不是漏翻）：
- **内部键 / 配置键 / 导出导入名** —— 翻了会让 DLL 加载失败（`WinError 127`）
- **宿主软件名单、类型枚举、授权串、Qt 字符串**
- **品牌名**（`BCC VR`、`BCC HSL` 这类产品线名称，英文原版值就是它本身）
- **槽位过短的**（如 `Pin`、`Hue`、`Map`，中文塞不进去）
- **BCC+ 单元名** —— 翻了会闪退（详见下文「崩溃三批」）

---

## 目录结构

```
.
├── README.md                     本文件
├── LICENSE                       MIT
├── AI_HANDOFF.md                 项目交接文档（最完整的技术总览，含全部阶段与结论）
├── 工作日志-2026-09-24.md         逐日工作记录
├── Git说明.txt                   本仓库版本管理约定
│
├── _work/                        ★ 工具链（脚本 + 数据）
│   ├── installer_gui.py          ★ 出货安装器源码（菜单式 汉化/还原，PyInstaller --onefile）
│   ├── *.py                      202 个脚本
│   ├── *.json                    31 个数据文件（槽位表 / 译名表 / 写入日志）
│   └── *.tsv                     5 个分桶表
│
└── Continuum 汉化组件 v19.0.0/    ★ 交付目录（此处只剩文本文件）
    ├── 说明.txt                   面向使用者的说明（含 FAQ）
    ├── Readme.txt                 README（中英双语）
    ├── EffectNameTable.txt        效果名中英对照（442 行）
    ├── ParamNameTable.txt         参数名中英对照（6997 条）
    ├── Install-Chinese.bat        安装脚本（需要本目录同时存在 DLL / aex，本仓库未提供）
    ├── Restore-English.bat        还原英文
    └── 还原英文（双击这个）.bat    还原英文（中文文件名版本）
```

> **为什么脚本目录叫 `_work/`？** 这是开发期的历史目录名，脚本里的路径常量（`WORK = .../_work`）依赖它。
> 改名会让全部脚本失效，所以原样保留。

---

## 技术要点

### 1. 字符串分散在三个池子里

只改一个地方是不够的 —— 效果名、分类名、参数名分别在**三套互不相干的存储**里：

| 池 | 位置 | 承载什么 | 提取方式 |
|---|---|---|---|
| PiPL 资源 | 488 个 `.aex` | 效果名 `eman` + 分类名 `gtac` | 解析 `MIB8eman` / `MIB8gtac` 记录 |
| 8 字节对齐槽位链 | 6 支引擎 DLL 的 `.rdata` | 大部分 UI 标签 | 扫描定长补零槽位链 |
| 独立 NUL 记号 | 引擎 DLL 的 `.rdata` / `_RDATA` | 第二、第三处同名参数名池 | 找前后都是 NUL 的孤立串 |

**最容易漏的就是第二、第三池** —— 只改第一池会出现「效果名中文了，但参数名还是英文」。

PiPL 记录布局（实测）：

```
MIB8gtac            ← 记录 tag（8 字节）
00 00 00 00         ← flags
08 00 00 00         ← 记录长度（小端 u32）
06                  ← Pascal 串长度
42 43 43 20 56 52   ← 数据 "BCC VR"
00                  ← 对齐填充
```

### 2. 六道闸门：判定哪些字符串「绝不能翻」

翻译写错位置比不翻译更糟 —— 把配置键翻成中文会让插件直接加载失败。所以写回前要过多道闸门：

- **形状闸**：首字符必须是大写字母或数字；不含 `_`；不含 `::`（挡掉 `scaleX`、`pcfo.depth.rm.mode`）
- **邻居闸**：往前 6 个记号内不得出现「标识符样」串（含 `_`、`.` 或首字母小写）
- **容量闸**：GBK 译名 + NUL 必须塞得进「到下一个非 NUL 字节」的距离
- **黑名单闸**：内部键 / 授权字段 / 宿主名单一律不翻

### 3. 写回不变式：文件长度必须不变

所有替换都是**等长原地覆盖**（中文字节 + 补零写满整槽）：

- 只动数据字节 → 不碰 `.text`、不碰节表、不碰指针
- 文件长度、所有偏移、PE 签名全不变 → 不存在「改了之后插件认不出自己」的问题

### 4. 编码：GBK，不是 UTF-8

这是**实测出来的**，不是猜的：写一处 → 读回字节 → 用 GBK 和 UTF-8 各解一次 → 看哪个能解出通顺中文。

在中文 Windows + AE 25.1 + Continuum 2026 上结论是 **GBK**。用 UTF-8 会出现两种症状：
界面显示 `妯＄硦` 这类乱码，或一添加效果就报
`特效：变换 (25::3) 无法初始化该效果`。

### 5. 崩溃三批（重点教训）

全中文版本曾经**一加效果就闪退、且没有任何提示框**。二分法定位到三批字符串，全部回退英文后解决：

| 批次 | 崩溃键 | 原因 |
|---|---|---|
| 1 | `Microsoft` | 命中内部逻辑判断 |
| 2 | `Textures` | 同上 |
| 3 | **82 个 BCC+ 单元名**（83 处） | 引擎按**英文单元名**查找单元，翻译后查不到 → 空指针 |

第 3 批尤其隐蔽：这些是**单元名**（`Frost`、`Three Strip`、`Center Spot`、`Grain` …），
看起来像普通 UI 文案，实际上被引擎当作标识符在用。

### 6. 残留分析：区分「漏翻」与「不该翻」

遇到「还剩一堆英文」时，**先拿英文原版同位置逐字节比对**：

- 值**相同** → 是品牌名 / 产品名，本来就不该翻
- 值**不同** → 才是真漏翻

只看「槽位装不下」会得出错误结论（本项目就踩过这个坑：`BCC VR` 起初被解释成「6 字节槽位太窄」，
实际上它是厂家给 VR 产品线起的品牌名，英文原版值就是它本身）。

---

## 快速开始（自己汉化一遍）

**前置条件**

- Windows，已安装正版 **Continuum 2026 (v19.0.0)**，并**已用英文版跑过一次**（生成 `Backup-English` 备份）
- Python 3.10+（脚本只用了标准库；`pefile` 可选，用于更强的 PE 解析）
- 管理员权限（安装阶段要写 `C:\Program Files\...`）

**大致流程**（每一步的具体命令见 `AI_HANDOFF.md`）

```
1. 扫出可翻译槽位           -> dll_chains.json / 名称表
2. 生成候选译名并过滤       -> param_zh.json / effect_zh.json
3. 写回 DLL（等长覆盖）      -> _work/patched_dll/
4. 写回 488 个 .aex 的 PiPL  -> _work/patched_aex/
5. 回读校验覆盖率            -> verify_resid.py 之类
6. 打包安装器                -> make_iss.py + build_exe*.py（需要 Inno Setup）
```

> ⚠️ 脚本里的路径常量是按作者本机（`D:\Programming project\插件汉化`）写的，
> 换机器需要先改 `WORK` / `PROJ` / `BK` 这几个常量。

---

## 安装器（r18）

出货的 `Continuum汉化安装器.exe` 就是 `_work/installer_gui.py` 用 PyInstaller `--onefile` 打的，
494 个汉化后的文件（6 个 DLL + 488 个 `.aex`）作为 `--add-data` 一起塞进 exe —— 所以它是**自包含**的，
双击时不需要旁边有任何其他文件。

双击（不带参数）会先弹菜单：

```
[1] 汉化        效果名 / 参数名换成中文
[2] 恢复原版    从 Backup-English 把英文原件拷回去
[0] 退出
```

也可以直接输入中文「汉化」或「回到原版」。命令行用法保持不变：
`/install`（汉化）、`/restore`（还原）、`/quiet`（静默汉化、不弹菜单）。

三个设计要点，都是踩过坑才定下来的：

1. **菜单在提权之前问完。** UAC 提权会开一个新的控制台窗口；如果让提权后的子进程再去读键盘，
   那个窗口里没人敲得到，会一直卡住。所以选择结果以 `/install` / `/restore` 参数传给子进程，
   子进程只要看到 `--elevated` 就跳过菜单。
2. **还原只依赖 `Backup-English`。** 那是**安装时在目标机上现场生成**的（写任何文件之前先备份），
   不依赖任何随包分发的英文原件 —— 这就是"只留一个 exe 也能同时汉化和还原"的原因。
3. **每个文件单独打印 OK / FAIL，复制完回读 sha256 校验。** 早先有一版吞掉了复制异常，
   结果只装了一半却显示成功。

打包命令（`<stage>` 里放 `installer_gui.py` + 那 494 个文件）：

```
PyInstaller --onefile --console --name Continuum汉化安装器 \
    --add-data "<stage>;." installer_gui.py
```

> 注意：PyInstaller 对 `--add-data` 的条目做 zlib 压缩，所以**不能**靠"在 exe 原始字节里搜中文字面量"
> 来验证打包内容；正确做法是用 `PyInstaller.archive.readers.CArchiveReader` 把条目解出来再比对哈希。

---

## 常见问题

**Q：装上后界面是乱码 `妯＄硦`？**
编码错了。本项目用 GBK；如果拿到的是 UTF-8 版本就会出现这个症状，换成 GBK 版本即可。

**Q：一添加效果就报「无法初始化该效果」或直接闪退？**
命中了崩溃三批里的字符串。检查是否把内部的**单元名**（`Frost` / `Three Strip` / `Grain` 等）翻成了中文。

**Q：关闭软件后才弹出崩溃报告，是汉化导致的吗？**
基本不是。判据：
1. 崩溃报告里的 `lastAppState` 是否已经走完 `...-term-fexit`（走完说明是退出阶段）
2. breadcrumb 记录的「终止时刻」与「生成 dump 的时刻」是否相差十几秒以上
3. 崩溃线程的调用栈里有没有 Continuum 的帧、有没有指向已卸载模块的指针

三条都符合「退出期 + 无插件栈」时，属于宿主自身的退出期问题，与字符串汉化无关。

**Q：为什么 `BCC VR` 这 5 个分组名没翻？**
它是厂家给 VR 产品线起的**品牌名**（与 `BCC HSL` 同类），英文原版值就是它本身，不属于界面文案。
那 5 个插件的**效果名本身是中文**（`BCC VR模糊` / `BCC VR重定向` / `BCC VR插入` / `BCC VR闪烁修复` / `BCC VR锐化`）。

**Q：`_work/` 里那些 `_` 开头的脚本是什么？**
排查过程中的一次性探针脚本（dump minidump、hexdump、断点二分等），保留是为了留下证据链。

---

## 法律与免责声明

- 本仓库**不包含** BorisFX、Adobe 的任何二进制文件、代码或资源。
- 本仓库的脚本**会修改**你本机已安装的 Continuum 文件。请**先备份**，风险自负。
- 反向工程与修改商业软件的合法性因司法辖区而异 —— 请确认你所在地区的法律以及你与 BorisFX 的许可协议是否允许。
- 译名对照表（`EffectNameTable.txt` / `ParamNameTable.txt`）是为互操作与学习目的制作的翻译参考。
- 如果你是在中国香港、中国台湾或中国澳门使用，请注意当地法律可能与本项目署名的适用法律不同。

**请支持正版**：<https://borisfx.com/>

---

## 许可

本项目代码以 **MIT License** 发布，详见 [LICENSE](LICENSE)。

---

## English summary

A community toolkit for localizing **BorisFX Continuum 2026 (v19.0.0)** into Simplified Chinese
for After Effects / Premiere Pro.

**What this repo is:** the localization toolchain (202 Python scripts), a verified
Chinese↔English name table (488 effect names + 6,997 parameter names), and a detailed write-up of
the pitfalls encountered — including three batches of strings that crash the host when translated.

**What it is NOT:** it contains **no BorisFX binaries** (no DLLs, no `.aex`, no installer) and is
**not** a one-click patch. You need your own licensed copy of Continuum, a Python install, and some
patience following the documented workflow. Byte offsets are version-specific and will not transfer
to other Continuum releases.

**Result achieved (v17):** 488/488 effect names and 483/488 category headers in Chinese;
25,479 translated strings covering 7,353 distinct originals (91.4% of all translatable tokens in the
six engine DLLs); zero crashes after the fix batches.

Licensed under MIT. Continuum is a trademark of BorisFX, Inc. This project is unaffiliated with
BorisFX.

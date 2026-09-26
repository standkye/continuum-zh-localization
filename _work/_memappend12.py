# -*- coding: utf-8 -*-
import os
p = r'D:\Programming project\插件汉化\.workbuddy\memory\2026-09-25.md'
s = open(p, encoding='utf-8').read()
add = '''

---

## 第 10 批：TIER C（1066 条单次出现 UI 标签）—— v12 交付完成

用户指令："继续把剩下的汉化了吧"。上一轮已把 TIER A（539 条）翻完，本轮处理 gen_cand9b.py
产出的 TIER C 清单（`_tc_list.txt`，1066 条 x1 频次）。

### 做法
1. `dump_tc2.py` 导出 TIER C 全清单（含 repr 键名 + avail + 所在 DLL），一次性读完再手写。
2. 手写 `gen_batch10.py`（键 -> 译名大字典，1032 条；刻意跳过 34 条）：
   - 跳过 Adobe 字形名（`Oacutesmall` / `Gbreve` / `Idotaccent` / `Thornsmall` …）—— 是字形标识符不是标签
   - 跳过品牌/版本号（`Tiffen` / `Primatte`(单独) / `SHA-512 part of OpenSSL…` / `Continuum 2026 19.0`）
   - 跳过内部调试串（`CubeShape eBuildRS3dScene entering`、`SetChannelToTexture leave`）
   - 跳过键盘修饰键 `Ctrl`（会破坏 `Ctrl+Shift+A` 这类快捷键显示）
   - `Fece Detection ML` / `Positioin` 是 Boris 自己的拼写错误，按正确含义翻（人脸检测 / 位置）
3. `check10.py`（照抄 check9.py 口径）跑严格自检：0 缺失 / 0 GBK 失败 / 0 超容 / 0 冲突。
4. `fix4_dll.py` 的 extra 列表加 `'batch10_miss.json'` → 重跑补丁。
5. 全套验收 → `deliver_now.py` → `build_exe12.py`（stage12）→ `exe_check2.py` → 装机。

### 结果
| 指标 | v11（第 9 批） | v12（第 10 批） |
|---|---|---|
| 总替换 | 24534 | **25575** |
| 写入点 | 24392 | **25426** |
| 覆盖英文原文种数 | 6409 | **7438** |
| 中文写入 | 24351 | **25385** |
| 词典总量 | 6481 | **7513** |

验收：accept4 全 0（长度/野改动/回读/越界/.text）· overlap bad=0 · enum 0/0 · LoadLibrary 6/6 OK。
`exe_check12`：523 条目，488 aex 0 不一致，6 DLL sha 一致。
`trigger_install12.py`：**24 秒装完，6/6 DLL + 488 aex 全部一致 = SUCCESS**（v11 那次 UAC rc=5 被拒，
本次成功；前提依然是 AE 必须彻底退出）。
新增 `gen_pntable.py`：从 `_fix4_writes.json` 重生成 `ParamNameTable.txt`，**3789 → 7056 条**。
说明.txt / Readme.txt 同步到 25426 / 7438 / 7056。

### ⚠️ 本轮踩到的两个坑（已写进 skill）
1. **容量口径差 1 字节**：`cand9b.json` 的 `avail` 字段是"到下一个非 NUL 字节的距离"（含尾随 NUL），
   真实约束是 `len(zh.encode('gbk')) + 1 <= avail`。我用 cand9b 的 avail 自检时忘了 +1，
   报 0 超容是假绿 —— 换 `check10.py`（对英文备份算 `min(avail)` 再比 need+1）才暴露出 4 条真超容
   （Cube/Roman/Type On/UpRes ML）。**新批次必须用 checkN.py 口径自检，不能用 cand 的 avail。**
2. **`verify_load.py` 默认指向 `patched_dll_c`**（历史遗留常量），不传参数就会去验旧目录 —— 这次差点拿
   `patched_dll_c` 的 6/6 OK 冒充新补丁通过。**必须显式传路径**：
   `python verify_load.py <patched_dir>`。
3. `exe_check2.py` 依赖 `PyInstaller`，用系统 python 跑会报 `No module named 'PyInstaller'`，
   必须用 `C:\\Users\\Jinna\\.workbuddy\\binaries\\python\\envs\\default\\Scripts\\python.exe`。
'''
open(p, 'w', encoding='utf-8').write(s + add)
print('appended', len(add))

# -*- coding: utf-8 -*-
import os
p = r'D:\Programming project\插件汉化\.workbuddy\memory\2026-09-25.md'
s = open(p, encoding='utf-8').read()
add = '''

---

## 给项目加 git 版本管理（用户要求："不然出错了别[没法回滚]"）

### 现状盘点
项目根目录 `D:\\Programming project\\插件汉化` 共 **3.9 GB**：
| 部分 | 体积 | 处理 |
|---|---|---|
| `Continuum 2026 Adobe v19.0.0.exe` | 2.9 GB | 忽略（官方可重下载） |
| `_work/` | 775 MB | 其中 4 份 `patched_dll*` 副本占 720MB，忽略 |
| `Continuum 汉化组件 v19.0.0/` | 260 MB | 6 DLL 174MB + 安装器 exe 69MB + 488 aex 17MB |

### 用户选定的方案
**文本全跟踪 + 产物走 Git LFS + 纯本地仓库（暂不要远端）**

### 落地
- `.gitattributes`：`* -text` **必须放第一行**（字节级补丁项目的生命线，见下）
  + `*.dll` 和 `Continuum汉化安装器.exe` 走 lfs filter；488 aex 直接入库（仅 17MB）
- `.gitignore`：2.9GB 安装包 / `patched_dll*` / `patched_aex*` / `__pycache__` /
  `_work/pyinstaller_stage*` / 第三方安装包 / `.workbuddy/`
- `git init` + `git lfs install --local` + `core.autocrlf=false`
  + 本地身份 `user.name=Jinna, user.email=jinna@local`（本机全局没配过 git 身份）
- 两次提交：`39f9543`（v12 基线，1431 条目）+ `c0b89b8`（Git 说明文档）
- 根目录新增 `Git说明.txt`（**刻意不放进交付目录**，否则会被 PyInstaller 打进安装包）
- 验证脚本：`_work/_git_verify.py`（普通文件字节保真）、`_work/_git_verify_lfs.py`（LFS 对象完整性）

### ⚠️ 本轮学到的三个 git 要点
1. **字节级补丁项目必须 `* -text` + `core.autocrlf=false`**。
   否则 git 的 CRLF/LF 自动转换会悄悄改掉 dump 类 txt 的字节，
   而整个流水线靠「读回字节 == 写进去的字节」来保证没改坏 —— 验���会全部失效。
2. **验证 LFS 文件不能直接用 `git cat-file blob HEAD:<dll>`** —— 拿到的是 133 字节指针，
   会误报 MISMATCH。正确做法是解析指针里的 `oid sha256:`，再去
   `.git/lfs/objects/<aa>/<bb>/<oid>` 取真实文件比对。
   （实测 7/7 OK，`.git/lfs` 占 242.8 MB；每提交一版二进制约 +240MB）
3. **确认 DLL 有没有被正确 smudge**：看文件开头两字节是不是 `MZ`；
   若是 133 字节就说明 LFS 没装好 —— 这是新环境最容易踩的坑。

### 入库规模
1427 个文件 / 288 MB（其中 227MB 在 LFS），非 LFS 部分 6/6 抽样字节完全一致。
'''
open(p, 'w', encoding='utf-8').write(s + add)
print('appended', len(add))

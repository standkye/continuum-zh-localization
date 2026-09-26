# NOTICE / 适用范围说明

## 本仓库不含任何厂家文件

本仓库**不包含、也不分发** BorisFX, Inc. 或 Adobe Inc. 拥有的任何文件：

- ❌ 没有 `*.dll`（Continuum 引擎 / BCCPlus 插件）
- ❌ 没有 `*.aex`（488 个效果宿主模块）
- ❌ 没有安装器 `*.exe`
- ❌ 没有厂家的代码、资源或图标

仓库中的 `Install-Chinese.bat` / `Restore-English.bat` 只是**安装流程脚本**；
它们会从**脚本所在目录**拷贝 DLL / aex，而本仓库并不提供这些文件。

## MIT 许可的覆盖范围

`LICENSE` 中的 MIT 许可仅覆盖本仓库中**自行编写**的内容：

- `_work/**.py` —— 汉化工具链脚本
- `_work/**.json` / `_work/**.tsv` —— 槽位表、译名表、统计表
- `README.md` / `AI_HANDOFF.md` / 工作日志 / `说明.txt` / `Readme.txt` —— 文档

该许可**不覆盖、也不授予** BorisFX / Adobe 拥有的任何软件或资源的任何权利。
使用本工具链修改商业软件时，你需要自行确保具备相应的许可。

## 译名对照表

`EffectNameTable.txt`（442 行）与 `ParamNameTable.txt`（6997 条）是为**互操作与学习**目的
制作的翻译参考。它们只包含字符串对照，不含厂家代码。若权利人认为不妥，请提 issue，会立即移除。

## 商标

BorisFX、Continuum、BCC 是 BorisFX, Inc. 的商标。
After Effects、Premiere Pro、Adobe 是 Adobe Inc. 的商标。
本项目与上述公司**无任何隶属或合作关系**。

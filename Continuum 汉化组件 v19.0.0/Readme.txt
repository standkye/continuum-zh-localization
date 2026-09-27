BorisFX Continuum 2026 (v19.0.0) - Chinese patch
=================================================
(Chinese below / 中文见下)

WHAT IT CHANGES
  - 488 effect names (shown in the Effects menu)        488 / 488
  - 483 effect categories (the BCC xxx group headers)   483 / 488
    The remaining 5 all carry the SAME header, "BCC VR", on 5 plug-ins:
        BCCBlur4 / BCCReorient / BCCVR2DInsert / BCCVRFlickerFixer / BCCVRSharpen
    It stays English for two reasons:
      1. Brand string. "BCC VR" is the vendor's own product-line name (same class as
         "BCC HSL") -- that IS the original English value. This patch classifies such
         brand names as "not UI copy", so they are not translated.
      2. Too narrow. Each of those category entries has a 6-byte text area
         (record size = 8) that "BCC VR" fills exactly, leaving only 1 byte of
         alignment padding. A full Chinese name ("BCC虚拟现实") needs 11 bytes. The
         most that would fit is "VR虚拟" (6 bytes) or "BCC虚拟" (7 bytes, which also
         means bumping the string-length byte 6 -> 7 and eating the pad).
    Not worth rewriting 5 .aex files and touching a length byte for one group header.
    NOTE: the EFFECT names of those 5 plug-ins ARE Chinese
    (BCC VR模糊 / BCC VR重定向 / BCC VR插入 / BCC VR闪烁修复 / BCC VR锐化).
  - parameter names inside 6 engine DLLs, 25,479 Chinese strings
    covering 7,353 distinct English originals:
    Continuum_AE_Float / _8Bit / _16Bit / _Common_AE / _3DObjects_AE / BCCPlus
    = 91.4% of every translatable string token in those DLLs.

CRASH FIX (3 batches, all fixed)
  An earlier all-Chinese build crashed After Effects. The pattern, once
  seen, is simple and was found in three rounds:

      Every string the BCC+ engine uses to LOOK UP A TABLE BY NAME must
      stay English. Translating it makes the lookup return null and the
      host crashes on insert -- with no error dialog.

  Batch 1 - offset 0x25C75C0  'Microsoft'
      used to build the registry path
      SOFTWARE\Microsoft\Windows\CurrentVersion\ProgramFilesDir
      -> lookup failed, null pointer, AddRef on null -> EVERY BCC+ effect
         crashed on insert.

  Batch 2 - offset 0x26ABFF0  'Textures'
      a bare alias key in the BCC+ unit table, sitting between
          0x26ABFE0 'BCC Textures'   (display name - safe to translate)
          0x26ABFF0 'Textures'       (bare alias key - CRASHED)
          0x26AC000 'bccunittexture' (internal id - never translated)
      -> only the Textures effect crashed.
      (The menu still reads "BCC纹理" because the menu name comes from the
      .aex PiPL record, a separate path.)

  Batch 3 - this build - Frost / Three Strip / Center Spot / Grain ... and
  a whole batch of other BCC+ effects crashed. SAME rule. BCC+ has 166
  "units"; each unit has one English unit-name string inside BCCPlus.dll,
  and the engine resolves the unit by that name. The unit name is NOT the
  menu name (the menu name comes from the .aex PiPL), so a Chinese menu
  entry does not mean the unit name may be translated. Confirmed crashes:
          'Frost'        0x0262272C
          'Three Strip'  0x0262AD58
          'Center Spot'  0x0260FAE0
          'Grain'        0x025DD180
  A full scan of the same pattern found 83 slots (82 unit names) that had
  been translated anywhere in BCCPlus.dll; ALL of them are back to English
  in this build. A few of those words double as common parameter titles
  (Tint / Vignette / Blur / Detail / Glow / Dissolve / Light / Transform),
  so in those specific BCC+ effects the word now shows English -- the
  unavoidable cost of not crashing. Control: the unit name 'Channel Blur'
  was never translated, so 通道模糊 always worked.

  All reverted strings are byte-identical to the vendor original. The rest
  of BCCPlus.dll stays Chinese, and the menu still shows the Chinese names.

  Verified before shipping (same three gates every time):
   1. structural audit recomputed from raw bytes: 83/83 slots legal --
      change within one slot, NUL-terminated, filler zeroed, 0 problems;
      both earlier crash keys still English.
   2. size: all 6 DLLs byte-size-identical to the factory originals.
   3. load: 6/6 LoadLibrary OK; installer payload matches the shipped
      directory byte-for-byte (6 DLLs + 488 .aex, 0 mismatch).

IDENTIFIER HYGIENE (new in this build)
  77 machine-readable identifiers had been translated by mistake. They are
  back to English. Each one is used by the code to look up a table, build a
  path or find a file, so translating it silently broke a feature (no crash,
  which is why it went unnoticed):

    - 7 preference file names x 4 DLLs (28 slots)
        WindowPreferences.bwsx / BrowserPreferences.bwsx /
        BrowserTextPreferences.bwsx / StandaloneBrowserPreferences.bwsx /
        WindowPreferences.tsws / BCCTitleStudio*.bwsx / SnapToHomePrefs.bwsx
      Proof: the vendor's own C:\ProgramData\BorisFX\ContinuumAE\19\Workspaces\
      contains exactly these file names.
    - 7 workspace XML attribute names x 4 DLLs (28 slots)
        Workspace / Left / Right / Top / Bottom / XPosition / YPosition
      Proof: the vendor .tsws files are
      <Workspace ScreenWidth=.. Left=.. Top=.. XPosition=.. YPosition=..>.
      Only those schema-region copies were reverted; the UI labels
      "左侧 / 右侧 / 顶部 / 底部 / 位置" stay Chinese.
    - 9 dotted ShaderColorBlend internal keys x 3 DLLs (27 slots)
        .effect .src .back .hostback .dest .host.applied .back.applied
        .composite .applied
    - 3 doubled display-name prefixes: "BCC BCC模糊" -> "BCC模糊" etc.
    - Deinterlace retranslated from 去隔行 to the industry-standard 去交错.

  Zero visual change; a static diff proves only these 77 slots moved.

BACKFILL (new in this build, "hyg2")
  The previous build documented 234 parameter names as "skipped by the
  conservative safety gates". Each one was re-judged:

    103 slots (44 distinct English words) -> confirmed display names, now
        translated. A slot qualified if either
          A. the word is a parameter <name> in the vendor preset files
             (presets index parameters by numeric ID, so <name> is only the
             display-name copy -- that IS the display-name vocabulary), or
          B. the surrounding string table (+-0x120) already holds >= 8
             Chinese strings, i.e. the table is already displayed in
             Chinese and completing it just finishes a half-translated row.
        Plus a continuity rule: a deferred sibling within 0x160 of an
        already-translated slot joins it, so no table stays half-Chinese.

    131 slots -> confirmed MUST stay English, by category:
          28 preference file names (7 words x 4 DLLs)
          27 dotted ShaderColorBlend.* internal keys
          21 workspace XML attribute/element names (Workspace/Left/Right/
             Top/Bottom/Workspaces)
          12 preset-browser metadata column names (Category / Filter Version
             / Creation Date -- machine column names next to the XML keys
             presetname / filterversion)
           8 brand strings BCC HSL / BCC VR (translation would equal the
             original -- no benefit)
           7 slots too short for Chinese (Pin / Hue / Map)
           6 licensing fields Master / Process (Sentinel/HASP XML)
           4 preset directory-name table (Presets)
           7 effect names BCC Motion Tracker FCP / BCC+Primatte Studio --
             their authoritative display source is the PiPL record in the
             .aex; changing only the DLL copy would desync it
           3 Enable Beat Reactor (neighbours are cache-cleanup / language-
             pack internal names -- purpose unknown)
           3 Mocha integration internal table (Mocha Init - Render)
           2 Launch Mocha Mask / Launch Mocha Track (same table as the
             MOCHA001/MOCHZ001 licence codes -- purpose unknown)
           2 3D Objects scripting callback names (Layer / Output)
           1 Textures -- the proven crash key, permanently English

  Verified by three independent gates before shipping:
   1. structural audit recomputed from raw bytes (not the builder's list):
      103/103 slots legal -- change within one slot, NUL-terminated, valid
      GBK, no '|' option table touched, no write past the next string.
      0 problems. Both crash keys still English.
   2. size: all 6 DLLs byte-size-identical to the factory originals.
   3. load: 6/6 LoadLibrary OK; 20 spot-checked backfilled words confirmed
      present as Chinese in the shipped bytes.

HOW TO INSTALL
  1. Quit After Effects completely
  2. Double-click  Continuum汉化安装器.exe
     A menu appears:
         [1] 汉化        patch to Chinese
         [2] 恢复原版    restore the original English files
         [0] 退出        quit
     Type 1 and press Enter (typing "汉化" works too), then click "Yes"
     on the UAC dialog.
  3. After SUCCESS, start After Effects

HOW TO RESTORE
  Double-click the same exe and type 2 ("回到原版" also works).
  Headless equivalent:  Continuum汉化安装器.exe /restore
  (backups live in C:\Program Files\BorisFX\ContinuumAE\19\Backup-English)

COMMAND LINE
  /install   patch, no menu            /restore   restore, no menu
  /quiet     patch silently            (no argument = show the menu)

  The choice is made before elevation and handed to the elevated process, so
  picking 2 never leaves an invisible prompt waiting in a new console window.

SAFETY
  - Every file is patched IN PLACE: file size, PE structure and all offsets
    are unchanged. Nothing is added, removed or moved.
  - The installer backs up the English originals to
    C:\Program Files\BorisFX\ContinuumAE\19\Backup-English
  - Presets (.bsp/.bap) index parameters by numeric ID, so changing display
    names does not break them.
  - No After Effects program file is touched.

ENCODING
  - This build writes GBK. That is the encoding verified BY TEST on this
    machine (Chinese Windows + AE 25.1 + Continuum 2026): write one string,
    read the bytes back, decode with both GBK and UTF-8 - GBK gives clean
    Chinese, UTF-8 does not.
  - Do NOT pick the encoding by AE version number. An earlier build of this
    patch did that, guessed UTF-8, and produced garbled names ("妯＄硦") plus
    the "cannot initialize this effect" error.

REQUIREMENTS / LIMITS
  - Continuum 2026 Adobe v19.0.0 (this machine: build 19.0.0.327)
  - AE 25.1 on a Chinese Windows (GBK). This is the configuration tested here.
  - Parameter names are Chinese only: the string slots were sized for the
    English text, so a second language does not fit.
  - Some strings stay English ON PURPOSE, not by omission:
      * internal keys / config keys / PE export-import names - translating
        them makes the DLL fail to load (WinError 127)
      * host-app names, type enums, license strings, Qt strings
      * a handful of slots too short for two Chinese chars (Pin, Hue)
      * 5 group headers are "BCC VR" - the PiPL record data area is only 6 bytes
        (see WHAT IT CHANGES; a full Chinese name needs 11)
      * BCC+ unit names - the engine looks each unit up BY ITS ENGLISH
        NAME; translating one makes that effect crash on insert (82 names;
        see CRASH FIX batch 3)
  - Known leftovers (harmless):
      * ~1,057 strings belong to the 3D Objects plug-in's own timeline panel;
        they live in the .rsrc section and are a separate UI
      * 66 command/menu strings in the .rsrc of each of the three AE engines
      * 142 parameter names deliberately kept English (judged one by one;
        131 from the BACKFILL batch below + 11 BCC+ unit names from
        CRASH FIX batch 3)
  - Re-apply after any Continuum update.

================================================
BorisFX Continuum 2026 (v19.0.0) 汉化组件 —— 中文说明

改了什么
  - 488 个效果名（Effects 菜单里的名字）        488 / 488
  - 483 个分组（BCC xxx 类型栏）                483 / 488
  - 6 个引擎 DLL 里的参数名，25479 处中文写入
    （覆盖 7353 个不同的英文原文，约占可翻译总量的 91.4%）
  - 崩溃修复：共分三批找到「BCC+ 引擎要拿去查表用的键被翻成中文 →
    对应效果闪退」的 bug，本版全部改回英文（详见英文部分 CRASH FIX
    一节，或 说明.txt）。第 3 批是把 BCCPlus.dll 里被翻过的 82 个
    BCC+ 单元名全部回退（霜冻 / 三色带 / 中心聚光 / 颗粒 …）
  - 标识符卫生：另有 77 处"程序要拿去查表/拼路径/找文件"的字符串
    曾被误翻，本版全部改回英文（详见英文部分 IDENTIFIER HYGIENE
    与 说明.txt 的【标识符卫生修复】一节）
  - 回填：上一版列为"被闸门保守跳过"的 234 处参数名逐条重判 ——
    103 处确认是显示名，已补成中文（44 个不同的词）；131 处确认必须保留
    英文，逐类理由见英文部分 BACKFILL 与 说明.txt 的【hyg2 回填】
    （含 44 个已译词的完整清单）

怎么装
  1. 完全退出 After Effects
  2. 双击 Continuum汉化安装器.exe，UAC 点"是"
  3. 看到 SUCCESS 后启动 After Effects

怎么还原
  运行 还原英文（双击这个）.bat
  （备份在 C:\Program Files\BorisFX\ContinuumAE\19\Backup-English）

安全性
  - 全部"就地替换"：文件大小、PE 结构、偏移一律不变
  - 自动备份英文原版
  - 预设按数字 ID 索引参数，改显示名不会破坏预设
  - 不碰 After Effects 自己的任何文件

编码
  - 本版写 GBK，这是在本机实测定的正确编码（中文 Windows + AE 25.1 +
    Continuum 2026）：写一处、读回字节、用 GBK 和 UTF-8 各解一次，
    GBK 解出通顺中文。
  - 不要按 AE 版本号选编码。早期有一版就是这么猜的，选了 UTF-8，
    结果界面乱码（「妯＄硦」）＋一添加效果就报「无法初始化该效果」。

限制
  - Continuum 2026 Adobe v19.0.0（本机 build 19.0.0.327）
  - 适用于中文 Windows 上的 AE 25.1（GBK），即本机实测配置
  - 参数名只有中文（槽位按英文长度分配，放不下第二种语言）
  - 部分字符串是**有意保留英文**，不是漏翻：内部键 / 配置键 / PE 导出导入名
    （翻了 DLL 加载失败，WinError 127）、宿主名单、类型枚举、授权串、Qt 串、
    以及极短栏位（Pin / Hue）；另有 5 个分组是 "BCC VR"（仅 6 字节）
  - 已知遗留（都不影响使用）：约 1057 处属于 3D Objects 插件自带的时间线
    面板（在 .rsrc 里，另一套 UI）；AE 三支引擎的 .rsrc 各有 66 处命令/菜单
    表；142 处参数名经逐条判定后保留英文（131 处来自【hyg2 回填】+ 11 处
    BCC+ 单元名来自【崩溃修复】第 3 批，不是"被跳过"，是确认不该翻）
  - Continuum 升级后需重新打补丁

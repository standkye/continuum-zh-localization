# -*- coding: utf-8 -*-
"""第三版 DLL 参数名补丁 —— 把漏掉的「参数名池」补上

背景（见 _work/_cmp_ctx.txt / _miss_probe.txt / _need_translate.txt）：
  上一版只替换了 dll_chains.json 里的槽位（15181 处，能显示中文，用户已验证）。
  但每支引擎 DLL 里**还有第二/第三处同名参数名池**没被链条提取器抓到 ——
  证据：`Width` / `Height` / `Blur` / `Channel` / `Rotate` / `Pivot Point` 等
  在 .rdata 里确实是**独立 NUL 记号**（前字节=NUL、后字节=NUL），
  而且左侧邻居就是 `Mixed|Left Only|Right Only` / `Spin|Rotate|Tumble` 这类
  枚举串 —— 典型的参数标签池，不是配置键。

本版策略（两层，互不干扰）：
  [已证集合] chains 槽位 —— 原样保留上一版行为（这一块用户实测正常，不动）
  [新增集合] .rdata / _RDATA 里所有独立 NUL 记号 —— 新增，但必须过三道闸门：
     闸 1 形状：首字符是大写字母或数字；不含 '_'；不含 '::'
              （挡掉 scaleX / peakHold / pcfo.depth.rm.mode / Pref_Type 这类键）
     闸 2 邻居：往前 6 个记号内不得出现「标识符样」串（含 '_' 或 '.' 或首字符小写）
              （挡掉 `Pref_Type/Pref_Value` 后面那个 `Color`、`aw.watchFolder` 后面那个 `Channel`）
     闸 3 容量：GBK 译名 + NUL 必须塞得进「到下一个非 NUL 字节」的距离
  另外全程套用内部键黑名单（NEVER），一路不翻。

⚠️ 只写 .rdata / _RDATA（新增集合）与 chains 所在区（已证集合）；
   .text 绝不触碰；文件长度必须不变。
"""
import os, re, json, bisect, struct

WORK = r"D:\Programming project\插件汉化\_work"
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"
OUT_DLL = os.path.join(WORK, 'patched_dll_d')
os.makedirs(OUT_DLL, exist_ok=True)
ENC = 'gbk'

NEW_SECTIONS = {'.rdata', '_RDATA'}          # 新增集合只在这两个节里动手

# ★ 位置排除区：(标记串, 向前扩, 向后扩) —— 命中即整段跳过
EXCL = [
    (b'Pref_Type',               64, 320),   # 序列化类型名表 Color/Blue/Alpha/Size/Data
    (b'BCC_OPT_PFDIR',           64, 512),   # 安装目录名清单 Presets/Styles/Images/...
    (b'PFDirectory',             64, 512),
    (b'PDDirectory',             64, 512),
    (b'haspsl-adminmode',        64, 512),   # HASP/RLM 授权字段
    (b'network_seats_to_consume', 64, 512),
    (b'reslic',                  64, 512),
    (b'InstallDate',             64, 512),   # 许可信息 Filmora/Dongle/Rehostable
    (b'durationChanged',         64, 320),   # Qt 对象名/信号名
    (b'activeObjectChanged',     64, 320),
    (b'multiFrameModeChanged',   64, 320),
    (b'invalidate',              64, 320),
    (b'ObjectArg',               64, 320),
]
TOKEN_RE = re.compile(rb'[\x20-\x7e]+')

# ---------------------------------------------------------------- 内部键黑名单
NEVER = {
    'resources', 'documentation',
    'filter version', 'creation date', 'category',
    'preset name', 'filter name', 'preset type', 'file path',
    'description', 'author', 'client',
    'presetname', 'filtername', 'filterversion', 'datetime', 'duration',
    'debug logging', 'version update check previous',
    'bcc avx licensing', 'bcc effects list',
    'bcc motion tracker fcp', 'bcc motion tracker prm',
    'bcc motion tracker avid', 'bcc motion tracker vegas',
    'bcc motion tracker resolve',
    'launch mocha mask', 'launch mocha track', 'mocha init - render',
    'pixelchooser mocha preset load dummy',
    'load pixelchooser and mocha with preset',
    'hide disabled parameters', 'use 4k gpu buffers',
    'gpu anti alias buffer level',
    'borisplugins', 'filtersets', 'utilities', 'bin',
    'stringmap', 'stringpair', 'stringid', 'stringvalue',
    'borisfxdirect', 'bfx-license-tool', 'bfx-version-update',
    'mocha continuum.app',
    # 本版新增的守卫（.rdata 里出现过的键样串）
    'pref_type', 'pref_value', 'alpha type', 'pointcount',
    'string', 'int', 'float', 'bool', 'double', 'long', 'void',
    'uint32', 'uint8', 'uint16', 'int32',
    'application', 'key', 'value', 'id', 'name', 'type',
}

# ---------------------------------------------------------------- 词典
param_zh = json.load(open(os.path.join(WORK, 'param_zh.json'), encoding='utf-8'))
for extra in ('hand_all.json', 'hand_other.json', 'hand_other2.json', 'gap_zh.json',
              'batch5_ename.json', 'batch6_ui.json', 'batch7_miss.json',
              'batch8_miss.json', 'batch9_miss.json', 'batch10_miss.json'):
    fp = os.path.join(WORK, extra)
    if os.path.exists(fp):
        param_zh.update(json.load(open(fp, encoding='utf-8')))
SHORT = json.load(open(os.path.join(WORK, 'gap_zh_short.json'), encoding='utf-8'))
chains = json.load(open(os.path.join(WORK, 'dll_chains.json'), encoding='utf-8'))

# 宿主 / 平台名单（用于「上下文守卫」）：这些串本身不是参数标签，
# 而是 DLL 里那张「支持的宿主软件」列表。它周围一圈的 Red / Combustion / Corel /
# Quantel / Natron 等**绝不能翻**（把它们当成颜色名/效果名翻出来会变成笑话）。
# ⚠️ 这些词本身不一定永不翻译（例如 Red 在参数池里就是「红」通道），
#    只在**近旁出现**时把该位置判为名单上下文而跳过。
HOST = {
    'Final Cut Pro', 'FinalCutPro', 'Motion', 'Red', 'Combustion', 'OpenFX',
    'Cyberlink PowerDirector', 'Corel', 'Edius Title Generator',
    'PF Pixel Format Suite', ' OBSOLETE', 'Optics', 'Silhouette',
    'AfterEffects', 'After Effects', 'PremierePro', 'Premiere',
    'SonyVegas', 'Sony Vegas', 'MagixMovieStudio', 'MagixVideoProX',
    'SonyCatalyst', 'EyeonFusion', 'AssimilateScratch', 'Quantel', 'Natron',
    'HitFilm', 'HITFILM', 'HitFilmVegasEffects', 'SGOMambaFX', 'Nucoda',
    'WondershareFilmora', 'Lightworks', 'Autograph', 'AutodeskFlame',
    'Baselight', 'Mistika', 'Avid Media Composer', 'Vegas Pro', 'Vegas Pro 13.0',
    'Motion4', 'Nuke', 'Resolve', 'DaVinci Resolve', 'BFX_PROFILE_OPENCL',
}

out = []
def p(s=''):
    out.append(str(s))
    print(s, flush=True)

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


def protected_ranges(d):
    """★ 导出名表 / 导入名表里每个名字字符串占的区间。
    这些串看着也是 .rdata 里的普通 C 串，但改掉等于给导出函数改名
    （实测：把导出的 `Common` 改成 `通用` 后，三支 AE 引擎 DLL 全部
     LoadLibrary 失败 WinError 127 —— 按名导入找不到过程）。
    所以任何落在这个区间里的写入都必须放弃。返回按起点排序的 [(start, end)]。
    """
    pe = d.find(b'PE\x00\x00')
    if pe < 0:
        return []
    nsec = int.from_bytes(d[pe + 6:pe + 8], 'little')
    optsz = int.from_bytes(d[pe + 20:pe + 22], 'little')
    opt = pe + 24
    magic = int.from_bytes(d[opt:opt + 2], 'little')
    ddoff = opt + (112 if magic == 0x20b else 96)

    secs = []
    for i in range(nsec):
        o = opt + optsz + i * 40
        va = int.from_bytes(d[o + 12:o + 16], 'little')
        rsize = int.from_bytes(d[o + 16:o + 20], 'little')
        roff = int.from_bytes(d[o + 20:o + 24], 'little')
        vsz = int.from_bytes(d[o + 8:o + 12], 'little')
        secs.append((va, max(vsz, rsize), roff))

    def r2o(rva):
        for va, vsz, roff in secs:
            if va <= rva < va + vsz:
                return roff + (rva - va)
        return None

    def add(off):
        if off is None:
            return
        e = d.find(b'\x00', off)
        if e > off:
            res.append((off, e + 1))

    res = []
    # --- 导出名 ---
    er, esz = struct.unpack_from('<II', d, ddoff)
    if er:
        eo = r2o(er)
        if eo is not None:
            nnam = struct.unpack_from('<I', d, eo + 24)[0]
            an = r2o(struct.unpack_from('<I', d, eo + 32)[0])
            if an is not None:
                for i in range(nnam):
                    add(r2o(struct.unpack_from('<I', d, an + i * 4)[0]))
    # --- 导入名（DLL 名 + 按名导入的函数名）---
    ir, isz = struct.unpack_from('<II', d, ddoff + 8)
    if ir:
        o = r2o(ir)
        while o is not None:
            desc = d[o:o + 20]
            if len(desc) < 20 or desc == b'\x00' * 20:
                break
            add(r2o(struct.unpack_from('<I', d, o + 12)[0]))
            frva = struct.unpack_from('<I', d, o)[0]
            t = r2o(frva) if frva else None
            while t is not None:
                v = int.from_bytes(d[t:t + 8], 'little')
                if v == 0:
                    break
                if not (v >> 63):                 # 最高位=0 表示按名字导入
                    p2 = r2o(v & 0x7fffffff)
                    if p2 is not None:            # 前 2 字节是 hint，跳过
                        add(p2 + 2)
                t += 8
            o += 20
    res.sort()
    return res


def word_like(t):
    """像个「词」而不是二进制碎片（挡掉 o7 / .cng / PJ1 / %s ( 之类）"""
    if len(t) < 4 or not t[0].isalpha():
        return False
    return all(ch.isalnum() or ch in " .-_()/&+" for ch in t)

def ident_like(t):
    """「配置键样」的判据。★ 只认两个强信号：
         · 含下划线 —— Pref_Type / Options_Map / BFX_AudioCacheCleanup 式内部键
         · 点号且无空格 —— pcfo.depth.rm.mode / aw.watchFolder 式路径键
       不再把「小写开头」一概算键：BCCPlus 的表是「显示名 + 小写键」交替
       （Scale|scale、Width|width、Matte|matte…），按小写拦会误伤要翻的显示名。
       参数标签里的点号很常见（Rad. Position Seed / Ang. Channel / Pos. X），
       所以「点号」必须配合「无空格」才当键。
    """
    if not word_like(t):
        return False
    if '_' in t:
        return True
    if '.' in t and ' ' not in t:
        return True
    return False

def shape_ok(t):
    if len(t) < 2 or len(t) > 60:
        return False
    if not t.isascii():
        return False
    if not (t[0].isupper() or t[0].isdigit()):
        return False
    if '_' in t or '::' in t:
        return False
    return True

p('=== 第四版 DLL 补丁（编码 %s，内部键黑名单 %d 条）===' % (ENC, len(NEVER)))
p('词典合计 %d 条（含新增 gap_zh %d 条）'
  % (len(param_zh), len(json.load(open(os.path.join(WORK, 'gap_zh.json'), encoding='utf-8')))))
p()

writes = []          # (dll, off, old, new, sec, kind, avail, nz)
                     #   avail = 到下一个非 NUL 字节的距离（容量上界）
                     #   nz    = 实际被清零的字节数 = max(译名长度, 原文长度) + 1
                     #           ★ 必须登记 nz，否则尾清零会落在「声明区间」之外，
                     #             独立复算会把它误判成野改动。
stat = {}
tot = {'proven': 0, 'new': 0, 'ov': 0, 'us': 0, 'ex': 0, 'excl': 0, 'prot': 0,
       'gate_shape': 0, 'gate_nb': 0, 'gate_host': 0, 'lap': 0, 'enum': 0,
         'bad_off': 0}

for name, ch in sorted(chains.items()):
    src = os.path.join(BK, name)
    if not os.path.exists(src):
        src = os.path.join(CONT, name)
    d = bytearray(open(src, 'rb').read())
    orig_len = len(d)
    secs = sections(bytes(d))

    # ---- 位置排除区（★ 第四版新增）----
    # 这些区域里的串**看着像参数名但其实不能翻**，而且同一个词在别处该翻，
    # 所以只能按**位置**排除，不能按词拉黑名单。
    #   Pref_Type 类型名表 : Color/Blue/Green/Alpha/Size/Data 是序列化类型标识
    #   目录名表          : Presets/Styles/Images/Particles 是真目录名（同 Resources）
    #   授权串            : haspsl / NetTime / Master / Process 是 RLM/HASP 字段
    #   许可信息          : InstallDate / Filmora / Dongle / Rehostable
    #   Qt 对象名         : durationChanged / invalidate / Layer / OutputSize
    excl = []
    for mk, back, fwd in EXCL:
        st = 0
        while True:
            k = d.find(mk, st)
            if k < 0:
                break
            excl.append((k - back, k + fwd))
            st = k + 1
    def in_excl(off):
        for lo, hi in excl:
            if lo <= off < hi:
                return True
        return False

    # ★ 导出/导入名保护：这些串改了会让宿主按名导入失败（WinError 127），一律不碰
    prot = protected_ranges(d)
    prot_starts = [x[0] for x in prot]

    def in_prot(off):
        i = bisect.bisect_right(prot_starts, off) - 1
        return i >= 0 and off < prot[i][1]

    plan = {}
    L = {'proven': 0, 'new': 0, 'ov': 0, 'us': 0, 'ex': 0, 'excl': 0, 'prot': 0,
         'gate_shape': 0, 'gate_nb': 0, 'gate_host': 0, 'lap': 0, 'enum': 0,
         'bad_off': 0}

    # ============ 1) 已证集合：chains 槽位（原样保留上一版行为） ============
    for off_s, arr in ch.items():
        cur = int(off_s)
        for s in arr:
            slot = max(8, ((len(s) + 1 + 7) // 8) * 8)
            if s.strip().lower() in NEVER:
                L['ex'] += 1
                cur += slot
                continue
            if in_prot(cur):
                L['prot'] += 1
                cur += slot
                continue
            zh = param_zh.get(s)
            if zh:
                try:
                    b = zh.encode(ENC)
                except UnicodeEncodeError:
                    b = None
                if b is None or len(b) > slot - 1:
                    L['ov'] += 1
                else:
                    raw = d[cur:cur + slot]
                    nul = raw.find(b'\x00')
                    safe = (nul > 0 and not any(raw[nul:]) and len(raw) == slot)
                    if safe:
                        plan[cur] = (s, zh, slot, sec_of(secs, cur), 'proven')
                        L['proven'] += 1
                    else:
                        L['us'] += 1
            cur += slot

    # ============ 2) 新增集合：.rdata / _RDATA 全量独立记号 ============
    # ★★ base = 本次补丁落盘【之前】的字节快照（即英文原文件）。
    #    所有「是不是独立记号」「可用空间多大」的判定必须基于 base，
    #    绝不能基于正在被改写的 d —— 否则尾清零把枚举列表的分隔符 '|'
    #    覆盖成 NUL 后，后一个单词会"变成"独立记号，引发链式写入，
    #    逐个破坏整个 `None|Bounce|Stick|Slide|Disappear` 选项表
    #    （实测 133 条坏写入，导致 AE 一用纹理效果就崩）。
    base = bytes(d)
    toks = []
    for m in TOKEN_RE.finditer(base):
        s, e = m.span()
        if s > 0 and base[s - 1] != 0:
            continue
        if e >= len(base) or base[e] != 0:
            continue                      # 必须 NUL 结尾才可能是 C 串
        sec = sec_of(secs, s)
        if sec not in NEW_SECTIONS:
            continue
        toks.append((s, e, m.group().decode('ascii', 'replace'), sec))

    offs = [t[0] for t in toks]

    for i, (s, e, tok, sec) in enumerate(toks):
        if s in plan:
            continue
        if tok.strip().lower() in NEVER:
            L['ex'] += 1
            continue
        if in_excl(s):
            L['excl'] += 1
            continue
        if in_prot(s):
            L['prot'] += 1
            continue
        zh = param_zh.get(tok)
        if not zh:
            continue
        if not shape_ok(tok):
            L['gate_shape'] += 1
            continue
        # 闸 2c：枚举选项表保护。'A|B|C' 这种用 '|' 串起来的下拉选项表，
        #        往前找最近的非 NUL 字节，若是 '|' 则说明本记号是表里的一项，
        #        整表是一个 C 串，翻任何一项都会把表写坏。
        q = s - 1
        while q >= 0 and base[q] == 0:
            q -= 1
        if q >= 0 and base[q] in (0x7C,):          # '|'
            L['enum'] += 1
            continue
        # 闸 2a：往前 96 字节内出现「标识符样」串 -> 判为配置区（键后面跟着的值不当标签翻）
        j0 = bisect.bisect_left(offs, s - 96)
        if any(ident_like(toks[k][2]) for k in range(j0, i)):
            L['gate_nb'] += 1
            continue
        # 闸 2b：±128 字节内出现宿主/平台名单串 -> 判为名单上下文（保留英文）
        j1 = bisect.bisect_right(offs, s + 128)
        if any(toks[k][2] in HOST for k in range(j0, j1) if k != i):
            L['gate_host'] += 1
            continue
        j = e
        while j < len(base) and base[j] == 0:
            j += 1
        avail = j - s
        try:
            b = zh.encode(ENC)
        except UnicodeEncodeError:
            b = None
        if b is None or len(b) + 1 > avail:
            # 主译名放不下 -> 试短译名；都不行就保留英文（绝不截断、绝不越界）
            nb2 = None
            sh = SHORT.get(tok)
            if sh:
                try:
                    sb = sh.encode(ENC)
                except UnicodeEncodeError:
                    sb = None
                if sb and len(sb) + 1 <= avail:
                    nb2 = sb
                    zh = sh
            if nb2 is None:
                L['ov'] += 1
                continue
            b = nb2
        plan[s] = (tok, zh, avail, sec, 'new')
        L['new'] += 1

    # ============ 3) 落盘 ============
    #  ★★ 统一闸门（不分已证/新增集合）：写入点必须满足
    #      (a) 英文原文件里 off-1 是 NUL —— 否则它躺在【别的字符串内部】
    #      (b) 往前最近的非 NUL 字节不是 '|' —— 否则它是枚举选项表的一项
    #           （'None|Bounce|Stick|Slide|Disappear' 整表是一个 C 串）
    #     违反任一条件都会把宿主字符串写坏。实测 133 条坏写入
    #     -> AE 一加「纹理」效果就崩（BCC.log: 'BCC+TiBCCnt'）。
    for _off in list(plan.keys()):
        if _off <= 0 or _off >= len(base) or base[_off - 1] != 0:
            del plan[_off]
            L['bad_off'] += 1
            continue
        _q = _off - 1
        while _q >= 0 and base[_q] == 0:
            _q -= 1
        if _q >= 0 and base[_q] == 0x7C:
            del plan[_off]
            L['bad_off'] += 1
    #  ★ 区间去重：链表里有「幻影槽」——把 'Fog On' 内部的 'On' 当成了一条独立记录。
    #    两个写入区间叠在一起时，后一条会改掉前一条的尾巴（实测生成过 '雾启开'）。
    #    按偏移排序后一旦发现与已写区间重叠就丢掉这条，保留先生效的那条。
    end_prev = -1
    for off, (old, zh, avail, sec, kind) in sorted(plan.items()):
        b = zh.encode(ENC)
        # 硬断言：GBK 译名 + NUL 必须塞得进可用空间，任何越界直接炸掉而不是静默写坏
        assert len(b) + 1 <= avail, ('OVERFLOW', name, hex(off), old, zh, len(b), avail)
        # ★ 必须把原英文串的余尾一并清零！
        #   译名比原文短时（如 'FEC Replace Color' -> 'FEC替换颜色'），
        #   只写 zh + NUL 会留下 `Color` / `ion` / `ency` 这类**残尾**，
        #   它们会变成串池里凭空多出来的独立记号（本次就是靠对账才发现的）。
        nz = max(len(b), len(old)) + 1
        assert nz <= avail, ('TAIL', name, hex(off), old, zh, nz, avail)
        if off < end_prev:
            L['lap'] += 1
            continue
        d[off:off + nz] = b'\x00' * nz
        d[off:off + len(b)] = b
        writes.append((name, off, old, zh, sec, kind, avail, nz))
        end_prev = off + nz

    assert len(d) == orig_len, name
    open(os.path.join(OUT_DLL, name), 'wb').write(bytes(d))
    for k in L:
        tot[k] += L[k]
    p('%-30s 已证 %5d + 新增 %5d = %5d   容量不足 %4d  排除键 %4d  排除区 %4d  导入导出名 %4d  形状拦 %3d  邻居拦 %4d  宿主拦 %4d  区间重叠丢弃 %3d'
      % (name, L['proven'], L['new'], L['proven'] + L['new'],
         L['ov'], L['ex'], L['excl'], L['prot'], L['gate_shape'], L['gate_nb'],
         L['gate_host'], L['lap']))

p()
p('合计：已证集合 %d，新增集合 %d，总替换 %d' % (tot['proven'], tot['new'], tot['proven'] + tot['new']))
p('      容量不足保留英文 %d，排除内部键 %d，排除区 %d，导入导出名 %d，形状拦截 %d，邻居拦截 %d，宿主名单拦截 %d，区间重叠丢弃 %d'
  % (tot['ov'], tot['ex'], tot['excl'], tot['prot'], tot['gate_shape'],
     tot['gate_nb'], tot['gate_host'], tot['lap']))
p()

# 段分布 & 校验
import collections
bysec = collections.Counter(w[4] for w in writes)
p('改动落点所在节：%r' % dict(bysec))
p('触碰 .text 的次数：%d' % sum(v for k, v in bysec.items() if k == '.text'))
p('新增集合样本（前 25 条）：')
for w in [x for x in writes if x[5] == 'new'][:25]:
    p('    %-28s 0x%08X %-7s av=%-3d %-26s -> %s' % (w[0].replace('Continuum_', ''), w[1], w[4], w[6], w[2][:26], w[3]))

json.dump(writes, open(os.path.join(WORK, '_fix4_writes.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=0)
p()
p('写入清单已存 _fix4_writes.json（%d 条）' % len(writes))

open(os.path.join(WORK, '_fix4_dll.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('DONE')

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
import os, re, json, bisect

WORK = r"D:\Programming project\插件汉化\_work"
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"
OUT_DLL = os.path.join(WORK, 'patched_dll_c')
os.makedirs(OUT_DLL, exist_ok=True)
ENC = 'gbk'

NEW_SECTIONS = {'.rdata', '_RDATA'}          # 新增集合只在这两个节里动手
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
    'application', 'key', 'value', 'id', 'name', 'type',
}

# ---------------------------------------------------------------- 词典
param_zh = json.load(open(os.path.join(WORK, 'param_zh.json'), encoding='utf-8'))
for extra in ('hand_all.json', 'hand_other.json', 'hand_other2.json', 'gap_zh.json'):
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

def ident_like(t):
    if '_' in t or '.' in t:
        return True
    return bool(t) and t[0].islower()

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

p('=== 第三版 DLL 补丁（编码 %s，内部键黑名单 %d 条）===' % (ENC, len(NEVER)))
p('词典合计 %d 条（含新增 gap_zh %d 条）'
  % (len(param_zh), len(json.load(open(os.path.join(WORK, 'gap_zh.json'), encoding='utf-8')))))
p()

writes = []          # (dll, off, old, new, sec, kind, avail, nz)
                     #   avail = 到下一个非 NUL 字节的距离（容量上界）
                     #   nz    = 实际被清零的字节数 = max(译名长度, 原文长度) + 1
                     #           ★ 必须登记 nz，否则尾清零会落在「声明区间」之外，
                     #             独立复算会把它误判成野改动。
stat = {}
tot = {'proven': 0, 'new': 0, 'ov': 0, 'us': 0, 'ex': 0,
       'gate_shape': 0, 'gate_nb': 0, 'gate_host': 0}

for name, ch in sorted(chains.items()):
    src = os.path.join(BK, name)
    if not os.path.exists(src):
        src = os.path.join(CONT, name)
    d = bytearray(open(src, 'rb').read())
    orig_len = len(d)
    secs = sections(bytes(d))

    plan = {}        # off -> (old, new, avail, sec, kind)
    L = {'proven': 0, 'new': 0, 'ov': 0, 'us': 0, 'ex': 0,
         'gate_shape': 0, 'gate_nb': 0, 'gate_host': 0}

    # ============ 1) 已证集合：chains 槽位（原样保留上一版行为） ============
    for off_s, arr in ch.items():
        cur = int(off_s)
        for s in arr:
            slot = max(8, ((len(s) + 1 + 7) // 8) * 8)
            if s.strip().lower() in NEVER:
                L['ex'] += 1
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
    toks = []
    for m in TOKEN_RE.finditer(bytes(d)):
        s, e = m.span()
        if s > 0 and d[s - 1] != 0:
            continue
        if e >= len(d) or d[e] != 0:
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
        zh = param_zh.get(tok)
        if not zh:
            continue
        if not shape_ok(tok):
            L['gate_shape'] += 1
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
        while j < len(d) and d[j] == 0:
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
        d[off:off + nz] = b'\x00' * nz
        d[off:off + len(b)] = b
        writes.append((name, off, old, zh, sec, kind, avail, nz))

    assert len(d) == orig_len, name
    open(os.path.join(OUT_DLL, name), 'wb').write(bytes(d))
    for k in L:
        tot[k] += L[k]
    p('%-30s 已证 %5d + 新增 %5d = %5d   容量不足 %4d  槽位存疑 %3d  排除键 %4d  形状拦 %3d  邻居拦 %4d  宿主名单拦 %4d'
      % (name, L['proven'], L['new'], L['proven'] + L['new'],
         L['ov'], L['us'], L['ex'], L['gate_shape'], L['gate_nb'], L['gate_host']))

p()
p('合计：已证集合 %d，新增集合 %d，总替换 %d' % (tot['proven'], tot['new'], tot['proven'] + tot['new']))
p('      容量不足保留英文 %d，槽位存疑 %d，排除内部键 %d，形状拦截 %d，邻居拦截 %d，宿主名单拦截 %d'
  % (tot['ov'], tot['us'], tot['ex'], tot['gate_shape'], tot['gate_nb'], tot['gate_host']))
p()

# 段分布 & 校验
import collections
bysec = collections.Counter(w[4] for w in writes)
p('改动落点所在节：%r' % dict(bysec))
p('触碰 .text 的次数：%d' % sum(v for k, v in bysec.items() if k == '.text'))
p('新增集合样本（前 25 条）：')
for w in [x for x in writes if x[5] == 'new'][:25]:
    p('    %-28s 0x%08X %-7s av=%-3d %-26s -> %s' % (w[0].replace('Continuum_', ''), w[1], w[4], w[6], w[2][:26], w[3]))

json.dump(writes, open(os.path.join(WORK, '_fix3_writes.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=0)
p()
p('写入清单已存 _fix3_writes.json（%d 条）' % len(writes))

open(os.path.join(WORK, '_fix3_dll.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('DONE')

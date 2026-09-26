# -*- coding: utf-8 -*-
"""verify_resid.py <补丁目录名>  —— 独立复核「这一版还剩哪些该翻没翻的英文参数名」

不 import fix4，常量自己抄一份，保证是**独立复算**而不是同一套逻辑自证。
分桶：
  NO_DICT  通过全部闸门、但词典里根本没有译文        → 该翻没翻（要补词）
  OV       词典有译文、但容量放不下（短译名也不够）  → 该翻没翻（要短译名）
  NB/HOST/EXCL/NEVER  被有意排除                     → 正确保留英文
"""
import os, re, json, bisect, collections, sys, struct

WORK = r"D:\Programming project\插件汉化\_work"
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
PATCH = os.path.join(WORK, sys.argv[1] if len(sys.argv) > 1 else 'patched_dll_d')
TAG = os.path.basename(PATCH.rstrip('\\/'))
NEW_SECTIONS = {'.rdata', '_RDATA'}
ENC = 'gbk'
TOKEN_RE = re.compile(rb'[\x20-\x7e]+')

EXCL = [
    (b'Pref_Type', 64, 320), (b'BCC_OPT_PFDIR', 64, 512), (b'PFDirectory', 64, 512),
    (b'PDDirectory', 64, 512), (b'haspsl-adminmode', 64, 512),
    (b'network_seats_to_consume', 64, 512), (b'reslic', 64, 512),
    (b'InstallDate', 64, 512), (b'durationChanged', 64, 320),
    (b'activeObjectChanged', 64, 320), (b'multiFrameModeChanged', 64, 320),
    (b'invalidate', 64, 320), (b'ObjectArg', 64, 320),
]

NEVER = {
    'resources', 'documentation', 'filter version', 'creation date', 'category',
    'preset name', 'filter name', 'preset type', 'file path',
    'description', 'author', 'client',
    'presetname', 'filtername', 'filterversion', 'datetime', 'duration',
    'debug logging', 'version update check previous',
    'bcc avx licensing', 'bcc effects list',
    'bcc motion tracker fcp', 'bcc motion tracker prm',
    'bcc motion tracker avid', 'bcc motion tracker vegas', 'bcc motion tracker resolve',
    'launch mocha mask', 'launch mocha track', 'mocha init - render',
    'pixelchooser mocha preset load dummy', 'load pixelchooser and mocha with preset',
    'hide disabled parameters', 'use 4k gpu buffers', 'gpu anti alias buffer level',
    'borisplugins', 'filtersets', 'utilities', 'bin',
    'stringmap', 'stringpair', 'stringid', 'stringvalue',
    'borisfxdirect', 'bfx-license-tool', 'bfx-version-update', 'mocha continuum.app',
    'pref_type', 'pref_value', 'alpha type', 'pointcount',
    'string', 'int', 'float', 'bool', 'double', 'long', 'void',
    'uint32', 'uint8', 'uint16', 'int32',
    'application', 'key', 'value', 'id', 'name', 'type',
}

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

DLLS = ['Continuum_AE_8Bit.dll', 'Continuum_AE_16Bit.dll', 'Continuum_AE_Float.dll',
        'Continuum_Common_AE.dll', 'Continuum_3DObjects_AE.dll', 'BCCPlus.dll']
SHORT_DLL = {d: d.replace('Continuum_', '').replace('_AE.dll', '') for d in DLLS}

param_zh = json.load(open(os.path.join(WORK, 'param_zh.json'), encoding='utf-8'))
for extra in ('hand_all.json', 'hand_other.json', 'hand_other2.json', 'gap_zh.json',
              'batch5_ename.json', 'batch6_ui.json', 'batch7_miss.json',
              'batch8_miss.json', 'batch9_miss.json', 'batch10_miss.json'):
    fp = os.path.join(WORK, extra)
    if os.path.exists(fp):
        param_zh.update(json.load(open(fp, encoding='utf-8')))
SHORT = json.load(open(os.path.join(WORK, 'gap_zh_short.json'), encoding='utf-8'))


def sections(d):
    pe = d.find(b'PE\x00\x00')
    nsec = int.from_bytes(d[pe + 6:pe + 8], 'little')
    optsz = int.from_bytes(d[pe + 20:pe + 22], 'little')
    base = pe + 24 + optsz
    r = []
    for i in range(nsec):
        o = base + i * 40
        nm = d[o:o + 8].rstrip(b'\x00').decode('ascii', 'replace')
        r.append((nm, int.from_bytes(d[o + 20:o + 24], 'little'),
                  int.from_bytes(d[o + 16:o + 20], 'little')))
    return r


def sec_of(secs, off):
    for nm, roff, rsize in secs:
        if roff <= off < roff + rsize:
            return nm
    return '?'


def word_like(t):
    if len(t) < 4 or not t[0].isalpha():
        return False
    return all((c.isalnum() or c in '.-_()&+/') for c in t)


def ident_like(t):
    if not word_like(t):
        return False
    if '_' in t:
        return True
    if '.' in t and ' ' not in t:
        return True
    return False


def cand_ok(t):
    """NO_DICT 桶专用更严的判据：只放「像是人写的标签」的串进来。
    .rdata 里还塞着大量查表用的 2 字节码（8C / TC / Vd / I@ ...），
    shape_ok 会把这些也放行，所以补词清单必须再收一道。"""
    if not (4 <= len(t) <= 48):
        return False
    if not t.isascii() or not t[0].isalpha() or not t[0].isupper():
        return False
    return all((c.isalnum() or c in ' -+.%&') for c in t)


def protected_ranges(d):
    """导出/导入名表里的名字字符串区间（与 fix4 同判据）。
    落在这里的英文串**不能翻** —— 改了等于给导出函数改名，宿主按名导入直接失败。"""
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

    res = []

    def add(off):
        if off is None:
            return
        e = d.find(b'\x00', off)
        if e > off:
            res.append((off, e + 1))

    er, esz = struct.unpack_from('<II', d, ddoff)
    if er:
        eo = r2o(er)
        if eo is not None:
            nnam = struct.unpack_from('<I', d, eo + 24)[0]
            an = r2o(struct.unpack_from('<I', d, eo + 32)[0])
            if an is not None:
                for i in range(nnam):
                    add(r2o(struct.unpack_from('<I', d, an + i * 4)[0]))
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
                if not (v >> 63):
                    p2 = r2o(v & 0x7fffffff)
                    if p2 is not None:
                        add(p2 + 2)
                t += 8
            o += 20
    res.sort()
    return res


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


out = []


def p(s=''):
    out.append(str(s))
    print(s, flush=True)


buckets = collections.defaultdict(list)   # bucket -> [(dll, tok, off, avail, pre, post)]
for dll in DLLS:
    a = open(os.path.join(BK, dll), 'rb').read()
    bp = os.path.join(PATCH, dll)
    if not os.path.exists(bp):
        p('!! 缺文件 ' + bp)
        continue
    b = open(bp, 'rb').read()
    secs = sections(a)
    excl = []
    for mk, back, fwd in EXCL:
        st = 0
        while True:
            k = b.find(mk, st)
            if k < 0:
                break
            excl.append((k - back, k + fwd))
            st = k + 1

    def in_excl(off):
        for lo, hi in excl:
            if lo <= off < hi:
                return True
        return False

    prot = protected_ranges(a)                 # 用英文基准算，原串两边一致
    prot_starts = [x[0] for x in prot]

    def in_prot(off):
        i = bisect.bisect_right(prot_starts, off) - 1
        return i >= 0 and off < prot[i][1]

    toks = []
    for m in TOKEN_RE.finditer(b):
        s, e = m.span()
        if s > 0 and b[s - 1] != 0:
            continue
        if e >= len(b) or b[e] != 0:
            continue
        toks.append((s, e, m.group().decode('ascii', 'replace'), sec_of(secs, s)))
    offs = [t[0] for t in toks]

    for i, (s, e, tok, sec) in enumerate(toks):
        if sec not in NEW_SECTIONS:
            continue
        if not shape_ok(tok):
            continue
        if b[s:e] != a[s:e]:
            continue                      # 已改过
        low = tok.strip().lower()
        if low in NEVER:
            buckets['NEVER'].append((SHORT_DLL[dll], tok, s, 0, [], []))
            continue
        j0 = bisect.bisect_left(offs, s - 96)
        j1 = bisect.bisect_right(offs, s + 128)
        pre = [toks[k][2][:26] for k in range(j0, i)][-6:]
        post = [toks[k][2][:26] for k in range(i + 1, j1)][:3]
        if in_excl(s):
            buckets['EXCL'].append((SHORT_DLL[dll], tok, s, 0, pre, post))
            continue
        if in_prot(s):
            buckets['PROT'].append((SHORT_DLL[dll], tok, s, 0, pre, post))
            continue
        if any(ident_like(toks[k][2]) for k in range(j0, i)):
            buckets['NB'].append((SHORT_DLL[dll], tok, s, 0, pre, post))
            continue
        if any(toks[k][2] in HOST for k in range(j0, j1) if k != i):
            buckets['HOST'].append((SHORT_DLL[dll], tok, s, 0, pre, post))
            continue
        j = e
        while j < len(a) and a[j] == 0:
            j += 1
        avail = j - s
        if tok in param_zh:
            zh = param_zh[tok]
            try:
                nb = len(zh.encode(ENC)) + 1
            except UnicodeEncodeError:
                nb = 10 ** 9
            sh = SHORT.get(tok, '')
            try:
                sb = len(sh.encode(ENC)) + 1 if sh else 10 ** 9
            except UnicodeEncodeError:
                sb = 10 ** 9
            buckets['OV'].append((SHORT_DLL[dll], tok, s, avail, pre,
                                  ['need=%d short=%s(%d)' % (nb, sh or '-', sb)]))
        else:
            if cand_ok(tok):
                buckets['NO_DICT'].append((SHORT_DLL[dll], tok, s, avail, pre, post))
            else:
                buckets['JUNK'].append((SHORT_DLL[dll], tok, s, avail, pre, post))

names = {k: collections.defaultdict(list) for k in buckets}
for k in buckets:
    for rec in buckets[k]:
        names[k][rec[1]].append(rec)


def emit(tag, title, note=''):
    if tag not in names:
        return
    lst = names[tag]
    n_occ = sum(len(v) for v in lst.values())
    p('-' * 104)
    p('【%s】%s   名字 %d 个 / 出现 %d 处' % (tag, title, len(lst), n_occ))
    if note:
        p('    ' + note)
    p('-' * 104)
    for tok in sorted(lst, key=lambda t: (-len(lst[t]), t)):
        v = lst[tok]
        p('  %-34s %2d 处 (%s)' % (tok, len(v), ','.join(sorted(set(x[0] for x in v)))))
        for (d, tk, s, avail, pre, post) in v[:2]:
            p('        [%s] 0x%08X avail=%-3d 前: %s' % (d, s, avail, ' | '.join(pre)))
            if post:
                p('                                后: %s' % ' | '.join(post))
    p()


p('=' * 104)
p('独立复核：%s   （英文基准 %s）' % (TAG, BK))
p('=' * 104)
p()
for k in ('NO_DICT', 'OV', 'NB', 'HOST', 'EXCL', 'PROT', 'NEVER', 'JUNK'):
    lst = names[k]
    p('  %-9s 名字 %5d / 出现 %6d' % (k, len(lst), sum(len(v) for v in lst.values())))
p()
emit('NO_DICT', '闸门全过、词典却没收 —— 真正「该翻没翻」', '这些是补词目标')
emit('OV', '词典有译文但容量放不下 —— 需要短译名')
emit('NB', '前 96 字节内有配置键样串 —— 有意保留', 'Preference/路径键上下文')
emit('HOST', '±128 字节内有宿主软件名单 —— 有意保留')
emit('EXCL', '落在位置排除区（类型名表/目录名/授权/Qt）—— 有意保留')
emit('PROT', '落在导出名/导入名表 —— 有意保留', '改了等于给导出函数改名，宿主 LoadLibrary 会 WinError 127')
emit('NEVER', '内部键黑名单 —— 有意保留')

# JUNK 只出统计，不出明细（4 万条二进制碎片没意义）
if 'JUNK' in names:
    p('-' * 104)
    p('【JUNK】.rdata 里的二进制碎片/查表码（非标签，已被 cand_ok 剔除）  名字 %d 个 / 出现 %d 处'
      % (len(names['JUNK']), sum(len(v) for v in names['JUNK'].values())))
    p('-' * 104)
    p()

open(os.path.join(WORK, '_resid_%s.txt' % TAG), 'w', encoding='utf-8').write('\n'.join(out))

# 同时落一份机器可读的分桶表（token 原样，不带报告里的对齐空格）
with open(os.path.join(WORK, '_buckets_%s.tsv' % TAG), 'w', encoding='utf-8') as f:
    f.write('bucket\tname\tcount\tdlls\tavail\tpre\tpost\n')
    for k in sorted(names):
        for tok, v in sorted(names[k].items(), key=lambda kv: (-len(kv[1]), kv[0])):
            f.write('%s\t%s\t%d\t%s\t%d\t%s\t%s\n'
                    % (k, tok, len(v), ','.join(sorted(set(x[0] for x in v))),
                       v[0][3], ' | '.join(v[0][4]), ' | '.join(v[0][5])))

print('\nDONE -> _resid_%s.txt    NO_DICT=%d  OV=%d'
      % (TAG, len(names['NO_DICT']), len(names['OV'])))

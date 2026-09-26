# -*- coding: utf-8 -*-
"""诊断：本版补丁后仍残留的英文参数名，各自被哪一道闸门拦下 / 落在哪个节。

分类（互斥，按优先级）：
  SECTION   : 落在 .rdata/_RDATA 以外的节（.data/.rsrc/...）—— 本版根本没扫
  NUL_BOUND : 前后不是「NUL 结尾」的独立 C 串（可能是数据块里的可打印片段）
  NEVER     : 内部键黑名单
  SHAPE     : 形状闸门（首字符小写 / 含下划线）
  NEIGHBOR  : 邻居闸门（前 6 个记号里出现标识符样串）
  CAPACITY  : 容量不足（GBK 译名 + NUL 塞不进）
  PATCHED   : 其实已改（不应出现在"残留"里，用于自检）
"""
import os, re, json, collections

WORK = r"D:\Programming project\插件汉化\_work"
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"
PATCH = os.path.join(WORK, 'patched_dll_c')
NEW_SECTIONS = {'.rdata', '_RDATA'}
TOKEN_RE = re.compile(rb'[\x20-\x7e]+')

NEVER = {
    'resources', 'documentation', 'filter version', 'creation date', 'category',
    'preset name', 'filter name', 'preset type', 'file path', 'description', 'author',
    'client', 'presetname', 'filtername', 'filterversion', 'datetime', 'duration',
    'debug logging', 'version update check previous', 'bcc avx licensing', 'bcc effects list',
    'bcc motion tracker fcp', 'bcc motion tracker prm', 'bcc motion tracker avid',
    'bcc motion tracker vegas', 'bcc motion tracker resolve', 'launch mocha mask',
    'launch mocha track', 'mocha init - render', 'pixelchooser mocha preset load dummy',
    'load pixelchooser and mocha with preset', 'hide disabled parameters',
    'use 4k gpu buffers', 'gpu anti alias buffer level', 'borisplugins', 'filtersets',
    'utilities', 'bin', 'stringmap', 'stringpair', 'stringid', 'stringvalue',
    'borisfxdirect', 'bfx-license-tool', 'bfx-version-update', 'mocha continuum.app',
    'pref_type', 'pref_value', 'alpha type', 'pointcount',
    'string', 'int', 'float', 'bool', 'double', 'long', 'void',
    'application', 'key', 'value', 'id', 'name', 'type',
}

param_zh = json.load(open(os.path.join(WORK, 'param_zh.json'), encoding='utf-8'))
for extra in ('hand_all.json', 'hand_other.json', 'hand_other2.json', 'gap_zh.json'):
    fp = os.path.join(WORK, extra)
    if os.path.exists(fp):
        param_zh.update(json.load(open(fp, encoding='utf-8')))

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
    return ('_' in t or '.' in t) or (bool(t) and t[0].islower())

def shape_ok(t):
    if len(t) < 2 or len(t) > 60 or not t.isascii():
        return False
    if not (t[0].isupper() or t[0].isdigit()):
        return False
    return not ('_' in t or '::' in t)

out = []
def p(s=''):
    out.append(str(s))
    print(s, flush=True)

reason = collections.Counter()
byreason_sec = collections.Counter()
samples = collections.defaultdict(list)
names_by_reason = collections.defaultdict(set)
per_dll = {}

for dll in ('Continuum_AE_8Bit.dll', 'Continuum_3DObjects_AE.dll', 'Continuum_AE_Float.dll',
            'Continuum_Common_AE.dll', 'BCCPlus.dll'):
    a = open(os.path.join(BK, dll), 'rb').read()
    b = open(os.path.join(PATCH, dll), 'rb').read()
    secs = sections(a)
    # 收集所有独立记号（不限制节）
    toks = []
    for m in TOKEN_RE.finditer(a):
        s, e = m.span()
        if s > 0 and a[s - 1] != 0:
            continue
        sec = sec_of(secs, s)
        toks.append((s, e, m.group().decode('ascii', 'replace'), sec))
    cnt = collections.Counter()
    for i, (s, e, tok, sec) in enumerate(toks):
        if tok not in param_zh:
            continue
        # 是否真的还是英文（回读）
        if not a[s:e] == b[s:e]:
            cnt['PATCHED'] += 1
            continue
        if sec not in NEW_SECTIONS:
            r = 'SECTION:' + sec
        elif e >= len(a) or a[e] != 0:
            r = 'NUL_BOUND'
        elif tok.strip().lower() in NEVER:
            r = 'NEVER'
        elif not shape_ok(tok):
            r = 'SHAPE'
        elif any(ident_like(toks[j][2]) for j in range(max(0, i - 6), i)):
            r = 'NEIGHBOR'
        else:
            j = e
            while j < len(a) and a[j] == 0:
                j += 1
            if len(param_zh[tok].encode('gbk')) + 1 > (j - s):
                r = 'CAPACITY'
            else:
                r = 'UNKNOWN'
        cnt[r] += 1
        reason[r] += 1
        byreason_sec[r + ' @ ' + sec] += 1
        names_by_reason[r].add(tok)
        if len(samples[r]) < 12:
            samples[r].append('%s 0x%08X %r' % (dll.replace('Continuum_', ''), s, tok))
    per_dll[dll] = cnt

p('=' * 92)
p('残留英文归因（按支）')
p('=' * 92)
allr = sorted(set(k for c in per_dll.values() for k in c))
p('%-30s %s' % ('DLL', ''.join('%12s' % r[:12] for r in allr)))
for dll, c in per_dll.items():
    p('%-30s %s' % (dll.replace('Continuum_', ''), ''.join('%12d' % c.get(r, 0) for r in allr)))
p()
p('合计：')
for r in sorted(reason, key=lambda x: -reason[x]):
    p('   %-26s %5d 处 / %4d 个名字' % (r, reason[r], len(names_by_reason[r])))
p()
p('=' * 92)
p('明细：各原因落在哪些节')
p('=' * 92)
for k, v in sorted(byreason_sec.items(), key=lambda x: -x[1]):
    p('   %-40s %5d' % (k, v))
p()
p('=' * 92)
p('样本')
p('=' * 92)
for r in sorted(samples, key=lambda x: -reason[x]):
    p('### %s   （%d 处 / %d 名字）' % (r, reason[r], len(names_by_reason[r])))
    for s in samples[r]:
        p('      ' + s)
    nm = sorted(names_by_reason[r])
    if len(nm) > 12:
        p('      名字示例: ' + ', '.join(nm[:40]))
    p()

open(os.path.join(WORK, '_diag_remain.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('DONE')

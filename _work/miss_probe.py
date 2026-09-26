# -*- coding: utf-8 -*-
"""漏翻参数名精确勘查（数据先行）

目的：搞清楚「预设语料里有、词典里没有」的那 662 个参数名，
      在 6 支引擎 DLL 里到底以什么形态存在：
        · 独立 NUL 记号（前面也是 NUL）-> 才是真正可安全替换的对象
        · 还是只作为长串子串出现 -> 不能直接替换
      并输出上下文样本，用于人工判断「显示标签」vs「内部键/配置键/类型名表」。

产出：_work/_miss_probe.txt
"""
import os, re, json

WORK = r"D:\Programming project\插件汉化\_work"
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"
PRESET = r"C:\ProgramData\BorisFX\Continuum\19\Presets"

DLLS = ['Continuum_AE_8Bit.dll', 'Continuum_AE_16Bit.dll', 'Continuum_AE_Float.dll',
        'Continuum_Common_AE.dll', 'Continuum_3DObjects_AE.dll', 'BCCPlus.dll']

TOKEN_RE = re.compile(rb'[\x20-\x7e]+')

out = []
def p(s=''):
    out.append(str(s))
    print(s, flush=True)

# ---------------------------------------------------------------- 词典
param_zh = json.load(open(os.path.join(WORK, 'param_zh.json'), encoding='utf-8'))
for extra in ('hand_all.json', 'hand_other.json', 'hand_other2.json'):
    fp = os.path.join(WORK, extra)
    if os.path.exists(fp):
        param_zh.update(json.load(open(fp, encoding='utf-8')))

# ---------------------------------------------------------------- 预设语料
corpus = {}
pat = re.compile(rb'<name>(.*?)</name>', re.S)
nfiles = 0
for root, dirs, fs in os.walk(PRESET):
    for f in fs:
        if not f.lower().endswith(('.bsp', '.bap')):
            continue
        nfiles += 1
        raw = open(os.path.join(root, f), 'rb').read()
        for m in pat.findall(raw):
            try:
                t = m.decode('utf-8')
            except Exception:
                try:
                    t = m.decode('gbk')
                except Exception:
                    continue
            t = t.strip()
            if t:
                corpus[t] = corpus.get(t, 0) + 1

p('预设文件 %d 个，唯一 <name> %d 条；词典 %d 条' % (nfiles, len(corpus), len(param_zh)))

miss = [n for n, c in corpus.items() if n not in param_zh]
p('缺译文 %d 条' % len(miss))

# 只看「像标签」的：ASCII、长度>=3、含字母、不是纯符号
def labelish(s):
    if len(s) < 3:
        return False
    if not s.isascii():
        return False
    if not any(ch.isalpha() for ch in s):
        return False
    if s.strip() != s:
        return False
    return True

miss_lab = sorted([n for n in miss if labelish(n)], key=lambda x: -corpus[x])
p('其中「像标签」的 %d 条（长度>=3、有字母、非纯符号）' % len(miss_lab))

# ---------------------------------------------------------------- PE 节表
def sections(d):
    """返回 [(name, va, vsize, raw_off, raw_size)]"""
    pe = d.find(b'PE\x00\x00')
    if pe < 0:
        return []
    nsec = int.from_bytes(d[pe + 6:pe + 8], 'little')
    optsz = int.from_bytes(d[pe + 20:pe + 22], 'little')
    base = pe + 24 + optsz
    r = []
    for i in range(nsec):
        o = base + i * 40
        nm = d[o:o + 8].rstrip(b'\x00').decode('ascii', 'replace')
        vsize = int.from_bytes(d[o + 8:o + 12], 'little')
        va = int.from_bytes(d[o + 12:o + 16], 'little')
        rsize = int.from_bytes(d[o + 16:o + 20], 'little')
        roff = int.from_bytes(d[o + 20:o + 24], 'little')
        r.append((nm, va, vsize, roff, rsize))
    return r

def sec_of(secs, off):
    for nm, va, vsize, roff, rsize in secs:
        if roff <= off < roff + rsize:
            return nm
    return '?'

# ---------------------------------------------------------------- 逐 DLL 扫描
# 建立全局：token -> [(dll, off, prev_token, avail)]
idx = {}
info = {}
for dll in DLLS:
    src = os.path.join(BK, dll)
    if not os.path.exists(src):
        src = os.path.join(CONT, dll)
    d = open(src, 'rb').read()
    secs = sections(d)
    info[dll] = (len(d), secs)
    n_tok = 0
    for m in TOKEN_RE.finditer(d):
        s, e = m.span()
        if s > 0 and d[s - 1] != 0:
            continue                      # 不是 C 串起点
        tok = m.group().decode('ascii', 'replace')
        if tok not in param_zh and tok not in corpus:
            continue
        j = e
        while j < len(d) and d[j] == 0:
            j += 1
        avail = j - s
        # 前一个记号
        k = s - 1
        prev = b''
        while k > 0 and d[k] == 0:
            k -= 1
        if k > 0:
            st = k
            while st > 0 and d[st - 1] != 0:
                st -= 1
            prev = d[st:k + 1]
            if len(prev) > 40:
                prev = prev[-40:]
        idx.setdefault(tok, []).append((dll, s, prev, avail, sec_of(secs, s)))
        n_tok += 1
    p('%s: 文件 %d 字节, 节 %s, 命中词典/语料的独立记号 %d' %
      (dll, len(d), [(x[0], x[4]) for x in secs if x[4]], n_tok))

p()
p('=' * 92)
p('缺译文名字在 DLL 里的「独立记号」命中情况（只看 labelish）')
p('=' * 92)
have_pos = [(n, idx[n]) for n in miss_lab if n in idx]
none_pos = [n for n in miss_lab if n not in idx]
p('有独立记号: %d 条；无任何独立记号: %d 条' % (len(have_pos), len(none_pos)))
p()
p('无独立记号的（改不了，除非它在长串里当子串）：')
for i in range(0, len(none_pos), 6):
    p('    ' + ' | '.join('%-22s' % x for x in none_pos[i:i + 6]))
p()

p('有独立记号的前 60 条（含分布 + 上下文）：')
p()
for n, lst in sorted(have_pos, key=lambda x: -corpus[x[0]])[:60]:
    bydll = {}
    for dll, off, prev, avail, sec in lst:
        bydll.setdefault(dll, []).append((off, prev, avail, sec))
    p('### %-30s 预设出现 x%-5d 独立记号 %d 处' % (n, corpus[n], len(lst)))
    for dll, arr in bydll.items():
        p('     %-30s x%d' % (dll, len(arr)))
        for off, prev, avail, sec in arr[:2]:
            p('        0x%08X 节=%-6s 可用=%3d  前:%r' % (off, sec, avail, prev))
    p()

# 汇总：按总处数排序的表
p('=' * 92)
p('全部「有独立记号」的缺译文名字（按命中处数降序，前 200）')
p('=' * 92)
for n, lst in sorted(have_pos, key=lambda x: -len(x[1]))[:200]:
    dlls = {}
    for dll, off, prev, avail, sec in lst:
        dlls[dll] = dlls.get(dll, 0) + 1
    short = {k.replace('Continuum_', '').replace('.dll', ''): v for k, v in dlls.items()}
    p('  %-38s x%-4d %s' % (n, len(lst), short))

open(os.path.join(WORK, '_miss_probe.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('DONE')

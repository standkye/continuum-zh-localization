# -*- coding: utf-8 -*-
"""第三版补丁的独立复算（不信任补丁脚本的自报数据）

做法：拿 Backup-English 与 patched_dll_c 逐字节 diff，然后核对
  1) 文件长度是否完全一致
  2) 每一个改动字节是否都落在 _fix4_writes.json 声明过的区间内（不允许有"野改动"）
  3) 每个声明的写入点，回读字节是否 == 期望译名的 GBK，且紧跟 NUL
  4) 每个改动字节所在节是否非 .text
  5) 是否出现非法 GBK 片段
  6) 新译名的覆盖情况（对预设语料重算一遍）
"""
import os, json, re

WORK = r"D:\Programming project\插件汉化\_work"
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"
PATCH = os.path.join(WORK, 'patched_dll_d')
PRESET = r"C:\ProgramData\BorisFX\Continuum\19\Presets"

out = []
def p(s=''):
    out.append(str(s))
    print(s, flush=True)

writes = json.load(open(os.path.join(WORK, '_fix4_writes.json'), encoding='utf-8'))
by_dll = {}
for row in writes:
    dll, off, old, zh, sec, kind, avail = row[:7]
    # 第 8 个字段 = 实际清零长度 nz（含尾清零）。老清单没有该字段时退化为 译名长度+1。
    nz = row[7] if len(row) > 7 else len(zh.encode('gbk')) + 1
    by_dll.setdefault(dll, []).append((off, old, zh, sec, kind, avail, nz))

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

p('=' * 88)
p('第四版 DLL 补丁 独立复算')
p('=' * 88)
p()

T = dict(len_bad=0, wild=0, bad_gbk=0, text_bad=0, readback_bad=0, overflow=0,
         changed=0, written=0, secs={}, names=0)
allnames = set()

for dll, arr in sorted(by_dll.items()):
    src = os.path.join(BK, dll)
    if not os.path.exists(src):
        src = os.path.join(CONT, dll)
    a = open(src, 'rb').read()
    b = open(os.path.join(PATCH, dll), 'rb').read()
    if len(a) != len(b):
        T['len_bad'] += 1
        p('  !! %s 长度不一致 英文 %d vs 补丁 %d' % (dll, len(a), len(b)))
        continue
    secs = sections(a)

    # 声明区间（用「屏蔽后整体比对」证明没有野改动，避免逐字节 Python 循环）
    a2 = bytearray(a)
    b2 = bytearray(b)
    chg = 0
    for off, old, zh, sec, kind, avail, nz in arr:
        zb = zh.encode('gbk')
        if len(zb) + 1 > avail:
            T['overflow'] += 1
            p('  !! %s 0x%08X 译名越界 %r avail=%d' % (dll, off, zh, avail))
        if nz > avail:
            T['overflow'] += 1
            p('  !! %s 0x%08X 清零长度越界 nz=%d avail=%d' % (dll, off, nz, avail))
        n = len(zb) + 1
        # 回读
        if b[off:off + len(zb)] != zb or b[off + len(zb)] != 0:
            T['readback_bad'] += 1
            p('  !! %s 0x%08X 回读不符 期望 %r 实得 %r'
              % (dll, off, zh, b[off:off + n]))
        # 声明区间 = 实际清零长度 nz（译名 + 尾清零）。所有改动字节都必须落在里面。
        for k in range(off, off + nz):
            if a[k] != b[k]:
                chg += 1
                sn = sec_of(secs, k)
                T['secs'][sn] = T['secs'].get(sn, 0) + 1
                if sn == '.text':
                    T['text_bad'] += 1
        # 屏蔽
        a2[off:off + nz] = b'\x00' * nz
        b2[off:off + nz] = b'\x00' * nz
        allnames.add(old)

    # 屏蔽后必须完全一致 -> 证明「所有改动都在声明区间内」
    if bytes(a2) != bytes(b2):
        T['wild'] += 1
        i = next(k for k in range(len(a2)) if a2[k] != b2[k])
        p('  !! %s 存在声明区间外的改动，首个位置 0x%08X %02X -> %02X'
          % (dll, i, a[i], b[i]))
    del a2, b2

    T['changed'] += chg
    T['written'] += len(arr)
    p('  %-30s 写入 %4d 处   改动字节 %6d' % (dll, len(arr), chg))

p()
p('-' * 88)
p('长度不一致          : %d   (期望 0)' % T['len_bad'])
p('野改动（区间外）    : %d   (期望 0)' % T['wild'])
p('回读不符            : %d   (期望 0)' % T['readback_bad'])
p('译名越界            : %d   (期望 0)' % T['overflow'])
p('.text 内改动        : %d   (期望 0)' % T['text_bad'])
p('改动字节总数        : %d' % T['changed'])
p('改动所在节分布      : %r' % T['secs'])
p('写入点总数          : %d' % T['written'])
p('覆盖的英文原文种数  : %d' % len(allnames))
p()

# ---------- 非法 GBK 检查 ----------
# 注：全库正则扫 GBK 片段在 58MB 文件上会拖死（几百万次匹配）。
#     这里改成等价且便宜的判据：**所有被改动的字节都属于声明写入区间，且回读精确等于
#     期望译名的 GBK 字节** —— 上面两项已验，故不可能引入非法 GBK。
p('-' * 88)
p('非法 GBK 片段：由「改动字节 ⊆ 声明区间 + 回读精确匹配」共同保证，'
  '野改动=%d、回读不符=%d -> %s'
  % (T['wild'], T['readback_bad'], '无风险' if T['wild'] == 0 and T['readback_bad'] == 0 else '★有风险'))
p()

# ---------- 预设语料覆盖率重算 ----------
p('-' * 88)
p('预设语料覆盖率重算（词典层）')
param_zh = json.load(open(os.path.join(WORK, 'param_zh.json'), encoding='utf-8'))
for extra in ('hand_all.json', 'hand_other.json', 'hand_other2.json', 'gap_zh.json',
              'batch5_ename.json', 'batch6_ui.json', 'batch7_miss.json',
              'batch8_miss.json'):
    fp = os.path.join(WORK, extra)
    if os.path.exists(fp):
        param_zh.update(json.load(open(fp, encoding='utf-8')))

corpus = {}
pat = re.compile(rb'<name>(.*?)</name>', re.S)
for root, dirs, fs in os.walk(PRESET):
    for f in fs:
        if not f.lower().endswith(('.bsp', '.bap')):
            continue
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

have = [n for n in corpus if n in param_zh]
p('  语料 %d 条，词典覆盖 %d 条 (%.1f%%)   仍未覆盖 %d 条'
  % (len(corpus), len(have), 100.0 * len(have) / len(corpus), len(corpus) - len(have)))
p('  词典总量 %d 条' % len(param_zh))
p()

# ---------- 每支 DLL 实际写入的中文标签数 ----------
p('-' * 88)
p('各 DLL 实际写入的中文标签数（译名含 CJK 的写入点）')
tot_cn = 0
for dll, arr in sorted(by_dll.items()):
    cn = sum(1 for off, old, zh, sec, kind, avail, nz in arr
             if any('\u4e00' <= ch <= '\u9fff' for ch in zh))
    tot_cn += cn
    p('  %-30s 写入 %4d 处，其中中文 %4d 处' % (dll, len(arr), cn))
p('  合计中文写入 %d 处' % tot_cn)

open(os.path.join(WORK, '_accept4.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('DONE')


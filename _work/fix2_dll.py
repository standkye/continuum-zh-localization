# -*- coding: utf-8 -*-
"""修复版 DLL 参数名补丁（GBK 编码 + 排除内部键）

2026-09-25 第二次修复：
  1) 编码 UTF-8 -> GBK
  2) ★ 排除「内部键」：这些字符串是插件自己用来找资源目录 / 解析预设 XML 的标识符，
     不是显示标签。改成中文会让 DllMain 返回 FALSE -> WinError 1114
     -> Continuum 弹「Could not load library」-> 添加任何效果都失败。
     实测：只恢复 Resources + Documentation 两个槽位，4 支引擎 DLL 立刻全部可加载。
     详见 _work/_bisect_log.txt 与 _work/_layer_test3.txt
"""
import os, json

BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"
WORK = r"D:\Programming project\插件汉化\_work"
OUT_DLL = os.path.join(WORK, 'patched_dll_b')
os.makedirs(OUT_DLL, exist_ok=True)
ENC = 'gbk'

# ---------------------------------------------------------------- 内部键黑名单
# 一律不翻译（大小写不敏感）。宁可少翻几个词，也不能让插件起不来。
NEVER = {
    # 致命：资源/文档目录名
    'resources', 'documentation',
    # 预设 XML 的元数据字段
    'filter version', 'creation date', 'category',
    'preset name', 'filter name', 'preset type', 'file path',
    'description', 'author', 'client',
    'presetname', 'filtername', 'filterversion', 'datetime', 'duration',
    # BorisFX 的设置项 / 子程序名
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
    # 其他高危：路径 / 标识符风格
    'borisplugins', 'filtersets', 'utilities', 'bin',
    'stringmap', 'stringpair', 'stringid', 'stringvalue',
    'borisfxdirect', 'bfx-license-tool', 'bfx-version-update',
    'mocha continuum.app',
}

param_zh = json.load(open(os.path.join(WORK, 'param_zh.json'), encoding='utf-8'))
for extra in ('hand_all.json', 'hand_other.json', 'hand_other2.json'):
    fp = os.path.join(WORK, extra)
    if os.path.exists(fp):
        param_zh.update(json.load(open(fp, encoding='utf-8')))

chains = json.load(open(os.path.join(WORK, 'dll_chains.json'), encoding='utf-8'))

out = []
def p(s=''):
    out.append(str(s))
    print(s, flush=True)

p('=== DLL 修复版（编码 %s，已排除内部键 %d 条）===' % (ENC, len(NEVER)))
p('param_zh entries: %d' % len(param_zh))
p()

tot_replace = tot_ov = tot_us = tot_excl = 0
never_hit = {}

for name, ch in sorted(chains.items()):
    src = os.path.join(BK, name)
    if not os.path.exists(src):
        src = os.path.join(CONT, name)
    d = bytearray(open(src, 'rb').read())
    orig_len = len(d)
    n = ov = us = ex = 0
    for off_s, arr in ch.items():
        cur = int(off_s)
        for s in arr:
            slot = max(8, ((len(s) + 1 + 7) // 8) * 8)
            if s.strip().lower() in NEVER:
                ex += 1
                never_hit[s.strip()] = never_hit.get(s.strip(), 0) + 1
                cur += slot
                continue
            zh = param_zh.get(s)
            if zh:
                try:
                    b = zh.encode(ENC)
                except UnicodeEncodeError:
                    b = None
                if b is None:
                    ov += 1
                elif len(b) <= slot - 1:
                    raw = d[cur:cur + slot]
                    nul = raw.find(b'\x00')
                    safe = (nul > 0 and not any(raw[nul:]) and len(raw) == slot)
                    if safe:
                        d[cur:cur + slot] = b'\x00' * slot
                        d[cur:cur + len(b)] = b
                        n += 1
                    else:
                        us += 1
                else:
                    ov += 1
            cur += slot
    assert len(d) == orig_len, name
    open(os.path.join(OUT_DLL, name), 'wb').write(bytes(d))
    tot_replace += n; tot_ov += ov; tot_us += us; tot_excl += ex
    p('%-30s 替换 %5d   容量不足 %4d   槽位存疑 %3d   排除内部键 %3d' % (name, n, ov, us, ex))

p()
p('合计：替换 %d，容量不足保留英文 %d，槽位存疑 %d，排除内部键 %d'
  % (tot_replace, tot_ov, tot_us, tot_excl))
p()
p('被排除的内部键（实际命中数）：')
for k, v in sorted(never_hit.items(), key=lambda x: -x[1]):
    p('    %-42s %d' % (k, v))

open(os.path.join(WORK, '_fix2_dll.txt'), 'w', encoding='utf-8').write('\n'.join(out))

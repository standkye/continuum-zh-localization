# -*- coding: utf-8 -*-
"""就地替换补丁器：
   .aex  -> PiPL 的 eman 值区间（文件长度不变）
   .dll  -> 8 字节对齐槽位（文件长度不变）
"""
import os, re, json, struct, shutil, math

CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"
LIB = r"C:\Program Files\BorisFX\ContinuumAE\19\lib"
WORK = r"D:\Programming project\插件汉化\_work"
OUT_AEX = os.path.join(WORK, 'patched_aex')
OUT_DLL = os.path.join(WORK, 'patched_dll')
os.makedirs(OUT_AEX, exist_ok=True)
os.makedirs(OUT_DLL, exist_ok=True)

param_zh = json.load(open(os.path.join(WORK, 'param_zh.json'), encoding='utf-8'))
# 用全手写表覆盖（hand_all=参数名, hand_other/2=分组标题与次要标签）。
# 分词器拼出来的机翻味太重，参数名一律以手写表为准 —— 手写表最后加载，
# 优先级最高，绝不能被旧表的机翻结果盖回去。
for extra in ('hand_all.json', 'hand_other.json', 'hand_other2.json'):
    p = os.path.join(WORK, extra)
    if os.path.exists(p):
        param_zh.update(json.load(open(p, encoding='utf-8')))
print("param_zh entries:", len(param_zh))
effect_zh = json.load(open(os.path.join(WORK, 'effect_zh.json'), encoding='utf-8'))
chains = json.load(open(os.path.join(WORK, 'dll_chains.json'), encoding='utf-8'))
hand_all = json.load(open(os.path.join(WORK, 'hand_all.json'), encoding='utf-8'))

rep = []

# ---------------- .aex ----------------
# 每个 .aex 的 PiPL 里有两个要改的字段：
#   eman -> 效果名（AE 效果菜单里那一行）
#   gtac -> 类型栏 / 分类（AE 效果菜单里的分组名，如 "BCC Blur"）
# 两个记录的布局完全一样： MIB8 | key(4) | pad(4) | size(4) | value
#   value = [1B 长度][UTF-8 文本][0x00 填充]
# 可用字节 = size - 2（长度字节 + 结尾 NUL 各占 1）。改长度字节即可，
# 但**绝不能改变 value 的总长度**，否则 PiPL 记录边界错乱、AE 拒绝加载。
#
# 【编码必须是 UTF-8】AE 25.1 实测全链路用 UTF-8（zstring\zh_CN 带 BOM、
# PresetEffects.xml 与 Continuum 自己的 presets\*.xml 都声明 utf-8）。
# 早前用 GBK 写，AE 一添加效果就弹「无法初始化该效果（25::3）」。
# UTF-8 每汉字 3 字节（GBK 2 字节），少数紧凑记录会放不下 —— 放不下就
# 保留英文，绝不截断出半个字符。
import re as _re
from names_manual import CATS as _CATS

rep.append("=== .aex 效果名 + 类型栏 ===")
ok = fail = 0
nrep = 0
ncat = 0


def _find_records(d, key):
    """按 TLV 找出所有 key 记录，返回 [(base, size, val)]。"""
    k = key.encode()
    res = []
    i = 0
    while True:
        j = d.find(k, i)
        if j < 0:
            break
        if d[j - 4:j] == b'MIB8':
            base = j - 4
            size = struct.unpack('<I', d[base + 12:base + 16])[0]
            val = base + 16
            if 0 < size < 4096:
                res.append((base, size, val))
        i = j + 4
    return res


for fn, items in sorted(effect_zh.items()):
    src = os.path.join(CONT, fn)
    dst = os.path.join(OUT_AEX, fn)
    shutil.copy2(src, dst)
    with open(dst, 'r+b') as f:
        d = bytearray(f.read())
        orig_len = len(d)
        for (en, zh, size, off, cap) in items:
            if not zh:
                continue
            b = zh.encode('utf-8')
            if len(b) > cap:
                # 截断必须落在字符边界上，否则会写出非法 UTF-8，
                # AE 解码失败 = 效果无法初始化。
                b = b[:cap]
                while b and len(b.decode('utf-8', 'ignore')) == 0:
                    b = b[:-1]
                # 长度字节只有 1 字节，绝不能 >255
                b = b[:255]
                while b and (b[-1] & 0xC0) == 0x80:
                    b = b[:-1]
                if not b:
                    continue
            val = off + 16
            # 校验原区域确实是 [L][text][0][pad]
            if d[val] != 0 and d[val + len(en.encode()) + 1:val + size].count(0) != size - len(en.encode()) - 2:
                pass
            d[val:val + size] = b'\x00' * size
            d[val] = len(b)
            d[val + 1:val + 1 + len(b)] = b
            nrep += 1
        # ---- 类型栏 / 分类（gtac）----
        # 用改过 eman 之后的内容重新定位（base 偏移与改 eman 无关，
        # 因为我们是等长改写，但重新搜索最稳）。
        for (base, size, val) in _find_records(bytes(d), 'gtac'):
            raw = d[val:val + size]
            n = raw[0]
            try:
                cat = raw[1:1 + n].decode('utf-8')
            except UnicodeDecodeError:
                # 源记录本身不是 UTF-8（例如已是 GBK 的旧残留）——回退再试一次
                try:
                    cat = raw[1:1 + n].decode('gbk')
                except UnicodeDecodeError:
                    continue
            tr = _CATS.get(cat)
            if not tr:
                continue
            tb = tr.encode('utf-8')
            budget = size - 2
            if len(tb) > budget:
                # 放不下就跳过，宁可保留英文也不要截断出半个字
                continue
            d[val:val + size] = b'\x00' * size
            d[val] = len(tb)
            d[val + 1:val + 1 + len(tb)] = tb
            ncat += 1
        assert len(d) == orig_len
        f.seek(0)
        f.write(d)
    ok += 1
rep.append(f"文件 {ok} 个，效果名替换 {nrep} 处，类型栏替换 {ncat} 处")

# 校验：大小一致 + 名字回读
bad = 0
for fn, items in sorted(effect_zh.items()):
    a = os.path.join(CONT, fn); b = os.path.join(OUT_AEX, fn)
    if os.path.getsize(a) != os.path.getsize(b):
        bad += 1
rep.append(f"文件大小不一致: {bad}")

# ---------------- DLL ----------------
rep.append("\n=== DLL 参数名 ===")
dlls = {'Continuum_AE_Float.dll': LIB, 'Continuum_AE_8Bit.dll': LIB,
        'Continuum_AE_16Bit.dll': LIB, 'Continuum_Common_AE.dll': LIB,
        'Continuum_3DObjects_AE.dll': LIB, 'BCCPlus.dll': CONT}
for name, base in dlls.items():
    src = os.path.join(base, name)
    if not os.path.exists(src):
        rep.append(f"{name}: 源文件不存在，跳过")
        continue
    dst = os.path.join(OUT_DLL, name)
    shutil.copy2(src, dst)
    ch = chains.get(name, {})
    n = 0
    skipped = 0
    # 关键：槽位合法性必须以「原始文件」为准来判定。
    # 早期版本拿 len(英文键) 当文本长度去算 tail 窗口，而槽里实际存的
    # 往往是**中文**（BorisFX 源文件里大量参数名本身已是 GBK 汉字），
    # 其字节数 ≠ ASCII 长度，导致 tail 窗口错位、把残留字节误判成"污染"，
    # 于是正常槽位被 skip（Cam Pos XY / Boost MB / FG Opacity 等 61 处）。
    # 正确判据：源槽位必须是 [文本][连续 NUL 填充] —— 即第一个 NUL 出现
    # 之后剩余全是 0；且文本本身不为空、能按 UTF-8 解出汉字或 ASCII。
    #
    # 编码同 .aex：必须是 UTF-8。UTF-8 每汉字 3 字节，比 GBK 占得多，
    # 所以放不下（len(b) > slot-1）的槽位数量会比以前多 —— 一律保留英文。
    with open(src, 'rb') as fs:
        srcd = fs.read()
    with open(dst, 'r+b') as f:
        d = bytearray(f.read())
        orig_len = len(d)
        for off_s, arr in ch.items():
            off = int(off_s)
            cur = off
            for s in arr:
                slot = max(8, ((len(s) + 1 + 7) // 8) * 8)
                zh = param_zh.get(s)
                if zh:
                    b = zh.encode('utf-8')
                    if len(b) <= slot - 1:
                        raw = srcd[cur:cur + slot]
                        nul = raw.find(b'\x00')
                        # 独立槽位：源里确实有 NUL 结尾，且其后全零
                        safe = (nul > 0
                                and not any(raw[nul:])
                                and len(raw) == slot)
                        if safe:
                            d[cur:cur + slot] = b'\x00' * slot
                            d[cur:cur + len(b)] = b
                            n += 1
                        else:
                            skipped += 1
                    else:
                        skipped += 1
                cur += slot
        assert len(d) == orig_len
        f.seek(0)
        f.write(d)
    same = os.path.getsize(src) == os.path.getsize(dst)
    rep.append(f"{name:28s} 替换 {n:5d} 处  跳过 {skipped:4d}  大小一致={same}")

open(os.path.join(WORK, 'patch_report.txt'), 'w', encoding='utf-8').write("\n".join(rep))

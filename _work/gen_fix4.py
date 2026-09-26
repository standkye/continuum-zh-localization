# -*- coding: utf-8 -*-
"""从 fix3_dll.py / accept3.py 生成 fix4_dll.py / accept4.py（第四版）
改动点：
  1) 邻居闸判据修正：ident_like 只认「含下划线」与「点号且无空格」的**词样**串；
     不再把「小写开头」一概算键（BCCPlus 是「显示名 + 小写键」交替表，被误伤一大片）。
  2) 新增「位置排除区」：按标记串动态定位，把类型名表/目录名表/授权串/许可信息/
     Qt 对象名整段排除（这些位置**不能翻**，但同一个词在别处该翻）。
  3) NEVER 加 uint32。
  4) 产物目录改 patched_dll_d，清单改 _fix4_writes.json。
"""
import os, re

WORK = r"D:\Programming project\插件汉化\_work"
s = open(os.path.join(WORK, 'fix3_dll.py'), encoding='utf-8').read()

# ---------- 1) 判据修正 ----------
old_ident = """def ident_like(t):
    if '_' in t or '.' in t:
        return True
    return bool(t) and t[0].islower()
"""
new_ident = '''def word_like(t):
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
'''
assert old_ident in s
s = s.replace(old_ident, new_ident)

# ---------- 2) NEVER 加 uint32 ----------
old_never = "    'string', 'int', 'float', 'bool', 'double', 'long', 'void',\n"
new_never = ("    'string', 'int', 'float', 'bool', 'double', 'long', 'void',\n"
             "    'uint32', 'uint8', 'uint16', 'int32',\n")
assert old_never in s
s = s.replace(old_never, new_never, 1)

# ---------- 3) 位置排除区 ----------
old_secs = "    d = bytearray(open(src, 'rb').read())\n    orig_len = len(d)\n    secs = sections(bytes(d))\n"
new_secs = '''    d = bytearray(open(src, 'rb').read())
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
'''
assert old_secs in s
s = s.replace(old_secs, new_secs, 1)

old_gate = """        if tok.strip().lower() in NEVER:
            L['ex'] += 1
            continue
        zh = param_zh.get(tok)"""
new_gate = """        if tok.strip().lower() in NEVER:
            L['ex'] += 1
            continue
        if in_excl(s):
            L['excl'] += 1
            continue
        zh = param_zh.get(tok)"""
assert old_gate in s
s = s.replace(old_gate, new_gate, 1)

# 统计字典加 excl
s = s.replace("tot = {'proven': 0, 'new': 0, 'ov': 0, 'us': 0, 'ex': 0,\n       'gate_shape': 0, 'gate_nb': 0, 'gate_host': 0}",
              "tot = {'proven': 0, 'new': 0, 'ov': 0, 'us': 0, 'ex': 0, 'excl': 0,\n       'gate_shape': 0, 'gate_nb': 0, 'gate_host': 0}")
s = s.replace("    L = {'proven': 0, 'new': 0, 'ov': 0, 'us': 0, 'ex': 0,\n         'gate_shape': 0, 'gate_nb': 0, 'gate_host': 0}",
              "    L = {'proven': 0, 'new': 0, 'ov': 0, 'us': 0, 'ex': 0, 'excl': 0,\n         'gate_shape': 0, 'gate_nb': 0, 'gate_host': 0}")
s = s.replace("""    p('%-30s 已证 %5d + 新增 %5d = %5d   容量不足 %4d  槽位存疑 %3d  排除键 %4d  形状拦 %3d  邻居拦 %4d  宿主名单拦 %4d'
      % (name, L['proven'], L['new'], L['proven'] + L['new'],
         L['ov'], L['us'], L['ex'], L['gate_shape'], L['gate_nb'], L['gate_host']))""",
              """    p('%-30s 已证 %5d + 新增 %5d = %5d   容量不足 %4d  排除键 %4d  排除区 %4d  形状拦 %3d  邻居拦 %4d  宿主拦 %4d'
      % (name, L['proven'], L['new'], L['proven'] + L['new'],
         L['ov'], L['ex'], L['excl'], L['gate_shape'], L['gate_nb'], L['gate_host']))""")
s = s.replace("""p('      容量不足保留英文 %d，槽位存疑 %d，排除内部键 %d，形状拦截 %d，邻居拦截 %d，宿主名单拦截 %d'
  % (tot['ov'], tot['us'], tot['ex'], tot['gate_shape'], tot['gate_nb'], tot['gate_host']))""",
              """p('      容量不足保留英文 %d，排除内部键 %d，排除区 %d，形状拦截 %d，邻居拦截 %d，宿主名单拦截 %d'
  % (tot['ov'], tot['ex'], tot['excl'], tot['gate_shape'], tot['gate_nb'], tot['gate_host']))""")

# ---------- 4) 输出路径与 EXCL 定义 ----------
s = s.replace("OUT_DLL = os.path.join(WORK, 'patched_dll_c')",
              "OUT_DLL = os.path.join(WORK, 'patched_dll_d')")
s = s.replace("_fix3_writes.json", "_fix4_writes.json").replace("_fix3_dll.txt", "_fix4_dll.txt")
s = s.replace("第三版 DLL 补丁", "第四版 DLL 补丁")

s = s.replace("""NEW_SECTIONS = {'.rdata', '_RDATA'}          # 新增集合只在这两个节里动手""",
              """NEW_SECTIONS = {'.rdata', '_RDATA'}          # 新增集合只在这两个节里动手

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
]""")

open(os.path.join(WORK, 'fix4_dll.py'), 'w', encoding='utf-8').write(s)
print('fix4_dll.py 已生成，%d 字节' % len(s))

# ---------- accept4 ----------
a = open(os.path.join(WORK, 'accept3.py'), encoding='utf-8').read()
a = a.replace("PATCH = os.path.join(WORK, 'patched_dll_c')", "PATCH = os.path.join(WORK, 'patched_dll_d')")
a = a.replace("_fix3_writes.json", "_fix4_writes.json").replace("_accept3.txt", "_accept4.txt")
a = a.replace("第三版 DLL 补丁 独立复算", "第四版 DLL 补丁 独立复算")
open(os.path.join(WORK, 'accept4.py'), 'w', encoding='utf-8').write(a)
print('accept4.py 已生成，%d 字节' % len(a))

# -*- coding: utf-8 -*-
import os, re, json
from collections import Counter

WORK = r"D:\Programming project\插件汉化\_work"
out = []

P = json.load(open(os.path.join(WORK, 'param_candidates.json'), encoding='utf-8'))
chains = json.load(open(os.path.join(WORK, 'dll_chains.json'), encoding='utf-8'))

# DLL 里所有槽位串
allslots = set()
for dll, ch in chains.items():
    for arr in ch.values():
        allslots.update(arr)

camel = re.compile(r'^[a-z][A-Za-z0-9]*$|^[a-z]+[A-Z]')
def looks_id(s):
    """内部标识符特征：camelCase / 全小写无空格 / 带下划线"""
    if camel.match(s):
        return True
    if '_' in s:
        return True
    if ' ' not in s and s.islower():
        return True
    return False

def ok_label(s):
    if len(s) < 3:
        return False
    if not all(32 <= ord(c) < 127 for c in s):
        return False
    if looks_id(s):
        return False
    if s[0].islower() and ' ' not in s:
        return False
    return True

for dll in chains:
    pass

inter_raw = [s for s in P if s in allslots]
inter_ok = [s for s in inter_raw if ok_label(s)]
out.append("=== 参数名筛选 ===")
out.append(f"预设候选 <name>          : {len(P)}")
out.append(f"  其中能在 DLL 槽位里找到 : {len(inter_raw)}")
out.append(f"  再剔除内部标识符/碎片   : {len(inter_ok)}")

# 出现频次分布（需要重新读预设拿 count）
cnt = Counter()
root = r"C:\ProgramData\BorisFX\Continuum\19\Presets"
for dp, dns, fns in os.walk(root):
    for fn in fns:
        if not fn.lower().endswith(('.bsp', '.bap')):
            continue
        try:
            t = open(os.path.join(dp, fn), 'rb').read().decode('utf-8', 'ignore')
        except Exception:
            continue
        for m in re.finditer(r'<name>(.*?)</name>', t, re.S):
            s = m.group(1).strip()
            if s in set(inter_ok):
                cnt[s] += 1
out.append(f"  带频次统计的             : {len(cnt)}")
buckets = Counter()
for s, c in cnt.items():
    buckets['>=100' if c >= 100 else '10-99' if c >= 10 else '2-9' if c >= 2 else '1'] += 1
out.append("频次分布: " + str(dict(buckets)))
top = cnt.most_common(40)
out.append("\n最高频 40 个:")
for s, c in top:
    out.append(f"  {c:5d}  {s}")

json.dump({s: c for s, c in cnt.items()},
          open(os.path.join(WORK, 'param_final.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
json.dump(inter_ok, open(os.path.join(WORK, 'param_ok.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

open(os.path.join(WORK, 'filter_report.txt'), 'w', encoding='utf-8').write("\n".join(out))

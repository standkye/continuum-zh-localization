# -*- coding: utf-8 -*-
"""按词素合成中文，并按槽位/记录容量截断"""
import os, json, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dict_zh import TOKENS, EFFECT_OVERRIDE
from dict_extra import EXTRA
from dict_extra2 import EXTRA2
from dict_fix import FIX, BIGRAM

TOKENS.update(EXTRA)
TOKENS.update(EXTRA2)
TOKENS.update(FIX)   # 最终覆盖
WORK = r"D:\Programming project\插件汉化\_work"
out = []

CAMEL = re.compile(r'(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|(?<=[A-Za-z])(?=[0-9])')


def slot_of(s):
    return max(8, ((len(s.encode('ascii', 'ignore')) + 1 + 7) // 8) * 8)


def _t(tok):
    for cand in (tok, tok.capitalize(), tok.upper(), tok.lower()):
        if cand in TOKENS:
            return TOKENS[cand]
    return None


def _translate_token(tok):
    v = _t(tok)
    if v is not None:
        return v
    # 带括号/句点的缩写：(Sub) -> Sub, Var. -> Var
    stripped = tok.strip('().,')
    if stripped and stripped != tok:
        v = _t(stripped)
        if v is not None:
            return v
    if tok.endswith("'s"):          # Artist's -> Artist
        v = _t(tok[:-2])
        if v is not None:
            return v
    if re.match(r'^[A-Za-z0-9]+$', tok):
        subs = [s for s in CAMEL.split(tok) if s]
        if len(subs) > 1:
            got = [_t(s) for s in subs]
            if all(g is not None for g in got):
                return "".join(got)
    if '-' in tok or '/' in tok:
        subs = [s for s in re.split(r'[-/]', tok) if s]
        if len(subs) > 1:
            got = [_t(s) for s in subs]
            if all(g is not None for g in got):
                return "".join(got)
    return tok


def compose(en):
    parts = []
    prev = None
    for t in en.split():
        key = (prev, t)
        if key in BIGRAM:
            zh = BIGRAM[key]
        else:
            zh = _translate_token(t)
        prev = t
        if zh == "":
            continue
        parts.append(zh)
    return "".join(parts)


def left_en(zh):
    return [w for w in re.findall(r'[A-Za-z]{2,}', zh) if w not in ('XY', 'RGB', 'RGBA', 'HSL', 'UV', 'LED', 'EPS', 'Hz')]


def fit(zh, cap):
    b = zh.encode('gbk', 'ignore')
    if len(b) <= cap:
        return zh, False
    b = b[:cap]
    s = b.decode('gbk', 'ignore')
    while s and len(s.encode('gbk', 'ignore')) > cap:
        s = s[:-1]
    return s, True


# ---------------- 参数名 ----------------
params = json.load(open(os.path.join(WORK, 'params_to_translate.json'), encoding='utf-8'))
param_zh = {}
trunc = []
leftover = []
for en in params:
    cap = slot_of(en) - 1
    zh = compose(en)
    zh, cut = fit(zh, cap)
    param_zh[en] = zh
    if cut:
        trunc.append((en, zh, cap))
    le = left_en(zh)
    if le:
        leftover.append((en, zh, le))

out.append("=== 参数名翻译 ===")
out.append(f"总数 {len(param_zh)}   截断 {len(trunc)}   有英文残留 {len(leftover)}")
out.append("\n被截断的（前 30）:")
for en, zh, cap in trunc[:30]:
    out.append(f"  [{cap}B] {en} -> {zh}")
out.append("\n仍有英文残留的（前 50）:")
for en, zh, le in leftover[:50]:
    out.append(f"  {en} -> {zh}   残留{le}")
json.dump(param_zh, open(os.path.join(WORK, 'param_zh.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

unk = {}
for en, zh, le in leftover:
    for w in le:
        unk[w] = unk.get(w, 0) + 1
out.append(f"\n未登录词 {len(unk)} 个，高频前 80:")
for w, c in sorted(unk.items(), key=lambda x: -x[1])[:80]:
    out.append(f"  {c:4d}  {w}")
json.dump(unk, open(os.path.join(WORK, 'unknown_tokens.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

# ---------------- 效果名 ----------------
aex = json.load(open(os.path.join(WORK, 'aex_names2.json'), encoding='utf-8'))
eff = {}
eff_report = []
for fn, v in aex.items():
    eff[fn] = []
    for (en, size, off) in v['names']:
        cap = size - 2
        raw = en.strip()
        base = re.sub(r'^BCC\+', '', raw)
        base = re.sub(r'^BCC\s+', '', base).strip()
        zh = (EFFECT_OVERRIDE.get(raw) or EFFECT_OVERRIDE.get(base)
              or compose(base))
        zh, cut = fit(zh, cap)
        eff[fn].append([en, zh, size, off, cap])
        eff_report.append((en, zh, cap, cut, left_en(zh)))

out.append(f"\n=== 效果名翻译 ===")
out.append(f"记录数 {len(eff_report)}  截断 {sum(1 for r in eff_report if r[3])}  "
           f"有残留 {sum(1 for r in eff_report if r[4])}")
out.append("示例 25:")
for en, zh, cap, cut, le in eff_report[:25]:
    out.append(f"  [{cap}B] {en!r} -> {zh} {'(截断)' if cut else ''}")
out.append("\n效果名有残留的（前 50）:")
n = 0
for en, zh, cap, cut, le in eff_report:
    if le:
        out.append(f"  [{cap}B] {en} -> {zh} 残留{le}")
        n += 1
        if n >= 50:
            break
json.dump(eff, open(os.path.join(WORK, 'effect_zh.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

open(os.path.join(WORK, 'trans_report.txt'), 'w', encoding='utf-8').write("\n".join(out))

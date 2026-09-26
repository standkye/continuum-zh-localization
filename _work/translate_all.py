# -*- coding: utf-8 -*-
"""Build the final translation table for ALL UI strings in the DLLs.

Sources, in priority order:
  1. names_manual.NAMES / CATS   - hand-written effect + category names
  2. dict_more.PHRASES           - hand-written fixed phrases
  3. morpheme composition        - dict_more.MORE -> dict_fix -> dict_extra2
                                   -> dict_extra -> dict_zh
Then the result is truncated to fit the 8-byte-aligned slot it lives in.
"""
import json, os, re, sys, importlib, collections

WORK = r"D:\Programming project\插件汉化\_work"
sys.path.insert(0, WORK)
from names_manual import NAMES, CATS
from dict_more import MORE, PHRASES
from dict_last import LAST, PHRASES2

PHRASES = dict(PHRASES)
PHRASES.update(PHRASES2)   # dict_last 的整串翻译优先

LAYERS = []
for mod, attr in (("dict_zh", "TOKENS"), ("dict_extra", "EXTRA"),
                  ("dict_extra2", "EXTRA2")):
    try:
        LAYERS.append(getattr(importlib.import_module(mod), attr))
    except Exception:
        LAYERS.append({})
try:
    LAYERS.append(getattr(importlib.import_module("dict_fix"), "FIX"))
except Exception:
    LAYERS.append({})
LAYERS.append(MORE)
LAYERS.append(LAST)          # highest priority of the word layers

WORD = {}
for d in LAYERS:
    WORD.update(d)
print("word layers merged:", len(WORD))

# ------------------------------------------------------------------ tokeniser

def split_words(s):
    s = s.strip()
    s = re.sub(r"\s*\(\s*", " (", s)
    out = []
    # 括号要作为独立 token 参与拼接，否则 "(Color" / "Mix)" 永远查不到词典，
    # 整串就会退化成英文 —— 这是参数名大面积漏翻的主因之一。
    for p in re.split(r"[\s\-/:]+|([()])", s):
        if not p: continue
        p = p.strip(".,':")
        if not p: continue
        p = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", p)     # camelCase
        p = re.sub(r"(?<=[A-Za-z])(?=\d)", " ", p)        # letter|digit
        p = re.sub(r"(?<=\d)(?=[A-Za-z])", " ", p)
        for w in p.split():
            if w: out.append(w)
    return out

# BIGRAM: fixed two-word collocations
BIGRAM = {
    ("Fall", "Off"): "衰减",
    ("Motion", "Blur"): "运动模糊",
    ("Pixel", "Chooser"): "像素选取",
    ("Match", "Move"): "运动匹配",
    ("Drop", "Shadow"): "投影",
    ("Color", "Range"): "颜色范围",
    ("Light", "Wrap"): "光线融合",
    ("Motion", "Key"): "运动键控",
    ("Time", "Displacement"): "时间置换",
    ("Lens", "Flare"): "镜头光晕",
    ("Advanced", "Controls"): "高级控制",
}

def compose(s):
    if s in PHRASES:
        return PHRASES[s]
    words = split_words(s)
    if not words:
        return s
    out, i = [], 0
    while i < len(words):
        w = words[i]
        if i + 1 < len(words) and (w, words[i + 1]) in BIGRAM:
            out.append(BIGRAM[(w, words[i + 1])]); i += 2; continue
        # 注意：词典里存在 ""（把 for/of 之类的小词译为空），
        # 用 `or` 会把空串判为假、继续往下查，最后退化成保留英文。
        for cand in (w, w.lower(), w.capitalize()):
            if cand in WORD:
                t = WORD[cand]
                break
        else:
            t = w                              # unknown: keep as-is
        out.append(t); i += 1
    zh = "".join(out)
    zh = re.sub(r"\s+", "", zh)
    zh = re.sub(r"[（(]\s*", "(", zh)
    zh = re.sub(r"\s*[)）]", ")", zh)
    return zh.strip()

# ------------------------------------------------------------------ capacity

def slot_of(s):
    return max(8, -(-(len(s) + 1) // 8) * 8)

def fit(zh, budget):
    """Truncate zh (GBK) so it fits `budget` bytes."""
    try:
        if len(zh.encode("gbk")) <= budget:
            return zh, False
    except UnicodeEncodeError:
        return zh, True
    lo, hi = 0, len(zh)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        try:
            ok = len(zh[:mid].encode("gbk")) <= budget
        except UnicodeEncodeError:
            ok = False
        if ok: lo = mid
        else: hi = mid - 1
    return zh[:lo], True

# ------------------------------------------------------------------ main

pz = json.load(open(os.path.join(WORK, "param_zh.json"), encoding="utf-8"))
HAND = json.load(open(os.path.join(WORK, "hand_all.json"), encoding="utf-8"))
print("hand-written params:", len(HAND))
try:
    HAND_OTHER = json.load(open(os.path.join(WORK, "hand_other.json"), encoding="utf-8"))
except Exception:
    HAND_OTHER = {}
print("hand-written others:", len(HAND_OTHER))
HAND.update(HAND_OTHER)          # 分组标题 / 次要标签 也全部手写
try:
    HAND.update(json.load(open(os.path.join(WORK, "hand_other2.json"), encoding="utf-8")))
except Exception:
    pass
labels = [l.rstrip("\n") for l in open(os.path.join(WORK, "gap_final.txt"), encoding="utf-8") if l.strip()]
chains = json.load(open(os.path.join(WORK, "dll_chains.json"), encoding="utf-8"))

# every string we intend to patch
targets = {}
targets.update(pz)                       # the 3789 preset-derived params
for s in labels:
    targets.setdefault(s, None)
for s in NAMES:                          # effect names living inside the DLLs
    targets.setdefault(s, None)
for s in CATS:
    targets.setdefault(s, None)

# minimal slot for each target (slot size is a property of the string itself)
result, truncated, haslatin = {}, [], []
for en in sorted(targets):
    # 参数名一律走全手写表（hand_all.json），不再用分词器拼 —— 拼出来的机翻味太重。
    zh = NAMES.get(en) or CATS.get(en) or HAND.get(en) or PHRASES.get(en) or compose(en)
    budget = slot_of(en) - 1
    zh, cut = fit(zh, budget)
    if cut:
        truncated.append((en, zh))
    result[en] = zh
    for m in re.findall(r"[A-Za-z]{3,}", zh):
        haslatin.append((en, zh, m))

print("total strings:", len(result))
print("truncated to fit:", len(truncated))
print("still containing a Latin word (>=3 chars):", len(haslatin))

json.dump(result, open(os.path.join(WORK, "zh_all.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=0)

with open(os.path.join(WORK, "translate_report.txt"), "w", encoding="utf-8") as f:
    f.write("=== TRUNCATED (%d) ===\n" % len(truncated))
    for en, zh in truncated:
        f.write("  %-46s -> %s\n" % (en, zh))
    f.write("\n=== STILL HAS LATIN (%d) ===\n" % len(haslatin))
    for en, zh, m in haslatin:
        f.write("  %-46s -> %-24s [%s]\n" % (en, zh, m))
print("wrote zh_all.json + translate_report.txt")

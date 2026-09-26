# -*- coding: utf-8 -*-
"""Merge hand_01..hand_10.txt into hand_all.json and verify coverage."""
import io, os, json, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

W = r"D:\Programming project\插件汉化\_work"
src = [l.strip() for l in io.open(os.path.join(W, "params_src.txt"), encoding="utf-8")
       if l.strip()]

hand = {}
dupes, badline = [], []
for i in range(1, 11):
    p = os.path.join(W, "hand_%02d.txt" % i)
    for ln, line in enumerate(io.open(p, encoding="utf-8"), 1):
        line = line.rstrip("\n")
        if not line.strip():
            continue
        if "|" not in line:
            badline.append("%s:%d  %r" % (os.path.basename(p), ln, line))
            continue
        en, zh = line.split("|", 1)
        if en in hand and hand[en] != zh:
            dupes.append("%-40s  %s  vs  %s" % (en, hand[en], zh))
        hand[en] = zh

missing = [s for s in src if s not in hand]
extra = [k for k in hand if k not in set(src)]

# slot budget check against the real DLL slot size (8-byte aligned)
def slot_of(s):
    return max(8, -(-(len(s) + 1) // 8) * 8)

over = []
for en, zh in hand.items():
    budget = slot_of(en) - 1
    try:
        n = len(zh.encode("gbk"))
    except UnicodeEncodeError as e:
        over.append("%-42s -> %s   [NOT GBK: %s]" % (en, zh, e))
        continue
    if n > budget:
        over.append("%-42s -> %s   need %d > %d" % (en, zh, n, budget))

latin = [(en, zh) for en, zh in hand.items() if re.search(r"[A-Za-z]{3,}", zh)]

print("source params      :", len(src))
print("hand-written       :", len(hand))
print("missing            :", len(missing))
print("extra (not needed) :", len(extra))
print("bad lines          :", len(badline))
print("conflicting dupes  :", len(dupes))
print("over budget / bad  :", len(over))
print("still has latin    :", len(latin))
print()

log = []
if badline:
    log.append("=== BAD LINES ==="); log += ["  " + x for x in badline]
if dupes:
    log.append("=== CONFLICTING DUPES ==="); log += ["  " + x for x in dupes]
if over:
    log.append("=== OVER BUDGET / NOT GBK ==="); log += ["  " + x for x in over]
if missing:
    log.append("=== MISSING (%d) ===" % len(missing)); log += ["  " + x for x in missing[:200]]
if latin:
    log.append("=== STILL LATIN (%d) ===" % len(latin)); log += ["  %-42s -> %s" % x for x in latin]
io.open(os.path.join(W, "hand_check.txt"), "w", encoding="utf-8").write("\n".join(log))

json.dump(hand, io.open(os.path.join(W, "hand_all.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=0)
print("wrote hand_all.json + hand_check.txt")

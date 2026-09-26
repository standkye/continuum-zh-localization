# -*- coding: utf-8 -*-
"""装机前置检查：AE 是否在跑、有没有挂着的 UAC 确认框。"""
import subprocess, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

r = subprocess.run(['tasklist'], capture_output=True)
out = r.stdout.decode('gbk', errors='ignore') + r.stderr.decode('gbk', errors='ignore')

o = []
for key in ['AfterFX.exe', 'consent.exe', 'Continuum汉化安装器.exe',
            'Adobe', 'powershell', 'After Effects']:
    hits = [l.strip() for l in out.splitlines() if key.lower() in l.lower()]
    o.append(f"[{key}]  命中 {len(hits)}")
    for h in hits[:6]:
        o.append("      " + h)

open(r"D:\Programming project\插件汉化\_work\_precheck.txt", 'w', encoding='utf-8').write("\n".join(o))
print("done")

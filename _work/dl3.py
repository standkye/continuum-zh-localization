# -*- coding: utf-8 -*-
import re, os, urllib.request, ssl
WORK = r"D:\Programming project\插件汉化\_work"
html = open(os.path.join(WORK, 'is_setup.exe'), 'rb').read().decode('latin1', 'ignore')
links = sorted(set(re.findall(r'href="([^"]+)"', html, re.I)))
exe = [l for l in links if l.lower().endswith('.exe')]
log = ["页面里的链接:"]
for l in links[:40]:
    log.append("  " + l)
log.append("\n.exe 链接: " + str(exe))
open(os.path.join(WORK, 'dl3_log.txt'), 'w', encoding='utf-8').write("\n".join(log))

ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
if exe:
    u = exe[0]
    if u.startswith('//'):
        u = 'https:' + u
    elif u.startswith('/'):
        u = 'https://jrsoftware.org' + u
    elif not u.startswith('http'):
        u = 'https://jrsoftware.org/' + u
    try:
        req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=300, context=ctx) as r:
            data = r.read()
        dst = os.path.join(WORK, 'inno_installer.exe')
        open(dst, 'wb').write(data)
        with open(os.path.join(WORK, 'dl3_log.txt'), 'a', encoding='utf-8') as f:
            f.write(f"\n下载 {u}\n  {len(data)/1024/1024:.2f} MB  魔数={data[:2]!r}\n  保存 {dst}")
    except Exception as e:
        with open(os.path.join(WORK, 'dl3_log.txt'), 'a', encoding='utf-8') as f:
            f.write(f"\n下载失败 {u}: {e}")

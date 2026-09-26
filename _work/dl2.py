# -*- coding: utf-8 -*-
import urllib.request, re, os, ssl
WORK = r"D:\Programming project\插件汉化\_work"
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
req = urllib.request.Request("https://jrsoftware.org/download.php/is.exe",
                             headers={'User-Agent': 'Mozilla/5.0'})
html = urllib.request.urlopen(req, timeout=60, context=ctx).read().decode('latin1')
links = sorted(set(re.findall(r'href="([^"]+\.exe)"', html, re.I)))
log = ["页面里的 exe 链接:"]
for l in links:
    log.append("  " + l)
# 选一个 6.x 的
cand = [l for l in links if re.search(r'6\.\d', l)]
log.append("\n候选: " + str(cand))
if cand:
    u = cand[0]
    if u.startswith('/'):
        u = "https://jrsoftware.org" + u
    elif not u.startswith('http'):
        u = "https://jrsoftware.org/" + u
    log.append("下载: " + u)
    try:
        r2 = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(r2, timeout=180, context=ctx) as r:
            data = r.read()
        dst = os.path.join(WORK, 'is_setup.exe')
        open(dst, 'wb').write(data)
        log.append(f"已保存 {len(data)/1024/1024:.1f} MB -> {dst}")
        log.append("魔数: " + repr(data[:2]))
    except Exception as e:
        log.append("下载失败: " + str(e))
open(os.path.join(WORK, 'dl2_log.txt'), 'w', encoding='utf-8').write("\n".join(log))

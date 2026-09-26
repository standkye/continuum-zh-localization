# -*- coding: utf-8 -*-
import urllib.request, os, ssl
WORK = r"D:\Programming project\插件汉化\_work"
dst = os.path.join(WORK, 'is_setup.exe')
urls = [
    "https://files.jrsoftware.org/is/6/innosetup-6.4.2.exe",
    "https://files.jrsoftware.org/is/6/innosetup-6.4.3.exe",
    "https://files.jrsoftware.org/is/6/innosetup-6.4.1.exe",
    "https://files.jrsoftware.org/is/6/innosetup-6.3.3.exe",
    "https://jrsoftware.org/download.php/is.exe",
]
log = []
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
for u in urls:
    try:
        req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
            data = r.read()
        log.append(f"OK {u} -> {len(data)/1024/1024:.1f} MB")
        open(dst, 'wb').write(data)
        log.append("已保存到 " + dst)
        break
    except Exception as e:
        log.append(f"FAIL {u} -> {e}")
open(os.path.join(WORK, 'dl_log.txt'), 'w', encoding='utf-8').write("\n".join(log))

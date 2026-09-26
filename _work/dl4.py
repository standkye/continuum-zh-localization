# -*- coding: utf-8 -*-
import urllib.request, os, ssl
WORK = r"D:\Programming project\插件汉化\_work"
LOG = os.path.join(WORK, 'dl4_log.txt')
U = "https://github.com/jrsoftware/issrc/releases/download/is-6_7_3/innosetup-6.7.3.exe"
DST = os.path.join(WORK, 'inno_setup.exe')
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
msg = []
try:
    req = urllib.request.Request(U, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=600, context=ctx) as r:
        total = int(r.headers.get('Content-Length') or 0)
        got = 0
        with open(DST, 'wb') as f:
            while True:
                chunk = r.read(262144)
                if not chunk:
                    break
                f.write(chunk); got += len(chunk)
    msg.append(f"OK {U}")
    msg.append(f"  {got/1024/1024:.2f} MB / 声明 {total/1024/1024:.2f} MB")
    msg.append("  魔数 " + repr(open(DST, 'rb').read(2)))
except Exception as e:
    msg.append("FAIL " + str(e))
open(LOG, 'w', encoding='utf-8').write("\n".join(msg))

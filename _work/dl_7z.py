# -*- coding: utf-8 -*-
import urllib.request, os, ssl, subprocess
WORK = r"D:\Programming project\插件汉化\_work"
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
urls = ["https://www.7-zip.org/a/7z2409-extra.7z",
        "https://www.7-zip.org/a/7z2301-extra.7z",
        "https://www.7-zip.org/a/7z2201-extra.7z"]
SZ = r"D:\APP\Utilities\QingShan\resources\files\7za.exe"
log = []
okfile = None
for u in urls:
    try:
        req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=90, context=ctx) as r:
            data = r.read()
        p = os.path.join(WORK, os.path.basename(u))
        open(p, 'wb').write(data)
        log.append(f"OK {u} {len(data)/1024:.0f} KB")
        okfile = p
        break
    except Exception as e:
        log.append(f"FAIL {u} {e}")

sfx = None
if okfile:
    outd = os.path.join(WORK, '7zextra')
    os.makedirs(outd, exist_ok=True)
    r = subprocess.run([SZ, 'x', '-y', '-o' + outd, okfile], capture_output=True)
    log.append("解压 rc=" + str(r.returncode))
    for f in sorted(os.listdir(outd)):
        log.append("  " + f)
    for f in ('7zS.sfx', '7z.sfx', '7zSD.sfx'):
        if os.path.exists(os.path.join(outd, f)):
            sfx = os.path.join(outd, f)
    log.append("SFX 模块: " + str(sfx))
open(os.path.join(WORK, 'dl7z_log.txt'), 'w', encoding='utf-8').write("\n".join(log))

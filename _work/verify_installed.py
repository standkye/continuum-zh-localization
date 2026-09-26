# -*- coding: utf-8 -*-
import os, hashlib

BAK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"
LIB = r"C:\Program Files\BorisFX\ContinuumAE\19\lib"

aex_bak = os.path.join(BAK, "aex")
print("backup root exists:", os.path.isdir(BAK))
print("backup aex count :", len([f for f in os.listdir(aex_bak)]) if os.path.isdir(aex_bak) else "MISSING")

dlls = ["Continuum_AE_Float.dll", "Continuum_AE_8Bit.dll", "Continuum_AE_16Bit.dll",
        "Continuum_Common_AE.dll", "Continuum_3DObjects_AE.dll", "BCCPlus.dll"]
for d in dlls:
    p = os.path.join(BAK, d)
    print("  backup %-28s %s" % (d, "OK" if os.path.exists(p) else "MISSING"))

# spot check: what does an installed aex actually contain now?
import struct, re
p = os.path.join(CONT, "BCCBlur.aex")
data = open(p, "rb").read()
i = data.find(b"MIB8eman")
if i >= 0:
    size = struct.unpack("<I", data[i+12:i+16])[0]
    raw = data[i+16:i+16+size]
    txt = raw[1:1+raw[0]] if raw else b""
    txt = txt.split(b"\x00")[0]
    print("BCCBlur.aex name bytes:", txt[:40])
    for enc in ("gbk", "utf-8"):
        try:
            print("  as %-6s -> %s" % (enc, txt.decode(enc)))
        except Exception as e:
            print("  as %-6s -> <decode error>" % enc)

p2 = os.path.join(LIB, "Continuum_AE_8Bit.dll")
d2 = open(p2, "rb").read()
for probe in ("主不透明度", "关键帧输出"):
    print("8Bit dll contains %s: %s" % (probe, probe.encode("gbk") in d2))

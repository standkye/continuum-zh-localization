import os, hashlib, time, sys

LIB = r"C:\Program Files\BorisFX\ContinuumAE\19\lib"
CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"
SRC = r"D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0"

DLLS = ["Continuum_AE_Float.dll", "Continuum_AE_8Bit.dll", "Continuum_AE_16Bit.dll",
        "Continuum_Common_AE.dll", "Continuum_3DObjects_AE.dll"]

def h(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def check():
    diff = 0
    for d in DLLS:
        if h(os.path.join(LIB, d)) != h(os.path.join(SRC, d)):
            diff += 1
    if h(os.path.join(CONT, "BCCPlus.dll")) != h(os.path.join(SRC, "BCCPlus.dll")):
        diff += 1
    aex_src = [f for f in os.listdir(SRC) if f.lower().endswith(".aex")]
    for f in aex_src:
        a = os.path.join(CONT, f)
        if not os.path.exists(a) or h(a) != h(os.path.join(SRC, f)):
            diff += 1
    return diff, len(aex_src) + 6

deadline = time.time() + 110
last = None
while time.time() < deadline:
    try:
        diff, total = check()
    except Exception as e:
        diff, total = -1, 0
    if diff != last:
        print("t=%3ds  TOTAL_DIFF = %s / %d" % (time.time() - (deadline - 110), diff, total))
        sys.stdout.flush()
        last = diff
    if diff == 0:
        print("INSTALL COMPLETE: all %d files match the Chinese source." % total)
        break
    time.sleep(4)
else:
    print("timeout, last TOTAL_DIFF =", last)

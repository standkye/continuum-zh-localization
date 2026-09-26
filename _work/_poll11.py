import os, hashlib, json
DEL = r"D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0"
DLLS = ["Continuum_AE_8Bit.dll","Continuum_AE_16Bit.dll","Continuum_AE_Float.dll",
        "Continuum_Common_AE.dll","Continuum_3DObjects_AE.dll","BCCPlus.dll"]
src = os.path.join(DEL, "DLL")
# installed dir
INST = r"C:\Program Files\BorisFX\ContinuumAE\19.0.0\64-bit\lib"
print("installed dir exists:", os.path.isdir(INST))
def sha(p):
    with open(p,'rb') as f: return hashlib.sha256(f.read()).hexdigest()[:8]
rows=[]
for n in DLLS:
    s = os.path.join(src, n)
    i = os.path.join(INST, n)
    a = sha(s) if os.path.exists(s) else "MISSING"
    b = sha(i) if os.path.exists(i) else "MISSING"
    rows.append((n, a, b, "OK" if a==b and a!="MISSING" else "DIFF"))
for r in rows: print("%-28s src=%s inst=%s %s" % r)
print("OK count:", sum(1 for r in rows if r[3]=="OK"), "/", len(rows))

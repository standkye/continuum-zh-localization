import os, hashlib
DELIV = r'D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0'
CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"
LIB = r"C:\Program Files\BorisFX\ContinuumAE\19\lib"
LIB_DLLS = ["Continuum_AE_Float.dll","Continuum_AE_8Bit.dll","Continuum_AE_16Bit.dll",
            "Continuum_Common_AE.dll","Continuum_3DObjects_AE.dll"]
def sha(p):
    m=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda: f.read(1<<20), b''): m.update(b)
    return m.hexdigest()[:8]
ok=0
for d in LIB_DLLS:
    s=os.path.join(DELIV,d); i=os.path.join(LIB,d)
    a=sha(s) if os.path.exists(s) else 'MISSING'
    b=sha(i) if os.path.exists(i) else 'MISSING'
    st='OK' if a==b and a!='MISSING' else ('MISSING' if b=='MISSING' else 'OLD')
    if st=='OK': ok+=1
    print('%-28s src=%s inst=%s %s'%(d,a,b,st))
s=os.path.join(DELIV,'BCCPlus.dll'); i=os.path.join(CONT,'BCCPlus.dll')
a=sha(s) if os.path.exists(s) else 'MISSING'
b=sha(i) if os.path.exists(i) else 'MISSING'
st='OK' if a==b and a!='MISSING' else ('MISSING' if b=='MISSING' else 'OLD')
if st=='OK': ok+=1
print('%-28s src=%s inst=%s %s'%('BCCPlus.dll',a,b,st))
print('DLL OK:',ok,'/6')
# aex
aex=[f for f in os.listdir(DELIV) if f.lower().endswith('.aex')]
bad=[]
for f in aex:
    i=os.path.join(CONT,f)
    if not os.path.exists(i): bad.append(f+'(missing)'); continue
    if sha(i)!=sha(os.path.join(DELIV,f)): bad.append(f)
print('aex total',len(aex),'bad',len(bad))
for f in bad[:15]: print('  -',f)

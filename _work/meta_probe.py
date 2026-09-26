# -*- coding: utf-8 -*-
"""在每支 DLL 的「被改动槽位」里找疑似内部键/元数据，并做 revert 探针验证"""
import os, json, subprocess

WORK = r'D:\Programming project\插件汉化\_work'
TMP = r'C:\Users\Jinna\.workbuddy\dlldbg'
os.makedirs(TMP, exist_ok=True)
BK = r"C:\Program Files\BorisFX\ContinuumAE\19\Backup-English"
LIB = r"C:\Program Files\BorisFX\ContinuumAE\19\lib"
CONT = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\BorisFX\Continuum"
PY = r'C:\Users\Jinna\.workbuddy\binaries\python\versions\3.13.12\python.exe'

TESTPY = os.path.join(TMP, '_lt.py')
open(TESTPY, 'w', encoding='utf-8').write(
    "import ctypes,sys,os\n"
    "p=os.path.abspath(sys.argv[1])\n"
    "try:\n"
    "    ctypes.WinDLL(p, winmode=0); print('OK')\n"
    "except OSError as e:\n"
    "    print('FAIL %s' % getattr(e,'winerror','?'))\n"
    "except Exception as e:\n"
    "    print('FAIL other %s' % e)\n")

def load_ok(data, tag):
    fp = os.path.join(TMP, 'rv_%s.dll' % tag)
    with open(fp, 'wb') as f:
        f.write(data)
    r = subprocess.run([PY, TESTPY, fp], capture_output=True)
    o = (r.stdout + r.stderr).decode('utf-8', 'replace').strip()
    try:
        os.remove(fp)
    except Exception:
        pass
    return o.startswith('OK'), o

chains = json.load(open(os.path.join(WORK, 'dll_chains.json'), encoding='utf-8'))
out = []
def p(s=''):
    out.append(str(s))
    print(s, flush=True)

# 疑似「内部键 / 元数据字段」的英文词（大小写不敏感、去空格比较）
META_WORDS = [
    'presetname', 'filtername', 'filterversion', 'datetime', 'duration',
    'presetname', 'preset type', 'preset name', 'filter name', 'filter version',
    'creation date', 'file path', 'description', 'author', 'client',
    'resources', 'documentation', 'category', 'particles', 'grunge texture',
    'borisplugins', 'filtersets', 'utilities', 'bin', 'debug logging',
    'stringmap', 'stringpair', 'stringid', 'stringvalue',
    'licensing', 'effects list', 'tracker', 'version', 'copyright',
    'image collection', 'mocha', 'bfx-', 'borisfxdirect', 'plugin',
]
def is_meta(s):
    t = s.strip().lower()
    if t in META_WORDS:
        return True
    for w in META_WORDS:
        if len(w) >= 5 and w in t:
            return True
    return False

for T in ['Continuum_3DObjects_AE.dll', 'Continuum_AE_8Bit.dll',
          'Continuum_AE_Float.dll', 'Continuum_AE_16Bit.dll',
          'Continuum_Common_AE.dll', 'BCCPlus.dll']:
    ch = chains.get(T)
    if not ch:
        p('%s : chains 里没有' % T); continue
    bkp = os.path.join(BK, T)
    curp = os.path.join(LIB if T != 'BCCPlus.dll' else CONT, T)
    if not (os.path.exists(bkp) and os.path.exists(curp)):
        p('%s : 文件缺失' % T); continue
    bk = open(bkp, 'rb').read()
    cur = open(curp, 'rb').read()

    changed = []
    for off_s, arr in ch.items():
        o = int(off_s)
        for s in arr:
            slot = max(8, ((len(s) + 1 + 7) // 8) * 8)
            if bk[o:o + slot] != cur[o:o + slot]:
                changed.append((o, slot, s))
            o += slot
    changed.sort()

    meta = [(o, sl, s) for (o, sl, s) in changed if is_meta(s)]
    p('=' * 78)
    p('%s' % T)
    p('  改动槽位 %d，其中疑似内部键/元数据 %d' % (len(changed), len(meta)))
    p('=' * 78)
    for o, sl, s in meta:
        nb = cur[o:o + sl].split(b'\x00')[0]
        try:
            nb = nb.decode('utf-8')
        except Exception:
            nb = repr(nb)
        p('    0x%08X slot=%-3d %-34r -> %r' % (o, sl, s, nb))
    p()

    # revert 探针：把疑似元数据恢复成英文，看能否加载
    if meta and len(changed) < 600:
        d = bytearray(cur)
        for (o, sl, s) in meta:
            d[o:o + sl] = bk[o:o + sl]
        ok, o2 = load_ok(d, T.replace('.dll', '')[:14])
        p('  [revert 探针] 仅把上述 %d 个槽位恢复英文 -> %s' % (len(meta), o2))
        p()
    elif meta:
        p('  （改动槽位太多 %d，revert 探针跳过；需用分组测试）' % len(changed))
        p()

open(os.path.join(WORK, '_meta_probe.txt'), 'w', encoding='utf-8').write('\n'.join(out))

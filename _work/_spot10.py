# -*- coding: utf-8 -*-
"""抽查 batch10 译名是否真写入 patched_dll_d"""
import os, json
W = r'D:\Programming project\插件汉化\_work'
D = os.path.join(W, 'patched_dll_d')
d = json.load(open(os.path.join(W, 'batch10_miss.json'), encoding='utf-8'))
DLLS = ['BCCPlus.dll', 'Continuum_3DObjects_AE.dll', 'Continuum_AE_8Bit.dll',
        'Continuum_AE_16Bit.dll', 'Continuum_AE_Float.dll', 'Continuum_Common_AE.dll']
blobs = {}
for f in DLLS:
    p = os.path.join(D, f)
    if os.path.exists(p):
        blobs[f] = open(p, 'rb').read()

checks = ['Blur Red', 'Blue Channel', 'Edge Composite', 'Matte ', 'Spectrum 7',
          'L003 Lavender Tint', 'Face Detection Matte', 'Volumetric Rays',
          'Obey Host Draft Render', 'Show Title Safe', 'Switch to 3D Render',
          'Unpremultiply', 'Witness Protection ML', 'Auto-animate Matte',
          'Cross Process Amount', 'Guided Filter', 'Halo Only', 'Skin Tone']
hit = miss = 0
for k in checks:
    zh = d[k].encode('gbk')
    where = [f for f, b in blobs.items() if zh in b]
    if where:
        hit += 1
        print('OK   %-32s -> %-18s  %s' % (repr(k), d[k], ','.join(where)))
    else:
        miss += 1
        print('MISS %-32s -> %s' % (repr(k), d[k]))
print('hit=%d miss=%d' % (hit, miss))

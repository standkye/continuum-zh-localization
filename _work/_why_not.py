# -*- coding: utf-8 -*-
"""为什么 Curves / Allow Resizing 没进 UI 候选清单？逐条复现 _ui_miss.py 的闸门。"""
import os, collections

BASE = r'D:\Programming project\插件汉化'
PD = os.path.join(BASE, '_work', 'patched_dll_d')
out = []
def say(*a):
    out.append(' '.join(str(x) for x in a))

def sections(d):
    pe = d.find(b'PE\x00\x00')
    nsec = int.from_bytes(d[pe+6:pe+8], 'little')
    optsz = int.from_bytes(d[pe+20:pe+22], 'little')
    sb = pe + 24 + optsz
    secs = []
    for i in range(nsec):
        o = sb + i*40
        n = d[o:o+8].rstrip(b'\x00').decode('ascii','replace')
        vsz = int.from_bytes(d[o+8:o+12],'little')
        va = int.from_bytes(d[o+12:o+16],'little')
        rsz = int.from_bytes(d[o+16:o+20],'little')
        ro = int.from_bytes(d[o+20:o+24],'little')
        secs.append((n, va, max(vsz,rsz), ro))
    return secs

def sec_of(secs, off):
    for n,va,sz,ro in secs:
        if ro <= off < ro+sz: return n
    return '?'

def ident_like(t):
    return ('_' in t) or ('.' in t) or (t[:1].islower())

TARGETS = ['Curves', 'Allow Resizing']

for tgt in TARGETS:
    say('='*76)
    say('目标 %r' % tgt)
    tbz = tgt.encode('ascii') + b'\x00'
    for fn in sorted(os.listdir(PD)):
        if not fn.lower().endswith('.dll'): continue
        d = open(os.path.join(PD,fn),'rb').read()
        secs = sections(d)
        start = 0
        while True:
            i = d.find(tbz, start)
            if i < 0: break
            start = i+1
            left_ok = (i==0) or d[i-1]==0
            k = i + len(tbz)
            while k < len(d) and d[k]==0: k += 1
            avail = k - i
            sec = sec_of(secs, i)
            say('')
            say('  %s off=%#x 左邻居NUL=%s 节=%s avail=%d' % (fn,i,left_ok,sec,avail))
            if not left_ok:
                say('     -> 死因: 不是独立记号（前面不是 NUL）')
                continue
            if sec != '.rdata':
                say('     -> 死因: 不在 .rdata')
                continue
            # 邻居闸：往前 96 字节的 ident_like 串
            lo = max(0, i-96)
            hits = []
            for m in d[lo:i].split(b'\x00'):
                if len(m) >= 2:
                    t = m.decode('ascii','ignore')
                    if t and ident_like(t):
                        hits.append(t)
            if hits:
                say('     -> 死因: 邻居闸（前 96B 有标识符样串）: %r' % hits[-4:])
            else:
                say('     -> 邻居闸: 通过')
            # 附近是否有中文
            wlo = max(0,i-256); whi = min(len(d), i+256)
            cjk = any(d[q] >= 0x80 for q in range(wlo,whi))
            say('     -> 附近256B有中文: %s' % cjk)
            if not cjk:
                say('        (这一条就是被「附近要有中文」挡掉的)')
            # 打印上下文
            lo2 = max(0,i-80); hi2 = min(len(d), i+len(tgt)+80)
            chunks=[]; cur=b''; pos=lo2
            for q in range(lo2,hi2):
                c=d[q]
                if 32<=c<127 or c>=0x80:
                    if not cur: pos=q
                    cur+=bytes([c])
                else:
                    if len(cur)>=2: chunks.append((pos,cur))
                    cur=b''
            if len(cur)>=2: chunks.append((pos,cur))
            say('     --- 上下文 ---')
            for p_,c_ in chunks:
                try: t=c_.decode('gbk')
                except Exception: t=repr(c_)
                say('        @%#x %s' % (p_,t))
    say('')

open(os.path.join(BASE,'_work','_why_not.txt'),'w',encoding='utf-8').write('\n'.join(out))
print('done')

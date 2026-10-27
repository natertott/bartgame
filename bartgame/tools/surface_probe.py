"""Validate real-ROM prop/floor composition and clearing in mGBA.

python tools/surface_probe.py

The logical ground remains authoritative for collision. Its actual substrate
must be present on BG2 while transparent material is on BG1; clearing and
opening use the normal gameplay actions, then inspect the renderer in VRAM.
"""
import json
from pathlib import Path
import probe as P
import critical_path as CP
import lift_probe as L
import myst_probe as M

UNDERLAY_OFFSET=2+2048+2048+4096
checks=[]


def check(name,ok,detail=''):
    checks.append(bool(ok));print(('PASS' if ok else 'FAIL'),name,detail,flush=True)


def under(c,x,y):return P.r16(c,P.sym('gRoom')+UNDERLAY_OFFSET+(y*32+x)*2)&65535


def entry(c,base,x,y):
    tx,ty=x*2,y*2
    sb=base+((ty>>5)<<1)+(tx>>5)
    a=0x06000000+sb*2048+((ty&31)*32+(tx&31))*2
    return tuple(P.r16(c,a+k)&65535 for k in (0,2,64,66))


def expected(c,mt):
    a=P.sym('metatile_map_myst' if CP.area(c)==2 else 'metatile_map_forest')+mt*8
    return tuple(P.r16(c,a+i*2)&65535 for i in range(4))


def main():
    c=P.boot();CP.dismiss(c);w=CP.world(c);P.enter_forest(c)
    counts=0
    for cell,d in enumerate(w['cells']):
        L.warp(c,cell,next(i for i,g in enumerate(d['gate']) if g))
        _,_,grid=CP.room_tiles(c)
        for (x,y),mt in grid.items():
            if not P.r8(c,P.sym('metatile_prop')+mt):continue
            base=under(c,x,y);counts+=1
            check('prop has a floor substrate',P.r8(c,P.sym('metatile_type')+base)==0,f'cell {cell} ({x},{y}) mt {mt} base {base}')
            check('BG2 uses substrate',entry(c,28,x,y)==expected(c,base))
            ov=P.r16(c,P.sym('gRoom')+2050+(y*32+x)*2)&65535
            if ov in (65535,CP.mt('SPARKLE'),CP.mt('SPARKLE_WHITE'),CP.mt('BLIGHT_MIST')):
                check('BG1 uses transparent prop',entry(c,24,x,y)==expected(c,mt))
    check('nonzero props checked',counts>50,str(counts))
    # Lifting through the real button path must reveal the stored surface.
    for name in ('BUSH','ROCK_SMALL','BOULDER'):
        found=None
        for cell,d in enumerate(w['cells']):
            L.warp(c,cell,next(i for i,g in enumerate(d['gate']) if g))
            found=L.find_tile(c,name)
            if found:break
        if not found and name=='BOULDER':
            cell=next(i for i,d in enumerate(w['cells']) if d['role'] not in (1,2,3))
            assert M.enter(c,cell,'boulders',2,2)
            found=L.find_tile(c,name)
        check(name+' exists',found is not None)
        if not found:continue
        x,y,spot,key=found;base=under(c,x,y)
        pl=P.sym('gPl');P.w8(c,pl+8,P.r8(c,pl+8)|0x20)
        L.stand_before(c,spot,key);P.press(c,'R',2,0)
        for _ in range(32):
            if L.state(c)==L.PS_CARRY:break
            c.run_frame()
        _,_,grid=CP.room_tiles(c)
        check(name+' lifts normally',L.state(c)==L.PS_CARRY)
        check(name+' reveals exact substrate',grid[(x,y)]==base)
        check(name+' redraws BG2',entry(c,28,x,y)==expected(c,base))
        P.press(c,'R',2,0);P.run(c,90)
    # Open an ordinary field chest; both states keep their substrate.
    found=None
    for cell,d in enumerate(w['cells']):
        if d['role'] not in (4,10):continue
        L.warp(c,cell,next(i for i,g in enumerate(d['gate']) if g))
        found=L.find_tile(c,'CHEST')
        if found:break
    check('field chest exists',found is not None)
    if found:
        x,y,_,_=found;base=under(c,x,y)
        check('chest opens through normal interaction',CP.open_chest(c))
        check('open chest retains substrate',under(c,x,y)==base)
        check('open chest background is original floor',entry(c,28,x,y)==expected(c,base))
        check('open chest material is BG1',entry(c,24,x,y)==expected(c,CP.mt('CHEST_OPEN')))
    print('RESULT %s %d/%d'%('PASS' if all(checks) else 'FAIL',sum(checks),len(checks)))
    return int(not all(checks))


if __name__=='__main__':raise SystemExit(main())

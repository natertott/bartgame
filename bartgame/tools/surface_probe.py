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
import bloom_probe as B

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


def hero_priority(c):
    # HERO_TILE is resident tile0, 64x32 (horizontal shape1,size3), palette0.
    # UI icons use other tiles/palettes, so inspect the actual hardware OAM.
    for i in range(128):
        at=0x07000000+i*8
        a0=P.r16(c,at)&65535;a1=P.r16(c,at+2)&65535;a2=P.r16(c,at+4)&65535
        if (a0&0x0300)==0x0200:continue
        if ((a0>>14)&3)==1 and (a1>>14)==3 and (a2&1023)==0 and (a2>>12)==0:
            return (a2>>10)&3
    return None


def large_chest_material(c,x,y):
    """The larger chest replaces its BG1 drawing with one real OBJ frame."""
    CP.clear_enemies(c);CP.heal(c);c.clear_keys(*range(10))
    P.w8(c,P.sym('gActors')+35,0)
    CP.teleport(c,x*16+8,(y+1)*16+14);P.run(c,48)
    tile=P.r16(c,L.ssym('sChestTile'))&65535
    frame=P.r8(c,L.ssym('sChestFrame'))
    defs=B.definitions(Path(P.ROOT)/'build/gen/assets.h')
    sh=P.sym('sheets')+defs['SHEET_INTERACTIVECHEST']*12
    source=P.r32(c,sh);size=P.r8(c,sh+6)*32
    got=B.bytes_at(c,0x06010000+tile*32,size)
    pixels=B.pixels(got,32,32)
    width=max((p[0] for p in pixels),default=-1)-min((p[0] for p in pixels),default=0)+1
    height=max((p[1] for p in pixels),default=-1)-min((p[1] for p in pixels),default=0)+1
    actual=[e for e in B.oam(c) if e['tile']==tile and e['shape']==0 and e['size']==2]
    return (0<tile and tile+size//32<=876 and len(actual)==1 and width>16 and height>16 and
            got==B.bytes_at(c,source+frame*size,size) and entry(c,24,x,y)==(0,0,0,0))


def depth_checks(c,w):
    for cell,x,y,want,label in ((0,16,11,1,'flat prop under hero'),
                                (6,23,18,1,'rock north of hero'),
                                (20,13,6,1,'blighted rock north of hero'),
                                (6,23,16,2,'hero behind solid prop')):
        L.warp(c,cell,next(i for i,g in enumerate(w['cells'][cell]['gate']) if g))
        CP.clear_enemies(c);CP.teleport(c,x*16+8,y*16+12);P.run(c,96)
        check('OAM '+label,hero_priority(c)==want,'priority %s'%hero_priority(c))
    # Original tree crowns must still hide the hero when his feet are beneath
    # them. Choose a real traversable crown tile, not a staged wall overlap.
    target=None
    for cell,d in enumerate(w['cells']):
        L.warp(c,cell,next(i for i,g in enumerate(d['gate']) if g))
        _,_,grid=CP.room_tiles(c);room=P.sym('gRoom')
        for (x,y),mt in grid.items():
            ov=P.r16(c,room+2050+(y*32+x)*2)&65535
            if ov==65535 or not 3<=x<29 or not 3<=y<21:continue
            name=L.tiles.METATILES[ov]['name']
            if name.startswith(('tree_top','tree_mid','tree2_','gtree','birch_','fir_')) and P.r8(c,P.sym('metatile_type')+mt)==0:
                target=(x,y);break
        if target:break
    check('traversable original crown found',target is not None)
    if target:
        CP.clear_enemies(c);CP.teleport(c,target[0]*16+8,target[1]*16+12);P.run(c,96)
        check('OAM original crown still occludes hero',hero_priority(c)==2,'priority %s'%hero_priority(c))


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
                if mt in (CP.mt('CHEST'),CP.mt('CHEST_OPEN')):
                    check('chest uses enlarged OBJ above its substrate',large_chest_material(c,x,y))
                else:
                    check('BG1 uses transparent prop',entry(c,24,x,y)==expected(c,mt))
    check('nonzero props checked',counts>50,str(counts))
    depth_checks(c,w)
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
        check('open chest material is the enlarged OBJ',large_chest_material(c,x,y))
    print('RESULT %s %d/%d'%('PASS' if all(checks) else 'FAIL',sum(checks),len(checks)))
    return int(not all(checks))


if __name__=='__main__':raise SystemExit(main())

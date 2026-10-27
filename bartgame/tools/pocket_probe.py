"""Exercise optional room pockets in the real ROM, including return visits.

python tools/pocket_probe.py [--seed 0xB4A7]
Debug navigation and item ownership isolate room reactions; barrier opening,
cape movement and loot pickup use the game's actual input and actor paths.
"""
import os
import sys
sys.path.insert(0,os.path.dirname(__file__))
import probe as P
import critical_path as C
import lift_probe as L


def main():
    seed=int(sys.argv[sys.argv.index('--seed')+1],0) if '--seed' in sys.argv else 0xB4A7
    c=P.boot(seed=seed); P.enter_forest(c)
    w=C.world(c); seen=set(); results=[]
    def check(name,ok,detail=''):
        results.append(bool(ok));print(('PASS' if ok else 'FAIL'),name,detail,flush=True)
    S=P.sym('gSpots'); W=P.sym('gWorld'); pl=P.sym('gPl')
    for cell in range(25):
        side=next(s for s,g in enumerate(w['cells'][cell]['gate']) if g)
        C.heal(c); L.warp(c,cell,side); C.clear_enemies(c)
        kind=P.r8(c,S+57)
        if not kind or kind in seen:continue
        seen.add(kind)
        gx,gy=P.r8(c,S+55),P.r8(c,S+56)
        tx,ty=P.r8(c,S+44),P.r8(c,S+45)
        dx=(tx>gx)-(tx<gx);dy=(ty>gy)-(ty<gy)
        # Pockets run along one axis; the outside approach is behind the neck.
        C.teleport(c,(gx-dx)*16+8,(gy-dy)*16+12)
        key='RIGHT' if dx>0 else 'LEFT' if dx<0 else 'DOWN' if dy>0 else 'UP'
        back={'UP':'DOWN','DOWN':'UP','LEFT':'RIGHT','RIGHT':'LEFT'}[key]
        bit={1:2,2:4,3:8}[kind]; eq={1:C.EQ_BOMBS,2:C.EQ_LAMP,3:C.EQ_CLOAK}[kind]
        initial=L.ttype(C.tt_at(c,gx,gy))
        check('pocket starts behind its readable barrier',initial=={1:'CRACK',2:'WEB',3:'PIT'}[kind],'%d cell%d %s'%(kind,cell,initial))
        P.w8(c,pl+8,P.r8(c,pl+8)|bit)
        if kind==1:P.w8(c,pl+7,10)
        C.equip_b(c,eq)
        if kind==3:
            P.hold(c,key,3)
            c.set_keys(P.key(c,key));P.press(c,'A',2,0)
            P.run(c,25);c.clear_keys(P.key(c,key));P.run(c,15)
            px,py=P.player_pos(c)
            check('cape crosses the pocket neck',dx*(px-(gx*16+8))+dy*(py-(gy*16+12))>=20,'pos %s gate%s'%(P.player_pos(c),(gx,gy)))
        else:
            P.hold(c,key,5);P.press(c,'A',2,4)
            if kind==1:P.hold(c,back,30);P.run(c,170)
            else:P.run(c,30)
            check('item opens the local barrier',L.ttype(C.tt_at(c,gx,gy))=='FLOOR')
            check('local opening records its save bit',P.r8(c,W+4+cell*13+4)&0x20)
        # Walk through the opened neck and into the hoard; no teleport across it.
        if kind!=3:
            C.teleport(c,(gx-dx)*16+8,(gy-dy)*16+12)
        P.hold(c,key,36);P.run(c,12)
        loot=P.r8(c,W+4+cell*13+4)&0x10
        check('the hoard is collected from inside',loot,'%d cell%d treasure%s pos%s'%(kind,cell,(tx,ty),P.player_pos(c)))
        C.heal(c);L.warp(c,cell,side)
        check('loot stays taken after returning',P.r8(c,W+4+cell*13+4)&0x10)
        if kind!=3:
            check('opened bomb or candle neck stays open',L.ttype(C.tt_at(c,gx,gy))=='FLOOR')
        else:
            check('cape route keeps its jump terrain',L.ttype(C.tt_at(c,gx,gy))=='PIT')
    check('seed has all three item pocket types',seen=={1,2,3},str(seen))
    print('RESULT %s %d/%d'%('PASS' if all(results) else 'FAIL',sum(results),len(results)))
    return 0 if all(results) else 1

if __name__=='__main__':sys.exit(main())

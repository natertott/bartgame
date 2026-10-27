"""Reproduce the gardener's blocked-front regression in actual mGBA.

The seed22/cell9 baseline put a censer at (8,16) behind a solid stump at
(8,17). Inspect real collision, use the lamp from every south approach,
receive the gardener's key, and revisit to check stable saved positions.
Inventory/room navigation/position and cleared enemies are fixtures; no
terrain, quest flag or censer state is assigned by this probe.
"""
import argparse
import hashlib
import json
from pathlib import Path

import probe as P
import critical_path as C
import roomgen_probe as R


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--rom',default=P.ROM)
    ap.add_argument('--map',default=P.MAP)
    ap.add_argument('--header',default=str(Path(P.ROOT)/'build/gen/assets.h'))
    ap.add_argument('--out',default='/tmp/torch-access.json')
    args=ap.parse_args();P.ROM=args.rom;P.MAP=args.map;P._syms=None
    defs=R.definitions(args.header);checks=[]
    def check(name,okay,detail=None):
        checks.append({'name':name,'passed':bool(okay),'detail':detail})
        print(('PASS' if okay else 'FAIL'),name,'' if detail is None else detail,flush=True)
    c=P.boot(rom=args.rom,seed=22);C.dismiss(c);world=C.world(c)
    cell=9;desc=world['cells'][cell];side=next(i for i,g in enumerate(desc['gate']) if g)
    check('seed22 cell9 is the naturally generated gardener quest',desc['role']==7,desc)
    P.enter_forest(c);R.warp(c,cell,side);C.clear_enemies(c);C.dismiss(c)
    layout=R.Layout(c,defs);seen=layout.flood(R.landing(side))
    g=P.sym('gSpots');pl=P.sym('gPl');flags=P.sym('gWorld')+4+cell*13+11
    npc=(P.r8(c,g+27),P.r8(c,g+28))
    positions=[(P.r8(c,g+31+i*2),P.r8(c,g+32+i*2)) for i in range(P.r8(c,g+39))]
    check('four unique cold censers exist',len(positions)==len(set(positions))==4,positions)
    check('gardener south speaking lane is reachable without future items',layout.reaches(seen,(npc[0],npc[1]+1)),npc)
    check('censers avoid the gardener and both speaking tiles',all(not(x==npc[0] and npc[1]-1<=y<=npc[1]+2) for x,y in positions))
    for i,(x,y) in enumerate(positions):
        check('censer%d south approach is reachable without future items'%i,layout.reaches(seen,(x,y+1)),[x,y+1])
        check('censer%d south approach is free physical floor'%i,layout.types[x,y+1]==defs['TT_FLOOR'] and layout.masks[x,y+1]==0)
    # Give only lamp ownership, not the later cape/bombs/gauntlet. The
    # unchanged gameplay actions must light each real generated censer.
    P.w8(c,pl+8,P.r8(c,pl+8)|4);C.equip_b(c,C.EQ_LAMP)
    for i,(x,y) in enumerate(positions):
        C.heal(c);C.clear_enemies(c);C.teleport(c,x*16+8,(y+1)*16+14)
        P.hold(c,'UP',4);P.press(c,'A',2,30)
        check('real south-facing lamp use lights censer%d'%i,C.tt_at(c,x,y)==defs['MT_TORCH_LIT'])
    npc_actor=C.find_actor(c,5)
    check('the gardener remains present',npc_actor is not None)
    keys_before=P.r8(c,pl+6)
    if npc_actor:
        C.teleport(c,npc_actor['x'],npc_actor['y']+22);P.hold(c,'UP',6);P.press(c,'A',2,30);C.dismiss(c)
        check('talking after lighting all four completes the quest',P.r8(c,flags)&4)
        key=C.find_actor(c,4,4)
        if key:C.teleport(c,key['x'],key['y']+2);P.run(c,12)
        check('the existing quest key is collected once',P.r8(c,pl+6)==keys_before+1,{'before':keys_before,'after':P.r8(c,pl+6)})
    R.warp(c,cell,side);C.clear_enemies(c);C.dismiss(c)
    revisited=[(P.r8(c,g+31+i*2),P.r8(c,g+32+i*2)) for i in range(P.r8(c,g+39))]
    check('quest completion preserves all four generated positions',revisited==positions,revisited)
    check('revisiting keeps all four censers lit',len(revisited)==4 and all(C.tt_at(c,x,y)==defs['MT_TORCH_LIT'] for x,y in revisited))
    npc_actor=C.find_actor(c,5)
    if npc_actor:
        C.teleport(c,npc_actor['x'],npc_actor['y']+22);P.hold(c,'UP',6);P.press(c,'A',2,30);C.dismiss(c)
        check('the gardener cannot pay the same key twice',P.r8(c,pl+6)==keys_before+1 and C.find_actor(c,4,4) is None)
    report={'rom_sha256':hashlib.sha256(Path(args.rom).read_bytes()).hexdigest(),'emulator':'mGBA 0.10.5','seed':'0x16','cell':9,'method':__doc__.strip(),'positions':positions,'npc':npc,'passed':sum(row['passed'] for row in checks),'total':len(checks),'checks':checks}
    Path(args.out).write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT %s %d/%d'%('PASS' if report['passed']==report['total'] else 'FAIL',report['passed'],report['total']))
    return int(report['passed']!=report['total'])


if __name__=='__main__':raise SystemExit(main())

"""Capture the built ROM's forest and natural mysteries through mGBA.

python3 tools/forest_review.py OUT [--seed 0xB4A7]

Every PNG is an unmodified 240x160 emulator framebuffer. Debug navigation
selects generated rooms; neither room layouts nor actor rosters are composed
outside the game. The seed, ROM SHA256 and destinations are recorded in JSON.
"""
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import probe as P
import critical_path as CP
import lift_probe as LP
import myst_probe as MP


def main():
    out = sys.argv[1]
    seed = int(sys.argv[sys.argv.index('--seed')+1], 0) if '--seed' in sys.argv else 0xB4A7
    os.makedirs(out, exist_ok=True)
    if '--rom' in sys.argv: P.ROM=sys.argv[sys.argv.index('--rom')+1]
    if '--map' in sys.argv: P.MAP=sys.argv[sys.argv.index('--map')+1]
    c = P.boot(rom=P.ROM, seed=seed)
    CP.dismiss(c)
    P.snap(c, os.path.join(out, 'drain_control.png'))
    world = CP.world(c)
    record = dict(seed=hex(seed), rom_sha256=hashlib.sha256(open(P.ROM,'rb').read()).hexdigest(),
                  navigation='mGBA runtime room transitions; original generated rooms and enemies', captures=[])
    P.enter_forest(c)
    for cell, desc in enumerate(world['cells']):
        side = next(i for i,g in enumerate(desc['gate']) if g)
        CP.heal(c)
        LP.warp(c, cell, side)
        CP.heal(c)
        # Navigate to a generated enemy spawn point, as roomshots.py does.
        g=P.sym('gSpots')
        if P.r8(c,g+24):
            x,y=P.r8(c,g),P.r8(c,g+1)
            CP.teleport(c,x*16+8,y*16+12)
        P.run(c, 8)
        # Read the real collision contracts from the loaded ROM, not art Python.
        R=P.sym('gRoom'); typ=P.sym('metatile_type'); coll=P.sym('metatile_coll')
        physics=[]
        for layer in (0,1):
            for y in range(P.r8(c,R+1)):
                for x in range(P.r8(c,R)):
                    mt=P.r16(c,R+2+layer*2048+(y*32+x)*2)&0xffff
                    physics += [255,255] if mt==65535 else [P.r8(c,typ+mt),P.r8(c,coll+mt)]
        physics += [P.r8(c,g+i) for i in range(25)]
        geometry=hashlib.sha256(bytes(physics)).hexdigest()
        name='forest_%02d_stage%d.png' %(cell,desc['stage'])
        P.snap(c,os.path.join(out,name))
        record['captures'].append(dict(file=name,cell=cell,stage=desc['stage'],area=CP.area(c),geometry_sha256=geometry))
    # Enter natural, unvisited generated mysteries, one of each style present.
    seen=set()
    for cell in range(25):
        m=P.r8(c,P.sym('gWorld')+MP.MYST_OFF+cell)
        if not m: continue
        kind=MP.KINDS[m&15]; size=(m>>4)&3; style=(m>>6)&3
        if style in seen: continue
        c = P.boot(rom=P.ROM, seed=seed)
        P.enter_forest(c)
        assert MP.enter(c,cell,kind,size,style), ('mystery entrance',cell,m)
        CP.heal(c)
        name='mystery_%s.png'%('cave','hollow','thicket')[style]
        # Also show the room's wall treatment, from a real walkable tile.
        R=P.sym('gRoom'); w=P.r8(c,R)
        _,_,grid=MP.grid(c)
        typ=P.sym('metatile_type')
        spot=next(((x,y) for y in range(3,7) for x in range(w//2-2,w//2+3)
                   if P.r8(c,typ+grid[(x,y)])==0),None)
        if spot:
            CP.teleport(c,spot[0]*16+8,spot[1]*16+12)
            P.run(c,8)
        P.snap(c,os.path.join(out,name))
        record['captures'].append(dict(file=name,cell=cell,kind=kind,size=size,style=style,area=CP.area(c)))
        seen.add(style)
    with open(os.path.join(out,'capture.json'),'w') as f: json.dump(record,f,indent=2)
    print(json.dumps(record,indent=2))


if __name__=='__main__': main()

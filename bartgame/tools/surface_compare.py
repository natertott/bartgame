"""Compare seeded physics/spawns to a pre-art-change ROM in real mGBA.

python tools/surface_compare.py --before-rom ROM --before-map MAP --out JSON
Reads logical tile contracts and the built solidity grid from each ROM;
render substrates/palette indices deliberately do not enter the comparison.
"""
import argparse
import hashlib
import json
from pathlib import Path
import probe as P
import critical_path as C
import lift_probe as L


def inspect(c):
    room=P.sym('gRoom');typ=P.sym('metatile_type');coll=P.sym('metatile_coll')
    values=[]
    for layer in (0,1):
        for y in range(P.r8(c,room+1)):
            for x in range(P.r8(c,room)):
                mt=P.r16(c,room+2+layer*2048+(y*32+x)*2)&65535
                if mt==65535:
                    values.extend((0,0))
                else:
                    t,m=P.r8(c,typ+mt),P.r8(c,coll+mt)
                    # Purely visual floor overlays do not block or interact.
                    values.extend((t,m) if layer==0 or t else (0,0))
    solidity=bytes(P.r8(c,room+4098+i) for i in range(4096))
    spots=bytes(P.r8(c,P.sym('gSpots')+i) for i in range(58))
    return {'logical':hashlib.sha256(bytes(values)).hexdigest(),
            'solid':hashlib.sha256(solidity).hexdigest(),
            'spots':hashlib.sha256(spots).hexdigest()}


def scan(rom,linker_map,seeds):
    P.MAP=linker_map;P._syms=None;result=[]
    for seed in seeds:
        c=P.boot(rom=rom,seed=seed);C.dismiss(c);world=C.world(c);P.enter_forest(c)
        for cell,desc in enumerate(world['cells']):
            C.heal(c);L.warp(c,cell,next(i for i,g in enumerate(desc['gate']) if g))
            result.append({'seed':hex(seed),'cell':cell,**inspect(c)})
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--before-rom',required=True);ap.add_argument('--before-map',required=True)
    ap.add_argument('--seeds',default='0xB4A7,0xDEADBEEF,7');ap.add_argument('--out',required=True)
    args=ap.parse_args();seeds=[int(s,0) for s in args.seeds.split(',')]
    current_rom,current_map=P.ROM,P.MAP
    old=scan(args.before_rom,args.before_map,seeds);new=scan(current_rom,current_map,seeds)
    errors=[{'before':a,'after':b} for a,b in zip(old,new) if a!=b]
    report={'checked_rooms':len(new),'unchanged_rooms':len(new)-len(errors),'differences':errors,
            'before_sha256':hashlib.sha256(Path(args.before_rom).read_bytes()).hexdigest(),
            'after_sha256':hashlib.sha256(Path(current_rom).read_bytes()).hexdigest()}
    Path(args.out).write_text(json.dumps(report,indent=2))
    print('RESULT %s %d/%d physical layouts and spawn records unchanged'%('FAIL' if errors else 'PASS',report['unchanged_rooms'],len(new)))
    return int(bool(errors))


if __name__=='__main__':raise SystemExit(main())

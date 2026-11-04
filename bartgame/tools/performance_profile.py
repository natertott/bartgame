#!/usr/bin/env python3
"""Development-only GBA timer2/3 cycle samples; production cadence is measured separately.

The room remains generated and AI remains active. Optional controlled swarms
replace its original enemies and are labelled separately. Healing/invulnerability
and central safe positioning isolate CPU cost, not combat difficulty.
"""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import probe as P
import critical_path as C
import lift_probe as L

NAMES=('total','video','text_flush','upload','tile_animation','input','game','sound',
       'player_update','items_update','enemies_update','npcs_update','objects_update',
       'room_events','camera_dark','hud','glitter_front','folk_front','interactive_back',
       'player_draw','enemies_draw','folk_draw','objects_draw','interactive_front','glitter_back')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bundle',required=True);ap.add_argument('--out',required=True)
    ap.add_argument('--seed',type=lambda x:int(x,0),default=0xB4A7)
    ap.add_argument('--cell',type=int);ap.add_argument('--swarm',type=int)
    ap.add_argument('--type',type=int,default=0);ap.add_argument('--frames',type=int,default=240)
    a=ap.parse_args();b=Path(a.bundle);out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    P.MAP=str(b/'bartgame.map');P._syms=None
    c=P.boot(rom=str(b/'bartgame.gba'),seed=a.seed);C.dismiss(c);P.enter_forest(c);C.dismiss(c)
    world=C.world(c)
    if a.cell is not None:L.warp(c,a.cell,next(i for i,x in enumerate(world['cells'][a.cell]['gate']) if x))
    # Choose a real unblocked floor cell near the middle, without changing terrain.
    w,h,grid=C.room_tiles(c);candidates=[]
    for (x,y),mt in grid.items():
        if mt!=65535 and not P.r8(c,P.sym('metatile_coll')+mt):
            typ=P.r8(c,P.sym('metatile_type')+mt)
            if typ==0 and 2<x<w-3 and 2<y<h-3:candidates.append((abs(x-w//2)+abs(y-h//2),x,y))
    if candidates:
        _,x,y=min(candidates);C.teleport(c,x*16+8,y*16+14)
    pl=P.sym('gPl');P.w16(c,pl+2,80);P.w16(c,pl,80)
    if a.swarm is not None:
        C.clear_enemies(c);P.w16(c,P.sym('gDbgSpawn'),(a.swarm<<8)|a.type)
    P.run(c,40);rows=[];seq=P.r32(c,P.sym('gPerfSequence'))
    for _ in range(a.frames):
        C.heal(c);P.run(c,1);now=P.r32(c,P.sym('gPerfSequence'))
        if now!=seq:
            rows.append({'sequence':now,'vblank':P.r32(c,P.sym('gFrame')),
                         'cycles':[P.r32(c,P.sym('gPerfCycles')+i*4) for i in range(len(NAMES))]})
            seq=now
    summary={n:{'mean':round(statistics.mean(r['cycles'][i] for r in rows),1),
                'max':max(r['cycles'][i] for r in rows),
                'p95':sorted(r['cycles'][i] for r in rows)[min(len(rows)-1,int(len(rows)*.95))]}
             for i,n in enumerate(NAMES)}
    result={'method':__doc__,'rom_sha256':hashlib.sha256((b/'bartgame.gba').read_bytes()).hexdigest(),
            'instrumented':True,'cycle_budget':280896,'seed':hex(a.seed),'cell':C.cell(c),
            'swarm':a.swarm,'type':a.type,'video_frames':a.frames,'completed_samples':len(rows),
            'phase_names':NAMES,'summary':summary,'samples':rows}
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'samples':len(rows),'worst':sorted(summary.items(),key=lambda x:-x[1]['mean'])[:10]}))
    P.snap(c,str(out.with_suffix('.png')))

if __name__=='__main__':main()

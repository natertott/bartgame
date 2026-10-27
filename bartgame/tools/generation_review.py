"""Inspect seeded progression and capture the real ROM's new room composition.

python tools/generation_review.py OUTDIR --seed 0xB4A7

Uses normal mGBA room transitions with debug navigation to frame generated
scenery. Native 240x160 framebuffers are saved without terrain/sprite compositing.
The accompanying JSON lists gated route legs, required tasks and optional rooms.
"""
import argparse
from collections import Counter, deque
import hashlib
import json
from pathlib import Path

import probe as P
import critical_path as CP
import lift_probe as LP
import myst_probe as MP
import tiles


def route(world, start, end, stage):
    parents={start:None};todo=deque([start])
    while todo:
        c=todo.popleft()
        if c==end:break
        for side,g in enumerate(world['cells'][c]['gate']):
            if g in (0,5,7) or (g==3 and stage<1) or (g==4 and stage<2) or (g==6 and stage<3):continue
            x,y=c%5+(side==1)-(side==3),c//5+(side==2)-(side==0)
            if not (0<=x<5 and 0<=y<5):continue
            n=y*5+x
            if n not in parents:parents[n]=c;todo.append(n)
    assert end in parents, ('unreachable progression leg',start,end,stage)
    result=[];c=end
    while c is not None:result.append(c);c=parents[c]
    return list(reversed(result))


def pacing(world):
    start=world['entry'];legs=[];whole=[start]
    for stage,target in enumerate(world['key_cell']+[world['goal']]):
        leg=route(world,start,target,stage)
        legs.append({'stage':stage,'from':start,'to':target,'cells':leg,'crossings':len(leg)-1})
        whole+=leg[1:];start=target
    edges=Counter(tuple(sorted((a,b))) for a,b in zip(whole,whole[1:]))
    return {'legs':legs,'required_crossings':len(whole)-1,'required_rooms':len(set(whole)),
            'optional_rooms':25-len(set(whole)),
            'repeated_crossings':sum(n-1 for n in edges.values()),'route':whole}


def maze_svg(report):
    """A labelled graph of the generated maze, separate from game frames."""
    world=report['world']; metric=report['pacing']
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="640" height="680" viewBox="0 0 640 680">',
           '<rect width="640" height="680" fill="#101820"/>',
           '<g font-family="sans-serif" fill="#e8e4cf">',
           '<text x="24" y="32" font-size="21">Seed %s — generated maze</text>'%report['seed'],
           '<text x="24" y="58" font-size="14">%d required crossings · %d optional rooms · %d repeated crossings</text>'%(metric['required_crossings'],metric['optional_rooms'],metric['repeated_crossings'])]
    center=lambda cell:(64+(cell%5)*126,112+(cell//5)*112)
    colors={1:'#7b9d80',2:'#7b9d80',3:'#e1a657',4:'#e8e4cf',5:'#6388b5',6:'#b48de8'}
    for cell,desc in enumerate(world['cells']):
        x,y=center(cell)
        for side in (1,2):
            g=desc['gate'][side]
            if not g:continue
            n=cell+(1 if side==1 else 5)
            if n>=25:continue
            xx,yy=center(n);color=colors.get(g,'#7b9d80')
            parts.append('<path d="M%d,%d L%d,%d" stroke="%s" stroke-width="5"/>'%(x,y,xx,yy,color))
            if g in (3,4,5,6):
                tag={3:'BOMB',4:'CANDLE',5:'KEY',6:'CAPE'}[g]
                parts.append('<text x="%d" y="%d" text-anchor="middle" fill="%s" font-size="9">%s</text>'%((x+xx)//2,(y+yy)//2-8,color,tag))
    stage=['#294f42','#4c5740','#53455d','#61386d']
    for cell,desc in enumerate(world['cells']):
        x,y=center(cell);label=str(cell)
        if cell==world['entry']:label+=' START'
        elif cell==world['goal']:label+=' HEART'
        elif cell in world['key_cell']:label+=' TASK %d'%(world['key_cell'].index(cell)+1)
        parts.append('<rect x="%d" y="%d" width="92" height="58" rx="8" fill="%s" stroke="#97a08b"/>'%(x-46,y-29,stage[desc['stage']]))
        parts.append('<text x="%d" y="%d" text-anchor="middle" font-size="12">%s</text>'%(x,y-3,label))
        parts.append('<text x="%d" y="%d" text-anchor="middle" font-size="11">stage %d</text>'%(x,y+15,desc['stage']))
    parts.extend(['<text x="24" y="627" font-size="12">Task 1: plates → Blightseeds · Task 2: waves → candle · Task 3: guardian → cape</text>',
                  '<text x="24" y="650" font-size="12">This is a review diagram of the ROM’s graph, not a game screenshot.</text></g></svg>'])
    return '\n'.join(parts)


def settle_view(c):
    # The camera eases at four pixels/frame. Let it catch the debug-navigated
    # hero and let trial enemies spawn before capturing actual framebuffers.
    for _ in range(96):
        CP.heal(c)
        c.run_frame()
    while P.r32(c,P.sym('gFrame')) & 2:
        CP.heal(c)
        c.run_frame()


def focus(c):
    """Choose a walkable camera target with legible terrain and landmarks."""
    room=P.sym('gRoom');typ=P.sym('metatile_type')
    w,h=P.r8(c,room),P.r8(c,room+1)
    names={};walk=[]
    for y in range(h):
        for x in range(w):
            mt=P.r16(c,room+2+(y*32+x)*2)&65535
            ov=P.r16(c,room+2050+(y*32+x)*2)&65535
            names[x,y]=tiles.METATILES[mt]['name']
            if P.r8(c,typ+mt)==0 and ov==65535 and 3<=x<w-3 and 3<=y<h-3:
                walk.append((x,y))
    def score(p):
        x,y=p;cx=max(0,min(w-15,x-7));cy=max(0,min(h-10,y-5))
        view=[names[xx,yy] for yy in range(cy,cy+10) for xx in range(cx,cx+15)]
        diverse=len(set(view));features=sum(n.startswith(('bridge','ledge','waterfall','mouth','fir_','birch_','sicktree','btree','gtree','crack','web','chest')) for n in view)
        # Prefer views with enough open floor to understand the composition.
        walls=sum(n.startswith(('canopy','forest_canopy','blight_wall')) for n in view)
        return diverse*3+min(features,20)*2-max(0,walls-70)
    if walk:
        x,y=max(walk,key=score);CP.teleport(c,x*16+8,y*16+12);settle_view(c)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('out');ap.add_argument('--seed',default='0xB4A7');ap.add_argument('--tasks-only',action='store_true')
    args=ap.parse_args();seed=int(args.seed,0);out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    c=P.boot(seed=seed);CP.dismiss(c);world=CP.world(c)
    report={'seed':hex(seed),'rom_sha256':hashlib.sha256(Path(P.ROM).read_bytes()).hexdigest(),
            'method':'mGBA native framebuffers with debug room navigation','pacing':pacing(world),
            'world':world,'rooms':[],'tasks':[],'pockets':[]}
    P.snap(c,str(out/'drain-control.png'));P.enter_forest(c)
    for cell,desc in ([] if args.tasks_only else enumerate(world['cells'])):
        CP.heal(c);LP.warp(c,cell,next(i for i,g in enumerate(desc['gate']) if g));CP.heal(c)
        focus(c)
        if desc['role']==2:
            CP.teleport(c,16*16,12*16+48);settle_view(c)
        name='room-%02d-stage%d.png'%(cell,desc['stage']);P.snap(c,str(out/name))
        spot=P.sym('gSpots');pocket=bool(P.r8(c,spot+53))
        report['rooms'].append({'cell':cell,'stage':desc['stage'],'role':desc['role'],'image':name, 'optional_pocket':pocket})
        if pocket:
            kind=P.r8(c,spot+57)
            if kind not in [p['kind'] for p in report['pockets']]:
                gx,gy=P.r8(c,spot+55),P.r8(c,spot+56)
                hx,hy=P.r8(c,spot+44),P.r8(c,spot+45)
                dx=(hx>gx)-(hx<gx);dy=(hy>gy)-(hy<gy)
                CP.teleport(c,(gx-dx)*16+8,(gy-dy)*16+12);settle_view(c)
                name='pocket-%s.png'%('none','bomb','candle','cape')[kind]
                P.snap(c,str(out/name))
                report['pockets'].append({'kind':kind,'cell':cell,'gate':[gx,gy],'hoard':[hx,hy],'image':name})
        print('Captured',cell,desc['stage'],name,flush=True)
    W=P.sym('gWorld')
    for idx,cell in enumerate(world['key_cell']):
        c=P.boot(seed=seed);CP.dismiss(c);P.enter_forest(c)
        m=P.r8(c,P.sym('gWorld')+MP.MYST_OFF+cell)
        kind,size,style=MP.KINDS[m&15],(m>>4)&3,(m>>6)&3
        assert MP.enter(c,cell,kind,size,style),('required task mouth',cell)
        CP.heal(c);R=P.sym('gRoom');CP.teleport(c,P.r8(c,R)*8,P.r8(c,R+1)*8+24);settle_view(c);name='required-task-%d.png'%(idx+1);P.snap(c,str(out/name))
        report['tasks'].append({'reward':('Blightseeds','Candle','Petal Cape')[idx],'cell':cell,'kind':kind,'style':style,'image':name})
    if args.tasks_only and (out/'generation.json').exists():
        old=json.loads((out/'generation.json').read_text())
        assert old['rom_sha256']==report['rom_sha256'], 'rerun full capture for the new ROM'
        old['tasks']=report['tasks'];report=old
    (out/'generation.json').write_text(json.dumps(report,indent=2))
    (out/'maze.svg').write_text(maze_svg(report))
    print(json.dumps(report['pacing'],indent=2))


if __name__=='__main__':main()

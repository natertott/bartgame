"""Capture matched generated forest views from the actual ROM in mGBA.

python tools/blight_review.py OUT [--rom ROM --map MAP --assets-header HEADER]
python tools/blight_review.py AFTER --match BEFORE/capture.json

Debug navigation, healing and cleared enemies/fireflies isolate the artwork. After the
camera settles, a clock fixture restarts terrain animation then runs 64 real
frames so matched controls have identical timing. Terrain, objects and
animation remain game-rendered. Native PNGs are unmodified
240x160 framebuffers; GIFs sample every other video frame at 30fps and enlarge
2x without smoothing. Matching reuses the first run's exact standing points.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from PIL import Image
import probe as P
import critical_path as C
import lift_probe as L

FEATURES = {
    'blighted-tree': ('btree_', 'sicktree_'),
    'ruined-wall': ('blight_wall',),
    'glowing-pool': ('blight_pool',),
    'crystals': ('blight_crystal',),
    'mixed-blight': ('rot_',),
}
DEEP_FEATURES = {
    'deep-wall': ('blight_wall',),
    'deep-pool': ('blight_pool',),
    'deep-tree': ('forest_blight_tree',),
}


def memory(c, at, size):
    return bytes(P.r8(c, at+i) for i in range(size))


def definitions(header):
    values={k:int(v,0) for k,v in re.findall(r'^#define\s+(MT_\w+)\s+(0x[0-9a-fA-F]+|\d+)\b',Path(header).read_text(),re.M)}
    return {v:k[3:].lower() for k,v in values.items()}


def grid(c, names):
    room=P.sym('gRoom');typ=P.sym('metatile_type')
    w,h=P.r8(c,room),P.r8(c,room+1)
    result={};walk=[]
    for y in range(h):
        for x in range(w):
            mt=P.r16(c,room+2+(y*32+x)*2)&65535
            ov=P.r16(c,room+2050+(y*32+x)*2)&65535
            result[x,y]=(names.get(mt,'unknown'),names.get(ov,'none'))
            if 3<=x<w-3 and 4<=y<h-3 and P.r8(c,typ+mt)==0 and ov==65535:
                walk.append((x,y))
    return w,h,result,walk


def focus(c, names, feature=None):
    w,h,tiles,walk=grid(c,names)
    targets=[p for p,n in tiles.items() if feature and any(v.startswith(FEATURES[feature]) for v in n)]
    if feature=='blighted-tree':
        bases=[p for p,n in tiles.items() if any(v.startswith(FEATURES[feature]) and v.endswith(('_4','_5')) for v in n)]
        targets=bases or targets
    def score(p):
        x,y=p;cx=max(0,min(w-15,x-7));cy=max(0,min(h-10,y-5))
        visible=[tiles[xx,yy] for yy in range(cy,cy+10) for xx in range(cx,cx+15)]
        flat=[n for pair in visible for n in pair if n!='none']
        diversity=len(set(flat))
        interesting=sum(n.startswith(('btree_','sicktree_','blight_wall','blight_pool','blight_crystal','rot_','bridge','chest')) for n in flat)
        walls=sum(n.startswith(('canopy','forest_canopy','blight_wall')) for n in flat)
        base=diversity*3+min(interesting,30)*2-max(0,walls-65)
        if targets:
            # Frame a feature above/near the hero, avoiding a wall-only view.
            below=1 if feature=='blighted-tree' else 2
            distance=min(abs(x-tx)*1.2+abs(y-(ty+below)) for tx,ty in targets)
            count=sum(any(n.startswith(FEATURES[feature]) for n in pair) for pair in visible)
            base+=min(count,12)*15-distance*(40 if feature=='blighted-tree' else 4)
        return base
    if not walk:raise AssertionError('no natural safe camera target')
    x,y=max(walk,key=score)
    return [x*16+8,y*16+12]


def deep_focus(c, names, feature):
    """Frame actual targets above Bloom, clear of the HUD and screen edge.

    These additional views never replace the frozen comparison standing
    points. Score the actual camera offset (Bloom is 104px below its top),
    not an approximate tile-centred crop. A complete wall-tree must fit.
    """
    w,h,tiles,walk=grid(c,names)
    prefixes=DEEP_FEATURES[feature]
    targets=[p for p,ns in tiles.items() if any(n.startswith(prefixes) for n in ns)]
    if feature=='deep-tree':
        targets=[p for p,ns in tiles.items() if 'forest_blight_tree4' in ns]
    if not targets or not walk:return None
    def score(p):
        x,y=p;cx=max(0,min(w*16-240,x*16+8-120));cy=max(0,min(h*16-160,y*16+12-104))
        visible=[]
        for tx,ty in targets:
            sx,sy=tx*16-cx,ty*16-cy
            if feature=='deep-tree':
                if 8<=sx<=200 and 64<=sy<=128:visible.append((sx+16,sy-8))
            elif 8<=sx<=216 and 32<=sy<=128:visible.append((sx+8,sy+8))
        if not visible:return (-1000000,0)
        # Keep the focal material near the middle of the playable picture;
        # prefer contiguous wall/pool clusters to a distant corner sliver.
        distance=min(abs(sx-120)+abs(sy-72) for sx,sy in visible)
        central=sum(48<=sx<=192 and 40<=sy<=112 for sx,sy in visible)
        value=1000+min(central,12)*35+min(len(visible),20)*8-distance*5
        return value,len(visible)
    position=max(walk,key=lambda p:score(p)[0]);value,count=score(position)
    if value<0:return None
    return {'position':[position[0]*16+8,position[1]*16+12],
            'focus_score':value,'visible_feature_tiles':count}


def settle(c, position):
    C.clear_enemies(c);C.teleport(c,*position)
    for _ in range(96):
        C.heal(c);C.clear_enemies(c);c.run_frame()
    # The old terrain cycles have a 10,080-frame LCM. Pin the animation
    # clock after generation/navigation, then let all normal uploads run.
    # This does not alter terrain, actor poses, RNG state, or framebuffer.
    clock=P.sym('gFrame');P.w16(c,clock,0);P.w16(c,clock+2,0)
    P.w8(c,P.sym('gActors')+28,0)
    # Firefly positions integrate their drift before the animation-clock
    # reset, so varying room-load duration can move their pixels by one.
    # Remove only these incidental actors in both comparison builds; the
    # terrain's real sparkle/mist animation and other objects stay intact.
    actors=P.sym('gActors')
    for i in range(1,96):
        at=actors+i*64
        if P.r8(c,at)==7 and P.r8(c,at+1)==6:  # AK_FX / FX_FIREFLY
            P.w8(c,at,0)
    for _ in range(64):
        C.heal(c);C.clear_enemies(c);c.run_frame()


def contract(c):
    room=P.sym('gRoom');typ=P.sym('metatile_type');coll=P.sym('metatile_coll')
    values=[]
    for layer in (0,1):
        for y in range(P.r8(c,room+1)):
            for x in range(P.r8(c,room)):
                mt=P.r16(c,room+2+layer*2048+(y*32+x)*2)&65535
                if mt==65535:values.extend((0,0))
                else:
                    t,m=P.r8(c,typ+mt),P.r8(c,coll+mt)
                    values.extend((t,m) if layer==0 or t else (0,0))
    return {'logical_sha256':hashlib.sha256(bytes(values)).hexdigest(),
            'solid_sha256':hashlib.sha256(memory(c,room+4098,4096)).hexdigest(),
            'spots_sha256':hashlib.sha256(memory(c,P.sym('gSpots'),58)).hexdigest()}


def gif(c,path,frames=96):
    pictures=[];terrain_hashes=set()
    for tick in range(frames):
        C.heal(c);C.clear_enemies(c);c.run_frame()
        if tick%2==0:
            pictures.append(c.bg_video.to_pil().convert('RGB').copy())
            terrain_hashes.add(hashlib.sha256(memory(c,0x06000000,32768)).hexdigest())
    colours=set()
    for picture in pictures:colours.update(picture.getdata())
    if len(colours)<=256:
        palette=Image.new('P',(1,1));values=[v for colour in sorted(colours) for v in colour]
        palette.putpalette(values+[0]*(768-len(values)))
    else:palette=pictures[0].quantize(colors=256,dither=Image.Dither.NONE)
    encoded=[p.quantize(palette=palette,dither=Image.Dither.NONE).resize((480,320),Image.Resampling.NEAREST) for p in pictures]
    durations=[(30,30,40)[i%3] for i in range(len(encoded))]
    encoded[0].save(path,save_all=True,append_images=encoded[1:],duration=durations,loop=0,disposal=1,optimize=True)
    return {'file':path.name,'video_frames':frames,'sample_stride':2,'duration_ms':sum(durations),
            'exact_GIF_palette':len(colours)<=256,'unique_colours':len(colours),
            'different_terrain_VRAM_states':len(terrain_hashes)}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('out');ap.add_argument('--rom',default=P.ROM);ap.add_argument('--map',default=P.MAP)
    ap.add_argument('--assets-header',default=str(Path(P.ROOT)/'build/gen/assets.h'))
    ap.add_argument('--seed',default='0xB4A7');ap.add_argument('--match');ap.add_argument('--no-gifs',action='store_true')
    ap.add_argument('--deep-features',action='store_true',help='Append new, separately labelled deep-material views without changing matched standing points')
    args=ap.parse_args();P.MAP=args.map;P._syms=None
    names=definitions(args.assets_header);out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    old=json.loads(Path(args.match).read_text()) if args.match else None
    seed=int(old['seed'],0) if old else int(args.seed,0)
    c=P.boot(rom=args.rom,seed=seed);C.dismiss(c)
    settle(c,[200,270]);P.snap(c,str(out/'drain-control.png'))
    report={'seed':hex(seed),'rom_sha256':hashlib.sha256(Path(args.rom).read_bytes()).hexdigest(),
            'fixture_version':2,
            'emulator':'mGBA 0.10.5','method':'Native240x160 framebuffers; generated terrain and animation untouched. Debug room navigation, safe standing positions, healing and cleared enemies/ambient firefly actors isolate art. Animation-clock fixture resetsgFrame0 after camera settles, then runs64 actual frames. GIFs use real frames, sampled30fps/enlarged2xNN.',
            'drain_image':'drain-control.png','rooms':[],'features':[],'animations':[]}
    world=C.world(c);P.enter_forest(c)
    for cell,desc in enumerate(world['cells']):
        L.warp(c,cell,next(i for i,g in enumerate(desc['gate']) if g))
        C.clear_enemies(c)
        previous=next((r for r in old['rooms'] if r['cell']==cell),None) if old else None
        position=previous['position'] if previous else focus(c,names)
        if desc['role']==2 and not previous:position=[256,240]
        settle(c,position);filename=f'room-{cell:02d}-stage{desc["stage"]}.png';P.snap(c,str(out/filename))
        room={'cell':cell,'stage':desc['stage'],'role':desc['role'],'position':position,
              'camera':[P.r16(c,P.sym('gCamX')),P.r16(c,P.sym('gCamY'))],
              'image':filename,**contract(c)}
        report['rooms'].append(room)
        print('CAPTURE',cell,'stage',desc['stage'],position,flush=True)
    if old:plan=list(old['features'])
    else:
        plan=[]
        for feature in FEATURES:
            candidates=[]
            for cell,desc in enumerate(world['cells']):
                minimum_stage=2 if feature=='blighted-tree' else 3
                if feature!='mixed-blight' and desc['stage']<minimum_stage:continue
                if feature=='mixed-blight' and desc['stage']!=2:continue
                L.warp(c,cell,next(i for i,g in enumerate(desc['gate']) if g));C.clear_enemies(c)
                _,_,tiles,_=grid(c,names)
                count=sum(any(n.startswith(FEATURES[feature]) for n in ns) for ns in tiles.values())
                if count:candidates.append((count,cell,focus(c,names,feature)))
            if candidates:
                _,cell,position=max(candidates)
                plan.append({'feature':feature,'cell':cell,'position':position,'image':feature+'.png'})
    if args.deep_features:
        for feature in DEEP_FEATURES:
            if any(v['feature']==feature for v in plan):continue
            candidates=[]
            for cell,desc in enumerate(world['cells']):
                # Prefer the regular maze for material views; arena-only
                # seeds can still show their real pools or edge trees.
                if desc['stage']<3:continue
                L.warp(c,cell,next(i for i,g in enumerate(desc['gate']) if g));C.clear_enemies(c)
                view=deep_focus(c,names,feature)
                if view:
                    candidates.append((desc['role']!=2,view['focus_score'],cell,view))
            if candidates:
                _,_,cell,view=max(candidates,key=lambda item:item[:3])
                plan.append({'feature':feature,'cell':cell,'image':feature+'.png',
                             'supplemental':True,**view})
    for view in plan:
        cell=view['cell'];desc=world['cells'][cell]
        L.warp(c,cell,next(i for i,g in enumerate(desc['gate']) if g));settle(c,view['position'])
        P.snap(c,str(out/view['image']));report['features'].append(dict(view,**contract(c)))
        if not args.no_gifs and view['feature'] in ('blighted-tree','ruined-wall','glowing-pool',*DEEP_FEATURES):
            report['animations'].append(gif(c,out/(view['feature']+'.gif')))
        print('FEATURE',view['feature'],cell,view['position'],flush=True)
    if old:
        keys=('logical_sha256','solid_sha256','spots_sha256')
        changes=[{'cell':a['cell'],'field':k} for a,b in zip(report['rooms'],old['rooms']) for k in keys if a[k]!=b[k]]
        report['physical_comparison']={'checked_rooms':len(report['rooms']),'unchanged_rooms':len(report['rooms'])-len(set(v['cell'] for v in changes)),'differences':changes}
        assert not changes,changes
        if old.get('fixture_version')==report['fixture_version']:
            report['visual_controls']=[]
            controls=['drain-control.png']+[r['image'] for r in report['rooms'] if r['stage']==0]
            for filename in controls:
                before=Image.open(Path(args.match).parent/filename).convert('RGB')
                after=Image.open(out/filename).convert('RGB')
                different=sum(a!=b for a,b in zip(before.getdata(),after.getdata()))
                report['visual_controls'].append({'file':filename,'identical':different==0,'different_pixels':different})
                print('CONTROL', 'PASS' if different==0 else 'DIFF', filename, different,flush=True)
        else:
            report['visual_controls_omitted']='Prior fixture left ambient fireflies alive; standing points and physical hashes reused, image controls require matching fixture versions.'
    (out/'capture.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS:',len(report['rooms']),'generated rooms,',len(report['features']),'feature views',flush=True)


if __name__=='__main__':main()

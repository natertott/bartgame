"""Capture genuine Bloom actions from a running ROM in mGBA.

python tools/bloom_review.py OUT [--rom ROM --map MAP --assets-header HEADER]

The forest is generated normally. Only actors, inventory, position and facing
are fixtures; no pose or animation frame is assigned. Actions run from button
input on natural traversable ground. PNGs are native 240x160 framebuffers.
GIFs use nearest-neighbour 2x frames, sampled at 30fps with GIF delay rounding.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image
import probe as P
import critical_path as C
import lift_probe as L
import bloom_probe as B

DIRECTION_KEYS=('UP','RIGHT','DOWN','LEFT')


def natural_spot(c,facing=0,travel=0):
    room=P.sym('gRoom');w=P.r8(c,room);h=P.r8(c,room+1)
    grid={(x,y):P.r16(c,room+2+(y*32+x)*2)&65535 for y in range(h) for x in range(w)}
    overlay={(x,y):P.r16(c,room+2050+(y*32+x)*2)&65535 for y in range(h) for x in range(w)}
    solid=bytes(P.r8(c,room+4098+i) for i in range(4096));types=P.sym('metatile_type')
    kinds={mt:P.r8(c,types+mt) for mt in set(grid.values()) if mt!=65535}
    dx,dy=((0,-1),(1,0),(0,1),(-1,0))[facing]
    candidates=[]
    for ty in range(5,h-4):
        for tx in range(5,w-4):
            x,y=tx*16+8,ty*16+14
            clear=True
            for step in range(0,travel+1,4):
                hx,hy=x+dx*step,y+dy*step
                for yy in (hy-12,hy-6,hy-1):
                    for xx in (hx-6,hx,hx+5):
                        if not 0<=xx<w*16 or not 0<=yy<h*16 or solid[(yy>>3)*64+(xx>>3)] or kinds.get(grid.get((xx>>4,yy>>4))) not in (0,12,15):
                            clear=False;break
                    if not clear:break
                if not clear:break
            if not clear:continue
            penalty=0
            for cy in range(ty-3,ty+3):
                for cx in range(tx-2,tx+3):
                    if kinds.get(grid.get((cx,cy))) not in (0,12,15):penalty+=40
                    if overlay.get((cx,cy),65535)!=65535:penalty+=15
            score=penalty+abs(x-w*8)/8+abs(y-h*8)/8
            candidates.append((score,x,y))
    return min(candidates)[1:] if candidates else None


def make_gif(frames,path):
    # A common exact palette avoids colour drift and dither whenever the GBA
    # scene fits in GIF's 256 colours. Fall back to normal GIF quantization.
    samples=frames[::2]
    colours=set()
    for im in samples:colours.update(colour for _,colour in im.getcolors(im.width*im.height))
    converted=[]
    if len(colours)<=256:
        pal=Image.new('P',(1,1));rgb=[n for colour in sorted(colours) for n in colour]
        pal.putpalette(rgb+[0]*(768-len(rgb)))
        converted=[im.quantize(palette=pal,dither=Image.Dither.NONE) for im in samples]
    else:
        converted=[im.quantize(colors=256,dither=Image.Dither.NONE) for im in samples]
    converted=[im.resize((480,320),Image.Resampling.NEAREST) for im in converted]
    durations=[(30,30,40)[i%3] for i in range(len(converted))]
    converted[0].save(path,save_all=True,append_images=converted[1:],duration=durations,
                      loop=0,disposal=2,optimize=False)
    return {'frames':len(samples),'colour_count':len(colours),'exact_palette':len(colours)<=256,
            'duration_ms':sum(durations)}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('out');ap.add_argument('--rom',default=P.ROM);ap.add_argument('--map',default=P.MAP)
    ap.add_argument('--assets-header',default=str(Path(P.ROOT)/'build/gen/assets.h'))
    ap.add_argument('--seed',default='0xB4A7');ap.add_argument('--quick',action='store_true',help='only swords and rolls')
    args=ap.parse_args();defs=B.configure(args);seed=int(args.seed,0)
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    c=B.boot(args.rom,seed);world=C.world(c);cell=world['entry']
    captures=[]

    def location(facing,travel):
        nonlocal cell
        spot=natural_spot(c,facing,travel)
        if spot:return spot
        for index,d in enumerate(world['cells']):
            L.warp(c,index,next(s for s,g in enumerate(d['gate']) if g));B.clear_actors(c)
            spot=natural_spot(c,facing,travel)
            if spot:cell=index;return spot
        raise AssertionError('no natural ground for action direction '+str(facing))

    def capture(name,facing,eq,keys,total=40,held=1,travel=0,custom=None,spot=None):
        spot=spot or location(facing,travel)
        B.reset_player(c,*spot,facing=facing,equipment=(0,eq,0));P.run(c,96)
        P.w8(c,P.sym('gActors')+28,0)
        frames=[];trace=[];selected=[];directory=out/name;directory.mkdir(exist_ok=True)
        c.set_keys(*(P.key(c,k) for k in keys))
        for tick in range(total):
            if tick==held:c.clear_keys(*(P.key(c,k) for k in keys))
            if custom:custom(tick)
            c.run_frame()
            image=c.bg_video.to_pil().convert('RGB').copy();frames.append(image)
            trace.append(B.live(c))
            if tick in (0,3,6,9,12,18,24,total-1):
                filename=f'frame-{tick:03d}.png';image.save(directory/filename);selected.append(filename)
        c.clear_keys(*range(10))
        gif=make_gif(frames,out/(name+'.gif'))
        captures.append({'name':name,'cell':cell,'position':list(spot),'facing':B.FACES[facing],
                         'input':keys,'held_frames':held,'game_frames':total,'gif':gif,'native_frames':selected,'trace':trace})
        print('CAPTURE',name,'cell',cell,'at',spot,flush=True)

    for f,d in enumerate(B.FACES):capture('sword-'+d,f,1,['B'],32)
    for f,d in enumerate(B.FACES):capture('roll-'+d,f,1,[DIRECTION_KEYS[f],'R'],40,travel=60)
    if not args.quick:
        for action,eq,total in (('bow',6,36),('lamp',3,40),('bomb',2,48),('cape',4,48),('guard',5,40)):
            for f,d in enumerate(B.FACES):
                capture(action+'-'+d,f,eq,['B'],total,held=24 if action=='guard' else 1,
                        travel=48 if action=='cape' else 0)
        found=L.find_tile(c,'BUSH')
        if not found:
            for index,d in enumerate(world['cells']):
                L.warp(c,index,next(s for s,g in enumerate(d['gate']) if g));B.clear_actors(c)
                found=L.find_tile(c,'BUSH')
                if found:cell=index;break
        if found:
            _,_,tile,key=found;f=DIRECTION_KEYS.index(key);spot=(tile[0]*16+8,tile[1]*16+14)
            def throw(tick):
                if tick==22:c.set_keys(P.key(c,'R'))
                if tick==23:c.clear_keys(P.key(c,'R'))
            capture('lift-throw',f,1,['R'],64,custom=throw,spot=spot)
    report={'rom_sha256':hashlib.sha256(Path(args.rom).read_bytes()).hexdigest(),'seed':hex(seed),
            'emulator':'mGBA 0.10.5','method':'Genuine button actions on natural generated forest ground. Full inventory, cleared actors, debug positioning/facing; no pose or frame assignment. PNGs native240x160; GIFs nearest2x atapproximately30fps.',
            'captures':captures}
    (out/'animations.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS:',len(captures),'real-ROM action clips',flush=True)


if __name__=='__main__':main()

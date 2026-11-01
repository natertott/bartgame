#!/usr/bin/env python3
"""Native tree study from a real profile30 mGBA run.

The scenes are deliberately constructed diagnostic groves, not natural forest
generation. The harness requests an existing ROM function; it never writes
video pixels, tile maps, tree art or action poses. Initial standing position
and facing are declared fixtures before ordinary input and native scanout.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

from PIL import Image, ImageDraw, ImageSequence
import probe as P
import bloom_probe as B
import critical_path as C

LOADED_SHA=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
FLOORS=('grass','path','sick-grass')


def sha(data):return hashlib.sha256(data).hexdigest()
def read(c,at,n):return bytes(P.r8(c,at+i) for i in range(n))
def write32(c,at,v):P.w16(c,at,v&65535);P.w16(c,at+2,v>>16)
def words(c,at,n):return list(struct.unpack('<%dH'%n,read(c,at,n*2)))


def component(points):
    left=set(points);best=0
    while left:
        todo=[left.pop()];size=0
        while todo:
            x,y=todo.pop();size+=1
            for near in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if near in left:left.remove(near);todo.append(near)
        best=max(best,size)
    return best


def sampled_gif(frames,path,hold=130):
    """Preserve exact sampled RGB and total holds, including idle duplicates."""
    merged=[];durations=[]
    for frame in frames:
        if merged and frame.tobytes()==merged[-1].tobytes():durations[-1]+=hold
        else:merged.append(frame);durations.append(hold)
    colors=sorted({color for frame in merged for _,color in frame.getcolors(frame.width*frame.height)})
    assert len(colors)<=256
    mapping={color:i for i,color in enumerate(colors)};table=[v for color in colors for v in color]
    indexed=[]
    for frame in merged:
        im=Image.new('P',frame.size);im.putpalette(table+[0]*(768-len(table)))
        data=frame.tobytes();im.putdata([mapping[c] for c in zip(data[::3],data[1::3],data[2::3])]);indexed.append(im)
    indexed[0].save(path,save_all=True,append_images=indexed[1:],duration=durations,loop=0,optimize=False,disposal=2)
    with Image.open(path) as check:decoded=[(f.convert('RGB').copy(),f.info['duration']) for f in ImageSequence.Iterator(check)]
    assert len(decoded)==len(merged)
    assert all(a.tobytes()==b.tobytes() and ms==hold_ms for (a,ms),b,hold_ms in zip(decoded,merged,durations))
    return {'sampled_frames':len(frames),'encoded_frames':len(decoded),'sample_hold_ms':hold,
            'encoded_holds_ms':durations,'exact_rgb_roundtrip':True,'engine_timing_claim':False}


class Review:
    def __init__(self,args):
        self.args=args;self.out=Path(args.out);self.out.mkdir(parents=True,exist_ok=True)
        if args.bundle:
            base=Path(args.bundle);self.rom=base/'bartgame.gba';self.map=base/'bartgame.map'
            self.header=base/'assets.h';self.freeze=json.loads((base/'freeze.json').read_text())
        else:
            self.rom=Path(args.rom);self.map=Path(args.map);self.header=Path(args.assets)
            self.freeze={'source_commit':None,'unfrozen_pilot':True}
        self.defs=B.definitions(self.header);assert self.defs['BART_FOREST_VARIANT']==30
        P.MAP=str(self.map);P._syms=None
        self.checks=[];self.rows=[];self.c=None;self.pending=None;self.completed=None
        self.immutable={str(p):sha(p.read_bytes()) for p in (self.rom,self.map,self.header)}

    def check(self,name,ok,detail=None):
        self.checks.append({'name':name,'passed':bool(ok),**({'detail':detail} if detail is not None else {})})

    def invoke(self):
        hook=P.sym('gVBlankHook');original=P.r32(self.c,hook);clock=P.r32(self.c,P.sym('gFrame'))
        try:
            write32(self.c,hook,P.sym('tree_study_begin')|1)
            for _ in range(180):
                P.run(self.c,1)
                if ((P.r32(self.c,P.sym('gFrame'))-clock)&0xffffffff)>=2:break
            else:raise RuntimeError('Tree-study ROM callback did not finish')
        finally:write32(self.c,hook,original)
        start=P.r32(self.c,P.sym('gGame')+8)
        for _ in range(180):
            P.run(self.c,1)
            if ((P.r32(self.c,P.sym('gGame')+8)-start)&0xffffffff)>=3:break
        else:raise RuntimeError('Tree-study callback did not return to ordinary game updates')

    def boot(self,request):
        self.c=P.boot(rom=str(self.rom),seed=0xB4A7)
        C.dismiss(self.c)
        P.w16(self.c,P.sym('gTreeStudyRequest'),request)
        P.w8(self.c,P.sym('gTreeStudyPending'),1)
        self.invoke();P.run(self.c,24)
        self.pending=self.completed=None
        self.c._callbacks.video_frame_started.append(self.scanout_start)
        self.c.add_frame_callback(self.scanout_end)

    def map_entry(self,base,x8,y8):
        block=base+(y8>>5)*2+(x8>>5)
        return P.r16(self.c,0x06000000+block*2048+((y8&31)*32+(x8&31))*2)&65535

    def bg_ink(self,base,x,y):
        entry=self.map_entry(base,x//8,y//8);xx,yy=x&7,y&7
        if entry&0x400:xx=7-xx
        if entry&0x800:yy=7-yy
        value=P.r8(self.c,0x06000000+(entry&1023)*32+yy*4+xx//2)
        return (value>>((xx&1)*4))&15,entry>>12

    def body_model(self):
        c=self.c;hero=B.hero_oam(c)
        if hero is None:return {'body_found':False,'expected':[]}
        metadata=B.sheet_metadata(c,0);w,h=metadata['width'],metadata['height']
        source=read(c,0x06010000,w*h//2);colors=words(c,0x05000200+hero['pal']*32,16)
        telemetry=words(c,P.sym('gForestV3Visibility'),12)
        guard=next((o for o in B.oam(c) if o['tile']==telemetry[2]),None) if telemetry[0] else None
        mask=read(c,0x06010000+guard['tile']*32,w*h//2) if guard else None
        exact=not guard or all(guard[k]==hero[k] for k in ('x','y','pal','shape','size','flip')) and guard['priority']==1
        def ink(data,x,y):
            at=((y//8)*(w//8)+x//8)*32+(y&7)*4+(x&7)//2
            return (data[at]>>((x&1)*4))&15
        expected=[];covered=0
        for y in range(h):
            for x in range(w):
                sx=w-1-x if hero['flip'] else x;i=ink(source,sx,y)
                if mask and ink(mask,sx,y):exact &= ink(mask,sx,y)==i
                if not i:continue
                px,py=hero['x']+x,hero['y']+y
                if not(0<=px<240 and 12<=py<160):continue
                bg,_=self.bg_ink(24,px,py)
                obscured=hero['priority']>1 and bg!=0
                if obscured:covered+=1
                if obscured and not(mask and exact and ink(mask,sx,y)==i):continue
                color=colors[i];parts=(color&31,(color>>5)&31,(color>>10)&31)
                if max(parts)<5 or sum(parts)<10:continue
                expected.append((x,y,px,py,*((v<<3)|(v>>2) for v in parts)))
        return {'body_found':True,'priority':hero['priority'],'guard_exact_native_subset':bool(exact),
                'guard_active':bool(guard),'body_pixels_behind_tree':covered,'body_vram_sha256':sha(source),
                'hero_OAM':hero,'body_canvas':[w,h],'body_vram_hex':source.hex(),'body_palette':colors,
                'guard_OAM':guard,'guard_vram_hex':mask.hex() if mask else None,
                'BG1_control':P.r16(c,0x0400000a)&65535,
                'expected':expected}

    def scanout_start(self):
        model=self.body_model();model['scanline0']=P.r16(self.c,0x04000006)
        model['video_frame']=self.c.frame_counter;self.pending=model

    def scanout_end(self):
        if self.pending is None:return
        model=self.pending;self.pending=None;image=self.c.bg_video.to_pil().convert('RGB')
        matches=[(x,y) for x,y,px,py,r,g,b in model.pop('expected') if image.getpixel((px,py))==(r,g,b)]
        model.update(exact_visible_pixels=len(matches),largest_visible_component=component(matches),
                     scanline160=P.r16(self.c,0x04000006),end_video_frame=self.c.frame_counter)
        self.completed=model

    def hardware(self):
        c=self.c;info=words(c,P.sym('gTreeStudyInfo'),16);placements=[]
        for n in range(info[4]):
            v=list(read(c,P.sym('gTreeStudyPlacements')+n*10,10))
            placements.append(dict(zip(('frame','x','y','w','h','root_x8','root_y8','root_w8','root_h8','anchor_y'),v)))
        frames=[]
        for n in range(self.defs['TREE_STUDY_COUNT']):
            at=P.sym('tree_study_frames')+n*12;pointer=P.r32(c,at)
            w,h,size,variety,state=read(c,at+4,5)
            frames.append({'map':words(c,pointer,w*h),'w8':w,'h8':h,'size':size,'variety':variety,'state':state})
        expected_bg1=[0]*600;roots=set()
        for p in placements:
            f=frames[p['frame']]
            for y in range(f['h8']):
                for x in range(f['w8']):expected_bg1[(p['y']//8+y)*30+p['x']//8+x]=f['map'][y*f['w8']+x]
            roots.update((p['root_x8']+x,p['root_y8']+y) for y in range(p['root_h8']) for x in range(p['root_w8']))
        floor=words(c,P.sym('tree_study_floor')+info[3]*8,4)
        expected_bg2=[floor[(y&1)*2+(x&1)] for y in range(20) for x in range(30)]
        actual_bg1=[self.map_entry(24,x,y) for y in range(20) for x in range(30)]
        actual_bg2=[self.map_entry(28,x,y) for y in range(20) for x in range(30)]
        actual_roots={(x,y) for y in range(20) for x in range(30) if P.r8(c,P.sym('gRoom')+4098+y*64+x)}
        palette=words(c,0x05000000+self.defs['TREE_STUDY_PALETTE_SLOT']*32,16)
        return {'info':info,'placements':placements,'frames':frames,'BG1_entries':actual_bg1,'BG2_entries':actual_bg2,
                'expected_BG1_entries':expected_bg1,'expected_BG2_entries':expected_bg2,
                'actual_roots8':[list(p) for p in sorted(actual_roots)],'expected_roots8':[list(p) for p in sorted(roots)],
                'tree_palette':palette,'expected_tree_palette':words(c,P.sym('tree_study_palette'),16),
                'room_pixels':[P.r8(c,P.sym('gRoom'))*16,P.r8(c,P.sym('gRoom')+1)*16],
                'gAnimTiles':P.r8(c,P.sym('gAnimTiles')),'atlas_VRAM_sha256':sha(read(c,0x06000000,info[5]*32)),
                'camera':words(c,P.sym('gForestV2DisplayedCamera'),2),
                'display_control':P.r16(c,0x04000000)&65535,
                'expected_atlas_sha256':sha(read(c,P.sym('tree_study_tiles'),info[5]*32))}

    def record(self,name,request,motion=None):
        self.boot(request)
        if motion:
            point=(96,40) if motion=='broad' else (96,96)
            C.teleport(self.c,*point);P.w8(self.c,P.sym('gActors')+7,1);P.run(self.c,120)
        initial=self.hardware();count=128 if motion else 16;images=[];observations=[];states=[]
        events={8:[('RIGHT',True)],24:[('RIGHT',False),('DOWN',True)],40:[('DOWN',False),('LEFT',True)],
                56:[('LEFT',False)],72:[('UP',True)],88:[('UP',False)]} if motion else {}
        previous_irq=P.r32(self.c,P.sym('gFrame'));previous_update=P.r32(self.c,P.sym('gGame')+8)
        for tick in range(count):
            for key,down in events.get(tick,[]):
                if down:self.c.add_keys(P.key(self.c,key))
                else:self.c.clear_keys(P.key(self.c,key))
            P.run(self.c,1);image=self.c.bg_video.to_pil().convert('RGB');images.append(image.copy())
            irq=P.r32(self.c,P.sym('gFrame'));updates=P.r32(self.c,P.sym('gGame')+8)
            observations.append({**(self.completed or {}),'irq_delta':(irq-previous_irq)&0xffffffff,
                                 'update_delta':(updates-previous_update)&0xffffffff})
            previous_irq=irq;previous_update=updates
            states.append({'tick':tick,'position':list(P.player_pos(self.c)),
                           'priority':P.r8(self.c,P.sym('gActors')+40),
                           'collision':P.r8(self.c,P.sym('gActors')+35)})
        final=self.hardware();self.check(name+' native frame count and scene ABI',initial['info'][0]==1 and initial['info'][11]==12 and initial['info'][4]==12)
        for key in ('BG1_entries','BG2_entries','tree_palette'):
            self.check(name+' exact '+key,initial[key]==initial['expected_'+key] and final[key]==final['expected_'+key])
        self.check(name+' exact declared root footprints',initial['actual_roots8']==initial['expected_roots8']==final['actual_roots8'])
        self.check(name+' compact native atlas stays unchanged in VRAM',initial['atlas_VRAM_sha256']==initial['expected_atlas_sha256']==final['atlas_VRAM_sha256'])
        self.check(name+' exact native world palette not overwritten',initial['gAnimTiles']==final['gAnimTiles']==0)
        self.check(name+' real world planes and native zero-scroll camera',initial['camera']==final['camera']==[0,0] and initial['display_control']&0x0600==0x0600)
        self.check(name+' actual player never fully hidden',all(o.get('body_found') and o.get('exact_visible_pixels',0)>0 and o.get('largest_visible_component',0)>=4 for o in observations))
        self.check(name+' exact current body guard',all(o.get('guard_exact_native_subset') for o in observations))
        self.check(name+' paired native scanout',all(o.get('scanline0')==0 and o.get('scanline160')==160 and o.get('video_frame')==o.get('end_video_frame') for o in observations))
        self.check(name+' one update per recorded VBlank',all(o['irq_delta']==o['update_delta']==1 for o in observations))
        if motion:
            self.check(name+' behind and front priorities both exercised',{o.get('priority') for o in observations}>={1,2})
            self.check(name+' ordinary input visits both sides of ground anchor',min(p['position'][1] for p in states)<(54 if motion=='broad' else 110)<max(p['position'][1] for p in states))
            self.check(name+' root blocks the final ordinary upward push',any(p['collision']&1 for p in states[72:]))
        path=self.out/name;path.mkdir(exist_ok=True)
        selected=sorted({0,count//4,count//2,count*3//4,count-1})
        native=[]
        for tick in selected:
            target=path/f'frame-{tick:03}.png';images[tick].save(target)
            native.append({'tick':tick,'path':str(target.relative_to(self.out)),'sha256':sha(target.read_bytes())})
        images[0].save(self.out/(name+'.png'))
        strip=Image.new('RGB',(240*len(selected),180),'#101820');draw=ImageDraw.Draw(strip)
        for n,tick in enumerate(selected):draw.text((240*n+4,2),name+f' / frame{tick}',fill='#e8d098');strip.paste(images[tick],(240*n,20))
        strip.save(self.out/(name+'-filmstrip.png'))
        row={'name':name,'fixture':'Deliberate in-ROM diagnostic tree grove; not natural generation.',
             'request':request,'floor':FLOORS[request%3],'layout':'repeated grove' if request>=3 else 'all twelve native trees',
             'frames':count,'image':name+'.png','filmstrip':name+'-filmstrip.png','native_frames':native,
             'initial_hardware':initial,'final_hardware_sha256':sha(json.dumps(final,sort_keys=True).encode()),
             'observations':observations,'player_states':states}
        if motion:
            filename=name+'.mp4';cmd=['ffmpeg','-loglevel','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size','240x160','-framerate','262144/4389','-i','-','-an','-c:v','libx264','-pix_fmt','yuv420p',str(self.out/filename)]
            process=subprocess.Popen(cmd,stdin=subprocess.PIPE)
            for image in images:process.stdin.write(image.tobytes())
            process.stdin.close();assert process.wait()==0
            row['video']=filename;row['gif']=name+'.gif'
            sampled=[images[t] for t in range(0,count,8)];row['gif_metadata']=sampled_gif(sampled,self.out/row['gif'])
            row['gif_metadata']['note']='Exact sampled colors; every eighth video frame held130ms for inspection, not full frame-rate playback.'
        self.rows.append(row)

    def run(self):
        for request in range(6):self.record(('tree-catalog-' if request<3 else 'repeated-grove-')+FLOORS[request%3],request)
        self.record('broad-tree-walk-around',0,'broad');self.record('narrow-tree-walk-around',2,'narrow')
        self.check('ROM/map/header stayed immutable',all(sha(Path(p).read_bytes())==v for p,v in self.immutable.items()))
        self.check('capture tool stayed immutable',sha(Path(__file__).read_bytes())==LOADED_SHA)
        report={'source_commit':self.freeze.get('source_commit'),'unfrozen_pilot':self.freeze.get('unfrozen_pilot',False),
                'schema':1,'complete':True,'forest_variant':30,'rom_sha256':sha(self.rom.read_bytes()),'capture_tool_sha256':LOADED_SHA,
                'method':__doc__.strip(),'captures':self.rows,'checks':self.checks,
                'passed':sum(c['passed'] for c in self.checks),'total':len(self.checks),
                'failures':[c for c in self.checks if not c['passed']],
                'contexts':len(self.rows),'frame_observations':sum(r['frames'] for r in self.rows),
                'minimum_visible_pixels':min(o.get('exact_visible_pixels',0) for r in self.rows for o in r['observations']),
                'minimum_connected_pixels':min(o.get('largest_visible_component',0) for r in self.rows for o in r['observations'])}
        (self.out/'capture.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({k:v for k,v in report.items() if k not in ('captures','checks')}),flush=True)
        return int(bool(report['failures']))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle');p.add_argument('--rom');p.add_argument('--map');p.add_argument('--assets');p.add_argument('--out',required=True)
    return Review(p.parse_args()).run()


if __name__=='__main__':raise SystemExit(main())

#!/usr/bin/env python3
"""Full natural forest rooms from real mGBA camera captures.

The panorama is a registered mosaic of nine unmodified 240x160 GBA video
frames, never a claimed 512x384 GBA screen. A native review-only switch pauses
simulation and suppresses HUD drawing; it changes camera/clock/display only.
No terrain, tile, palette, tree pixels, actor pose or framebuffer is injected.
Ordinary HUD-on stills and input-driven movies are captured separately.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

from PIL import Image
from mgba._pylib import ffi
import probe as P
import bloom_probe as B
import critical_path as C
from sewer_concept_audit import NativeRom
import forest_tree_review as T

LOADED_SHA=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
DEFAULT_ROOMS=(('healthy',0xB4A7,16),('mixed',0xB4A7,0),('deep',0x6,4))
TIMING_BASELINE_SHA='1ef84e4fc5df0cc32c74ce7e46852bc88818a6122006a7410432b64600405ce3'


def sha(data):return hashlib.sha256(data).hexdigest()
def read(c,at,n):return bytes(P.r8(c,at+i) for i in range(n))
def write32(c,at,value):P.w16(c,at,value&65535);P.w16(c,at+2,value>>16)
def words(c,at,n):return list(struct.unpack('<%dH'%n,read(c,at,n*2)))
def save_json(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
def rgb_sha(image):return sha(image.convert('RGB').tobytes())


class Review:
    # Reuse only read-only scanout/body-proof helpers from the immutable tree
    # study. They inspect actual resident character bytes and native BG1/OAM.
    map_entry=T.Review.map_entry
    bg_ink=T.Review.bg_ink
    scanout_end=T.Review.scanout_end

    def __init__(self,args):
        self.args=args;self.base=Path(args.bundle).resolve();self.out=Path(args.out).resolve()
        self.out.mkdir(parents=True,exist_ok=True)
        self.rom=NativeRom(self.base);self.defs=self.rom.defs
        if self.defs['BART_FOREST_VARIANT']!=31:raise ValueError('requires production tree profile31')
        P.MAP=str(self.base/'bartgame.map');P._syms=None
        self.freeze=json.loads((self.base/'freeze.json').read_text()) if (self.base/'freeze.json').exists() else {'unfrozen_pilot':True}
        self.immutable={name:sha((self.base/name).read_bytes()) for name in ('bartgame.gba','bartgame.map','assets.h')}
        self.deps={}
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).resolve()
                if path.parent==Path(__file__).resolve().parent:self.deps[path.name]=sha(path.read_bytes())
        self.rows=[];self.checks=[];self.c=None;self.pending=None;self.completed=None
        self.ts=self.rom.tileset('forest')
        self.timing_baseline=None;self.timing_limits={}
        if args.movies:
            if not args.timing_baseline:raise ValueError('--movies requires --timing-baseline with the pinned historical report')
            original=Path(args.timing_baseline).read_bytes()
            if sha(original)!=TIMING_BASELINE_SHA:raise ValueError('timing baseline is not the pinned read-only comparison report')
            self.timing_baseline=json.loads(original)
            self.timing_limits={r['room']:r['missed_updates'] for r in self.timing_baseline['captures'] if r['build']=='base29'}
            if self.timing_limits!={'healthy':1,'mixed':1,'deep':0}:raise ValueError('unexpected historical timing control')
            (self.out/'timing-baseline.json').write_bytes(original)
        self.rng=B.static_symbol('sRand')
        self.check('native GBA tile budget',0<self.ts['tile_count']<=1024,self.ts['tile_count'])
        self.check('forest atlas does not overlap BG3 screenblocks12..15',self.ts['tile_count']<=768,self.ts['tile_count'])
        self.check('native GBA world palette budget',0<self.ts['palette_count']<=12,self.ts['palette_count'])

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
        expected=[];covered1=covered3=0;scroll=self.ppu_scroll()
        for y in range(h):
            for x in range(w):
                sx=w-1-x if hero['flip'] else x;i=ink(source,sx,y)
                if mask and ink(mask,sx,y):exact &= ink(mask,sx,y)==i
                if not i:continue
                px,py=hero['x']+x,hero['y']+y
                if not(0<=px<240 and 12<=py<160):continue
                bg1,_=self.bg_ink(24,(px+scroll['BG1_scroll'][0])&511,(py+scroll['BG1_scroll'][1])&511)
                bg3,_=self.bg_ink(12,(px+scroll['BG3_scroll'][0])&511,(py+scroll['BG3_scroll'][1])&511)
                hidden1=hero['priority']>1 and bg1!=0
                hidden3=hero['priority']>2 and bg3!=0
                covered1+=hidden1;covered3+=hidden3
                if (hidden1 or hidden3) and not(mask and exact and ink(mask,sx,y)==i):continue
                color=colors[i];parts=(color&31,(color>>5)&31,(color>>10)&31)
                if max(parts)<5 or sum(parts)<10:continue
                expected.append((x,y,px,py,*((v<<3)|(v>>2) for v in parts)))
        return {'body_found':True,'priority':hero['priority'],'guard_exact_native_subset':bool(exact),
                'guard_active':bool(guard),'body_pixels_behind_tree':covered1+covered3,
                'body_pixels_behind_BG1':covered1,'body_pixels_behind_BG3':covered3,
                'body_vram_sha256':sha(source),'guard_telemetry':telemetry,'hero_OAM':hero,'body_canvas':[w,h],
                'body_vram_hex':source.hex(),'body_palette':colors,'guard_OAM':guard,
                'guard_vram_hex':mask.hex() if mask else None,'BG1_control':P.r16(c,0x0400000a)&65535,
                'BG3_control':P.r16(c,0x0400000e)&65535,'expected':expected}

    def ppu_scroll(self):
        # CPU reads of BGHOFS/VOFS are open bus on real GBA. Read mGBA's
        # renderer-write mirror without issuing any register writes instead.
        io=ffi.cast('struct GBA*',self.c._core.board).memory.io
        return {f'BG{bg}_scroll':[int(io[(0x10+bg*4)//2])&511,int(io[(0x12+bg*4)//2])&511]
                for bg in (1,2,3)}

    def scanout_start(self):
        T.Review.scanout_start(self)
        if self.pending is not None:self.pending['PPU_scroll_at_scanline0']=self.ppu_scroll()

    def check(self,name,ok,detail=None):
        self.checks.append({'name':name,'passed':bool(ok),**({'detail':detail} if detail is not None else {})})
        print(('PASS ' if ok else 'FAIL ')+name,flush=True)

    def static(self,name):return B.static_symbol(name)

    def boot(self,seed,cell):
        self.c=P.boot(rom=str(self.base/'bartgame.gba'),seed=seed);C.dismiss(self.c)
        c=self.c;self.world=C.world(c)
        P.enter_forest(c)
        side=next(i for i,v in enumerate(self.world['cells'][cell]['gate']) if v)
        for name,value in (('sNextArea',1),('sNextCell',cell),('sNextSide',side),('sTransPhase',0)):
            P.w8(c,self.static(name),value)
        P.w8(c,P.sym('gGame'),2)
        for _ in range(1200):
            P.run(c,1)
            if C.gstate(c)==1 and C.area(c)==1 and C.cell(c)==cell:break
        else:raise RuntimeError('forest navigation fixture did not settle')
        C.dismiss(c)
        self.check(f'{hex(seed)} cell{cell} naturally generated selected room',
                   P.r32(c,P.sym('gWorld'))==seed and C.cell(c)==cell)
        self.pending=self.completed=None
        c._callbacks.video_frame_started.append(self.scanout_start)
        c.add_frame_callback(self.scanout_end)

    def clear_enemies(self):
        # An explicit viewing/motion isolation fixture, after natural generation.
        # Leave all NPCs, loot and interaction actors in the room.
        base=P.sym('gActors');removed=[]
        for i in range(1,96):
            at=base+i*64
            if P.r8(self.c,at) in (2,3,7):
                removed.append({'slot':i,'kind':P.r8(self.c,at),'type':P.r8(self.c,at+1)})
                P.w8(self.c,at,0)
        return removed

    def safe(self,px,py):
        c=self.c;at=P.sym('gRoom');w,h=P.r8(c,at),P.r8(c,at+1)
        if not(16<=px<w*16-16 and 32<=py<h*16-16):return False
        for yy in range(py-12,py,4):
            for xx in range(px-6,px+6,4):
                if P.r8(c,at+4098+(yy//8)*64+xx//8):return False
        mt=P.r16(c,at+2+(((py-6)//16)*32+px//16)*2)&65535
        return mt<self.defs['METATILE_COUNT'] and P.r8(c,P.sym('metatile_type')+mt)==self.defs['TT_FLOOR']

    def point(self):
        candidates=[]
        for y in range(64,352,8):
            for x in range(48,472,8):
                if self.safe(x,y):candidates.append((abs(x-256)+abs(y-232),(x,y)))
        if not candidates:raise RuntimeError('no safe natural standing point')
        return min(candidates)[1]

    def settle(self,point):
        C.teleport(self.c,*point);base=P.sym('gActors')
        P.w8(self.c,base+6,16);P.w8(self.c,base+7,2)
        for _ in range(48):self.clear_enemies();C.heal(self.c);P.run(self.c,1)
        self.c.clear_keys(*range(10))

    def physical(self):
        c=self.c;base=P.sym('gRoom');w,h=P.r8(c,base),P.r8(c,base+1)
        out={'dimensions':[w*16,h*16]}
        for name,offset,length in (('ground',2,2048),('overlay',2050,2048),('collision',4098,4096),('underlay',8194,2048)):
            out[name+'_sha256']=sha(read(c,base+offset,length))
        out['world_sha256']=sha(read(c,P.sym('gWorld'),668))
        out['spots_sha256']=sha(read(c,P.sym('gSpots'),58))
        return out

    def snapshot(self):
        c=self.c
        return {'camera':[P.r16(c,P.sym('gCamX')),P.r16(c,P.sym('gCamY'))],
                **self.ppu_scroll(),
                'scroll_read_method':'Read-only mGBA GBA.memory.io renderer-write mirror; CPU BGHOFS/VOFS reads are write-only/open-bus.',
                'BG1_displayed_camera_telemetry':words(c,P.sym('gForestV2DisplayedCamera'),2),
                'DISPCNT':P.r16(c,0x04000000)&65535,'BG1CNT':P.r16(c,0x0400000a)&65535,
                'BG2CNT':P.r16(c,0x0400000c)&65535,'BG3CNT':P.r16(c,0x0400000e)&65535,'gFrame':P.r32(c,P.sym('gFrame')),
                'rng':P.r32(c,self.rng),'player':list(P.player_pos(c)),
                'world_actors':[{'slot':i,'kind':P.r8(c,P.sym('gActors')+i*64),
                                 'type':P.r8(c,P.sym('gActors')+i*64+1),
                                 'x_q16':P.r32(c,P.sym('gActors')+i*64+8),
                                 'y_q16':P.r32(c,P.sym('gActors')+i*64+12),
                                 'z_q16':P.r32(c,P.sym('gActors')+i*64+16)}
                                for i in range(96) if P.r8(c,P.sym('gActors')+i*64)],
                'BG_maps_sha256':sha(read(c,0x06000000+24*2048,8*2048)),
                'BG3_map_sha256':sha(read(c,0x06000000+12*2048,4*2048)),
                'BG_palette_sha256':sha(read(c,0x05000000,512)),
                'BG_tiles_sha256':sha(read(c,0x06000000,self.ts['tile_count']*32)),
                'OAM':B.oam(c),'body_scanout':self.completed}

    def fidelity(self):
        c=self.c;ts=self.ts;actual=read(c,0x06000000,ts['tile_count']*32)
        animated=set();valid=True
        for entry in ts['animations']:
            start=entry['base']*32;animated.update(range(start,start+128))
            valid &= actual[start:start+128] in [entry['data'][i*128:(i+1)*128] for i in range(entry['frames'])]
        static=all(a==b for i,(a,b) in enumerate(zip(actual,ts['tiles'])) if i not in animated)
        expected=bytearray(ts['palettes']);phase=(P.r32(c,P.sym('gFrame'))>>3)&3
        count=self.defs.get('FOREST_V2_PULSE_COUNT',0)
        slots=read(c,P.sym('forest_v2_pulse_slots')+self.defs['TS_FOREST']*count,count) if count else b''
        for i,slot in enumerate(slots):
            if slot!=255:expected[slot*32:(slot+1)*32]=read(c,P.sym('forest_v2_pulse_colors')+(i*4+phase)*32,32)
        colors=read(c,P.sym('gPalBg'),len(expected))
        return {'static_resident_BG_tiles_equal_ROM':static,'animated_tiles_are_authored_ROM_frames':bool(valid),
                'software_palette_matches_authored_phase':colors==bytes(expected),'pulse_phase':phase,
                'resident_BG_sha256':sha(actual),'ROM_BG_sha256':sha(ts['tiles']),
                'expected_palette_sha256':sha(expected),'software_palette_sha256':sha(colors)}

    def tree_data(self):
        """Read production renderer ABI and validate resident lower-half maps."""
        c=self.c;stats=words(c,P.sym('gForestTreeStats'),16);n=stats[1]
        raw=read(c,P.sym('gForestTrees'),n*8)
        frames=[]
        for frame in range(self.defs['FOREST_TREE_FRAME_COUNT']):
            frames.append({'width':P.r8(c,P.sym('forest_tree_width')+frame),
                           'state':P.r8(c,P.sym('forest_tree_state')+frame),
                           'variety':P.r8(c,P.sym('forest_tree_variety')+frame),
                           'anchor':[P.r8(c,P.sym('forest_tree_anchor_x')+frame),P.r8(c,P.sym('forest_tree_anchor_y')+frame)],
                           'entries':words(c,P.sym('forest_tree_entries')+frame*32,16)})
        placements=[];lower_ok=True;root_ok=True
        expected_lower=[0]*4096
        for i,(x,y,frame,flags,m0,m1) in enumerate(struct.iter_unpack('<hh4B',raw)):
            f=frames[frame];width=f['width'];w8=width//8
            row=(y+16)//16;col=x//16
            root_ok &= all(P.r16(c,P.sym('gForestTreeRoots')+(row*32+col+dx)*2)==i+1 for dx in range(width//16))
            for yy in range(2,4):
                sy=y//8+yy
                if not 0<=sy<48:continue
                for xx in range(w8):expected_lower[sy*64+x//8+xx]=f['entries'][yy*w8+xx]
            placements.append({'index':i,'x':x,'y':y,'frame':frame,'flags':flags,
                               'width':width,'height':32,'state':f['state'],'variety':f['variety'],
                               'root_band':[x,y+16,x+width,y+32],'root_masks':[m0,m1]})
        actual_lower=[self.map_entry(12,x,y) for y in range(64) for x in range(64)]
        lower_ok=actual_lower==expected_lower
        return {'count':n,'stats':stats,'stat_names':['version','count','wood_cells','authored_cells','healthy','sick','dead','broad','narrow','stage','overflow','clipped_upper_cells','cached_redraws','reserved','unused','unused'],
                'placements':placements,'frames':frames,'placement_bytes_hex':raw.hex(),'placement_sha256':sha(raw),
                'roots_sha256':sha(read(c,P.sym('gForestTreeRoots'),2048)),
                'root_ownership_matches_placements':bool(root_ok),
                'lower_BG3_exact_source_maps':bool(lower_ok),
                'expected_lower_map_sha256':sha(struct.pack('<4096H',*expected_lower)),
                'actual_lower_map_sha256':sha(struct.pack('<4096H',*actual_lower))}

    def capture_view(self,x,y,clock=256):
        c=self.c
        P.w16(c,P.sym('gForestReviewCamera'),x);P.w16(c,P.sym('gForestReviewCamera')+2,y)
        write32(c,P.sym('gForestReviewClock'),clock)
        P.w8(c,P.sym('gForestReviewEnabled'),1)
        # One world draw prepares OAM/scroll; the next VBlank uploads it. Extra
        # frames settle any native lazy sprite upload, never writing video RAM.
        for _ in range(5):
            write32(c,P.sym('gFrame'),clock-1);P.run(c,1)
        image=c.bg_video.to_pil().convert('RGB').copy();meta=self.snapshot()
        self.check(f'camera {x},{y} native BG scroll',meta['camera']==[x,y] and meta['BG1_scroll']==[x,y] and meta['BG2_scroll']==[x,y] and meta['BG3_scroll']==[x,y])
        self.check(f'camera {x},{y} native HUD suppressed',not(meta['DISPCNT']&0x100))
        scan=meta['body_scanout']
        self.check(f'camera {x},{y} paired scanline0..160 PPU scroll',
                   scan and scan.get('scanline0')==0 and scan.get('scanline160')==160 and
                   scan.get('video_frame')==scan.get('end_video_frame') and
                   all(scan['PPU_scroll_at_scanline0'][f'BG{bg}_scroll']==[x,y] for bg in (1,2,3)))
        return image,meta

    def normal(self):
        P.w8(self.c,P.sym('gForestReviewEnabled'),0)
        P.run(self.c,12)

    def still(self,path):
        im=self.c.bg_video.to_pil().convert('RGB').copy();im.save(path)
        return {'file':str(path.relative_to(self.out)),'size':list(im.size),
                'png_sha256':sha(path.read_bytes()),'RGB_sha256':rgb_sha(im),'hardware':self.snapshot()}

    def panorama(self,name):
        folder=self.out/name;folder.mkdir(exist_ok=True)
        contract=self.physical();trees=self.tree_data();fidelity=self.fidelity()
        self.check(name+' resident static tree/world atlas equals ROM',fidelity['static_resident_BG_tiles_equal_ROM'])
        self.check(name+' animated tiles are actual authored ROM frames',fidelity['animated_tiles_are_authored_ROM_frames'])
        self.check(name+' actual BG3 tree lower halves equal native source maps',trees['lower_BG3_exact_source_maps'])
        self.check(name+' declared tree roots own the correct physical base cells',trees['root_ownership_matches_placements'])
        self.check(name+' tree placement capacity respected',trees['stats'][10]==0,trees['count'])
        (folder/'room.bin').write_bytes(read(self.c,P.sym('gRoom'),10242))
        (folder/'BG_tiles.bin').write_bytes(read(self.c,0x06000000,self.ts['tile_count']*32))
        (folder/'BG_maps.bin').write_bytes(read(self.c,0x06000000+24*2048,16384))
        (folder/'BG3_map.bin').write_bytes(read(self.c,0x06000000+12*2048,8192))
        images={};views=[]
        # World partitions have no overlap. Each is a literal rectangle copied
        # from a native view; selected edges favor the interior of that view.
        xs=(0,136,272);ys=(0,112,224);xb=(0,188,324,512);yb=(0,136,248,384)
        mosaic=Image.new('RGB',(512,384));coverage=bytearray(512*384)
        for j,y in enumerate(ys):
            for i,x in enumerate(xs):
                im,meta=self.capture_view(x,y);images[(i,j)]=im
                path=folder/f'camera-{x:03d}-{y:03d}.png';im.save(path)
                world=[xb[i],yb[j],xb[i+1],yb[j+1]]
                crop=[world[0]-x,world[1]-y,world[2]-x,world[3]-y]
                piece=im.crop(crop);mosaic.paste(piece,world[:2])
                for yy in range(world[1],world[3]):
                    for xx in range(world[0],world[2]):coverage[yy*512+xx]+=1
                views.append({'file':str(path.relative_to(self.out)),'size':list(im.size),
                              'png_sha256':sha(path.read_bytes()),'RGB_sha256':rgb_sha(im),
                              'camera':[x,y],'source_crop':crop,'world_crop':world,
                              'crop_RGB_sha256':rgb_sha(piece),'hardware':meta})
        comparisons=[]
        for j in range(3):
            for i in range(3):
                for ni,nj in ((i+1,j),(i,j+1)):
                    if ni>=3 or nj>=3:continue
                    x,y=xs[i],ys[j];nx,ny=xs[ni],ys[nj]
                    r=[max(x,nx),max(y,ny),min(x+240,nx+240),min(y+160,ny+160)]
                    a=images[i,j].crop([r[0]-x,r[1]-y,r[2]-x,r[3]-y]);b=images[ni,nj].crop([r[0]-nx,r[1]-ny,r[2]-nx,r[3]-ny])
                    differences=sum(p!=q for p,q in zip(a.getdata(),b.getdata()))
                    comparisons.append({'cameras':[[x,y],[nx,ny]],'world_overlap':r,'different_pixels':differences,'total_pixels':a.width*a.height})
        path=folder/'full-room.png';mosaic.save(path)
        self.check(name+' full room has exactly one native source per pixel',all(v==1 for v in coverage))
        copied=all(mosaic.crop(v['world_crop']).tobytes()==Image.open(self.out/v['file']).convert('RGB').crop(v['source_crop']).tobytes() for v in views)
        self.check(name+' mosaic pixels equal declared native crops',copied)
        self.check(name+' room geometry unchanged across camera fixture',contract==self.physical())
        self.check(name+' placements unchanged across camera fixture',trees==self.tree_data())
        self.check(name+' world actors stay at the same coordinates across all views',
                   all(v['hardware']['world_actors']==views[0]['hardware']['world_actors'] for v in views))
        self.check(name+' simulation RNG stays frozen across all camera views',
                   len({v['hardware']['rng'] for v in views})==1)
        return {'file':str(path.relative_to(self.out)),'size':[512,384],'png_sha256':sha(path.read_bytes()),
                'RGB_sha256':rgb_sha(mosaic),'views':views,'overlap_comparisons':comparisons,
                'physical':contract,'trees':trees,'fidelity':fidelity,
                'method':'Nine real mGBA240x160 frames, native camera/clock/HUD fixture; disjoint literal crop copies. This512x384 panorama is not a single GBA framebuffer.',
                'HUD_treatment':'Native game draw omits HUD/textbox and disablesBG0 only in review camera mode. Normal HUD-on native stills are separate.',
                'actor_treatment':'Same frozen world actor coordinates in every view; no actor layers moved, cloned, erased, or composited.',
                'overlap_note':'Native ambient glitter uses viewport-edge/HUD culling and per-view budgets; overlap differences are reported, not blended or painted.'}

    def walk(self,name,point):
        folder=self.out/name/'walk';folder.mkdir(exist_ok=True)
        self.normal();self.clear_enemies();self.settle(point)
        # Ordinary directional input only after the disclosed standing fixture.
        frames=[];observations=[];last_runs=P.r32(self.c,P.sym('gGame')+8)
        sequence=[('RIGHT',48),('DOWN',36),('LEFT',48),('UP',36)]
        tick=0
        for direction,hold in sequence:
            self.c.set_keys(P.key(self.c,direction))
            for _ in range(hold):
                P.run(self.c,1);image=self.c.bg_video.to_pil().convert('RGB').copy()
                image.save(folder/f'{tick:04d}.png');frames.append(image)
                now=P.r32(self.c,P.sym('gGame')+8)
                observations.append({'tick':tick,'direction':direction,'position':list(P.player_pos(self.c)),
                                     'logic_updates':(now-last_runs)&0xffffffff,'gFrame':P.r32(self.c,P.sym('gFrame')),
                                     'run_frames':now,'body':self.completed})
                last_runs=now;tick+=1
        self.c.clear_keys(*range(10))
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate','16777216/280896','-i',str(folder/'%04d.png'),'-c:v','libx264','-pix_fmt','yuv444p','-crf','14',str(folder.parent/'walk.mp4')],check=True)
        gif=folder.parent/'walk.gif'
        try:gifmeta=T.sampled_gif(frames[::8],gif,hold=130)
        except AssertionError:
            if gif.exists():gif.unlink()
            gif=None;gifmeta={'omitted':True,'reason':'Native sampled RGB union exceeds GIF palette or failed exact roundtrip; raw frames and full-rate video retained.'}
        save_json(folder.parent/'walk-observations.json',observations)
        body=[o['body'] for o in observations if o['body'] and o['body'].get('body_found')]
        minimum=min((b['exact_visible_pixels'] for b in body),default=0)
        self.check(name+' ordinary walk Bloom minimum visible colored pixels',minimum>=37,minimum)
        self.check(name+' ordinary walk body guard uses exact current pixels',all(b['guard_exact_native_subset'] for b in body))
        missed=[{'tick':o['tick'],'gFrame':o['gFrame'],'position':o['position']} for o in observations if not o['logic_updates']]
        limit=self.timing_limits[name]
        baseline=next(r for r in self.timing_baseline['captures'] if r['build']=='base29' and r['room']==name)
        expected=next((n,s,k) for n,s,k in DEFAULT_ROOMS if n==name)
        bound=(self.current_case==dict(zip(('name','seed','cell'),expected)) and
               baseline['initial_position']==list(point) and len(baseline['frames'])==len(observations)==168)
        self.check(name+' timing qualification bound to pinned room seed position and frame count',bound,
                   {'case':self.current_case,'initial_position':list(point),'frames':len(observations),
                    'pinned_baseline_ROM_sha256':baseline['rom_sha256'],'comparison_sha256':TIMING_BASELINE_SHA})
        self.check(name+' every recorded frame has paired native body proof',len(body)==len(observations) and
                   all(b.get('scanline0')==0 and b.get('scanline160')==160 and b.get('video_frame')==b.get('end_video_frame') for b in body))
        self.check(name+' missed logic intervals do not exceed pinned historical control',bound and len(missed)<=limit,
                   {'actual_missed_intervals':missed,'allowed_historical_count':limit,'historical_profile':29,
                    'comparison_sha256':TIMING_BASELINE_SHA,'frame_perfect_claim':False})
        return {'movie':str((folder.parent/'walk.mp4').relative_to(self.out)),'gif':str(gif.relative_to(self.out)) if gif else None,
                'frames':len(frames),'raw_frames_local':str(folder),'observations':str((folder.parent/'walk-observations.json').relative_to(self.out)),
                'minimum_visible_Bloom_pixels':minimum,'missed_updates':sum(o['logic_updates']==0 for o in observations),
                'total_logic_updates':sum(o['logic_updates'] for o in observations),'missed_update_frames':missed,
                'historical_missed_update_limit':limit,'timing_qualification_case':self.current_case,'timing_comparison_sha256':TIMING_BASELINE_SHA,'frame_perfect_claim':False,'gif_metadata':gifmeta,
                'fixture':'Enemy/projectile/FX clearing and initial safe standing position only; the recorded movement is ordinary directional input. No tree/terrain/pose pixels injected.'}

    def room(self,name,seed,cell):
        self.current_case={'name':name,'seed':seed,'cell':cell}
        self.boot(seed,cell)
        folder=self.out/name;folder.mkdir(exist_ok=True)
        P.run(self.c,3);arrival=self.still(folder/'native-arrival.png')
        removed=self.clear_enemies();point=self.point();self.settle(point)
        before=self.still(folder/'native-HUD.png')
        pano=self.panorama(name)
        self.normal();self.settle(point)
        views=[]
        for label,facing in (('north',0),('west',3),('south',2)):
            P.w8(self.c,P.sym('gActors')+7,facing);P.w8(self.c,P.sym('gActors')+6,facing*8);P.run(self.c,6)
            views.append(self.still(folder/f'native-HUD-{label}.png'))
        movie=self.walk(name,point) if self.args.movies else None
        row={'name':name,'seed':hex(seed),'cell':cell,'stage':self.world['cells'][cell]['stage'],
             'initial_position':list(point),'navigation_fixture':'Actual title-seeded maze; ordinary sewer entrance then selected cell through existing native area-transition statics. Terrain is generated by ROM.',
             'cleared_actors':removed,'native_arrival':arrival,'native_HUD':before,'normal_facing_views':views,'panorama':pano,'walk':movie}
        self.rows.append(row);self.save()

    def save(self):
        save_json(self.out/'capture.json',{'source_freeze':self.freeze,'bundle':str(self.base),
            'bundle_sha256':self.immutable,'forest_variant':31,'capture_tool_sha256':LOADED_SHA,
            'capture_dependency_sha256':self.deps,'command':sys.argv,'captures':self.rows,
            'timing_baseline':{'file':'timing-baseline.json','sha256':TIMING_BASELINE_SHA,
                               'method':'Same naturally generated cells, same safe positions,60-frame warmup and matched clock1024/input sequence. Historical profile29 has1/1/0 missed logic intervals; the main capture preserves every native video frame and reports its exact missed ticks. Different art and navigation phases limit timing comparison.'} if self.timing_baseline else None,
            'checks':self.checks,'pass':all(c['passed'] for c in self.checks)})

    def finish(self):
        if len(self.rows)==3:
            frames={p['frame'] for r in self.rows for p in r['panorama']['trees']['placements']}
            self.check('three natural rooms use all twelve approved tree frames',frames==set(range(12)),sorted(frames))
        if self.timing_baseline:
            self.check('pinned timing comparison copied without changes',sha((self.out/'timing-baseline.json').read_bytes())==TIMING_BASELINE_SHA)
        self.check('frozen ROM/header/map unchanged',all(sha((self.base/n).read_bytes())==v for n,v in self.immutable.items()))
        self.check('capture helper unchanged during execution',sha(Path(__file__).read_bytes())==LOADED_SHA)
        self.check('capture dependencies unchanged during execution',all(sha((Path(__file__).parent/n).read_bytes())==v for n,v in self.deps.items()))
        self.save()
        if not all(c['passed'] for c in self.checks):raise SystemExit('capture verification failed')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',required=True);parser.add_argument('--out',required=True)
    parser.add_argument('--only',default='healthy,mixed,deep');parser.add_argument('--movies',action='store_true')
    parser.add_argument('--timing-baseline')
    args=parser.parse_args();review=Review(args)
    for name,seed,cell in DEFAULT_ROOMS:
        if name in args.only.split(','):review.room(name,seed,cell)
    review.finish()


if __name__=='__main__':main()

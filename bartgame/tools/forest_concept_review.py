#!/usr/bin/env python3
"""Review five forest art alternatives in real, matched mGBA runs.

The frozen ROM generates every room and mystery normally. Disclosed fixtures
select seed, room transition, inventory, health and safe player position/facing,
and clear unrelated enemies. Ambient glitter stays active. After the camera
settles, the comparison clock is normalized, then64 real frames run before
recording. No terrain, mystery descriptor, actor animation frame or picture is
assigned. Actual item actions create the recorded opened/burnt/pressed states.
Movement across a chasm is released while the transition is still loading,
so a faster graphics upload cannot add a walk step in the destination room.

The baseline writes a reusable position/feature plan; --match reuses it in
every alternative. Native PNGs are exact240x160 framebuffers. Only ten useful
flows get full-rate MP4 viewing copies and exact-palette GIFs; other contexts
use a single still or three native before/action/after frames.
"""
import argparse, hashlib, json, struct, subprocess
from pathlib import Path
from types import SimpleNamespace
from PIL import Image, ImageDraw, ImageFont
import probe as P
import bloom_probe as BP
import bloom_review as BR
import blight_review as BL
import critical_path as C
import lift_probe as L
import myst_probe as M
import interactive_review as IR
from sewer_concept_audit import NativeRom
from bloom_suite_gallery import write_gif
from sewer_concept_review import gif_durations

FPS=16777216/280896
FONT=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)
ARCHES=('glade','grove','ruins','pond','thicket','boneyard','Heart glade','entry')
SIDES=('UP','RIGHT','DOWN','LEFT')
GROUPS=('control','rooms','landscapes','npcs','interiors','interactive','gates')
MOVIE_INTERACTIONS={'forest-wood-chest','cave-floor-switch','forest-bomb-wall','forest-cobweb','forest-cape-hole'}
FEATURES={
    'healthy-canopy':('gtree_','gtree2_','tree_','tree2_','birch_','fir_'),
    'mixed-forest':('rot_','forest_rot'),
    'deep-blight':('forest_blight_tree','blight_wall','blight_pool','canopy_blight'),
    'water-bridge':('water','shore_','bridge'),
    'pit-bank':('pit','forest_blight_pit'),
    'ledge-path':('ledge_','ramp_'),
    'ground-growths':('fern_patch','leaf_litter','bush','moss_flowers','blight_crystal'),
}
sha=lambda data:hashlib.sha256(data).hexdigest()

def read(c,at,n):return bytes(P.r8(c,at+i) for i in range(n))
def jsonsha(value):return sha(json.dumps(value,sort_keys=True,separators=(',',':')).encode())

class Review(IR.Review):
    def __init__(self,args):
        self.args=args;self.frozen=Path(args.frozen).resolve();self.out=Path(args.out).resolve()
        self.out.mkdir(parents=True,exist_ok=True)
        args.rom=str(self.frozen/'bartgame.gba');P.ROM=args.rom
        args.map=str(self.frozen/'bartgame.map');args.assets_header=str(self.frozen/'assets.h')
        self.defs=BP.configure(SimpleNamespace(map=args.map,assets_header=args.assets_header))
        C.mt=lambda name:self.defs['MT_'+name]
        self.names={v:k[3:].lower() for k,v in self.defs.items() if k.startswith('MT_')}
        self.variant=self.defs.get('BART_FOREST_VARIANT',0)
        self.rom=NativeRom(self.frozen);self.rom_hash=sha(self.rom.rom)
        self.freeze=json.loads((self.frozen/'freeze.json').read_text())
        self.frozen_hashes={name:sha((self.frozen/name).read_bytes()) for name in ('bartgame.gba','bartgame.map','assets.h','freeze.json')}
        self.tool_hash=sha(Path(__file__).read_bytes())
        self.old=json.loads(Path(args.match).read_text()) if args.match else None
        self.old_rows={r['name']:r for r in self.old['captures']} if self.old else {}
        self.old_plan=self.old.get('plan',{}) if self.old else {}
        self.rows=[];self.checks=[];self.missing=[];self.c=None;self.worlds={};self.catalog={};self.plan={}
        self.keep_boss=False;self.mystery=None;self.ts_cache={};self.seed=int(args.seed,0)
        self.rng=BP.static_symbol('sRand')
        self.groups=set(args.only.split(',')) if args.only else set(GROUPS)
        self.check('valid forest study profile',0<=self.variant<=5)
        self.check('selected surrounding art retained',self.defs.get('BART_ENEMY_VARIANT')==11 and self.defs.get('BART_UI_VARIANT')==6 and self.defs.get('BART_MENU_VARIANT')==1 and self.defs.get('BART_SEWER_VARIANT')==9)
        self.check('frozen ROM checksum matches manifest',self.rom_hash==self.freeze['rom_sha256'])
        self.static_hardware()

    def check(self,name,condition,detail=None):
        row={'name':name,'passed':bool(condition)}
        if detail is not None:row['detail']=detail
        self.checks.append(row)
        if not condition:print('FAIL',name,detail,flush=True)

    def clear(self):
        at=P.sym('gActors')
        for i in range(1,96):
            if P.r8(self.c,at+i*64)==2 and not (self.keep_boss and P.r8(self.c,at+i*64+1)==5):P.w8(self.c,at+i*64,0)

    def maze(self):
        c=self.c;base=P.sym('gWorld');cells=[]
        for i in range(25):
            raw=read(c,base+4+i*13,13)
            cells.append({'gate':list(raw[:4]),'role':raw[5],'arg':raw[6],'stage':raw[7],
                          'arch':raw[8],'density':raw[9],'theme':raw[10],'dist':raw[12]})
        known=C.world(c)
        out={k:v for k,v in known.items() if k!='cells'};out['cells']=cells
        out['mysteries']=list(read(c,base+M.MYST_OFF,25))
        return out

    def progress(self):
        base=P.sym('gWorld');values=[]
        for i in range(25):values += [P.r8(self.c,base+4+i*13+4),P.r8(self.c,base+4+i*13+11)]
        values += list(read(self.c,base+M.FLAGS_OFF,25))
        return sha(bytes(values))

    def boot(self,row):
        self.keep_boss=row.get('retain_boss',False)
        super().boot(row)
        maze=self.maze();seed=row['seed'];record={'maze':maze,'maze_sha256':jsonsha(maze)}
        if seed in self.worlds:self.check(row['name']+' deterministic maze',record==self.worlds[seed])
        self.worlds[seed]=record
        self.check(row['name']+' actual requested seed',P.r32(self.c,P.sym('gWorld'))==int(seed,0))

    def contract(self):
        c=self.c;base=P.sym('gRoom');w,h=P.r8(c,base),P.r8(c,base+1)
        arrays=[];typebytes=bytearray();typ=P.sym('metatile_type');coll=P.sym('metatile_coll')
        for offset in (2,2050,8194):
            array=b''.join(read(c,base+offset+y*64,w*2) for y in range(h));arrays.append(array)
            if offset in (2,2050):
                for (mt,) in struct.iter_unpack('<H',array):
                    typebytes += bytes((255,255)) if mt==65535 else bytes((P.r8(c,typ+mt),P.r8(c,coll+mt)))
        return {'dimensions':[w,h],'ground_sha256':sha(arrays[0]),'overlay_sha256':sha(arrays[1]),
                'underlay_sha256':sha(arrays[2]),'collision_sha256':sha(read(c,base+4098,4096)),
                'types_sha256':sha(typebytes),'spots_sha256':sha(read(c,P.sym('gSpots'),58))}

    def settle(self,point,facing=0):
        C.teleport(self.c,*point);a=P.sym('gActors');P.w8(self.c,a+7,facing);P.w8(self.c,a+6,facing*8)
        for _ in range(72):self.clear();C.heal(self.c);P.run(self.c,1)
        clock=P.sym('gFrame');P.w16(self.c,clock,0);P.w16(self.c,clock+2,0)
        for _ in range(64):self.clear();C.heal(self.c);P.run(self.c,1)

    def state(self,target=None):
        c=self.c;a=P.sym('gActors');state=P.r8(c,a+2)
        row={'game_state':C.gstate(c),'area':C.area(c),'cell':C.cell(c),'state':state,
             'state_name':IR.STATES[state] if state<len(IR.STATES) else str(state),
             'position':list(P.player_pos(c)),'z_q16':P.r32(c,a+16),'hp':P.r16(c,P.sym('gPl')),
             'camera':[P.r16(c,P.sym('gCamX')),P.r16(c,P.sym('gCamY'))],
             'oam':P.r8(c,P.sym('gOamCount')),'textbox':P.r8(c,P.sym('gTbActive')),'rng_state':P.r32(c,self.rng)}
        if target:
            base=P.sym('gRoom');at=target[1]*32+target[0]
            for name,offset in (('target_ground',2),('target_overlay',2050)):
                row[name]=self.names.get(P.r16(c,base+offset+at*2)&65535,'none')
        return row

    def static_hardware(self):
        for name in ('sewer','forest','myst'):
            ts=self.rom.tileset(name);self.ts_cache[name]=ts
            self.check(name+' tile budget',0<ts['tile_count']<=1024,ts['tile_count'])
            self.check(name+' area palette budget',0<ts['palette_count']<=12,ts['palette_count'])
            self.check(name+' native RGB555 palettes',all(not(v&0x8000) for v, in struct.iter_unpack('<H',ts['palettes'])))
            self.check(name+' legal animation allocations',all(a['frames']>0 and a['speed']>0 and a['base']+4<=ts['tile_count'] for a in ts['animations']))

    def hardware(self):
        name=('sewer','forest','myst')[C.area(self.c)];ts=self.ts_cache[name];c=self.c
        _,_,grid=self.grid();valid=True
        for row in grid.values():
            for mt in row[2:]:
                if mt==65535:continue
                if mt>=self.defs['METATILE_COUNT']:valid=False;continue
                entries=struct.unpack_from('<4H',ts['map'],mt*8)
                valid &= all((q&1023)<ts['tile_count'] and (q>>12)<ts['palette_count'] for q in entries)
        data=read(c,0x06000000,ts['tile_count']*32);animated=set();legal=True
        for a in ts['animations']:
            start=a['base']*32;animated.update(range(start,start+128))
            legal &= data[start:start+128] in [a['data'][i*128:(i+1)*128] for i in range(a['frames'])]
        static=all(x==y for i,(x,y) in enumerate(zip(data,ts['tiles'])) if i not in animated)
        palettes=read(c,P.sym('gPalBg'),ts['palette_count']*32)==ts['palettes']
        oam=BP.oam(c);shapes=all(o['shape']<3 and o['tile']<1024 and 0<=o['pal']<16 for o in oam)
        return {'active_tileset':name,'native_room_mappings':bool(valid),'static_BG_bytes_match_ROM':static,
                'animated_BG_bytes_are_authored_frames':bool(legal),'world_palette_bytes_match_ROM':palettes,
                'OAM_legal':shapes and len(oam)<=128,'oam_count':len(oam),
                'BG_sha256':sha(data),'animated_allocations':len(ts['animations'])}

    def still_point(self,prefixes=(),point=None):
        if point is not None:return list(point)
        w,h,g=self.grid()
        if not prefixes and w>=15 and h>=10:
            preferred=BL.focus(self.c,self.names)
            if self.safe(*preferred):return preferred
        candidates=[]
        targets=[(x,y) for (x,y),row in g.items() if any(n.startswith(prefixes) for n in row[:2])] if prefixes else []
        for ty in range(3,h-2):
            for tx in range(2,w-2):
                px,py=tx*16+8,ty*16+12
                if not self.safe(px,py):continue
                cx=max(0,min(max(0,w*16-240),px-120));cy=max(0,min(max(0,h*16-160),py-104))
                visible=[row[:2] for (x,y),row in g.items() if 0<=x*16-cx<240 and 16<=y*16-cy<144]
                flat=[n for row in visible for n in row if n!='none'];score=len(set(flat))*3
                if targets:
                    shown=[(x,y) for x,y in targets if 8<=x*16-cx<=216 and 24<=y*16-cy<=128]
                    if not shown:continue
                    score += min(len(shown),14)*30-min(abs(x*16-cx-112)+abs(y*16-cy-80) for x,y in shown)*2
                else:score-=abs(px-w*8)/8+abs(py-h*8)/8
                candidates.append((score,px,py))
        if not candidates:return None
        return list(max(candidates)[1:])

    def reused(self,name,key,default=None):
        old=self.old_rows.get(name)
        return old.get(key,default) if old else default

    def record(self,row,point,target=None,facing=0,events=None,extra=None):
        events=events or {};extra=extra or {};name=row['name'];movie=row.get('movie',False)
        point=self.reused(name,'position',point);target=self.reused(name,'target',target);facing=self.reused(name,'facing',facing)
        self.settle(point,facing)
        if row.get('action')=='shrine':P.w16(self.c,P.sym('gPl'),8)
        initial=self.state(target);contract=self.contract();progress=self.progress();maze=self.maze();held=set()
        images={};trace=[];transitions=[];last=None;hw=[];total=row.get('frames',16)
        selection={0,total-1,min(total-1,extra.get('middle_frame',total//2))} if row.get('group') not in ('rooms','control','interiors') else {0}
        if movie:selection={0,total//4,total//2,total*3//4,total-1}
        raw=self.out/'all-frames'/name
        if movie:raw.mkdir(parents=True,exist_ok=True)
        frames=[]
        for tick in range(total):
            for key,down in events.get(tick,[]):
                if down:held.add(key)
                else:held.discard(key)
            self.c.clear_keys(*range(10))
            if held:self.c.set_keys(*(P.key(self.c,k) for k in sorted(held)))
            if row.get('action')!='shrine':C.heal(self.c)
            self.clear();P.run(self.c,1);state=self.state(target);state['tick']=tick
            signature=tuple(state.get(k) for k in ('game_state','area','cell','state','target_ground','target_overlay'))
            if signature!=last:transitions.append({'tick':tick,'state':list(signature)});last=signature
            if tick%8==0 or tick in selection:trace.append(state)
            if tick in selection or movie:
                image=self.c.bg_video.to_pil().convert('RGB').copy()
                if tick in selection:images[tick]=image
                if movie:image.save(raw/f'frame-{tick:03}.png');frames.append(image)
            if tick in (0,total//2,total-1) and state['game_state']==1:hw.append(self.hardware())
        self.c.clear_keys(*range(10));final=self.state(target)
        folder=self.out/name;folder.mkdir(exist_ok=True)
        for tick,image in sorted(images.items()):image.save(folder/f'frame-{tick:03}.png')
        images[0].save(self.out/(name+'.png'))
        after_image=None
        if total-1 in images:after_image=name+'-after.png';images[total-1].save(self.out/after_image)
        filmstrip=None
        if len(images)>1:
            filmstrip=name+'-filmstrip.png';film=Image.new('RGB',(240*len(images),184),'#101820');d=ImageDraw.Draw(film);d.fontmode='1'
            for i,(tick,image) in enumerate(sorted(images.items())):
                film.paste(image,(i*240,24));d.text((i*240+4,5),f'{name} / frame{tick}',font=FONT,fill='#e8c878')
            film.save(self.out/filmstrip)
        video=gif=None;gifmeta=None
        if movie:
            video=name+'.mp4'
            subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(FPS),'-i',str(raw/'frame-%03d.png'),'-vf','scale=480:320:flags=neighbor','-an','-c:v','libx264','-threads','1','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(self.out/video)],check=True)
            gif=name+'.gif';gifmeta=write_gif([im.resize((480,320),Image.Resampling.NEAREST) for im in frames[::2]],gif_durations(total),self.out/gif)
            if not gifmeta['exact_palette']:(self.out/gif).unlink();gif=None
        result={**row,**extra,'position':point,'target':target,'facing':facing,'initial':initial,'final':final,
                'natural_mystery':self.mystery,'physical_contract':contract,'final_physical_contract':self.contract(),
                'maze_sha256':jsonsha(maze),'initial_progress_sha256':progress,'final_progress_sha256':self.progress(),
                'initial_rng':initial['rng_state'],'final_rng':final['rng_state'],
                'inputs':{str(k):[[key,bool(down)] for key,down in v] for k,v in events.items()},'image':name+'.png','after_image':after_image,
                'native_frames':[f'{name}/frame-{tick:03}.png' for tick in sorted(images)],'filmstrip':filmstrip,
                'video':video,'video_fps':FPS if movie else None,'gif':gif,'gif_metadata':gifmeta,
                'all_frames':str(raw.relative_to(self.out)) if movie else None,
                'video_frames':total,'trace':trace,'mechanic_transitions':transitions,'hardware_samples':hw}
        if row.get('cell') is not None:
            desc=self.world['cells'][row['cell']];at=P.sym('gWorld')+4+row['cell']*13
            result['stage']=desc['stage'];result['role']=desc['role'];result['archetype']=ARCHES[P.r8(self.c,at+8)]
        self.check(name+' native framebuffer dimensions',all(im.size==(240,160) for im in images.values()))
        self.check(name+' unchanged maze generator output',self.maze()==maze)
        self.check(name+' legal loaded hardware',bool(hw) and all(all(v for k,v in sample.items() if k in ('native_room_mappings','static_BG_bytes_match_ROM','animated_BG_bytes_are_authored_frames','world_palette_bytes_match_ROM','OAM_legal')) for sample in hw),hw)
        if not row.get('action'):self.check(name+' scenery leaves geometry untouched',self.contract()==contract)
        self.activation_checks(result)
        if movie:self.check(name+' actual scene animation changes',len({sha(im.tobytes()) for im in frames})>1)
        old=self.old_rows.get(name)
        if old:
            fields=('seed','cell','position','target','facing','physical_contract','final_physical_contract','maze_sha256','initial_progress_sha256','final_progress_sha256','initial_rng','final_rng','inputs')
            result['matched_case']={field:old.get(field)==result.get(field) for field in fields}
            result['matched_case']['initial_camera']=old['initial']['camera']==initial['camera']
            result['matched_case']['initial_and_final_logical_state']=all(
                {k:v for k,v in old[field].items() if k!='oam'}=={k:v for k,v in result[field].items() if k!='oam'} for field in ('initial','final'))
            result['matched_case']['mechanic_transition_order']=[t['state'] for t in old['mechanic_transitions']]==[t['state'] for t in transitions]
            result['transition_tick_observation']={'baseline':[t['tick'] for t in old['mechanic_transitions']],'candidate':[t['tick'] for t in transitions],
                'note':'Native graphics load sizes may change transition completion by a VBlank; logical endpoints and ordered states remain strict checks.'}
            self.check(name+' matches baseline layout and actual state changes',all(result['matched_case'].values()),result['matched_case'])
        self.rows.append(result);self.save();print('CAPTURE',name,'seed',row['seed'],'cell',row.get('cell'),'movie',movie,flush=True)

    def activation_checks(self,r):
        action=r.get('action');name=r['name'];states=[t['state'] for t in r['mechanic_transitions']];trace=r['trace'];end=r['final'];start=r['initial']
        if action=='chest':self.check(name+' actual chest opens',any(s[3]==6 for s in states) or end.get('target_ground')!=start.get('target_ground') or end.get('target_overlay')!=start.get('target_overlay'))
        elif action=='enter':self.check(name+' actual entrance reaches generated interior',any(s[1]==2 for s in states))
        elif action=='leave':self.check(name+' actual exit returns to forest',any(s[1]==1 for s in states))
        elif action=='switch':self.check(name+' actual switch depresses',any(s[-1]=='myst_switch_down' for s in states))
        elif action=='torch':self.check(name+' actual lamp lights censer',any(s[-2]=='torch_lit' for s in states))
        elif action=='shrine':
            self.check(name+' injured Bloom heals',start['hp']==8 and any(t['hp']>=24 for t in trace))
            self.check(name+' actual shrine becomes spent',end.get('target_ground')!=start.get('target_ground'))
        elif action in ('bomb','lamp'):self.check(name+' actual item clears barrier',end.get('target_ground')!=start.get('target_ground'))
        elif action=='cape':
            self.check(name+' actual cape gains height',any(t['z_q16']>8*65536 and t['state']==5 for t in trace))
            self.check(name+' cape does not fall',all(s[3]!=4 for s in states))
        elif action=='lift':self.check(name+' actual lift reaches carry state',any(s[3]==11 for s in states))
        elif action=='npc':self.check(name+' actual NPC dialogue opens',any(t['textbox'] for t in trace))
        elif action=='gate':
            if r['gate_kind']==6:self.check(name+' actual cape crosses room boundary',end['cell']!=r['cell'] and all(s[3]!=4 for s in states))
            else:self.check(name+' actual outer gate opens',end.get('target_ground')!=start.get('target_ground') or end['cell']!=r['cell'])

    def interactive(self,row):
        row=dict(row,group='interactive',movie=row['name'] in MOVIE_INTERACTIONS)
        if row['name'] in ('cave-pot','thicket-boulder','forest-bush'):row['action']='lift';row['frames']=112
        self.boot(row);chosen=self.target(row)
        if not chosen:self.missing.append(row);self.check(row['name']+' natural target exists',False);self.save();return
        target,point,face,extra=chosen;events={};action=row.get('action');pl=P.sym('gPl')
        if action in ('chest','enter','torch'):
            point=[target[0]*16+8,target[1]*16+(42 if action=='enter' else 46)]
            if not self.safe(*point):point=[target[0]*16+8,target[1]*16+30]
        if action=='chest':events={8:[('UP',True)],36:[('UP',False)]}
        elif action=='enter':events={8:[('UP',True)],55:[('UP',False)]}
        elif action=='leave':events={8:[('DOWN',True)],56:[('DOWN',False)]}
        elif action=='shrine':target=(target[0],target[1]+1);point=[target[0]*16+8,target[1]*16+44];events={8:[('UP',True)],36:[('UP',False)]}
        elif action=='switch':
            options=[([target[0]*16+40,target[1]*16+12],3,'LEFT'),([target[0]*16-24,target[1]*16+12],1,'RIGHT'),([target[0]*16+8,target[1]*16+32],0,'UP')]
            point,face,key=next(v for v in options if self.safe(*v[0]));events={8:[(key,True)],34:[(key,False)]}
        elif action=='torch':
            C.equip_b(self.c,C.EQ_LAMP);P.w8(self.c,pl+8,P.r8(self.c,pl+8)|4)
            events={8:[('UP',True)],25:[('UP',False),('A',True)],27:[('A',False)]}
        elif action in ('bomb','lamp','cape'):
            kind=extra['pocket_kind'];P.w8(self.c,pl+8,P.r8(self.c,pl+8)|{1:2,2:4,3:8}[kind]);P.w8(self.c,pl+7,10)
            C.equip_b(self.c,{1:C.EQ_BOMBS,2:C.EQ_LAMP,3:C.EQ_CLOAK}[kind]);key=extra['direction'];warm=13 if extra['approach_distance_tiles']==2 else 0
            if action=='cape':events={8:[(key,True)],11+warm:[('A',True)],13+warm:[('A',False)],36+warm:[(key,False)]}
            else:
                events={8:[(key,True)],13+warm:[(key,False),('A',True)],15+warm:[('A',False)]}
                if action=='bomb':events[17+warm]=[(SIDES[(face+2)%4],True)];events[47+warm]=[(SIDES[(face+2)%4],False)]
        elif action=='lift':
            P.w8(self.c,pl+8,P.r8(self.c,pl+8)|32)
            point=[target[0]*16+8,target[1]*16+30];face=0
            events={1:[('UP',True)],4:[('UP',False)],8:[('R',True)],10:[('R',False)],40:[('R',True)],42:[('R',False)]};extra['middle_frame']=28
        self.record(row,point,target,face,events,extra)

    def natural_rooms(self):
        row={'name':'seeded-forest','seed':hex(self.seed),'cell':None};self.boot(row);P.enter_forest(self.c)
        for cell,desc in enumerate(self.world['cells']):
            self.warp(cell);self.mystery=None;name=f'forest-room-{cell:02d}-stage{desc["stage"]}'
            point=self.reused(name,'position') or self.still_point()
            if point is None:raise RuntimeError('no safe generated standing point for '+name)
            _,_,g=self.grid();self.catalog[cell]={'grid':g,'world':self.maze()['cells'][cell],'point':point}
            if 'rooms' in self.groups:self.record({'name':name,'group':'rooms','seed':hex(self.seed),'cell':cell,'frames':16,'note':'Actual generated room; same fixed standing point in all five alternatives.'},point)

    def landscape_plan(self):
        if 'landscapes' in self.old_plan:return self.old_plan['landscapes']
        plan=[]
        for name,prefixes in FEATURES.items():
            choices=[]
            for cell,entry in self.catalog.items():
                stage=entry['world']['stage']
                if name=='healthy-canopy' and stage>1:continue
                if name=='mixed-forest' and stage!=2:continue
                if name=='deep-blight' and stage<3:continue
                count=sum(any(n.startswith(prefixes) for n in row[:2]) for row in entry['grid'].values())
                if name=='water-bridge':
                    if not any(any(n.startswith('bridge') for n in row[:2]) for row in entry['grid'].values()):continue
                if count:choices.append((count,cell))
            if not choices:self.missing.append({'name':name,'reason':'No such feature in the primary generated seed.'});continue
            point=None
            # A dense pit band at the northern border can have no useful
            # camera approach. Try the other real occurrences before calling
            # a feature missing; never move or inject the terrain itself.
            for _,cell in sorted(choices,reverse=True):
                self.warp(cell);point=self.still_point(prefixes)
                if point is not None:break
            if point is None:self.missing.append({'name':name,'reason':'No safe view of naturally generated feature.'});continue
            plan.append({'name':name,'group':'landscapes','seed':hex(self.seed),'cell':cell,'prefixes':list(prefixes),'position':point,
                         'frames':128 if name in ('healthy-canopy','mixed-forest','deep-blight','water-bridge') else 24,
                         'movie':name in ('healthy-canopy','mixed-forest','deep-blight','water-bridge')})
        goal=self.world['goal'];plan.append({'name':'heart-glade','group':'landscapes','seed':hex(self.seed),'cell':goal,'position':[256,240],'retain_boss':True,'frames':128,'movie':True})
        return plan

    def landscapes(self):
        self.plan['landscapes']=self.landscape_plan()
        for row in self.plan['landscapes']:
            self.boot(row);point=row['position']
            if not self.safe(*point):point=self.still_point(row.get('prefixes',()))
            self.record(row,point,extra={'note':'Generated landscape and live ambient glitter. Heart context retains the real boss; other enemies are cleared.'})

    def npcs(self):
        for role,label in ((5,'hermit'),(6,'nun'),(7,'gardener')):
            seed=hex(self.seed);cell=next(i for i,e in self.catalog.items() if e['world']['role']==role)
            row={'name':'forest-npc-'+label,'group':'npcs','seed':seed,'cell':cell,'action':'npc','frames':112}
            self.boot(row);sp=P.sym('gSpots');tx,ty=P.r8(self.c,sp+27),P.r8(self.c,sp+28)
            point=[tx*16+8,(ty+1)*16+14]
            events={1:[('UP',True)],7:[('UP',False)],12:[('A',True)],14:[('A',False)]}
            self.record(row,point,[tx,ty],0,events,{'note':'Actual generated NPC placement and ordinary talk input; sprite and portrait share the real room.'})

    def interiors(self):
        for style,(label,seed,cell) in enumerate((('cave',11,17),('hollow',6,3),('thicket',6,17))):
            row={'name':'interior-'+label,'group':'interiors','seed':hex(seed),'cell':cell,'interior':True,'frames':24}
            self.boot(row);self.check(label+' actual descriptor style',self.mystery['style']==style,self.mystery)
            point=self.reused(row['name'],'position') or self.still_point()
            self.record(row,point,extra={'note':'Entered through the natural generated mouth. No mystery descriptor or terrain fixture.'})

    def gates(self):
        for kind,label in ((2,'thorns'),(3,'cracked-wall'),(4,'cobweb'),(5,'locked-door'),(6,'chasm')):
            seed=hex(self.seed);row={'name':'outer-gate-'+label,'group':'gates','seed':seed,'cell':None,'action':'gate','gate_kind':kind,'frames':240 if kind==3 else 144}
            self.boot(row);matches=[(cell,side) for cell,desc in enumerate(self.world['cells']) for side,g in enumerate(desc['gate']) if g==kind]
            if not matches:self.missing.append(row);self.check(label+' natural gate exists',False);continue
            cell,side=matches[0];row['cell']=cell;row['side']=side;P.enter_forest(self.c);self.warp(cell)
            pl=P.sym('gPl');P.w8(self.c,pl+8,127);P.w8(self.c,pl+6,3);P.w8(self.c,pl+7,10)
            x,y,key=C.door_inside(side);face=side
            # The approach is two natural corridor tiles inside the barrier.
            point=[x,y];target=[16,1] if side==0 else [16,23] if side==2 else [31,12] if side==1 else [0,12]
            if side==0:point=[x,y+16]
            events={1:[(key,True)]}
            if kind==2:C.equip_b(self.c,C.EQ_SWORD);events[25]=[(key,False),('A',True)];events[27]=[('A',False)];events[52]=[('A',True)];events[54]=[('A',False)]
            elif kind==3:
                C.equip_b(self.c,C.EQ_BOMBS);events[25]=[(key,False),('A',True)];events[27]=[('A',False)];events[30]=[(SIDES[(side+2)%4],True)];events[60]=[(SIDES[(side+2)%4],False)]
            elif kind==4:C.equip_b(self.c,C.EQ_LAMP);events[25]=[(key,False),('A',True)];events[27]=[('A',False)]
            elif kind==5:events[56]=[(key,False)]
            else:C.equip_b(self.c,C.EQ_CLOAK);events[11]=[('A',True)];events[13]=[('A',False)];events[56]=[(key,False)]
            self.record(row,point,target,face,events,{'note':'Actual generated inter-room gate; inventory/key fixtures permit the real sword/item/unlock action.'})

    def save(self):
        rows=self.rows;failures=[r for r in self.checks if not r['passed']]
        report={'schema':1,'method':__doc__.strip(),'emulator':'mGBA 0.10.5','forest_variant':self.variant,
                'source_commit':self.freeze.get('source_commit'),'freeze_sha256':self.frozen_hashes['freeze.json'],'frozen_input_sha256':self.frozen_hashes,
                'capture_tool_sha256':self.tool_hash,
                'rom_sha256':self.rom_hash,'seed':hex(self.seed),'groups':sorted(self.groups),'complete':self.groups==set(GROUPS),
                'capture_count':len(rows),'captures':rows,'rooms':[r for r in rows if r.get('group')=='rooms'],
                'plan':self.plan,'worlds':self.worlds,'checks':self.checks,'passed':len(self.checks)-len(failures),'total':len(self.checks),
                'failures':failures,'missing':self.missing,
                'format_note':'Exact native PNGs/filmstrips are primary. MP4 is full-rate/lossy with2x nearest-neighbor enlargement. GIF is retained only when the complete sampled sequence has an exact palette. Raw movie frames remain local archival evidence.'}
        (self.out/'capture.json').write_text(json.dumps(report,indent=2)+'\n')

    def run(self):
        if 'control' in self.groups:
            row={'name':'drain-control','group':'control','seed':hex(self.seed),'cell':None,'frames':16}
            self.boot(row);self.record(row,[200,270])
        if self.groups&{'rooms','landscapes','npcs'}:self.natural_rooms()
        if 'landscapes' in self.groups:self.landscapes()
        if 'npcs' in self.groups:self.npcs()
        if 'interiors' in self.groups:self.interiors()
        if 'interactive' in self.groups:
            for row in IR.plan():
                if row['cell'] is not None:self.interactive(row)
        if 'gates' in self.groups:self.gates()
        self.check('frozen ROM unchanged after capture',sha((self.frozen/'bartgame.gba').read_bytes())==self.rom_hash)
        self.check('entire frozen bundle stayed immutable during capture',all(sha((self.frozen/name).read_bytes())==expected for name,expected in self.frozen_hashes.items()))
        self.check('capture tool stayed immutable during capture',sha(Path(__file__).read_bytes())==self.tool_hash)
        if self.groups==set(GROUPS):
            self.check('all25 primary generated rooms captured',len([r for r in self.rows if r.get('group')=='rooms'])==25)
            self.check('all three mystery styles captured',{r['natural_mystery']['style'] for r in self.rows if r.get('group')=='interiors'}=={0,1,2})
            self.check('ten meaningful animation/control movies',len([r for r in self.rows if r.get('movie')])==10)
            self.check('every requested natural feature found',not self.missing,self.missing)
        self.save();print('RESULT',sum(r['passed'] for r in self.checks),'/',len(self.checks),'captures',len(self.rows),'movies',sum(r.get('movie',False) for r in self.rows),flush=True)
        return int(any(not r['passed'] for r in self.checks) or bool(self.missing))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--frozen',required=True);p.add_argument('--out',required=True);p.add_argument('--match');p.add_argument('--seed',default='0xB4A7');p.add_argument('--only',help='Comma-separated review groups; partial preflight is explicitly marked incomplete.')
    return Review(p.parse_args()).run()
if __name__=='__main__':raise SystemExit(main())

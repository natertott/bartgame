#!/usr/bin/env python3
"""Reproducible mGBA workload survey with natural rosters and explicit stress fixtures.

No terrain, artwork, framebuffer, enemy HP, AI or frame clock is changed. Natural
cases retain all generated actors. Controlled stress cases explicitly replace the
roster through the game's developer spawn request; their counts are not asserted
as naturally generated gameplay. Player health/inventory and room positioning are
fixtures. Raw VBlank/logic ages distinguish repeated video frames from modal or
transition states, which are reported separately rather than called slow logic.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import time
import traceback

import probe as P
import critical_path as C
import bloom_probe as B
from sewer_concept_audit import NativeRom

SHA=lambda x:hashlib.sha256(x).hexdigest()
MYST_OFF=4+25*13+2+3+3+3+25+1+1
KINDS=('none','pots','chest','npc','fairy','waves','survive','miniboss','switches','torches','boulders')


def read(c,at,n):
    return bytes(c.memory.u8[at+i] for i in range(n))


def w32(c,at,value):
    P.w16(c,at,value&65535);P.w16(c,at+2,(value>>16)&65535)


class Survey:
    def __init__(self,args):
        self.args=args;self.bundle=Path(args.bundle).resolve();self.out=Path(args.out).resolve()
        self.out.mkdir(parents=True,exist_ok=True)
        P.MAP=str(self.bundle/'bartgame.map');P._syms=None
        self.rom=NativeRom(self.bundle);self.rows=[];self.transitions=[];self.checks=[];self.media=[];self.errors=[];self.clips=[]
        self.rom_sha=SHA((self.bundle/'bartgame.gba').read_bytes())
        self.source=(self.bundle/'source-commit.txt').read_text().strip()
        self.addrs={n:P.sym(n) for n in ('gActors','gPl','gGame','gFrame','gRoom','gTbActive','gCamX','gCamY','gWorld','gOamCount','gAmbientPotential','gAmbientVisible','gAmbientSiteCount')}
        self.statics={n:B.static_symbol(n) for n in ('sNextArea','sNextCell','sNextSide','sTransPhase')}
        self.mtypes=P.sym('metatile_type')
        try:self.root_rows=P.sym('gForestTreeRootRows')
        except KeyError:self.root_rows=None
        self.modal_statics={n:B.static_symbol(n) for n in ('sDlgState','sShopActive')}
        self.suite=args.suite.split(',') if args.suite!='all' else ['natural','interiors','stress','actions','ui']
        self.frames=args.frames;self.started=time.time();self.fixture_points={}
        self.reference=json.loads(Path(args.reference).read_text()) if args.reference else None
        self.reference_cases={v['name']:v for v in self.reference['scenarios']} if self.reference else {}
        self.fixtures=[
            'Seed pinned before normal title Start. Original generated terrain and room rosters retained in natural cases.',
            'Existing transition request navigates rooms, bypassing travel/gates only for workload coverage; its generation/fade latency is separately recorded.',
            'Player is positioned on an actually walkable central floor near the densest local enemy group. No ground tiles are edited.',
            'Full ordinary inventory,80maximum player health,99ammo and ten hearts exercise the real HUD. Player health is restored each video frame; enemy HP, AI, timers and RNG remain live.',
            'Natural cases never remove or inject enemies. Explicit stress cases clear only nonplayer actors, then use the existing gDbgSpawn enemy-spawn path at stated counts/types.',
            'When --reference is supplied, the baseline planned player tile is reused; camera easing and enemy AI/HP are never forced to manufacture equal state.',
            'Optional --warmup runs ordinary unheld simulation/health restoration before each nonmodal sample, separating steady camera workloads from arrival/camera approach.',
            'Inputs are a fixed video-frame schedule. Faster builds may consequently advance more simulation updates; performance traces are not a claim of identical world states at equal video ages.',
            'All screenshots are native untouched240x160 mGBA framebuffers. Modal and transition states are reported separately from expected gameplay updates.',
        ]

    def check(self,name,ok,detail=None):
        self.checks.append(dict(name=name,passed=bool(ok),detail=detail))
        print(('PASS ' if ok else 'FAIL ')+name,flush=True)

    def wanted(self,name):
        return not self.args.case or re.search(self.args.case,name)

    def boot(self,seed,start=True):
        c=P.boot(rom=str(self.bundle/'bartgame.gba'),seed=seed,start=start)
        if start:C.dismiss(c,1000)
        return c

    def inventory(self,c,equipment=(4,1,5)):
        p=self.addrs['gPl'];P.w16(c,p,80);P.w16(c,p+2,80)
        P.w16(c,p+4,999);P.w8(c,p+7,99);P.w8(c,p+8,0x7f);P.w8(c,p+35,99);P.w8(c,p+36,0x0f)
        for i,e in enumerate(equipment):P.w8(c,p+9+i,e)

    def warp(self,c,area,cell,side=0):
        c.clear_keys(*range(10));C.dismiss(c,1000)
        start_frame=P.r32(c,self.addrs['gFrame']);start_logic=P.r32(c,self.addrs['gGame']+8)
        for n,v in (('sNextArea',area),('sNextCell',cell),('sNextSide',side),('sTransPhase',0)):P.w8(c,self.statics[n],v)
        P.w8(c,self.addrs['gGame'],2)
        for video in range(1800):
            c.run_frame()
            if C.gstate(c)==1 and C.area(c)==area and (area==0 or C.cell(c)==cell):break
        else:raise AssertionError('transition did not settle')
        row=dict(area=area,cell=cell,video_frames=video+1,vblanks=P.r32(c,self.addrs['gFrame'])-start_frame,logic_updates=P.r32(c,self.addrs['gGame']+8)-start_logic)
        self.transitions.append(row);C.dismiss(c,1000);self.inventory(c)
        return row

    def actor_counts(self,c):
        a=self.addrs['gActors'];counts=Counter();enemies=Counter();on=0
        camx=P.r16(c,self.addrs['gCamX']);camy=P.r16(c,self.addrs['gCamY'])
        for i in range(96):
            p=a+i*64;kind=P.r8(c,p)
            if kind:
                counts[str(kind)]+=1
                if kind==2:
                    enemies[str(P.r8(c,p+1))]+=1
                    x=P.r32(c,p+8)>>16;y=P.r32(c,p+12)>>16
                    if camx-32<=x<camx+272 and camy-32<=y<camy+192:on+=1
        return dict(kinds=dict(counts),enemy_types=dict(enemies),enemies=sum(enemies.values()),enemies_near_viewport=on,actors=sum(counts.values()))

    def safe_spot(self,c,name):
        r=self.addrs['gRoom'];w=P.r8(c,r);h=P.r8(c,r+1);solid=read(c,r+4098,4096)
        a=self.addrs['gActors'];enemies=[]
        for i in range(1,96):
            p=a+i*64
            if P.r8(c,p)==2:enemies.append((P.r32(c,p+8)>>16,P.r32(c,p+12)>>16))
        candidates=[]
        for ty in range(3,h-3):
            for tx in range(3,w-3):
                mt=P.r16(c,r+2+(ty*32+tx)*2)&65535
                if mt==65535 or P.r8(c,self.mtypes+mt)!=self.rom.defs['TT_FLOOR']:continue
                px,py=tx*16+8,ty*16+14
                if any(solid[(y>>3)*64+(x>>3)] for y in (py-8,py-1) for x in (px-5,px+4)):continue
                near=sum(abs(ex-px)<108 and abs(ey-py)<75 for ex,ey in enemies)
                distance=min((abs(ex-px)+abs(ey-py) for ex,ey in enemies),default=0)
                # Prefer enemies in view without teleporting into a contact box.
                contact=sum(abs(ex-px)<22 and abs(ey-py)<26 for ex,ey in enemies)
                score=near*1000-contact*1300-distance-abs(px-w*8)//2-abs(py-h*8)//2
                candidates.append((score,px,py))
        reference=self.reference_cases.get(name)
        point=reference['metadata'].get('fixture_point') if reference else None
        if point:
            x,y=point;tx=x//16;ty=y//16
            mt=P.r16(c,r+2+(ty*32+tx)*2)&65535
            assert mt!=65535 and P.r8(c,self.mtypes+mt)==self.rom.defs['TT_FLOOR'],'reference floor changed: '+name
            assert not any(solid[(yy>>3)*64+(xx>>3)] for yy in (y-8,y-1) for xx in (x-5,x+4)),'reference collision changed: '+name
            C.teleport(c,x,y)
        elif candidates:_,x,y=max(candidates);C.teleport(c,x,y)
        else:x,y=P.player_pos(c)
        self.fixture_points[name]=[x,y]
        self.inventory(c);P.run(c,4)
        return [x,y]

    def keys(self,c,tick,mode):
        c.clear_keys(*range(10));keys=[]
        if mode=='idle':return
        phase=tick%96
        if mode in ('combat','walk'):
            if 0<=phase<12:keys.append('RIGHT')
            elif 24<=phase<36:keys.append('DOWN')
            elif 48<=phase<60:keys.append('LEFT')
            elif 72<=phase<84:keys.append('UP')
        if mode=='combat':
            if tick%24==0:keys.append('B')
            if 12<=tick%48<20:keys.append('L')
            if tick%96==64:keys.append('A')
        elif mode=='bombs':
            if tick%32==0:keys.append('A')
            if tick%24==8:keys.append('B')
            if 16<=tick%48<24:keys.append('L')
        elif mode=='bow':
            if tick%16==0:keys.append('A')
            if tick%32==8:keys.append('B')
            if 16<=tick%48<24:keys.append('L')
        elif mode=='fire':
            if tick%32==0:keys.append('A')
            if tick%24==8:keys.append('B')
        elif mode=='lift':
            if tick%64 in (0,32):keys.append('R')
            if tick%96==48:keys.append('B')
        for key in keys:c.set_keys(P.key(c,key))

    def measure(self,c,name,seed,kind,mode='combat',metadata=None,frames=None):
        if not self.wanted(name):return
        frames=frames or self.frames
        metadata=dict(metadata or {})
        if name in self.fixture_points:metadata['fixture_point']=self.fixture_points[name]
        if self.args.warmup and kind!='modal':
            c.clear_keys(*range(10))
            for _ in range(self.args.warmup):P.w16(c,self.addrs['gPl'],80);c.run_frame()
        if self.root_rows and C.area(c)==1:
            owners=struct.unpack('<1024H',read(c,P.sym('gForestTreeRoots'),2048))
            expected=[sum((owners[y*32+x]!=0)<<x for x in range(32)) for y in range(32)]
            actual=[P.r32(c,self.root_rows+y*4) for y in range(32)]
            self.check(name+' root occupancy cache matches original owner grid',actual==expected)
        initial=dict(area=C.area(c),cell=C.cell(c),position=list(P.player_pos(c)),camera=[P.r16(c,self.addrs['gCamX']),P.r16(c,self.addrs['gCamY'])],roster=self.actor_counts(c))
        f0=P.r32(c,self.addrs['gFrame']);l0=P.r32(c,self.addrs['gGame']+8)
        samples=[];counts=[];statecounts=Counter();pstates=Counter();last=f0;prev=l0;eligible=updates=0;longest=run=0;oam=ambient=0
        record=bool(self.args.record and re.search(self.args.record,name));clip_rows=[]
        if record:(self.out/'clips'/name).mkdir(parents=True,exist_ok=True)
        for tick in range(frames):
            self.keys(c,tick,mode);P.w16(c,self.addrs['gPl'],80)
            beforestate=C.gstate(c);beforetb=P.r8(c,self.addrs['gTbActive'])
            beforearea=C.area(c);beforecell=C.cell(c)
            beforemodal=any(P.r8(c,a) for a in self.modal_statics.values())
            c.run_frame()
            frame=P.r32(c,self.addrs['gFrame']);logic=P.r32(c,self.addrs['gGame']+8)
            delta=(logic-prev)&0xffffffff;vd=(frame-last)&0xffffffff
            state=C.gstate(c);statecounts[str(state)]+=1;pstates[str(P.r8(c,self.addrs['gActors']+2))]+=1
            expect=kind!='modal' and beforestate==1 and not beforetb and not beforemodal and state==1 and not P.r8(c,self.addrs['gTbActive']) and not any(P.r8(c,a) for a in self.modal_statics.values())
            if expect:
                eligible+=1;updates+=delta
                run=run+1 if delta==0 else 0;longest=max(longest,run)
            maxo=P.r8(c,self.addrs['gOamCount']);oam=max(oam,maxo);ambient=max(ambient,P.r8(c,self.addrs['gAmbientPotential']))
            sample=dict(video=tick,gFrame=frame,logic=logic,logic_delta=delta,vblank_delta=vd,state=state,player_state=P.r8(c,self.addrs['gActors']+2),sword_active=P.r8(c,self.addrs['gPl']+21),shield_up=P.r8(c,self.addrs['gPl']+34),lamp_timer=P.r8(c,self.addrs['gPl']+23),carry=P.r8(c,self.addrs['gPl']+33),modal_npc=P.r8(c,self.modal_statics['sDlgState']),modal_shop=P.r8(c,self.modal_statics['sShopActive']),textbox=P.r8(c,self.addrs['gTbActive']),expected_play=expect,area=C.area(c),cell=C.cell(c),prepared_oam=maxo)
            samples.append(sample)
            if record:
                path=self.out/'clips'/name/('%03d.png'%tick);P.snap(c,str(path))
                clip_rows.append(dict(file=str(path.relative_to(self.out)),sha256=SHA(path.read_bytes()),gFrame=frame,logic=logic))
            if tick%15==0:counts.append(dict(video=tick,**self.actor_counts(c)))
            prev,last=logic,frame
        c.clear_keys(*range(10))
        histogram=Counter(str(x['logic_delta']) for x in samples if x['expected_play'])
        row=dict(name=name,kind=kind,seed=hex(seed),input_mode=mode,metadata=metadata,warmup_frames=self.args.warmup if kind!='modal' else 0,initial=initial,video_frames=frames,vblanks=(last-f0)&0xffffffff,logic_updates=(prev-l0)&0xffffffff,eligible_gameplay_frames=eligible,eligible_gameplay_updates=updates,update_ratio=updates/eligible if eligible else None,missed_gameplay_updates=histogram.get('0',0),logic_delta_histogram=dict(histogram),longest_repeat=longest,game_states=dict(statecounts),player_states=dict(pstates),oam_peak=oam,ambient_potential_peak=ambient,actor_samples=counts,samples=samples,ending=dict(area=C.area(c),cell=C.cell(c),roster=self.actor_counts(c)))
        reference=self.reference_cases.get(name)
        if reference:
            row['reference_match']=dict(fixture_point=metadata.get('fixture_point')==reference['metadata'].get('fixture_point'),initial_enemy_types=initial['roster']['enemy_types']==reference['initial']['roster']['enemy_types'],initial_enemy_count=initial['roster']['enemies']==reference['initial']['roster']['enemies'],initial_player_position=initial['position']==reference['initial']['position'],initial_camera=initial['camera']==reference['initial']['camera'])
        selected=kind!='natural' or row['missed_gameplay_updates']>=4 or initial['roster']['enemies']>=6 or self.args.screenshots=='all'
        if self.args.screenshots!='none' and selected:
            path=self.out/'native'/(name+'.png');path.parent.mkdir(exist_ok=True);P.snap(c,str(path));self.media.append(dict(file=str(path.relative_to(self.out)),sha256=SHA(path.read_bytes()),size=[240,160],kind='untouched actual mGBA framebuffer'))
        if record:
            from PIL import Image
            pictures=[Image.open(self.out/v['file']).convert('RGB') for v in clip_rows[::6]]
            gif=self.out/'clips'/(name+'.gif')
            pictures[0].save(gif,save_all=True,append_images=pictures[1:],duration=100,loop=0,optimize=False)
            self.clips.append(dict(name=name,kind='actual mGBA simulation clip; native240x160; every6th frame held100ms, approximate real59.73Hz speed',gif=str(gif.relative_to(self.out)),gif_sha256=SHA(gif.read_bytes()),sample_step=6,duration_ms=100,frames=clip_rows))
        self.rows.append(row)
        print('%-49s %3d/%3d %.3f enemies%d->%d OAM%d repeat%d'%(name,updates,eligible,row['update_ratio'] or 0,initial['roster']['enemies'],row['ending']['roster']['enemies'],oam,longest),flush=True)
        self.save(False)

    def natural(self):
        for seed in self.args.seeds:
            c=self.boot(seed);world=C.world(c)
            if self.wanted('drain-%08x'%seed):
                self.inventory(c);self.measure(c,'drain-%08x'%seed,seed,'drain','idle')
            for cell,desc in enumerate(world['cells']):
                name='forest-%08x-cell%02d'%(seed,cell)
                if not self.wanted(name):continue
                side=next((i for i,g in enumerate(desc['gate']) if g),0)
                self.warp(c,1,cell,side);point=self.safe_spot(c,name)
                self.measure(c,name,seed,'natural','combat',dict(stage=desc['stage'],role=desc['role'],goal=cell==world['goal'],point=point))

    def interiors(self):
        for seed in self.args.seeds:
            c=self.boot(seed);world=C.world(c);kinds=set();styles=set();required=set(world['key_cell'])
            descriptors=[P.r8(c,self.addrs['gWorld']+MYST_OFF+i) for i in range(25)]
            for cell,packed in enumerate(descriptors):
                if not packed:continue
                kind=packed&15;style=packed>>6
                if cell not in required and kind in kinds and style in styles:continue
                name='interior-%08x-cell%02d-%s-%d'%(seed,cell,KINDS[kind],style)
                if not self.wanted(name):continue
                kinds.add(kind);styles.add(style)
                self.warp(c,2,cell);self.safe_spot(c,name)
                self.measure(c,name,seed,'interior','combat',dict(parent_cell=cell,descriptor=packed,mystery_kind=KINDS[kind],style=('cave','hollow','thicket')[style],size=(packed>>4)&3,required=cell in required))

    def clear_stress_actors(self,c):
        a=self.addrs['gActors']
        for i in range(1,96):P.w8(c,a+i*64,0)

    def spawn(self,c,count,type_):
        at=P.sym('gDbgSpawn');w32(c,at,(count<<8)|type_)
        for _ in range(80):
            c.run_frame()
            if not P.r32(c,at):return
        raise AssertionError('developer spawn request not consumed')

    def stress(self):
        seed=self.args.seeds[0]
        for mode,counts in [('beetles',(4,8,12,16,24)),('bats',(4,8,12,16,24)),('spitters',(4,8,12,16,24)),('slimes',(4,8,12,16,24)),('knights',(4,8,12,16,24)),('mixed',(4,8,12,16,24))]:
            for count in counts:
                name='stress-%s-%02d'%(mode,count)
                if not self.wanted(name):continue
                c=self.boot(seed);world=C.world(c);self.warp(c,1,world['entry'],2);self.safe_spot(c,name);self.clear_stress_actors(c)
                if mode=='mixed':
                    for type_ in range(5):
                        n=count//5+(type_<count%5)
                        if n:self.spawn(c,n,type_)
                else:self.spawn(c,count,('beetles','bats','spitters','slimes','knights').index(mode))
                self.inventory(c);P.run(c,12)
                self.measure(c,name,seed,'stress-throughput' if self.args.stress_mode=='idle' else 'stress',self.args.stress_mode,dict(replaced_roster=True,requested_enemies=count,enemy_family=mode,synthetic_throughput=self.args.stress_mode=='idle',player_offense=self.args.stress_mode!='idle'))

    def actions(self):
        seed=self.args.seeds[0];c=self.boot(seed);world=C.world(c)
        cells=sorted(range(25),key=lambda i:(world['cells'][i]['stage'],i))
        deep=next(i for i in reversed(cells) if i!=world['goal'])
        for cell,label in ((cells[0],'healthy'),(deep,'deep'),(world['goal'],'heart')):
            for mode,equip in (('bombs',(2,1,5)),('bow',(6,1,5)),('fire',(3,1,4)),('lift',(4,1,5))):
                name='actions-'+label+'-'+mode
                if not self.wanted(name):continue
                self.warp(c,1,cell,next((i for i,g in enumerate(world['cells'][cell]['gate']) if g),0));self.safe_spot(c,name);self.inventory(c,equip)
                if mode=='lift':self.face_liftable(c)
                self.measure(c,name,seed,'actions',mode,dict(natural_roster=True))

    def face_liftable(self,c):
        # Find an actual existing liftable with a dry approach. R still performs
        # the real pickup/throw; no carried state or thrown object is injected.
        r=self.addrs['gRoom'];w=P.r8(c,r);h=P.r8(c,r+1)
        candidates={self.rom.defs.get('MT_'+n) for n in ('BUSH','ROCK','BOULDER','POT')}
        for ty in range(3,h-3):
            for tx in range(3,w-3):
                mt=P.r16(c,r+2+(ty*32+tx)*2)&65535
                if mt not in candidates:continue
                below=P.r16(c,r+2+((ty+1)*32+tx)*2)&65535
                if below==65535 or P.r8(c,self.mtypes+below)!=self.rom.defs['TT_FLOOR']:continue
                C.teleport(c,tx*16+8,(ty+1)*16+12);P.w8(c,self.addrs['gActors']+7,0);P.w8(c,self.addrs['gActors']+6,0);P.run(c,2);return True
        return False

    def ui(self):
        seed=self.args.seeds[0];c=self.boot(seed);self.inventory(c)
        name='ui-dialogue-drain'
        if self.wanted(name):
            C.teleport(c,21*16+8,7*16+4);P.hold(c,'UP',6);P.press(c,'A',2,100)
            self.check('real named wizard dialogue opens',P.r8(c,self.addrs['gTbActive'])!=0)
            self.measure(c,name,seed,'modal','idle',dict(expected_modal=True),frames=120);C.dismiss(c,1200)
        # Menu latencies are separate workloads; run_frames is deliberately
        # paused in GS_MAP and cannot measure menu responsiveness.
        for target,key,predicate in (
            ('items','START',lambda:C.gstate(c)==4),
            ('keys','R',lambda:P.r8(c,P.sym('gMenuStudyPage'))==1),
            ('overview','R',lambda:P.r8(c,P.sym('gMenuStudyPage'))==2),
            ('zoom','A',lambda:P.r8(c,P.sym('gMenuStudyZoom'))==1),
            ('overview-return','B',lambda:P.r8(c,P.sym('gMenuStudyZoom'))==0),
            ('close','START',lambda:C.gstate(c)==1)):
            if self.args.case and not re.search(self.args.case,'ui-menu'):break
            f0=P.r32(c,self.addrs['gFrame']);c.set_keys(P.key(c,key));wait=None
            for i in range(1200):
                c.run_frame()
                if i==1:c.clear_keys(P.key(c,key))
                if i>=2 and predicate():wait=i+1;break
            c.clear_keys(*range(10))
            self.transitions.append(dict(kind='menu',target=target,video_frames=wait,vblanks=P.r32(c,self.addrs['gFrame'])-f0,draw_frames=P.r16(c,P.sym('gMenuStudyDrawFrames'))&65535))
            self.check('real menu '+target+' settles',wait is not None)
            P.run(c,8)
        if self.wanted('ui-shop'):
            C.dismiss(c,1000);C.teleport(c,4*16+8,7*16+6);P.hold(c,'UP',8);P.press(c,'A',3,60)
            shop=B.static_symbol('sShopActive')
            self.check('real frog market opens',P.r8(c,shop)!=0)
            self.measure(c,'ui-shop',seed,'modal','idle',dict(expected_shop=True),frames=120)
            P.press(c,'B',3,48);C.dismiss(c,1000)

    def save(self,complete):
        valid=[r for r in self.rows if r['eligible_gameplay_frames']>0]
        worst=sorted(valid,key=lambda r:r['update_ratio'])
        report=dict(schema=1,method=__doc__.strip(),emulator='mGBA0.10.5',source_commit=self.source,rom_sha256=self.rom_sha,tool_sha256=SHA(Path(__file__).read_bytes()),fixtures=self.fixtures,complete=complete,seeds=[hex(s) for s in self.args.seeds],configured_frames=self.frames,warmup_frames=self.args.warmup,reference_report_sha256=SHA(Path(self.args.reference).read_bytes()) if self.args.reference else None,reference_source_commit=self.reference['source_commit'] if self.reference else None,scenarios=self.rows,transitions=self.transitions,media=self.media,clips=self.clips,checks=self.checks,passed=sum(r['passed'] for r in self.checks),total=len(self.checks),errors=self.errors,summary=dict(scenarios=len(self.rows),natural_rooms=sum(r['kind']=='natural' for r in self.rows),video_frames=sum(r['video_frames'] for r in self.rows),eligible_frames=sum(r['eligible_gameplay_frames'] for r in self.rows),eligible_updates=sum(r['eligible_gameplay_updates'] for r in self.rows),worst=[dict(name=r['name'],ratio=r['update_ratio'],missed=r['missed_gameplay_updates'],enemies=r['initial']['roster']['enemies'],oam=r['oam_peak']) for r in worst[:15]],elapsed_seconds=round(time.time()-self.started,2)))
        temporary=self.out/'report.json.tmp'
        temporary.write_text(json.dumps(report,indent=2)+'\n');temporary.replace(self.out/'report.json')
        return report

    def run(self):
        try:
            for suite in self.suite:getattr(self,suite)()
            if 'natural' in self.suite and not self.args.case:self.check('all25 natural rooms per seed measured',sum(r['kind']=='natural' for r in self.rows)==25*len(self.args.seeds))
            self.check('ROM bytes remain unchanged',SHA((self.bundle/'bartgame.gba').read_bytes())==self.rom_sha)
        except Exception as e:
            traceback.print_exc();self.errors.append(str(e));self.save(False);raise
        report=self.save(True);print(json.dumps(report['summary'],indent=2),flush=True)
        return int(report['passed']!=report['total'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle',required=True);p.add_argument('--out',required=True)
    p.add_argument('--suite',default='all',help='all or comma-separated natural,interiors,stress,actions,ui')
    p.add_argument('--case',help='regular-expression selection within suites')
    p.add_argument('--frames',type=int,default=180)
    p.add_argument('--stress-mode',choices=('combat','idle'),default='combat',help='idle isolates AI/render throughput without player offense; enemy HP/AI remain live')
    p.add_argument('--reference',help='baseline report whose planned player tiles are reused; camera/AI are not forced')
    p.add_argument('--warmup',type=int,default=0,help='ordinary unheld video frames before each nonmodal sample; use matched values for steady-state comparisons')
    p.add_argument('--record',help='case-name regex: preserve every native framebuffer and a sampled GIF for selected cases')
    p.add_argument('--seeds',nargs='+',type=lambda x:int(x,0),default=[0xB4A7,0xDEADBEEF,7])
    p.add_argument('--screenshots',choices=('selected','all','none'),default='selected')
    return Survey(p.parse_args()).run()


if __name__=='__main__':raise SystemExit(main())

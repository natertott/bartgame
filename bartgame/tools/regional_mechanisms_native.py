#!/usr/bin/env python3
"""Exercise generated regional mechanism entrances and physical verbs in mGBA.

Disclosed fixtures: fresh private SRAM and title seed; normal pending room
transitions for regional survey; hero position/standing/facing; owned equipment,
ammunition and one mineral-water bottle; player invulnerability while isolating
mechanism input. No Annex menu or direct handoff-room request is used. Actual
regional doors, tools, levers, body movement and vehicle controls produce all
mechanism, collision, completion and reward changes. No enemy HP/state,
completion/fusion bits, terrain, palette, VRAM, clock or pixels are assigned.
"""
import argparse,hashlib,json,re,shutil,struct,subprocess
from pathlib import Path
import probe as P
import critical_path as C
import bloom_probe as B
from sewer_concept_audit import NativeRom
from types import SimpleNamespace

GAME=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def abi(bundle,out):
    folder=out/'abi';src=folder/'src';src.mkdir(parents=True,exist_ok=True)
    commit=(bundle/'source-commit.txt').read_text().strip()
    names=subprocess.check_output(['git','-C',str(GAME.parent),'ls-tree','-r','--name-only',commit,'--','bartgame/src'],text=True).splitlines()
    for name in names:
        if name.endswith(('.h','.inc')) or name.endswith(('handoff_objects.c','handoff_mobility.c')):
            (src/Path(name).name).write_bytes(subprocess.check_output(['git','-C',str(GAME.parent),'show',commit+':'+name]))
    event=subprocess.check_output(['git','-C',str(GAME.parent),'show',commit+':bartgame/src/handoff_events.c'],text=True)
    menu=re.search(r'static\s+struct\s*\{([^}]+)\}\s*m\s',event).group(1)
    legacy=subprocess.check_output(['git','-C',str(GAME.parent),'show',commit+':bartgame/src/legacy_items.c'],text=True)
    legacy_state=re.search(r'static\s+struct\s*\{([^}]+)\}\s*s\s',legacy).group(1)
    fields={
        'obj_size':'sizeof(Mechanism)','obj_x':'__builtin_offsetof(Mechanism,x)','obj_y':'__builtin_offsetof(Mechanism,y)',
        'obj_type':'__builtin_offsetof(Mechanism,type)','obj_state':'__builtin_offsetof(Mechanism,state)',
        'obj_solid':'__builtin_offsetof(Mechanism,solid)','obj_goal':'__builtin_offsetof(Mechanism,goal)',
        'obj_tile':'__builtin_offsetof(Mechanism,tile)','obj_frame':'__builtin_offsetof(Mechanism,frame)','obj_pending':'__builtin_offsetof(Mechanism,pending)',
        'objects_count':'__builtin_offsetof(__typeof__(sObj),count)','objects_complete':'__builtin_offsetof(__typeof__(sObj),complete)',
        'objects_pattern':'__builtin_offsetof(__typeof__(sObj),pattern)','objects_field':'__builtin_offsetof(__typeof__(sObj),field)',
        'objects_manip':'__builtin_offsetof(__typeof__(sObj),manip_tick)',
        'mob_pattern':'__builtin_offsetof(__typeof__(sMob),pattern)','mob_field':'__builtin_offsetof(__typeof__(sMob),field)',
        'mob_active':'__builtin_offsetof(__typeof__(sMob),active)',
        'mob_site':'__builtin_offsetof(__typeof__(sMob),site)','mob_px':'__builtin_offsetof(__typeof__(sMob),px)',
        'mob_py':'__builtin_offsetof(__typeof__(sMob),py)','mob_bx0':'__builtin_offsetof(__typeof__(sMob),bx0)',
        'mob_by0':'__builtin_offsetof(__typeof__(sMob),by0)','mob_by1':'__builtin_offsetof(__typeof__(sMob),by1)',
        'mob_cx0':'__builtin_offsetof(__typeof__(sMob),cx0)','mob_launch':'__builtin_offsetof(__typeof__(sMob),launch)',
        'mob_landing':'__builtin_offsetof(__typeof__(sMob),landing)',
        'mob_cart_done':'__builtin_offsetof(__typeof__(sMob),cart_done)','mob_bridge_done':'__builtin_offsetof(__typeof__(sMob),bridge_done)',
        'mob_chute_done':'__builtin_offsetof(__typeof__(sMob),chute_done)',
        'mob_under_done':'__builtin_offsetof(__typeof__(sMob),under_done)','mob_underx':'__builtin_offsetof(__typeof__(sMob),underx)','mob_undery':'__builtin_offsetof(__typeof__(sMob),undery)',
        'menu_active':'__builtin_offsetof(MenuAbi,active)',
        'legacy_minish':'__builtin_offsetof(LegacyAbi,minish)','legacy_clones':'__builtin_offsetof(LegacyAbi,clones)','legacy_size':'sizeof(LegacyAbi)',
        'plan_size':'sizeof(RegionalContentPlan)','spots_door':'__builtin_offsetof(RegionalContentSpots,door)',
        'spots_has_door':'__builtin_offsetof(RegionalContentSpots,has_door)','spots_traversal':'__builtin_offsetof(RegionalContentSpots,traversal_rect)',
        'spots_npc':'__builtin_offsetof(RegionalContentSpots,npc)','spots_mechanism':'__builtin_offsetof(RegionalContentSpots,mechanism_rect)',
        'remaining':'__builtin_offsetof(HandoffState,remaining)','completed':'__builtin_offsetof(HandoffState,completed)',
        'inventory_skills':'__builtin_offsetof(LegacyInventory,skills)','inventory_level':'__builtin_offsetof(LegacyInventory,sword_level)',
        'inventory_bottles':'__builtin_offsetof(LegacyInventory,bottles)',
        'inventory_owned':'__builtin_offsetof(LegacyInventory,owned)','LI_FLIPPERS':'LI_FLIPPERS',
        'room_ground':'__builtin_offsetof(Room,ground)','room_solid':'__builtin_offsetof(Room,solid)','room_stride':'ROOM_MAX_W','player_gilt':'__builtin_offsetof(PlayerState,gilt)',
        'fusion_flags':'__builtin_offsetof(HandoffState,fusion_flags)','fuser_shape':'__builtin_offsetof(HandoffState,fuser_shape)','halves':'__builtin_offsetof(HandoffState,kinstone_shapes)',
    }
    objsrc=(src/'handoff_objects.c').read_text()
    for name in re.findall(r'\bHO_[A-Z_]+\b',re.search(r'enum\s*\{(.*?)\};',objsrc,re.S).group(1)):
        fields[name]=name
    code='#include "handoff_objects.c"\n#include "handoff_mobility.c"\n#include "regional_content.h"\ntypedef struct{'+menu+'} MenuAbi;\ntypedef struct{'+legacy_state+'} LegacyAbi;\nconst unsigned int native_abi[] __attribute__((used,section(".abi")))={'+','.join(fields.values())+'};\n'
    (folder/'abi.c').write_text(code)
    cmd=['arm-none-eabi-gcc','-mcpu=arm7tdmi','-mthumb','-std=gnu11','-fno-builtin','-I'+str(src),'-I'+str(bundle),'-c',str(folder/'abi.c'),'-o',str(folder/'abi.o')]
    r=subprocess.run(cmd,capture_output=True,text=True);(folder/'compile.log').write_text(r.stdout+r.stderr);r.check_returncode()
    subprocess.run(['arm-none-eabi-objcopy','-O','binary','--only-section=.abi',str(folder/'abi.o'),str(folder/'abi.bin')],check=True)
    data=(folder/'abi.bin').read_bytes();values=struct.unpack('<'+'I'*len(fields),data);result=dict(zip(fields,values))
    (folder/'facts.json').write_text(json.dumps(dict(source_commit=commit,facts=result,compiler_command=cmd),indent=2)+'\n')
    return result

class Review:
    def __init__(self,a):
        self.bundle=a.bundle.resolve();self.out=a.out.resolve();self.out.mkdir(parents=True,exist_ok=True);self.f=abi(self.bundle,self.out)
        private=self.out/'private';private.mkdir(exist_ok=True);shutil.copy2(self.bundle/'bartgame.gba',private/'bartgame.gba')
        P.ROM=str(private/'bartgame.gba');P.MAP=str(self.bundle/'bartgame.map');P._syms=None;B.configure(SimpleNamespace(map=P.MAP,assets_header=str(self.bundle/'assets.h')))
        nm=subprocess.check_output(['arm-none-eabi-nm','-n',str(self.bundle/'bartgame.elf')],text=True)
        self.syms={n:int(ad,16) for ad,n in re.findall(r'^([0-9a-f]{8})\s+\w\s+(\S+)\s*$',nm,re.M)}
        nms=subprocess.check_output(['arm-none-eabi-nm','-S',str(self.bundle/'bartgame.elf')],text=True)
        candidates=[int(ad,16) for ad,size in re.findall(r'^([0-9a-f]{8})\s+([0-9a-f]+)\s+b\s+s\s*$',nms,re.M) if int(size,16)==self.f['legacy_size']]
        if len(candidates)!=1:raise AssertionError('unique pinned legacy state ABI: '+repr(candidates))
        self.legacy_state=candidates[0]
        self.r=self.section('.ewram_bss.regional_events');self.menu=self.section('.ewram_bss.handoff_menu')
        self.native=NativeRom(self.bundle);self.sheet_meta,self.sheet_pixels=self.native.sheet('handoff_mechanisms')
        self.seed=a.seed;self.checks=[];self.fixtures=[];self.frames=[];self.rooms=[];self.views=[];self.inputs=[];self.seen=set();self.qualifying=False;self.boot_count=0;self.c=P.boot(rom=P.ROM,seed=a.seed);self.settle();self.gear()
    def section(self,name):
        lines=Path(P.MAP).read_text().splitlines()
        for i,l in enumerate(lines):
            w=l.split()
            if w and w[0]==name:return int(w[1],16) if len(w)>1 else int(lines[i+1].split()[0],16)
        raise KeyError(name)
    def w32(self,addr,v):P.w16(self.c,addr,v&65535);P.w16(self.c,addr+2,(v>>16)&65535)
    def raw(self,addr,n):return bytes(P.r8(self.c,addr+i) for i in range(n))
    def check(self,name,ok,detail=None):
        live=C.gstate(self.c)==1 and P.r16(self.c,P.sym('gPl'))>0
        ok=bool(ok) and (live or not self.qualifying)
        self.checks.append(dict(name=name,passed=ok,requires_live_hero=self.qualifying,live_hero=live,detail=detail));print('PASS' if ok else 'FAIL',name,flush=True)
    def status(self):return dict(area=C.area(self.c),cell=C.cell(self.c),state=C.gstate(self.c),hero=P.actor(self.c,0),health=[P.r16(self.c,P.sym('gPl')),P.r16(self.c,P.sym('gPl')+2)],text=P.r8(self.c,P.sym('gTbActive')))
    def run(self,n,keys=(),record=False,pred=None):
        if isinstance(keys,str):keys=[keys]
        trace=dict(start_frame=P.r32(self.c,P.sym('gFrame')),keys=list(keys),requested_frames=n,start=self.status());ran=0
        self.c.set_keys(*(P.key(self.c,k) for k in keys))
        for i in range(n):
            if self.qualifying and P.r16(self.c,P.sym('gPl'))<=0:raise AssertionError('invalid controller fixture: player health depleted')
            P.w8(self.c,P.sym('gActors')+28,255)
            self.c.run_frame();ran+=1
            if record and i%3==0:self.frames.append(self.c.bg_video.to_pil().convert('RGB').copy())
            if pred and pred():break
        self.c.clear_keys(*(P.key(self.c,k) for k in keys))
        trace.update(actual_frames=ran,end_frame=P.r32(self.c,P.sym('gFrame')),end=self.status());self.inputs.append(trace)
        if self.qualifying and P.r16(self.c,P.sym('gPl'))<=0:raise AssertionError('invalid controller fixture: player health depleted')
    def settle(self):
        for i in range(1800):
            if P.r8(self.c,P.sym('gTbActive')) or P.r8(self.c,self.menu+self.f['menu_active']):self.run(2,'A');self.run(8)
            elif C.gstate(self.c)==1:return
            else:P.run(self.c,3)
        raise AssertionError('scene/modal did not settle')
    def gear(self):
        p=P.sym('gPl');li=P.sym('gLegacyInventory')
        for i in range(16):P.w8(self.c,li+i,255)
        self.w32(li+self.f['inventory_skills'],0x1fff);P.w8(self.c,li+self.f['inventory_level'],4)
        P.w8(self.c,li+self.f['inventory_bottles'],0x27);P.w8(self.c,p+8,0x7f);P.w8(self.c,p+36,15);P.w8(self.c,p+35,50);P.w8(self.c,p+7,20)
        self.fixtures.append(dict(kind='loadout: all tool ownership, original item flags,50 arrows,20seeds,one mineralwater bottle; swordlevel4 and learned skills'))
    def fresh(self,label):
        self.qualifying=False;self.c=P.boot(rom=P.ROM,seed=self.seed);self.boot_count+=1;self.settle();self.gear()
        self.fixtures.append(dict(kind='fresh seeded core before isolated case',label=label,boot=self.boot_count,health=P.r16(self.c,P.sym('gPl'))))
        if C.gstate(self.c)!=1 or P.r16(self.c,P.sym('gPl'))<=0:raise AssertionError('fresh core did not produce a living player')
    def case(self,label,fn,*args):
        self.fresh(label);self.qualifying=True
        try:fn(*args)
        finally:self.qualifying=False
    def nav(self,x,y,face=0):
        at=P.sym('gActors');self.w32(at+8,x<<16);self.w32(at+12,y<<16);self.w32(at+16,0);self.w32(at+20,0);P.w8(self.c,at+2,0);P.w8(self.c,at+7,face);P.w8(self.c,at+6,face*8)
        self.fixtures.append(dict(kind='hero navigation/standing/facing',area=C.area(self.c),cell=C.cell(self.c),x=x,y=y,face=face));self.run(2)
    def equip(self,e):
        p=P.sym('gPl');P.w8(self.c,p+9,e);P.w8(self.c,p+10,1);P.w8(self.c,p+11,5)
        self.fixtures.append(dict(kind='equipment assignment A/B/L',value=[e,1,5]))
    def warp(self,area,cell):
        self.settle();self.c.clear_keys(*range(10))
        for name,v in [('sNextArea',area),('sNextCell',cell),('sNextSide',2),('sTransPhase',0)]:P.w8(self.c,self.syms[name],v)
        if area==3:
            P.w8(self.c,self.syms['sCreamNextNode'],cell*2);P.w16(self.c,self.syms['sCreamNextX'],65535);P.w16(self.c,self.syms['sCreamNextY'],65535);P.w8(self.c,self.syms['sCreamNextFacing'],2);P.w8(self.c,self.syms['sCreamDropRows'],0)
        P.w8(self.c,P.sym('gGame'),2);self.fixtures.append(dict(kind='normal regional room transition request',area=area,cell=cell));self.settle();self.run(5)
    def plan(self):
        vals=self.raw(self.r,self.f['plan_size']);names=['area','cell','field_site','interior_site','event_kind','quest_kind','mechanism_variant','traversal_variant','fusion_color','has_wave','stage','terrace','field_mechanism_variant'];return dict(zip(names,vals))
    def scan(self,expect_fields=True):
        found={};fields={}
        for area in [1,3]:
            for cell in range(25):
                if P.r16(self.c,P.sym('gPl'))<P.r16(self.c,P.sym('gPl')+2):self.fresh('read-only survey continuation')
                self.warp(area,cell);p=self.plan();sp=P.sym('gRegionalSpots')
                p['door']=list(self.raw(sp+self.f['spots_door'],2));p['has_door']=P.r8(self.c,sp+self.f['spots_has_door']);p['traversal_rect']=list(self.raw(sp+self.f['spots_traversal'],4));p['mechanism_rect']=list(self.raw(sp+self.f['spots_mechanism'],4));p['mob_active']=P.r8(self.c,self.syms['sMob']+self.f['mob_active']);self.rooms.append(p)
                if p['event_kind']==28 and p['has_door'] and p['fusion_color']!=1:found.setdefault(p['mechanism_variant'],p)
                if p['traversal_variant']<3 and p['mob_active'] and p['traversal_rect'][2]>=5 and p['traversal_rect'][3]>=5:fields.setdefault(p['traversal_variant'],p)
        (self.out/'survey.json').write_text(json.dumps(self.rooms,indent=2)+'\n');self.check('actual generated mechanism room vocabulary',len(found)>=10,list(found))
        if expect_fields:self.check('actual admitted field traversal stamps exist',len(fields)>0,list(fields))
        return found,fields
    def enter(self,p,label):
        self.warp(p['area'],p['cell']);sp=P.sym('gRegionalSpots');door=self.raw(sp+self.f['spots_door'],2);self.nav(door[0]*16+8,door[1]*16+24);self.run(45);P.snap(self.c,str(self.out/(label+'-entrance.png')))
        self.entry_hp=P.r16(self.c,P.sym('gPl'));self.run(2,'A');self.settle();self.check(label+': ordinary generated door enters own interior',C.area(self.c)==4 and P.r8(self.c,self.syms['sHandoffSite'])==p['interior_site'],self.status());self.run(30);P.snap(self.c,str(self.out/(label+'-inside.png')))
        return C.area(self.c)==4
    def objects(self):
        a=self.syms['sObj'];rows=[]
        for i in range(P.r8(self.c,a+self.f['objects_count'])):
            at=self.syms['sObjects']+i*self.f['obj_size'];rows.append(dict(index=i,x=P.r16(self.c,at+self.f['obj_x']),y=P.r16(self.c,at+self.f['obj_y']),type=P.r8(self.c,at+self.f['obj_type']),state=P.r8(self.c,at+self.f['obj_state']),solid=P.r8(self.c,at+self.f['obj_solid']),goal=P.r8(self.c,at+self.f['obj_goal']),tile=P.r16(self.c,at+self.f['obj_tile'])&65535,frame=P.r8(self.c,at+self.f['obj_frame']),pending=P.r8(self.c,at+self.f['obj_pending'])))
        return rows
    def inspect(self,p,pattern):
        label='pattern-'+str(pattern)
        if not self.enter(p,label):return
        rows=self.objects();self.seen.update(o['type'] for o in rows)
        for o in rows:
            expected=self.sheet_pixels[o['frame']*512:(o['frame']+1)*512]
            o['uploaded']=self.raw(0x6010000+o['tile']*32,512)==expected if o['tile'] else False
        self.check(label+': native object slots allocated',len(rows)>0 and all(o['tile']>0 for o in rows),rows)
        self.check(label+': exact authored ROM pixels streamed',all(o['pending'] or o['uploaded'] for o in rows),rows)
        count=P.r16(self.c,P.sym('gOamCount'))&65535;next_tile=P.r16(self.c,self.syms['sNextTile'])&65535
        failures=P.r16(self.c,P.sym('gSpriteAllocFailures'))&65535 if 'gSpriteAllocFailures' in self.syms else 0
        self.check(label+': native OAM and OBJ budget',count<=128 and next_tile<=876 and failures==0,dict(oam=count,next_tile=next_tile,failures=failures))
        self.views.append(dict(label=label,plan=p,slots=rows))
        visible=next((o for o in rows if o['type']!=self.f['HO_TARGET']),rows[0])
        self.nav(visible['x'],min(320,visible['y']+40));self.run(45);P.snap(self.c,str(self.out/(label+'-feature.png')))
        self.frames=[];self.run(120,record=True);self.movie(label)
    def obj(self,name):return next(o for o in self.objects() if o['type']==self.f[name])
    def complete(self):return P.r8(self.c,self.syms['sObj']+self.f['objects_complete'])!=0
    def walk_to(self,x,y,record=False,limit=500):
        for i in range(limit):
            px,py=P.player_pos(self.c)
            if abs(x-px)<=1 and abs(y-py)<=1:return True
            key=('LEFT' if px>x else 'RIGHT') if abs(x-px)>1 else ('UP' if py>y else 'DOWN');self.run(1,key,record)
            if P.r8(self.c,P.sym('gTbActive')):return self.complete()
        return False
    def movie(self,name):
        if self.frames:self.frames[0].save(self.out/(name+'.gif'),save_all=True,append_images=self.frames[1:],duration=50,loop=0)
        self.frames=[]
    def pressure(self,p):
        if not self.enter(p,'pressure'):return
        d=self.obj('HO_METAL_DOOR');self.nav(d['x'],d['y']+28);self.run(70,'UP',True);self.check('closed gate stops ordinary northward walk',P.player_pos(self.c)[1]>d['y']+8 and not self.complete(),self.status())
        self.equip(4);self.nav(d['x'],d['y']+28);self.c.set_keys(P.key(self.c,'UP'));P.press(self.c,'A',2,0);self.run(65,'UP',True);self.check('Cape cannot bypass closed mechanism gate',P.player_pos(self.c)[1]>d['y']+8 and not self.complete(),self.status());self.equip(0)
        stone=self.obj('HO_STATUE');plate=self.obj('HO_SWITCH');self.nav(stone['x'],stone['y']+18)
        self.run(180,['UP','R'],True,pred=lambda:self.obj('HO_STATUE')['y']==plate['y'] and P.r8(self.c,self.syms['sObj']+self.f['objects_manip'])==0);self.run(2)
        self.check('actual push places statue on pressure plate',self.obj('HO_STATUE')['y']==plate['y'] and not self.obj('HO_METAL_DOOR')['solid'],self.objects())
        goal=next(o for o in self.objects() if o['goal']==128);ok=self.walk_to(d['x'],P.player_pos(self.c)[1],True) and self.walk_to(goal['x'],goal['y'],True)
        self.check('normal walk reaches reward through opened pressure gate',ok and self.complete(),self.status());P.snap(self.c,str(self.out/'pressure-complete.png'));self.movie('pressure')
    def bridge(self,p):
        if not self.enter(p,'bridge'):return
        m=self.obj('HO_PULL_LEVER');self.nav(m['x'],m['y']+18);self.run(2,'R',True);self.run(12,record=True)
        self.check('real R raises the physical bridge',self.obj('HO_PULL_LEVER')['state']==1,self.objects())
        target=next(o for o in self.objects() if o['goal']==128)
        # The solid handle remains on the south bank; walk around it before
        # aligning with the newly raised deck rather than through its post.
        side=m['x']+24
        crossed=self.walk_to(side,P.player_pos(self.c)[1],True) and self.walk_to(side,m['y']-26,True) and self.walk_to(target['x'],P.player_pos(self.c)[1],True) and self.walk_to(target['x'],target['y'],True)
        self.check('normal walking crosses raised bridge to actual goal',crossed and self.complete(),self.status());P.snap(self.c,str(self.out/'bridge-complete.png'));self.movie('bridge')
    def mirror(self,p):
        if not self.enter(p,'mirror'):return
        ray=self.obj('HO_LIGHT_RAY');self.nav(ray['x'],ray['y']+32);self.run(60,'L',True)
        self.check('real raised Mirror Shield lights receiver and opens gate',self.obj('HO_LIGHT_RECEIVER')['state']==1 and not self.obj('HO_METAL_DOOR')['solid'],self.objects())
        goal=next(o for o in self.objects() if o['goal']==128);self.check('receiver gate permits actual reward walk',self.walk_to(goal['x'],goal['y'],True) and self.complete(),self.status());P.snap(self.c,str(self.out/'mirror-complete.png'));self.movie('mirror')
    def clones(self,p):
        if not self.enter(p,'clones'):return
        jar=self.obj('HO_JAR_PORTAL');d=self.obj('HO_METAL_DOOR');self.nav(jar['x'],jar['y']);self.run(2,'R');self.run(5)
        self.check('real jar R enters Minish form',P.r8(self.c,self.legacy_state+self.f['legacy_minish'])==1,self.status())
        self.nav(d['x'],d['y']+28);self.frames=[];self.run(70,'UP',True);self.check('Minish form cannot bypass closed formation gate',P.player_pos(self.c)[1]>d['y']+7 and not self.complete(),self.status())
        self.nav(jar['x'],jar['y']);self.run(2,'R');self.run(5);self.check('real jar R returns full size',P.r8(self.c,self.legacy_state+self.f['legacy_minish'])==0,self.status())
        switches=[o for o in self.objects() if o['type']==self.f['HO_SWITCH']];first=switches[0]['x'];direction='RIGHT' if switches[1]['x']>first else 'LEFT';step=1 if direction=='RIGHT' else -1
        self.nav(first,19*16+12);self.run(65,'B',True)
        for target in [first+step*32,first+step*64,first+step*96]:
            self.run(70,[direction,'B'],True,pred=lambda target=target:abs(P.player_pos(self.c)[0]-target)<=1);self.run(8,'B',True)
        self.run(1);self.check('held sword on staging plates creates three real copies',P.r8(self.c,self.legacy_state+self.f['legacy_clones'])==3,self.status())
        self.run(32,'UP',True);self.check('real formation reaches three plates and opens gate',not self.obj('HO_METAL_DOOR')['solid'],self.objects());P.snap(self.c,str(self.out/'clones-formation.png'));self.movie('clones')
    def crypt_tools(self,p):
        if not self.enter(p,'tool-crypt'):return
        self.frames=[]
        m=self.obj('HO_HIT_LEVER');self.equip(1);self.nav(m['x'],m['y']+18);self.run(2,'A',True);self.run(35,record=True)
        self.check('actual sword activates strike seal',self.obj('HO_HIT_LEVER')['state']==1,self.objects());self.check('one tool cannot release three-part seal',self.obj('HO_METAL_DOOR')['solid']==1,self.objects())
        m=self.obj('HO_EYE_SWITCH');self.equip(6);self.nav(m['x'],m['y']+44);self.run(2,'A',True);self.run(45,record=True)
        self.check('actual arrow activates eye seal',self.obj('HO_EYE_SWITCH')['state']==1,self.objects());self.check('two tools cannot release three-part seal',self.obj('HO_METAL_DOOR')['solid']==1,self.objects())
        m=self.obj('HO_PACCI_POT');self.equip(14);self.nav(m['x'],m['y']+32);self.run(2,'A',True);self.run(40,record=True)
        self.check('actual Pacci projectile flips pot and opens final seal',self.obj('HO_PACCI_POT')['state']==1 and not self.obj('HO_METAL_DOOR')['solid'],self.objects())
        self.nav(m['x'],m['y']+18);self.run(2,'R',True);self.check('flipped pot R gives a real bounce',P.actor(self.c,0)['z']>0 or P.actor(self.c,0)['state']==5,self.status());P.snap(self.c,str(self.out/'tool-crypt-open.png'));self.movie('tool-crypt')
    def garden(self,p):
        if not self.enter(p,'garden'):return
        self.frames=[]
        m=self.obj('HO_HIDDEN_LADDER');self.nav(m['x'],m['y']+18);self.run(2,'R',True);self.run(3)
        self.check('real R reveals buried ladder',self.obj('HO_HIDDEN_LADDER')['state']==1,self.objects())
        m=self.obj('HO_BEANSTALK');self.equip(19);self.nav(m['x'],m['y']+18);self.run(2,'A',True);self.run(30,record=True)
        self.check('actual bottle water feeds beanstalk',self.obj('HO_BEANSTALK')['state']==1,self.objects())
        m=self.obj('HO_WEATHER');self.nav(m['x'],m['y']+18);self.run(2,'R',True);self.run(5)
        self.check('actual weather turn releases garden seal',self.obj('HO_WEATHER')['state']==1 and not self.obj('HO_METAL_DOOR')['solid'],self.objects());P.snap(self.c,str(self.out/'garden-open.png'));self.movie('garden')
    def frozen(self,p):
        if not self.enter(p,'frozen'):return
        self.frames=[]
        for kind in ['HO_BIG_ICE','HO_FROZEN_FLOWER','HO_BARREL_WEB']:
            m=self.obj(kind);self.equip(17);self.nav(m['x'],m['y']+36);self.run(2,'A',True);self.run(45,record=True);self.check('real fire frees '+kind,self.obj(kind)['state']==1 and not self.obj(kind)['solid'],self.objects())
        self.check('three actual fire contacts release cellar seal',not self.obj('HO_METAL_DOOR')['solid'],self.objects());P.snap(self.c,str(self.out/'frozen-open.png'));self.movie('frozen')
    def field(self,p,pattern):
        self.warp(p['area'],p['cell']);mob=self.syms['sMob'];get=lambda n:P.r8(self.c,mob+self.f['mob_'+n])
        self.check('field traversal '+str(pattern)+' is the actual regional variant',get('field')==1 and get('pattern')==pattern,self.status())
        rx,ry,rw,rh=self.raw(P.sym('gRegionalSpots')+self.f['spots_traversal'],4);ring=[];rm=P.sym('gRoom')
        for yy in range(ry,ry+rh):
            for xx in range(rx,rx+rw):
                if xx in [rx,rx+rw-1] or yy in [ry,ry+rh-1]:
                    mt=P.r16(self.c,rm+self.f['room_ground']+(yy*self.f['room_stride']+xx)*2)&65535
                    ring.append(dict(x=xx,y=yy,type=P.r8(self.c,P.sym('metatile_type')+mt),solid=[P.r8(self.c,rm+self.f['room_solid']+(yy*2+dy)*self.f['room_stride']*2+xx*2+dx) for dy in [0,1] for dx in [0,1]]))
        self.check('field '+str(pattern)+' has an actual dry collision-free perimeter',len(ring)>0 and all(q['type']==0 and not any(q['solid']) for q in ring),ring)
        self.frames=[]
        if pattern==1 and P.r8(self.c,P.sym('gMobilityLayer')):
            # The ordinary room arrival may already stand on an end ramp.
            # Walk off that ramp before the disclosed navigation fixture, so
            # a fixture teleport cannot be mistaken for a bridge crossing.
            self.run(45,'DOWN',True,pred=lambda:P.r8(self.c,P.sym('gMobilityLayer'))==0)
            self.check('ordinary arrival can leave field bridge ramp',P.r8(self.c,P.sym('gMobilityLayer'))==0,self.status())
        px=get('px')*16+8;py=get('py')*16+14;site=p['field_site'];remaining=P.sym('gHandoffState')+self.f['remaining']+site*2
        self.nav(px,py);self.run(2,'A',True);self.settle();self.check('field '+str(pattern)+' cache rejects an unearned crossing',not(P.r16(self.c,remaining)&0x4000),self.status())
        if pattern==0:
            x=P.r16(self.c,P.sym('gMobilityCartX'));y=P.r16(self.c,P.sym('gMobilityCartY'));self.nav(x,y+16);self.run(20);self.run(2,'A',True);self.check('real A boards regional cart',P.r8(self.c,P.sym('gMobilityMode'))==1,self.status());self.run(4);self.run(2,'A',True);self.run(500,record=True,pred=lambda:P.r8(self.c,P.sym('gMobilityMode'))==0);self.check('cart crosses and dismounts on dry station',get('cart_done')==1 and P.r8(self.c,P.sym('gMobilityMode'))==0,self.status())
        elif pattern==1:
            x=(get('bx0')+1)*16+8;top=get('by0');bottom=get('by1');self.nav(x,bottom*16+14);self.run(3);self.run((bottom-top+2)*16,'UP',True,pred=lambda:get('bridge_done')==1);self.check('upper deck is a real completed field crossing',get('bridge_done')==1,self.status())
        else:
            x=(get('cx0')+1)*16+8;y=get('launch')*16+14;self.nav(x,y);self.run(20);self.run(2,'R',True);self.check('real R launches parachute from field ledge',P.r8(self.c,P.sym('gMobilityMode'))==2,self.status());self.run(300,['RIGHT','DOWN'],True,pred=lambda:P.r8(self.c,P.sym('gMobilityMode'))==0);self.check('controlled field descent reaches dry lower shelf',get('chute_done')==1 and P.r8(self.c,P.sym('gMobilityMode'))==0,self.status())
        # Return to the cache only after the route flag was earned by controls.
        # Navigation is disclosed independently of the real traversal itself.
        self.nav(px,py);P.w16(self.c,P.sym('gPl')+self.f['player_gilt'],0);self.fixtures.append(dict(kind='gilt reset before isolated reward accounting',amount=0));before=0;self.run(2,'A',True);self.settle();after=P.r16(self.c,P.sym('gPl')+self.f['player_gilt'])&65535
        self.check('field '+str(pattern)+' crossing pays its actual cache',bool(P.r16(self.c,remaining)&0x4000) and after==100,self.status())
        self.run(2,'A');self.settle();self.check('field '+str(pattern)+' cache cannot pay twice',(P.r16(self.c,P.sym('gPl')+self.f['player_gilt'])&65535)==after,self.status())
        if pattern==1:
            center=(get('bx0')+1)*16+8;bottom=get('by1')*16+14
            self.nav(center,bottom);self.run(45,'DOWN',True,pred=lambda:P.r8(self.c,P.sym('gMobilityLayer'))==0)
            self.check('bridge ramp returns to ground plane',P.r8(self.c,P.sym('gMobilityLayer'))==0,self.status())
            uy=get('undery')*16+14;self.nav(rx*16+8,uy);self.run(rw*20,'RIGHT',True,pred=lambda:get('under_done')==1)
            self.check('actual low-bank walk passes beneath bridge',get('under_done')==1 and P.r8(self.c,P.sym('gMobilityLayer'))==0,self.status())
            self.walk_to(get('underx')*16+8,uy,True);self.run(2,'A',True);self.settle();paid=P.r16(self.c,P.sym('gPl')+self.f['player_gilt'])&65535
            self.check('underpass earns its separate twenty-gilt cache',bool(P.r16(self.c,remaining)&0x2000) and paid==after+20,self.status())
            self.run(2,'A');self.settle();self.check('underpass cache cannot pay twice',(P.r16(self.c,P.sym('gPl')+self.f['player_gilt'])&65535)==paid,self.status())
        self.movie('field-'+str(pattern));P.snap(self.c,str(self.out/('field-'+str(pattern)+'-result.png')))
    def red_fusion(self,p):
        self.warp(p['area'],p['cell']);sp=P.sym('gRegionalSpots');x,y,w,h=self.raw(sp+self.f['spots_mechanism'],4);hs=P.sym('gHandoffState');npc=self.raw(sp+self.f['spots_npc'],2)
        self.check('red fusion has a physical field pool',w>=5 and h>=5 and P.r8(self.c,self.syms['sObj']+self.f['objects_field'])==1,dict(plan=p,rect=[x,y,w,h]))
        if w<5 or h<5:return
        tile=lambda tx,ty:P.r16(self.c,P.sym('gRoom')+self.f['room_ground']+(ty*self.f['room_stride']+tx)*2)&65535
        old=tile(x+2,y+3);self.nav((x+2)*16+8,(y+4)*16+12);self.frames=[];self.run(30,'UP',True)
        self.check('unfused field island cannot yield its reward',not self.complete() and not(P.r16(self.c,hs+self.f['remaining']+p['field_site']*2)&0x8000),self.status())
        self.nav(npc[0]*16+8,npc[1]*16+26);shape=P.r8(self.c,hs+self.f['fuser_shape']+2);P.w8(self.c,hs+self.f['halves']+6+shape,1);self.fixtures.append(dict(kind='one matching red kinstone half',shape=shape))
        self.run(2,'A',True);self.settle();self.run(10,record=True)
        self.check('real fuser A consumes half and raises field bridge',(P.r8(self.c,hs+self.f['fusion_flags'])&4)!=0 and P.r8(self.c,hs+self.f['halves']+6+shape)==0 and tile(x+2,y+3)!=old,self.status())
        self.nav((x+2)*16+8,(y+4)*16+12);self.walk_to((x+2)*16+8,(y+2)*16+12,True);self.run(3,record=True)
        self.check('actual walking across fused bridge reaches island reward',bool(P.r16(self.c,hs+self.f['remaining']+p['field_site']*2)&0x8000),self.status());P.snap(self.c,str(self.out/'red-fusion-island.png'));self.movie('red-fusion');self.settle()
    def entrance_safety(self,p,pattern):
        item=self.f['LI_FLIPPERS'];at=P.sym('gLegacyInventory')+self.f['inventory_owned']+(item>>5)*4;old=P.r32(self.c,at);self.w32(at,old&~(1<<(item&31)))
        self.fixtures.append(dict(kind='remove Flippers ownership for ordinary-entry safety',item=item))
        label='dry-entry-'+str(pattern)
        if not self.enter(p,label):return
        self.frames=[];self.run(120,record=True);actor=P.actor(self.c,0);px,py=P.player_pos(self.c);mt=P.r16(self.c,P.sym('gRoom')+self.f['room_ground']+((py//16)*self.f['room_stride']+px//16)*2)&65535
        self.check(label+': no swimming gear needed to stand at actual arrival',P.r8(self.c,P.sym('metatile_type')+mt)==0 and actor['state']==0 and self.entry_hp>0 and P.r16(self.c,P.sym('gPl'))==self.entry_hp,self.status())
        self.run(160,'DOWN',True,pred=lambda:C.area(self.c)!=4);self.settle();self.check(label+': actual southward walking returns to parent',C.area(self.c)==p['area'] and C.cell(self.c)==p['cell'],self.status());self.movie(label);self.w32(at,old);self.fixtures.append(dict(kind='restore prior Flippers ownership after isolated safety check'))
    def report(self,error=None):
        data=dict(method=__doc__,seed=self.seed,source_commit=(self.bundle/'source-commit.txt').read_text().strip(),rom_sha256=sha(self.bundle/'bartgame.gba'),tool_sha256=sha(__file__),checks=self.checks,fixtures=self.fixtures,input_trace=self.inputs,rooms=self.rooms,views=self.views,observed_object_families=sorted(self.seen),passed=sum(c['passed'] for c in self.checks),total=len(self.checks),error=error)
        (self.out/'report.json').write_text(json.dumps(data,indent=2)+'\n');return data

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--bundle',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--seed',type=lambda x:int(x,0),default=0xb4a7);ap.add_argument('--ferry-only',action='store_true');ap.add_argument('--fields-only',action='store_true');a=ap.parse_args();r=Review(a)
    try:
        found,fields=r.scan(not a.ferry_only)
        for pattern,p in sorted(found.items()):
            if not a.fields_only and (not a.ferry_only or pattern==2):r.case('render pattern '+str(pattern),r.inspect,p,pattern)
        if not a.ferry_only:
            if not a.fields_only:
                for pattern,fn in [(0,r.pressure),(4,r.garden),(6,r.bridge),(8,r.mirror),(9,r.clones),(10,r.crypt_tools),(11,r.frozen)]:
                    if pattern in found:r.case('controller pattern '+str(pattern),fn,found[pattern])
                    else:r.check('generated pattern '+str(pattern)+' present',False)
            for p,room in fields.items():r.case('field traversal '+str(p),r.field,room,p)
            red=next((p for p in r.rooms if p['fusion_color']==2 and p['mechanism_rect'][2]>=5),None)
            if red:r.case('red fusion',r.red_fusion,red)
            else:r.check('red fusion physical field host exists',False)
            if not a.fields_only:
                for pattern in range(3):
                    p=next((p for p in r.rooms if p['event_kind']==27 and p['traversal_variant']==pattern and p['has_door'] and p['fusion_color']!=1),None)
                    if p:r.case('unassisted entrance '+str(pattern),r.entrance_safety,p,pattern)
                    else:r.check('generated traversal entrance '+str(pattern)+' exists',False)
    except Exception as e:r.report(repr(e));raise
    d=r.report();print('RESULT',d['passed'],'/',d['total']);raise SystemExit(0 if d['passed']==d['total'] else 1)
if __name__=='__main__':main()

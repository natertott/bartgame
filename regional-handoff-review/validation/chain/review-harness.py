#!/usr/bin/env python3
"""Exercise real regional quests and the four-objective Earth victory in mGBA.

The normal ROM and its exact committed ABI are used. Opening gifts, NPC
acceptance, quest actions, enemy damage, objectives and the Earth pickup use
real input. No inventory, health, enemy, completion, gate or terrain is assigned.
Hero position/facing are disclosed navigation fixtures. The isolated quest
suite additionally requests the game's ordinary regional room-load path; the
chain suite follows actual admitted graph edges and ordinary doors instead.
This is a native mechanic proof using navigation fixtures, not an unassisted
playthrough. Private ROM/SRAM copies never open a user's save.
"""
from collections import deque
import argparse
import hashlib
import heapq
import io
import json
from pathlib import Path
import re
import shutil
import struct

import mgba.core
import mgba.image
import subprocess
import tarfile

import probe as P
import critical_path as C
import release_boundary_review as B
from regional_native_support import NativeRun, sha


GAME=Path(__file__).resolve().parent.parent
REPO=GAME.parent
PLAN_FIELDS=('area','cell','field_site','interior_site','event_kind','quest_kind',
             'mechanism_variant','traversal_variant','fusion_color','has_wave',
             'stage','terrace','field_mechanism_variant')
QUEST_FIELDS=('kind','state','stake','difficulty','origin_area','origin_cell',
              'target_area','target_cell','mode','progress','quota','wave',
              'cargo_held','cargo_ground','cargo_flying','reserved','timer','count',
              'cargo_x','cargo_y','receiver_x','receiver_y')
QUEST_WORDS={'timer','count','cargo_x','cargo_y','receiver_x','receiver_y'}


class DraftPreferences:
    def __init__(self,run):self.run=run
    def __len__(self):return 3
    def __getitem__(self,round_):
        choices=self.run.snapshot()['draft']['options']
        priorities=(7,15,20) if round_==0 else (89,88,87,98) if round_==1 else (79,74,72,73,75)
        return next((choices.index(item) for item in priorities if item in choices),0)


def extra_abi(bundle,out,headers):
    """Compile read-only offsets from the pinned actual implementation.

    Private animation/anchor data is inspected by its own compiler layout,
    never by hand-maintained offsets. This object is not linked into the ROM.
    """
    out.mkdir(parents=True,exist_ok=True)
    commit=(bundle/'source-commit.txt').read_text().strip()
    archive=subprocess.check_output(['git','archive',commit,'bartgame/src'],cwd=REPO)
    files={}
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        for member in tar:
            if member.isfile() and member.name.endswith(('.c','.inc')):
                rel=Path(member.name).relative_to('bartgame/src')
                if '..' in rel.parts:raise ValueError(member.name)
                path=out/rel;path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(tar.extractfile(member).read());files[str(rel)]=sha(path)
    expressions={'plan_size':'sizeof(RegionalContentPlan)',
                 'puzzle_size':'sizeof(HandoffPuzzle)',
                 'puzzle_blocks':'offsetof(HandoffPuzzle,blocks)',
                 'puzzle_length':'offsetof(HandoffPuzzle,length)',
                 'puzzle_solution':'offsetof(HandoffPuzzle,solution)',
                 'cream_climb_x':'offsetof(CreamRoomInfo,climb_x)',
                 'cream_upper_bottom':'offsetof(CreamRoomInfo,upper_bottom)',
                 'cream_lower_top':'offsetof(CreamRoomInfo,lower_top)',
                 'world_key_cell':'offsetof(World,key_cell)',
                 'world_gate_cell':'offsetof(World,gate_cell)',
                 'world_gate_side':'offsetof(World,gate_side)',
                 'world_myst':'offsetof(World,myst)',
                 'world_myst_flags':'offsetof(World,myst_flags)',
                 'handoff_contract_item':'offsetof(HandoffState,contract_item)',
                 'handoff_difficulty':'offsetof(HandoffState,difficulty)',
                 'handoff_score':'offsetof(HandoffState,score)',
                 'ldef_size':'sizeof(LegacyItemDef)',
                 'ldef_flags':'offsetof(LegacyItemDef,flags)',
                 'ldef_equip':'offsetof(LegacyItemDef,equip)',
                 'legacy_item_count':'LI_COUNT'}
    expressions.update({'plan_'+f:'offsetof(RegionalContentPlan,'+f+')' for f in PLAN_FIELDS})
    expressions.update({'quest_'+f:'offsetof(HandoffQuest,'+f+')' for f in QUEST_FIELDS})
    for f in ('points','point_count','giver','receiver','owned','board','plan','wave_site','component'):
        expressions['r_'+f]='offsetof(__typeof__(r),'+f+')'
    for f in ('clock','clean','count','site','kind','board_x','board_y','phase','quota','switch_mask','goal_spawned'):
        expressions['s_'+f]='offsetof(__typeof__(s),'+f+')'
    unit=out/'handoff-observe.c'
    unit.write_text((out/'handoff_events.c').read_text()+'\n#include <stddef.h>\n'
        +'__attribute__((used,section(".qa_offsets"))) const unsigned qa_extra[]={\n'
        +',\n'.join(expressions.values())+'\n};\n')
    obj=out/'observe.o';raw=out/'observe.bin'
    command=['arm-none-eabi-gcc','-mcpu=arm7tdmi','-mthumb','-O2','-fno-builtin',
             '-DBART_FOREST_VARIANT=32','-I',str(headers),'-I',str(out),
             '-c',str(unit),'-o',str(obj)]
    result=subprocess.run(command,capture_output=True,text=True)
    (out/'compile.log').write_text(result.stdout+result.stderr);result.check_returncode()
    subprocess.run(['arm-none-eabi-objcopy','-O','binary','-j','.qa_offsets',str(obj),str(raw)],check=True)
    values=struct.unpack('<'+'I'*len(expressions),raw.read_bytes())
    answer=dict(zip(expressions,values))
    (out/'provenance.json').write_text(json.dumps(dict(source_commit=commit,
        source_sha256=files,unit_sha256=sha(unit),command=command,offsets=answer),indent=2)+'\n')
    return answer


class Journey:
    def __init__(self,bundle,out):
        self.bundle,self.out=Path(bundle).resolve(),Path(out).resolve()
        self.out.mkdir(parents=True,exist_ok=True)
        self.harness_sha256=sha(__file__)
        (self.out/'review-harness.py').write_bytes(Path(__file__).read_bytes())
        self.run=NativeRun(self.bundle,self.out)
        native_keys=self.run.keys
        def observed_keys(keys,count=1,record=False):
            before=None if self.run.c is None else P.r32(self.run.c,P.sym('gFrame'))
            result=native_keys(keys,count,record)
            self.run.inputs[-1]['native_frame_counter_initial']=before
            self.run.inputs[-1]['native_frame_counter_final']=P.r32(self.run.c,P.sym('gFrame'))
            return result
        self.run.keys=observed_keys
        self.extra=extra_abi(self.bundle,self.out/'private-abi',self.out/'abi/headers')
        self.checks=[];self.errors=[];self.scope_complete=False
        self.movie=[];self.stage_log=[]
        symbols=subprocess.check_output(['arm-none-eabi-nm','-an',str(self.bundle/'bartgame.elf')],text=True)
        values={}
        for line in symbols.splitlines():
            m=re.fullmatch(r'([0-9a-f]+) [a-zA-Z] (\S+)',line)
            if m:values.setdefault(m[2],[]).append(int(m[1],16))
        self.plan_addr=self.unique(values,'sPlan')
        self.r_addr=B.section('.ewram_bss.regional_events')
        self.s_addr=B.section('.ewram_bss.handoff_runtime')
        self.puzzle_addr=self.unique(values,'sPuzzlePool')
        self.initial=None
        maptext=(self.bundle/'bartgame.map').read_text()
        self.gear={}
        for field in ('sList','sCount','sCursor'):
            matches=re.findall(r'\.bss\.'+field+r'\s+0x([0-9a-f]+)\s+0x[0-9a-f]+\s+build/gear_menu\.o',maptext)
            if len(matches)!=1:raise RuntimeError(('ambiguous frozen Satchel symbol',field,matches))
            self.gear[field]=int(matches[0],16)
        self.defs={n:int(v) for n,v in re.findall(r'^#define\s+(\w+)\s+(\d+)\s*$',(self.bundle/'assets.h').read_text(),re.M)}

    @staticmethod
    def unique(values,name):
        found=values.get(name,[])
        if len(found)!=1:raise ValueError((name,found))
        return found[0]

    @property
    def c(self):return self.run.c

    def check(self,name,ok,detail=None):
        self.checks.append(dict(name=name,passed=bool(ok),detail=detail))
        print(('PASS ' if ok else 'FAIL ')+name,flush=True)
        return bool(ok)

    def read(self,address,n):return bytes(P.r8(self.c,address+i) for i in range(n))

    def quest(self):
        q=P.sym('gHandoffState')+self.run.abi['handoff_quest'];d={}
        for f in QUEST_FIELDS:
            a=q+self.extra['quest_'+f]
            d[f]=P.r16(self.c,a) if f in QUEST_WORDS else P.r8(self.c,a)
        return d

    def plans(self):
        return [{f:P.r8(self.c,self.plan_addr+i*self.extra['plan_size']+self.extra['plan_'+f])
                 for f in PLAN_FIELDS} for i in range(50)]

    def plan(self,site):
        return next((p for p in self.plans() if site in (p['field_site'],p['interior_site'])),None)

    def private(self,field,word=False):
        prefix,name=field.split('_',1);address=(self.r_addr if prefix=='r' else self.s_addr)+self.extra[field]
        return P.r16(self.c,address) if word else P.r8(self.c,address)

    def points(self):
        n=self.private('r_point_count');a=self.r_addr+self.extra['r_points']
        return [(P.r8(self.c,a+2*i),P.r8(self.c,a+2*i+1)) for i in range(n)]

    def start(self,seed,choices=(0,1,2)):
        self.run.start(seed)
        self.opening_choices=self.run.finish_draft(DraftPreferences(self.run) if choices=='funds' else choices)
        self.run.dismiss();self.run.keys([],3)
        self.initial=self.run.snapshot();actual=P.r32(self.c,P.sym('gGame')+self.run.abi['game_seed'])
        if seed==0 or actual!=seed:raise RuntimeError(('native title seed differs from requested positive seed',seed,actual))
        self.check('three opening gifts chosen with real input',self.initial['draft']['state']==2,self.initial)
        return self.initial

    def modal(self):
        self.run.dismiss()
        if self.run.snapshot()['state']==6:return
        self.run.settle()

    def nav(self,x,y,face=0):
        """Only position/facing; never force health, action, z or immunity."""
        address=P.sym('gActors')
        def w32(a,v):P.w16(self.c,a,v&65535);P.w16(self.c,a+2,(v>>16)&65535)
        before=self.run.snapshot()
        w32(address+8,x<<16);w32(address+12,y<<16);P.w8(self.c,address+7,face)
        self.run.fixtures.append(dict(kind='hero position/facing navigation',x=x,y=y,
                                     face=face,before=before))

    def wait_normal(self,limit=240):
        for _ in range(limit):
            v=self.run.snapshot()
            if v['health'][0]==0:raise RuntimeError('hero died; no health restoration fixture is permitted')
            if v['state']==1 and v['actor']['state'] in (0,11) and not v['text']:return
            if v['text']:self.run.dismiss()
            else:self.run.keys([],1)
        raise RuntimeError('hero did not recover to ordinary control')

    def request_room(self,area,cell,node=None):
        """Isolated-case fixture: use the existing normal fade/load path."""
        before=self.run.snapshot()
        for name,value in [('sNextArea',area),('sNextCell',cell),('sNextSide',2),('sTransPhase',0)]:
            P.w8(self.c,B.static(name),value)
        if area==3:
            for name,value in [('sCreamNextNode',cell*2 if node is None else node),('sCreamNextFacing',0),('sCreamDropRows',0)]:P.w8(self.c,B.static(name),value)
            for name in ('sCreamNextX','sCreamNextY'):P.w16(self.c,B.static(name),65535)
        P.w8(self.c,P.sym('gGame'),2)
        self.run.fixtures.append(dict(kind='ordinary regional room-load request for isolated quest',area=area,cell=cell,node=node,before=before))
        self.run.settle(area);self.run.keys([],3);self.run.dismiss()

    def drive(self,key,predicate,limit=500,record=False):
        images=[]
        for i in range(limit):
            images.extend(self.run.keys(key,1,record=record and i%4==0))
            if predicate():break
        self.run.keys([],2)
        if record:self.movie.extend(images)
        return predicate()

    def area(self):return self.run.snapshot()['area']
    def cell(self):return self.run.snapshot()['cell']

    def enter_region(self,area):
        if self.area()==area:return
        if self.area()!=0:self.return_hub()
        self.wait_normal()
        self.nav(152 if area==1 else 312,62 if area==1 else 94,0)
        self.drive('UP',lambda:self.area()==area and self.run.snapshot()['state']==1,600)
        self.run.settle(area);self.run.dismiss()
        if self.area()!=area:raise RuntimeError('ordinary Drain ladder failed')

    def forest_route(self,target):
        a=self.run.abi;W=P.sym('gWorld');base=a['world_cells'];size=a['cell_size']
        start=self.cell();q=deque([start]);prev={start:None}
        while q:
            cell=q.popleft()
            if cell==target:break
            opened=P.r8(self.c,W+base+cell*size+a['cell_opened'])
            for side,(dx,dy) in enumerate(((0,-1),(1,0),(0,1),(-1,0))):
                gate=P.r8(self.c,W+base+cell*size+a['cell_gate']+side)
                x,y=cell%5+dx,cell//5+dy
                if not(0<=x<5 and 0<=y<5) or gate==0:continue
                if not self.forest_gate_available(cell,side,gate,opened):continue
                nxt=y*5+x
                if nxt not in prev:prev[nxt]=(cell,side);q.append(nxt)
        if target not in prev:raise RuntimeError(('target is not currently admitted',start,target))
        route=[];cell=target
        while prev[cell] is not None:
            frm,side=prev[cell];route.append((frm,side));cell=frm
        return list(reversed(route))

    def trial_facts(self):
        w=P.sym('gWorld');a=self.run.abi;result=[]
        for i in range(3):
            cell=P.r8(self.c,w+self.extra['world_key_cell']+i)
            flags=P.r8(self.c,w+a['world_cells']+cell*a['cell_size']+a['cell_flags'])
            mystery=P.r8(self.c,w+self.extra['world_myst_flags']+cell)
            result.append(dict(index=i,cell=cell,claimed=bool(flags&8),won=bool(mystery&4),
                gate_cell=P.r8(self.c,w+self.extra['world_gate_cell']+i),
                gate_side=P.r8(self.c,w+self.extra['world_gate_side']+i)))
        return result

    def forest_gate_available(self,cell,side,gate,opened):
        for fact in self.trial_facts():
            frm,d=fact['gate_cell'],fact['gate_side'];to=frm+(-5,1,5,-1)[d]
            if (cell,side) in ((frm,d),(to,(d+2)&3)) and not(fact['won'] and fact['claimed']):return False
        if gate in (1,2) or opened&(1<<side):return True
        items=self.run.u8('gPl',self.run.abi['player_items'])
        return (gate==3 and items&2) or (gate==4 and items&4) or (gate==6 and items&8) or (gate==5 and self.run.u8('gPl',6)>0)

    def equip(self,item,button='A'):
        """Select an actually owned item in the ordinary real Satchel UI."""
        self.wait_normal();self.run.tap('START',5);self.run.tap('SELECT',5)
        self.run.keys([],12);defs=P.sym('gLegacyItemDefs')
        inv=list(self.read(self.gear['sList'],P.r8(self.c,self.gear['sCount'])))
        if item not in inv:raise RuntimeError(('requested Satchel item is not genuinely owned',item,inv))
        for _ in range(inv.index(item)):self.run.tap('RIGHT',6)
        cursor=P.r8(self.c,self.gear['sCursor'])
        if cursor!=inv.index(item):raise RuntimeError(('real Satchel cursor did not reach selected item',cursor,item,inv))
        self.run.tap(button,6);self.run.tap('START',10);self.wait_normal()
        expected=P.r8(self.c,defs+item*self.extra['ldef_size']+self.extra['ldef_equip'])
        slot={'A':0,'B':1,'L':2}[button];actual=self.run.u8('gPl',self.run.abi['player_equip']+slot)
        if actual!=expected:raise RuntimeError(('real Satchel equipment assignment differs',item,expected,actual))
        self.stage_log.append(dict(kind='real Satchel assignment',item=item,button=button,possessions=inv,equip=actual,state=self.run.snapshot()))

    def go_forest(self,target):
        self.enter_region(1)
        for frm,side in self.forest_route(target):
            self.wait_normal();x,y,key=C.door_inside(side)
            base=P.sym('gWorld')+self.run.abi['world_cells']+frm*self.run.abi['cell_size']
            gate=P.r8(self.c,base+self.run.abi['cell_gate']+side)
            opened=P.r8(self.c,base+self.run.abi['cell_opened'])&(1<<side)
            if not opened and gate in (3,4,6):self.equip({3:7,4:15,6:20}[gate])
            self.nav(x,y,side)
            if not opened and gate in (2,3,4,6):
                self.run.keys(key,14)
                if gate==2:self.run.tap('B',20)
                elif gate==3:
                    # Charge/release a genuine impact bomb toward the wall,
                    # retreat while it lands so blast damage is avoidable.
                    self.run.keys('A',30);self.run.keys([],2)
                    opposite={'UP':'DOWN','DOWN':'UP','LEFT':'RIGHT','RIGHT':'LEFT'}[key]
                    self.run.keys(opposite,24);self.run.keys([],36)
                elif gate==4:self.run.tap('A',32)
                else:self.run.keys([key,'A'],2);self.run.keys(key,60)
            for attempt in range(3):
                if self.run.snapshot()['state']==2:self.run.settle(1)
                if self.cell()!=frm:break
                self.drive(key,lambda:self.run.snapshot()['state']!=1 or self.cell()!=frm,180)
                if self.run.snapshot()['state']==2:self.run.settle(1)
                if self.cell()!=frm:break
                if self.run.snapshot()['text']:self.run.dismiss()
                self.run.tap('B',20)
            if self.cell()!=frm+(-5,1,5,-1)[side]:raise RuntimeError(('admitted border did not cross',frm,side,gate,self.run.snapshot()))
            self.stage_log.append(dict(kind='real Forest border',origin=frm,side=side,gate=gate,arrival=self.run.snapshot()))

    def cream_edges(self):
        a=self.run.abi;w=P.sym('gCreamWorld');result=[]
        for n in range(50):
            degree=P.r8(self.c,w+a['cream_degree']+n);row=[]
            for i in range(degree):
                p=w+a['cream_edges']+(n*6+i)*a['cream_edge_size']
                row.append(dict(zip(('target','kind','require','flags'),self.read(p,4))))
            result.append(row)
        return result

    def cream_tokens(self):
        bits=self.run.u8('gPl',self.run.abi['player_items'])
        owned=self.run.snapshot()['inventory']['owned']
        return (1 if bits&2 else 0)|(2 if bits&4 else 0)|(4 if bits&8 and owned[0]&(1<<18) else 0)

    def use_cream_gate(self,node,index,edge):
        required=edge['require'];opened=bool(self.run.u8('gCreamOpenEdges',node)&(1<<index))
        if not required or opened or required==7:return
        if required==4:return # pit: real cape jump performed by the edge driver
        room=P.sym('gCreamRoom');cx=P.r8(self.c,room+self.extra['cream_climb_x']);terrace=node&1;wy=6 if terrace else 19;other=edge['target']//2
        if edge['kind']==1:
            left=other%5<(node//2)%5;px,py,face=(40 if left else 472),wy*16+14,(3 if left else 1)
        elif edge['kind']==4:px,py,face=112,(wy+1)*16+14,0
        elif edge['kind']==2:
            gy=P.r8(self.c,room+self.extra['cream_lower_top']+cx) if other==node//2 else 2
            px,py,face=cx*16+16,(gy+1)*16+14,0
        else:
            gx=27 if edge['flags']&1 else 10 if terrace else cx
            gy=min(P.r8(self.c,room+self.extra['cream_upper_bottom']+gx),P.r8(self.c,room+self.extra['cream_upper_bottom']+gx+1)) if terrace else 22
            px,py,face=gx*16+16,(gy-1)*16+14,2
        self.equip(15 if required&2 else 7)
        for attempt in range(3):
            self.wait_normal();self.nav(px,py,face);self.run.tap('A',35)
            if self.run.u8('gCreamOpenEdges',node)&(1<<index):break
        after=self.run.snapshot();self.check('real earned tool clears a generated Cream route barrier',bool(self.run.u8('gCreamOpenEdges',node)&(1<<index)),dict(node=node,index=index,edge=edge,state=after))
        if not(self.run.u8('gCreamOpenEdges',node)&(1<<index)):raise RuntimeError(('real Cream gate use failed',node,index,edge,after))

    def go_cream(self,target):
        self.enter_region(3);edges=self.cream_edges();start=self.run.u8('gCreamNode');tokens=self.cream_tokens()
        prev={start:None};q=deque([start])
        while q:
            n=q.popleft()
            if n==target:break
            for i,e in enumerate(edges[n]):
                if e['require']&tokens!=e['require'] or e['target'] in prev:continue
                prev[e['target']]=(n,i);q.append(e['target'])
        if target not in prev:raise RuntimeError(('Cream target not currently admitted',start,target,tokens))
        route=[];n=target
        while prev[n] is not None:
            frm,i=prev[n];route.append((frm,i));n=frm
        for n,i in reversed(route):
            e=edges[n][i];self.wait_normal();room=P.sym('gCreamRoom');cx=P.r8(self.c,room+self.extra['cream_climb_x']);upper=room+self.extra['cream_upper_bottom'];t=n&1
            self.use_cream_gate(n,i,e)
            if e['require']==4:self.equip(20)
            if e['kind']==1:
                left=e['target']//2%5<n//2%5;self.nav(20 if left else 492,(6 if t else 19)*16+14,3 if left else 1);key='LEFT' if left else 'RIGHT'
            elif e['kind']==2:
                y=min(P.r8(self.c,upper+cx),P.r8(self.c,upper+cx+1))
                self.nav((cx+1)*16+8,(y+1)*16+7 if e['target']//2==n//2 else 24,0);key='UP'
            elif e['kind']==3:
                x=27 if e['flags']&1 else 10 if t else cx;y=min(P.r8(self.c,upper+x),P.r8(self.c,upper+x+1)) if t else 22
                self.nav(x*16+16,y*16+12,2);key='DOWN'
            else:self.nav(7*16,((6 if t else 19)+1)*16+14,0);key='UP'
            if e['require']==4:self.run.keys([key,'A'],2);self.run.keys(key,48)
            self.drive(key,lambda:self.run.u8('gCreamNode')==e['target'] and self.run.snapshot()['state']==1,700)
            self.run.settle(3);self.run.dismiss()
            if self.run.u8('gCreamNode')!=e['target']:raise RuntimeError(('actual Cream edge stalled',n,i,e,self.run.snapshot()))

    def go_plan(self,plan):
        if plan['area']==1:self.go_forest(plan['cell'])
        else:self.go_cream(plan['cell']*2+plan['terrace'])

    def tile_type(self,x,y):
        a=self.run.abi;r=P.sym('gRoom');mt=P.r16(self.c,r+a['room_ground']+(y*32+x)*2)
        return P.r8(self.c,P.sym('metatile_type')+mt)

    def return_hub(self):
        if self.area()==4:self.leave_interior()
        if self.area()==1:
            entry=P.r8(self.c,P.sym('gWorld')+self.run.abi['world_entry']);self.go_forest(entry)
            tiles=[(x,y) for y in range(24) for x in range(32) if self.tile_type(x,y)==21]
            if not tiles:raise RuntimeError('entry stairs not present')
            x,y=tiles[0];self.wait_normal();self.nav(x*16+8,y*16+8,2);self.run.keys([],2);self.run.settle(0)
        elif self.area()==3:
            goal=P.r8(self.c,P.sym('gCreamWorld')+self.run.abi['cream_entry']);self.go_cream(goal)
            self.wait_normal();self.nav(400,350,0);self.run.tap('A');self.run.settle(0)
        self.run.dismiss()

    def enter_interior(self,plan):
        self.go_plan(plan);v=self.run.snapshot();point=v['spots']['door']
        if not v['spots']['flags']['door']:raise RuntimeError('planned regional entrance was not physically placed')
        self.wait_normal();self.nav(point[0]*16+8,point[1]*16+14,0);self.run.tap('A',4);self.run.settle(4);self.run.dismiss()
        site=self.private('s_site');self.check('ordinary regional entrance reaches its dealt site',site==plan['interior_site'],dict(plan=plan,site=site,arrival=self.run.snapshot()))

    def leave_interior(self):
        self.run.dismiss();self.wait_normal();self.nav(16*16+8,21*16+14,2)
        self.drive('DOWN',lambda:self.area()!=4 and self.run.snapshot()['state']==1,400)
        self.run.settle();self.run.dismiss()

    def fight(self,finished,limit=1600,owned=False):
        for turn in range(limit):
            if finished():return True
            v=self.run.snapshot()
            if v['health'][0]==0:raise RuntimeError('hero died during genuine combat')
            if v['text']:self.run.dismiss();continue
            if v['actor']['state']!=0:self.run.keys([],3);continue
            enemies=[P.actor(self.c,i) for i in range(1,96) if P.actor(self.c,i)['kind']==2 and (not owned or P.r8(self.c,self.r_addr+self.extra['r_owned']+i))]
            if turn%100==0:self.stage_log.append(dict(kind='combat observation',turn=turn,owned_component_only=owned,state=v,quest=self.quest(),enemies=enemies,wave_site=self.private('r_wave_site'),wave=self.run.u8('gHandoffState',self.run.abi['handoff_wave']+self.private('r_wave_site')),remaining=self.run.u16('gHandoffState',self.run.abi['handoff_remaining']+2*self.private('r_wave_site'))))
            if not enemies:
                if owned:
                    giver=self.read(self.r_addr+self.extra['r_giver'],2);self.nav(giver[0]*16+8,giver[1]*16+14,0)
                self.run.keys([],12);continue
            enemy=enemies[turn%len(enemies)];approach=None
            for candidate in range(3):
                attempt=C.trial_attack_position(self.c,enemy,turn+candidate)
                if attempt is None:continue
                xx,yy,kk=attempt;spot=v['spots']['door']
                if owned:
                    at=(yy//16)*32+xx//16
                    if not(P.r8(self.c,self.r_addr+self.extra['r_component']+(at>>3))&(1<<(at&7))):continue
                if self.area() in (1,3) and v['spots']['flags']['door'] and kk=='UP' and abs(xx-(spot[0]*16+8))<26 and spot[1]*16-48<yy<spot[1]*16+56:continue
                approach=attempt;break
            if approach is None:self.run.keys([],8);continue
            x,y,key=approach;face={'UP':0,'RIGHT':1,'DOWN':2,'LEFT':3}[key]
            self.nav(x,y,face);self.run.keys(key,1);self.run.tap('B',15)
        return finished()

    def solve_board(self):
        index=self.run.u16('gHandoffPuzzleIndex');p=self.puzzle_addr+index*self.extra['puzzle_size']
        moves=self.read(p+self.extra['puzzle_solution'],P.r8(self.c,p+self.extra['puzzle_length']))
        x0,y0=self.private('s_board_x'),self.private('s_board_y')
        self.stage_log.append(dict(kind='read-only certified puzzle witness followed through real pushes',puzzle_index=index,board_origin=[x0,y0],moves=list(moves)))
        for encoded in moves:
            which,d=divmod(encoded,4);cell=self.run.u8('gHandoffBoardBlocks',which);dx=(0,1,0,-1)[d];dy=(-1,0,1,0)[d]
            self.wait_normal();self.nav((x0+cell%5-dx)*16+8,(y0+cell//5-dy)*16+14,d)
            self.run.tap('A',6)
        return bool(self.run.u8('gHandoffBoardSolved'))

    def finish_quest(self,kind):
        if kind==1:
            for x,y in self.points():
                if self.quest()['state']==3:break
                self.wait_normal();self.nav(x*16+8,y*16+14,0);self.run.tap('A',6)
        elif kind==2:self.fight(lambda:self.quest()['state']==3,1200,owned=True)
        elif kind==3:
            q=self.quest()
            if q['mode']==0:
                for _ in range(6):
                    if self.quest()['state']==3:break
                    for x,y in self.points():
                        self.wait_normal();self.nav(x*16+8,y*16+14,0);self.run.keys([],4)
                        if self.quest()['state']==3:break
                    self.run.keys([],30)
            elif q['mode']==1:
                self.wait_normal();self.nav(q['cargo_x'],q['cargo_y']+22,0);self.run.tap('B',20)
            else:raise RuntimeError('dig Scavenger mode needs real Mitts assignment reviewer support')
        elif kind==4:
            self.walk_stealth()
        elif kind==5:
            q=self.quest();self.wait_normal();self.nav(q['cargo_x'],q['cargo_y'],0);self.run.tap('A',18)
            if getattr(self,'carry_reentry',False):self.carry_reentry_control()
            for wave in (1,2):
                q=self.quest()
                if not q['cargo_held']:
                    self.wait_normal();self.nav(q['cargo_x'],q['cargo_y'],0);self.run.tap('A',18)
                q=self.quest();self.wait_normal();self.nav(q['receiver_x'],q['receiver_y'],0);self.run.keys([],3)
                if self.quest()['wave']<wave:
                    giver=self.read(self.r_addr+self.extra['r_giver'],2)
                    x,y=max(self.points(),key=lambda p:abs(p[0]-giver[0])+abs(p[1]-giver[1]))
                    self.nav(x*16+8,y*16+14,0);self.run.keys([],3)
                self.check('actual cargo ambush %d remains to be fought'%wave,self.quest()['wave']==wave and self.quest()['count']>0,dict(quest=self.quest(),state=self.run.snapshot()))
                # Put the real pot down through an actual throw before sword
                # combat. Its normal landing/fallback anchor stays recoverable.
                if self.quest()['cargo_held']:
                    x,y=self.points()[0];self.wait_normal();self.nav(x*16+8,y*16+14,0);self.run.tap('A',30)
                self.fight(lambda:self.quest()['count']==0 and not any(P.actor(self.c,i)['kind']==2 and P.r8(self.c,self.r_addr+self.extra['r_owned']+i) for i in range(1,96)),1200,owned=True)
                q=self.quest();self.wait_normal();self.nav(q['cargo_x'],q['cargo_y'],0);self.run.tap('A',18)
            q=self.quest();self.wait_normal();self.nav(q['receiver_x'],q['receiver_y'],0);self.run.tap('A',12)
        elif kind==6:
            q=self.quest();self.return_hub();self.courier_checkpoint();self.enter_region(q['target_area'])
            v=self.run.snapshot();x,y=v['spots']['npc']
            if not v['spots']['flags']['npc']:
                x=P.r8(self.c,self.r_addr+self.extra['r_giver']);y=P.r8(self.c,self.r_addr+self.extra['r_giver']+1)
            self.wait_normal();self.nav(x*16+8,y*16+14,0);self.run.tap('A',12)
        else:self.solve_board();self.run.keys([],3)
        self.run.dismiss();return self.quest()['state']==3

    def carry_reentry_control(self):
        q=self.quest();self.wait_normal();self.nav(q['receiver_x'],q['receiver_y'],0);self.run.keys([],3)
        started=self.quest();self.check('carrying the pot starts a real unresolved first ambush',started['state']==2 and started['wave']==1 and started['count']>0,started)
        # Throw on a real dry field point. Walk the actual regional borders
        # to the Drain stairs and return through its ordinary wall ladder.
        x,y=self.points()[0];self.wait_normal();self.nav(x*16+8,y*16+14,2);self.run.tap('A',30)
        plan=self.plan(32+(25 if q['origin_area']==3 else 0)+q['origin_cell'])
        before_leave=self.quest();self.return_hub();self.go_plan(plan);returned=self.quest()
        self.check('ordinary exit and re-entry preserve the unresolved cargo ambush',before_leave['count']>0 and returned['state']==2 and returned['wave']==1 and returned['count']>0,dict(before=before_leave,after=returned,state=self.run.snapshot()))
        self.wait_normal();self.nav(returned['cargo_x'],returned['cargo_y'],0);self.run.tap('A',18)
        q=self.quest();self.nav(q['receiver_x'],q['receiver_y'],0);self.run.tap('A',4);self.run.image('carry-unresolved-refuses-delivery');self.run.dismiss()
        denied=self.quest();self.check('returning with unresolved enemies cannot deliver the cargo',denied['state']==2 and denied['count']>0 and denied['wave']==1,dict(quest=denied,state=self.run.snapshot()))

    def walk_stealth(self):
        """Walk the field from its giver with time-aware sight-cone routing.

        Observation predicts ordinary input; no clock, watcher or position is
        changed after the giver interaction. The visible source cone formula
        and actual Room collision determine the route, including waits.
        """
        self.wait_normal();q=self.quest();v=self.run.snapshot();start=(v['actor']['x'],v['actor']['y'])
        goal=(q['receiver_x'],q['receiver_y']);watchers=[(x*16+8,y*16+14) for x,y in self.points()[:3]]
        w=self.run.u8('gRoom',self.run.abi['room_w'])*16;h=self.run.u8('gRoom',self.run.abi['room_h'])*16
        solid=self.read(P.sym('gRoom')+self.run.abi['room_solid'],4096)
        def blocked(x,y):return x<0 or y<0 or x>=w or y>=h or bool(solid[(y//8)*64+x//8])
        def safe_feet(x,y):
            if any(blocked(xx,yy) for xx in (x-5,x+4) for yy in (y-8,y-1)):return False
            return self.tile_type(x//16,(y-4)//16) in (0,12,15,19,20,25)
        def watched(x,y,clock):
            for i,(wx,wy) in enumerate(watchers):
                face=(clock//120+i)&3;dx,dy=x-wx,y-wy;vx,vy=((0,-1),(1,0),(0,1),(-1,0))[face]
                forward=dx*vx+dy*vy;side=dx*vy-dy*vx
                if forward<4 or forward>76 or abs(side)>forward//2+6:continue
                n=max(abs(dx),abs(dy))//8+1
                if all(not blocked(wx+int(dx*j/n),wy+int(dy*j/n)) for j in range(1,n)):return True
            return False
        def heuristic(x,y):return (max(0,abs(x-goal[0])-15)+max(0,abs(y-goal[1])-15))//5
        clock=P.r32(self.c,self.s_addr+self.extra['s_clock']);phase=clock%480
        initial=(start[0],start[1],phase);front=[(heuristic(*start),0,initial)];best={initial:0};prev={initial:None};end=None
        actions=(('UP',0,-1),('RIGHT',1,0),('DOWN',0,1),('LEFT',-1,0),(None,0,0))
        limit=max(1,q['timer']//4-2)
        while front:
            _,cost,state=heapq.heappop(front)
            if cost!=best[state]:continue
            x,y,t=state
            if abs(x-goal[0])<=15 and abs(y-goal[1])<=15:end=state;break
            if cost>=limit:continue
            for key,dx,dy in actions:
                nx,ny=x+dx*5,y+dy*5;nt=(t+4)%480
                if not safe_feet(nx,ny):continue
                if any(watched(int(x+dx*1.25*k),int(y+dy*1.25*k),(t+k)%480) for k in range(1,5)):continue
                nxt=(nx,ny,nt);nc=cost+1
                if nc>=best.get(nxt,1<<30):continue
                best[nxt]=nc;prev[nxt]=(state,key);heapq.heappush(front,(nc+heuristic(nx,ny),nc,nxt))
        if end is None:raise RuntimeError(('no safe timed watcher route',start,goal,watchers,q))
        route=[];state=end
        while prev[state] is not None:
            old,key=prev[state];route.append(key);state=old
        route.reverse();walk_trace=[]
        for key in route:
            old=self.run.snapshot()['actor'];dx,dy={'UP':(0,-5),'DOWN':(0,5),'LEFT':(-5,0),'RIGHT':(5,0),None:(0,0)}[key]
            self.movie.extend(self.run.keys([] if key is None else key,4,record=True))
            walk_trace.append(self.run.snapshot())
            if self.quest()['state']!=2:break
            actual=self.run.snapshot()['actor']
            if actual['state']!=0 or abs(actual['x']-old['x']-dx)>2 or abs(actual['y']-old['y']-dy)>2:break
        self.stage_log.append(dict(kind='continuous stealth walk',start=start,goal=goal,
                                   watchers=watchers,clock=clock,planned_actions=route,trace=walk_trace))
        if self.quest()['state']==2:
            self.stealth_replans=getattr(self,'stealth_replans',0)+1
            if self.stealth_replans<12:self.walk_stealth()

    def courier_checkpoint(self):
        """Save via the real Drain Trophy, cold boot exact produced bytes."""
        self.wait_normal();self.nav(416,254,0);self.run.tap('A',12)
        if self.run.snapshot()['service_menu']['active']!=5:raise RuntimeError('real Trophy service did not open for courier checkpoint')
        self.run.tap('DOWN');self.run.tap('DOWN');self.run.tap('A',12)
        if self.run.snapshot()['service_menu']['active']!=9:raise RuntimeError('Trophy difficulty service did not open')
        self.run.tap('A',12);self.run.dismiss();self.wait_normal()
        before=self.run.snapshot();q=self.quest();saved=self.read(0x0e000000,32768)
        (self.out/'courier-checkpoint-private.bin').write_bytes(saved);self.run.image('courier-real-checkpoint')
        private=self.out/'cold-continue';private.mkdir(exist_ok=True);rom=private/'bartgame.gba'
        shutil.copy2(self.bundle/'bartgame.gba',rom);c=mgba.core.load_path(str(rom));c.bg_video=mgba.image.Image(240,160);c.set_video_buffer(c.bg_video);c.reset()
        for i,value in enumerate(saved):P.w8(c,0x0e000000+i,value)
        self.run.fixtures.append(dict(kind='cold Continue restores exact genuine SRAM bytes',bytes=len(saved),sha256=hashlib.sha256(saved).hexdigest()))
        self.run.c=c;self.run.keys([],45);self.run.tap('START',6);self.run.settle(0);self.run.dismiss();self.wait_normal()
        after=self.run.snapshot();self.check('active cross-region courier survives actual save and cold Continue' if q['kind']==6 else 'pending chain survives actual save and cold Continue',self.quest()==q and before['inventory']==after['inventory'] and after['starting_draft']==0 and after['draft']['state']==2,dict(before=before,after=after,quest_before=q,quest_after=self.quest(),sram_sha256=hashlib.sha256(saved).hexdigest()))
        self.run.image('courier-cold-continue')

    def tiles(self,kind,overlay=False):
        a=self.run.abi;room=P.sym('gRoom');base=room+a['room_overlay' if overlay else 'room_ground']
        result=[]
        for y in range(self.run.u8('gRoom',a['room_h'])):
            for x in range(self.run.u8('gRoom',a['room_w'])):
                mt=P.r16(self.c,base+(y*32+x)*2)&65535
                if mt!=65535 and P.r8(self.c,P.sym('metatile_type')+mt)==kind:result.append((x,y))
        return result

    def tiles_mt(self,name,overlay=False):
        target=self.defs[name];a=self.run.abi;r=P.sym('gRoom');base=r+a['room_overlay' if overlay else 'room_ground']
        return [(x,y) for y in range(self.run.u8('gRoom',a['room_h'])) for x in range(self.run.u8('gRoom',a['room_w'])) if P.r16(self.c,base+(y*32+x)*2)&65535==target]

    def earn_trial(self,index):
        fact=self.trial_facts()[index];cell=fact['cell'];self.go_forest(cell)
        mouths=self.tiles(24)
        if not mouths:raise RuntimeError(('required trial mouth missing',index,cell))
        tx,ty=mouths[0];self.wait_normal();self.nav(tx*16+8,(ty+1)*16+14,0)
        self.drive('UP',lambda:self.area()==2 and self.run.snapshot()['state']==1,180)
        self.run.settle(2);self.run.dismiss()
        if self.area()!=2:raise RuntimeError(('ordinary required trial mouth failed',index,cell,self.run.snapshot()))
        kind=P.r8(self.c,P.sym('gWorld')+self.extra['world_myst']+cell)&15
        self.run.image('trial-%d-enter'%index)
        if kind==8:
            for tx,ty in self.tiles_mt('MT_MYST_SWITCH',True):
                self.wait_normal();self.nav(tx*16+8,ty*16+12,0);self.run.keys([],8)
        elif kind in (5,7):
            if not self.fight(lambda:bool(self.tiles(18)),1800):raise RuntimeError(('genuine required trial combat unfinished',index,kind,self.run.snapshot()))
        else:raise RuntimeError(('unexpected original required trial kind',index,kind))
        chests=self.tiles(18)
        if not chests:raise RuntimeError(('required trial reward chest did not materialize',index,self.trial_facts()))
        tx,ty=chests[0];self.wait_normal();self.nav(tx*16+8,(ty+1)*16+14,0);self.run.keys('UP',24)
        self.run.keys([],45);self.run.dismiss();self.wait_normal();self.run.image('trial-%d-earned'%index)
        self.check('original Forest trial %d genuinely won and claimed'%(index+1),all(self.trial_facts()[index][k] for k in ('won','claimed')),dict(kind=kind,facts=self.trial_facts(),state=self.run.snapshot()))
        exits=self.tiles(24)
        if not exits:raise RuntimeError('old trial return mouth absent')
        tx,ty=max(exits,key=lambda xy:xy[1]);self.nav(tx*16+8,ty*16+14,2)
        self.drive('DOWN',lambda:self.area()==1 and self.run.snapshot()['state']==1,180)
        self.run.settle(1);self.run.dismiss()
        if self.area()!=1 or self.cell()!=cell:raise RuntimeError(('trial did not return to actual origin',index,self.run.snapshot()))
        self.stage_log.append(dict(kind='original trial earned',index=index,event_kind=kind,facts=self.trial_facts(),state=self.run.snapshot()))

    def completed(self,site):
        return bool(P.r8(self.c,P.sym('gHandoffState')+self.run.abi['handoff_completed']+(site>>3))&(1<<(site&7)))

    def finish_event(self,plan):
        kind=plan['event_kind'];self.enter_interior(plan);site=plan['interior_site'];before=self.run.snapshot()
        self.run.image('event-%d-enter'%site)
        if kind in (1,3,6):
            self.wait_normal();self.nav(264,190,0);self.run.tap('A',12)
        elif kind in (2,4,14,15,23,24,25):
            self.fight(lambda:self.completed(site),2400)
        elif kind in (10,11):self.solve_board();self.run.keys([],3)
        elif kind==9:
            for i in range(4):self.wait_normal();self.nav((9+i*4)*16+8,12*16+14,0);self.run.keys([],4)
        elif kind==5:
            for i in range(6):
                if self.completed(site):break
                self.wait_normal();self.nav((7+(i%3)*8)*16+8,(7+(i//3)*8)*16+14,0);self.run.tap('A',6)
        elif kind==12:
            self.equip(15)
            for i in range(3):self.wait_normal();self.nav((8+i*8)*16+8,10*16+36,0);self.run.tap('A',32)
        else:raise RuntimeError(('unimplemented reviewer for real chain event family',kind,plan))
        self.run.dismiss();self.run.image('event-%d-result'%site)
        if not self.completed(site):raise RuntimeError(('actual chain event did not finish',plan,before,self.run.snapshot()))
        self.stage_log.append(dict(kind='real regional event completion',plan=plan,before=before,after=self.run.snapshot()))

    def chain_case(self,seed,earn_trials=True,guard=False):
        self.start(seed)
        if earn_trials:
            for i in range(3):self.earn_trial(i)
        for objective in range(3 if guard else 4):
            self.run.dismiss();self.wait_normal();self.run.keys([],34)
            before=self.run.snapshot();chain=before['chain'];frame_counter_before=P.r32(self.c,P.sym('gFrame'))
            if chain['step']!=objective or chain['state']!=1:raise RuntimeError(('next actual chain objective not active',objective,before,self.trial_facts()))
            plan=self.plan(chain['target'])
            if not plan:raise RuntimeError(('chain target is not actual regional content',chain))
            if chain['kind'] in (1,3):self.finish_event(plan)
            elif chain['kind']==2:
                self.go_plan(plan);self.fight(lambda:self.run.snapshot()['chain']['step']>objective,2000,owned=True)
            elif chain['kind']==4:
                self.go_plan(plan)
                if self.quest()['state'] not in (1,2):raise RuntimeError('chain expected actual active quest')
                self.finish_quest(self.quest()['kind'])
            elif chain['kind']==5:
                self.go_plan(plan);v=self.run.snapshot();x,y=v['spots']['cache'];self.wait_normal();self.nav(x*16+8,y*16+14,0);self.run.tap('A',12)
            else:raise RuntimeError(('unknown actual chain objective',chain))
            wait_frames=0
            for wait_frames in range(4000):
                next_chain=self.run.snapshot()['chain']
                if next_chain['step']==objective+1 and (objective==3 or next_chain['state']!=1 or (next_chain['kind'],next_chain['target'])!=(chain['kind'],chain['target'])):break
                self.run.keys([],1)
            trigger=next((entry for entry in reversed(self.run.inputs) if entry['initial']['chain']['step']==objective and entry['final']['chain']['step']==objective+1),None)
            self.stage_log.append(dict(reward_action_input=trigger,kind='actual objective handoff settled',objective=objective,physical_wait_frames=wait_frames,game_frame_counter_before=frame_counter_before,game_frame_counter_after=P.r32(self.c,P.sym('gFrame')),contract_item=self.run.u16('gHandoffState',self.extra['handoff_contract_item']),state=self.run.snapshot()))
            after=self.run.snapshot();self.check('real regional objective %d advances once'%(objective+1),after['chain']['step']==objective+1,dict(before=before,plan=plan,after=after))
            self.run.image('objective-%d-earned'%(objective+1))
            if after['chain']['step']!=objective+1:raise RuntimeError(('objective did not hand off',before,after))
            if objective<3 and self.area()==4:self.leave_interior()
        if guard:
            self.run.keys([],34);v=self.run.snapshot();facts=self.trial_facts()
            self.check('three early regional objectives cannot bypass the original trials',v['chain']['step']==3 and v['chain']['state']==0 and v['chain']['kind']==3 and v['chain']['target']==0 and v['state']==1 and not any(f['won'] or f['claimed'] for f in facts),dict(state=v,facts=facts))
            self.run.image('original-trials-still-required');self.return_hub();self.courier_checkpoint();self.scope_complete=all(c['passed'] for c in self.checks);return
        # Last boss created a tangible actor. Wait before moving onto the
        # element and establish that the four objectives alone did not win.
        before=self.run.snapshot();earth=[]
        for i in range(1,96):
            actor=P.actor(self.c,i)
            if actor['kind']==6 and actor['type']==22 and P.r8(self.c,P.sym('gActors')+64*i+48)==0x40:earth.append(actor)
        self.check('four objectives leave physical Earth pickup pending',before['state']==1 and before['chain']['step']==4 and before['chain']['state']==1 and len(earth)==1,dict(state=before,actors=earth))
        self.run.image('earth-waiting')
        if not earth:
            # The fixed visible native center is the source materialization
            # point; still check the real pickup inventory/state transition.
            x,y=(264,190) if self.area()==4 else tuple(v*16+d for v,d in zip(before['spots']['cache'],(8,14)))
        else:x,y=earth[0]['x'],earth[0]['y']
        self.wait_normal();self.nav(x,y,0);self.run.keys([],25);self.run.dismiss();self.run.image('earth-victory')
        after=self.run.snapshot();self.check('physical Earth Element pickup wins the new run path',after['state']==6 and after['chain']['state']==2,dict(before=before,after=after))
        if after['state']==6:self.new_run_after_chain_win()
        self.scope_complete=all(c['passed'] for c in self.checks)

    def new_run_after_chain_win(self):
        """Cold boot only the exact SRAM produced by the genuine Earth win."""
        saved=self.read(0x0e000000,32768);(self.out/'earth-victory-private.bin').write_bytes(saved)
        self.run.keys([],150);self.run.image('earth-victory-panel')
        private=self.out/'cold-after-win';private.mkdir(exist_ok=True);rom=private/'bartgame.gba';shutil.copy2(self.bundle/'bartgame.gba',rom)
        c=mgba.core.load_path(str(rom));c.bg_video=mgba.image.Image(240,160);c.set_video_buffer(c.bg_video);c.reset()
        for i,value in enumerate(saved):P.w8(c,0x0e000000+i,value)
        self.run.c=c;self.run.fixtures.append(dict(kind='cold boot from exact Earth-victory SRAM',bytes=len(saved),sha256=hashlib.sha256(saved).hexdigest()))
        self.run.keys([],45);has_save=P.r8(self.c,B.static('sTitleHasSave','game.o'))
        self.check('Earth victory retires the finished run on a cold title',has_save==0,dict(title_has_continue=has_save,sram_sha256=hashlib.sha256(saved).hexdigest()))
        self.run.tap('START',8)
        for _ in range(2400):
            v=self.run.snapshot()
            if v['draft']['state']==1 and v['starting_draft'] and v['service_menu']['active']==1:break
            if v['text']:self.run.dismiss()
            else:self.run.keys([],2)
        v=self.run.snapshot();owned=v['inventory']['owned']
        self.check('next play starts a fresh run and its three opening choices',v['area']==0 and v['draft']['state']==1 and v['draft']['round']==0 and v['chain']['step']==0 and not(owned[2]&15) and not any(f['won'] or f['claimed'] for f in self.trial_facts()),dict(state=v,new_seed=P.r32(self.c,P.sym('gGame')+self.run.abi['game_seed']),facts=self.trial_facts()))
        self.run.image('fresh-run-after-earth-victory')

    def choose_difficulty(self,difficulty):
        if self.area()!=0:raise RuntimeError('difficulty change must use actual Drain trophy')
        self.wait_normal();self.nav(416,254,0);self.run.tap('A',12)
        if self.run.snapshot()['service_menu']['active']!=5:raise RuntimeError('physical Trophy did not open')
        self.run.tap('DOWN');self.run.tap('DOWN');self.run.tap('A',12)
        for _ in range(difficulty):self.run.tap('DOWN',4)
        self.run.tap('A',12);self.run.dismiss();self.wait_normal()
        actual=self.run.u8('gHandoffState',self.extra['handoff_difficulty'])
        if actual!=difficulty:raise RuntimeError(('actual Trophy difficulty differs',difficulty,actual))

    def stakes_case(self,seed=7):
        self.start(seed,choices='funds');self.choose_difficulty(4)
        plan=next((p for p in self.plans() if p['quest_kind']==2),None)
        if not plan:raise RuntimeError('stakes case needs actual Hunt seed')
        self.request_room(plan['area'],plan['cell'],plan['cell']*2+plan['terrace'])
        x,y=self.run.snapshot()['spots']['npc'];self.wait_normal();self.nav(x*16+8,y*16+14,0);self.run.tap('A',4);self.run.image('stakes-announced');self.run.dismiss();self.run.keys([],2)
        accepted=self.quest();self.check('real regional quest announces and latches its difficulty stake',accepted['state']==2 and accepted['stake']==1 and accepted['difficulty']==4,accepted)
        self.request_room(0,0);self.choose_difficulty(12)
        changed=self.quest();self.check('changing run difficulty cannot raise an active quest stake',changed['state']==2 and changed['stake']==1 and changed['difficulty']==4,dict(active=changed,current_difficulty=self.run.u8('gHandoffState',self.extra['handoff_difficulty'])))
        before=self.run.snapshot();self.run.keys([],changed['timer']+4);after=self.run.snapshot()
        self.check('real timeout charges the originally announced stake exactly once',self.quest()['state']==4 and before['gilt']-after['gilt']==50 and before['health']==after['health'],dict(before=before,after=after,quest=self.quest()))
        self.run.keys([],180);again=self.run.snapshot();self.check('failed timed quest does not charge twice',after['gilt']==again['gilt'] and after['health']==again['health'],dict(after=after,again=again))
        self.run.image('stakes-real-failure');self.scope_complete=all(c['passed'] for c in self.checks)

    def discover(self,start_seed=1,count=96):
        """Read the actual native dealt plan; this is discovery, not success."""
        found={};all_seeds=[];target={(kind,area) for kind in range(1,8) for area in ((1,) if kind==7 else (1,3))}
        for seed in range(start_seed,start_seed+count):
            self.start(seed);quest_plans=[p for p in self.plans() if 1<=p['quest_kind']<=7]
            if len(quest_plans)!=1:raise RuntimeError(('new run did not deal exactly one regional quest',seed,quest_plans))
            plan=quest_plans[0]
            row=dict(seed=seed,plan=plan,actual_seed=P.r32(self.c,P.sym('gGame')+self.run.abi['game_seed']))
            all_seeds.append(row);key=(plan['quest_kind'],plan['area'])
            if key not in found:found[key]=row;print('DISCOVER '+json.dumps(row),flush=True)
            if target<=found.keys():break
        result=dict(rows=all_seeds,first_by_kind_area=[found[key] for key in sorted(found)],missing=[list(v) for v in sorted(target-found.keys())])
        (self.out/'discovered-seeds.json').write_text(json.dumps(result,indent=2)+'\n')
        self.check('native seed discovery covers all eligible regional quest origins',not result['missing'],result)
        self.scope_complete=all(c['passed'] for c in self.checks)

    def quest_case(self,kind,seed):
        self.start(seed)
        plan=next((p for p in self.plans() if p['quest_kind']==kind),None)
        if not self.check('seed deals requested quest onto a real regional room',plan is not None,dict(kind=kind,seed=seed,plan=plan)):return
        self.request_room(plan['area'],plan['cell'],plan['cell']*2+plan['terrace'])
        v=self.run.snapshot();self.check('regional giver is physically present',v['spots']['flags']['npc'],v)
        x,y=v['spots']['npc'];self.wait_normal();self.nav(x*16+8,y*16+14,0);self.run.tap('A',4)
        accepted=self.quest();self.run.image('quest-accepted');self.run.dismiss();self.run.keys([],2)
        self.check('real NPC starts the announced regional quest',accepted['kind']==kind and accepted['origin_area']==plan['area'] and accepted['origin_cell']==plan['cell'] and self.quest()['state']==2,dict(accepted=accepted,active=self.quest()))
        before=self.quest();success=self.finish_quest(kind)
        self.check('quest succeeds through real mechanics',success and self.completed(plan['field_site']),dict(before=before,after=self.quest(),state=self.run.snapshot(),origin_site_completed=self.completed(plan['field_site'])))
        self.run.image('quest-result')
        if success:
            score=P.r32(self.c,P.sym('gHandoffState')+self.extra['handoff_score'])
            self.request_room(plan['area'],plan['cell'],plan['cell']*2+plan['terrace'])
            x,y=self.run.snapshot()['spots']['npc'];self.wait_normal();self.nav(x*16+8,y*16+14,0);self.run.tap('A',12);self.run.dismiss()
            self.check('completed regional quest cannot restart or pay its score twice',self.quest()['state']==3 and self.completed(plan['field_site']) and P.r32(self.c,P.sym('gHandoffState')+self.extra['handoff_score'])==score,dict(quest=self.quest(),score_before=score,score_after=P.r32(self.c,P.sym('gHandoffState')+self.extra['handoff_score']),state=self.run.snapshot()))
        self.scope_complete=all(c['passed'] for c in self.checks)

    def save(self):
        report=self.run.report_identity()|dict(method=__doc__,harness_sha256=self.harness_sha256,
             private_abi=self.extra,checks=self.checks,scope_complete=self.scope_complete,
             errors=self.errors,opening_choices=getattr(self,'opening_choices',None),initial=self.initial,final=self.run.snapshot(),
             stages=self.stage_log,inputs=self.run.inputs)
        (self.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        if self.movie:self.movie[0].save(self.out/'journey.gif',save_all=True,append_images=self.movie[1:],duration=67,loop=0)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bundle',required=True,type=Path);ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--suite',choices=('quest','chain','trials','stakes','guard','carry-reentry','discover'),default='quest')
    ap.add_argument('--kind',type=int,choices=range(1,8),default=1)
    ap.add_argument('--seed',type=lambda n:int(n,0),default=0xb4a7)
    ap.add_argument('--count',type=int,default=96)
    args=ap.parse_args();journey=Journey(args.bundle,args.out)
    try:
        if args.suite=='quest':journey.quest_case(args.kind,args.seed)
        elif args.suite=='discover':journey.discover(args.seed,args.count)
        elif args.suite=='carry-reentry':
            journey.carry_reentry=True;journey.quest_case(5,args.seed)
        elif args.suite=='chain':journey.chain_case(args.seed)
        elif args.suite=='guard':journey.chain_case(args.seed,earn_trials=False,guard=True)
        elif args.suite=='stakes':journey.stakes_case(args.seed)
        else:
            journey.start(args.seed)
            for i in range(3):journey.earn_trial(i)
            journey.scope_complete=all(c['passed'] for c in journey.checks)
    except Exception as exc:
        journey.errors.append(str(exc));raise
    finally:journey.save()
    raise SystemExit(0 if journey.scope_complete else 1)


if __name__=='__main__':main()

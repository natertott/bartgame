#!/usr/bin/env python3
"""Actual mGBA checkpoint, map and published-extension migration review.

Private SRAM and the title seed are fixtures. Player position/facing fixtures
shorten navigation to real doors and NPCs; actual input activates those doors,
accepts quests and chooses Trophy difficulty to invoke the normal serializer.
No inventory, quest/chain/completion, terrain, enemy, camera or pixel writes are
used. A second core receives the first core's complete serialized SRAM as a
disclosed power-cycle fixture. The old source ROM is tested independently.
"""
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import shutil
import struct
import traceback

from elftools.elf.elffile import ELFFile
import mgba.core
import mgba.image
import probe as P
import critical_path as C
from arcade_journal_review import profile, preferences

SRAM=0x0e000000
SHA=lambda b:hashlib.sha256(b).hexdigest()


class ABI:
    def __init__(self,bundle):
        self.bundle=Path(bundle).resolve();self.types={};self.variables={}
        self.file=(self.bundle/'bartgame.elf').open('rb');self.elf=ELFFile(self.file)
        for cu in self.elf.get_dwarf_info().iter_CUs():
            unit=cu.get_top_DIE().attributes['DW_AT_name'].value.decode()
            for die in cu.iter_DIEs():
                name=die.attributes.get('DW_AT_name')
                if not name:continue
                name=name.value.decode()
                if die.tag=='DW_TAG_typedef':
                    target=self.resolve(die)
                    if target.tag=='DW_TAG_structure_type' and name not in self.types:
                        self.types[name]=target
                if die.tag=='DW_TAG_variable' and 'DW_AT_location' in die.attributes:
                    loc=die.attributes['DW_AT_location'].value
                    if isinstance(loc,list) and len(loc)==5 and loc[0]==3:
                        self.variables[(Path(unit).name,name)]=(int.from_bytes(bytes(loc[1:]),'little'),self.resolve(die.get_DIE_from_attribute('DW_AT_type')))
    def resolve(self,die):
        while die.tag in ('DW_TAG_typedef','DW_TAG_const_type','DW_TAG_volatile_type'):
            die=die.get_DIE_from_attribute('DW_AT_type')
        return die
    def members(self,name):
        die=self.types[name] if isinstance(name,str) else name
        return {d.attributes['DW_AT_name'].value.decode():d.attributes['DW_AT_data_member_location'].value
                for d in die.iter_children() if d.tag=='DW_TAG_member'}
    def size(self,name):return self.types[name].attributes['DW_AT_byte_size'].value
    def variable(self,file,name):return self.variables[(file,name)]


class Review:
    def __init__(self,args):
        self.args=args;self.out=args.out.resolve();self.out.mkdir(parents=True,exist_ok=True)
        self.rows=[];self.fixtures=[];self.media=[];self.trace=[]
        self.current=None
    def configure(self,bundle):
        self.bundle=Path(bundle).resolve();self.abi=ABI(self.bundle)
        P.MAP=str(self.bundle/'bartgame.map');P._syms=None
        self.members={n:self.abi.members(n) for n in ('HandoffState','HandoffQuest','PlayerState','World','Cell','LegacyInventory')}
        self.menu_addr,self.menu_type=self.abi.variable('handoff_events.c','m')
        self.menu_fields=self.abi.members(self.menu_type)
    def address(self,kind,field):
        return P.sym({'HandoffState':'gHandoffState','PlayerState':'gPl','World':'gWorld','LegacyInventory':'gLegacyInventory'}[kind])+self.members[kind][field]
    def raw(self,c,at,n):return bytes(P.r8(c,at+i) for i in range(n))
    def write(self,c,at,data):
        for i,b in enumerate(data):P.w8(c,at+i,b)
    def w32(self,c,at,n):P.w16(c,at,n&65535);P.w16(c,at+2,(n>>16)&65535)
    def mode(self,c):return P.r8(c,self.menu_addr+self.menu_fields['active'])
    def state(self,c):return dict(state=C.gstate(c),area=C.area(c),cell=C.cell(c),text=P.r8(c,P.sym('gTbActive')),menu=self.mode(c),actor=P.actor(c,0))
    def check(self,name,ok,observed=None):
        self.rows.append(dict(name=name,passed=bool(ok),observed=observed))
        print(('PASS ' if ok else 'FAIL ')+name,flush=True)
        if not ok:raise AssertionError(name)
    def press(self,c,key,n=2,release=10):P.press(c,key,n,release)
    def settle(self,c,area=None,limit=2400):
        for _ in range(limit):
            if P.r8(c,P.sym('gTbActive')):self.press(c,'A',2,8)
            elif self.mode(c)==1:self.press(c,'A',2,8)
            else:P.run(c,3)
            pending=P.r8(c,P.sym('gStartingDraft')) if 'gStartingDraft' in P._syms else 0
            if C.gstate(c)==1 and not P.r8(c,P.sym('gTbActive')) and not self.mode(c) and not pending and (area is None or C.area(c)==area):return
        raise AssertionError(('settle',self.state(c)))
    def fresh(self,label,sram=None,seed=13,start=True):
        private=self.out/'private'/label;private.mkdir(parents=True,exist_ok=True)
        rom=private/'bartgame.gba';shutil.copy2(self.bundle/'bartgame.gba',rom)
        c=mgba.core.load_path(str(rom));c.bg_video=mgba.image.Image(240,160);c.set_video_buffer(c.bg_video);c.reset()
        self.write(c,SRAM,sram if sram is not None else b'\xff'*32768)
        P.run(c,45)
        if start:
            if seed is not None:self.w32(c,P.sym('gSeedOverride'),seed)
            self.press(c,'START',2,6);self.settle(c,0)
        return c
    def shot(self,c,name):
        p=self.out/(name+'.png');P.snap(c,str(p));self.media.append(dict(file=p.name,sha256=SHA(p.read_bytes()),kind='untouched240x160 mGBA output'))
    def nav(self,c,x,y,facing=0):
        a=P.sym('gActors');self.w32(c,a+8,x<<16);self.w32(c,a+12,y<<16);P.w8(c,a+7,facing)
        self.fixtures.append(dict(kind='hero navigation position/facing only',x=x,y=y,facing=facing,area=C.area(c),cell=C.cell(c)))
        P.run(c,3)
    def normal(self,c):
        for _ in range(300):
            if P.actor(c,0)['state']==0:return
            P.run(c,2)
        raise AssertionError(('no normal player state',self.state(c)))
    def cross(self,c,side):
        before=C.cell(c);gate=C.world(c)['cells'][before]['gate'][side]
        x,y,key=C.door_inside(side);self.normal(c);self.nav(c,x,y,side)
        if gate==2:self.press(c,'B',2,24);self.normal(c)
        c.set_keys(P.key(c,key))
        for _ in range(220):
            c.run_frame()
            if C.cell(c)!=before or C.gstate(c)!=1:break
        c.clear_keys(P.key(c,key));self.settle(c,1)
        self.check('real open border reaches neighboring room',C.cell(c)!=before,self.state(c))
    def path(self,c,goal):
        world=C.world(c);start=C.cell(c);prev={start:None};q=deque([start])
        while q:
            cell=q.popleft()
            for side in range(4):
                if world['cells'][cell]['gate'][side] not in (1,2):continue
                nx=cell%5+(0,1,0,-1)[side];ny=cell//5+(-1,0,1,0)[side]
                neighbor=ny*5+nx if 0<=nx<5 and 0<=ny<5 else -1
                if neighbor<0 or neighbor in prev:continue
                prev[neighbor]=(cell,side);q.append(neighbor)
        if goal not in prev:return None
        route=[];at=goal
        while prev[at] is not None:
            before,side=prev[at];route.append(side);at=before
        return route[::-1]
    def go(self,c,goal):
        route=self.path(c,goal)
        if route is None:return False
        for side in route:self.cross(c,side)
        return C.cell(c)==goal
    def plans(self,c):
        addr,_=self.abi.variable('regional_content.c','sPlan');fields=self.abi.members('RegionalContentPlan');size=self.abi.size('RegionalContentPlan')
        return [{k:P.r8(c,addr+i*size+off) for k,off in fields.items()} for i in range(50)]
    def discovery(self,c):return self.raw(c,P.sym('gRegionalDiscovery'),50*self.abi.size('RegionalContentDiscovery'))
    def quest(self,c):
        base=self.address('HandoffState','quest');fields=self.members['HandoffQuest']
        return {k:P.r8(c,base+fields[k]) for k in ('kind','state','origin_area','origin_cell','target_area','target_cell','difficulty','stake')}
    def begin_quest(self,c):
        P.enter_forest(c);self.settle(c,1)
        plan=next(p for p in self.plans(c) if p['quest_kind'])
        self.check('generated quest giver is in a real Forest room',plan['area']==1,plan)
        self.check('giver room is reached through open regional borders',self.go(c,plan['cell']),plan)
        d=self.abi.members('RegionalContentDiscovery');base=P.sym('gRegionalDiscovery')+plan['cell']*self.abi.size('RegionalContentDiscovery')
        x=P.r8(c,base+d['npc']);y=P.r8(c,base+d['npc']+1)
        self.check('actual regional giver has a discovered tile anchor',x>0 and y>0 and P.r8(c,base+d['marks'])&2,dict(x=x,y=y))
        self.normal(c);self.nav(c,x*16+8,y*16+30);self.press(c,'A');self.settle(c,1)
        q=self.quest(c)
        self.check('real giver input starts a regional quest',q['state']==2 and q['origin_area']==1 and q['origin_cell']==plan['cell'],q)
        self.shot(c,'01-active-regional-quest')
        return plan
    def map_roundtrip(self,c):
        self.press(c,'START',2,30);self.press(c,'SELECT',2,30);self.press(c,'R',2,8)
        for _ in range(240):
            if P.r8(c,P.sym('gMenuStudyPage'))==2:break
            P.run(c,2)
        page=P.r8(c,P.sym('gMenuStudyPage'))
        self.check('Satchel atlas resolves to the selected Forest map',page==2 and C.gstate(c)==4,dict(page=page,state=self.state(c)))
        self.shot(c,'02-regional-forest-map');self.press(c,'A',2,20)
        for _ in range(240):
            if P.r8(c,P.sym('gMenuStudyZoom')):break
            P.run(c,2)
        self.check('real A input opens the selected room detail',P.r8(c,P.sym('gMenuStudyZoom'))==1)
        P.run(c,3) # the completed native canvas is uploaded at the next VBlank
        self.shot(c,'03-regional-forest-detail')
        self.press(c,'START',2,20);self.check('regional map returns to actual room',C.area(c)==1 and C.gstate(c)==1,self.state(c))
    def return_drain(self,c):
        entry=C.world(c)['entry'];self.check('backtracking returns to original Forest entry',self.go(c,entry),self.state(c))
        room=P.sym('gRoom');w=P.r8(c,room);h=P.r8(c,room+1);found=[]
        for y in range(h):
            for x in range(w):
                tile=P.r16(c,room+2+(y*32+x)*2)
                if P.r8(c,P.sym('metatile_type')+tile)==21:found.append((x,y))
        self.check('original Forest entry contains its real Drain stairs',bool(found),found)
        x,y=found[0];self.normal(c);self.nav(c,x*16+8,y*16+10);P.run(c,3);self.settle(c,0)
    def trophy_save(self,c,old=False):
        self.normal(c)
        if old:self.nav(c,120,254)
        else:self.nav(c,416,254)
        self.press(c,'A',2,12);self.check('physical Trophy opens its actual service',self.mode(c)==5,self.state(c))
        self.press(c,'DOWN');self.press(c,'DOWN');self.press(c,'A',2,12)
        self.check('actual Trophy opens difficulty settings',self.mode(c)==9,self.state(c))
        self.press(c,'A',2,12);self.settle(c,0 if not old else 4)
        return self.raw(c,SRAM,32768)
    def new_save(self):
        self.configure(self.args.bundle);c=self.fresh('new-run')
        self.check('opening draft has three real selections before exploration',P.r8(c,self.address('HandoffState','draft_round'))==3 and P.r8(c,self.address('HandoffState','draft_state'))==2)
        plan=self.begin_quest(c);self.map_roundtrip(c);self.return_drain(c)
        self.check('active quest survives ordinary room changes and hub return',self.quest(c)['state']==2,self.quest(c))
        saved=self.trophy_save(c);d=self.discovery(c);state=self.raw(c,P.sym('gHandoffState'),self.abi.size('HandoffState'));inv=self.raw(c,P.sym('gLegacyInventory'),self.abi.size('LegacyInventory'))
        versions=[struct.unpack_from('<HH',saved,offset+12) for offset in (0x4000,0x5000) if struct.unpack_from('<I',saved,offset)[0]==0x58455243]
        size=self.abi.size('ExtraRun');quest_area=P.r8(c,P.sym('gRegionalQuestArea')) if 'gRegionalQuestArea' in P._syms else None
        self.check('normal native save writes extension3 and its actual%d-byte payload'%size,(3,size) in versions,versions)
        self.check('saved map discoveries contain actual placed features',any(d),dict(bytes=len(d),sha256=SHA(d),plan=plan))
        (self.out/'new-checkpoint-private.bin').write_bytes(saved)
        cold=self.fresh('new-cold',saved,seed=None)
        self.check('cold Continue preserves the exact regional map anchors',self.discovery(cold)==d)
        self.check('cold Continue preserves live quest and chain facts',self.raw(cold,P.sym('gHandoffState'),self.abi.size('HandoffState'))==state,dict(before=self.quest(c),after=self.quest(cold)))
        self.check('cold Continue preserves actual earned draft inventory',self.raw(cold,P.sym('gLegacyInventory'),self.abi.size('LegacyInventory'))==inv)
        if quest_area is not None:
            self.check('cold Continue preserves run-start quest region',P.r8(cold,P.sym('gRegionalQuestArea'))==quest_area and quest_area in (1,3),dict(before=quest_area,after=P.r8(cold,P.sym('gRegionalQuestArea'))))
        self.check('cold Continue does not rerun opening draft',not P.r8(cold,P.sym('gStartingDraft')) and self.mode(cold)==0,self.state(cold))
        self.shot(cold,'04-cold-continue')
    def old_save(self):
        self.configure(self.args.old_bundle)
        ram=bytearray(b'\xff'*32768);j=profile(0xA50102,0x101,8);pref=preferences(2,1);ram[0x7ec0:0x7ee0]=j;ram[0x7f00:0x7f0c]=pref
        self.fixtures.append(dict(kind='private serialized older journal/appearance',earned=False))
        c=self.fresh('published-v2',bytes(ram),seed=13)
        self.nav(c,280,130);self.press(c,'A',2,20);self.settle(c,4)
        self.check('published ROM enters its historical Annex for compatibility fixture',C.area(c)==4)
        # Start an actual old optional contract; it must become a real chain.
        self.nav(c,360,254);self.press(c,'A');self.press(c,'A');self.settle(c,4)
        self.check('published optional contract is actually active',P.r8(c,self.address('HandoffState','contract_state'))==1)
        # Start the old courier quest through the historical challenge desk.
        self.nav(c,280,254);self.press(c,'A')
        for _ in range(20):self.press(c,'DOWN',2,5)
        self.press(c,'A',2,20);self.settle(c,4)
        self.check('published Annex courier is actually active',self.quest(c)['kind']==6 and self.quest(c)['state']==2 and self.quest(c)['origin_area']==4,self.quest(c))
        self.nav(c,264,354);P.hold(c,'DOWN',100)
        if C.area(c)==0:
            self.nav(c,280,130);self.press(c,'A',2,20)
        self.settle(c,4)
        self.check('published courier survives its actual return route',self.quest(c)['state']==2 and self.quest(c)['origin_area']==4,self.quest(c))
        saved=self.trophy_save(c,old=True);inv=self.raw(c,P.sym('gLegacyInventory'),self.abi.size('LegacyInventory'))
        profile_bytes=self.raw(c,SRAM+0x7d00,256);bits=self.raw(c,P.sym('gJournalItemBits'),20)+self.raw(c,P.sym('gJournalEnemyBits'),12)
        self.shot(c,'05-published-v2-checkpoint');(self.out/'published-v2-private.bin').write_bytes(saved)
        versions=[struct.unpack_from('<HH',saved,offset+12) for offset in (0x4000,0x5000) if struct.unpack_from('<I',saved,offset)[0]==0x58455243]
        self.check('fixture is a genuine published extension2 checkpoint',(2,1404) in versions,versions)
        self.configure(self.args.bundle);cold=self.fresh('migrated-v2',saved,seed=None)
        self.check('published extension2 inventory survives native Continue',self.raw(cold,P.sym('gLegacyInventory'),self.abi.size('LegacyInventory'))==inv)
        self.check('old Annex quest does not become a regional ghost',self.quest(cold)['state']==0,self.quest(cold))
        target=P.r8(cold,self.address('HandoffState','contract_target'))
        self.check('old optional contract migrates to actual regional target',P.r8(cold,self.address('HandoffState','contract_state'))==1 and 32<=target<128,dict(target=target))
        self.check('old map has no invented discovery coordinates',not any(self.discovery(cold)))
        if 'gRegionalQuestArea' in P._syms:
            self.check('published extension2 seeds a valid run-start quest region',P.r8(cold,P.sym('gRegionalQuestArea'))==1,dict(seed=13,quest_area=P.r8(cold,P.sym('gRegionalQuestArea'))))
        self.check('published profile and preferences remain byte-identical',self.raw(cold,SRAM+0x7d00,256)==profile_bytes and self.raw(cold,SRAM+0x7f00,12)==pref)
        newbits=self.raw(cold,P.sym('gJournalItemBits'),20)+self.raw(cold,P.sym('gJournalEnemyBits'),12)
        self.check('all prior cabinet knowledge is retained',all((a&b)==a for a,b in zip(bits,newbits)))
        self.check('migration Continue does not start a new draft',not P.r8(cold,P.sym('gStartingDraft')) and self.mode(cold)==0,self.state(cold))
        self.shot(cold,'06-published-save-migrated')
    def run(self):
        error=None
        try:self.new_save();self.old_save()
        except Exception as e:error=repr(e);traceback.print_exc()
        report=dict(method=__doc__,rom_sha256=SHA((self.args.bundle/'bartgame.gba').read_bytes()),
                    published_rom_sha256=SHA((self.args.old_bundle/'bartgame.gba').read_bytes()),
                    tool_sha256=SHA(Path(__file__).read_bytes()),checks=self.rows,fixtures=self.fixtures,media=self.media,
                    passed=sum(r['passed'] for r in self.rows),total=len(self.rows),complete=error is None,error=error)
        (self.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print('RESULT',report['passed'],'/',report['total'],'complete',report['complete'],flush=True)
        return error is None and all(r['passed'] for r in self.rows)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',required=True,type=Path);p.add_argument('--old-bundle',required=True,type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args()
    raise SystemExit(0 if Review(a).run() else 1)


if __name__=='__main__':main()

#!/usr/bin/env python3
"""Inspect real regional maps and return to an unchanged live scene in mGBA.

The isolated map cases request the normal regional fade/load path, with no
inventory, health, quest, completion, terrain, camera or pixel assignment.
Doors, overview/zoom controls and returning to play use real input. Hero
position/facing fixtures shorten the approach to an actual placed entrance.
The optional pending-trials case earns its first three objectives through the
normal mechanics, or consumes the exact genuine native journey checkpoint,
before inspecting charts and another real Trophy checkpoint. The Cream case
accepts and completes a courier through normal inputs and checks both the
entitlement safety guard and the later permitted preference change.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import traceback

import mgba.core
import mgba.image

import probe as P
import release_boundary_review as B
from regional_journey_review import Journey
from regional_save_native import ABI


class Review(Journey):
    def __init__(self,bundle,out):
        super().__init__(bundle,out)
        self.structs=ABI(self.bundle)
        self.gear_state={name:self.structs.variable('gear_menu.c',name)[0]
                         for name in ('sActive','sPage','sZoom','sMapCell')}
        self.map_cases=[]
        header=(self.out/'abi/headers/legacy_items.h').read_text()
        self.flippers=int(re.search(r'\bLI_FLIPPERS\s*=\s*(0x[0-9a-fA-F]+|\d+)',header).group(1),0)

    def wait_byte(self,address,value,limit=600):
        for _ in range(limit):
            if P.r8(self.c,address)==value:
                self.run.keys([],3)
                return True
            self.run.keys([],2)
        return False

    def live_scene(self):
        names=('Room','RoomSpots','RegionalContentSpots','HandoffState','World','CreamWorld')
        globals_=('gRoom','gSpots','gRegionalSpots','gHandoffState','gWorld','gCreamWorld')
        answer={name:self.read(P.sym(global_),self.structs.size(name))
                for name,global_ in zip(names,globals_)}
        for variable in ('s','r'):
            address,kind=self.structs.variable('handoff_events.c',variable)
            answer['runtime_'+variable]=self.read(address,kind.attributes['DW_AT_byte_size'].value)
        answer['hero']=self.read(P.sym('gActors'),64)
        answer['discovery']=self.read(P.sym('gRegionalDiscovery'),50*self.run.abi['discovery_size'])
        answer['node']=bytes([self.run.u8('gCreamNode')])
        return answer

    def map_markers(self,area):
        a=self.run.abi
        prefix='menu' if area==1 else 'gear'
        count=self.run.u8('gMenuMapMarkerCount' if area==1 else 'gGearMapMarkerCount')
        address=P.sym('gMenuMapMarkers' if area==1 else 'gGearMapMarkers')
        result=[]
        for i in range(count):
            start=address+i*a[prefix+'_marker_size'];row={}
            for field in ('tile_x','tile_y','source_x','source_y','x','y'):
                at=start+a[prefix+'_marker_'+field]
                row[field]=P.r8(self.c,at) if field.startswith('tile_') else P.r16(self.c,at)
            field='kind' if area==1 else 'ch'
            row[field]=P.r8(self.c,start+a[prefix+'_marker_'+field]);result.append(row)
        return result

    def map_case(self,area,cell,label,expect=None,pending=False):
        self.wait_normal()
        before_state=self.run.snapshot()
        self.run.tap('START',30);self.run.tap('SELECT',30);self.run.tap('R',12)
        if area==1:
            ready=self.wait_byte(P.sym('gMenuStudyPage'),2)
            selected=self.run.u8('gMenuStudyMapCell')
        else:
            ready=self.wait_byte(self.gear_state['sPage'],1) and self.wait_byte(self.gear_state['sActive'],1)
            selected=P.r8(self.c,self.gear_state['sMapCell'])
        self.check(label+': atlas resolves actual parent region and room',ready and selected==cell,
                   dict(expected_area=area,expected_cell=cell,selected=selected,state=self.run.snapshot()))
        before=self.live_scene()
        self.run.image(label+'-overview')
        self.run.tap('A',20)
        zoom=P.sym('gMenuStudyZoom') if area==1 else self.gear_state['sZoom']
        self.check(label+': real A opens detailed chart',self.wait_byte(zoom,1))
        if area==3:
            # sZoom flips before drawing; periodic blink redraws also reset
            # this buffer while the preview is in progress. Observe a fully
            # populated chart, not an arbitrary ARM instruction boundary.
            for _ in range(600):
                if self.run.u8('gGearMapMarkerCount'):break
                self.run.keys([],1)
        markers=self.map_markers(area)
        if expect:
            for flag,kind,spot in ((1,1,'door'),(2,2,'npc'),(4,9,'npc'),(8,12,'mechanism'),(16,10,'npc'),(32,3,'cache')):
                if not expect['marks']&flag:continue
                token=kind if area==1 else {1:ord('D'),2:ord('Q'),9:ord('W'),12:ord('K'),10:ord('V'),3:ord('G')}[kind]
                key='kind' if area==1 else 'ch';xy=expect[spot]
                found=any(m[key]==token and (m['tile_x'],m['tile_y'])==tuple(xy) for m in markers)
                self.check(label+': actual '+spot+' anchor has its semantic icon',found,
                           dict(expected=xy,token=token,markers=markers))
            chain=self.run.snapshot()['chain'];goal=self.plan(chain['target']) if chain['state']==1 else None
            if goal and goal['area']==area and goal['cell']==cell:
                spot='door' if chain['target']==goal['interior_site'] else 'cache' if chain['kind']==5 else 'npc'
                xy=expect[spot];key='kind' if area==1 else 'ch';token=11 if area==1 else ord('O')
                self.check(label+': active objective is tethered to its actual feature',
                           any(m[key]==token and (m['tile_x'],m['tile_y'])==tuple(xy) for m in markers),
                           dict(expected=xy,chain=chain,markers=markers))
        if pending:
            self.check(label+': pending trials invent no objective tile',
                       all(m['kind']!=11 for m in markers) if area==1 else all(m['ch']!=ord('O') for m in markers),markers)
        self.run.image(label+'-zoom')
        paused=self.live_scene()
        self.check(label+': overview and zoom preserve paused scene and facts',before==paused,
                   dict(changed=[key for key in before if before[key]!=paused[key]]))
        self.run.tap('START',30);self.run.keys([],3)
        after=self.live_scene()
        kept=('Room','RoomSpots','RegionalContentSpots','discovery','node','World','CreamWorld')
        self.check(label+': resume restores actual room and discovered anchors',
                   self.area()==before_state['area'] and self.cell()==before_state['cell'] and self.run.snapshot()['state']==1 and all(before[key]==after[key] for key in kept),
                   dict(changed=[key for key in kept if before[key]!=after[key]],before=before_state,after=self.run.snapshot()))
        self.run.image(label+'-resumed')
        self.map_cases.append(dict(label=label,area=area,cell=cell,markers=markers,
                                  scene_sha256={key:hashlib.sha256(value).hexdigest() for key,value in before.items()}))

    def observed(self,area,cell):
        size=self.run.abi['discovery_size'];base=P.sym('gRegionalDiscovery')+(cell+(25 if area==3 else 0))*size
        fields=self.structs.members('RegionalContentDiscovery')
        result={name:(P.r8(self.c,base+fields[name]),P.r8(self.c,base+fields[name]+1))
                for name in ('door','npc','mechanism','cache')}
        result['marks']=P.r8(self.c,base+fields['marks'])&63
        return result

    def isolated(self,seed):
        self.start(seed)
        for area in (1,3):
            plans=[p for p in self.plans() if p['area']==area and p['interior_site']!=255]
            # Cover actual entrances plus each distinct field role available in
            # this deal without asserting that fixtures prove route admission.
            chosen=[]
            for key in ('quest_kind','has_wave','fusion_color','field_mechanism_variant'):
                selected=next((p for p in plans if (p[key]!=255 if key.endswith(('color','variant')) else p[key])),None)
                if selected and selected not in chosen:chosen.append(selected)
            if not chosen:chosen=plans[:1]
            for index,plan in enumerate(chosen):
                cell=plan['cell'];self.request_room(area,cell,cell*2+plan['terrace'])
                self.map_case(area,cell,'region%d-field%d'%(area,index),self.observed(area,cell))
                if index==0:
                    point=self.run.snapshot()['spots']['door']
                    self.wait_normal();self.nav(point[0]*16+8,point[1]*16+14,0)
                    self.run.tap('A',6);self.run.settle(4);self.run.dismiss()
                    self.check('actual region%d door reaches its generated interior'%area,
                               self.area()==4 and self.private('s_site')==plan['interior_site'],self.run.snapshot())
                    actor=self.run.snapshot()['actor'];x,y=actor['x'],actor['y']
                    feet=[dict(x=px,y=py,type=self.tile_type(px//16,py//16))
                          for px,py in ((x-8,y-4),(x+8,y-4),(x,y-12),(x,y+4))]
                    self.check('region%d interior arrival has dry feet without Flippers'%area,
                               all(p['type'] not in (self.defs['TT_PIT'],self.defs['TT_WATER']) for p in feet) and not(self.run.snapshot()['inventory']['owned'][self.flippers//32]&(1<<(self.flippers%32))),
                               dict(plan=plan,actor=actor,feet=feet,inventory=self.run.snapshot()['inventory']))
                    self.map_case(area,cell,'region%d-interior'%area,self.observed(area,cell))
                    # The isolated entrance may deal a hostile event whose
                    # spawn is under attack. Move to its real dry exit before
                    # waiting, rather than demanding idle recovery in danger.
                    self.nav(264,350,2)
                    self.drive('DOWN',lambda:self.area()!=4 and self.run.snapshot()['state']==1,400)
                    self.run.settle();self.run.dismiss()
                    self.check('actual region%d interior exit returns to its parent'%area,self.area()==area and self.cell()==cell,self.run.snapshot())
        self.scope_complete=all(c['passed'] for c in self.checks)

    def pending(self,seed,checkpoint=None):
        if checkpoint is None:self.chain_case(seed,earn_trials=False,guard=True)
        else:
            source=json.loads((checkpoint.parent/'report.json').read_text());saved=checkpoint.read_bytes()
            self.check('pending checkpoint comes from this exact candidate',
                       source['rom_sha256']==hashlib.sha256((self.bundle/'bartgame.gba').read_bytes()).hexdigest() and source['scope_complete'] and not source['errors'] and len(saved)==32768,
                       dict(source_rom=source['rom_sha256'],checkpoint_sha256=hashlib.sha256(saved).hexdigest()))
            private=self.out/'checkpoint-core';private.mkdir(exist_ok=True);rom=private/'bartgame.gba';shutil.copy2(self.bundle/'bartgame.gba',rom)
            c=mgba.core.load_path(str(rom));c.bg_video=mgba.image.Image(240,160);c.set_video_buffer(c.bg_video);c.reset()
            for i,b in enumerate(saved):P.w8(c,0x0e000000+i,b)
            self.run.c=c;self.run.fixtures.append(dict(kind='exact genuine pending-trials SRAM from native journey',path=str(checkpoint),sha256=hashlib.sha256(saved).hexdigest(),source_report_sha256=hashlib.sha256((checkpoint.parent/'report.json').read_bytes()).hexdigest()))
            self.run.keys([],45);self.run.tap('START',12);self.run.settle(0);self.run.dismiss();self.wait_normal()
            self.initial=self.run.snapshot();chain=self.initial['chain']
            self.check('genuine checkpoint continues with original trials still pending',chain['step']==3 and chain['state']==0 and chain['target']==0 and not any(f['won'] or f['claimed'] for f in self.trial_facts()),dict(chain=chain,facts=self.trial_facts()))
        for area in (1,3):
            self.enter_region(area)
            self.map_case(area,self.cell(),'pending-region%d'%area,pending=True)
        self.return_hub();before=self.run.snapshot()['chain']
        self.courier_checkpoint()
        saved=self.read(0x0e000000,32768)
        (self.out/'pending-trials-checkpoint-private.bin').write_bytes(saved)
        after=self.run.snapshot()['chain']
        self.check('pending trials survive actual Trophy checkpoint and cold Continue',
                   before==after and after['step']==3 and after['state']==0,dict(before=before,after=after))
        self.scope_complete=all(c['passed'] for c in self.checks)

    def cold_quest(self,seed):
        self.start(seed)
        plan=next(p for p in self.plans() if p['quest_kind'])
        self.check('seed deals the actual quest giver in Cream',plan['area']==3,plan)
        self.go_plan(plan);x,y=self.run.snapshot()['spots']['npc']
        self.wait_normal();self.nav(x*16+8,y*16+14,0);self.run.tap('A',6);self.run.dismiss()
        quest=self.quest()
        self.check('real Cream NPC accepts its regional quest',quest['state']==2 and quest['origin_area']==3 and quest['origin_cell']==plan['cell'],quest)
        self.map_case(3,plan['cell'],'cream-active-quest',self.observed(3,plan['cell']))
        self.return_hub();self.wait_normal();self.nav(416,254,0);self.run.tap('A',12)
        if self.run.snapshot()['service_menu']['active']!=5:raise RuntimeError('actual Trophy did not open for entitlement toggle')
        self.run.tap('DOWN');self.run.tap('A',12);message=B.text_message(self.c)
        self.run.image('cream-entitlement-guard');self.run.dismiss();self.wait_normal()
        self.check('Trophy explains why an accepted Cream task prevents a stranding restriction',self.run.snapshot()['entitlement']==0 and 'Finish your current Cream quest or seal' in message,dict(message=message,state=self.run.snapshot()))
        before=self.read(P.sym('gHandoffState'),self.structs.size('HandoffState'))
        anchors=self.read(P.sym('gRegionalDiscovery'),50*self.run.abi['discovery_size'])
        area=self.run.u8('gRegionalQuestArea');plans=self.plans()
        self.courier_checkpoint()
        self.check('cold Continue keeps accepted Cream quest and its run-start region',area==3 and self.run.u8('gRegionalQuestArea')==3 and self.plans()==plans,dict(before=area,after=self.run.u8('gRegionalQuestArea'),quest=self.quest()))
        self.check('cold Cream quest, full handoff facts and anchors remain exact',
                   self.read(P.sym('gHandoffState'),self.structs.size('HandoffState'))==before and self.read(P.sym('gRegionalDiscovery'),len(anchors))==anchors)
        self.check('accepted Cream courier completes by real delivery',self.finish_quest(6),self.quest())
        self.return_hub();self.wait_normal();self.nav(416,254,0);self.run.tap('A',12)
        if self.run.snapshot()['service_menu']['active']!=5:raise RuntimeError('actual Trophy did not open after courier delivery')
        self.run.tap('DOWN');self.run.tap('A',12);message=B.text_message(self.c);self.run.dismiss();self.wait_normal()
        self.check('Trophy allows restriction after the accepted task is finished',self.run.snapshot()['entitlement']==1,dict(message=message,state=self.run.snapshot()))
        self.courier_checkpoint()
        self.check('changed entitlement and cold Continue cannot move the latched Cream giver',
                   self.run.snapshot()['entitlement']==1 and self.run.u8('gRegionalQuestArea')==3 and self.plans()==plans,
                   dict(entitlement=self.run.snapshot()['entitlement'],quest_area=self.run.u8('gRegionalQuestArea'),giver=self.quest()))
        self.scope_complete=all(c['passed'] for c in self.checks)

    def save(self):
        super().save();path=self.out/'report.json';report=json.loads(path.read_text())
        report.update(method=__doc__,map_cases=self.map_cases,harness_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        path.write_text(json.dumps(report,indent=2)+'\n')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    p.add_argument('--seed',type=lambda s:int(s,0),default=0xb4a7);p.add_argument('--suite',choices=('maps','pending','cold-quest'),default='maps');p.add_argument('--checkpoint',type=Path);args=p.parse_args()
    r=Review(args.bundle,args.out)
    try:
        if args.suite=='maps':r.isolated(args.seed)
        elif args.suite=='pending':r.pending(args.seed,args.checkpoint)
        else:r.cold_quest(args.seed)
    except Exception as error:r.errors.append(repr(error));traceback.print_exc()
    r.save();passed=sum(c['passed'] for c in r.checks);print('RESULT',passed,'/',len(r.checks),'complete',r.scope_complete,flush=True)
    raise SystemExit(0 if r.scope_complete and not r.errors else 1)


if __name__=='__main__':main()

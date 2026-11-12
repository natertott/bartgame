#!/usr/bin/env python3
"""Native paired-event and fusion consequence checks on a frozen ROM.

Fixtures are fresh private SRAM, deterministic title seed, hero navigation,
ordinary regional room-load requests, and explicitly logged tool/kinstone
ownership. All fusions, gates, chamber completion, waves and rewards use actual
mGBA input. No completion, enemy, terrain, clock, video or outcome is assigned.
This isolates mechanics; it is not an unassisted traversal or a source-art render.
"""
import argparse,json,struct,subprocess
from pathlib import Path
import probe as P
from regional_journey_review import Journey,sha


class Pairs(Journey):
    def __init__(self,bundle,out):
        super().__init__(bundle,out)
        directory=self.out/'private-abi'
        fields={name:'offsetof(HandoffState,'+name+')' for name in
                ('memory_known','memory_code','memory_length','fusion_flags',
                 'kinstone_shapes','fuser_shape','gold_owned','gold_fused','food_mask')}
        fields.update({'s_memory_input':'offsetof(__typeof__(s),memory_input)',
                       's_memory_show':'offsetof(__typeof__(s),memory_show)',
                       'r_door_frame':'offsetof(__typeof__(r),door_frame)',
                       'inventory_level':'offsetof(LegacyInventory,sword_level)',
                       'inventory_kinstones':'offsetof(LegacyInventory,kinstones)'})
        unit=directory/'pairs-observe.c'
        unit.write_text((directory/'handoff-observe.c').read_text()+
            '\n__attribute__((used,section(".qa_pairs"))) const unsigned pairs_abi[]={'+','.join(fields.values())+'};\n')
        obj=directory/'pairs.o';raw=directory/'pairs.bin'
        command=['arm-none-eabi-gcc','-mcpu=arm7tdmi','-mthumb','-O2','-fno-builtin',
                 '-DBART_FOREST_VARIANT=32','-I',str(self.out/'abi/headers'),'-I',str(directory),'-c',str(unit),'-o',str(obj)]
        result=subprocess.run(command,capture_output=True,text=True)
        (directory/'pairs-compile.log').write_text(result.stdout+result.stderr);result.check_returncode()
        subprocess.run(['arm-none-eabi-objcopy','-O','binary','-j','.qa_pairs',str(obj),str(raw)],check=True)
        self.pair_abi=dict(zip(fields,struct.unpack('<'+'I'*len(fields),raw.read_bytes())))
        (directory/'pairs-provenance.json').write_text(json.dumps(dict(source_commit=(self.bundle/'source-commit.txt').read_text().strip(),command=command,unit_sha256=sha(unit),offsets=self.pair_abi),indent=2)+'\n')
        self.harness_sha256=sha(__file__)
        (self.out/'review-pairs-harness.py').write_bytes(Path(__file__).read_bytes())

    def byte(self,field):return P.r8(self.c,P.sym('gHandoffState')+self.pair_abi[field])
    def give_fixture(self,field,value,index=0):
        address=P.sym('gHandoffState')+self.pair_abi[field]+index
        before=P.r8(self.c,address);P.w8(self.c,address,value)
        self.run.fixtures.append(dict(kind='kinstone inventory ownership',field=field,index=index,before=before,value=value))

    def tools(self):
        address=P.sym('gLegacyInventory')+self.run.abi['inventory_owned']
        for i in range(16):P.w8(self.c,address+i,255)
        P.w8(self.c,P.sym('gLegacyInventory')+self.pair_abi['inventory_level'],4)
        P.w8(self.c,P.sym('gPl')+self.run.abi['player_items'],0x7f)
        self.run.fixtures.append(dict(kind='all legacy tool ownership, original tool flags0x7f and sword level4 for isolated input tests; health/enemy state unchanged'))

    def go_plan(self,plan):
        self.request_room(plan['area'],plan['cell'],plan['cell']*2+plan['terrace'])

    def point_action(self,point,label=None):
        self.wait_normal();self.nav(point[0]*16+8,point[1]*16+14,0)
        if label:self.run.image(label+'-before')
        self.run.tap('A',8);self.run.dismiss();self.run.keys([],4)
        if label:self.run.image(label+'-after')

    def half(self,color):
        shape=P.r8(self.c,P.sym('gHandoffState')+self.pair_abi['fuser_shape']+color)
        self.give_fixture('kinstone_shapes',1,color*3+shape)
        return shape

    def green(self):
        plan=next(p for p in self.plans() if p['fusion_color']==0);self.go_plan(plan)
        view=self.run.snapshot();self.check('green real giver and cache physically placed',view['spots']['flags']['npc'] and view['spots']['flags']['cache'],view)
        site=plan['field_site'];before=self.run.u16('gHandoffState',self.run.abi['handoff_remaining']+site*2)
        self.point_action(view['spots']['cache'],'green-locked-cache')
        self.check('green cache refuses claim before fusion',self.run.u16('gHandoffState',self.run.abi['handoff_remaining']+site*2)==before and not(self.byte('fusion_flags')&1))
        self.point_action(view['spots']['npc'])
        self.check('green fuser refuses absent half',not(self.byte('fusion_flags')&1))
        shape=self.half(0);self.point_action(view['spots']['npc'],'green-fuse')
        self.check('green real NPC consumes matching half and unlocks cache',self.byte('fusion_flags')&1 and P.r8(self.c,P.sym('gHandoffState')+self.pair_abi['kinstone_shapes']+shape)==0)
        gilt=self.run.snapshot()['gilt'];self.point_action(view['spots']['cache'],'green-claim')
        first=self.run.snapshot()['gilt'];claimed=self.run.u16('gHandoffState',self.run.abi['handoff_remaining']+site*2)
        self.check('green cache grants actual100gilt once',first==min(999,gilt+100) and claimed&0x4000,dict(before=gilt,after=first,claimed=claimed))
        self.go_plan(plan);self.point_action(self.run.snapshot()['spots']['cache'])
        self.check('green cache remains claimed on revisit',self.run.snapshot()['gilt']==first and self.run.u16('gHandoffState',self.run.abi['handoff_remaining']+site*2)&0x4000)

    def blue(self):
        plan=next(p for p in self.plans() if p['fusion_color']==1);self.go_plan(plan);view=self.run.snapshot()
        frame_before=P.r8(self.c,self.r_addr+self.pair_abi['r_door_frame'])
        self.point_action(view['spots']['door'],'blue-closed-door')
        self.check('blue physical pocket refuses entry before fusion',self.area()==plan['area'] and self.cell()==plan['cell'] and not(self.byte('fusion_flags')&2),self.run.snapshot())
        shape=self.half(1);self.point_action(view['spots']['npc'],'blue-fuse')
        frame_after=P.r8(self.c,self.r_addr+self.pair_abi['r_door_frame'])
        self.check('blue NPC consumes matching half and changes actual door frame',self.byte('fusion_flags')&2 and P.r8(self.c,P.sym('gHandoffState')+self.pair_abi['kinstone_shapes']+3+shape)==0 and frame_after!=frame_before,dict(before=frame_before,after=frame_after))
        self.enter_interior(plan);self.check('blue fusion opens its own actual pocket',self.area()==4 and self.private('s_site')==plan['interior_site'],self.run.snapshot())
        self.run.image('blue-open-pocket-inside');self.leave_interior()
        self.check('blue pocket exit returns to real regional origin',self.area()==plan['area'] and self.cell()==plan['cell'],self.run.snapshot())

    def gold(self):
        plan=next(p for p in self.plans() if p['event_kind']==26);self.enter_interior(plan)
        def barrier(xs):return [self.tile_type(x,8) for x in xs]
        sealed=barrier(range(11,21));self.point_action((12,10),'gold-missing-flow')
        self.check('gold Flow seal refuses absent half',not(self.byte('gold_fused')&1) and barrier(range(11,21))==sealed)
        self.give_fixture('gold_owned',self.byte('gold_owned')|1);self.point_action((12,10),'gold-flow-opens')
        flow=barrier(range(11,21));self.check('gold Flow fusion opens only its actual first barrier',self.byte('gold_fused')&1 and all(t==0 for t in flow[:5]) and flow[5:]==sealed[5:],dict(sealed=sealed,opened=flow))
        self.point_action((19,10));self.check('gold statues refuse missing three pieces',self.byte('gold_fused')==1)
        self.give_fixture('gold_owned',15);self.point_action((19,10),'gold-statues-open')
        self.check('all3gold statue halves open remaining real wall',self.byte('gold_fused')==15 and all(t==0 for t in barrier(range(11,21))))
        self.point_action((16,5),'gold-final-cache')
        self.check('gold final cache requires real seals and completes',self.completed(plan['interior_site']))
        self.leave_interior();self.enter_interior(plan)
        self.check('gold opened seals persist on revisit',self.byte('gold_fused')==15 and all(t==0 for t in barrier(range(11,21))))
        self.leave_interior()

    def memory(self):
        learn=next(p for p in self.plans() if p['event_kind']==7)
        recall=next(p for p in self.plans() if p['event_kind']==8)
        self.enter_interior(recall);self.run.image('memory-recall-unlearned')
        for i in range(4):self.wait_normal();self.nav((9+i*4)*16+8,10*16+14);self.run.keys([],3)
        self.check('real Recall rejects plates until paired Learn is watched',not self.completed(recall['interior_site']) and not self.byte('memory_known'))
        self.leave_interior();self.enter_interior(learn)
        shows=[]
        for i in range(420):
            self.movie.extend(self.run.keys([],1,record=i%4==0))
            if i%12==0:shows.append(P.r8(self.c,self.s_addr+self.pair_abi['s_memory_show']))
        self.run.image('memory-learn-sequence')
        length=self.byte('memory_length');code=self.read(P.sym('gHandoffState')+self.pair_abi['memory_code'],length)
        self.check('real Learn timed display records its paired sequence',self.byte('memory_known') and set(code)<=set(shows),dict(code=list(code),observed=shows))
        self.leave_interior();self.enter_interior(recall)
        wrong=(code[0]+1)%4;self.wait_normal();self.nav((9+wrong*4)*16+8,10*16+14);self.run.keys([],3)
        self.check('wrong Recall plate cannot complete sequence',not self.completed(recall['interior_site']) and P.r8(self.c,self.s_addr+self.pair_abi['s_memory_input'])==0)
        for plate in code:
            self.wait_normal();self.nav(264,238);self.run.keys([],2)
            self.nav((9+plate*4)*16+8,10*16+14);self.run.keys([],3)
        self.run.image('memory-recall-complete');self.check('real paired Recall sequence completes once',self.completed(recall['interior_site']))
        self.leave_interior();self.enter_interior(recall);self.check('Recall completion survives actual exit and revisit',self.completed(recall['interior_site']));self.leave_interior()

    def portal(self):
        plan=next((p for p in self.plans() if p['event_kind']==23),None)
        if not self.check('seed contains normal three-wave paired portal',plan is not None,self.plans()):return
        pocket=next(p for p in self.plans() if p['event_kind']==24 and p['fusion_color']!=1)
        self.go_plan(pocket);v=self.run.snapshot();self.point_action(v['spots']['door'],'portal-paired-door-asleep')
        self.check('paired pocket door refuses before portal trial',self.area()==pocket['area'] and self.cell()==pocket['cell'])
        self.enter_interior(plan);self.point_action((16,11),'portal-before-waves')
        self.check('portal cannot bypass its actual waves',self.area()==4 and self.private('s_site')==plan['interior_site'] and not self.completed(plan['interior_site']))
        result=self.fight(lambda:self.completed(plan['interior_site']),limit=4000)
        wave=self.run.u16('gHandoffState',self.run.abi['handoff_wave']+plan['interior_site']*2)
        self.run.image('portal-three-waves-cleared');self.check('portal requires three genuine waves before clear',result and wave>=3,dict(wave=wave,state=self.run.snapshot()))
        self.point_action((16,11));self.run.settle(4)
        if self.private('s_site')==plan['interior_site']:self.point_action((16,11));self.run.settle(4)
        self.check('earned portal enters paired nonblue pocket',self.private('s_site')==pocket['interior_site'] and not(self.byte('fusion_flags')&2),dict(pocket=pocket,state=self.run.snapshot(),site=self.private('s_site')))
        self.run.image('portal-paired-pocket-inside');self.leave_interior()
        self.check('nested pocket returns original portal room origin',self.area()==plan['area'] and self.cell()==plan['cell'],self.run.snapshot())
        self.enter_interior(pocket);self.check('trial permanently wakes the separate regional pocket door',self.private('s_site')==pocket['interior_site']);self.leave_interior()

    def wave(self):
        plan=next(p for p in self.plans() if p['has_wave'] and p['area']==1)
        self.go_plan(plan);p=self.run.snapshot()['spots']['npc'];self.wait_normal();self.nav(p[0]*16+8,p[1]*16+14)
        self.run.keys([],10);site=self.private('r_wave_site')
        view=self.run.snapshot();anchor=view['spots']['cache'] if view['spots']['flags']['cache'] else view['spots']['npc']
        def anchored_prizes():
            prizes=[]
            for i in range(1,96):
                actor=P.actor(self.c,i)
                if actor['kind']==6 and actor['type']==22 and (actor['x'],actor['y'])==(anchor[0]*16+8,anchor[1]*16+14):
                    prizes.append(actor|dict(item=P.r8(self.c,P.sym('gActors')+i*64+48)))
            return prizes
        self.check('real field wave uses regional persistent identity',site==132)
        gold_before=self.byte('gold_owned')
        self.fight(lambda:self.completed(site),limit=2400,owned=True)
        self.run.keys([],8);first_prizes=anchored_prizes()
        self.check('first actual field wave grants persistent first-clear',self.completed(site),self.run.snapshot());self.run.image('field-wave-first-clear')
        gold_after=self.byte('gold_owned')
        self.check('first field clear grants a real pickup or unique golden half',len(first_prizes)==1 or gold_before!=gold_after,dict(anchor=anchor,prizes=first_prizes,gold_before=gold_before,gold_after=gold_after,legacy_actors=[P.actor(self.c,i)|dict(item=P.r8(self.c,P.sym('gActors')+i*64+48)) for i in range(1,96) if P.actor(self.c,i)['kind']==6 and P.actor(self.c,i)['type']==22]))
        self.stage_log.append(dict(kind='field first-clear source fact',site=site,first_clear=self.completed(site),wave=self.run.u16('gHandoffState',self.run.abi['handoff_wave']+site*2),prizes=first_prizes))
        self.go_plan(plan);self.wait_normal();v=self.run.snapshot();p=v['spots']['npc'];self.nav(p[0]*16+8,p[1]*16+14)
        self.run.keys([],200);before=self.run.u16('gHandoffState',self.run.abi['handoff_wave']+site*2)
        self.fight(lambda:self.run.u16('gHandoffState',self.run.abi['handoff_wave']+site*2)>before,limit=2400,owned=True)
        after=self.run.u16('gHandoffState',self.run.abi['handoff_wave']+site*2)
        self.check('field endless waves resume and escalate on revisit',after>before and self.completed(site),dict(before=before,after=after))
        self.run.keys([],8);self.check('second field wave cannot repeat first-clear reward',not anchored_prizes() and self.byte('gold_owned')==gold_after,dict(anchor=anchor,prizes=anchored_prizes(),gold_before=gold_after,gold_after=self.byte('gold_owned')))

    def save(self):
        super().save()
        path=self.out/'report.json';report=json.loads(path.read_text())
        report.update(method=__doc__,input_method='Actual mGBA controls produce effects. Listed title seed, navigation, ordinary room-load requests and tool/kinstone ownership are fixtures; no completion, enemy, terrain, clock or video assignments.',private_pair_abi=self.pair_abi)
        path.write_text(json.dumps(report,indent=2)+'\n')


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--bundle',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--seed',type=lambda s:int(s,0),default=0xb4a7)
    ap.add_argument('--suite',choices=('fusions','memory','portal','wave'),default='fusions')
    args=ap.parse_args();r=Pairs(args.bundle,args.out)
    try:
        r.start(args.seed);r.tools()
        if args.suite=='fusions':r.green();r.blue();r.gold()
        else:getattr(r,args.suite)()
        r.scope_complete=all(c['passed'] for c in r.checks)
    except Exception as exc:r.errors.append(str(exc));raise
    finally:r.save()
    raise SystemExit(0 if r.scope_complete else 1)

if __name__=='__main__':main()

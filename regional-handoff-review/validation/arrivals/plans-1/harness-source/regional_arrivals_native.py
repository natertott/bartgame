#!/usr/bin/env python3
"""Check ordinary generated-interior arrival/return safety without Flippers.

Only fresh private SRAM, title seeds, ordinary regional room-load requests and
hero navigation/facing are fixtures. The ordinary three opening choices are
made through input. No inventory, health, enemies, outcome flags, terrain,
collision, camera or pixels are assigned. Actual A uses generated doors and
actual Down walks out. This is broad isolated access coverage, not unassisted
exploration or completion of these chambers. Paired/blue locked doors are
excluded here and covered by the real-unlock paired-event suite.
"""
import argparse
import json
from pathlib import Path

import probe as P
import release_boundary_review as B
from regional_native_support import NativeRun,sha
from regional_save_native import ABI


def request(r,p):
    before=r.snapshot()
    for name,value in [('sNextArea',p['area']),('sNextCell',p['cell']),('sNextSide',2),('sTransPhase',0)]:P.w8(r.c,B.static(name),value)
    if p['area']==3:
        for name,value in [('sCreamNextNode',p['cell']*2+p['terrace']),('sCreamNextFacing',0),('sCreamDropRows',0)]:P.w8(r.c,B.static(name),value)
        for name in ('sCreamNextX','sCreamNextY'):P.w16(r.c,B.static(name),65535)
    P.w8(r.c,P.sym('gGame'),r.abi['enum_transition']);r.fixtures.append(dict(kind='ordinary regional room-load for isolated arrival case',plan=p,before=before));r.settle(p['area']);r.dismiss();r.keys([],2)


def nav(r,x,y,face):
    actor=P.sym('gActors')
    for offset,value in ((8,x<<16),(12,y<<16)):P.w16(r.c,actor+offset,value&65535);P.w16(r.c,actor+offset+2,value>>16)
    P.w8(r.c,actor+7,face);r.fixtures.append(dict(kind='hero navigation/facing',x=x,y=y,facing=face))


def normal(r):
    # Ordinary action locks still apply to the review. Do not manufacture a
    # standing state or mistake pressing A during hurt recovery for a bad door.
    for _ in range(240):
        v=r.snapshot()
        if v['health'][0]<=0:raise RuntimeError('hero died; health is never reset by this review')
        if v['state']==r.abi['enum_play'] and v['actor']['state']==0 and not v['text']:return
        if v['text']:r.dismiss()
        else:r.keys([],1)
    raise RuntimeError('ordinary player control did not recover: '+str(r.snapshot()))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--bundle',required=True,type=Path);parser.add_argument('--out',required=True,type=Path);parser.add_argument('--seeds',nargs='+',default=['0xb4a7','1','3','13']);args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    abi=ABI(args.bundle);pa=abi.variable('regional_content.c','sPlan')[0];pf=abi.members('RegionalContentPlan');ps=abi.size('RegionalContentPlan');sa,st=abi.variable('handoff_events.c','s');sf=abi.members(st)
    selected={};checks=[];cases=[]
    def check(name,ok,detail=None):
        checks.append(dict(name=name,passed=bool(ok),detail=detail));print(('PASS ' if ok else 'FAIL ')+name,flush=True)
    for raw in args.seeds:
        seed=int(raw,0);r=NativeRun(args.bundle,args.out/('plans-'+str(seed)));r.start(seed);r.finish_draft();r.dismiss();r.keys([],2)
        for i in range(50):
            p={key:P.r8(r.c,pa+i*ps+offset) for key,offset in pf.items()}
            if p['interior_site']==255 or p['fusion_color']==1 or p['event_kind']==24:continue
            label=('mechanism-'+str(p['mechanism_variant']) if p['event_kind']==28 else 'traversal-'+str(p['traversal_variant']) if p['event_kind']==27 else 'event-'+str(p['event_kind']))
            selected.setdefault(label,dict(seed=seed,plan=p))
    check('all twelve generated mechanism entrances sampled',all('mechanism-'+str(i) in selected for i in range(12)),sorted(selected))
    check('all three generated traversal entrances sampled',all('traversal-'+str(i) in selected for i in range(3)),sorted(selected))
    check('all seventeen unsealed event families sampled',all('event-'+str(i) in selected for i in (1,2,3,4,5,6,7,8,9,10,11,12,13,14,23,25,26)),sorted(selected))
    for label,choice in sorted(selected.items()):
        r=None
        try:
            r=NativeRun(args.bundle,args.out/label);r.start(choice['seed']);r.finish_draft();r.dismiss();r.keys([],2);request(r,choice['plan'])
            # LI_FLIPPERS=0x46 is a stable original identifier; read-only control.
            owned=r.snapshot()['inventory']['owned'];check(label+': ordinary loadout has no Flippers',not(owned[70//32]&(1<<(70%32))),owned)
            door=r.snapshot()['spots']['door']
            for _ in range(6):
                normal(r);nav(r,door[0]*16+8,door[1]*16+24,0);r.keys([],1)
                if r.snapshot()['actor']['state']!=0:continue
                r.tap('A',3)
                if r.snapshot()['area']==r.abi['enum_handoff'] or r.snapshot()['state']==r.abi['enum_transition']:break
            r.settle(r.abi['enum_handoff']);r.dismiss()
            initial=r.snapshot();site=P.r8(r.c,sa+sf['site']);check(label+': actual door enters its dealt interior',site==choice['plan']['interior_site'],dict(choice=choice,initial=initial,site=site))
            observations=[]
            for _ in range(60):
                observations.append(r.snapshot());r.keys([],1)
            stable=r.snapshot();check(label+': standing arrival never drowns or falls',all(v['actor']['state'] not in (4,7) and v['area']==r.abi['enum_handoff'] for v in observations),dict(initial=initial,final=stable,states=sorted(set(v['actor']['state'] for v in observations))))
            check(label+': arrival stays alive without a reset loop',stable['health'][0]>0 and stable['area']==r.abi['enum_handoff'],stable);r.image('arrival')
            normal(r);nav(r,264,334,2);r.keys([],2)
            for _ in range(100):
                r.keys('DOWN',1)
                if r.snapshot()['state']!=r.abi['enum_play']:break
            r.settle(choice['plan']['area']);r.dismiss();r.keys([],40);returned=r.snapshot()
            check(label+': actual south exit returns to physical origin',returned['area']==choice['plan']['area'] and returned['cell']==choice['plan']['cell'] and returned['spots']['door']==door,returned)
            check(label+': return remains usable without bounce or fall',returned['state']==r.abi['enum_play'] and returned['actor']['state'] not in (4,7) and returned['health'][0]>0,returned);r.image('returned')
            case=dict(label=label,**choice,**r.report_identity(),initial=initial,final=returned,inputs=r.inputs)
            (r.out/'report.json').write_text(json.dumps(case,indent=2)+'\n');cases.append(dict(label=label,seed=choice['seed'],plan=choice['plan'],report=label+'/report.json'))
        except Exception as error:
            check(label+': complete access protocol',False,str(error))
            failure=dict(label=label,**choice,error=str(error))
            if r is not None:
                failure.update(**r.report_identity(),final=r.snapshot(),inputs=r.inputs)
                (r.out/'report.json').write_text(json.dumps(failure,indent=2)+'\n')
            cases.append(dict(label=label,seed=choice['seed'],plan=choice['plan'],error=str(error)))
    report=dict(method=__doc__,source_commit=(args.bundle/'source-commit.txt').read_text().strip(),rom_sha256=sha(args.bundle/'bartgame.gba'),tool_sha256=sha(__file__),checks=checks,cases=cases,passed=sum(c['passed'] for c in checks),total=len(checks));(args.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');raise SystemExit(report['passed']!=report['total'])


if __name__=='__main__':main()

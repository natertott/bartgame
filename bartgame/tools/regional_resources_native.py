#!/usr/bin/env python3
"""Survey actual regional field allocations and visible added objects in mGBA.

Fresh SRAM/title seed, ordinary room-load requests and hero position/facing are
explicit fixtures for this broad scene survey. No owned items, health, enemy
state, completion flags, terrain, collision, camera or framebuffer are assigned.
This verifies rendering/budgets; natural exploration and mechanics have their
own input-only suites.
"""
import argparse
import json
from pathlib import Path

import probe as P
import release_boundary_review as B
from regional_native_support import NativeRun,sha
from regional_save_native import ABI


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--bundle',required=True,type=Path);parser.add_argument('--out',required=True,type=Path);parser.add_argument('--seeds',nargs='+',default=['0xb4a7','1','3','13']);args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    checks=[];cases=[]
    def check(name,ok,detail):
        checks.append(dict(name=name,passed=bool(ok),detail=detail));print(('PASS ' if ok else 'FAIL ')+name,flush=True)
    for raw in args.seeds:
        seed=int(raw,0);r=NativeRun(args.bundle,args.out/('seed-'+str(seed)));abi=ABI(args.bundle)
        pa=abi.variable('regional_content.c','sPlan')[0];pf=abi.members('RegionalContentPlan');ps=abi.size('RegionalContentPlan')
        ra,rt=abi.variable('handoff_events.c','r');rf=abi.members(rt)
        r.start(seed);r.finish_draft();r.dismiss();r.keys([],4)
        plans=[{key:P.r8(r.c,pa+i*ps+off) for key,off in pf.items()} for i in range(50)]
        selected={}
        for p in plans:
            if p['interior_site']==255:continue
            labels=[]
            if p['quest_kind']:labels.append('quest')
            if p['has_wave']:labels.append('wave-'+str(p['area']))
            if p['fusion_color']!=255:labels.append('fusion-'+str(p['fusion_color']))
            if p['traversal_variant']!=255:labels.append('traversal-'+str(p['traversal_variant']))
            if p['field_mechanism_variant']!=255:labels.append('small-'+str(p['area']))
            for label in labels:selected.setdefault(label,p)
        # De-duplicate shared categories while retaining their labels.
        by_site={}
        for label,p in selected.items():by_site.setdefault(p['field_site'],dict(plan=p,labels=[]))['labels'].append(label)
        for case in by_site.values():
            p=case['plan'];before=r.snapshot()
            for name,value in [('sNextArea',p['area']),('sNextCell',p['cell']),('sNextSide',2),('sTransPhase',0)]:P.w8(r.c,B.static(name),value)
            if p['area']==3:
                for name,value in [('sCreamNextNode',p['cell']*2+p['terrace']),('sCreamNextFacing',0),('sCreamDropRows',0)]:P.w8(r.c,B.static(name),value)
                for name in ('sCreamNextX','sCreamNextY'):P.w16(r.c,B.static(name),65535)
            P.w8(r.c,P.sym('gGame'),r.abi['enum_transition'])
            r.fixtures.append(dict(kind='ordinary room-load request for isolated resource survey',plan=p,before=before))
            r.settle(p['area']);r.dismiss();r.keys([],4)
            spots=r.snapshot()['spots'];door=spots['door'];x=door[0]*16+8;y=door[1]*16+30
            actor=P.sym('gActors')
            for off,value in [(8,x<<16),(12,y<<16)]:P.w16(r.c,actor+off,value&65535);P.w16(r.c,actor+off+2,value>>16)
            P.w8(r.c,actor+7,0);r.fixtures.append(dict(kind='hero navigation to view generated doorway',x=x,y=y))
            # The real camera eases at at most4px per logic frame. Wait for
            # it instead of mistaking an offscreen entrance for missing art.
            r.keys([],4);door_tile=P.r16(r.c,ra+rf['door_tile'])&65535
            for _ in range(100):
                resources=r.resources()
                if any(o['tile']==door_tile for o in resources['world_oam']):break
                r.keys([],1)
            r.keys([],3);resources=r.resources()
            case.update(seed=seed,spots=spots,door_tile=door_tile,resources=resources,health=r.snapshot()['health'],observed=r.snapshot(),camera=[P.r16(r.c,P.sym('gCamX')),P.r16(r.c,P.sym('gCamY'))])
            label='field-'+str(p['area'])+'-'+str(p['cell'])
            r.image(label);case['image']=str(r.out.relative_to(args.out)/str(label+'.png'))
            check(raw+'/'+label+': no native allocation failures',resources['alloc_failures']==0,case)
            check(raw+'/'+label+': complete field graphics fit world tile budget',resources['next_tile'] is not None and resources['next_tile']<=resources['world_tile_limit'],case)
            check(raw+'/'+label+': generated doorway owns actual tile storage',bool(spots['flags']['door'] and door_tile),case)
            check(raw+'/'+label+': doorway is actually submitted to native OAM',any(o['tile']==door_tile for o in resources['world_oam']),case)
            check(raw+'/'+label+': observer did not die during survey',r.snapshot()['health'][0]>0,case)
            cases.append(case)
        (r.out/'trace.json').write_text(json.dumps(dict(**r.report_identity(),inputs=r.inputs),indent=2)+'\n')
    report=dict(method=__doc__,source_commit=(args.bundle/'source-commit.txt').read_text().strip(),rom_sha256=sha(args.bundle/'bartgame.gba'),tool_sha256=sha(__file__),support_sha256=sha(Path(__file__).with_name('regional_native_support.py')),checks=checks,cases=cases,passed=sum(c['passed'] for c in checks),total=len(checks))
    (args.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');raise SystemExit(report['passed']!=report['total'])


if __name__=='__main__':main()

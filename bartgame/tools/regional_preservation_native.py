#!/usr/bin/env python3
"""Keep the original Drain wizard, frog shop and cabinet accessible in mGBA.

Fresh private SRAM and the deterministic title seed are the only fixtures.
Opening gifts, walking across the existing bridge, facing, A/B interactions,
shop dismissal and cabinet tabs use actual inputs. No player position, health,
inventory, camera, actors, terrain, completion, menus or pixels are assigned.
"""
import argparse
import json
from pathlib import Path

import probe as P
import release_boundary_review as B
from regional_native_support import NativeRun, sha


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bundle',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    r=NativeRun(args.bundle,args.out);r.start(0xb4a7);r.finish_draft((0,0,2));r.dismiss();r.keys([],12)
    checks=[]
    def check(name,ok,observed=None):
        checks.append(dict(name=name,passed=bool(ok),observed=observed))
        print(('PASS ' if ok else 'FAIL ')+name,flush=True)
    def walk(x,y):
        for _ in range(1200):
            v=r.snapshot();px,py=v['actor']['x'],v['actor']['y']
            if v['area']!=r.abi['enum_sewer'] or v['state']!=r.abi['enum_play'] or v['text'] or v['service_menu']['active']:return False
            if abs(px-x)<=1 and abs(py-y)<=1:return True
            horizontal=abs(px-x)>1;delta=x-px if horizontal else y-py
            key=('RIGHT' if delta>0 else 'LEFT') if horizontal else ('DOWN' if delta>0 else 'UP')
            count=min(8,max(1,int((abs(delta)-1)/max(1.25,v['actor']['speed']/256))))
            before=(px,py);r.keys(key,count)
            if (r.snapshot()['actor']['x'],r.snapshot()['actor']['y'])==before:return False
        return False
    def front(x,y):
        v=r.snapshot()['actor']
        route=([(v['x'],142),(248,142),(248,270)] if v['y']<200 else [(v['x'],270)])
        route += [(248,270),(248,142),(x,142),(x,y)]
        return all(walk(*point) for point in route)
    def stat(name,obj):return P.r8(r.c,B.static(name,obj))
    check('real three-round opening completed',r.snapshot()['draft']['state']==r.abi['enum_draft_done'])
    ok=front(72,116);r.tap('A',20)
    check('original frog market has a natural dry approach',ok,r.snapshot())
    check('original Peddler shop opens independently of new Exchange',stat('sShopActive','text.o')==1 and stat('sDlgState','npc.o')==2 and not r.snapshot()['service_menu']['active'],r.snapshot())
    r.image('original-frog-shop')
    before=r.snapshot();r.tap('B',12);r.dismiss();r.keys([],8);after=r.snapshot()
    check('dismissing original shop spends no gilt and restores play',not stat('sShopActive','text.o') and not stat('sDlgState','npc.o') and before['gilt']==after['gilt'] and after['state']==r.abi['enum_play'],dict(before=before,after=after))
    ok=front(344,116);r.tap('A',12)
    check('original wizard remains naturally reachable',ok,r.snapshot())
    check('original wizard still opens named dialogue',stat('sDlgState','npc.o')==1 and r.u8('gTbActive') and not r.snapshot()['service_menu']['active'],r.snapshot())
    r.image('original-wizard-dialogue');r.dismiss();r.keys([],8)
    check('wizard dismissal restores ordinary Drain play',not stat('sDlgState','npc.o') and not r.u8('gTbActive') and r.snapshot()['state']==r.abi['enum_play'],r.snapshot())
    ok=front(392,132);r.tap('A',16)
    check('original memory cabinet has a natural dry approach',ok,r.snapshot())
    check('original cabinet opens through its real A interaction',stat('sActive','arcade.o') and r.snapshot()['state']!=r.abi['enum_play'] and not r.snapshot()['service_menu']['active'],r.snapshot())
    r.image('original-cabinet-items');first=r.u8('gArcadePage');r.tap('R',16)
    check('cabinet still changes between item and enemy pages',r.u8('gArcadePage')!=first,dict(before=first,after=r.u8('gArcadePage')))
    r.image('original-cabinet-enemies');r.tap('B',16);r.keys([],8)
    check('cabinet dismissal restores the same Drain location',not stat('sActive','arcade.o') and r.snapshot()['state']==r.abi['enum_play'] and abs(r.snapshot()['actor']['x']-392)<=1 and abs(r.snapshot()['actor']['y']-132)<=1,r.snapshot())
    r.image('original-cabinet-return')
    report=dict(**r.report_identity(),method=__doc__,inputs=r.inputs,checks=checks,passed=sum(c['passed'] for c in checks),total=len(checks),final=r.snapshot())
    (args.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    return report['passed']!=report['total']

if __name__=='__main__':raise SystemExit(main())

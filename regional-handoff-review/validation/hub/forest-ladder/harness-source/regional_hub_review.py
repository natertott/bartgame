#!/usr/bin/env python3
"""Reach ordinary Drain services and both ladders using real game controls.

The title seed and fresh private SRAM are the only fixtures. The test chooses
the opening gifts, walks, interacts and returns without assigning position,
facing, health, inventory, camera, menus, progression, terrain or pixels.
"""
import argparse
import json
from pathlib import Path

from regional_native_support import NativeRun,sha
import release_boundary_review as B


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    checks=[];cases=[]
    def check(name,ok,detail=None):
        checks.append(dict(name=name,passed=bool(ok),detail=detail))
        print(('PASS ' if ok else 'FAIL ')+name,flush=True)
    def fresh(name):
        r=NativeRun(a.bundle,a.out/name);r.start(0xb4a7);r.finish_draft(choices=(0,0,2));r.dismiss();r.keys([],12)
        check(name+': three gifts chosen through real opening',r.snapshot()['draft']['state']==r.abi['enum_draft_done'],r.snapshot())
        return r
    def walk(r,x,y,limit=1000):
        for _ in range(limit):
            v=r.snapshot();px,py=v['actor']['x'],v['actor']['y']
            if v['area']!=r.abi['enum_sewer'] or v['state']!=r.abi['enum_play'] or v['text'] or v['service_menu']['active']:
                return False
            if abs(px-x)<=1 and abs(py-y)<=1:return True
            delta=x-px if abs(px-x)>1 else y-py
            key=('RIGHT' if delta>0 else 'LEFT') if abs(px-x)>1 else ('DOWN' if delta>0 else 'UP')
            speed=max(1.25,v['actor']['speed']/256)
            count=min(8,max(1,int((abs(delta)-1)/speed)))
            before=(px,py);r.keys(key,count)
            if (r.snapshot()['actor']['x'],r.snapshot()['actor']['y'])==before:
                return False
        return False
    def front(r,x,y):
        current=r.snapshot()['actor']
        # The real central bridge crosses the sewer channel. All upper-bank
        # services/ladders use it, rather than a dry-map teleport fixture.
        route=([(current['x'],142),(248,142),(248,270)] if current['y']<200
               else [(current['x'],270)])
        route += [(248,270),(248,142),(x,142),(x,y)] if y<200 else [(x,270),(x,y)]
        return all(walk(r,*point) for point in route)
    def open_service(r,name,x,y,mode,key='A'):
        ok=front(r,x,y);before=r.snapshot();r.tap(key,12);after=r.snapshot()
        check(name+': real walk reaches interaction front',ok,before)
        check(name+': physical interaction opens expected service',
              after['area']==r.abi['enum_sewer'] and after['service_menu']['active']==mode,after)
        check(name+': service consumes item/roll input',after['bombs']==before['bombs'] and after['actor']['state']==0,dict(before=before,after=after))
        r.image(name)
        return ok and after['service_menu']['active']==mode
    def close(r):
        if r.snapshot()['service_menu']['active']:r.tap('B',12)
        r.dismiss();r.keys([],4)
    def record(r,name):
        data=dict(**r.report_identity(),method=__doc__,inputs=r.inputs,final=r.snapshot())
        (r.out/'report.json').write_text(json.dumps(data,indent=2)+'\n')
        cases.append(dict(name=name,path=r.out.name,identity=r.report_identity()))

    r=fresh('services')
    open_service(r,'extended-peddler',120,126,r.abi['enum_menu_shop']);close(r)
    open_service(r,'field-fusions',152,254,r.abi['enum_menu_fuse']);close(r)
    open_service(r,'regional-chain',304,254,r.abi['enum_menu_contract'])
    before=r.snapshot();r.tap('A',12);r.dismiss();r.keys([],6);after=r.snapshot()
    check('chain inspection does not teleport into a challenge',after['area']==r.abi['enum_sewer'] and before['chain']['target']==after['chain']['target'],dict(before=before,after=after))
    close(r)
    open_service(r,'guide-hint',304,254,r.abi['enum_menu_hint'],key='R');close(r)
    if open_service(r,'drain-inn',352,254,r.abi['enum_menu_inn']):
        before=r.snapshot()
        # This real opening seed gives200gilt in the observed reward round.
        # Pay the middle bed using that earned currency, never a money fixture.
        if before['gilt']>=200:
            r.tap('DOWN',4);r.tap('A',4);r.keys([],200);r.dismiss();r.keys([],8)
            after=r.snapshot()
            check('inn spends earned200gilt',after['gilt']==before['gilt']-200,dict(before=before,after=after))
            check('inn restores movement and places promised chest',after['actor']['state']==0 and after['inn_reward']!=0,after)
            if after['inn_reward']:
                ok=front(r,384,254);r.tap('A',12);r.dismiss()
                check('bed chest is physically claimed in Drain',ok and r.snapshot()['inn_reward']==0,r.snapshot())
                r.image('drain-bed-chest-claimed')
        else:
            check('test opening actually earns bed money',False,before)
    close(r)
    if open_service(r,'drain-trophy',416,254,r.abi['enum_menu_trophy']):
        before=r.snapshot()['entitlement'];r.tap('DOWN',4);r.tap('A',8);message=B.text_message(r.c);r.dismiss();r.keys([],8)
        if r.snapshot()['entitlement']==before:
            check('Trophy refuses to lock an accepted Cream objective',message.startswith('Finish your current Cream quest or seal'),dict(message=message,state=r.snapshot()))
            # Abandon through its actual offered UI, then demonstrate that an
            # otherwise available preference still changes and saves normally.
            close(r)
            if open_service(r,'chain-set-aside',304,254,r.abi['enum_menu_contract']):
                r.tap('DOWN',4);r.tap('DOWN',4);r.tap('A',8);r.dismiss();r.keys([],8)
                check('real guide can set optional seals aside',r.snapshot()['chain']['state']==0,r.snapshot())
            close(r)
            if open_service(r,'drain-trophy-uncommitted',416,254,r.abi['enum_menu_trophy']):
                r.tap('DOWN',4);r.tap('A',8);r.dismiss();r.keys([],8)
        check('real Trophy UI changes its available preference',r.snapshot()['entitlement']==(before^1),r.snapshot())
        # Return to ordinary mode through the same real service and save.
        if open_service(r,'drain-trophy-restore',416,254,r.abi['enum_menu_trophy']):
            r.tap('DOWN',4);r.tap('A',8);r.dismiss();r.keys([],8)
            check('real Trophy UI restores ordinary mode',r.snapshot()['entitlement']==before,r.snapshot())
    close(r);record(r,'services')

    r=fresh('cream-ladder');x=r.abi['hub_ladder_x'];y=r.abi['hub_ladder_return']
    ok=front(r,x,y);check('Cream ladder has a natural dry approach',ok,r.snapshot());r.image('cream-ladder-approach')
    frames=[]
    for _ in range(300):
        frames+=r.keys('UP',1,record=True)
        v=r.snapshot()
        if v['area']==r.abi['enum_cream'] and v['state']==r.abi['enum_play']:break
    r.dismiss();v=r.snapshot();check('walking up the second wall ladder enters Cream',v['area']==r.abi['enum_cream'],v);r.image('cream-arrival')
    if v['area']==r.abi['enum_cream']:
        r.tap('A',8);r.settle(r.abi['enum_sewer']);r.keys([],180);v=r.snapshot()
        check('Cream return remains below ladder without bounce',v['area']==r.abi['enum_sewer'] and abs(v['actor']['x']-x)<=1 and abs(v['actor']['y']-y)<=1,v)
        r.image('cream-ladder-return')
    if frames:frames[0].save(r.out/'cream-ladder-walk.gif',save_all=True,append_images=frames[1:],duration=17,loop=0)
    record(r,'cream-ladder')

    r=fresh('forest-ladder');ok=front(r,152,94);check('original Forest ladder approach remains dry',ok,r.snapshot());r.image('forest-ladder-approach')
    for _ in range(300):
        r.keys('UP',1)
        v=r.snapshot()
        if v['area']==r.abi['enum_forest'] and v['state']==r.abi['enum_play']:break
    check('original Forest ladder still enters Forest',r.snapshot()['area']==r.abi['enum_forest'],r.snapshot());r.image('forest-arrival');record(r,'forest-ladder')

    report=dict(method=__doc__,checks=checks,cases=cases,passed=sum(c['passed'] for c in checks),total=len(checks),
                rom_sha256=sha(a.bundle/'bartgame.gba'),tool_sha256=sha(__file__),
                source_commit=(a.bundle/'source-commit.txt').read_text().strip(),
                limits=['These are natural service/ladder deployment checks; alternate shop offers/beds and regional event completions have separate tests.'])
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    raise SystemExit(report['passed']!=report['total'])


if __name__=='__main__':main()

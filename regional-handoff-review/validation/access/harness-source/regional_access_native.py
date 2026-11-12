#!/usr/bin/env python3
"""Observe regional access, map locations and sprite budgets in real mGBA.

The Forest case walks from the genuine opening through the Drain and an open
regional border to an ordinary generated entrance. It never assigns position,
camera, inventory, health, enemies, progression, terrain or pixels. Separate
survey cases explicitly disclose normal-room-load and hero navigation fixtures;
they do not qualify as natural exploration or completed event interactions.
"""
from collections import deque
import argparse
import json
from pathlib import Path

import probe as P
import critical_path as C
import release_boundary_review as B
from regional_native_support import NativeRun,sha
from regional_save_native import ABI


class Access:
    def __init__(self,bundle,out):
        self.r=NativeRun(bundle,out);self.checks=[];self.movie=[]
        abi=ABI(bundle);self.plan_addr=abi.variable('regional_content.c','sPlan')[0]
        self.plan_size=abi.size('RegionalContentPlan');self.plan_fields=abi.members('RegionalContentPlan')
        self.defs={}
        for line in (Path(bundle)/'assets.h').read_text().splitlines():
            words=line.split()
            if len(words)==3 and words[0]=='#define' and words[2].isdigit():self.defs[words[1]]=int(words[2])

    def check(self,name,ok,detail=None):
        self.checks.append(dict(name=name,passed=bool(ok),detail=detail))
        print(('PASS ' if ok else 'FAIL ')+name,flush=True)
        return bool(ok)

    def line(self,x,y,limit=800):
        r=self.r
        for _ in range(limit):
            v=r.snapshot();p=v['actor'];dx=x-p['x'];dy=y-p['y']
            if v['health'][0]<=0 or v['text'] or v['state']!=r.abi['enum_play']:return False
            if abs(dx)<=2 and abs(dy)<=2:return True
            horizontal=abs(dx)>2;d=dx if horizontal else dy
            key=('RIGHT' if d>0 else 'LEFT') if horizontal else ('DOWN' if d>0 else 'UP')
            n=min(5,max(1,int((abs(d)-1)/max(1,p['speed']/256))))
            before=(p['x'],p['y']);self.movie.extend(r.keys(key,n,record=True))
            after=r.snapshot()['actor']
            if (after['x'],after['y'])==before:return False
        return False

    def walk(self,x,y):
        """Plan only from the actual loaded collision/type arrays; drive keys."""
        r=self.r;a=r.abi;room=P.sym('gRoom');w=P.r8(r.c,room+a['room_w'])*16;h=P.r8(r.c,room+a['room_h'])*16
        solid=bytes(P.r8(r.c,room+a['room_solid']+i) for i in range(4096))
        ground=[P.r16(r.c,room+a['room_ground']+i*2)&65535 for i in range(1024)]
        types=P.sym('metatile_type');forbidden={1,2,3,4,5,6,7,8,9,10,11,16,21}
        def clear(px,py):
            if px<5 or px+4>=w or py<8 or py>=h:return False
            for yy in range((py-8)//8,(py-1)//8+1):
                for xx in range((px-5)//8,(px+4)//8+1):
                    if solid[yy*64+xx]:return False
            mt=ground[((py-4)//16)*32+px//16]
            return mt!=65535 and P.r8(r.c,types+mt) not in forbidden
        p=r.snapshot()['actor'];start=(round(p['x']/8)*8,round((p['y']-4)/8)*8+4)
        goal=(round(x/8)*8,round((y-4)/8)*8+4)
        q=deque([start]);prev={start:None};found=None
        while q:
            at=q.popleft()
            if abs(at[0]-x)<=6 and abs(at[1]-y)<=6 and clear(*at):found=at;break
            for dx,dy in ((0,-8),(8,0),(0,8),(-8,0)):
                nxt=(at[0]+dx,at[1]+dy)
                if nxt in prev or not clear(*nxt) or not clear(at[0]+dx//2,at[1]+dy//2):continue
                prev[nxt]=at;q.append(nxt)
        if found is None:return False
        path=[]
        while found!=start:path.append(found);found=prev[found]
        path.reverse()
        # Retain corners, coalesce straight segments, then move by real input.
        points=[]
        for i,at in enumerate(path):
            if i==len(path)-1 or i==0 or (at[0]-path[i-1][0],at[1]-path[i-1][1])!=(path[i+1][0]-at[0],path[i+1][1]-at[1]):points.append(at)
        if not all(self.line(*at) for at in points):return False
        return self.line(x,y)

    def open_forest(self):
        r=self.r;r.start(0xb4a7);r.finish_draft();r.dismiss();r.keys([],12)
        # Walk across the actual Drain bridge and up the original wall ladder.
        ok=all(self.line(*point) for point in [(248,270),(248,142),(152,142),(152,94)])
        self.check('natural Drain bridge and Forest ladder approach',ok,r.snapshot())
        for _ in range(350):
            r.keys('UP',1)
            if r.snapshot()['area']==r.abi['enum_forest'] and r.snapshot()['state']==r.abi['enum_play']:break
        r.settle(r.abi['enum_forest']);r.dismiss();r.keys([],3)
        self.check('ordinary Forest arrival through wall ladder',r.snapshot()['area']==r.abi['enum_forest'],r.snapshot())
        return r.snapshot()

    def open_neighbor(self):
        r=self.r;a=r.abi;v=r.snapshot();cell=v['cell'];w=P.sym('gWorld')
        base=w+a['world_cells']+cell*a['cell_size'];sides=[i for i in range(4) if P.r8(r.c,base+a['cell_gate']+i)==1]
        if not sides:raise RuntimeError('review seed has no open ordinary border')
        # Prefer an unsealed ordinary event rather than a paired pocket. The
        # choice reads actual seeded metadata from this frozen ELF's DWARF.
        def plan(side):
            target=cell+(-5,1,5,-1)[side];p=self.plan_addr+target*self.plan_size
            return {name:P.r8(r.c,p+offset) for name,offset in self.plan_fields.items()}
        viable=[side for side in sides if plan(side)['fusion_color']!=1 and plan(side)['event_kind']!=24]
        if not viable:raise RuntimeError('review seed has no directly open ordinary event')
        side=viable[-1];x,y,key=C.door_inside(side)
        self.check('natural dry path to original border',self.walk(x,y),r.snapshot())
        for _ in range(260):
            r.keys(key,1)
            if r.snapshot()['state']==a['enum_transition']:break
        r.settle(a['enum_forest']);r.dismiss();r.keys([],3)
        self.check('natural original border reaches adjacent regional room',r.snapshot()['cell']==cell+(-5,1,5,-1)[side],r.snapshot())

    def map_check(self,name):
        r=self.r;a=r.abi;before=r.snapshot();r.tap('START',10);r.tap('SELECT',10);r.tap('R',80);r.tap('A',80);r.keys([],5)
        count=r.u8('gMenuMapMarkerCount');markers=[]
        for i in range(count):
            p=P.sym('gMenuMapMarkers')+i*a['menu_marker_size']
            markers.append({f:(P.r8(r.c,p+a['menu_marker_'+f]) if f in ('cell','kind','tile_x','tile_y') else P.r16(r.c,p+a['menu_marker_'+f])) for f in ('cell','kind','tile_x','tile_y','source_x','source_y','x','y')})
        door=before['spots']['door'];matching=[m for m in markers if m['cell']==before['cell'] and m['kind']==1 and [m['tile_x'],m['tile_y']]==door]
        self.check(name+': zoom exposes actual discovered door coordinates',bool(matching),dict(before=before,markers=markers,zoom=r.u8('gMenuStudyZoom')))
        r.image(name+'-map');r.tap('START',20);r.keys([],4)

    def door(self):
        r=self.r;before=r.snapshot();door=before['spots']['door'];x=door[0]*16+8;y=door[1]*16+14
        ok=self.walk(x,y+24)
        self.check('natural path reaches generated doorway approach',ok,r.snapshot())
        r.image('forest-door-approach');resource=r.resources();self.check('Forest added field allocations fit native OBJ budget',resource['alloc_failures'] in (None,0) and (resource['next_tile'] is None or resource['next_tile']<=resource['world_tile_limit']),resource)
        self.map_check('forest')
        # A works from the pictured lower approach; no hidden room-load call.
        r.keys('UP',1);r.keys([],2);r.tap('A',8)
        for _ in range(1300):
            v=r.snapshot()
            if v['area']==r.abi['enum_handoff'] and v['state']==r.abi['enum_play']:break
            if v['text']:r.dismiss()
            else:r.keys([],1)
        after=r.snapshot();self.check('actual A doorway enters regional interior',after['area']==r.abi['enum_handoff'],dict(before=before,after=after));r.image('forest-interior')
        if after['area']!=r.abi['enum_handoff']:return False
        # The ordinary room arrival is already at the interior's bottom exit.
        # Walk out and observe the saved physical origin, never request a load.
        for _ in range(90):
            r.keys('DOWN',1)
            if r.snapshot()['state']!=r.abi['enum_play']:break
        r.settle(r.abi['enum_forest']);r.dismiss();r.keys([],40);returned=r.snapshot()
        self.check('ordinary interior exit returns to its actual Forest room',returned['area']==before['area'] and returned['cell']==before['cell'] and returned['spots']['door']==door,returned)
        self.check('door return does not immediately bounce back',returned['state']==r.abi['enum_play'] and returned['area']==r.abi['enum_forest'],returned)
        self.check('returned door keeps a natural usable approach',self.walk(x,y+24),r.snapshot())
        for _ in range(180):
            r.keys('UP',1)
            if r.snapshot()['state']!=r.abi['enum_play']:break
        r.settle(r.abi['enum_handoff']);r.dismiss();r.keys([],3)
        self.check('walking north through pictured doorway enters the same interior',r.snapshot()['area']==r.abi['enum_handoff'],r.snapshot());r.image('forest-interior-walk-entry')
        return True

    def report(self):
        r=self.r
        if self.movie:self.movie[0].save(r.out/'natural-forest.gif',save_all=True,append_images=self.movie[1:],duration=67,loop=0)
        report=dict(**r.report_identity(),method=__doc__,checks=self.checks,passed=sum(c['passed'] for c in self.checks),total=len(self.checks),inputs=r.inputs,final=r.snapshot(),tool_sha256=sha(__file__))
        (r.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',required=True,type=Path);p.add_argument('--out',required=True,type=Path);args=p.parse_args()
    test=Access(args.bundle,args.out)
    try:test.open_forest();test.open_neighbor();test.door()
    except Exception as e:test.check('native sequence completed without exception',False,str(e))
    report=test.report();raise SystemExit(report['passed']!=report['total'])


if __name__=='__main__':main()

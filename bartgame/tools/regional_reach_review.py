#!/usr/bin/env python3
"""Independently solve actual C regional graphs and compare live reach masks.

The existing placement build provides production world/planner code and an
explicit host adapter. Exported primitive gate/edge/fact arrays are inputs to
this Python reference; expected reach never calls the production reach query.
Counted keys are edge costs in Forest. Cream uses directed component nodes,
with the Cape+Pacci conjunction. Original trial facts remain separate from
capabilities and opened bits. This is host graph proof, not native gameplay.
"""
from collections import Counter,deque
import argparse
import ctypes as C
import heapq
import json
from pathlib import Path
import time

from regional_placement_review import sha


def graph(lib):
    buffer=(C.c_uint8*2048)();length=lib.qa_reach_graph(buffer);data=list(buffer[:length]);at=0
    def take(n):
        nonlocal at
        value=data[at:at+n];at+=n;return value
    forest_entry,cream_entry=take(2)
    cells=[dict(zip(('n','e','s','w','opened','flags','myst'),take(7))) for _ in range(25)]
    trials=[dict(zip(('cell','side','key'),take(3))) for _ in range(3)]
    edges=[]
    for _ in range(50):edges.append([tuple(take(2)) for _ in range(take(1)[0])])
    terraces=take(25)
    if at!=length:raise ValueError(('graph serializer length disagreement',at,length))
    return dict(forest_entry=forest_entry,cream_entry=cream_entry,cells=cells,trials=trials,edges=edges,terraces=terraces)


def neighbor(cell,side):
    x,y=cell%5,cell//5;dx,dy=((0,-1),(1,0),(0,1),(-1,0))[side];x+=dx;y+=dy
    return y*5+x if 0<=x<5 and 0<=y<5 else None


def expected(g,items,keys,pacci):
    def trial_ready(cell,side):
        for t in g['trials']:
            if (cell,side) in ((t['cell'],t['side']),(neighbor(t['cell'],t['side']),(t['side']+2)%4)):
                key=g['cells'][t['key']]
                return bool(key['flags']&8 and key['myst']&4)
        return True
    pending=[(0,g['forest_entry'])];price={g['forest_entry']:0}
    while pending:
        cost,cell=heapq.heappop(pending)
        if cost!=price[cell]:continue
        for side,name in enumerate(('n','e','s','w')):
            nxt=neighbor(cell,side);c=g['cells'][cell];gate=c[name];opened=bool(c['opened']&(1<<side))
            if nxt is None or gate==0 or not trial_ready(cell,side):continue
            need={2:1,3:2,4:4,6:8}.get(gate,0)
            if not opened and need and not(items&need):continue
            total=cost+int(gate==5 and not opened)
            if total>keys or total>=price.get(nxt,999):continue
            price[nxt]=total;heapq.heappush(pending,(total,nxt))
    forest=sum(1<<cell for cell in price)
    tokens=(1 if items&2 else 0)|(2 if items&4 else 0)|(4 if items&8 and pacci else 0)
    seen={g['cream_entry']};pending=deque(seen)
    while pending:
        for nxt,require in g['edges'][pending.popleft()]:
            if nxt not in seen and tokens&require==require:seen.add(nxt);pending.append(nxt)
    cream=sum(1<<cell for cell in range(25) if cell*2+g['terraces'][cell] in seen)
    return [forest,cream]


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--placement-build',required=True,type=Path);parser.add_argument('--out',required=True,type=Path);parser.add_argument('--seeds',type=int,default=256);args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    lib=C.CDLL(str(args.placement_build/'regional-placement.so'));lib.qa_seed.argtypes=[C.c_uint32]
    lib.qa_reach_fixture.argtypes=[C.c_int]*5+[C.POINTER(C.c_uint32)]
    production=(C.c_uint32*2)();counter=Counter();failures=[];started=time.time()
    for seed in range(args.seeds):
        lib.qa_seed(seed)
        for caps in range(8):
            items=1|64|(caps<<1)
            for pacci in (0,1):
                for keys in (0,1,3):
                    for facts in (0,1,3,7):
                        for opened in (0,1):
                            lib.qa_reach_fixture(items,keys,pacci,facts,opened,production);g=graph(lib)
                            want=expected(g,items,keys,pacci);got=list(production);counter['mask_comparisons']+=1
                            if got!=want and len(failures)<20:failures.append(dict(seed=seed,items=items,keys=keys,pacci=pacci,facts=facts,opened=opened,expected=want,actual=got,graph=g))
                            if caps==0 and not pacci and not opened:
                                for area,region in ((1,0),(3,1)):
                                    for cell in range(25):
                                        actual=bool(lib.regional_content_reachable(area,cell));counter['site_wrapper_comparisons']+=1
                                        if actual!=bool(want[region]&(1<<cell)) and len(failures)<20:failures.append(dict(seed=seed,area=area,cell=cell,wrapper=actual,expected=want,items=items,keys=keys,facts=facts))
        if (seed+1)%64==0:print(str(seed+1)+' seeds; '+str(dict(counter))+'; failures='+str(len(failures)),flush=True)
    build=json.loads((args.placement_build/'report.json').read_text())
    report=dict(method=__doc__,passed=not failures,seeds=args.seeds,counts=dict(counter),failures=failures,tool_sha256=sha(__file__),actual_c_build=str(args.placement_build),library_sha256=sha(args.placement_build/'regional-placement.so'),source_commit=build['source_commit'],source_sha256=build['source_sha256'],host_adapters=build['adapters'],elapsed_seconds=time.time()-started)
    (args.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('passed','seeds','counts','elapsed_seconds')}));raise SystemExit(bool(failures))


if __name__=='__main__':main()

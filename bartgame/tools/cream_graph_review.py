#!/usr/bin/env python3
"""Compile the actual Cream C generator; audit directed capability-state mazes.

This is a host qualification, not an emulator image or a test of room pixels.
Every generated graph runs its actual C400-state no-trap solver. Selected
samples are independently reconstructed and solved in Python, including all
possible inherited capability masks. The fixed ROM certificate is exercised
explicitly, never inferred from a successful random seed.
"""
import argparse
from collections import Counter, deque
import ctypes as C
import hashlib
import json
from pathlib import Path
import subprocess
import time

GAME=Path(__file__).resolve().parent.parent
SHA=lambda data:hashlib.sha256(data).hexdigest()

class Edge(C.Structure):
    _fields_=[('target',C.c_uint8),('kind',C.c_uint8),('require',C.c_uint8),('flags',C.c_uint8)]
class World(C.Structure):
    _fields_=[('seed',C.c_uint32),('entry_node',C.c_uint8),('goal_node',C.c_uint8),
              ('reward_node',C.c_uint8*3),('attempts',C.c_uint8),('fallback',C.c_uint8),
              ('degree',C.c_uint8*50),('edges',(Edge*6)*50),('content',C.c_uint8*50),
              ('stage',C.c_uint8*50),('corruption',C.c_uint8*25),
              ('required_rooms',C.c_uint8),('required_steps',C.c_uint16)]

def plain(w):
    return dict(seed=w.seed,entry_node=w.entry_node,goal_node=w.goal_node,reward_node=list(w.reward_node),
                attempts=w.attempts,fallback=w.fallback,content=list(w.content),stage=list(w.stage),
                corruption=list(w.corruption),required_rooms=w.required_rooms,required_steps=w.required_steps,
                edges=[[dict(target=e.target,kind=e.kind,require=e.require,flags=e.flags)
                        for e in w.edges[n][:w.degree[n]]] for n in range(50)])

def independent(w):
    edges=w['edges'];rewards={node:1<<i for i,node in enumerate(w['reward_node'])}
    def claim(node,mask):
        bit=rewards.get(node,0)
        if bit and mask&(bit-1)==bit-1:mask|=bit
        return mask
    def onward(state):
        node,mask=state
        return [(e['target'],claim(e['target'],mask)) for e in edges[node] if mask&e['require']==e['require']]
    # The model has50 physical components, not25 undifferentiated rooms.
    reverse={};normalized=[]
    for node in range(50):
        for mask in range(8):
            if claim(node,mask)!=mask:continue
            state=(node,mask);normalized.append(state)
            for to in onward(state):reverse.setdefault(to,[]).append(state)
    goal=(w['goal_node'],7);winning={goal};queue=deque([goal])
    while queue:
        for previous in reverse.get(queue.popleft(),[]):
            if previous not in winning:winning.add(previous);queue.append(previous)
    all_reached=set();shortest=None
    for inherited in range(8):
        start=(w['entry_node'],claim(w['entry_node'],inherited));reached={start};queue=deque([start]);parents={start:None}
        while queue:
            cur=queue.popleft()
            for nxt in onward(cur):
                if nxt not in reached:reached.add(nxt);queue.append(nxt);parents[nxt]=cur
        assert goal in reached,'goal lacks capability-satisfying route'
        assert reached<=winning,'a legal jump/cave entry strands the player'
        if inherited==7:assert len({node for node,mask in reached})==50,'a physical terrace is unreachable'
        if inherited==0:
            path=[];cur=goal
            while cur is not None:path.append(cur);cur=parents[cur]
            shortest=list(reversed(path))
        all_reached|=reached
    assert len(shortest)-1==w['required_steps']
    assert len({node//2 for node,mask in shortest})==w['required_rooms']<25
    traversed=[]
    for (node,mask),(target,_) in zip(shortest,shortest[1:]):
        e=next(e for e in edges[node] if e['target']==target and mask&e['require']==e['require'])
        traversed.append(e)
    assert any(e['kind']==2 for e in traversed),'no climbing in solved route'
    assert any(e['flags']&1 for e in traversed),'multi-room descent never used'
    assert any(e['kind']==4 and not e['flags']&2 for e in traversed),'required nonlocal cave never used'
    assert w['entry_node']//10==4 and w['entry_node']%2==0
    assert w['goal_node']//10==0 and w['goal_node']%2==1
    assert w['corruption'][w['goal_node']//2]==2
    assert w['corruption'][w['entry_node']//2]==0 and max(w['corruption'])<=2
    for n,out in enumerate(edges):
        assert 0<len(out)<=6
        assert w['content'][n]&18!=18,'two rewards share one chest footprint'
        if len(out)<=1:assert w['content'][n]&~1,'empty dead end'
        for e in out:
            t=e['target'];assert 0<=t<50 and 0<=e['require']<=7
            r,c=n//10,(n//2)%5;tr,tc=t//10,(t//2)%5
            if e['kind']==1:assert r==tr and abs(c-tc)==1 and n%2==t%2
            elif e['kind']==2:assert c==tc and ((t==n+1 and n%2==0) or (tr==r-1 and n%2==1 and t%2==0))
            elif e['kind']==3:
                if e['flags']&1:assert c==tc and 2<=tr-r<=4 and n%2==1 and t%2==0
                else:assert c==tc and ((t==n-1 and n%2==1) or (tr==r+1 and n%2==0 and t%2==1))
            elif e['kind']==4:assert any(x['kind']==4 and x['target']==n for x in edges[t])
            else:raise AssertionError('unknown edge verb')
    return dict(reachable_states=len(all_reached),winning_states=len(winning),
                climbs=sum(e['kind']==2 for e in traversed),drops=sum(e['kind']==3 for e in traversed),
                long_drop_spans=[e['target']//10-n//10 for (n,m),e in zip(shortest,traversed) if e['flags']&1],
                cave_steps=sum(e['kind']==4 for e in traversed),solution=[list(s) for s in shortest])

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True);p.add_argument('--seeds',type=int,default=10000)
    p.add_argument('--independent',type=int,default=256);p.add_argument('--cc',default='gcc');a=p.parse_args()
    out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True);started=time.time()
    binary=out/'cream-world.so'
    cmd=[a.cc,'-shared','-fPIC','-O2','-w','-fno-builtin','-I',str(GAME/'src'),str(GAME/'src/cream_world.c'),'-o',str(binary)]
    result=subprocess.run(cmd,capture_output=True,text=True);(out/'compile.log').write_text(result.stdout+result.stderr);result.check_returncode()
    lib=C.CDLL(str(binary));lib.cream_generate.argtypes=[C.c_uint32];lib.cream_generate.restype=C.c_uint8
    lib.cream_generate_certified.argtypes=[C.c_uint32];lib.cream_generate_certified.restype=C.c_uint8
    lib.cream_world_validate.restype=C.c_uint8
    world=World.in_dll(lib,'gCreamWorld');attempts=Counter();peaks=Counter();drop_spans=Counter();steps=[];rooms=[];samples=[];fallbacks=0
    checks=[]
    def check(name,ok,detail=None):
        checks.append(dict(name=name,passed=bool(ok),detail=detail));print(('PASS ' if ok else 'FAIL ')+name,flush=True)
        if not ok:raise AssertionError(name)
    check('compact graph within1536bytes',C.sizeof(World)<=1536,C.sizeof(World))
    # First sequential seeds exercise small values/zero. Later cases spread
    # across the32-bit seed space using a bijective odd multiplier.
    for i in range(a.seeds):
        seed=i if i<a.seeds//2 else (i*0x9e3779b1)&0xffffffff
        assert lib.cream_generate(seed) and lib.cream_world_validate(),seed
        first=bytes(world);w=plain(world);assert lib.cream_generate(seed) and first==bytes(world),(seed,'nondeterminism')
        attempts[w['attempts']]+=1;peaks[w['goal_node']//2]+=1;steps.append(w['required_steps']);rooms.append(w['required_rooms']);fallbacks+=w['fallback']
        for n,edges in enumerate(w['edges']):
            for e in edges:
                if e['flags']&1:drop_spans[e['target']//10-n//10]+=1
        if i<a.independent:
            result=independent(w);samples.append(dict(graph=w,independent=result))
    check('actual C generator and no-trap state solver pass everyseed',True,a.seeds)
    check('deterministic graph bytes for everyseed',True,a.seeds)
    check('independent Python capability/geometry/dead-end solver passes',len(samples)==min(a.seeds,a.independent),len(samples))
    check('all five top-row peaks occur',set(peaks)==set(range(5)),dict(peaks))
    check('two-,three-,four-room descents all occur',set(drop_spans)=={2,3,4},dict(drop_spans))
    check('fresh capability route never requiresall25rooms',max(rooms)<25,dict(min=min(rooms),max=max(rooms)))
    certificate=[]
    for seed in (0,1,7,0xb4a7,0xdeadbeef,0xffffffff):
        assert lib.cream_generate_certified(seed) and lib.cream_world_validate()
        w=plain(world);certificate.append(dict(seed=seed,graph_sha256=SHA(bytes(world)),independent=independent(w)))
    check('explicit solved ROM fallback independently passesallinheritedinventories',True,len(certificate))
    report=dict(method=__doc__,checks=checks,passed=sum(c['passed'] for c in checks),total=len(checks),seeds=a.seeds,
                graph_bytes=C.sizeof(World),fallbacks=fallbacks,attempt_histogram=dict(attempts),peak_columns=dict(peaks),drop_span_histogram=dict(drop_spans),
                required_steps=dict(min=min(steps),max=max(steps),mean=sum(steps)/len(steps)),required_rooms=dict(min=min(rooms),max=max(rooms),mean=sum(rooms)/len(rooms)),
                samples=samples,certificates=certificate,source_sha256={n:SHA((GAME/n).read_bytes()) for n in ('src/cream_world.c','src/cream_world.h','src/cream_world_fallback.inc')},
                tool_sha256=SHA(Path(__file__).read_bytes()),compile_command=cmd,elapsed_seconds=round(time.time()-started,3))
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',report['passed'],'/',report['total'],'seeds',a.seeds,'fallbacks',fallbacks,'elapsed',report['elapsed_seconds'],flush=True)
    return int(report['passed']!=report['total'])
if __name__=='__main__':raise SystemExit(main())

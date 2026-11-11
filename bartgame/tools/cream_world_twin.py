#!/usr/bin/env python3
"""Independent Python Cream generator, compared with the unmodified C boundary.

Expected graphs are constructed using Python lists, explicit unsigned32 math,
independent canonical-state reverse traversal, and a manual wire serializer.
No C routine or parsed C data participates in Python generation. The C adapter
is used only after Python generation to obtain observed bytes for comparison.
The fixed certificate is independently reconstructed from its original shape
seed (0x4ce2a547, content seed0), rather than copied from C's literal graph.
This is host engineering proof; it does not simulate player input or pixels.
"""
from collections import Counter, deque
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import time

MASK=(1<<32)-1
GAME=Path(__file__).resolve().parent.parent

def mix(x):
    x&=MASK; x^=x>>16; x=x*0x7feb352d&MASK
    x^=x>>15; x=x*0x846ca68b&MASK; return x^(x>>16)

class Random:
    def __init__(self,state): self.state=state&MASK
    def next(self):
        x=self.state; x^=x<<13&MASK; x^=x>>17; x^=x<<5&MASK
        self.state=x&MASK; return self.state
    def pick(self,n): return self.next()%n

class Twin:
    def __init__(self,seed):
        self.seed=seed&MASK; self.entry=self.goal=255; self.rewards=[255]*3
        self.attempts=self.fallback=self.required_rooms=self.required_steps=0
        self.edges=[[] for _ in range(50)]
        self.content=[0]*50; self.stage=[255]*50; self.corruption=[0]*25
    @staticmethod
    def row(n): return n//10
    @staticmethod
    def col(n): return n//2%5
    @classmethod
    def altitude(cls,n): return (4-cls.row(n))*2+(n&1)
    def add(self,a,b,kind,require=0,flags=0):
        if len(self.edges[a])>=6:return False
        self.edges[a].append([b,kind,require,flags]); return True
    def remove(self,a,b):
        for i,e in enumerate(self.edges[a]):
            if e[0]==b:del self.edges[a][i];return
    def edge(self,a,b): return next(e for e in self.edges[a] if e[0]==b)
    def cave(self,n): return any(e[1]==4 for e in self.edges[n])
    def neighbor(self,n,d):
        row,col=self.row(n),self.col(n)
        if d==0:return n+1 if n%2==0 else n-11 if row else -1
        if d==1:return n+2 if col<4 else -1
        if d==2:return n-1 if n%2 else n+11 if row<4 else -1
        return n-2 if col else -1
    def tree(self,rng):
        stack=[self.entry]; seen={self.entry}
        while stack:
            n=stack[-1]; candidates=[self.neighbor(n,d) for d in range(4)]
            candidates=[to for to in candidates if to>=0 and to not in seen]
            if not candidates:stack.pop();continue
            to=candidates[rng.pick(len(candidates))]; delta=self.altitude(to)-self.altitude(n)
            self.add(n,to,2 if delta>0 else 3 if delta<0 else 1)
            self.add(to,n,3 if delta>0 else 2 if delta<0 else 1)
            seen.add(to);stack.append(to)
    def path(self,start=None,goal=None,cut=(-1,-1)):
        if start is None:start=self.entry
        if goal is None:goal=self.goal
        parents={start:start}; queue=deque([start])
        while queue:
            n=queue.popleft()
            if n==goal:break
            for to,kind,req,flags in self.edges[n]:
                if flags&2 or (n,to)==cut or (to,n)==cut or to in parents:continue
                parents[to]=n;queue.append(to)
        if goal<0:return set(parents)
        if goal not in parents:return []
        out=[goal]
        while out[-1]!=start:out.append(parents[out[-1]])
        return out[::-1]
    def long_drop(self,rng):
        path=self.path();length=len(path);start=rng.pick(max(1,length-1))
        for k in range(length-1):
            at=(start+k)%(length-1)
            if at<2 or at>length-4:continue
            side=self.path(goal=-1,cut=(path[at],path[at+1])); src=dst=-1;count=0
            for col in range(5):
                for row in range(3):
                    for span in range(2,5-row):
                        a=2*(row*5+col)+1;b=2*((row+span)*5+col)
                        if a in side and b not in side:
                            count+=1
                            if rng.pick(count)==0:src,dst=a,b
            if src<0:continue
            self.remove(path[at],path[at+1]);self.remove(path[at+1],path[at])
            return self.add(src,dst,3,0,1) and self.add(src,dst,4,7,2) and self.add(dst,src,4,7,2)
        return False
    def required_cave(self,rng):
        path=self.path();length=len(path);long_at=-1;source=target=-1;count=0
        if length<19:return False
        for a in range(length-1):
            if self.edge(path[a],path[a+1])[3]&1:long_at=a
        if long_at<0:return False
        for a in range(2,length-4):
            for b in range(a+2,min(length-1,a+9)):
                shortened=length-(b-a-1); moved=long_at-(b-a-1 if long_at>=b else 0)
                if a<=long_at<b:continue
                if shortened<17 or moved<2 or moved>shortened-5 or a>shortened-4 or abs(moved-a)<3:continue
                if self.cave(path[a]) or self.cave(path[b]):continue
                if abs(self.row(path[a])-self.row(path[b]))+abs(self.col(path[a])-self.col(path[b]))<2:continue
                if not any(abs(third-a)>=3 for third in range(moved+3,shortened-3)):continue
                count+=1
                if rng.pick(count)==0:source,target=a,b
        if source<0:return False
        cut=source+rng.pick(target-source)
        self.remove(path[cut],path[cut+1]);self.remove(path[cut+1],path[cut])
        return self.add(path[source],path[target],4) and self.add(path[target],path[source],4)
    def missions(self,rng):
        path=self.path();length=len(path);long_at=cave_at=third=-1;count=0
        if length<17:return False
        for i in range(length-1):
            e=self.edge(path[i],path[i+1])
            if e[3]&1:long_at=i
            if e[1]==4 and not e[3]&2:cave_at=i
        if long_at<2 or cave_at<2 or long_at>length-5 or cave_at>length-4 or abs(long_at-cave_at)<3:return False
        for i in range(long_at+3,length-3):
            if abs(i-cave_at)>=3:
                count+=1
                if rng.pick(count)==0:third=i
        if third<0:return False
        cuts=sorted([long_at,cave_at,third])
        cutpairs={(path[c],path[c+1]) for c in cuts}
        cutpairs|={(b,a) for a,b in list(cutpairs)}
        for phase in range(4):
            start=path[cuts[phase-1]+1] if phase else self.entry
            queue=deque([start]);self.stage[start]=phase
            while queue:
                n=queue.popleft()
                for to,kind,req,flags in self.edges[n]:
                    if flags&2 or (n,to) in cutpairs or self.stage[to]!=255:continue
                    self.stage[to]=phase;queue.append(to)
        for n in range(50):
            if self.stage[n]>3:return False
            for e in self.edges[n]:
                if e[3]&2:e[2]=7
                elif self.stage[e[0]]>self.stage[n]:e[2]=(1<<self.stage[e[0]])-1;e[3]|=4
                elif self.stage[e[0]]<self.stage[n]:e[3]|=4
        for phase in range(3):
            branch=[255]*50;queue=deque()
            for n in path:
                if self.stage[n]==phase:branch[n]=0;queue.append(n)
            while queue:
                n=queue.popleft()
                for to,kind,req,flags in self.edges[n]:
                    if flags&2 or self.stage[to]!=phase or branch[to]!=255:continue
                    branch[to]=branch[n]+1;queue.append(to)
            best=-1;score=-1000
            for n in range(50):
                if self.stage[n]!=phase or n==self.entry or self.cave(n):continue
                s=rng.next()&7
                if branch[n]:s+=16-min(20,branch[n]*2)
                if len(self.edges[n])==1:s+=6
                if s>score:score=s;best=n
            if best<0:return False
            self.rewards[phase]=best
        for n in range(50):
            h=mix(self.seed^((n*0x9e3779b9)&MASK));v=1
            if h&7==0:v|=4
            elif h&7==1:v|=8
            elif h&7<4:v|=2
            if len(self.edges[n])<=1 and not v&2:v|=2 if h&1 else 16
            self.content[n]=v
        for n in self.rewards:self.content[n]|=32
        self.content[self.entry]=136;self.content[self.goal]=64
        self.corruption=[min(2,(max(self.stage[2*i:2*i+2])*2+4-i//5)//4) for i in range(25)]
        self.corruption[self.entry//2]=0;self.corruption[self.goal//2]=2
        return True
    def claim(self,n,mask):
        mask&=7
        for i,r in enumerate(self.rewards):
            if n==r and mask&((1<<i)-1)==(1<<i)-1:mask|=1<<i
        return mask
    def onward(self,state):
        n,m=state
        return [(to,self.claim(to,m)) for to,kind,req,flags in self.edges[n] if m&req==req]
    def validate(self):
        if not 0<=self.entry<50 or not 0<=self.goal<50:return False
        if self.row(self.entry)!=4 or self.entry%2 or self.row(self.goal)!=0 or self.goal%2!=1:return False
        if self.corruption[self.entry//2]!=0 or self.corruption[self.goal//2]!=2 or max(self.corruption)>2:return False
        longs=caves=0;incoming=[set() for _ in range(50)]
        for n,out in enumerate(self.edges):
            if not 1<=len(out)<=6 or self.stage[n]>3 or self.content[n]&18==18:return False
            if len(out)<=1 and not self.content[n]&~1:return False
            for to,kind,req,flags in out:
                if to>=50 or req>7:return False
                incoming[to].add(n);dx=self.col(to)-self.col(n);dy=self.row(to)-self.row(n)
                if kind==1:
                    if abs(dx)!=1 or dy or to%2!=n%2:return False
                elif kind==2:
                    if dx or not ((to==n+1 and n%2==0) or (dy==-1 and n%2==1 and to%2==0)):return False
                elif kind==3:
                    if flags&1:
                        if dx or not 2<=dy<=4 or n%2!=1 or to%2!=0:return False
                        longs+=1
                    elif dx or not ((to==n-1 and n%2==1) or (dy==1 and n%2==0 and to%2==1)):return False
                elif kind==4:
                    if n//2==to//2 or not any(e[0]==n and e[1]==4 for e in self.edges[to]):return False
                    caves+=1
                else:return False
        if not longs or caves<4 or max(map(len,incoming))>6:return False
        if any(r>=50 or self.stage[r]!=i or not self.content[r]&32 for i,r in enumerate(self.rewards)):return False
        # Independently enumerate normalized states, then build their reverse
        # graph, instead of duplicating C's incoming-node/mask-inversion code.
        reverse={}
        for n in range(50):
            for m in range(8):
                if self.claim(n,m)!=m:continue
                state=(n,m)
                for nxt in self.onward(state):reverse.setdefault(nxt,[]).append(state)
        goal=(self.goal,7);winning={goal};queue=deque([goal])
        while queue:
            for previous in reverse.get(queue.popleft(),[]):
                if previous not in winning:winning.add(previous);queue.append(previous)
        reached={(self.entry,self.claim(self.entry,m)) for m in range(8)};queue=deque(reached)
        while queue:
            for nxt in self.onward(queue.popleft()):
                if nxt not in reached:reached.add(nxt);queue.append(nxt)
        return reached<=winning and all((n,7) in reached for n in range(50))
    def solution(self,mask=0):
        start=(self.entry,self.claim(self.entry,mask));parents={start:None};queue=deque([start])
        while queue:
            state=queue.popleft()
            if state==(self.goal,7):
                path=[]
                while state is not None:path.append(state[0]);state=parents[state]
                return path[::-1]
            for nxt in self.onward(state):
                if nxt not in parents:parents[nxt]=state;queue.append(nxt)
        return []
    @classmethod
    def candidate(cls,seed,shape):
        w=cls(seed);rng=Random(shape or 1)
        w.entry=2*(20+rng.pick(5));w.tree(rng);w.goal=2*rng.pick(5)+1
        if not w.long_drop(rng) or not w.required_cave(rng) or not w.missions(rng) or not w.validate():return None
        path=w.solution()
        if not 19<=len(path)<=200:return None
        w.required_rooms=len({n//2 for n in path})
        if w.required_rooms>22:return None
        w.required_steps=len(path)-1;return w
    @classmethod
    def certified(cls,seed):
        w=cls.candidate(0,0x4ce2a547)
        assert w is not None and w.validate()
        w.seed=seed&MASK;w.attempts=24;w.fallback=1;return w
    @classmethod
    def generate(cls,seed):
        seed&=MASK
        for attempt in range(24):
            w=cls.candidate(seed,mix(seed^0x43555244^(attempt*0x9e3779b9&MASK)))
            if w is not None:w.attempts=attempt+1;return w
        return cls.certified(seed)
    def serialize(self):
        out=bytearray(1392)
        struct.pack_into('<I',out,0,self.seed)
        out[4:11]=bytes([self.entry,self.goal,*self.rewards,self.attempts,self.fallback])
        out[11:61]=bytes(map(len,self.edges))
        for n,edges in enumerate(self.edges):
            for i in range(6):out[61+24*n+4*i:65+24*n+4*i]=bytes(edges[i] if i<len(edges) else [255,0,0,0])
        out[1261:1311]=bytes(self.content);out[1311:1361]=bytes(self.stage)
        out[1361:1386]=bytes(self.corruption);out[1386]=self.required_rooms
        struct.pack_into('<H',out,1388,self.required_steps)
        return bytes(out)

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True)
    p.add_argument('--seeds',type=int,default=1000);a=p.parse_args()
    out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True);started=time.time()
    src=[GAME/'src'/n for n in ['cream_world.c','cream_world.h','cream_world_fallback.inc']]
    hashes={str(f.relative_to(GAME)):sha(f) for f in src}
    # The comparison boundary is compiled from actual unmodified production C.
    binary=out/'cream-world.so'
    cmd=['gcc','-shared','-fPIC','-O2','-w','-fno-builtin','-I',str(GAME/'src'),str(src[0]),'-o',str(binary)]
    result=subprocess.run(cmd,capture_output=True,text=True);(out/'compile.log').write_text(result.stdout+result.stderr);result.check_returncode()
    lib=ctypes.CDLL(str(binary));observed=(ctypes.c_ubyte*1392).in_dll(lib,'gCreamWorld')
    for n in ['cream_generate','cream_generate_certified']:
        fn=getattr(lib,n);fn.argtypes=[ctypes.c_uint32];fn.restype=ctypes.c_uint8
    checks=[];cases=[];attempts=Counter();peaks=Counter();spans=Counter();digest=hashlib.sha256()
    def check(name,ok,detail=None):
        checks.append({'name':name,'passed':bool(ok),'detail':detail})
        if not ok:raise AssertionError((name,detail))
    symbols=subprocess.check_output(['nm','-S','--defined-only',str(binary)],text=True)
    symbol=next(line.split() for line in symbols.splitlines() if line.split()[-1]=='gCreamWorld')
    check('actual C world symbol is exactly1392bytes',int(symbol[1],16)==1392,int(symbol[1],16))
    def compare(seed,certificate=False):
        w=Twin.certified(seed) if certificate else Twin.generate(seed)
        expected=w.serialize()  # completed BEFORE calling the C boundary
        ok=getattr(lib,'cream_generate_certified' if certificate else 'cream_generate')(seed)
        actual=bytes(observed)
        mismatch=[i for i,(x,y) in enumerate(zip(expected,actual)) if x!=y]
        if mismatch:
            (out/'mismatch-python.bin').write_bytes(expected);(out/'mismatch-c.bin').write_bytes(actual)
        check(('certificate' if certificate else 'seed')+f' {seed:#010x}',ok and not mismatch,
              None if not mismatch else {'first_offset':mismatch[0],'python':expected[mismatch[0]],'c':actual[mismatch[0]],'bytes':len(mismatch)})
        digest.update(expected)
        cases.append({'seed':seed,'certificate':certificate,'attempts':w.attempts,'fallback':w.fallback,'sha256':hashlib.sha256(expected).hexdigest()})
        if not certificate:
            attempts[w.attempts]+=1;peaks[w.goal//2]+=1
            for n,edges in enumerate(w.edges):
                for to,kind,req,flags in edges:
                    if flags&1:spans[to//10-n//10]+=1
    # Boundary, PRNG-zero-input and mixed full-width seeds; deduplicate while
    # retaining order, then fill exactly --seeds generated cases.
    seeds=[0,1,MASK,0x80000000,0x7fffffff,0x43555244,0x4ce2a547,0xb4a7,0xdeadbeef]
    seeds+=list(range(max(0,a.seeds//2)))
    rng=Random(0x50a7c0de)
    while len(set(seeds))<a.seeds:seeds.append(rng.next())
    seeds=list(dict.fromkeys(seeds))[:a.seeds]
    for i,seed in enumerate(seeds):
        compare(seed)
        if (i+1)%100==0:print(f'{i+1}/{len(seeds)} complete',flush=True)
    for seed in [0,1,7,0xb4a7,0xdeadbeef,MASK]:compare(seed,True)
    check('all five peaks represented',set(peaks)==set(range(5)),dict(peaks))
    check('all long-drop spans represented',set(spans)=={2,3,4},dict(spans))
    check('production sources unchanged',hashes=={str(f.relative_to(GAME)):sha(f) for f in src})
    report={'tool':'independent Python/C whole-record generator equivalence','passed':all(c['passed'] for c in checks),
            'checks':checks,'generated_seeds':len(seeds),'explicit_certificates':6,'record_bytes':1392,
            'compared_bytes':1392*(len(seeds)+6),'cases':cases,'attempt_histogram':dict(attempts),
            'natural_fallbacks':sum(c['fallback'] for c in cases if not c['certificate']),
            'peak_histogram':dict(peaks),'drop_span_histogram':dict(spans),'combined_record_sha256':digest.hexdigest(),
            'source_sha256':hashes,'tool_sha256':sha(__file__),'seconds':time.time()-started,
            'scope':'Host proof of exact PRNG, integer, rejection, topology, gates, content, fields, unused slots and zero padding. Python generation never calls C or parses C output/source. Canonical-state validation is independent. Fixed certificate independently reconstructed from original shape seed with content seed0. Not emulator gameplay or an exhaustive32-bit seed proof.'}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['passed','generated_seeds','explicit_certificates','compared_bytes','natural_fallbacks','seconds']},indent=2))

if __name__=='__main__':main()

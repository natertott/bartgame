#!/usr/bin/env python3
"""Generate1528 original5x5 push puzzles with feasible/minimum certificates.
Templates use an exact assignment lower bound plus witness; maze minima use
push-state BFS with player-component canonicalization. D4 preserves proofs.
"""
from collections import deque
from itertools import permutations
import argparse,hashlib,json,random
from pathlib import Path
D=((0,-1),(1,0),(0,1),(-1,0))
def step(c,d):
 x,y=c%5,c//5;dx,dy=D[d];x+=dx;y+=dy
 return y*5+x if 0<=x<5 and 0<=y<5 else -1
def flood(walls,blocks,start):
 if start<0 or walls>>start&1 or start in blocks:return 0
 seen=1<<start;stack=[start];occupied=walls|sum(1<<x for x in blocks)
 while stack:
  for d in range(4):
   n=step(stack[-1],d)
   if n>=0 and not occupied>>n&1 and not seen>>n&1:seen|=1<<n;stack.insert(0,n)
  stack.pop()
 return seen
def legal(a,d):return a==0 or a==1 and d&1 or a==2 and not d&1
def solved(p,b,r):return sum(1<<x for x in b)==p['goals'] if p['kind']==0 else bool(r>>p['goal']&1)
def minimum(p,limit=10000):
 b=tuple(p['blocks']);r=flood(p['walls'],b,p['entry'])
 if solved(p,b,r):return 0,[]
 q=deque([(b,r,())]);seen={(b,r)}
 while q and len(seen)<=limit:
  bs,region,path=q.popleft()
  for i,c in enumerate(bs):
   for d in range(4):
    n=step(c,d);back=step(c,(d+2)&3)
    if not legal(p['axes'][i],d) or back<0 or not region>>back&1 or n<0 or p['walls']>>n&1 or n in bs or n in (p['entry'],p['goal']):continue
    out=list(bs);out[i]=n;out=tuple(out);nr=flood(p['walls'],out,c);np=path+(i*4+d,)
    if solved(p,out,nr):return len(np),list(np)
    key=(out,nr)
    if key not in seen:seen.add(key);q.append((out,nr,np))
 return None,None
def witness(p):
 bs=list(p['blocks']);player=p['player']
 if not flood(p['walls'],bs,p['entry'])>>player&1:return False
 for move in p['solution']:
  i,d=divmod(move,4);c=bs[i];n=step(c,d);back=step(c,(d+2)&3);r=flood(p['walls'],bs,player)
  if not legal(p['axes'][i],d) or n<0 or back<0 or not r>>back&1 or n in bs or p['walls']>>n&1 or n in (p['entry'],p['goal']):return False
  bs[i]=n;player=c
 return solved(p,bs,flood(p['walls'],bs,player))
def transform(p,t):
 def cell(c):
  x,y=c%5,c//5
  if t>=4:x=4-x
  for _ in range(t&3):x,y=4-y,x
  return y*5+x
 def direction(d):
  x,y=D[d]
  if t>=4:x=-x
  for _ in range(t&3):x,y=-y,x
  return D.index((x,y))
 o=dict(p)
 for k in ('walls','goals'):o[k]=sum(1<<cell(c) for c in range(25) if p[k]>>c&1)
 o['blocks']=[cell(c) for c in p['blocks']];o['axes']=[3-a if (t&1) and a else a for a in p['axes']]
 for k in ('entry','goal','player'):o[k]=cell(p[k])
 o['solution']=[m//4*4+direction(m&3) for m in p['solution']]
 return o
def signature(p):return p['kind'],p['walls'],p['goals'],tuple(p['blocks']),tuple(p['axes']),p['entry'],p['goal']
def candidate(rng,kind):
 entry,goal=22,2;axes=list(rng.choice([(0,1,2),(1,0,2),(1,2,0),(0,0,1),(0,2,0)]))
 if kind:
  walls=sum(1<<c for c in range(25) if c%5 in (0,4) or c//5 in (0,4))&~((1<<entry)|(1<<goal));possible=[6,8,11,13,16,18]
  for c in rng.sample(possible,rng.randrange(3)):walls|=1<<c
  spots=[c for c in possible if not walls>>c&1]
  if len(spots)<3:return
  bs=rng.sample(spots,3)
  if not flood(walls,bs,entry)>>goal&1:return
  goals=0
 else:walls=0;bs=rng.sample([c for c in range(25) if c not in (entry,goal)],3);goals=sum(1<<c for c in bs)
 original=bs[:];player=entry;undo=[]
 for _ in range(rng.randrange(12,45)):
  region=flood(walls,bs,player);moves=[]
  for i,c in enumerate(bs):
   for d in range(4):
    n=step(c,(d+2)&3);retreat=step(n,(d+2)&3) if n>=0 else -1
    if not legal(axes[i],d) or n<0 or retreat<0 or n in bs or retreat in bs or walls>>n&1 or walls>>retreat&1 or n in (entry,goal) or not region>>n&1:continue
    if not kind:
     old=abs(c%5-original[i]%5)+abs(c//5-original[i]//5);new=abs(n%5-original[i]%5)+abs(n//5-original[i]//5)
     if new<=old:continue
    moves.append((i,d,n,retreat))
  if not moves:break
  i,d,n,player=rng.choice(moves);bs[i]=n;undo.append(i*4+d)
 if not undo or len(undo)>32:return
 p=dict(kind=kind,walls=walls,goals=goals,blocks=bs,axes=axes,player=player,entry=entry,goal=goal,solution=list(reversed(undo)))
 if not flood(walls,bs,entry)>>player&1 or not witness(p):return
 if kind:
  if solved(p,bs,flood(walls,bs,entry)):return
  count,path=minimum(p)
  if count is None or not 1<=count<=20:return
  p['minimum']=count;p['solution']=path;p['player']=entry
 else:
  targets=[c for c in range(25) if goals>>c&1];bound=min(sum(abs(bs[i]%5-g[i]%5)+abs(bs[i]//5-g[i]//5) for i in range(3)) for g in permutations(targets))
  if bound!=len(undo) or not 2<=bound<=12:return
  p['minimum']=bound
 return p
def generate():
 rng=random.Random(0xB47C0DE);pool=[];seen=set();counts=[0,0];attempts=0
 while min(counts)<95 or sum(counts)<191:
  kind=0 if counts[0]<96 else 1;attempts+=1
  if attempts>300000:raise RuntimeError(('generation budget',counts))
  p=candidate(rng,kind)
  if not p:continue
  variants=[transform(p,t) for t in range(8)];keys=[signature(x) for x in variants]
  if len(set(keys))!=8 or any(k in seen for k in keys):continue
  assert all(witness(x) for x in variants)
  pool.extend(variants);seen.update(keys);counts[kind]+=1
 assert len(pool)==1528
 return pool,counts,attempts
def write(pool,path):
 lines=['/* Original generated puzzles: tools/handoff_puzzle_pool.py. */','static const HandoffPuzzle sPuzzlePool[HANDOFF_PUZZLE_COUNT] = {'];arr=lambda xs:'{'+','.join(str(x) for x in xs)+'}'
 for p in pool:lines.append(' {0x%08Xu,0x%08Xu,%s,%s,%d,%d,%d,%d,%d,%d,%s},'%(p['walls'],p['goals'],arr(p['blocks']),arr(p['axes']),p['player'],p['entry'],p['goal'],p['kind'],p['minimum'],len(p['solution']),arr(p['solution'])))
 path.write_text('\n'.join(lines+['};'])+'\n')
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',default='src/handoff_puzzles.inc');ap.add_argument('--report',default='/tmp/handoff-puzzles.json');ap.add_argument('--verify-seeds',type=int,default=1000);a=ap.parse_args();pool,counts,attempts=generate();out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True);write(pool,out);checks=0
 for i in range(a.verify_seeds):
  p=pool[(i*741+311)%len(pool)];assert witness(p);checks+=1
  if p['kind']:n,_=minimum(p);assert n==p['minimum'];checks+=1
  else:
   gs=[c for c in range(25) if p['goals']>>c&1];bound=min(sum(abs(p['blocks'][j]%5-g[j]%5)+abs(p['blocks'][j]//5-g[j]//5) for j in range(3)) for g in permutations(gs));assert bound==p['minimum'];checks+=1
 r=dict(seed=hex(0xB47C0DE),puzzles=len(pool),bases=counts,attempts=attempts,verification_seeds=a.verify_seeds,passed=checks,certificate_method='Feasible witness plus exact template Manhattan lower bound, or push-state BFS maze minimum; D4 proof-preserving transforms.',min_pushes=min(p['minimum'] for p in pool),max_pushes=max(p['minimum'] for p in pool),pool_sha256=hashlib.sha256(out.read_bytes()).hexdigest());Path(a.report).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
if __name__=='__main__':main()

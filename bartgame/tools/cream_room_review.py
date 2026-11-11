#!/usr/bin/env python3
"""Qualify actual Cream room C geometry against its directed state graph.

This uses the real cream_room.c and cream_world.c, native new metatile metadata,
and the engine's unchanged8px collision rules in a host adapter. It is not an
emulator capture, an AI movement test, or a substitute for the ROM smoke test.
"""
FIXTURE = r"""#include "room.h"
#include "util.h"
#include "cream_room.h"
#include "meta.inc"
Room gRoom;
s16 gCamX,gCamY;
u32 gRoomRevision;
u8 gAnimTiles;
u32 hash32(u32 a,u32 b) {u32 h=a*0x9E3779B1u^(b+0x7F4A7C15u);h^=h>>15;h*=0x85EBCA77u;h^=h>>13;h*=0xC2B2AE3Du;h^=h>>16;return h;}
void room_clear(int w,int h,u16 fill) {int i;gRoom.w=w;gRoom.h=h;for(i=0;i<1024;i++){gRoom.ground[i]=gRoom.underlay[i]=fill;gRoom.overlay[i]=MT_NONE;}}
void room_set(int x,int y,u16 mt){if(x<0||y<0||x>=gRoom.w||y>=gRoom.h)return;gRoom.ground[y*32+x]=mt;if(mt==MT_NONE||!metatile_prop[mt])gRoom.underlay[y*32+x]=mt;}
void room_set_overlay(int x,int y,u16 mt){if(x>=0&&y>=0&&x<gRoom.w&&y<gRoom.h)gRoom.overlay[y*32+x]=mt;}
u16 room_get(int x,int y){return x<0||y<0||x>=gRoom.w||y>=gRoom.h?MT_BLACK:gRoom.ground[y*32+x];}
u16 room_get_overlay(int x,int y){return x<0||y<0||x>=gRoom.w||y>=gRoom.h?MT_NONE:gRoom.overlay[y*32+x];}
u8 room_type(int x,int y){u16 mt=room_get(x,y);return mt==MT_NONE?TT_SOLID:metatile_type[mt];}
u8 room_type_px(int x,int y){return x<0||y<0?TT_SOLID:room_type(x>>4,y>>4);}
void room_build_solid(void){int x,y;memset(gRoom.solid,1,sizeof(gRoom.solid));for(y=0;y<gRoom.h;y++)for(x=0;x<gRoom.w;x++){u16 mt=room_get(x,y),ov=room_get_overlay(x,y);u8 mask=mt==MT_NONE?15:metatile_coll[mt];if(ov!=MT_NONE&&metatile_coll[ov]&&metatile_type[ov]!=TT_FLOOR)mask|=metatile_coll[ov];u8*s=&gRoom.solid[(y*2)*64+x*2];s[0]=(mask>>3)&1;s[1]=(mask>>2)&1;s[64]=(mask>>1)&1;s[65]=mask&1;}}
void room_render(void){}
bool8 room_solid_px(int x,int y){return x<0||y<0||x>=gRoom.w*16||y>=gRoom.h*16?1:gRoom.solid[(y>>3)*64+(x>>3)];}
bool8 room_box_solid(int x0,int y0,int x1,int y1){int x,y;if(x0<0||y0<0||x1>=gRoom.w*16||y1>=gRoom.h*16)return 1;for(y=y0>>3;y<=y1>>3;y++)for(x=x0>>3;x<=x1>>3;x++)if(gRoom.solid[y*64+x])return 1;return 0;}
"""

import ctypes as C,sys,json,collections,time,argparse,re,subprocess
from pathlib import Path
GAME=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True);p.add_argument('--seeds',type=int,default=256);a=p.parse_args()
out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(GAME/'art'))
import cream_terrain as terrain
import cream_graph_review as G
header=(GAME/'build/gen/assets.h').read_text()
base=int(re.search(r'#define METATILE_COUNT (\d+)',header).group(1))+1
header=re.sub(r'^#define MT_CREAM_[^\n]*\n','',header,flags=re.M)
header=re.sub(r'#define METATILE_COUNT \d+','#define METATILE_COUNT %d'%(base+len(terrain.METATILES)),header)
if '#define TT_CLIMB ' not in header:header+='\n#define TT_CLIMB 26\n'
header+='\n'+'\n'.join('#define MT_%s %d'%(m['name'].upper(),base+i) for i,m in enumerate(terrain.METATILES))+'\n'
(out/'assets.h').write_text(header)
types={k:int(v) for k,v in re.findall(r'#define TT_(\w+) (\d+)',header)};metadata=[]
for key in ('type','coll','prop'):
 values=[1 if key=='type' else 15 if key=='coll' else 0]*base
 values += [types[m['type']] if key=='type' else m.get(key,0) for m in terrain.METATILES]
 metadata.append('const u8 metatile_%s[]={%s};'%(key,','.join(map(str,values))))
(out/'meta.inc').write_text('\n'.join(metadata))
(out/'room_host.c').write_text(FIXTURE)
command=['gcc','-shared','-fPIC','-O2','-w','-fno-builtin','-I',str(out),'-I',str(GAME/'src'),str(GAME/'src/cream_world.c'),str(GAME/'src/cream_room.c'),str(out/'room_host.c'),'-o',str(out/'room.so')]
result=subprocess.run(command,capture_output=True,text=True);(out/'compile.log').write_text(result.stdout+result.stderr);result.check_returncode()
lib=C.CDLL(str(out/'room.so'));w=G.World.in_dll(lib,'gCreamWorld')

class Spot(C.Structure):_fields_=[('x',C.c_uint8),('y',C.c_uint8)]
class Terrace(C.Structure):_fields_=[('spawns',Spot*6),('spawn_count',C.c_uint8),('content',C.c_uint8),('chest',Spot),('npc',Spot),('heal',Spot),('cache',Spot),('mission',Spot)]
class Info(C.Structure):_fields_=[('cell',C.c_uint8),('stage',C.c_uint8),('motif',C.c_uint8),('climb_x',C.c_uint8),('upper_bottom',C.c_uint8*32),('lower_top',C.c_uint8*32),('terrace',Terrace*2),('return_door',Spot)]
class Room(C.Structure):_fields_=[('w',C.c_uint8),('h',C.c_uint8),('ground',C.c_uint16*1024),('overlay',C.c_uint16*1024),('solid',C.c_uint8*4096),('underlay',C.c_uint16*1024)]
class Route(C.Structure):_fields_=[('edge',C.c_uint8),('mode',C.c_uint8),('target',C.c_uint8),('rows',C.c_uint8),('x',C.c_int16),('y',C.c_int16)]
info=Info.in_dll(lib,'gCreamRoom');room=Room.in_dll(lib,'gRoom');opened=(C.c_uint8*50).in_dll(lib,'gCreamOpenEdges')
lib.cream_generate.argtypes=[C.c_uint32];lib.cream_generate.restype=C.c_uint8
lib.room_box_solid.restype=C.c_uint8;lib.room_type.restype=C.c_uint8;lib.cream_room_route.restype=C.c_uint8
lib.cream_room_arrival.argtypes=[C.c_int,C.POINTER(G.Edge),C.POINTER(C.c_int),C.POINTER(C.c_int),C.POINTER(C.c_int)]
fails=[];count=collections.Counter();samples=[]
def check(ok,name,detail):
 count[name]+=1
 if not ok and len(fails)<30:fails.append(dict(name=name,**detail))
def dry(x,y,t):
 typ=lib.room_type(x,y)
 return typ in (0,24,26) and not lib.room_box_solid(x*16+2,y*16+6,x*16+13,y*16+13) and (typ==26 or lib.cream_room_terrace_at(x*16+8,y*16+14,t)==t)
def flood(t):
 valid={(x,y) for y in range(24) for x in range(32) if dry(x,y,t)}
 # Climb stripes intentionally join floor components; constrain this walk-only
 # test to dry floor in the requested terrace.
 valid={p for p in valid if lib.room_type(*p)!=26}
 start=min(valid,key=lambda p:abs(p[0]-16)+abs(p[1]-(6 if t else 19)))
 seen={start};q=[start]
 for x,y in q:
  for p in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
   if p in valid and p not in seen:seen.add(p);q.append(p)
 return seen
for seed in range(a.seeds):
 assert lib.cream_generate(seed)
 for n in range(50):opened[n]=63
 for cell in range(25):
  lib.cream_room_build(cell);count['rooms']+=1
  if seed<2:samples.append(dict(seed=seed,cell=cell,stage=info.stage,ground=list(room.ground)[:24*32],overlay=list(room.overlay)[:24*32],underlay=list(room.underlay)[:24*32]))
  prior=(bytes(room),bytes(info));preview=Info();mask=(C.c_uint8*768)();lib.cream_room_preview(cell,C.byref(preview),mask)
  check(prior==(bytes(room),bytes(info)),'pure_preview',dict(seed=seed,cell=cell))
  check(all(bytes(getattr(preview.terrace[t],n))==bytes(getattr(info.terrace[t],n)) for t in (0,1) for n in ('chest','npc','heal','cache','mission')),'preview_spots',dict(seed=seed,cell=cell))
  seen=[flood(t) for t in (0,1)]
  if cell==w.entry_node//2:
   d=info.return_door;check((d.x,d.y+1) in seen[0] and (d.x+1,d.y+1) in seen[0],'entry_return_front',dict(seed=seed,cell=cell,xy=[d.x,d.y]))
  for t in (0,1):
   node=cell*2+t;p=info.terrace[t];d=dict(seed=seed,cell=cell,t=t)
   check(p.spawn_count>0,'safe_spawn',d)
   for i in range(p.spawn_count):check((p.spawns[i].x,p.spawns[i].y) in seen[t],'enemy_spawn',d|dict(i=i,xy=[p.spawns[i].x,p.spawns[i].y]))
   for flag,name in ((2,'chest'),(4,'npc'),(8,'heal'),(16,'cache'),(32,'mission')):
    if p.content&flag:
     pos=getattr(p,name);near=any(abs(x-pos.x)<=1 and abs(y-(pos.y+1))<=1 for x,y in seen[t]);check(near,'content_'+name,d|dict(xy=[pos.x,pos.y]))
   for i in range(w.degree[node]):
    e=w.edges[node][i];target=e.target//2;x=16*16;y=(6 if t else 19)*16+14;face=0;intent=0
    if e.kind==1:x=10 if target%5<cell%5 else 502;intent=32 if x==10 else 16
    elif e.kind==2:
     x=info.climb_x*16+16
     y=min(info.upper_bottom[info.climb_x],info.upper_bottom[info.climb_x+1])*16+12 if target==cell else 16;intent=64
    elif e.kind==3:
     xx=C.c_int();yy=C.c_int();lib.cream_room_drop_pos(node,i,C.byref(xx),C.byref(yy));x,y=xx.value,yy.value;intent=128
    elif e.kind==4:
     xx=C.c_int();yy=C.c_int();lib.cream_room_cave_pos(t,C.byref(xx),C.byref(yy));x,y=xx.value,yy.value;intent=64
    route=Route();ok=lib.cream_room_route(node,x,y,face,intent,C.byref(route))
    check(ok and route.edge==i,'edge_trigger',d|dict(edge=i,kind=e.kind,xy=[x,y],found=[ok,route.edge,route.mode]))
    if e.kind in (1,3,4):
     tile=(x//16,(y-4)//16)
     if e.kind==4:
      front=(7,(6 if t else 19)+2);reachable=front in seen[t] and all(not lib.room_box_solid(x-4,yy-7,x+3,yy-1) for yy in range(y,y+32))
     else:reachable=tile in seen[t]
     check(reachable,'edge_approach',d|dict(edge=i,kind=e.kind,xy=tile))
    px=C.c_int();py=C.c_int();f=C.c_int();lib.cream_room_arrival(node,C.byref(e),C.byref(px),C.byref(py),C.byref(f));land=(px.value,py.value)
    # Build the target after arrival: this catches source-profile leakage.
    lib.cream_room_build(target)
    ok=not lib.room_box_solid(land[0]-4,land[1]-7,land[0]+3,land[1]-1)
    check(ok,'arrival_clear',d|dict(edge=i,kind=e.kind,target=e.target,xy=land))
    lib.cream_room_build(cell)
 # Closed barriers must have a complete, reachable physical footprint, then
 # restore their route's correct native floor/climb/cave after actual use.
 if seed<32:
  for n in range(50):opened[n]=0
  for cell in range(25):
   lib.cream_room_build(cell)
   for t in (0,1):
    node=cell*2+t
    for i in range(w.degree[node]):
     e=w.edges[node][i]
     if not e.require or e.require==4:continue
     target=e.target//2;cx=info.climb_x;wy=6 if t else 19
     x0=cx;x1=cx+1;y0=y1=info.lower_top[cx]
     if e.kind==1:x0=x1=1 if target%5<cell%5 else 30;y0=wy-1;y1=wy+1
     elif e.kind==4:x0=6;x1=7;y0=y1=wy
     elif e.kind==2 and target!=cell:y0=y1=2
     elif e.kind==3:
      xx=C.c_int();yy=C.c_int();lib.cream_room_drop_pos(node,i,C.byref(xx),C.byref(yy));x0=xx.value//16-1;x1=x0+1;y0=y1=yy.value//16
     expected=9 if e.require==1 else 10 if e.require in (2,3) else 1
     d=dict(seed=seed,cell=cell,t=t,edge=i,require=e.require)
     check(all(lib.room_type(x,y)==expected for y in range(y0,y1+1) for x in range(x0,x1+1)),'gate_footprint',d)
     if e.require==7:lib.cream_room_unlock_edge(node,i)
     else:lib.cream_room_gate_cleared(x0,y0)
     check(bool(opened[node]&(1<<i)),'gate_persistence',d)
     check(all(lib.room_type(x,y) in (0,24,26) for y in range(y0,y1+1) for x in range(x0,x1+1)),'gate_native_restore',d)
     # Rebuild closed for each test: opening one reciprocal edge must not
     # invalidate the next footprint assertion in this room.
     for n in range(50):opened[n]=0
     lib.cream_room_build(cell)
print(json.dumps(dict(counts=count,failures=fails),indent=2));(out/'report.json').write_text(json.dumps(dict(counts=count,failures=fails),indent=2))
(out/'rooms.json').write_text(json.dumps(dict(base=base,rooms=samples)))
raise SystemExit(bool(fails))

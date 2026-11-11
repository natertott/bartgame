#!/usr/bin/env python3
"""Batch actual Cream C geometry with a single native host process.

Reuses cream_room_review.py's explicit8px collision/metadata adapter. Per seed,
all25 actual rooms are built once and cached in host memory; no mock topology
or procedural geometry replaces C. C then floods both dry components and
checks every route, actual target clearance, spawn and content approach.
This is host geometry evidence, not native AI/input/timing qualification.
"""
import argparse,hashlib,json,subprocess,time
from pathlib import Path
GAME=Path(__file__).resolve().parents[1]
C=r'''
#include <stdio.h>
#include <stdlib.h>
#include "cream_room.h"
#include "room.h"
#include "actor.h"
static Room rooms[CC_ROOMS];
static CreamRoomInfo infos[CC_ROOMS];
static u8 seen[2][768],valid[768];
static u32 count_rooms,count_routes,count_arrivals,count_spawns,count_content,count_returns,failures;
static u32 current_seed;
static int current_cell,current_t;
static void check(int okay,const char* why){if(!okay){if(failures<12)fprintf(stderr,"seed%u room%d terrace%d %s\n",current_seed,current_cell,current_t,why);failures++;}}
static int solid(const Room*r,int x0,int y0,int x1,int y1){int x,y;if(x0<0||y0<0||x1>=r->w*16||y1>=r->h*16)return 1;for(y=y0>>3;y<=y1>>3;y++)for(x=x0>>3;x<=x1>>3;x++)if(r->solid[y*64+x])return 1;return 0;}
static void flood(int terrace){
 int x,y,n,start=-1,best=99999,head=0,tail=0;u16 q[768];
 for(n=0;n<768;n++){x=n%32;y=n/32;int t=room_type(x,y),d=ABS(x-16)+ABS(y-(terrace?6:19));valid[n]=(t==TT_FLOOR||t==TT_MYST)&&!room_box_solid(x*16+2,y*16+6,x*16+13,y*16+13)&&cream_room_terrace_at(x*16+8,y*16+14,terrace)==terrace;seen[terrace][n]=0;if(valid[n]&&d<best){start=n;best=d;}}
 check(start>=0,"no dry component");if(start<0)return;
 q[tail++]=start;seen[terrace][start]=1;
 while(head<tail){n=q[head++];x=n%32;y=n/32;const int dx[4]={0,1,0,-1},dy[4]={-1,0,1,0};for(int i=0;i<4;i++){int xx=x+dx[i],yy=y+dy[i],nn=yy*32+xx;if(xx<0||xx>=32||yy<0||yy>=24||!valid[nn]||seen[terrace][nn])continue;seen[terrace][nn]=1;q[tail++]=nn;}}
}
static int nearby(Spot p,int t){int x,y;for(y=p.y;y<=p.y+2;y++)for(x=p.x-1;x<=p.x+1;x++)if(x>=0&&x<32&&y>=0&&y<24&&seen[t][y*32+x])return 1;return 0;}
int main(int argc,char**argv){u32 limit=argc>1?(u32)strtoul(argv[1],0,0):1000;
 for(current_seed=0;current_seed<limit;current_seed++){
  check(cream_generate(current_seed),"invalid state graph");
  for(int n=0;n<50;n++)gCreamOpenEdges[n]=63;
  for(current_cell=0;current_cell<25;current_cell++){cream_room_build(current_cell);rooms[current_cell]=gRoom;infos[current_cell]=gCreamRoom;count_rooms++;}
  for(current_cell=0;current_cell<25;current_cell++){
   gRoom=rooms[current_cell];gCreamRoom=infos[current_cell];
   flood(0);flood(1);
   for(current_t=0;current_t<2;current_t++){
    int node=current_cell*2+current_t;CreamTerraceSpots*p=&gCreamRoom.terrace[current_t];
    check(p->spawn_count>0,"no safe spawn");
    for(int j=0;j<p->spawn_count;j++){Spot z=p->spawns[j];check(z.x<32&&z.y<24&&seen[current_t][z.y*32+z.x],"unreachable enemy spawn");count_spawns++;}
    if(p->content&CC_CONTENT_ENTRY){Spot z=gCreamRoom.return_door;check(z.y+1<24&&seen[current_t][(z.y+1)*32+z.x],"hub return arch lacks dry front");count_returns++;}
    Spot features[5]={p->chest,p->npc,p->heal,p->cache,p->mission};
    const int flags[5]={2,4,8,16,32};
    for(int j=0;j<5;j++)if(p->content&flags[j]){check(nearby(features[j],current_t),"unreachable content front");count_content++;}
    for(int j=0;j<gCreamWorld.degree[node];j++){
     const CreamEdge*e=&gCreamWorld.edges[node][j];int target=e->target/2,x=256,y=(current_t?6:19)*16+14,face=0;u16 intent=0;CreamRoomRoute route;
     if(e->kind==CC_WALK){x=target%5<current_cell%5?10:502;intent=x==10?KEY_LEFT:KEY_RIGHT;}
     else if(e->kind==CC_CLIMB){x=gCreamRoom.climb_x*16+16;y=target==current_cell?MIN(gCreamRoom.upper_bottom[gCreamRoom.climb_x],gCreamRoom.upper_bottom[gCreamRoom.climb_x+1])*16+12:16;intent=KEY_UP;}
     else if(e->kind==CC_DROP){cream_room_drop_pos(node,j,&x,&y);intent=KEY_DOWN;}
     else if(e->kind==CC_CAVE){cream_room_cave_pos(current_t,&x,&y);intent=KEY_UP;}
     check(cream_room_route(node,x,y,face,intent,&route)&&route.edge==j,"route trigger disagrees");count_routes++;
     if(e->kind==CC_WALK||e->kind==CC_DROP||e->kind==CC_CAVE){int okay=0;if(e->kind==CC_CAVE){okay=seen[current_t][((current_t?6:19)+2)*32+7];for(int yy=y;yy<y+32;yy++)okay=okay&&!room_box_solid(x-4,yy-7,x+3,yy-1);}else{int xx=x/16,yy=(y-4)/16;okay=xx>=0&&xx<32&&yy>=0&&yy<24&&seen[current_t][yy*32+xx];}check(okay,"route lacks reachable dry approach");}
     int px,py;cream_room_arrival(node,e,&px,&py,&face);check(!solid(&rooms[target],px-4,py-7,px+3,py-1),"target landing collides");count_arrivals++;
    }
   }
  }
  if(failures>=12)break;
 }
 printf("{\"seeds\":%u,\"rooms\":%u,\"routes\":%u,\"arrivals\":%u,\"spawn_checks\":%u,\"content_fronts\":%u,\"hub_return_fronts\":%u,\"failures\":%u}\n",current_seed,count_rooms,count_routes,count_arrivals,count_spawns,count_content,count_returns,failures);return failures?1:0;
}
'''
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True);p.add_argument('--seeds',type=int,default=100000);a=p.parse_args();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True);started=time.time()
 prep=subprocess.run(['python3',str(GAME/'tools/cream_room_review.py'),'--out',str(out/'adapter'),'--seeds','0'],capture_output=True,text=True);(out/'adapter.log').write_text(prep.stdout+prep.stderr);prep.check_returncode()
 source=out/'batch.c';source.write_text(C);binary=out/'batch';adapter=out/'adapter'
 cmd=['gcc','-O2','-w','-fno-builtin','-I',str(adapter),'-I',str(GAME/'src'),str(GAME/'src/cream_world.c'),str(GAME/'src/cream_room.c'),str(adapter/'room_host.c'),str(source),'-o',str(binary)]
 r=subprocess.run(cmd,capture_output=True,text=True);(out/'compile.log').write_text(r.stdout+r.stderr);r.check_returncode();r=subprocess.run([str(binary),str(a.seeds)],capture_output=True,text=True);(out/'run.log').write_text(r.stdout+r.stderr);r.check_returncode();counts=json.loads(r.stdout)
 files=['src/cream_world.c','src/cream_world.h','src/cream_world_fallback.inc','src/cream_room.c','src/cream_room.h','art/cream_terrain.py','tools/cream_room_review.py']
 report=dict(passed=not counts['failures'],method=__doc__,**counts,elapsed_seconds=time.time()-started,source_hashes={n:hashlib.sha256((GAME/n).read_bytes()).hexdigest() for n in files},tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest());(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
if __name__=='__main__':main()

#!/usr/bin/env python3
"""Sweep the production regional planner against actual Forest/Cream rooms.

This compiles the real world generators, room builders, path refinement,
regional planner, token queries and generated native metadata. Explicit host
adapters provide room storage, the unchanged coarse8px collision query, ordinary
mode and capability fixtures. It does not emulate AI/input/rendering and does
not qualify mechanisms stamped after the planner; native tests cover those.
"""
from collections import Counter
import argparse
import ctypes as C
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import time


GAME=Path(__file__).resolve().parent.parent
SOURCES=['world.c','roomgen.c','forest_paths.c','cream_world.c','cream_room.c',
         'regional_content.c','world_tokens.c']
PLAN_FIELDS=['area','cell','field_site','interior_site','event_kind','quest_kind',
             'mechanism_variant','traversal_variant','fusion_color','has_wave',
             'stage','terrace','field_mechanism_variant']

FIXTURE=r'''
#include "room.h"
#include "util.h"
#include "game.h"
#include "player.h"
#include "actor.h"
#include "cream_room.h"
#include "cream_runtime.h"
#include "regional_content.h"
#include "handoff_events.h"
#include "legacy_items.h"
#include "world.h"
#include "myst.h"
#ifdef QA_STAMP_FIELDS
#include "handoff_objects.h"
#include "handoff_mobility.h"
#endif
Room gRoom;GameState gGame;PlayerState gPl;Actor gActors[ACTOR_MAX];Actor*gPlayer=&gActors[0];
static Room qaBefore;
HandoffState gHandoffState;LegacyInventory gLegacyInventory;CreamProgress gCreamProgress;u8 gCreamNode;
s16 gCamX,gCamY;u32 gRoomRevision;u8 gAnimTiles,gRoomTorchesDirty;u32 gDbg[8];
/* Fine masks are outside this declared coarse8px host model. Temporary
   generator probes still execute their real restore loop; these callbacks
   cannot alter the coarse Room that is used by every geometry assertion. */
void room_shapes_clear(void){}
void room_shape_tile(int x,int y,u16 tile){(void)x;(void)y;(void)tile;}
void memcpy32(void*dst,const void*src,u32 n){u8*d=dst;const u8*s=src;while(n--)*d++=*s++;}
void memset32(void*dst,u32 value,u32 n){u32*d=dst;while(n>=4){*d++=value;n-=4;}}
void room_clear(int w,int h,u16 fill){int i;gRoom.w=w;gRoom.h=h;for(i=0;i<1024;i++){gRoom.ground[i]=gRoom.underlay[i]=fill;gRoom.overlay[i]=MT_NONE;}}
void room_set(int x,int y,u16 mt){if(x<0||y<0||x>=gRoom.w||y>=gRoom.h)return;gRoom.ground[y*32+x]=mt;if(mt==MT_NONE||!metatile_prop[mt])gRoom.underlay[y*32+x]=mt;}
void room_set_overlay(int x,int y,u16 mt){if(x>=0&&y>=0&&x<gRoom.w&&y<gRoom.h)gRoom.overlay[y*32+x]=mt;}
u16 room_get(int x,int y){return x<0||y<0||x>=gRoom.w||y>=gRoom.h?MT_BLACK:gRoom.ground[y*32+x];}
u16 room_get_overlay(int x,int y){return x<0||y<0||x>=gRoom.w||y>=gRoom.h?MT_NONE:gRoom.overlay[y*32+x];}
u8 room_type(int x,int y){u16 m=room_get(x,y);return m==MT_NONE?TT_SOLID:metatile_type[m];}
u8 room_type_px(int x,int y){return x<0||y<0?TT_SOLID:room_type(x/16,y/16);}
void room_build_solid(void){int x,y;memset(gRoom.solid,1,sizeof(gRoom.solid));for(y=0;y<gRoom.h;y++)for(x=0;x<gRoom.w;x++){u16 m=room_get(x,y),o=room_get_overlay(x,y);u8 c=m==MT_NONE?15:metatile_coll[m];if(o!=MT_NONE&&metatile_coll[o]&&metatile_type[o]!=TT_FLOOR)c|=metatile_coll[o];u8*s=&gRoom.solid[y*128+x*2];s[0]=(c>>3)&1;s[1]=(c>>2)&1;s[64]=(c>>1)&1;s[65]=c&1;}}
void room_change(int x,int y,u16 mt){room_set(x,y,mt);room_build_solid();}
void room_change_overlay(int x,int y,u16 mt){room_set_overlay(x,y,mt);room_build_solid();}
void room_render(void){room_build_solid();}
bool8 room_solid_px(int x,int y){return x<0||y<0||x>=gRoom.w*16||y>=gRoom.h*16?TRUE:gRoom.solid[(y/8)*64+x/8];}
bool8 room_box_solid(int x0,int y0,int x1,int y1){int x,y;if(x0<0||y0<0||x1>=gRoom.w*16||y1>=gRoom.h*16)return TRUE;for(y=y0/8;y<=y1/8;y++)for(x=x0/8;x<=x1/8;x++)if(gRoom.solid[y*64+x])return TRUE;return FALSE;}
int legacy_surface_at(int x,int y){(void)x;(void)y;return LS_NONE;}
bool8 legacy_item_owned(int item){return item>0&&item<LI_COUNT&&(gLegacyInventory.owned[item>>5]&(1u<<(item&31)));}
static int qaCreamUnlocked=1;
bool8 handoff_region_unlocked(int area){return area!=AREA_CREAM||qaCreamUnlocked;}
u8 handoff_switch_facts(int site){return (unsigned)site<256&&(gHandoffState.completed[site>>3]&(1u<<(site&7)))?255:0;}
int room_px_w(void){return gRoom.w*16;}int room_px_h(void){return gRoom.h*16;}
void qa_seed(u32 seed){memset(&gPl,0,sizeof(gPl));memset(&gHandoffState,0,sizeof(gHandoffState));memset(&gLegacyInventory,0,sizeof(gLegacyInventory));gPl.items=ITEM_SWORD|ITEM_SHIELD;gGame.seed=seed;world_generate(seed);cream_generate(hash32(seed,0x43524541u));regional_content_new_run();}
void qa_capabilities(int all){int i;gPl.items=all?255:ITEM_SWORD|ITEM_SHIELD;gPl.items2=all?255:0;gPl.keys=all?99:0;for(i=0;i<4;i++)gLegacyInventory.owned[i]=all?0xffffffffu:0;}
void qa_build(int area,int cell,int open){int i;gGame.area=area;gGame.cell=cell;for(i=0;i<25;i++)gWorld.cells[i].opened=open?15:0;for(i=0;i<50;i++)gCreamOpenEdges[i]=open?63:0;if(area==AREA_FOREST)roomgen_build(cell);else cream_room_build(cell);room_build_solid();qaBefore=gRoom;regional_content_place(area,cell);}
void qa_plan(int area,int cell,u8*out){RegionalContentPlan p;memset(out,255,32);if(!regional_content_get(area,cell,&p))return;
__PLAN__
}
void qa_spots(u8*out){RegionalContentSpots*p=&gRegionalSpots;
out[0]=p->has_door;out[1]=p->has_npc;out[2]=p->has_cache;out[3]=p->has_mechanism;out[4]=p->terrace;out[5]=p->compact_door;
out[6]=p->door.x;out[7]=p->door.y;out[8]=p->npc.x;out[9]=p->npc.y;out[10]=p->cache.x;out[11]=p->cache.y;
out[12]=p->mechanism.x;out[13]=p->mechanism.y;
out[14]=p->mechanism_rect.x;out[15]=p->mechanism_rect.y;out[16]=p->mechanism_rect.w;out[17]=p->mechanism_rect.h;
out[18]=p->traversal_rect.x;out[19]=p->traversal_rect.y;out[20]=p->traversal_rect.w;out[21]=p->traversal_rect.h;
#ifdef QA_NEW_PLACEMENT
out[22]=p->quest_rect.x;out[23]=p->quest_rect.y;out[24]=p->quest_rect.w;out[25]=p->quest_rect.h;
#endif
}
int qa_front(int x,int y){Spot p={(u8)x,(u8)y};return regional_content_front_reachable(p);}
int qa_entry(int area){return area==AREA_FOREST?gWorld.entry:gCreamWorld.entry_node/2;}
int qa_goal(int area){return area==AREA_FOREST?gWorld.goal:gCreamWorld.goal_node/2;}
int qa_no_tool_reach(int area,int cell){int i;qa_capabilities(0);for(i=0;i<25;i++)gWorld.cells[i].opened=0;for(i=0;i<50;i++)gCreamOpenEdges[i]=0;return regional_content_reachable(area,cell);}
#ifdef QA_BATCH_REACH
void qa_reach_fixture(int items,int keys,int pacci,int trials,int opened,u32*out){int i;gPl.items=items;gPl.items2=0;gPl.keys=keys;memset(&gLegacyInventory,0,sizeof(gLegacyInventory));if(pacci)gLegacyInventory.owned[LI_PACCI_CANE>>5]|=1u<<(LI_PACCI_CANE&31);for(i=0;i<25;i++){gWorld.cells[i].opened=opened?hash32(gGame.seed,i*311)&15:0;gWorld.cells[i].flags&=~CF_ITEM_TAKEN;gWorld.myst_flags[i]&=~MF_WON;}for(i=0;i<3;i++)if(trials&(1<<i)){int k=gWorld.key_cell[i];gWorld.cells[k].flags|=CF_ITEM_TAKEN;gWorld.myst_flags[k]|=MF_WON;}regional_content_reach_masks(out);}
int qa_reach_graph(u8*out){int i,j,k=0;out[k++]=gWorld.entry;out[k++]=gCreamWorld.entry_node;for(i=0;i<25;i++){for(j=0;j<4;j++)out[k++]=gWorld.cells[i].gate[j];out[k++]=gWorld.cells[i].opened;out[k++]=gWorld.cells[i].flags;out[k++]=gWorld.myst_flags[i];}for(i=0;i<3;i++){out[k++]=gWorld.gate_cell[i];out[k++]=gWorld.gate_side[i];out[k++]=gWorld.key_cell[i];}for(i=0;i<50;i++){out[k++]=gCreamWorld.degree[i];for(j=0;j<gCreamWorld.degree[i];j++){const CreamEdge*e=&gCreamWorld.edges[i][j];out[k++]=e->target;out[k++]=e->require;}}for(i=0;i<25;i++){RegionalContentPlan p;regional_content_get(AREA_CREAM,i,&p);out[k++]=p.terrace;}return k;}
#endif
#ifdef QA_QUEST_ROTATION
int qa_locked_quest_area(u32 seed){qaCreamUnlocked=0;qa_seed(seed);qaCreamUnlocked=1;return gRegionalQuestArea;}
#endif
int qa_discovery_bytes(void){return sizeof(gRegionalDiscovery);}
int qa_room_bytes(void){return sizeof(gRoom);}
void qa_reservation_bytes(u8*out){for(int y=0;y<32;y++)for(int x=0;x<32;x++)out[y*32+x]=regional_content_reserved(x,y);}
static int qa_equal(const void*a,const void*b,int n){const u8*x=a,*y=b;while(n--)if(*x++!=*y++)return FALSE;return TRUE;}
int qa_preview_keeps_live_queries(void){u8 before[32*32],marks[MP_COUNT*2];Room room=gRoom;RoomSpots spots=gSpots;int x,y,i=0;for(y=0;y<32;y++)for(x=0;x<32;x++)before[i++]=regional_content_reserved(x,y);roomgen_preview_details((gGame.cell+7)%25,marks,0,0);if(!qa_equal(&room,&gRoom,sizeof(room))||!qa_equal(&spots,&gSpots,sizeof(spots)))return FALSE;i=0;for(y=0;y<32;y++)for(x=0;x<32;x++)if(before[i++]!=regional_content_reserved(x,y))return FALSE;return TRUE;}
int qa_discovery_equal(int area,int cell){RegionalContentDiscovery d;int i=regional_content_index(area,cell);regional_content_marks(area,cell,&d);{const u8*a=(const u8*)&d,*b=(const u8*)&gRegionalDiscovery[i];int j;for(j=0;j<sizeof(d);j++)if(a[j]!=b[j])return FALSE;return TRUE;}}
#ifdef QA_NEW_PLACEMENT
int qa_validate_routes(void){return regional_content_validate_routes();}
static int qa_in_rect(RegionalContentRect r,int x,int y){return r.w&&r.h&&x>=r.x&&x<r.x+r.w&&y>=r.y&&y<r.y+r.h;}
int qa_mutated_outside_rects(void){int x,y,n=0;RegionalContentSpots*p=&gRegionalSpots;for(y=0;y<gRoom.h;y++)for(x=0;x<gRoom.w;x++){int at=y*32+x;if((gRoom.ground[at]!=qaBefore.ground[at]||gRoom.overlay[at]!=qaBefore.overlay[at])&&!qa_in_rect(p->mechanism_rect,x,y)&&!qa_in_rect(p->traversal_rect,x,y)&&!qa_in_rect(p->quest_rect,x,y))n++;}return n;}
int qaSpawnDetails[24*7];static int qaSpawnRequestCount;
void qa_spawns(int area,int*out){int t,i,j,n=0;Spot admitted[24];u8 terrace[24];out[0]=out[1]=out[2]=out[3]=0;qaSpawnRequestCount=0;for(t=0;t<(area==AREA_CREAM?2:1);t++){int count=area==AREA_CREAM?((gCreamRoom.terrace[t].content&CC_CONTENT_ENEMIES)&&gGame.cell!=gCreamWorld.goal_node/2?gCreamRoom.terrace[t].spawn_count:0):gSpots.spawn_count;for(i=0;i<count;i++){Spot p=area==AREA_CREAM?gCreamRoom.terrace[t].spawns[i]:gSpots.spawns[i];int*row=&qaSpawnDetails[out[0]*7];row[0]=t;row[1]=i;row[2]=p.x;row[3]=p.y;qaSpawnRequestCount=++out[0];row[4]=regional_content_spawn_point(t,i,&p);row[5]=p.x;row[6]=p.y;if(row[4]){for(j=0;j<n;j++)if(terrace[j]==t&&admitted[j].x==p.x&&admitted[j].y==p.y)out[3]++;admitted[n]=p;terrace[n++]=t;out[1]++;if(room_box_solid(p.x*16+3,p.y*16+5,p.x*16+12,p.y*16+14)||room_type(p.x,p.y)!=TT_FLOOR)out[2]++;}}}}
#ifdef QA_STAMP_FIELDS
static int qa_walkable(int x,int y,int objects){int px=x*16+8,py=y*16+14,t=room_type(x,y);if(x<1||y<1||x>=gRoom.w-1||y>=gRoom.h-1)return FALSE;if(t!=TT_FLOOR&&t!=TT_SLOW&&t!=TT_SWITCH&&t!=TT_DOOR_OPEN&&t!=TT_CHEST_OPEN)return FALSE;if(room_box_solid(px-5,py-8,px+4,py-1))return FALSE;if(objects&&(handoff_objects_box_solid(px-5,py-8,px+4,py-1)||handoff_mobility_box_solid(px-5,py-8,px+4,py-1)))return FALSE;return TRUE;}
static void qa_walk_flood(u8*seen,int objects){static const int dx[]={0,1,0,-1},dy[]={-1,0,1,0};int queue[1024],head=0,tail=0,x=gRegionalSpots.door.x,y=gRegionalSpots.door.y+1;memset(seen,0,1024);if(!qa_walkable(x,y,objects))return;seen[y*32+x]=1;queue[tail++]=y*32+x;while(head<tail){int at=queue[head++];for(int d=0;d<4;d++){int nx=at%32+dx[d],ny=at/32+dy[d],n=ny*32+nx;if(nx<1||ny<1||nx>=gRoom.w-1||ny>=gRoom.h-1||seen[n]||!qa_walkable(nx,ny,objects))continue;seen[n]=1;queue[tail++]=n;}}}
void qa_stamp_fields(int*out){RegionalContentPlan p;RegionalContentRect b;u8 before[1024],after[1024];int x,y;memset(out,0,8*sizeof(int));handoff_objects_reset();handoff_mobility_reset();if(!regional_content_get(gGame.area,gGame.cell,&p)||!gRegionalSpots.has_mechanism)return;b=gRegionalSpots.traversal_rect.w?gRegionalSpots.traversal_rect:gRegionalSpots.mechanism_rect;if(!b.w||!b.h)return;qa_walk_flood(before,0);if(p.fusion_color==2){out[0]=1;out[6]=2;out[1]=handoff_objects_build_fusion(gGame.seed,b.x,b.y,b.w,b.h);}else if(p.field_mechanism_variant!=RC_NONE&&!gRegionalSpots.traversal_rect.w){out[0]=2;out[6]=p.field_mechanism_variant;out[1]=handoff_objects_build_field(gGame.seed,p.field_mechanism_variant,b.x,b.y,b.w,b.h);}else if(p.traversal_variant!=RC_NONE&&gRegionalSpots.traversal_rect.w){out[0]=3;out[6]=p.traversal_variant;out[1]=handoff_mobility_build_field(gGame.seed,p.traversal_variant,p.field_site,b.x,b.y,b.w,b.h);}else return;room_build_solid();out[2]=regional_content_validate_routes();qa_walk_flood(after,1);for(y=1;y<gRoom.h-1;y++)for(x=1;x<gRoom.w-1;x++){int at=y*32+x;if(before[at]&&!after[at]&&!qa_in_rect(gRegionalSpots.mechanism_rect,x,y)&&!qa_in_rect(gRegionalSpots.traversal_rect,x,y)&&!qa_in_rect(gRegionalSpots.quest_rect,x,y))out[3]++;}for(y=b.y;y<b.y+b.h;y++)for(x=b.x;x<b.x+b.w;x++)if((x==b.x||y==b.y||x==b.x+b.w-1||y==b.y+b.h-1)&&!qa_walkable(x,y,1))out[4]++;out[5]=qa_mutated_outside_rects();for(int i=0;i<qaSpawnRequestCount;i++){int*row=&qaSpawnDetails[i*7];if(row[4]&&!qa_walkable(row[5],row[6],1))out[7]++;}}
#endif

#endif
'''


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--seeds',type=int,default=128)
    p.add_argument('--seed-values',nargs='+',help='Explicit integer seeds instead of range(--seeds).')
    p.add_argument('--bundle',type=Path,help='Use exact pinned runtime sources/headers from this frozen bundle.')
    p.add_argument('--stamp-fields',action='store_true',help='Link and execute actual object/fusion/mobility field builders after placement.')
    a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    started=time.time()
    src=GAME/'src';commit=None
    for name in ['assets.h','assets.c']:shutil.copy2(GAME/'build/gen'/name,out/name)
    if a.bundle:
        commit=(a.bundle/'source-commit.txt').read_text().strip()
        if not re.fullmatch('[0-9a-f]{40}',commit):raise ValueError('bundle needs full commit')
        if (a.bundle/'assets.h').read_bytes()!=(out/'assets.h').read_bytes():
            raise ValueError('current generated assets/header must match the pinned bundle before host qualification')
        src=out/'source';src.mkdir(exist_ok=True)
        data=subprocess.check_output(['git','archive',commit,'bartgame/src'],cwd=GAME.parent)
        with tarfile.open(fileobj=io.BytesIO(data)) as archive:
            for m in archive:
                if not m.isfile():continue
                rel=Path(m.name).relative_to('bartgame/src');target=src/rel
                target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(archive.extractfile(m).read())
    source_paths=sorted(set([src/n for n in SOURCES]+[src/'forest_trees.c',src/'util.c']+list(src.rglob('*.h'))))
    if a.stamp_fields:source_paths += [src/'handoff_objects.c',src/'handoff_mobility.c']
    source_hashes={'src/'+str(f.relative_to(src)):sha(f) for f in source_paths}
    enhanced='quest_rect' in (src/'regional_content.h').read_text() and bool(re.search(r'bool8\s+regional_content_spawn_point\s*\([^)]*\)\s*\{',(src/'regional_content.c').read_text()))
    fixture=FIXTURE.replace('__PLAN__','\n'.join(f'out[{i}]=p.{name};' for i,name in enumerate(PLAN_FIELDS)))
    (out/'fixture.c').write_text(fixture)
    util=(src/'util.c').read_text()
    # Only actual production PRNG/hash functions are used; memory uses libc.
    (out/'prng.c').write_text('#include "util.h"\n'+util[util.index('static u32 sRand'):])
    trees=(src/'forest_trees.c').read_text()
    classification=trees[trees.index('static bool8 between('):trees.index('void forest_trees_reset(')]
    (out/'trees.c').write_text('#include "forest_trees.h"\n#include "assets.h"\n#include "room.h"\n'+classification+'\nvoid forest_trees_plan(void){}\n')
    libfile=out/'regional-placement.so'
    cmd=['gcc','-shared','-fPIC','-O2','-w','-fno-builtin','-DBART_FOREST_VARIANT=32','-I',str(out),'-I',str(src)]
    if enhanced:cmd+=['-DQA_NEW_PLACEMENT=1']
    rotates='gRegionalQuestArea' in (src/'regional_content.h').read_text()
    if rotates:cmd+=['-DQA_QUEST_ROTATION=1']
    if 'void regional_content_reach_masks(' in (src/'regional_content.c').read_text():cmd+=['-DQA_BATCH_REACH=1']
    if a.stamp_fields:
        cmd+=['-DQA_STAMP_FIELDS=1','-Wl,--gc-sections','-Wl,--no-undefined']
        for name in ('handoff_objects','handoff_mobility'):
            # Hide only these module exports so linker GC keeps the actual
            # builders/collision paths while discarding unrelated controllers,
            # audio and rendering; no stub replaces a builder or its geometry.
            compile_command=['gcc','-c','-O2','-w','-fPIC','-fno-builtin','-fvisibility=hidden','-ffunction-sections','-fdata-sections','-DBART_FOREST_VARIANT=32','-I',str(out),'-I',str(src),str(src/(name+'.c')),'-o',str(out/(name+'.o'))]
            result=subprocess.run(compile_command,capture_output=True,text=True);(out/(name+'-compile.log')).write_text(result.stdout+result.stderr);result.check_returncode();cmd+=[str(out/(name+'.o'))]
    cmd += [str(src/n) for n in SOURCES]
    cmd += [str(out/n) for n in ['assets.c','fixture.c','prng.c','trees.c']]+['-o',str(libfile)]
    r=subprocess.run(cmd,capture_output=True,text=True);(out/'compile.log').write_text(r.stdout+r.stderr);r.check_returncode()
    lib=C.CDLL(str(libfile));buf=(C.c_uint8*32)();sp=(C.c_uint8*32)()
    lib.qa_seed.argtypes=[C.c_uint32]
    lib.qa_plan.argtypes=[C.c_int,C.c_int,C.POINTER(C.c_uint8)]
    count=Counter();failed=Counter();coverage=Counter();failures=[];samples=[];seed_cases=[]
    def check(name,ok,detail=None):
        count[name]+=1
        if not ok:
            failed[name]+=1
            if len(failures)<100:failures.append(dict(check=name,detail=detail))
    seeds=[int(v,0) for v in a.seed_values] if a.seed_values else list(range(a.seeds))
    for number,seed in enumerate(seeds):
        lib.qa_seed(seed);plans=[]
        for area in (1,3):
            for cell in range(25):
                lib.qa_plan(area,cell,buf);meta=dict(zip(PLAN_FIELDS,list(buf)))
                plans.append(meta);key=dict(seed=seed,area=area,cell=cell,event=meta['event_kind'])
                check('field_namespace',meta['field_site']==32+(25 if area==3 else 0)+cell,key)
                is_core=cell in (lib.qa_entry(area),lib.qa_goal(area))
                check('entry_goal_reserved',(meta['interior_site']==255)==is_core,key)
                if not is_core:
                    coverage['event:'+str(meta['event_kind'])]+=1
                    if meta['quest_kind']:
                        coverage['quest:'+str(meta['quest_kind'])]+=1
                        coverage['quest_area:'+str(meta['quest_kind'])+':'+str(area)]+=1
                        if rotates:
                            check('quest_giver_reachable_without_tools',lib.qa_no_tool_reach(area,cell),key|dict(plan=meta))
                    if meta['mechanism_variant']!=255:coverage['mechanism:'+str(meta['mechanism_variant'])]+=1
                    if meta['traversal_variant']!=255:coverage['traversal:'+str(meta['traversal_variant'])]+=1
                    if meta['fusion_color']!=255:coverage['fusion:'+str(meta['fusion_color'])]+=1
                initial_spots=None
                for opened in (0,1):
                    lib.qa_build(area,cell,opened);lib.qa_spots(sp);values=list(sp)
                    count['actual_rooms']+=1
                    detail=key|dict(open=opened,plan=meta,spots=values[:26])
                    if enhanced:
                        result=(C.c_int*4)();lib.qa_spawns(area,result)
                        count['original_spawns_requested']+=result[0];count['original_spawns_admitted']+=result[1]
                        check('original_enemy_population_retained',result[0]==result[1],key|dict(open=opened,spawn=list(result)))
                        check('admitted_spawns_have_real_dry_feet',result[2]==0,key|dict(open=opened,spawn=list(result)))
                        check('admitted_spawns_are_unique',result[3]==0,key|dict(open=opened,spawn=list(result)))
                        if result[0]!=result[1] or result[3]:
                            trace=list((C.c_int*(24*7)).in_dll(lib,'qaSpawnDetails'));detail['spawn_trace']=[trace[i*7:i*7+7] for i in range(result[0])]
                    if is_core:
                        check('core_no_new_anchors',not any(values[:4]),detail)
                        continue
                    if initial_spots is None:initial_spots=values
                    else:
                        # A gate opening may enlarge the dry component, but
                        # must not move a feature the player already found.
                        unchanged=all(not initial_spots[i] or (values[i] and values[6+2*i:8+2*i]==initial_spots[6+2*i:8+2*i]) for i in range(4))
                        check('discovered_anchors_stable_after_gate_open',unchanged,detail|dict(before=initial_spots[:26]))
                    check('interior_has_actual_door',bool(values[0]),detail)
                    if meta['quest_kind'] or meta['has_wave'] or meta['fusion_color']!=255:
                        check('required_npc_anchor',bool(values[1]),detail)
                    if values[0]:check('door_front_current_component',lib.qa_front(values[6],values[7]),detail)
                    if values[1]:check('npc_front_current_component',lib.qa_front(values[8],values[9]),detail)
                    if values[2]:check('cache_front_current_component',lib.qa_front(values[10],values[11]),detail)
                    if values[3]:
                        check('mechanism_rectangle_exists',(values[16]>0 and values[17]>0) or (values[20]>0 and values[21]>0),detail)
                        coverage['placed_field_mechanism:'+str(meta['field_mechanism_variant'])]+=1
                    if meta['traversal_variant']!=255:
                        coverage['traversal_rect:'+str(meta['traversal_variant'])+':'+str(bool(values[20] and values[21]))]+=1
                    if seed<2:samples.append(detail)
                    check('discovery_matches_actual',lib.qa_discovery_equal(area,cell),detail)
                    if enhanced:
                        if meta['fusion_color']==2:
                            check('red_fusion_has_crossing_rectangle',values[16]>=5 and values[17]>=5,detail)
                        if meta['quest_kind']==7:
                            check('block_quest_has_board_rectangle',values[24]>=7 and values[25]>=7,detail)
                        check('old_routes_preserved_by_clearing',lib.qa_validate_routes(),detail)
                        check('clearing_confined_to_admitted_rectangles',lib.qa_mutated_outside_rects()==0,detail)
                    if area==1:
                        check('map_preview_preserves_live_room_and_reservations',lib.qa_preview_keeps_live_queries(),detail)
                    if a.stamp_fields:
                        stamp=(C.c_int*8)();lib.qa_stamp_fields(stamp)
                        if stamp[0]:
                            stamped=detail|dict(stamp=list(stamp));coverage['actual_builder:'+str(stamp[0])+':'+str(stamp[6])+':'+str(bool(stamp[1]))]+=1
                            check('actual_builder_accepts_planned_field_footprint',stamp[1],stamped)
                            check('poststamp_production_routes_preserved',stamp[2],stamped)
                            check('poststamp_independent_routes_and_fronts_preserved',stamp[3]==0,stamped)
                            check('poststamp_field_perimeter_remains_walkable',stamp[4]==0,stamped)
                            check('poststamp_changes_confined_to_admitted_rectangles',stamp[5]==0,stamped)
                            check('poststamp_original_spawn_feet_preserved',stamp[7]==0,stamped)
                if not is_core:
                    lib.qa_build(area,cell,0);lib.qa_spots(sp)
                    values=list(sp)
                    check('discovered_anchors_stable_on_revisit',all(not initial_spots[i] or (values[i] and values[6+2*i:8+2*i]==initial_spots[6+2*i:8+2*i]) for i in range(4)),key|dict(before=initial_spots[:26],revisit=values[:26]))
        sites=[m['interior_site'] for m in plans if m['interior_site']!=255]
        check('interior_namespace_unique',len(sites)==46 and set(sites)==set(range(82,128)),dict(seed=seed,sites=sites))
        check('single_run_side_quest',sum(bool(m['quest_kind']) for m in plans)==1,dict(seed=seed))
        check('both_regions_have_wave',all(sum(bool(m['has_wave']) for m in plans if m['area']==area)==1 for area in (1,3)),dict(seed=seed))
        check('fusion_three_colors',sorted(m['fusion_color'] for m in plans if m['fusion_color']!=255)==[0,1,2],dict(seed=seed))
        seed_cases.append(dict(seed=seed,plans=plans))
        if enhanced:
            blocks=next((m for m in plans if m['quest_kind']==7),None)
            if blocks:
                # Cold first-placement must equal a build whose plan already
                # exists. A temporary geometry probe must restore live paths
                # before regional placement snapshots their reservations.
                states=[]
                for warm in (True,False):
                    lib.qa_seed(seed)
                    if warm:lib.qa_plan(blocks['area'],blocks['cell'],buf)
                    lib.qa_build(blocks['area'],blocks['cell'],0);lib.qa_spots(sp)
                    reserved=(C.c_uint8*1024)();lib.qa_reservation_bytes(reserved)
                    room=bytes((C.c_uint8*lib.qa_room_bytes()).in_dll(lib,'gRoom'))
                    states.append(dict(spots=list(sp)[:26],room_sha256=hashlib.sha256(room).hexdigest(),reserved_sha256=hashlib.sha256(bytes(reserved)).hexdigest()))
                check('first_blocks_plan_probe_preserves_live_room_and_reservations',states[0]==states[1],dict(seed=seed,plan=blocks,warm=states[0],cold=states[1]))
        if rotates:check('locked_cream_keeps_quest_origin_in_forest',lib.qa_locked_quest_area(seed)==1,dict(seed=seed))
        if (number+1)%16==0:print(f'{number+1}/{len(seeds)} seeds; rooms={count["actual_rooms"]}; failures={len(failures)}',flush=True)
    if len(seeds)>=16:
        check('all_seven_quests_covered',all(coverage['quest:'+str(i)] for i in range(1,8)),dict(coverage))
        check('all_twelve_mechanism_patterns',all(coverage['mechanism:'+str(i)] for i in range(12)),dict(coverage))
        check('all_three_traversal_patterns',all(coverage['traversal:'+str(i)] for i in range(3)),dict(coverage))
        if enhanced:check('all_three_field_traversal_patterns_placed',all(coverage['traversal_rect:'+str(i)+':True'] for i in range(3)),dict(coverage))
        if rotates and len(seeds)>=256:check('six_quests_offered_from_both_regions',all(coverage['quest_area:'+str(kind)+':'+str(area)] for kind in range(1,7) for area in (1,3)),dict(coverage))
    unchanged=source_hashes=={'src/'+str(f.relative_to(src)):sha(f) for f in source_paths}
    check('source_stable_during_sweep',unchanged)
    report=dict(method=__doc__,counts=dict(count),failure_counts=dict(failed),coverage=dict(coverage),failures=failures,
                passed=not failures,seeds=len(seeds),source_commit=commit,source_sha256=source_hashes,enhanced_placement_observation=enhanced,
                tool_sha256=sha(__file__),compile_command=cmd,elapsed_seconds=time.time()-started,
                generated_assets_sha256={name:sha(out/name) for name in ('assets.c','assets.h')},
                adapters=['Ordinary entitlement mode; dry base surfaces before new mechanism stamping.',
                          'Actual native metatile metadata and original coarse8px collision/Room storage.',
                          'Actual production PRNG/hash; no replacement graph or room geometry.',
                          'Actual forest-tree legacy classification; tree-render planning is a no-op because it never mutates Room collision.'])
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'plans.json').write_text(json.dumps(seed_cases,indent=2)+'\n')
    (out/'samples.json').write_text(json.dumps(samples,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['passed','seeds','counts','elapsed_seconds']}))
    raise SystemExit(bool(failures))


if __name__=='__main__':main()

#!/usr/bin/env python3
"""Qualify actual unified requirement and hidden-placement C on host fixtures.
Queries consume real serialized field types, while room/switch/owned callbacks
are explicit deterministic adapters. This is not native graphics/input proof.
"""
import argparse,hashlib,json,subprocess
from pathlib import Path
GAME=Path(__file__).resolve().parents[1]
HARNESS=r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define GBA_H
#define EWRAM_BSS
#define IWRAM_CODE
#define TRUE 1
#define FALSE 0
#define ALIGN4
#define ABS(x) ((x)<0?-(x):(x))
#define CLAMP(v,l,h) ((v)<(l)?(l):(v)>(h)?(h):(v))
typedef uint8_t u8;typedef uint16_t u16;typedef uint32_t u32;
typedef int8_t s8;typedef int16_t s16;typedef int32_t s32;typedef u8 bool8;
#include "world_tokens.c"
PlayerState gPl;
World gWorld;
HandoffState gHandoffState;
CreamProgress gCreamProgress;
Room gRoom;
LegacyInventory gLegacyInventory;
static u8 types[1024],surfaces[1024],switches[256];
bool8 legacy_item_owned(int id){return id>0&&id<LI_COUNT&&((gLegacyInventory.owned[id>>5]>>(id&31))&1);}
u8 handoff_switch_facts(int site){if(site<0||site>=256)return 0;return gHandoffState.completed[site>>3]&(1u<<(site&7))?255:switches[site];}
u8 room_type(int tx,int ty){return tx<0||ty<0||tx>=gRoom.w||ty>=gRoom.h?TT_SOLID:types[ty*32+tx];}
int legacy_surface_at(int px,int py){int tx=px>>4,ty=py>>4;return tx<0||ty<0||tx>=gRoom.w||ty>=gRoom.h?LS_NONE:surfaces[ty*32+tx];}
bool8 room_box_solid(int x0,int y0,int x1,int y1){int x,y;for(y=y0>>4;y<=y1>>4;y++)for(x=x0>>4;x<=x1>>4;x++){int t=room_type(x,y);if(t==TT_SOLID||t==TT_THORN||t==TT_CRACK||t==TT_LIFT1)return TRUE;}return FALSE;}
static int checks;
#define CHECK(x) do{checks++;if(!(x)){fprintf(stderr,"line%d:%s\n",__LINE__,#x);exit(1);}}while(0)
static void fresh(void){int x,y;memset(&gPl,0,sizeof(gPl));memset(&gWorld,0,sizeof(gWorld));memset(&gHandoffState,0,sizeof(gHandoffState));memset(&gCreamProgress,0,sizeof(gCreamProgress));memset(&gLegacyInventory,0,sizeof(gLegacyInventory));memset(types,0,sizeof(types));memset(surfaces,0,sizeof(surfaces));memset(switches,0,sizeof(switches));gRoom.w=32;gRoom.h=24;for(y=0;y<24;y++)for(x=0;x<32;x++)if(!x||!y||x==31||y==23)types[y*32+x]=TT_SOLID;}
int main(void){
 int i,j;WorldTokenNeed n;Spot out,start={2,2},origin={10,5},candidate;
 fresh();n=world_tokens_empty();CHECK(world_tokens_meet(&n));CHECK(!world_tokens_meet(NULL));
 /* Every inherited Cream capability combination, independently of rewards. */
 for(i=0;i<8;i++)for(j=0;j<2;j++){
  gPl.items=(i&1?ITEM_BOMBS:0)|(i&2?ITEM_LAMP:0)|(i&4?ITEM_CLOAK:0);
  gLegacyInventory.owned[0]=j?1u<<LI_PACCI_CANE:0;
  CHECK(world_tokens_cream_mask()==((i&3)|((i&4)&&j?4:0)));
  for(int req=0;req<8;req++){int have=(i&3)|((i&4)&&j?4:0);CHECK(world_tokens_cream_open(req)==((have&req)==req));}
 }
 CHECK(!world_tokens_cream_open(8));fresh();n=world_tokens_empty();n.old_items=ITEM_SWORD|((u16)ITEM2_BOW<<8);
 CHECK(!world_tokens_meet(&n));gPl.items=ITEM_SWORD;CHECK(!world_tokens_meet(&n));gPl.items2=ITEM2_BOW;CHECK(world_tokens_meet(&n));
 n.legacy_item=LI_COUNT-1;CHECK(!world_tokens_meet(&n));gLegacyInventory.owned[(LI_COUNT-1)>>5]|=1u<<((LI_COUNT-1)&31);CHECK(world_tokens_meet(&n));
 n.keys=3;gPl.keys=2;CHECK(!world_tokens_meet(&n));gPl.keys=3;CHECK(world_tokens_meet(&n)&&gPl.keys==3);
 n.fusions=5;gHandoffState.fusion_flags=4;CHECK(!world_tokens_meet(&n));gHandoffState.fusion_flags=5;CHECK(world_tokens_meet(&n));
 n.gold=9;gHandoffState.gold_fused=1;CHECK(!world_tokens_meet(&n));gHandoffState.gold_fused=9;CHECK(world_tokens_meet(&n));
 n.switch_site=HS_SWITCHES;n.switch_mask=5;switches[HS_SWITCHES]=4;CHECK(!world_tokens_meet(&n));switches[HS_SWITCHES]=5;CHECK(world_tokens_meet(&n));
 n.puzzle_site=HS_BLOCK_MAZE;CHECK(!world_tokens_meet(&n));gHandoffState.completed[HS_BLOCK_MAZE>>3]|=1u<<(HS_BLOCK_MAZE&7);CHECK(world_tokens_meet(&n));
 n.boss_flags=WT_BOSS_HEART|WT_BOSS_CREAM;CHECK(!world_tokens_meet(&n));gWorld.goal=CELLS;CHECK(!world_tokens_meet(&n));gWorld.goal=0;gWorld.cells[0].flags=CF_CLEARED;CHECK(!world_tokens_meet(&n));gCreamProgress.boss_dead=1;CHECK(world_tokens_meet(&n));n.boss_flags=128;CHECK(!world_tokens_meet(&n));
 n=world_tokens_empty();n.switch_mask=1;CHECK(!world_tokens_meet(&n));n.legacy_item=255;CHECK(!world_tokens_meet(&n));
 /* Actual semantic features, approached from a dry connected component. */
 fresh();types[5*32+10]=TT_LIFT1;CHECK(world_hidden_find(WH_CUT,origin,start,0,&out)&&out.x==10&&out.y==5);
 CHECK(world_hidden_reachable(WH_CUT,origin,start));CHECK(!world_hidden_reachable(WH_DIG,origin,start));
 for(i=1;i<23;i++)types[i*32+8]=TT_SOLID;
 CHECK(!world_hidden_find(WH_CUT,origin,start,8,&out));surfaces[5*32+8]=LS_DIG_WALL;candidate.x=8;candidate.y=5;
 CHECK(world_hidden_reachable(WH_DIG,candidate,start));CHECK(world_hidden_find(WH_DIG,origin,start,2,&out)&&out.x==8&&out.y==5);
 types[5*32+8]=TT_CRACK;CHECK(world_hidden_find(WH_BOMB,origin,start,2,&out)&&out.x==8&&out.y==5);
 /* Safe fallback, hazard-ring exclusion, no OOB on invalid inputs. */
 fresh();types[5*32+10]=TT_THORN;types[4*32+10]=types[6*32+10]=types[5*32+9]=types[5*32+11]=TT_WATER;
 out.x=out.y=255;CHECK(!world_hidden_find(WH_CUT,origin,start,8,&out)&&out.x==255&&out.y==255);
 fresh();types[5*32+10]=TT_THORN;surfaces[4*32+10]=surfaces[6*32+10]=surfaces[5*32+9]=surfaces[5*32+11]=LS_SWAMP;
 CHECK(!world_hidden_find(WH_CUT,origin,start,8,&out));
 candidate.x=candidate.y=255;CHECK(!world_hidden_reachable(WH_CUT,origin,candidate));CHECK(!world_hidden_reachable(WH_CUT,candidate,start));
 CHECK(!world_hidden_find(-1,origin,start,8,&out));CHECK(!world_hidden_find(3,origin,start,8,&out));CHECK(!world_hidden_find(WH_CUT,origin,start,8,NULL));
 fresh();types[20*32+20]=TT_LIFT1;origin.x=origin.y=2;CHECK(!world_hidden_find(WH_CUT,origin,start,255,&out));
 /* Deterministic ring choice never jumps across a separating wall. */
 for(i=0;i<1000;i++){
  fresh();origin.x=5+(i%15);origin.y=4+(i%10);types[origin.y*32+origin.x]=TT_LIFT1;
  CHECK(world_hidden_find(WH_CUT,origin,start,i%9,&out)&&out.x==origin.x&&out.y==origin.y);
  CHECK(world_hidden_reachable(WH_CUT,out,start));
 }
 printf("{\"checks\":%d,\"need_bytes\":%zu,\"persistent_scratch_bytes\":0}\n",checks,sizeof(WorldTokenNeed));return 0;
}
'''
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True);p.add_argument('--cc',default='cc');a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True);source=out/'world-tokens-host.c';source.write_text(HARNESS);binary=out/'world-tokens-host'
 cmd=[a.cc,'-std=gnu11','-O2','-w','-I',str(GAME/'src'),'-I',str(GAME/'build/gen'),str(source),'-o',str(binary)]
 r=subprocess.run(cmd,capture_output=True,text=True);(out/'compile.log').write_text(r.stdout+r.stderr);r.check_returncode();r=subprocess.run([str(binary)],capture_output=True,text=True);(out/'run.log').write_text(r.stdout+r.stderr);r.check_returncode();counts=json.loads(r.stdout)
 files=['src/world_tokens.c','src/world_tokens.h','src/handoff_events.h','src/legacy_items.h','src/cream_runtime.h','src/world.h','src/player.h']
 report=dict(passed=True,method=__doc__,**counts,source_hashes={n:hashlib.sha256((GAME/n).read_bytes()).hexdigest() for n in files},tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest());(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(counts)
if __name__=='__main__':main()

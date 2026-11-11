#!/usr/bin/env python3
"""Run actual traversal-annex C against explicit host room/input fixtures.

Real fixed-point cart/parachute motion, plane collision/priority, native tile
placement and once-only fusion rewards are tested. Rendering uploads/sound
are inert spies: this is source/runtime logic evidence, not emulator imagery.
"""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
GAME=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()
def clean(s):return re.sub(r'^\s*#include[^\n]*$','',s,flags=re.M)
def fixture():
 src=GAME/'src';c=(src/'handoff_mobility.c').read_text()
 out='''#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
typedef uint8_t u8;typedef uint16_t u16;typedef uint32_t u32;
typedef int8_t s8;typedef int16_t s16;typedef int32_t s32;typedef u8 bool8;
#define TRUE 1
#define FALSE 0
#define EWRAM_BSS
#define ABS(a) ((a)<0?-(a):(a))
#define MIN(a,b) ((a)<(b)?(a):(b))
#define MAX(a,b) ((a)>(b)?(a):(b))
#define CLAMP(v,lo,hi) ((v)<(lo)?(lo):((v)>(hi)?(hi):(v)))
#define Q16(v) ((s32)((v)*65536))
#define Q8(v) ((s32)((v)*256))
#define PX(v) ((v)>>16)
#define FACE_N 0
#define FACE_E 1
#define FACE_S 2
#define FACE_W 3
#define OBJ_TILE(v) ((void*)(uintptr_t)(v))
#define KEY_A 1
#define KEY_B 2
#define KEY_L 512
#define KEY_R 256
#define KEY_UP 64
#define KEY_DOWN 128
#define KEY_LEFT 32
#define KEY_RIGHT 16
'''
 actor=(src/'actor.h').read_text();out+=re.search(r'typedef struct Actor \{.*?\} Actor;',actor,re.S)[0]+'\n'
 player=(src/'player.h').read_text();out+='\n'.join(re.findall(r'enum\s*\{[^}]+\}\s*;',player))+'\n';out+=re.search(r'typedef struct\s*\{.*?\}\s*PlayerState;',player,re.S)[0]+'\n'
 for name in ('legacy_items.h','handoff_events.h','handoff_mobility.h'):out+=clean((src/name).read_text())+'\n'
 out+='typedef struct {u8 x,y;} Spot;\n'+clean((src/'world_tokens.h').read_text())+'\n'
 out+='enum {AREA_SEWER,AREA_FOREST,AREA_MYST,AREA_CREAM,AREA_HANDOFF};\n'
 for i,name in enumerate(sorted(set(re.findall(r'\bMT_\w+',c)))):out+=f'#define {name} {i+1}\n'
 for i,name in enumerate(sorted(set(re.findall(r'\bSFX_\w+',c)))):out+=f'#define {name} {i+1}\n'
 out+='''#define SHEET_HANDOFF_MOBILITY 0
static u16 ground[32*24],overlay[32*24],keys;
static u32 gFrame;
static s16 gCamX,gCamY;
static Actor hero,*gPlayer=&hero;
static PlayerState gPl;
HandoffState gHandoffState;
static struct {u8 area;} gGame;
static u16 gKeysDown,gKeysHeld;
static int kind=HS_TRAVERSAL,grants,notifies,solidity_calls;
static u16 pixels[4096];
typedef struct {const u16* tiles;u8 frame_tiles,pal;} SpriteSheet;
static const SpriteSheet sheets[]={{pixels,16,3}};
WorldTokenNeed world_tokens_empty(void) {WorldTokenNeed n={0};n.switch_site=n.puzzle_site=255;return n;}
bool8 world_tokens_meet(const WorldTokenNeed* n) {return (gHandoffState.fusion_flags&n->fusions)==n->fusions;}
int handoff_current_kind(void) {return kind;}
void room_set(int x,int y,u16 mt) {if(x>=0&&x<32&&y>=0&&y<24)ground[y*32+x]=mt;}
void room_set_overlay(int x,int y,u16 mt) {if(x>=0&&x<32&&y>=0&&y<24)overlay[y*32+x]=mt;}
void room_change(int x,int y,u16 mt) {room_set(x,y,mt);}
void room_build_solid(void) {solidity_calls++;}
void sfx_play(int id) {(void)id;}
void textbox_open(const char* msg) {(void)msg;}
void legacy_item_grant(int item,int count) {if(item==LI_RUPEE100&&count==1)grants++;}
void handoff_notify(int k,int a,int b,int item) {(void)k;(void)a;(void)b;(void)item;notifies++;}
u16 sprite_load_frame(int sh,int frame) {(void)sh;(void)frame;return 32;}
void vram_queue(const void* src,volatile void* dst,u32 n) {(void)src;(void)dst;(void)n;}
void draw_sprite(int x,int y,int sh,u16 tile,int fr,int hf,int pr,int pal) {(void)x;(void)y;(void)sh;(void)tile;(void)fr;(void)hf;(void)pr;(void)pal;}
'''
 return out+clean(c)
MAIN=r'''
static int checks;
#define CHECK(x) do {checks++;if(!(x)){fprintf(stderr,"line%d: %s\n",__LINE__,#x);exit(1);}}while(0)
static void fresh(void) {
 memset(&hero,0,sizeof(hero));memset(&gPl,0,sizeof(gPl));memset(&gHandoffState,0,sizeof(gHandoffState));
 memset(ground,0,sizeof(ground));memset(overlay,0,sizeof(overlay));kind=HS_TRAVERSAL;gGame.area=AREA_HANDOFF;
 gKeysDown=gKeysHeld=0;grants=notifies=0;handoff_mobility_build(42);
}
int main(void) {
 int i,j,oldx,oldy;
 fresh();CHECK(gMobilityMode==HMOB_WALK&&gMobilityLayer==0&&solidity_calls==1);
 CHECK(ground[7*32+3]==MT_LH_MOB_CLIFF&&ground[6*32+5]==MT_LH_MOB_LAUNCH);
 CHECK(ground[14*32+15]==MT_CAVE_FLOOR0&&overlay[14*32+15]==MT_LH_MOB_DECK);
 CHECK(ground[9*32+25]==MT_LH_MOB_PIT);gHandoffState.fusion_flags=4;handoff_mobility_build(42);
 CHECK(ground[9*32+25]==MT_LH_MOB_RAMP);
 /* The same central crossing is ordinary dry lower floor, or a raised deck
    with its own lateral boundaries, hazard suppression and render priority. */
 hero.x=Q16(15*16+8);hero.y=Q16(14*16+14);handoff_mobility_update();CHECK(gMobilityLayer==0);
 CHECK(!handoff_mobility_handles_floor(248,230)&&handoff_mobility_priority(2)==2);
 hero.y=Q16(7*16+14);handoff_mobility_update();CHECK(gMobilityLayer==1);
 CHECK(handoff_mobility_handles_floor(248,230)&&handoff_mobility_priority(2)==1);
 CHECK(handoff_mobility_box_solid(14*16-1,220,14*16+4,228));
 CHECK(!handoff_mobility_box_solid(15*16,220,15*16+8,228));
 hero.y=Q16(21*16+14);handoff_mobility_update();CHECK(gMobilityLayer==0);
 hero.y=Q16(20*16+14);handoff_mobility_update();CHECK(gMobilityLayer==1);
 hero.y=Q16(6*16+14);handoff_mobility_update();CHECK(gMobilityLayer==0);
 CHECK(handoff_mobility_box_solid(55,125,61,132));
 /* Cart motion follows actual rectangular rails, never diagonal shortcuts;
    the request to leave waits for a valid station and picks dry floor. */
 fresh();sPadCooldown=0;hero.x=Q16(gMobilityCartX);hero.y=Q16(gMobilityCartY+9);
 CHECK(handoff_mobility_interact()&&gMobilityMode==HMOB_CART&&gPl.input_lock);
 for(i=0;i<500&&gMobilityMode==HMOB_CART;i++) {
  oldx=PX(sCartX);oldy=PX(sCartY);gKeysDown=i==10?KEY_A:0;
  CHECK(handoff_mobility_pre_player());
  CHECK(PX(sCartX)==oldx||PX(sCartY)==oldy);
  CHECK(PX(sCartX)>=tile_x(4)&&PX(sCartX)<=tile_x(11)&&PX(sCartY)>=tile_y(17)&&PX(sCartY)<=tile_y(20));
 }
 CHECK(i<500&&gMobilityMode==HMOB_WALK&&!gPl.input_lock&&hero.z==0&&hero.state==PS_NORMAL);
 CHECK(ground[(PX(hero.y)-4)/16*32+PX(hero.x)/16]!=MT_LH_MOB_WATER);
 CHECK(gPl.safe_x==PX(hero.x)&&gPl.safe_y==PX(hero.y));
 /* Launch, steering, slow/fast descent and lower landing are physically
    bounded. No charged input may move a parachute outside its lower shelf. */
 for(j=0;j<3;j++) {
  fresh();sPadCooldown=0;hero.x=Q16(tile_x(5));hero.y=Q16(tile_y(6));hero.state=PS_NORMAL;gKeysDown=KEY_R;
  CHECK(handoff_mobility_pre_player()&&gMobilityMode==HMOB_PARACHUTE&&!(gKeysDown&KEY_R));
  for(i=0;i<200&&gMobilityMode==HMOB_PARACHUTE;i++) {
   gKeysHeld=(j==0?KEY_UP|KEY_LEFT:j==1?KEY_DOWN|KEY_RIGHT:0);gKeysDown=j==2&&i==10?KEY_A:0;
   oldy=hero.y;CHECK(handoff_mobility_pre_player());CHECK(hero.y>=oldy);
   CHECK(PX(hero.x)>=tile_x(3)&&PX(hero.x)<=tile_x(8));CHECK(hero.z>=0&&hero.z<=Q16(12));
  }
  CHECK(i<200&&hero.y==Q16(tile_y(11))&&hero.z==0&&hero.state==PS_NORMAL&&!gPl.input_lock);
  CHECK(ground[(PX(hero.y)-4)/16*32+PX(hero.x)/16]!=MT_LH_MOB_CLIFF);
 }
 /* Transport owns item controls; interruptions preserve semantic states. */
 fresh();sPadCooldown=0;hero.x=Q16(gMobilityCartX);hero.y=Q16(gMobilityCartY+9);
 CHECK(handoff_mobility_interact()&&handoff_mobility_busy());gKeysDown=KEY_B|KEY_L|KEY_R;gKeysHeld=KEY_B|KEY_L|KEY_R;
 CHECK(handoff_mobility_pre_player()&&gPl.input_lock==1&&!gKeysDown&&!gKeysHeld);
 hero.state=PS_SWALLOWED;CHECK(!handoff_mobility_pre_player()&&hero.state==PS_SWALLOWED&&!handoff_mobility_busy()&&!gPl.input_lock);
 fresh();sPadCooldown=0;hero.x=Q16(tile_x(5));hero.y=Q16(tile_y(6));gKeysDown=KEY_R;
 CHECK(handoff_mobility_pre_player()&&handoff_mobility_busy());hero.state=PS_HURT;
 CHECK(!handoff_mobility_pre_player()&&hero.state==PS_HURT&&hero.y==Q16(tile_y(11))&&hero.z==0&&!gPl.input_lock);
 fresh();sPadCooldown=0;hero.x=Q16(gMobilityCartX);hero.y=Q16(gMobilityCartY+9);CHECK(handoff_mobility_interact());
 hero.state=PS_DEAD;CHECK(!handoff_mobility_pre_player()&&hero.state==PS_DEAD&&!handoff_mobility_busy());
 /* Fusion reward is real and once-only across a rebuilt room. */
 fresh();gHandoffState.fusion_flags=4;handoff_mobility_build(42);hero.x=Q16(tile_x(26));hero.y=Q16(tile_y(6));
 CHECK(handoff_mobility_interact()&&grants==1&&notifies==1&&prize_taken());
 CHECK(handoff_mobility_interact()&&grants==1);handoff_mobility_build(42);CHECK(ground[6*32+26]==MT_LH_MOB_OPEN);
 CHECK(handoff_mobility_interact()&&grants==1);
 /* Hooks are inert outside the new annex, including collision and layers. */
 gGame.area=AREA_FOREST;gMobilityLayer=1;CHECK(!handoff_mobility_pre_player());
 CHECK(!handoff_mobility_interact()&&!handoff_mobility_box_solid(0,0,500,500));
 CHECK(!handoff_mobility_handles_floor(248,230)&&handoff_mobility_priority(2)==2);
 printf("{\"checks\":%d,\"cart_stop\":%d,\"course_tiles\":%d}\n",checks,gMobilityCartPoint,32*24);return 0;
}
'''
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True);p.add_argument('--cc',default='cc');a=p.parse_args();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
 f=out/'mobility-host.c';f.write_text(fixture()+MAIN);binary=out/'mobility-host';command=[a.cc,'-std=gnu11','-O2',str(f),'-o',str(binary)]
 result=subprocess.run(command,capture_output=True,text=True);(out/'compile.log').write_text(result.stdout+result.stderr);result.check_returncode()
 result=subprocess.run([str(binary)],capture_output=True,text=True);(out/'run.log').write_text(result.stdout+result.stderr);result.check_returncode();counts=json.loads(result.stdout)
 inputs=['src/handoff_mobility.c','src/handoff_mobility.h','art/handoff_mobility.py','src/player.h','src/actor.h','src/legacy_items.h','src/handoff_events.h']
 report=dict(passed=True,method=__doc__,**counts,source_hashes={n:SHA((GAME/n).read_bytes()) for n in inputs},tool_sha256=SHA(Path(__file__).read_bytes()),compiled_source_sha256=SHA(f.read_bytes()))
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(counts))
if __name__=='__main__':main()

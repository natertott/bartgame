/* Native mechanism courses append the handoff's object verbs without
   modifying any old room, actor sheet, or existing mystery puzzle. */
#include "handoff_objects.h"
#include "handoff_events.h"
#include "legacy_items.h"
#include "legacy_enemies.h"
#include "player.h"
#include "room.h"
#include "actor.h"
#include "objects.h"
#include "enemy.h"
#include "video.h"
#include "sound.h"
#include "text.h"
#include "game.h"
#include "util.h"

#define HO_LIMIT 24
#define HO_ABS(x) ((x)<0?-(x):(x))
enum { HO_STATUE,HO_GRAVE,HO_FURNITURE,HO_BIG_DOOR,HO_BOSS_DOOR,
 HO_LIGHT_DOOR,HO_METAL_DOOR,HO_PULL_LEVER,HO_PUSH_LEVER,HO_HIT_LEVER,
 HO_BIG_LEVER,HO_FLOAT,HO_LAVA,HO_LILY,HO_FAN,HO_WHIRLWIND,HO_STEAM,
 HO_BAR,HO_CHAIN,HO_HIDDEN_LADDER,HO_BEANSTALK,HO_WARP,HO_TRAP,
 HO_ROTATING_TRAP,HO_BRIDGE,HO_WEATHER,HO_PACCI_POT,HO_GUST_LOAD,
 HO_TORCH,HO_TARGET,HO_SWITCH,HO_PULL_ROCK,HO_LIGHT_SWITCH,HO_EYE_SWITCH,
 HO_LIGHT_RAY,HO_JAR_PORTAL,HO_BIG_ICE,HO_FROZEN_FLOWER,HO_BARREL_WEB,
 HO_LADDER_DOWN,HO_DEST_HOLE,HO_LIGHT_RECEIVER,HO_COUNT };

typedef struct {
 s16 x,y,home_x,home_y;
 u16 tile,timer;
 u8 type,state,frame,pending,solid,goal,link,mode,last_frame;
} Mechanism;
static Mechanism sObjects[HO_LIMIT] EWRAM_BSS;
static u16 sWeatherTile;
static struct {
 u16 clock;u32 seed;
 u8 count,active,variant,goals,weather,manip_index,manip_tick,manip_dir,manip_pull;
 s16 move_x,move_y,hero_x,hero_y;
 s16 field_left,field_top,field_right,field_bottom;
 u8 jar_load,jar_key,complete,climb_ticks,portal_cooldown;
 u8 regional,field,pattern,mirror,required_goals,interlock,fusion;
} sObj EWRAM_BSS;
static bool8 overlap(const Mechanism* m,int x0,int y0,int x1,int y1,int hw,int hh) {
 return x1>=m->x-hw&&x0<=m->x+hw&&y1>=m->y-hh&&y0<=m->y+hh;
}
static void flag_goal(Mechanism* m) {
 if(m->goal)sObj.goals|=m->goal;
 if((sObj.goals&sObj.required_goals)==sObj.required_goals)sObj.complete=1;
}
static void ping(Mechanism* m) {sfx_play(SFX_SECRET);fx_spawn(FX_SPARK,m->x,m->y-12);}
static Mechanism* add(int type,int tx,int ty,int solid,int goal) {
 Mechanism*m;if(sObj.count>=HO_LIMIT)return NULL;
 m=&sObjects[sObj.count++];memset(m,0,sizeof(*m));m->type=type;
 m->x=m->home_x=tx*16+8;m->y=m->home_y=ty*16+12;
 m->solid=solid;m->goal=goal;m->frame=m->last_frame=type*2;m->pending=1;m->link=255;return m;
}
void handoff_objects_reset(void) {sWeatherTile=0;memset(&sObj,0,sizeof(sObj));memset(sObjects,0,sizeof(sObjects));}
int handoff_objects_variant(void) {return sObj.active?sObj.variant:-1;}
bool8 handoff_objects_complete(void) {return sObj.active&&sObj.complete;}
static void surface_patch(int x0,int y0,int w,int h,u16 tile) {
 int x,y;for(y=y0;y<y0+h;y++)for(x=x0;x<x0+w;x++)room_set(x,y,tile);
}
static void patch(int x0,int y0,int w,int h,u16 tile) {int x,y;for(y=y0;y<y0+h;y++)for(x=x0;x<x0+w;x++)room_set(x,y,tile);}
void handoff_objects_build(u32 seed) {
 int i;Mechanism*m;
 handoff_objects_reset();sObj.active=1;sObj.seed=seed;sObj.variant=(seed>>8)&3;sObj.required_goals=7;
 /* Each station has broad approach space and a permanent south exit. No
    newly discovered optional tool can strand the existing run. */
 if(sObj.variant==0) {
  add(HO_STATUE,7,16,1,0);add(HO_GRAVE,15,16,1,0);add(HO_FURNITURE,24,16,1,0);
  add(HO_SWITCH,7,13,0,0);add(HO_SWITCH,15,13,0,0);add(HO_SWITCH,24,13,0,0);
  add(HO_PULL_LEVER,7,10,1,1);add(HO_PUSH_LEVER,15,10,1,2);add(HO_HIT_LEVER,24,10,1,4);
  m=add(HO_BIG_DOOR,5,5,1,0);if(m)m->link=6;
  m=add(HO_METAL_DOOR,11,5,1,0);if(m)m->link=7;
  add(HO_LIGHT_DOOR,20,5,1,0);add(HO_BOSS_DOOR,27,5,1,0);
  add(HO_BIG_LEVER,15,7,1,0);add(HO_EYE_SWITCH,27,8,0,0);add(HO_LIGHT_SWITCH,20,8,0,0);
  add(HO_PULL_ROCK,4,18,1,0);add(HO_TORCH,20,11,1,0);
  surface_patch(2,12,2,2,MT_LH_SLOPE_X);surface_patch(27,12,2,2,MT_LH_SLOPE_Y);
  room_set(10,20,MT_LH_CONVEYOR_N);room_set(11,20,MT_LH_CONVEYOR_E);
  room_set(11,21,MT_LH_CONVEYOR_S);room_set(10,21,MT_LH_CONVEYOR_W);
  m=add(HO_BIG_DOOR,8,3,1,0);if(m)m->mode=1;
  m=add(HO_BIG_DOOR,23,3,1,0);if(m)m->mode=2;
 }else if(sObj.variant==1) {
  patch(4,7,6,5,MT_LH_MOB_PIT);patch(13,7,6,5,MT_LH_LAVA);patch(22,7,6,5,MT_LH_MOB_WATER);
  for(i=0;i<3;i++) {int x=7+i*9;patch(x-1,8,2,1,MT_CAVE_FLOOR0);add(HO_TARGET,x,8,0,1<<i);}
  m=add(HO_FLOAT,5,11,0,0);if(m){m->mode=1;m->link=64;}
  m=add(HO_LAVA,14,11,0,0);if(m){m->mode=1;m->link=64;}
  m=add(HO_LILY,23,11,0,0);if(m){m->mode=1;m->link=64;}
  add(HO_FAN,5,17,1,0);add(HO_WHIRLWIND,16,17,0,0);add(HO_STEAM,25,17,0,0);
  add(HO_BAR,9,4,0,0);add(HO_CHAIN,23,4,0,0);
  surface_patch(4,14,3,2,MT_LH_ICE);surface_patch(13,14,3,2,MT_LH_SWAMP);surface_patch(22,14,3,2,MT_LH_DUST);
  surface_patch(28,9,2,2,MT_LH_SHALLOW);surface_patch(11,9,1,3,MT_LH_CRUMBLE);
 }else if(sObj.variant==2) {
  add(HO_HIDDEN_LADDER,5,8,0,1);add(HO_BEANSTALK,15,8,1,0);add(HO_WEATHER,25,8,1,2);
  m=add(HO_WARP,5,14,0,0);if(m)m->link=4;
  m=add(HO_WARP,25,14,0,0);if(m)m->link=3;
  add(HO_TRAP,10,17,0,0);add(HO_ROTATING_TRAP,21,17,0,0);
  patch(12,11,8,3,MT_LH_MOB_PIT);add(HO_BRIDGE,15,12,0,0);
  m=add(HO_PULL_LEVER,15,16,1,4);if(m)m->link=7;
  add(HO_FAN,8,5,1,0);add(HO_STEAM,23,5,0,0);
  room_set(3,19,MT_LH_MINISH_PORTAL);
  patch(6,17,4,4,MT_CAVE_WALL);patch(7,18,2,2,MT_CAVE_FLOOR0);room_set(6,19,MT_LH_MINISH_GAP);
  add(HO_TARGET,8,18,0,0);
  room_set(11,19,MT_LH_CLONE_PLATE);room_set(13,19,MT_LH_CLONE_PLATE);room_set(15,19,MT_LH_CLONE_PLATE);
  room_set(17,19,MT_LH_CLONE_PLATE); /* fourth station belongs to the original Bloom */
  add(HO_SWITCH,11,18,0,0);add(HO_SWITCH,13,18,0,0);add(HO_SWITCH,15,18,0,0);
  m=add(HO_METAL_DOOR,15,9,1,0);if(m)m->mode=1;
  for(i=12;i<=18;i++){room_set(i,4,MT_CAVE_WALL);if(i!=15)room_set(i,9,MT_CAVE_WALL);}
  for(i=5;i<=8;i++){room_set(12,i,MT_CAVE_WALL);room_set(18,i,MT_CAVE_WALL);}
#ifdef MT_LH_SHAPE_NW
  for(i=0;i<9;i++)room_set(3+i*3,3,MT_LH_SHAPE_NW+i);
#endif
 }else {
  add(HO_PACCI_POT,7,12,1,0);add(HO_GUST_LOAD,15,12,0,0);add(HO_TARGET,24,12,0,0);
  add(HO_LIGHT_SWITCH,7,7,0,1);add(HO_EYE_SWITCH,15,7,0,2);add(HO_HIT_LEVER,24,7,1,4);
  add(HO_LIGHT_DOOR,7,4,1,0);add(HO_METAL_DOOR,15,4,1,0);add(HO_BOSS_DOOR,24,4,1,0);
  add(HO_TORCH,4,17,1,0);add(HO_BIG_LEVER,12,17,1,0);add(HO_PULL_ROCK,21,17,1,0);
  add(HO_HIDDEN_LADDER,27,18,0,0);add(HO_BEANSTALK,27,8,1,0);
  add(HO_LIGHT_RAY,25,6,0,0);add(HO_LIGHT_RECEIVER,25,3,0,0);
  add(HO_JAR_PORTAL,3,20,0,0);legacy_surface_set(3,20,LS_MINISH_PORTAL);room_set(3,20,MT_LH_MINISH_PORTAL);
  add(HO_BIG_ICE,20,18,1,0);add(HO_FROZEN_FLOWER,22,18,1,0);add(HO_BARREL_WEB,8,18,1,0);
  m=add(HO_LADDER_DOWN,3,4,0,0);if(m)m->link=21;
  m=add(HO_DEST_HOLE,28,20,0,0);if(m)m->link=20;
  surface_patch(3,16,2,2,MT_LH_DIG);surface_patch(5,16,1,3,MT_LH_DIG_WALL);
  room_set(24,18,MT_LH_DASH_WALL);room_set(18,18,MT_LH_SPRING);room_set(27,10,MT_LH_WATER_SPROUT);
  room_set(19,5,MT_LH_ICE_BLOCK);
 }
}
/* Regional ruins are small, coherent puzzles. The entrance and permanent
   return remain the room builder's; only this puzzle's own footprint changes. */
static int rx(int x) {return sObj.mirror?31-x:x;}
static Mechanism* radd(int type,int x,int y,int solid,int goal) {return add(type,rx(x),y,solid,goal);}
static void rpatch(int x,int y,int w,int h,u16 mt) {for(int yy=y;yy<y+h;yy++)for(int xx=x;xx<x+w;xx++)room_set(rx(xx),yy,mt);}
static void rwall(int y,int x0,int x1,int gap) {for(int x=x0;x<=x1;x++)if(x!=gap)room_set(rx(x),y,MT_CAVE_WALL);}
static void reward_goal(int x,int y) {radd(HO_TARGET,x,y,0,128);}
static void bonus_goal(int x,int y,int bit) {
 Mechanism*m=radd(HO_TARGET,x,y,0,0);if(m){m->mode=2;m->link=bit;
  if(gHandoffState.remaining[handoff_current_site()]&(1u<<bit))m->state=1;}
}
bool8 handoff_objects_can_solve(int pattern) {
 int i;bool8 bottle=FALSE,mineral=FALSE;
 for(i=0;i<4;i++)if(legacy_item_owned(LI_BOTTLE1+i)){bottle=TRUE;if(gLegacyInventory.bottles[i]==LI_BOTTLE_MINERAL_WATER)mineral=TRUE;}
 switch(pattern%HANDOFF_REGIONAL_MECHANISMS) {
 case 4:return bottle;
 case 7:return legacy_item_owned(LI_POWER_BRACELETS)||legacy_item_owned(LI_FOURSWORD);
 case 8:return legacy_item_owned(LI_MIRROR_SHIELD);
 case 9:return legacy_item_owned(LI_FOURSWORD);
 case 10:return legacy_item_owned(LI_PACCI_CANE)&&(legacy_item_owned(LI_BOW)||legacy_item_owned(LI_LIGHT_ARROW));
 case 11:return legacy_item_owned(LI_FIRE_ROD)||(mineral&&legacy_item_owned(LI_LANTERN_OFF));
 default:return TRUE;
 }
}
bool8 handoff_objects_field_can_solve(int variant) {
 switch(variant&3) {
 case 1:return legacy_item_owned(LI_LANTERN_OFF)||legacy_item_owned(LI_FIRE_ROD);
 case 2:for(int i=0;i<4;i++)if(legacy_item_owned(LI_BOTTLE1+i))return TRUE;return FALSE;
 case 3:return legacy_item_owned(LI_PACCI_CANE);
 default:return TRUE;
 }
}
void handoff_objects_build_regional(u32 seed,int pattern) {
 Mechanism *m,*a,*b;
 handoff_objects_reset();sObj.active=sObj.regional=1;sObj.seed=seed;
 sObj.pattern=pattern%HANDOFF_REGIONAL_MECHANISMS;sObj.variant=sObj.pattern%4;
 sObj.mirror=seed&1;sObj.required_goals=128;
 switch(sObj.pattern) {
 case 0: /* A storeroom: move the statue onto its plate to open the old seal. */
  rwall(9,4,27,15);m=radd(HO_METAL_DOOR,15,9,1,0);if(m){m->mode=2;m->link=1;}
  a=radd(HO_SWITCH,11,14,0,1);if(a)a->link=0;
  radd(HO_STATUE,11,16,1,0);radd(HO_GRAVE,22,16,1,0);
  radd(HO_FURNITURE,6,17,1,0);radd(HO_PULL_ROCK,25,13,1,0);
  reward_goal(15,6);break;
 case 1: /* Three sealed vaults share a courtyard; each has a different verb. */
  for(int y=4;y<=16;y++){rpatch(3,y,1,1,MT_CAVE_WALL);rpatch(12,y,1,1,MT_CAVE_WALL);rpatch(21,y,1,1,MT_CAVE_WALL);rpatch(29,y,1,1,MT_CAVE_WALL);}
  rwall(9,4,11,7);rwall(9,13,20,16);rwall(9,22,28,25);
  radd(HO_BIG_DOOR,7,9,1,0);radd(HO_LIGHT_DOOR,16,9,1,0);radd(HO_BOSS_DOOR,25,9,1,0);
  radd(HO_LIGHT_SWITCH,16,14,0,0);radd(HO_TORCH,18,15,1,0);
  /* The final goal is the guardian vault; side vaults offer their own caches. */
  reward_goal(25,6);bonus_goal(7,6,0);bonus_goal(16,6,1);break;
 case 2: { /* A working ferry spans the only channel to the far-bank hoard. */
  int platform=HO_FLOAT+(seed>>4)%3;
  for(int y=5;y<=17;y++){rpatch(10,y,1,1,MT_CAVE_WALL);rpatch(21,y,1,1,MT_CAVE_WALL);}
  rpatch(11,11,10,3,platform==HO_LAVA?MT_LH_LAVA:platform==HO_LILY?MT_LH_MOB_WATER:MT_LH_MOB_PIT);
  m=radd(platform,15,14,0,0);if(m)m->mode=1;
  reward_goal(15,7);break;}
 case 3: /* A windy mine gallery, with steam and rotating hazards to time. */
  for(int y=5;y<=18;y++){rpatch(9,y,1,1,MT_CAVE_WALL);rpatch(22,y,1,1,MT_CAVE_WALL);}
  rpatch(10,10,12,2,MT_LH_MOB_PIT);radd(HO_WHIRLWIND,15,13,0,0);
  radd(HO_FAN,12,17,1,0);radd(HO_STEAM,19,15,0,0);
  radd(HO_BAR,12,7,0,0);radd(HO_CHAIN,19,7,0,0);
  reward_goal(15,5);break;
 case 4: /* Water feeds the dead garden; a loose stair and weather vane remain. */
  radd(HO_HIDDEN_LADDER,7,15,0,1);radd(HO_BEANSTALK,15,13,1,2);radd(HO_WEATHER,24,15,1,4);
  rwall(8,5,26,15);m=radd(HO_METAL_DOOR,15,8,1,0);if(m)m->mode=3;
  reward_goal(15,5);break;
 case 5: /* A visibly paired staircase reaches a sealed upper pocket. */
  rwall(9,3,28,-1);
  a=radd(HO_LADDER_DOWN,7,17,0,0);b=radd(HO_DEST_HOLE,24,6,0,0);
  if(a&&b){a->link=(u8)(b-sObjects);b->link=(u8)(a-sObjects);}
  a=radd(HO_WARP,24,15,0,0);b=radd(HO_WARP,7,6,0,0);
  if(a&&b){a->link=(u8)(b-sObjects);b->link=(u8)(a-sObjects);}
  radd(HO_TRAP,15,16,0,0);radd(HO_ROTATING_TRAP,19,13,0,0);reward_goal(15,5);break;
 case 6: /* Pulling the lower-bank handle raises the missing bridge itself. */
  for(int y=5;y<=18;y++){rpatch(10,y,1,1,MT_CAVE_WALL);rpatch(21,y,1,1,MT_CAVE_WALL);}
  rpatch(11,11,10,3,MT_LH_MOB_PIT);radd(HO_BRIDGE,15,12,0,0);
  radd(HO_PULL_LEVER,15,17,1,1);reward_goal(15,6);break;
 case 7: /* Farm/grave keys and three styles of handle guard a compact crypt. */
  rwall(9,3,28,15);m=radd(HO_METAL_DOOR,15,9,1,0);if(m)m->mode=3;
  radd(HO_PULL_LEVER,8,16,1,1);radd(HO_PUSH_LEVER,15,16,1,2);radd(HO_BIG_LEVER,23,16,1,4);
  for(int i=0;i<4;i++)room_set(rx(18+i*2),19,MT_LH_CLONE_PLATE);
  rwall(6,4,11,8);rwall(6,20,27,23);
  for(int y=3;y<6;y++){rpatch(4,y,1,1,MT_CAVE_WALL);rpatch(11,y,1,1,MT_CAVE_WALL);rpatch(20,y,1,1,MT_CAVE_WALL);rpatch(27,y,1,1,MT_CAVE_WALL);}
  m=radd(HO_BIG_DOOR,8,6,1,0);if(m)m->mode=1;
  m=radd(HO_BIG_DOOR,23,6,1,0);if(m)m->mode=2;
  bonus_goal(8,4,0);bonus_goal(23,4,1);
  rpatch(11,18,2,1,MT_LH_CONVEYOR_N);rpatch(19,18,2,1,MT_LH_CONVEYOR_S);
  reward_goal(15,5);break;
 case 8: /* Reflect the ray into its north receiver to release the shrine seal. */
  rwall(8,3,28,15);m=radd(HO_METAL_DOOR,15,8,1,0);
  a=radd(HO_LIGHT_RECEIVER,15,9,0,1);if(a)a->link=0;
  radd(HO_LIGHT_RAY,15,12,0,0);reward_goal(15,4);break;
 case 9: /* A Four Sword formation opens a real gate; the jar is a small route. */
  rwall(9,4,27,15);m=radd(HO_METAL_DOOR,15,9,1,0);if(m)m->mode=1;
  for(int i=0;i<4;i++)room_set(rx(10+i*2),19,MT_LH_CLONE_PLATE);
  for(int i=0;i<3;i++)radd(HO_SWITCH,10+i*2,17,0,0);
  radd(HO_JAR_PORTAL,4,19,0,0);legacy_surface_set(rx(4),19,LS_MINISH_PORTAL);room_set(rx(4),19,MT_LH_MINISH_PORTAL);
  rpatch(23,14,5,5,MT_CAVE_WALL);rpatch(24,15,3,3,MT_CAVE_FLOOR0);room_set(rx(23),17,MT_LH_MINISH_GAP);
  bonus_goal(25,16,0);reward_goal(15,6);break;
 case 10: /* The three tool seals use actual projectiles, not menu checks. */
  rwall(8,3,28,15);m=radd(HO_METAL_DOOR,15,8,1,0);if(m)m->mode=3;
  radd(HO_PACCI_POT,8,13,1,1);radd(HO_EYE_SWITCH,15,11,0,2);radd(HO_HIT_LEVER,23,13,1,4);
  radd(HO_GUST_LOAD,20,17,0,0);radd(HO_LIGHT_SWITCH,6,17,0,0);radd(HO_LIGHT_DOOR,6,11,1,0);
  room_set(rx(8),16,MT_LH_SPRING);rpatch(4,18,2,2,MT_LH_DIG);rpatch(6,18,1,2,MT_LH_DIG_WALL);
  room_set(rx(25),17,MT_LH_DASH_WALL);room_set(rx(27),12,MT_LH_WATER_SPROUT);
  reward_goal(15,5);break;
 default: /* Thaw the cellar, free its flower, and burn or draw away the silk. */
  rwall(8,3,28,15);m=radd(HO_METAL_DOOR,15,8,1,0);if(m)m->mode=3;
  radd(HO_BIG_ICE,8,14,1,1);radd(HO_FROZEN_FLOWER,16,14,1,2);radd(HO_BARREL_WEB,24,14,1,4);
  rpatch(11,11,10,2,MT_LH_ICE);rpatch(5,18,4,1,MT_LH_SHALLOW);rpatch(22,18,4,1,MT_LH_SWAMP);
  room_set(rx(25),10,MT_LH_CRUMBLE);room_set(rx(6),11,MT_LH_DUST);room_set(rx(20),18,MT_LH_ICE_BLOCK);
  reward_goal(15,5);break;
 }
 /* Consumed regional keys leave their matching doors open on later visits. */
 for(int i=0;i<sObj.count;i++)if(sObjects[i].type==HO_BIG_DOOR&&sObjects[i].mode<3&&
    (gHandoffState.remaining[handoff_current_site()]&(1u<<(8+sObjects[i].mode)))) {
  sObjects[i].state=1;sObjects[i].solid=0;sObjects[i].frame=HO_BIG_DOOR*2+1;sObjects[i].last_frame=sObjects[i].frame;
 }
}
bool8 handoff_objects_build_field(u32 seed,int variant,int x,int y,int w,int h) {
 Mechanism*m;
 if(w<5||h<4||x<1||y<1||x+w>=gRoom.w||y+h>=gRoom.h)return FALSE;
 /* The planner reserves dry floor. Refuse changed or occupied footprints. */
 for(int yy=y;yy<y+h;yy++)for(int xx=x;xx<x+w;xx++)
  if(room_box_solid(xx*16+1,yy*16+1,xx*16+14,yy*16+14)||room_get_overlay(xx,yy)!=MT_NONE||room_type(xx,yy)!=TT_FLOOR||legacy_surface_at(xx*16+8,yy*16+8)!=LS_NONE)return FALSE;
 handoff_objects_reset();sObj.active=sObj.regional=sObj.field=1;sObj.seed=seed;
 sObj.pattern=variant%HANDOFF_REGIONAL_MECHANISMS;sObj.variant=sObj.pattern%4;sObj.required_goals=128;sObj.interlock=1;
 sObj.field_left=x*16;sObj.field_top=y*16;sObj.field_right=(x+w)*16-1;sObj.field_bottom=(y+h)*16-1;
 switch(sObj.pattern) {
 case 0:case 6:
  add(HO_STATUE,x+1,y+2,1,0);add(HO_SWITCH,x+1,y+1,0,1);break;
 case 1:case 11:add(HO_FROZEN_FLOWER,x+1,y+1,1,1);add(HO_BARREL_WEB,x+3,y+1,1,2);sObj.interlock=3;break;
 case 2:case 4:add(HO_BEANSTALK,x+2,y+1,1,1);break;
 case 3:case 10:add(HO_PACCI_POT,x+2,y+1,1,1);break;
 case 5:add(HO_HIDDEN_LADDER,x+1,y+1,0,1);break;
 case 7:add(HO_BIG_LEVER,x+1,y+1,1,1);break;
 case 8:add(HO_LIGHT_RECEIVER,x+2,y,0,1);add(HO_LIGHT_RAY,x+2,y+1,0,0);break;
 case 9:add(HO_WEATHER,x+1,y+1,1,1);break;
 }
 m=add(HO_TARGET,x+w-2,y+h-2,0,128);if(m)m->mode=1;
 return TRUE;
}

bool8 handoff_objects_build_fusion(u32 seed,int x,int y,int w,int h) {
 if(h<5||!handoff_objects_build_field(seed,0,x,y,w,h))return FALSE;
 u16 island=room_get(x+2,y+2);
 memset(sObjects,0,sizeof(sObjects));sObj.count=0;sObj.fusion=1;sObj.interlock=0;
 for(int yy=y+1;yy<y+4;yy++)for(int xx=x+1;xx<x+4;xx++)room_set(xx,yy,MT_LH_MOB_WATER);
 /* A 16px island holds the reward. Its southern approach is an actual gap,
    never a cosmetic flag; a red fusion inserts its walkable bridge. */
 room_set(x+2,y+2,island);
 if(gHandoffState.fusion_flags&4)room_set(x+2,y+3,MT_LH_MOB_RAMP);
 Mechanism*m=add(HO_TARGET,x+2,y+2,0,128);if(m)m->mode=3;
 room_build_solid();return TRUE;
}

void handoff_objects_enter(void) {
 int i;if(!sObj.active)return;
 for(i=0;i<sObj.count;i++) {sObjects[i].tile=sprite_alloc(16);sObjects[i].pending=1;}
 sWeatherTile=sprite_load_sheet(SHEET_HANDOFF_WEATHER);
 for(i=0;i<sObj.count;i++)if(sObjects[i].type==HO_BOSS_DOOR) {
  enemy_spawn(LE_BEETLE_0,sObjects[i].x-20,sObjects[i].y-28);
  enemy_spawn(LE_KEESE_0,sObjects[i].x+20,sObjects[i].y-36);break;
 }
 if(!sObj.regional&&sObj.variant==0&&!legacy_item_owned(LI_BIG_KEY))legacy_item_spawn(LI_BIG_KEY,5*16+8,18*16+8);
 if(sObj.regional&&!sObj.field&&sObj.pattern==1&&!(gHandoffState.remaining[handoff_current_site()]&0x100)&&!legacy_item_owned(LI_BIG_KEY))legacy_item_spawn(LI_BIG_KEY,rx(7)*16+8,17*16+8);
 if(sObj.regional&&!sObj.field&&sObj.pattern==10&&!gPl.arrows&&(legacy_item_owned(LI_BOW)||legacy_item_owned(LI_LIGHT_ARROW)))legacy_item_spawn(LI_ARROWS5,rx(15)*16+8,18*16+8);
 if(sObj.regional) {
  static const char* const clues[HANDOFF_REGIONAL_MECHANISMS]={
   "The stone keeper rests beside an empty pressure plate. Its weight may open the northern seal.",
   "Three vaults: a great key, a flame, and the defeat of the guardians. The north courtyard holds their prize.",
   "The old ferry still reaches both banks. Stand on its broad center and let it carry you across.",
   "The mine breathes. Time the steam, take the rising wind, and watch the circling fire.",
   "A loose stair, a thirsty root, a weather vane. Wake all three to open the garden's seal.",
   "Paired stairs and violet pads reach the upper pocket. The southern passage remains the way home.",
   "The handle on this bank raises the bridge. The far bank holds a golden mark.",
   "Pull, push, and weight answer the three handles. Smaller locks remember farm and grave keys.",
   "Face the falling light with a mirror. Its receiver is fixed to the front of the northern seal.",
   "Three copies can hold the plates. A small jar offers another route to a hidden alcove.",
   "Turn the pot, strike the eye, and cut the far handle. The jar can send a clod across the gap.",
   "Fire frees the flower and silk; mineral water also melts the great ice. Three signs wake the northern seal."};
  if(!sObj.field)textbox_open(clues[sObj.pattern]);
  return;
 }
 textbox_open(sObj.variant==0?"Mechanism court. Hold R and a direction to push or pull. Levers answer a pull, a push, or a sword. Three gold marks complete the trial.":
 sObj.variant==1?"Crossing court. The broad rafts carry your feet over the channels. Time the steam and circling fire. Visit all three gold standards.":
 sObj.variant==2?"Hidden court. Inspect the loose stair, pull the bridge lever, and turn the weather vane. Water feeds the old beanstalk. South is always open.":
 "Tool court. Fire lights the lantern seal, arrows find the eye, and a blade turns the lever. Pacci flips pottery; the jar catches and launches debris.");
}
static bool8 movable(int type) {return type==HO_STATUE||type==HO_GRAVE||type==HO_FURNITURE||type==HO_PULL_ROCK;}
static bool8 target_free(int index,int x,int y) {
 int i;
 /* Preserve the permanent south exit even when moving the largest furniture. */
 if(!sObj.field&&x+12>=14*16&&x-12<=18*16&&y+8>=21*16)return FALSE;
 if(sObj.field&&(x-12<sObj.field_left||x+12>sObj.field_right||y-8<sObj.field_top||y+8>sObj.field_bottom))return FALSE;
 if(room_box_solid(x-11,y-8,x+11,y+7))return FALSE;
 for(i=0;i<sObj.count;i++)if(i!=index&&sObjects[i].solid&&overlap(&sObjects[i],x-10,y-7,x+10,y+7,12,8))return FALSE;
 return TRUE;
}
static void open_link(Mechanism*m) {
 int i;if(m->link<sObj.count){sObjects[m->link].state=1;sObjects[m->link].solid=0;sObjects[m->link].pending=1;}
 for(i=0;i<sObj.count;i++)if(sObjects[i].type==HO_METAL_DOOR&&!sObjects[i].mode){sObjects[i].state=1;sObjects[i].solid=0;}
}
bool8 handoff_objects_pre_player(void) {
 int i,px,py,dir,dx,dy;Actor*a=gPlayer;
 if(!sObj.active||!a||textbox_active())return FALSE;
 if(sObj.climb_ticks&&a->state==PS_NORMAL) {
  if(room_box_solid(PX(a->x)-5,PX(a->y)-10,PX(a->x)+4,PX(a->y)-1)){sObj.climb_ticks=0;return FALSE;}
  a->y-=Q16(.75);player_external_walk_tick(Q8(.75),DIR_N);sObj.climb_ticks--;
  if(a->iframes)a->iframes--;
  if(gPl.item_cooldown)gPl.item_cooldown--;
  return TRUE;
 }
 if(a->state!=PS_NORMAL){sObj.climb_ticks=sObj.manip_tick=0;return FALSE;}
 if(sObj.manip_tick) {
  Mechanism*m=&sObjects[sObj.manip_index];int t=33-sObj.manip_tick;
  dx=sObj.manip_dir==DIR_E?1:sObj.manip_dir==DIR_W?-1:0;dy=sObj.manip_dir==DIR_S?1:sObj.manip_dir==DIR_N?-1:0;
  m->x=sObj.move_x+dx*t/2;m->y=sObj.move_y+dy*t/2;
  a->x=Q16(sObj.hero_x)+dx*Q16(.5)*t;a->y=Q16(sObj.hero_y)+dy*Q16(.5)*t;player_external_walk_tick(Q8(.5),facing_to_dir(a->facing));
  if(a->iframes)a->iframes--;
  if(gPl.item_cooldown)gPl.item_cooldown--;
  if(!--sObj.manip_tick){m->x=sObj.move_x+dx*16;m->y=sObj.move_y+dy*16;ping(m);}return TRUE;
 }
 px=PX(a->x);py=PX(a->y)-4;dir=facing_to_dir(a->facing);
 dx=dir==DIR_E?1:dir==DIR_W?-1:0;dy=dir==DIR_S?1:dir==DIR_N?-1:0;
 for(i=0;i<sObj.count;i++) {
  Mechanism*m=&sObjects[i];int kind=m->type;
  if(!overlap(m,px+dx*14-5,py+dy*14-5,px+dx*14+5,py+dy*14+5,13,11))continue;
  if(movable(kind)&&(gKeysHeld&KEY_R)) {
   int move=DIR_NONE;
   if(gKeysHeld&KEY_UP)move=DIR_N;else if(gKeysHeld&KEY_DOWN)move=DIR_S;else if(gKeysHeld&KEY_LEFT)move=DIR_W;else if(gKeysHeld&KEY_RIGHT)move=DIR_E;
   if(move==DIR_NONE)continue;
   int mx=move==DIR_E?16:move==DIR_W?-16:0,my=move==DIR_S?16:move==DIR_N?-16:0;
   if((move==dir||move==((dir+16)&31))&&target_free(i,m->x+mx,m->y+my)&&!room_box_solid(px+mx-5,py+my-6,px+mx+5,py+my+3)) {
    sObj.manip_index=i;sObj.manip_tick=32;sObj.manip_dir=move;sObj.manip_pull=move!=dir;
    sObj.move_x=m->x;sObj.move_y=m->y;sObj.hero_x=PX(a->x);sObj.hero_y=PX(a->y);
    gKeysDown&=~KEY_R;return TRUE;
   }
  }
  if(!(gKeysDown&KEY_R))continue;
  if(kind==HO_PULL_LEVER||kind==HO_PUSH_LEVER||kind==HO_BIG_LEVER) {
   if(kind==HO_BIG_LEVER&&!legacy_item_owned(LI_POWER_BRACELETS)&&!legacy_player_clone_count()) {textbox_open("The heavy handle needs more strength. Bracelets or another Bloom could move it.");return TRUE;}
   m->state^=1;open_link(m);flag_goal(m);ping(m);gKeysDown&=~KEY_R;return TRUE;
  }
  if(kind==HO_BIG_DOOR) {
   int key=m->mode==1?LI_QST_LONLON_KEY:m->mode==2?LI_QST_GRAVEYARD_KEY:LI_BIG_KEY;
   if(!legacy_item_owned(key)){textbox_open(m->mode==1?"The farm gate needs the Farm Key.":m->mode==2?"The grave gate needs the Graveyard Key.":"The large keyhole needs a Big Key. Ordinary keys do not fit.");return TRUE;}
   legacy_item_remove(key);m->solid=0;m->state=1;
   if(sObj.regional&&!sObj.field)gHandoffState.remaining[handoff_current_site()]|=1u<<(8+m->mode);
   flag_goal(m);ping(m);gKeysDown&=~KEY_R;return TRUE;
  }
  if(kind==HO_HIDDEN_LADDER) {
   if(m->state){player_set_pos(m->x,m->y+4);sObj.climb_ticks=64;}
   else{m->state=1;flag_goal(m);ping(m);}
   gKeysDown&=~KEY_R;return TRUE;
  }
  if(kind==HO_WEATHER) {sObj.weather=(sObj.weather+1)%3;m->state=sObj.weather;flag_goal(m);ping(m);gKeysDown&=~KEY_R;return TRUE;}
  if(kind==HO_WARP&&m->link<sObj.count) {Mechanism* to=&sObjects[m->link];player_set_pos(to->x,to->y+18);sfx_play(SFX_SECRET);gKeysDown&=~KEY_R;return TRUE;}
  if(kind==HO_PACCI_POT&&m->state) {a->state=PS_JUMP;a->zvel=Q16(1.625);a->dir=DIR_N;a->speed=Q8(.46875);gKeysDown&=~KEY_R;return TRUE;}
  if((kind==HO_LADDER_DOWN||kind==HO_DEST_HOLE)&&!sObj.portal_cooldown&&m->link<sObj.count) {
   Mechanism* to=&sObjects[m->link];int tx=to->x,ty=to->y+18;
   if(!room_box_solid(tx-6,ty-10,tx+5,ty)&&!handoff_objects_box_solid(tx-6,ty-10,tx+5,ty)) {
    player_set_pos(tx,ty);a->state=PS_JUMP;a->z=Q16(24);a->zvel=0;a->speed=0;sObj.portal_cooldown=60;sfx_play(SFX_FALL);
   }
   gKeysDown&=~KEY_R;return TRUE;
  }
  if(kind==HO_FROZEN_FLOWER&&m->state&&m->timer!=255){player_heal(8);m->timer=255;ping(m);gKeysDown&=~KEY_R;return TRUE;}
  if(kind==HO_BEANSTALK&&m->state) {a->state=PS_JUMP;a->zvel=Q16(3.5625);a->dir=DIR_N;a->speed=Q8(1);gKeysDown&=~KEY_R;return TRUE;}
 }
 return FALSE;
}
bool8 handoff_objects_box_solid(int x0,int y0,int x1,int y1) {
 int i;if(!sObj.active)return FALSE;
 for(i=0;i<sObj.count;i++)if(sObjects[i].solid&&overlap(&sObjects[i],x0,y0,x1,y1,sObj.field?10:12,sObj.field?7:8))return TRUE;
 return FALSE;
}
bool8 handoff_objects_support(int px,int py) {
 int i;if(!sObj.active)return FALSE;
 for(i=0;i<sObj.count;i++) {
  Mechanism*m=&sObjects[i];
  if((m->type>=HO_FLOAT&&m->type<=HO_LILY)||(m->type==HO_BRIDGE&&m->state))
   if(overlap(m,px,py,px,py,15,9))return TRUE;
 }
 return FALSE;
}
void handoff_objects_tool_box(int kind,int x0,int y0,int x1,int y1) {
 int i;if(!sObj.active)return;
 for(i=0;i<sObj.count;i++) {
  Mechanism*m=&sObjects[i];if(!overlap(m,x0,y0,x1,y1,12,12))continue;
  if((m->type==HO_HIT_LEVER&&(kind==LE_HIT_SWORD||kind==LE_HIT_BOOMERANG||kind==LE_HIT_THROWN))||
     (m->type==HO_EYE_SWITCH&&(kind==LE_HIT_ARROW||kind==LE_HIT_BEAM))||
     ((m->type==HO_LIGHT_SWITCH||m->type==HO_LIGHT_DOOR||m->type==HO_TORCH)&&(kind==LE_HIT_LANTERN||kind==LE_HIT_FIRE))) {
   if(!m->state){m->state=1;m->solid=0;flag_goal(m);open_link(m);if(m->type==HO_TORCH)m->timer=240;ping(m);}
  }
  if(m->type==HO_BEANSTALK&&(kind==33||kind==34)&&!m->state){m->state=1;flag_goal(m);ping(m);}
  if(m->type==HO_PACCI_POT&&kind==LE_HIT_PACCI){m->state=1;m->timer=180;m->solid=0;flag_goal(m);ping(m);}
  if((m->type==HO_BIG_ICE&&(kind==LE_HIT_FIRE||kind==34))||
     (m->type==HO_FROZEN_FLOWER&&(kind==LE_HIT_FIRE||kind==LE_HIT_LANTERN))||
     (m->type==HO_BARREL_WEB&&(kind==LE_HIT_FIRE||kind==LE_HIT_LANTERN||kind==LE_HIT_GUST_SMALL||kind==LE_HIT_GUST_BIG))||
     (m->type==HO_LIGHT_RECEIVER&&kind==LE_HIT_REFLECTED)) {
   if(!m->state){m->state=1;m->solid=0;flag_goal(m);open_link(m);ping(m);}
  }
  if(m->type==HO_GUST_LOAD&&(kind==LE_HIT_GUST_SMALL||kind==LE_HIT_GUST_BIG)&&!sObj.jar_load) {sObj.jar_load=1;m->state=1;m->solid=0;ping(m);}
 }
}
static int ray_length(const Mechanism*m) {return sObj.field?MIN(144,MAX(16,sObj.field_bottom-16-m->y)):144;}
static int ray_receiver_y(const Mechanism*m) {
 int y=3*16;for(int i=0;i<sObj.count;i++)if(sObjects[i].type==HO_LIGHT_RECEIVER&&sObjects[i].x==m->x&&sObjects[i].y<m->y)y=MAX(y,sObjects[i].y);
 return y;
}
void handoff_objects_update(void) {
 int i,j;Actor*a=gPlayer;
 if(!sObj.active||!a)return;
 {
  int x0,y0,x1,y1;
  if(player_sword_box(&x0,&y0,&x1,&y1))handoff_objects_tool_box(LE_HIT_SWORD,x0,y0,x1,y1);
  if(player_lamp_box(&x0,&y0,&x1,&y1))handoff_objects_tool_box(LE_HIT_LANTERN,x0,y0,x1,y1);
  for(i=1;i<ACTOR_MAX;i++) {
   Actor* tool=&gActors[i];
   bool8 arrow=tool->kind==AK_PROJ&&tool->type==PJ_ARROW&&tool->v[0];
   bool8 thrown=tool->kind==AK_OBJECT&&tool->type==OBJ_THROWN&&PX(tool->z)<=18;
   if(arrow||thrown) {
    const Hitbox* hb=&gHitboxes[tool->hitbox];int x=PX(tool->x)+hb->ox,y=PX(tool->y)-PX(tool->z)+hb->oy;
    handoff_objects_tool_box(arrow?LE_HIT_ARROW:LE_HIT_THROWN,x-hb->hw,y-hb->hh,x+hb->hw-1,y+hb->hh-1);
   }
  }
 }
 sObj.clock++;if(sObj.portal_cooldown)sObj.portal_cooldown--;
 if(sObj.fusion&&(gHandoffState.fusion_flags&4)&&!sObj.jar_key) {
  room_change(sObj.field_left/16+2,sObj.field_top/16+3,MT_LH_MOB_RAMP);sObj.jar_key=1;
 }
 for(i=0;i<sObj.count;i++) {
  Mechanism*m=&sObjects[i];int oldx=m->x,oldy=m->y,t=m->type;
  if(t>=HO_FLOAT&&t<=HO_LILY) {
   int phase=(sObj.clock+i*20)&255,travel=(phase<128?phase:255-phase)/2;
   bool8 supported=!a->z&&a->state!=PS_DEAD&&overlap(m,PX(a->x),PX(a->y),PX(a->x),PX(a->y),15,9);
   if(m->mode)m->y=m->home_y-travel;else m->x=m->home_x+travel;
   if(supported) {a->x+=Q16(m->x-oldx);a->y+=Q16(m->y-oldy);}
  }
  if(t==HO_LIGHT_RAY)m->state=0;
  if(t==HO_LIGHT_RAY&&HO_ABS(PX(a->x)-m->x)<8&&PX(a->y)>m->y&&PX(a->y)<m->y+ray_length(m)) {
   if(gPl.shield_up&&legacy_item_owned(LI_MIRROR_SHIELD)&&a->facing==FACE_N) {
    m->state=1;handoff_objects_tool_box(LE_HIT_REFLECTED,m->x-4,0,m->x+4,m->y);
   }else{m->state=0;if(!a->z)player_hurt(1,DIR_S);}
  }
  if(t==HO_BOSS_DOOR&&!enemies_alive()){m->state=1;m->solid=0;}
  if(t==HO_SWITCH) {
   int pressed=0;if(sObj.field&&m->goal)sObj.goals&=~m->goal;
   if(!a->z&&overlap(m,PX(a->x),PX(a->y),PX(a->x),PX(a->y),10,8))pressed=1;
   for(j=0;j<sObj.count;j++)if(movable(sObjects[j].type)&&HO_ABS(m->x-sObjects[j].x)<8&&HO_ABS(m->y-sObjects[j].y)<8)pressed=1;
   for(j=0;j<legacy_player_clone_count();j++) {
    int cx,cy;if(legacy_clone_position(j,&cx,&cy)&&overlap(m,cx,cy,cx,cy,10,8))pressed=1;
   }
   m->state=pressed;
   if(pressed){flag_goal(m);open_link(m);}
  }
  if(t==HO_TORCH&&m->timer&&!--m->timer)m->state=0;
  if(t==HO_PACCI_POT&&m->timer&&!--m->timer){m->state=0;m->solid=1;}
  if(t==HO_TARGET&&!a->z&&(m->mode!=1||(sObj.goals&sObj.interlock)==sObj.interlock)&&(m->mode!=3||((gHandoffState.fusion_flags&4)&&((PX(a->x)>>4)==(m->x>>4))&&((PX(a->y)>>4)==(m->y>>4))))&&overlap(m,PX(a->x),PX(a->y),PX(a->x),PX(a->y),10,10)) {
   if(!m->state){m->state=1;flag_goal(m);ping(m);
    if(sObj.regional&&!sObj.field&&m->mode==2&&m->link<8){
     u16 bit=1u<<m->link;int site=handoff_current_site();
     if(!(gHandoffState.remaining[site]&bit)){gHandoffState.remaining[site]|=bit;legacy_item_grant(LI_RUPEE20,1);}
    }
   }
  }
  if(t==HO_FAN&&PX(a->y)>=m->y-96&&PX(a->y)<m->y&&HO_ABS(PX(a->x)-m->x)<16)actor_move(a,Q8(.5),DIR_N);
  if(t==HO_WHIRLWIND&&HO_ABS(PX(a->x)-m->x)<12&&HO_ABS(PX(a->y)-m->y)<10&&!a->z&&a->state==PS_NORMAL) {a->state=PS_JUMP;a->zvel=Q16(3.5625);a->dir=DIR_N;a->speed=Q8(1);}
  if(t==HO_STEAM&&(sObj.clock%120)<50&&HO_ABS(PX(a->x)-m->x)<11&&PX(a->y)<m->y&&PX(a->y)>m->y-40)player_hurt(2,DIR_S);
  if(t==HO_BAR||t==HO_CHAIN) {
   int phase=(sObj.clock*2+i*17)&255;
   for(j=1;j<=3;j++) {int x=m->x+(sin_table[phase]*j*8>>14),y=m->y+(sin_table[(phase+64)&255]*j*8>>14);
    if(HO_ABS(PX(a->x)-x)<8&&HO_ABS(PX(a->y)-y+5)<8&&!a->z)player_hurt(t==HO_CHAIN?4:2,DIR_S);
   }
  }
  if(t==HO_TRAP||t==HO_ROTATING_TRAP) {
   if(!m->timer&&HO_ABS(PX(a->x)-m->x)<11&&HO_ABS(PX(a->y)-m->y)<9&&!a->z){m->timer=90;m->state=1;}
   if(m->timer){m->timer--;if(!m->timer)m->state=0;}
   if(m->state&&m->timer<75&&a->state==PS_NORMAL&&HO_ABS(PX(a->x)-m->x)<11&&HO_ABS(PX(a->y)-m->y)<9&&!a->z) {a->state=PS_FALL;a->timer=36;a->sub=0;}
  }
  if(t==HO_BRIDGE) {
   for(j=0;j<sObj.count;j++)if(sObjects[j].type==HO_PULL_LEVER&&sObjects[j].state)m->state=1;
   if(m->state&&!m->timer) {
    int tx,ty,cx=m->home_x/16,cy=m->home_y/16;for(ty=cy-1;ty<=cy+1;ty++)for(tx=cx-1;tx<=cx+1;tx++)room_change(tx,ty,tx==cx-1?MT_LH_MOB_DECK_W:tx==cx+1?MT_LH_MOB_DECK_E:MT_LH_MOB_DECK);
    m->timer=1;
   }
  }
  m->frame=(t*2)+(m->state?1:0);
  if(t==HO_FLOAT||t==HO_LAVA||t==HO_LILY||t==HO_WHIRLWIND||t==HO_STEAM||t==HO_CHAIN||t==HO_FAN)m->frame=t*2+(((sObj.clock/12)+i)&1);
  if(m->last_frame!=m->frame){m->last_frame=m->frame;m->pending=1;}
 }
 /* Pressure gates remain open while their actual plate has weight. */
 for(i=0;i<sObj.count;i++)if(sObjects[i].type==HO_METAL_DOOR&&sObjects[i].mode==2) {
  Mechanism*m=&sObjects[i];bool8 held=m->link<sObj.count&&sObjects[m->link].type==HO_SWITCH&&sObjects[m->link].state;
  if(held||(!m->solid&&overlap(m,PX(a->x)-5,PX(a->y)-8,PX(a->x)+4,PX(a->y),12,8))) {m->state=1;m->solid=0;}
  else {m->state=0;m->solid=1;}
  m->frame=HO_METAL_DOOR*2+m->state;if(m->last_frame!=m->frame){m->last_frame=m->frame;m->pending=1;}
 }
 /* A regional three-verb seal waits for its own flags; generic one-handle
    doors do not accidentally open it. */
 for(i=0;i<sObj.count;i++)if(sObjects[i].type==HO_METAL_DOOR&&sObjects[i].mode==3) {
  if((sObj.goals&7)==7){Mechanism*m=&sObjects[i];m->state=1;m->solid=0;m->frame=HO_METAL_DOOR*2+1;if(m->last_frame!=m->frame){m->last_frame=m->frame;m->pending=1;}}
 }
 /* The cloned formation, actual movable props, and the hero all feed
    the same pressure test. Solving all three plates latches the bonus gate. */
 for(i=0;i<sObj.count;i++)if(sObjects[i].type==HO_METAL_DOOR&&sObjects[i].mode==1) {
  int count=0;for(j=0;j<sObj.count;j++)if(sObjects[j].type==HO_SWITCH&&sObjects[j].state)count++;
  if(count>=3&&!sObjects[i].timer){sObjects[i].timer=1;ping(&sObjects[i]);}
  sObjects[i].state=sObjects[i].timer!=0;sObjects[i].solid=!sObjects[i].state;
  if(sObjects[i].last_frame!=sObjects[i].type*2+sObjects[i].state){sObjects[i].frame=sObjects[i].type*2+sObjects[i].state;sObjects[i].last_frame=sObjects[i].frame;sObjects[i].pending=1;}
 }
 /* A sucked clod occupies the jar rather than becoming permanent loot.
    Releasing the equipped jar launches the existing thrown-object actor. */
 if(sObj.jar_load) {
  u16 keys=player_equip_keys(EQ_GUST_JAR);
  if(!(gKeysHeld&keys)) {Actor* load=thrown_spawn(CARRY_ROCK,PX(a->x),PX(a->y),a->facing);if(load){sObj.jar_load=0;sfx_play(SFX_SPIT);}}
 }
 if(sObj.weather==1&&a->state==PS_NORMAL)actor_move(a,Q8(.25),DIR_E);

}
void handoff_objects_flush_frames(void) {
 int i;const SpriteSheet* sh;
 if(!sObj.active)return;
 sh=&sheets[SHEET_HANDOFF_MECHANISMS];
 for(i=0;i<sObj.count;i++) {Mechanism*m=&sObjects[i];if(m->pending&&m->tile) {
  dma3_copy32(sh->tiles+m->frame*sh->frame_tiles*16,OBJ_TILE(m->tile),sh->frame_tiles*32);m->pending=0;
 }}
}
void handoff_objects_draw(void) {
 int i,j;if(!sObj.active)return;
 for(i=0;i<sObj.count;i++) {
  Mechanism*m=&sObjects[i];if(!m->tile)continue;
  if(m->type==HO_GUST_LOAD&&m->state)continue;
  draw_sprite(m->x-16-gCamX,m->y-28-gCamY,SHEET_HANDOFF_MECHANISMS,m->tile,0,0,m->type>=HO_FLOAT&&m->type<=HO_LILY?3:2,handoff_mechanisms_frame_pal[m->frame]);
  if(m->type==HO_LIGHT_RAY&&sWeatherTile) {
   int end=m->state?ray_receiver_y(m):m->y+ray_length(m);
   int from=m->state?PX(gPlayer->y)-14:m->y;
   int dy=m->state?-8:8;
   for(int yy=from;(dy>0?yy<end:yy>end);yy+=dy)draw_sprite(m->x-4-gCamX,yy-gCamY,SHEET_HANDOFF_WEATHER,sWeatherTile,2,0,2,PAL_OBJ_IRON);
  }
  if(m->type==HO_BAR||m->type==HO_CHAIN) {
   int phase=(sObj.clock*2+i*17)&255;
   for(j=1;j<=3;j++)draw_sprite(m->x+(sin_table[phase]*j*8>>14)-16-gCamX,m->y+(sin_table[(phase+64)&255]*j*8>>14)-28-gCamY,SHEET_HANDOFF_MECHANISMS,m->tile,0,0,2,handoff_mechanisms_frame_pal[m->frame]);
  }
 }

 /* No actor allocation or state mutation in this render pass. */
 if(sObj.weather&&sWeatherTile)for(i=0;i<10;i++) {
  int x=(i*43+sObj.clock*(sObj.weather==2?2:1))%248-8;
  int y=(i*29+sObj.clock*2)%168-8;
  draw_sprite(x,y,SHEET_HANDOFF_WEATHER,sWeatherTile,sObj.weather==2?0:1,0,1,PAL_OBJ_IRON);
 }

}

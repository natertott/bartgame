#!/usr/bin/env python3
"""Execute actual mechanism-course C with explicit host physics/input spies.

No emulator or artwork claims: checks cover course bounds, tool reactions,
exact push distance/cadence, exit reservation, timers and clone occupancy.
"""
import argparse,json,re,subprocess
from pathlib import Path
import handoff_mobility_host as M
GAME=Path(__file__).resolve().parents[1]
def clean(s):return re.sub(r'^\s*#include[^\n]*$','',s,flags=re.M)
def fixture():
 src=(GAME/'src/handoff_objects.c').read_text()
 prefix=M.fixture().split('/* Native traversal annex:')[0]
 # Mobility fixture definitions include many harmless inactive helper spies.
 prefix=prefix.replace('static u16 pixels[4096]','static u16 pixels[65536]')
 for i,name in enumerate(sorted(set(re.findall(r'\bMT_\w+',src)))):
  if not re.search(r'#define '+name+r'\b',prefix):prefix+=f'\n#define {name} {300+i}\n'
 for i,name in enumerate(sorted(set(re.findall(r'\bSFX_\w+',src)))):
  if not re.search(r'#define '+name+r'\b',prefix):prefix+=f'\n#define {name} {30+i}\n'
 prefix+='\n#define LEGACY_ENEMY_BASE 9\n#define FX_SPARK 4\n'
 enemy=(GAME/'src/legacy_enemies.h').read_text()
 prefix+='\n'+re.search(r'enum LegacyEnemyType \{.*?\};',enemy,re.S)[0]
 prefix+='\n'+re.search(r'enum LegacyHitKind \{.*?\};',enemy,re.S)[0]
 prefix+='\n'+clean((GAME/'src/handoff_objects.h').read_text())
 prefix+='''
#define SHEET_HANDOFF_MECHANISMS 0
#define SHEET_HANDOFF_WEATHER 1
#define PAL_OBJ_IRON 4
#define DIR_N 0
#define DIR_E 8
#define DIR_S 16
#define DIR_W 24
#define DIR_NONE 255
#define AK_PLAYER 1
#define AK_OBJECT 6
#define AK_PROJ 3
#define ACTOR_MAX 96
#define PJ_ARROW 3
#define OBJ_THROWN 20
static Actor gActors[ACTOR_MAX];
typedef struct {s8 ox,oy;u8 hw,hh;} Hitbox;
static const Hitbox gHitboxes[16]={{0,0,4,4}};
bool8 player_sword_box(int*a,int*b,int*c,int*d){(void)a;(void)b;(void)c;(void)d;return FALSE;}
bool8 player_lamp_box(int*a,int*b,int*c,int*d){(void)a;(void)b;(void)c;(void)d;return FALSE;}
static const u8 handoff_mechanisms_frame_pal[84]={0};
static s16 sin_table[256];
static int clones,clone_x,clone_y,removed,healed,hurts,next_tile;
static Actor dummy;
bool8 room_box_solid(int x0,int y0,int x1,int y1){(void)x0;(void)y0;(void)x1;(void)y1;return FALSE;}
bool8 textbox_active(void){return FALSE;}
bool8 legacy_item_owned(int item){(void)item;return TRUE;}
void legacy_item_remove(int item){removed=item;}
int legacy_player_clone_count(void){return clones;}
bool8 legacy_clone_position(int i,int*x,int*y){(void)i;*x=clone_x+i*32;*y=clone_y;return clones>0;}
void legacy_surface_set(int x,int y,int kind){(void)x;(void)y;(void)kind;}
Actor* legacy_item_spawn(int i,int x,int y){(void)i;(void)x;(void)y;return &dummy;}
Actor* enemy_spawn(int t,int x,int y){(void)t;(void)x;(void)y;return &dummy;}
Actor* fx_spawn(int t,int x,int y){(void)t;(void)x;(void)y;return &dummy;}
Actor* thrown_spawn(int t,int x,int y,int d){(void)t;(void)x;(void)y;(void)d;return &dummy;}
u16 sprite_alloc(int n){int t=next_tile;next_tile+=n;return t;}
u16 sprite_load_sheet(int n){(void)n;return sprite_alloc(4);}
int facing_to_dir(int d){return d*8;}
void player_set_pos(int x,int y){hero.x=Q16(x);hero.y=Q16(y);}
void player_external_walk_tick(int speed,int d){hero.speed=speed;hero.facing=d/8;}
void player_heal(int d){healed+=d;}
bool8 player_hurt(int d,int dir){(void)dir;hurts+=d;return TRUE;}
bool8 actor_move(Actor*a,int speed,int dir){if(dir==DIR_N)a->y-=speed<<8;if(dir==DIR_E)a->x+=speed<<8;if(dir==DIR_S)a->y+=speed<<8;if(dir==DIR_W)a->x-=speed<<8;return FALSE;}
int enemies_alive(void){return 0;}
u16 player_equip_keys(int eq){return eq==EQ_GUST_JAR?KEY_B:0;}
void dma3_copy32(const void*s,volatile void*d,u32 n){(void)s;(void)d;(void)n;}
'''
 return prefix+clean(src)
MAIN=r'''
static int checks;
#define CHECK(c) do{checks++;if(!(c)){fprintf(stderr,"line%d: %s\n",__LINE__,#c);exit(1);}}while(0)
static void fresh(int variant){memset(&hero,0,sizeof(hero));memset(&gPl,0,sizeof(gPl));memset(ground,0,sizeof(ground));gKeysDown=gKeysHeld=0;clones=hurts=removed=healed=0;next_tile=32;handoff_objects_build(variant<<8);hero.kind=AK_PLAYER;hero.x=Q16(264);hero.y=Q16(332);}
static Mechanism* find(int type){for(int i=0;i<sObj.count;i++)if(sObjects[i].type==type)return &sObjects[i];return NULL;}
int main(void){int i;
 for(i=0;i<4;i++){
  fresh(i);CHECK(sObj.variant==i);CHECK(sObj.count>8&&sObj.count<=24);CHECK(!sObj.complete);
  for(int k=0;k<sObj.count;k++){CHECK(sObjects[k].x>=32&&sObjects[k].x<480);CHECK(sObjects[k].y>=32&&sObjects[k].y<352);CHECK(sObjects[k].type<HO_COUNT);}
 }
 fresh(0);CHECK(!target_free(0,264,360));
 Mechanism*m=find(HO_STATUE);int x=m->x,y=m->y;
 hero.x=Q16(x);hero.y=Q16(y+18);hero.facing=FACE_N;gKeysHeld=KEY_R|KEY_UP;
 CHECK(handoff_objects_pre_player());CHECK(sObj.manip_tick==32);
 for(i=0;i<32;i++)CHECK(handoff_objects_pre_player());
 CHECK(m->x==x&&m->y==y-16);CHECK(PX(hero.y)==y+2);
 fresh(0);m=find(HO_SWITCH);clones=1;clone_x=m->x;clone_y=m->y;handoff_objects_update();CHECK(m->state==1);
 fresh(2);m=find(HO_METAL_DOOR);clones=2;clone_x=11*16+8;clone_y=18*16+12;handoff_objects_update();CHECK(!m->state&&m->solid);clones=3;handoff_objects_update();CHECK(m->state&&!m->solid);clones=0;handoff_objects_update();CHECK(m->state&&!m->solid);
 fresh(3);m=find(HO_BIG_ICE);CHECK(m->solid);handoff_objects_tool_box(LE_HIT_FIRE,m->x-4,m->y-4,m->x+4,m->y+4);CHECK(m->state==1&&!m->solid);
 fresh(3);m=find(HO_BIG_ICE);handoff_objects_tool_box(33,m->x-4,m->y-4,m->x+4,m->y+4);CHECK(m->state==0);handoff_objects_tool_box(34,m->x-4,m->y-4,m->x+4,m->y+4);CHECK(m->state==1);
 fresh(3);m=find(HO_FROZEN_FLOWER);handoff_objects_tool_box(LE_HIT_LANTERN,m->x-4,m->y-4,m->x+4,m->y+4);CHECK(m->state==1&&!m->solid);
 fresh(3);m=find(HO_BARREL_WEB);handoff_objects_tool_box(LE_HIT_GUST_SMALL,m->x-4,m->y-4,m->x+4,m->y+4);CHECK(m->state==1&&!m->solid);
 fresh(3);m=find(HO_PACCI_POT);handoff_objects_tool_box(LE_HIT_PACCI,m->x-4,m->y-4,m->x+4,m->y+4);CHECK(m->state==1&&m->timer==180&&!m->solid);for(i=0;i<180;i++)handoff_objects_update();CHECK(m->state==0&&m->solid);
 fresh(3);m=find(HO_TORCH);handoff_objects_tool_box(LE_HIT_FIRE,m->x-4,m->y-4,m->x+4,m->y+4);CHECK(m->timer==240);for(i=0;i<240;i++)handoff_objects_update();CHECK(m->state==0);
 fresh(2);m=find(HO_PULL_LEVER);hero.x=Q16(m->x);hero.y=Q16(m->y+18);hero.facing=FACE_N;gKeysDown=KEY_R;CHECK(handoff_objects_pre_player());handoff_objects_update();CHECK(ground[11*32+14]==MT_LH_MOB_DECK_W&&ground[13*32+16]==MT_LH_MOB_DECK_E);
 fresh(3);m=find(HO_LIGHT_RAY);hero.x=Q16(m->x);hero.y=Q16(m->y+32);hero.facing=FACE_N;gPl.shield_up=1;handoff_objects_update();CHECK(m->state==1&&find(HO_LIGHT_RECEIVER)->state==1&&hurts==0);
 fresh(3);m=find(HO_LIGHT_RAY);hero.x=Q16(m->x);hero.y=Q16(m->y+32);handoff_objects_update();CHECK(hurts==1);
 handoff_objects_reset();CHECK(!handoff_objects_box_solid(0,0,500,500));CHECK(!handoff_objects_support(100,100));CHECK(handoff_objects_variant()==-1);
 printf("{\"checks\":%d,\"object_kinds\":%d,\"result\":\"pass\"}\n",checks,HO_COUNT);return 0;
}
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 c=out/'objects-host.c';c.write_text(fixture()+MAIN);exe=out/'objects-host'
 r=subprocess.run(['cc','-std=gnu11','-O2',str(c),'-o',str(exe)],capture_output=True,text=True);(out/'compile.log').write_text(r.stdout+r.stderr);r.check_returncode()
 r=subprocess.run([str(exe)],capture_output=True,text=True);(out/'run.log').write_text(r.stdout+r.stderr);r.check_returncode();(out/'report.json').write_text(r.stdout);print(r.stdout,end='')
if __name__=='__main__':main()

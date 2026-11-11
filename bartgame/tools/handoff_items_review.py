#!/usr/bin/env python3
"""Run actual bomb_throw.c against a deterministic host room fixture.

This checks simulation, not rendering or GBA timing. No replacement bomb
algorithm exists in the fixture: it stubs allocation, walls, input and blast.
"""
import json
from pathlib import Path
import re
import subprocess
import tempfile

GAME=Path(__file__).resolve().parents[1]
def strip_includes(text):return re.sub(r'^\s*#include[^\n]*$', '', text, flags=re.M)

def main():
    actor=strip_includes((GAME/'src/actor.h').read_text())
    player=strip_includes((GAME/'src/player.h').read_text())
    source=strip_includes((GAME/'src/bomb_throw.c').read_text())
    defs='''#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
typedef uint8_t u8;typedef uint16_t u16;typedef uint32_t u32;
typedef int8_t s8;typedef int16_t s16;typedef int32_t s32;typedef u8 bool8;
#define TRUE 1
#define FALSE 0
#define Q16(x) ((s32)((x)*65536))
#define Q8(x) ((s32)((x)*256))
#define PX(x) ((x)>>16)
#define MIN(a,b) ((a)<(b)?(a):(b))
#define MAX(a,b) ((a)>(b)?(a):(b))
#define CLAMP(x,a,b) MIN(MAX(x,a),b)
#define ABS(x) ((x)<0?-(x):(x))
#define IWRAM_CODE
#define SHEET_HERO_TILES 16
#define SHEET_HERO_FRAMES 1
#define SHEET_SWORD_TILES 16
#define SHEET_SHIELD_TILES 4
#define SHEET_SHIELD_FRAMES 1
#define SHEET_ITEMS 0
#define F_ITEMS_BOMBS 0
#define F_ITEMS_BOMB_LIT 1
#define KEY_A 1
#define KEY_B 2
#define KEY_L 512
#define KEY_START 8
#define SFX_BOMB_SET 1
#define OBJ_IMPACT_BOMB 21
#define EQ_REMOTE_BOMBS 8
'''
    stub='''
Actor gActors[ACTOR_MAX];Actor* gPlayer=&gActors[0];PlayerState gPl;
u16 gKeysDown,gKeysHeld;u32 gFrame;int gCamX,gCamY;
const u8 items_frame_pal[]={0,0};
static int blast_count,blast_x,blast_y,wall_x;
int bombs_live(void){int i,n=0;for(i=1;i<ACTOR_MAX;i++)n+=gActors[i].kind==AK_OBJECT&&gActors[i].type==21;return n;}
Actor* actor_new(u8 kind,u8 type,int x,int y){int i;for(i=1;i<ACTOR_MAX;i++)if(!gActors[i].kind){Actor*a=&gActors[i];memset(a,0,sizeof(*a));a->kind=kind;a->type=type;a->x=Q16(x);a->y=Q16(y);return a;}return NULL;}
int facing_to_dir(int f){return f*8;}
void actor_free(Actor*a){a->kind=0;}
void actor_set_sheet(Actor*a,int sheet,u16 tile){a->sheet=sheet;a->tile=tile;}
u16 items_sheet_tile(void){return 1;}
void sfx_play(int n){(void)n;}
void actor_draw(Actor*a){(void)a;}
int room_px_w(void){return 512;}
int room_px_h(void){return 384;}
bool8 room_solid_px(int x,int y){(void)y;return x>=wall_x;}
void objects_blast(int x,int y){blast_count++;blast_x=x;blast_y=y;}
u16 player_equip_keys(int eq){u16 b=0;for(int i=0;i<3;i++)if(gPl.equip[i]==eq)b|=i==0?KEY_A:i==1?KEY_B:KEY_L;return b;}
void player_item_pose(int eq){(void)eq;}
void draw_sprite(int x,int y,int sh,u16 ti,int fr,int hf,int pr,int pa){(void)x;(void)y;(void)sh;(void)ti;(void)fr;(void)hf;(void)pr;(void)pa;}
'''
    test='''
static int checks;
#define CHECK(cond) do{checks++;if(!(cond)){fprintf(stderr,"FAIL:%d %s\\n",__LINE__,#cond);exit(1);}}while(0)
static void reset(void){memset(gActors,0,sizeof(gActors));memset(&gPl,0,sizeof(gPl));gPlayer=&gActors[0];gPlayer->kind=AK_PLAYER;gPlayer->x=Q16(80);gPlayer->y=Q16(80);gPlayer->facing=FACE_E;gPl.bombs=9;gPl.equip[0]=EQ_BOMBS;wall_x=512;blast_count=0;gKeysHeld=gKeysDown=0;bomb_charge_cancel();}
static void flight(Actor*a){int n=0;while(a->kind&&a->state==0&&n++<80)bomb_throw_update(a);CHECK(n<80);}
static void hold_release(int ticks,u16 key){gKeysHeld=gKeysDown=key;bomb_charge_update();gKeysDown=0;for(int i=1;i<ticks;i++)bomb_charge_update();gKeysHeld=0;bomb_charge_update();}
int main(void){
 int i;reset();CHECK(bomb_throw_range(1)==0);CHECK(bomb_throw_range(3)==0);CHECK(bomb_throw_range(30)==24);CHECK(bomb_throw_range(60)==32);CHECK(bomb_throw_range(200)==32);
 for(i=1;i<=90;i++)CHECK(bomb_throw_range(i)>=bomb_throw_range(i-1));
 for(int face=0;face<4;face++)for(int ticks=1;ticks<=120;ticks+=29){
  reset();gPlayer->facing=face;hold_release(ticks,KEY_A);CHECK(gPl.bombs==8);CHECK(bombs_live()==1);Actor*a=&gActors[1];int range=bomb_throw_range(ticks);flight(a);CHECK(blast_count==1);CHECK(!bombs_live());CHECK(blast_x==80+(face==FACE_E?range:face==FACE_W?-range:0));CHECK(blast_y==80+(face==FACE_S?range:face==FACE_N?-range:0));
 }
 reset();wall_x=94;hold_release(60,KEY_A);flight(&gActors[1]);CHECK(blast_x==93);CHECK(blast_count==1);
 reset();hold_release(120,KEY_A);CHECK(gBombChargeTicks==0);CHECK(gPl.bombs==8);flight(&gActors[1]);CHECK(blast_x==112);
 reset();gKeysHeld=gKeysDown=KEY_A;bomb_charge_update();gKeysDown=0;for(i=0;i<200;i++)bomb_charge_update();CHECK(gBombChargeTicks==60);CHECK(gPl.bombs==9);CHECK(!bombs_live());gPlayer->state=PS_HURT;bomb_charge_update();CHECK(!gBombChargeKey);CHECK(gPl.bombs==9);
 reset();gPl.equip[0]=0;gPl.equip[2]=EQ_BOMBS;hold_release(30,KEY_L);CHECK(gPl.bombs==8);flight(&gActors[1]);CHECK(blast_x==104);
 reset();gPl.bombs=0;hold_release(30,KEY_A);CHECK(!bombs_live());CHECK(!gBombChargeKey);
 reset();bomb_throw_spawn(80,80,FACE_E,32);bomb_throw_spawn(80,80,FACE_E,32);hold_release(30,KEY_A);CHECK(bombs_live()==2);CHECK(gPl.bombs==9);
 reset();gPl.equip[0]=EQ_REMOTE_BOMBS;hold_release(30,KEY_A);flight(&gActors[1]);CHECK(blast_count==0);CHECK(bomb_throw_remote_count()==1);gPl.bombs=0;gPl.item_cooldown=0;gKeysHeld=gKeysDown=KEY_A;bomb_charge_update();CHECK(blast_count==1);CHECK(!bomb_throw_remote_count());
 printf("{\\"checks\\":%d,\\"result\\":\\"pass\\",\\"algorithm\\":\\"actual bomb_throw.c\\"}\\n",checks);return 0;
}
'''
    with tempfile.TemporaryDirectory(prefix='bart-handoff-items-') as tmp:
        path=Path(tmp);c=path/'review.c';exe=path/'review';c.write_text(defs+actor+player+stub+source+test)
        subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(c),'-o',str(exe)],check=True)
        result=subprocess.check_output([str(exe)],text=True);print(result,end='')
if __name__=='__main__':main()

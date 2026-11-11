/* Charge at native simulation cadence, release once, land once. All blast
   mechanics stay in objects_blast so thrown/remote/enemy bombs share damage,
   terrain reactions and presentation rather than maintaining parallel rules. */
#include "bomb_throw.h"
#include "player.h"
#include "objects.h"
#include "room.h"
#include "video.h"
#include "sound.h"
#include "legacy_items.h"

extern void objects_blast(int px,int py);
u8 gBombChargeTicks;
u16 gBombChargeKey;
static u8 sRemoteCharge;

int bomb_throw_range(int held_ticks) {
    int t=CLAMP(held_ticks,0,60);
    /* A tap is a drop. The deliberate nonlinear response gives exactly
       24px at half a second and32px at the one-second cap. */
    if(t<=3)return 0;
    return t<=30 ? (t*24+15)/30 : 24+((t-30)*8+15)/30;
}

void bomb_charge_cancel(void) {
    gBombChargeTicks=0;gBombChargeKey=0;sRemoteCharge=0;
}

static Actor* spawn(int px,int py,int facing,int range,bool8 remote) {
    Actor* a;
    if(bombs_live()>=2)return NULL;
    a=actor_new(AK_OBJECT,OBJ_IMPACT_BOMB,px,py);
    if(!a)return NULL;
    actor_set_sheet(a,SHEET_ITEMS,items_sheet_tile());
    a->frame=F_ITEMS_BOMBS;a->pal=items_frame_pal[F_ITEMS_BOMBS];
    a->dir=facing_to_dir(facing);a->facing=facing;
    a->flags=AF_FLYING|AF_NOSHADOW;a->hitbox=HB_SMALL;a->prio=2;
    a->z=Q16(16);a->vx=px;a->vy=py;
    a->v[0]=12+CLAMP(range,0,32)/4;a->v[1]=CLAMP(range,0,32);
    a->v[4]=remote;a->timer=0;
    sfx_play(SFX_BOMB_SET);
    return a;
}
Actor* bomb_throw_spawn(int px,int py,int facing,int range) {return spawn(px,py,facing,range,FALSE);}
Actor* bomb_throw_remote_spawn(int px,int py,int facing,int range) {return spawn(px,py,facing,range,TRUE);}

static void impact(Actor* a) {
    a->z=0;
    if(a->v[4]) {a->state=1;a->flags=0;return;}
    /* Retire first: the shared blast may allocate effects or kill an actor. */
    int px=PX(a->x),py=PX(a->y);
    actor_free(a);objects_blast(px,py);
}

void bomb_throw_update(Actor* a) {
    if(a->state==1) {
        a->frame=(gFrame&16)?F_ITEMS_BOMB_LIT:F_ITEMS_BOMBS;
        a->pal=items_frame_pal[a->frame];return;
    }
    int n=a->v[0],t=++a->timer,r=a->v[1],dx=0,dy=0;
    int x,y,oldx=PX(a->x),oldy=PX(a->y);
    if(t>n)t=n;
    if(a->facing==FACE_N)dy=-r;
    else if(a->facing==FACE_E)dx=r;
    else if(a->facing==FACE_S)dy=r;
    else dx=-r;
    x=a->vx+dx*t/n;y=a->vy+dy*t/n;
    /* Sample every travelled pixel: the maximum velocity is<2px/tick,
       nevertheless this preserves correct contact next to thin collision. */
    int steps=MAX(ABS(x-oldx),ABS(y-oldy)),i,startx=oldx,starty=oldy;
    for(i=1;i<=steps;i++) {
        int sx=startx+(x-startx)*i/steps,sy=starty+(y-starty)*i/steps;
        if(sx<8||sy<8||sx>=room_px_w()-8||sy>=room_px_h()-8||room_solid_px(sx,sy-4)) {
            a->x=Q16(oldx);a->y=Q16(oldy);impact(a);return;
        }
        oldx=sx;oldy=sy;
    }
    a->x=Q16(x);a->y=Q16(y);
    /* A hand-height start, compact parabolic rise, then an exact floor end. */
    a->z=(s32)(((n-t)*16*65536)/n)+
         (s32)((4*t*(n-t)*12*65536)/(n*n));
    if(t>=n)impact(a);
}

void bomb_throw_draw(Actor* a) {actor_draw(a);}
int bomb_throw_remote_count(void) {
    int i,n=0;
    for(i=1;i<ACTOR_MAX;i++)if(gActors[i].kind==AK_OBJECT&&gActors[i].type==OBJ_IMPACT_BOMB&&gActors[i].v[4])n++;
    return n;
}
void bomb_throw_remote_detonate(void) {
    int i;
    for(i=1;i<ACTOR_MAX;i++) {
        Actor* a=&gActors[i];
        if(a->kind==AK_OBJECT&&a->type==OBJ_IMPACT_BOMB&&a->v[4]) {
            int px=PX(a->x),py=PX(a->y);actor_free(a);objects_blast(px,py);
        }
    }
}

void bomb_charge_update(void) {
    Actor* p=gPlayer;
    u16 keys=player_equip_keys(EQ_BOMBS),remote=player_equip_keys(EQ_REMOTE_BOMBS);
    if(p->state!=PS_NORMAL || (gKeysDown&KEY_START)) {bomb_charge_cancel();return;}
    if(!gBombChargeKey) {
        u16 pressed=gKeysDown&(keys|remote);
        if(!pressed || gPl.item_cooldown)return;
        /* One physical initiating button owns this throw, even if equipment
           changes or another assigned key is subsequently pressed. */
        gBombChargeKey=pressed&-pressed;sRemoteCharge=(remote&gBombChargeKey)!=0;
        if(sRemoteCharge && bomb_throw_remote_count()) {
            bomb_throw_remote_detonate();bomb_charge_cancel();gPl.item_cooldown=12;return;
        }
        if(!gPl.bombs || bombs_live()>=2) {bomb_charge_cancel();return;}
        gBombChargeTicks=1;player_item_pose(EQ_BOMBS);
    } else if(!(gKeysHeld&gBombChargeKey)) {
        int range=bomb_throw_range(gBombChargeTicks);
        Actor* a=sRemoteCharge ? bomb_throw_remote_spawn(PX(p->x),PX(p->y),p->facing,range) :
                                 bomb_throw_spawn(PX(p->x),PX(p->y),p->facing,range);
        if(a) {gPl.bombs--;gPl.item_cooldown=12;player_item_pose(EQ_BOMBS);}
        bomb_charge_cancel();
    } else if(gBombChargeTicks<60)gBombChargeTicks++;
}

void bomb_charge_draw(bool8 behind) {
    static const s8 hand[4][2]={{5,-19},{10,-11},{3,-8},{-10,-11}};
    int f=gPlayer->facing;
    if(!gBombChargeKey || gPlayer->state!=PS_NORMAL || behind!=(f==FACE_N))return;
    draw_sprite(PX(gPlayer->x)+hand[f][0]-8-gCamX,
                PX(gPlayer->y)+hand[f][1]-8-gCamY,SHEET_ITEMS,items_sheet_tile(),
                F_ITEMS_BOMBS,0,gPlayer->prio,items_frame_pal[F_ITEMS_BOMBS]);
}

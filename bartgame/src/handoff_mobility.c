/* Native traversal annex: a rideable closed rail, steerable parachute shelf,
   and two crossing collision planes. Nothing here changes the Forest/Drain. */
#include "handoff_mobility.h"
#include "handoff_events.h"
#include "legacy_items.h"
#include "game.h"
#include "room.h"
#include "player.h"
#include "actor.h"
#include "video.h"
#include "text.h"
#include "sound.h"
#include "util.h"
#include "world_tokens.h"

u8 gMobilityMode,gMobilityLayer,gMobilityCartPoint;
s16 gMobilityCartX,gMobilityCartY;
static u16 sCartTile,sChuteTile;
static u8 sCartFrame,sChuteFrame,sExitCart,sFastDrop,sPadCooldown;
static s32 sCartX,sCartY;
static const u8 sRail[4][2]={{4,20},{11,20},{11,17},{4,17}};
static bool8 active(void) {return gGame.area==AREA_HANDOFF&&handoff_current_kind()==HS_TRAVERSAL;}
bool8 handoff_mobility_busy(void) {return active()&&gMobilityMode!=HMOB_WALK;}
static bool8 inside(int px,int py,int x0,int y0,int x1,int y1) {return px>=x0&&px<=x1&&py>=y0&&py<=y1;}
static int tile_x(int tx) {return tx*16+8;}
static int tile_y(int ty) {return ty*16+14;}
static bool8 near(int px,int py,int radius) {return ABS(PX(gPlayer->x)-px)<=radius&&ABS(PX(gPlayer->y)-py)<=radius;}
static void rect(int x0,int y0,int x1,int y1,u16 mt) {int x,y;for(y=y0;y<=y1;y++)for(x=x0;x<=x1;x++)room_set(x,y,mt);}
static bool8 red_fusion(void) {WorldTokenNeed n=world_tokens_empty();n.fusions=4;return world_tokens_meet(&n);}
static bool8 prize_taken(void) {return (gHandoffState.completed[HS_TRAVERSAL>>3]>>(HS_TRAVERSAL&7))&1;}
static void clear_control(void) {
    gPl.input_lock=0;gPl.sword_active=0;gPl.shield_up=0;
    gPlayer->state=PS_NORMAL;gPlayer->z=gPlayer->zvel=0;gPlayer->speed=0;
}
void handoff_mobility_build(u32 seed) {
    int x,y;
    (void)seed;
    gMobilityMode=HMOB_WALK;gMobilityLayer=0;gMobilityCartPoint=0;
    sCartTile=sChuteTile=0;sCartFrame=sChuteFrame=255;
    sExitCart=sFastDrop=0;sPadCooldown=15;
    sCartX=Q16(tile_x(sRail[0][0]));sCartY=Q16(tile_y(sRail[0][1]));
    gMobilityCartX=PX(sCartX);gMobilityCartY=PX(sCartY);
    /* Three spatial lessons: a visibly tall western face, a central bridge
       crossing a lower horizontal bank, and the optional red-fusion shelf. */
    rect(3,4,9,6,MT_CAVE_FLOOR0);
    rect(3,7,8,10,MT_LH_MOB_CLIFF);
    for(x=3;x<=8;x++)room_set(x,6,MT_LH_MOB_LAUNCH);
    rect(9,9,20,18,MT_LH_MOB_WATER);
    rect(7,13,23,15,MT_CAVE_FLOOR0);
    /* North/south ramps enter the upper plane. East/west remains a separate
       lower corridor at the exact same map coordinates. */
    for(y=7;y<=20;y++)for(x=14;x<=16;x++) {
        if(y==7||y==20)room_set(x,y,MT_LH_MOB_RAMP);
        else room_set_overlay(x,y,x==14?MT_LH_MOB_DECK_W:x==16?MT_LH_MOB_DECK_E:MT_LH_MOB_DECK);
    }
    for(x=4;x<=11;x++) {
        room_set(x,17,MT_LH_MOB_RAIL_H);room_set(x,20,MT_LH_MOB_RAIL_H);
    }
    for(y=17;y<=20;y++) {room_set(4,y,MT_LH_MOB_RAIL_V);room_set(11,y,MT_LH_MOB_RAIL_V);}
    room_set(4,20,MT_LH_MOB_STOP);room_set(11,17,MT_LH_MOB_STOP);
    room_set(4,17,MT_LH_MOB_RAIL_SE);room_set(11,20,MT_LH_MOB_RAIL_NW);
    /* A red fusion changes the actual floor and collision over a broad gap.
       The island and reward remain optional; the base course always exits. */
    rect(23,4,28,11,MT_LH_MOB_PIT);
    rect(24,4,27,7,MT_CAVE_FLOOR0);
    for(y=8;y<=11;y++)for(x=25;x<=26;x++)
        room_set(x,y,red_fusion()?MT_LH_MOB_RAMP:MT_LH_MOB_PIT);
    room_set(26,6,prize_taken()?MT_LH_MOB_OPEN:MT_LH_MOB_PRIZE);
    room_set(27,12,MT_LH_MOB_SOCKET);
    room_set(5,12,MT_LH_MOB_SIGN);
    room_set(18,20,MT_LH_MOB_SIGN);
    room_build_solid();
}
bool8 handoff_mobility_handles_floor(int px,int py) {
    return active()&&gMobilityLayer==1&&inside(px,py,14*16,7*16,17*16-1,21*16-1);
}
int handoff_mobility_priority(int original) {
    return active()&&gMobilityLayer==1?1:original;
}
bool8 handoff_mobility_box_solid(int x0,int y0,int x1,int y1) {
    if(!active())return FALSE;
    /* Elevated feet cannot step through either rail or fall sideways onto
       the lower path; only the two end ramps connect these planes. */
    if(gMobilityLayer==1 && (x0<14*16+3||x1>17*16-4))return TRUE;
    if(gMobilityMode!=HMOB_PARACHUTE && gMobilityLayer==0 &&
       x1>=3*16&&x0<9*16&&y1>=7*16&&y0<11*16)return TRUE;
    return FALSE;
}
static void manual_timers(void) {
    gPl.input_lock=1;
    if(gPlayer->iframes)gPlayer->iframes--;
    if(gPl.item_cooldown)gPl.item_cooldown--;
    gPl.sword_active=gPl.shield_up=0;
}
static void cart_exit(void) {
    gMobilityMode=HMOB_WALK;clear_control();
    gPlayer->x=sCartX-(gMobilityCartPoint==2?Q16(16):0);
    gPlayer->y=sCartY+(gMobilityCartPoint==2?0:Q16(11));gPlayer->facing=FACE_S;
    gPl.safe_x=PX(gPlayer->x);gPl.safe_y=PX(gPlayer->y);sPadCooldown=20;
    sfx_play(SFX_BUMP);
}
static void cart_tick(void) {
    int target=(gMobilityCartPoint+1)&3;
    s32 tx=Q16(tile_x(sRail[target][0])),ty=Q16(tile_y(sRail[target][1]));
    int direction=tx>sCartX?FACE_E:tx<sCartX?FACE_W:ty>sCartY?FACE_S:FACE_N;
    if(gKeysDown&KEY_A){sExitCart=1;gKeysDown&=~KEY_A;}
    if(sCartX<tx)sCartX=MIN(tx,sCartX+Q16(1.5));
    if(sCartX>tx)sCartX=MAX(tx,sCartX-Q16(1.5));
    if(sCartY<ty)sCartY=MIN(ty,sCartY+Q16(1.5));
    if(sCartY>ty)sCartY=MAX(ty,sCartY-Q16(1.5));
    gMobilityCartX=PX(sCartX);gMobilityCartY=PX(sCartY);
    gPlayer->x=sCartX;gPlayer->y=sCartY-Q16(5);gPlayer->facing=direction;
    gPlayer->state=PS_NORMAL;gPlayer->speed=0;gPlayer->z=0;
    if(sCartX==tx&&sCartY==ty) {
        gMobilityCartPoint=target;
        if(sExitCart && !(target&1)){sExitCart=0;cart_exit();}
    }
}
static void parachute_tick(void) {
    Actor* a=gPlayer;
    int side=(gKeysHeld&KEY_RIGHT?1:0)-(gKeysHeld&KEY_LEFT?1:0);
    s32 landing=Q16(tile_y(11));
    s32 speed=sFastDrop?Q16(2):(gKeysHeld&KEY_UP)?Q16(.5):(gKeysHeld&KEY_DOWN)?Q16(1):Q16(.75);
    if(gKeysDown&KEY_A){sFastDrop=1;gKeysDown&=~KEY_A;}
    a->x=CLAMP(a->x+side*Q16(.75),Q16(tile_x(3)),Q16(tile_x(8)));
    a->y=MIN(landing,a->y+speed);a->z=MIN(Q16(12),(landing-a->y)/2);
    a->state=PS_JUMP;a->facing=FACE_S;a->speed=0;a->zvel=0;
    if(a->y==landing) {
        gMobilityMode=HMOB_WALK;clear_control();a->iframes=20;sPadCooldown=20;
        gPl.safe_x=PX(a->x);gPl.safe_y=PX(a->y);sfx_play(SFX_BUMP);
    }
}
bool8 handoff_mobility_pre_player(void) {
    if(!active())return FALSE;
    if(gMobilityMode!=HMOB_WALK &&
       ((gMobilityMode==HMOB_CART&&gPlayer->state!=PS_NORMAL)||
        (gMobilityMode==HMOB_PARACHUTE&&gPlayer->state!=PS_JUMP))) {
        int old_mode=gMobilityMode;
        gMobilityMode=HMOB_WALK;gPl.input_lock=0;
        /* A hurt body must keep its hurt/warp/death state. A parachute hit
           resolves onto its guaranteed dry landing before hurt recovery,
           rather than leaving a standing body inside the cliff collision. */
        if(old_mode==HMOB_PARACHUTE&&gPlayer->state==PS_HURT) {
            gPlayer->x=CLAMP(gPlayer->x,Q16(tile_x(3)),Q16(tile_x(8)));
            gPlayer->y=Q16(tile_y(11));gPlayer->z=gPlayer->zvel=0;
            gPl.safe_x=PX(gPlayer->x);gPl.safe_y=PX(gPlayer->y);
        }
        return FALSE;
    }
    if(gPlayer->state==PS_DEAD)return FALSE;
    if(sPadCooldown)sPadCooldown--;
    if(gMobilityMode==HMOB_CART||gMobilityMode==HMOB_PARACHUTE) {
        manual_timers();
        if(gMobilityMode==HMOB_CART)cart_tick();else parachute_tick();
        /* Items are unavailable while the vehicle owns movement. Handle A
           as exit/fold first, then suppress equipment/lift inputs this tick. */
        gKeysDown&=~(KEY_A|KEY_B|KEY_L|KEY_R);
        gKeysHeld&=~(KEY_A|KEY_B|KEY_L|KEY_R);
        return TRUE;
    }
    if(!sPadCooldown && (gKeysDown&KEY_R) && gPlayer->state==PS_NORMAL &&
       inside(PX(gPlayer->x),PX(gPlayer->y),3*16,6*16,9*16-1,7*16+4)) {
        gMobilityMode=HMOB_PARACHUTE;sFastDrop=0;gPl.input_lock=1;
        gPlayer->state=PS_JUMP;gPlayer->z=Q16(12);gPlayer->zvel=0;
        gKeysDown&=~KEY_R;sfx_play(SFX_JUMP);return TRUE;
    }
    return FALSE;
}
void handoff_mobility_update(void) {
    int px,py;
    if(!active()||gMobilityMode!=HMOB_WALK)return;
    px=PX(gPlayer->x);py=PX(gPlayer->y)-4;
    if(!gMobilityLayer && inside(px,py,14*16+4,7*16,17*16-5,8*16-1))gMobilityLayer=1;
    if(!gMobilityLayer && inside(px,py,14*16+4,20*16,17*16-5,21*16-1))gMobilityLayer=1;
    if(gMobilityLayer && (py<7*16||py>=21*16))gMobilityLayer=0;
}
bool8 handoff_mobility_interact(void) {
    if(!active()||gMobilityMode!=HMOB_WALK||gPlayer->state!=PS_NORMAL)return FALSE;
    if(!sPadCooldown && near(gMobilityCartX,gMobilityCartY+9,20)) {
        gMobilityMode=HMOB_CART;gMobilityLayer=0;sExitCart=0;gPl.input_lock=1;
        gPlayer->x=sCartX;gPlayer->y=sCartY-Q16(5);gPl.sword_active=gPl.shield_up=0;
        gKeysDown&=~KEY_A;sfx_play(SFX_MENU);return TRUE;
    }
    if(near(tile_x(26),tile_y(6),18)) {
        if(!red_fusion()){textbox_open("A red fusion joins the broken shelf to this cache.");return TRUE;}
        if(!prize_taken()) {
            gHandoffState.completed[HS_TRAVERSAL>>3]|=1u<<(HS_TRAVERSAL&7);
            legacy_item_grant(LI_RUPEE100,1);room_change(26,6,MT_LH_MOB_OPEN);
            handoff_notify(HN_EVENT,AREA_HANDOFF,HS_TRAVERSAL,LI_RUPEE100);sfx_play(SFX_CHEST);
            textbox_open("The red fusion raised a real bridge. This cache holds one hundred gilt.");
        }else textbox_open("The shelf remembers your red fusion. Its cache is empty.");
        return TRUE;
    }
    if(near(tile_x(5),tile_y(12),20)||near(tile_x(18),tile_y(20),20)) {
        textbox_open("Cart: A boards; A again leaves at the next round stop.|Bridge: enter either end ramp to cross above; walk across the middle bank to pass below.|Shelf: stand on its arrow and press R. Steer left/right; A folds the parachute for a quicker descent.");
        return TRUE;
    }
    return FALSE;
}
static void stream(int frame,u16* tile,u8* old) {
    const SpriteSheet* sh=&sheets[SHEET_HANDOFF_MOBILITY];
    if(!*tile){*tile=sprite_load_frame(SHEET_HANDOFF_MOBILITY,frame);*old=frame;}
    else if(*old!=frame) {vram_queue(sh->tiles+frame*sh->frame_tiles*16,OBJ_TILE(*tile),sh->frame_tiles*32);*old=frame;}
}
void handoff_mobility_draw(void) {
    int target,face,frame;
    if(!active())return;
    target=(gMobilityCartPoint+1)&3;
    face=tile_x(sRail[target][0])>gMobilityCartX?FACE_E:tile_x(sRail[target][0])<gMobilityCartX?FACE_W:tile_y(sRail[target][1])>gMobilityCartY?FACE_S:FACE_N;
    frame=face*2+(gMobilityMode==HMOB_CART?((gFrame>>3)&1):0);stream(frame,&sCartTile,&sCartFrame);
    if(sCartTile)draw_sprite(gMobilityCartX-16-gCamX,gMobilityCartY-26-gCamY,SHEET_HANDOFF_MOBILITY,sCartTile,0,0,1,sheets[SHEET_HANDOFF_MOBILITY].pal);
    if(gMobilityMode==HMOB_PARACHUTE) {
        frame=8+((gFrame>>4)&1);stream(frame,&sChuteTile,&sChuteFrame);
        if(sChuteTile)draw_sprite(PX(gPlayer->x)-16-gCamX,PX(gPlayer->y)-PX(gPlayer->z)-45-gCamY,SHEET_HANDOFF_MOBILITY,sChuteTile,0,0,0,sheets[SHEET_HANDOFF_MOBILITY].pal);
    }
}

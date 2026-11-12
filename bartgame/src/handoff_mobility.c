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
#include "regional_content.h"

u8 gMobilityMode,gMobilityLayer,gMobilityCartPoint;
s16 gMobilityCartX,gMobilityCartY;
static u16 sCartTile,sChuteTile;
static u8 sCartFrame,sChuteFrame,sExitCart,sFastDrop,sPadCooldown;
static s32 sCartX,sCartY;
static u8 sRail[4][2]={{4,20},{11,20},{11,17},{4,17}};
static struct {
 u8 active,regional,field,pattern,area,cell,site,cart,bridge,chute,prize;
 u8 bx0,bx1,by0,by1,cx0,cx1,cy0,cy1,launch,landing,px,py,signx,signy;
 u8 cart_done,bridge_from,bridge_done,chute_done,under_done,under_from,underx,undery;
} sMob EWRAM_BSS;
static bool8 active(void) {return sMob.active&&gGame.area==sMob.area&&gGame.cell==sMob.cell;}
bool8 handoff_mobility_busy(void) {return active()&&gMobilityMode!=HMOB_WALK;}
static bool8 inside(int px,int py,int x0,int y0,int x1,int y1) {return px>=x0&&px<=x1&&py>=y0&&py<=y1;}
static int tile_x(int tx) {return tx*16+8;}
static int tile_y(int ty) {return ty*16+14;}
static bool8 near(int px,int py,int radius) {return ABS(PX(gPlayer->x)-px)<=radius&&ABS(PX(gPlayer->y)-py)<=radius;}
static void rect(int x0,int y0,int x1,int y1,u16 mt) {int x,y;for(y=y0;y<=y1;y++)for(x=x0;x<=x1;x++)room_set(x,y,mt);}
static bool8 red_fusion(void) {WorldTokenNeed n=world_tokens_empty();n.fusions=4;return world_tokens_meet(&n);}
static bool8 prize_taken(void) {return sMob.field?!!(gHandoffState.remaining[sMob.site]&0x4000):(gHandoffState.completed[sMob.site>>3]>>(sMob.site&7))&1;}
void handoff_mobility_reset(void) {memset(&sMob,0,sizeof(sMob));gMobilityMode=HMOB_WALK;gMobilityLayer=0;}
static void activate(u8 regional,u8 field,u8 pattern,u8 site) {
 handoff_mobility_reset();sMob.active=1;sMob.regional=regional;sMob.field=field;sMob.pattern=pattern;sMob.site=site;
 sMob.area=gGame.area;sMob.cell=gGame.cell;
 sCartTile=sChuteTile=0;sCartFrame=sChuteFrame=255;sExitCart=sFastDrop=0;sPadCooldown=15;
}
static void cart_position(void) {gMobilityCartPoint=0;sCartX=Q16(tile_x(sRail[0][0]));sCartY=Q16(tile_y(sRail[0][1]));gMobilityCartX=PX(sCartX);gMobilityCartY=PX(sCartY);}
static bool8 route_done(void) {return !sMob.regional||(sMob.pattern==0?sMob.cart_done:sMob.pattern==1?sMob.bridge_done:sMob.chute_done);}

static void clear_control(void) {
    gPl.input_lock=0;gPl.sword_active=0;gPl.shield_up=0;
    gPlayer->state=PS_NORMAL;gPlayer->z=gPlayer->zvel=0;gPlayer->speed=0;
}
void handoff_mobility_build(u32 seed) {
    int x,y;
    (void)seed;
    activate(0,0,255,HS_TRAVERSAL);
    sMob.cart=sMob.bridge=sMob.chute=sMob.prize=1;
    sMob.bx0=14;sMob.bx1=16;sMob.by0=7;sMob.by1=20;
    sMob.cx0=3;sMob.cx1=8;sMob.cy0=7;sMob.cy1=10;sMob.launch=6;sMob.landing=11;
    sMob.px=26;sMob.py=6;sMob.signx=5;sMob.signy=12;
    sRail[0][0]=4;sRail[0][1]=20;sRail[1][0]=11;sRail[1][1]=20;sRail[2][0]=11;sRail[2][1]=17;sRail[3][0]=4;sRail[3][1]=17;
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
/* The same verbs are placed as local routes, not a collection of stations. */
static void rail_at(int x,int y,int shape) {
 bool8 wet=room_type(x,y)==TT_WATER;
 static const u16 dry[]={MT_LH_MOB_RAIL_H,MT_LH_MOB_RAIL_V,MT_LH_MOB_RAIL_SE,MT_LH_MOB_RAIL_NW,MT_LH_MOB_STOP};
 static const u16 water[]={MT_LH_MOB_WET_H,MT_LH_MOB_WET_V,MT_LH_MOB_WET_SE,MT_LH_MOB_WET_NW,MT_LH_MOB_WET_STOP};
 room_set(x,y,wet?water[shape]:dry[shape]);
}
static void rail_loop(int left,int top,int right,int bottom) {
 sRail[0][0]=left;sRail[0][1]=bottom;sRail[1][0]=right;sRail[1][1]=bottom;
 sRail[2][0]=right;sRail[2][1]=top;sRail[3][0]=left;sRail[3][1]=top;
 for(int x=left;x<=right;x++){rail_at(x,top,0);rail_at(x,bottom,0);}
 for(int y=top;y<=bottom;y++){rail_at(left,y,1);rail_at(right,y,1);}
 rail_at(left,bottom,4);rail_at(right,top,4);rail_at(left,top,2);rail_at(right,bottom,3);cart_position();
}
static void bridge_span(int left,int top,int bottom) {
 sMob.bx0=left;sMob.bx1=left+2;sMob.by0=top;sMob.by1=bottom;
 for(int y=top;y<=bottom;y++)for(int x=left;x<=left+2;x++) {
  if(y==top||y==bottom)room_set(x,y,MT_LH_MOB_RAMP);
  else room_set_overlay(x,y,x==left?MT_LH_MOB_DECK_W:x==left+2?MT_LH_MOB_DECK_E:MT_LH_MOB_DECK);
 }
}
static void chute_face(int left,int right,int launch,int landing) {
 sMob.cx0=left;sMob.cx1=right;sMob.cy0=launch+1;sMob.cy1=landing-1;sMob.launch=launch;sMob.landing=landing;
 for(int y=launch+1;y<landing;y++)for(int x=left;x<=right;x++)room_set(x,y,MT_LH_MOB_CLIFF);
 for(int x=left;x<=right;x++)room_set(x,launch,MT_LH_MOB_LAUNCH);
}
void handoff_mobility_build_regional(u32 seed,int pattern,int site) {
 u16 floor=room_get(16,20);int phase=seed&1;
 activate(1,0,pattern%3,site);sMob.prize=1;
 if(sMob.pattern==0) {
  sMob.cart=1;rect(11,4,20,18,MT_LH_MOB_WATER);
  /* A long suspended railway joins two dry banks. Water remains visible
     between sleepers and still drowns an unmounted walker. */
  rail_loop(5,6+phase,25,18);sMob.px=25;sMob.py=10;sMob.signx=5;sMob.signy=20;
 }else if(sMob.pattern==1) {
  sMob.bridge=1;rect(7,6,24,18,MT_LH_MOB_WATER);rect(5,12,26,13,floor);
  bridge_span(14,5,19);sMob.px=19;sMob.py=4;sMob.signx=12;sMob.signy=20;
  sMob.underx=26;sMob.undery=12;room_set(sMob.underx,sMob.undery,(gHandoffState.remaining[site]&0x2000)?MT_LH_MOB_OPEN:MT_LH_MOB_PRIZE);
 }else {
  sMob.chute=1;chute_face(5,12,7,14);sMob.px=12;sMob.py=16;sMob.signx=8;sMob.signy=5;
  /* The west path reaches the upper shelf; a wall face separates it from
     the landing. Returning around the eastern bank is always possible. */
 }
 room_set(sMob.px,sMob.py,prize_taken()?MT_LH_MOB_OPEN:MT_LH_MOB_PRIZE);
 room_set(sMob.signx,sMob.signy,MT_LH_MOB_SIGN);room_build_solid();
}
static bool8 mobility_floor_decoration(u16 mt) {
 if(mt==MT_NONE)return TRUE;
 if(metatile_type[mt]!=TT_FLOOR)return FALSE;
 return !metatile_prop[mt]||mt==MT_CREAM_MOLD_S0||mt==MT_CREAM_MOLD_S1||mt==MT_CREAM_MOLD_S2;
}
typedef struct {u16 ground[30],overlay[30],underlay[30];} MobilityFieldBackup;
static void mobility_field_backup(MobilityFieldBackup*b,int x,int y,int w,int h) {
 for(int yy=0;yy<h;yy++)for(int xx=0;xx<w;xx++){int i=yy*w+xx,j=(y+yy)*ROOM_MAX_W+x+xx;b->ground[i]=room_get(x+xx,y+yy);b->overlay[i]=room_get_overlay(x+xx,y+yy);b->underlay[i]=gRoom.underlay[j];}
}
static bool8 mobility_field_validate(const MobilityFieldBackup*b,int x,int y,int w,int h) {
 room_build_solid();
 if(regional_content_validate_routes())return TRUE;
 for(int yy=0;yy<h;yy++)for(int xx=0;xx<w;xx++){int i=yy*w+xx,j=(y+yy)*ROOM_MAX_W+x+xx;room_set(x+xx,y+yy,b->ground[i]);room_set_overlay(x+xx,y+yy,b->overlay[i]);gRoom.underlay[j]=b->underlay[i];}
 room_build_solid();handoff_mobility_reset();return FALSE;
}
bool8 handoff_mobility_build_field(u32 seed,int pattern,int site,int x,int y,int w,int h) {
 u16 floor;int middle;MobilityFieldBackup before;
 if(w<5||w>6||h!=5||x<1||y<1||x+w>=gRoom.w||y+h>=gRoom.h)return FALSE;
 for(int yy=y;yy<y+h;yy++)for(int xx=x;xx<x+w;xx++)
  if(room_type(xx,yy)!=TT_FLOOR||!mobility_floor_decoration(room_get_overlay(xx,yy))||legacy_surface_at(xx*16+8,yy*16+8)!=LS_NONE||room_box_solid(xx*16+1,yy*16+1,xx*16+14,yy*16+14))return FALSE;
 mobility_field_backup(&before,x,y,w,h);
 for(int yy=y;yy<y+h;yy++)for(int xx=x;xx<x+w;xx++)room_set_overlay(xx,yy,MT_NONE);
 floor=room_get(x,y);activate(1,1,pattern%3,site);sMob.prize=1;middle=y+h/2;
 if(sMob.pattern==0) {
  sMob.cart=1;rect(x+2,y+1,x+w-3,y+h-2,MT_LH_MOB_WATER);
  rail_loop(x+1,y+1,x+w-2,y+h-2);sMob.px=x+w-2;sMob.py=y+h-1;sMob.signx=x+1;sMob.signy=y+h-1;
 }else if(sMob.pattern==1) {
  sMob.bridge=1;rect(x+1,y+1,x+w-2,y+h-2,MT_LH_MOB_WATER);
  rect(x,y+h/2,x+w-1,y+h/2,floor);
  bridge_span(x+w/2-1,y,y+h-1);sMob.px=x+w-1;sMob.py=y;sMob.signx=x+1;sMob.signy=y+h-1;
  sMob.underx=x+w-1;sMob.undery=middle;room_set(sMob.underx,sMob.undery,(gHandoffState.remaining[site]&0x2000)?MT_LH_MOB_OPEN:MT_LH_MOB_PRIZE);
 }else {
  sMob.chute=1;chute_face(x+1,x+w-2,y,y+h-1);sMob.px=x+w-2;sMob.py=y+h-1;sMob.signx=x;sMob.signy=y;
 }
 room_set(sMob.px,sMob.py,prize_taken()?MT_LH_MOB_OPEN:MT_LH_MOB_PRIZE);
 room_set(sMob.signx,sMob.signy,MT_LH_MOB_SIGN);(void)seed;return mobility_field_validate(&before,x,y,w,h);
}

bool8 handoff_mobility_handles_floor(int px,int py) {
    if(!active())return FALSE;
    if(gMobilityMode==HMOB_CART)return ABS(px-gMobilityCartX)<=12&&ABS(py-gMobilityCartY)<=18;
    return sMob.bridge&&gMobilityLayer==1&&inside(px,py,sMob.bx0*16,sMob.by0*16,(sMob.bx1+1)*16-1,(sMob.by1+1)*16-1);
}
int handoff_mobility_priority(int original) {
    return active()&&gMobilityLayer==1?1:original;
}
bool8 handoff_mobility_box_solid(int x0,int y0,int x1,int y1) {
    if(!active())return FALSE;
    /* Elevated feet cannot step through either rail or fall sideways onto
       the lower path; only the two end ramps connect these planes. */
    if(sMob.bridge&&gMobilityLayer==1 && (x0<sMob.bx0*16+3||x1>(sMob.bx1+1)*16-4))return TRUE;
    if(sMob.chute&&gMobilityMode!=HMOB_PARACHUTE && gMobilityLayer==0 &&
       x1>=sMob.cx0*16&&x0<(sMob.cx1+1)*16&&y1>=sMob.cy0*16&&y0<(sMob.cy1+1)*16)return TRUE;
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
    if(sMob.regional) {
        static const s8 dx[4]={0,-16,16,0},dy[4]={16,0,0,-16};
        for(int i=0;i<4;i++) {int x=PX(sCartX)+dx[i],y=PX(sCartY)+dy[i];
            if(room_type_px(x,y)==TT_FLOOR&&!room_box_solid(x-5,y-9,x+4,y)) {gPlayer->x=Q16(x);gPlayer->y=Q16(y);break;}
        }
    }
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
        if(target==2)sMob.cart_done=1;
        if(sExitCart && !(target&1)){sExitCart=0;cart_exit();}
    }
}
static void parachute_tick(void) {
    Actor* a=gPlayer;
    int side=(gKeysHeld&KEY_RIGHT?1:0)-(gKeysHeld&KEY_LEFT?1:0);
    s32 landing=Q16(tile_y(sMob.landing));
    s32 speed=sFastDrop?Q16(2):(gKeysHeld&KEY_UP)?Q16(.5):(gKeysHeld&KEY_DOWN)?Q16(1):Q16(.75);
    if(gKeysDown&KEY_A){sFastDrop=1;gKeysDown&=~KEY_A;}
    a->x=CLAMP(a->x+side*Q16(.75),Q16(tile_x(sMob.cx0)),Q16(tile_x(sMob.cx1)));
    a->y=MIN(landing,a->y+speed);a->z=MIN(Q16(12),(landing-a->y)/2);
    a->state=PS_JUMP;a->facing=FACE_S;a->speed=0;a->zvel=0;
    if(a->y==landing) {
        gMobilityMode=HMOB_WALK;sMob.chute_done=1;clear_control();a->iframes=20;sPadCooldown=20;
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
            gPlayer->x=CLAMP(gPlayer->x,Q16(tile_x(sMob.cx0)),Q16(tile_x(sMob.cx1)));
            gPlayer->y=Q16(tile_y(sMob.landing));gPlayer->z=gPlayer->zvel=0;
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
    if(sMob.chute&&!sPadCooldown && (gKeysDown&KEY_R) && gPlayer->state==PS_NORMAL &&
       inside(PX(gPlayer->x),PX(gPlayer->y),sMob.cx0*16,sMob.launch*16,(sMob.cx1+1)*16-1,(sMob.launch+1)*16+4)) {
        gMobilityMode=HMOB_PARACHUTE;sFastDrop=0;gPl.input_lock=1;
        gPlayer->state=PS_JUMP;gPlayer->z=Q16(12);gPlayer->zvel=0;
        gKeysDown&=~KEY_R;sfx_play(SFX_JUMP);return TRUE;
    }
    return FALSE;
}
void handoff_mobility_update(void) {
    int px,py,top,bottom,left,right;
    if(!active()||gMobilityMode!=HMOB_WALK||!sMob.bridge)return;
    px=PX(gPlayer->x);py=PX(gPlayer->y)-4;
    top=sMob.by0*16;bottom=sMob.by1*16;left=sMob.bx0*16+4;right=(sMob.bx1+1)*16-5;
    if(!gMobilityLayer&&inside(px,py,left,top,right,top+15)){gMobilityLayer=1;sMob.bridge_from=1;}
    if(!gMobilityLayer&&inside(px,py,left,bottom,right,bottom+15)){gMobilityLayer=1;sMob.bridge_from=2;}
    if(gMobilityLayer&&((sMob.bridge_from==1&&py>=bottom)||(sMob.bridge_from==2&&py<top+16)))sMob.bridge_done=1;
    if(gMobilityLayer&&(py<top||py>=bottom+16))gMobilityLayer=0;
    if(sMob.regional&&!gMobilityLayer&&sMob.underx) {
        if(ABS(py-(sMob.undery*16+8))<20) {
            if(!sMob.under_from&&px<left-8)sMob.under_from=1;
            if(!sMob.under_from&&px>right+8)sMob.under_from=2;
            if((sMob.under_from==1&&px>right+8)||(sMob.under_from==2&&px<left-8))sMob.under_done=1;
        }else sMob.under_from=0;
    }
}
bool8 handoff_mobility_interact(void) {
    if(!active()||gMobilityMode!=HMOB_WALK||gPlayer->state!=PS_NORMAL)return FALSE;
    if(sMob.cart&&!sPadCooldown && near(gMobilityCartX,gMobilityCartY+9,20)) {
        gMobilityMode=HMOB_CART;gMobilityLayer=0;sExitCart=0;gPl.input_lock=1;
        gPlayer->x=sCartX;gPlayer->y=sCartY-Q16(5);gPl.sword_active=gPl.shield_up=0;
        gKeysDown&=~KEY_A;sfx_play(SFX_MENU);return TRUE;
    }
    if(sMob.regional&&sMob.underx&&gMobilityLayer==0&&near(tile_x(sMob.underx),tile_y(sMob.undery),16)) {
        if(!(gHandoffState.remaining[sMob.site]&0x2000)) {
            if(!sMob.under_done){textbox_open("The low-bank seal wakes when you walk beneath the span.");return TRUE;}
            gHandoffState.remaining[sMob.site]|=0x2000;legacy_item_grant(LI_RUPEE20,1);
            room_change(sMob.underx,sMob.undery,MT_LH_MOB_OPEN);textbox_open("The low bank passes beneath the bridge. A small cache waits in its shelter.");
        }else textbox_open("The lower-bank cache is empty.");
        return TRUE;
    }
    if(sMob.prize&&near(tile_x(sMob.px),tile_y(sMob.py),18)) {
        if(!sMob.regional&&!red_fusion()){textbox_open("A red fusion joins the broken shelf to this cache.");return TRUE;}
        if(!route_done()&&!prize_taken()){textbox_open(sMob.pattern==0?"The far station's seal wakes when the cart arrives.":sMob.pattern==1?"Cross the upper bridge from one ramp to the other to wake this seal.":"The landing seal remembers a parachute descent from the arrow shelf.");return TRUE;}
        if(!prize_taken()) {
            if(sMob.field)gHandoffState.remaining[sMob.site]|=0x4000;else gHandoffState.completed[sMob.site>>3]|=1u<<(sMob.site&7);
            legacy_item_grant(LI_RUPEE100,1);room_change(sMob.px,sMob.py,MT_LH_MOB_OPEN);
            handoff_notify(HN_EVENT,gGame.area,gGame.area==AREA_HANDOFF?sMob.site:gGame.cell,LI_RUPEE100);sfx_play(SFX_CHEST);
            textbox_open(sMob.regional?"The crossing is complete. The old cache holds one hundred gilt.":"The red fusion raised a real bridge. This cache holds one hundred gilt.");
        }else textbox_open(sMob.regional?"The crossing's cache is empty.":"The shelf remembers your red fusion. Its cache is empty.");
        return TRUE;
    }
    if(near(tile_x(sMob.signx),tile_y(sMob.signy),20)||(!sMob.regional&&near(tile_x(18),tile_y(20),20))) {
        textbox_open(sMob.regional?(sMob.pattern==0?"The cart joins these banks. A boards; A again leaves at the next round stop. The far station wakes its cache.":sMob.pattern==1?"The ramps lead over the water. The low bank passes beneath the slats. Walk both routes to find their caches.":"The arrow shelf opens a descent. Press R, steer left or right, hold Up to drift slowly, or A to fold the silk. A cache waits on the landing."):"Cart: A boards; A again leaves at the next round stop.|Bridge: enter either end ramp to cross above; walk across the middle bank to pass below.|Shelf: stand on its arrow and press R. Steer left/right; A folds the parachute for a quicker descent.");
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
    if(sMob.cart) {
    target=(gMobilityCartPoint+1)&3;
    face=tile_x(sRail[target][0])>gMobilityCartX?FACE_E:tile_x(sRail[target][0])<gMobilityCartX?FACE_W:tile_y(sRail[target][1])>gMobilityCartY?FACE_S:FACE_N;
    frame=face*2+(gMobilityMode==HMOB_CART?((gFrame>>3)&1):0);stream(frame,&sCartTile,&sCartFrame);
    if(sCartTile)draw_sprite(gMobilityCartX-16-gCamX,gMobilityCartY-26-gCamY,SHEET_HANDOFF_MOBILITY,sCartTile,0,0,1,sheets[SHEET_HANDOFF_MOBILITY].pal);
    }
    if(gMobilityMode==HMOB_PARACHUTE) {
        frame=8+((gFrame>>4)&1);stream(frame,&sChuteTile,&sChuteFrame);
        if(sChuteTile)draw_sprite(PX(gPlayer->x)-16-gCamX,PX(gPlayer->y)-PX(gPlayer->z)-45-gCamY,SHEET_HANDOFF_MOBILITY,sChuteTile,0,0,0,sheets[SHEET_HANDOFF_MOBILITY].pal);
    }
}

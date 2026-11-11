/* Ordinary Drain services: physical people/fixtures, without a room-select
   desk. Existing Peddler stock/dialogue and the purple wizard stay intact. */
#include "hub_services.h"
#include "game.h"
#include "room.h"
#include "actor.h"
#include "player.h"
#include "handoff_events.h"

enum { HUB_TRADER,HUB_FUSER,HUB_GUIDE,HUB_BED,HUB_TROPHY,HUB_SERVICE_COUNT };
typedef struct {s16 x,y;u8 frame,service;} HubService;
static const HubService sServices[HUB_SERVICE_COUNT]={
    {120,110,4,HRS_SHOP},
    {152,238,0,HRS_FUSE},
    {304,238,8,HRS_CHAIN},
    {352,238,F_CREAMFOLK_DRAIN_BED,HRS_INN},
    {416,238,F_CREAMFOLK_DRAIN_TROPHY,HRS_TROPHY}
};
enum { HUB_CHEST_X=384,HUB_CHEST_Y=238 };
static u16 sTiles[HUB_SERVICE_COUNT],sChestTile;
static u8 sReady;

void hub_services_build(void) {
    int x,y;
    u16 ground[15],overlay[15];
    sReady=0;
    if(gGame.area!=AREA_SEWER)return;
    /* Copy before writing, so the placement remains independent of the
       relative source/destination. Exact metatile IDs retain native pixels,
       timing, palette, collision and the ladder's recognizable up arrow. */
    for(y=0;y<5;y++)for(x=0;x<3;x++) {
        ground[y*3+x]=room_get(8+x,y);
        overlay[y*3+x]=room_get_overlay(8+x,y);
    }
    for(y=0;y<5;y++)for(x=0;x<3;x++) {
        room_set(18+x,y,ground[y*3+x]);
        room_set_overlay(18+x,y,overlay[y*3+x]);
    }
    /* The existing carpet/floor south of this stamp is dry and passable.
       No storage, cabinet, north-bank route or NPC is relocated. */
    room_render();
}

void hub_services_enter(void) {
    int i;
    sReady=0;sChestTile=0;
    for(i=0;i<HUB_SERVICE_COUNT;i++)sTiles[i]=0;
    if(gGame.area!=AREA_SEWER)return;
    for(i=0;i<HUB_SERVICE_COUNT;i++)
        sTiles[i]=sprite_load_frame(SHEET_CREAMFOLK,sServices[i].frame);
    sChestTile=sprite_load_frame(SHEET_INTERACTIVECHEST,F_INTERACTIVECHEST_BRASS_CLOSED);
    sReady=1;
}

static bool8 at_front(int x,int y) {
    int dx=PX(gPlayer->x)-x,dy=PX(gPlayer->y)-y;
    return gPlayer->facing==FACE_N && ABS(dx)<=14 && dy>=8 && dy<=30;
}

u16 hub_services_try_interact(u16 pressed) {
    int i;
    if(!sReady||gGame.area!=AREA_SEWER||!gPlayer||gPlayer->state!=PS_NORMAL)return 0;
    if((pressed&KEY_A)&&gHandoffState.inn_reward&&at_front(HUB_CHEST_X,HUB_CHEST_Y)) {
        if(handoff_claim_inn_reward())return KEY_A;
    }
    for(i=0;i<HUB_SERVICE_COUNT;i++) {
        const HubService* service=&sServices[i];
        if(!at_front(service->x,service->y))continue;
        if(i==HUB_GUIDE && (pressed&KEY_R)) {
            if(handoff_open_service(HRS_HINT))return KEY_R;
        }
        if((pressed&KEY_A)&&handoff_open_service(service->service))return KEY_A;
    }
    return 0;
}

static bool8 box_overlap(int ax0,int ay0,int ax1,int ay1,int bx0,int by0,int bx1,int by1) {
    return ax0<=bx1 && ax1>=bx0 && ay0<=by1 && ay1>=by0;
}

bool8 hub_services_box_solid(int x0,int y0,int x1,int y1) {
    int i;
    if(!sReady||gGame.area!=AREA_SEWER)return FALSE;
    for(i=0;i<HUB_SERVICE_COUNT;i++) {
        const HubService* service=&sServices[i];
        int half=i==HUB_BED?9:i==HUB_TROPHY?7:6;
        if(box_overlap(x0,y0,x1,y1,service->x-half,service->y-11,service->x+half,service->y))return TRUE;
    }
    return gHandoffState.inn_reward &&
        box_overlap(x0,y0,x1,y1,HUB_CHEST_X-10,HUB_CHEST_Y-10,HUB_CHEST_X+10,HUB_CHEST_Y);
}

void hub_services_draw(bool8 front) {
    int i;
    if(!sReady||gGame.area!=AREA_SEWER||!gPlayer)return;
    for(i=0;i<HUB_SERVICE_COUNT;i++) {
        const HubService* service=&sServices[i];
        int pal=i==HUB_TROPHY?PAL_OBJ_FX:PAL_OBJ_IRON;
        if(sTiles[i] && (PX(gPlayer->y)<=service->y)==front)
            draw_sprite(service->x-16-gCamX,service->y-31-gCamY,
                        SHEET_CREAMFOLK,sTiles[i],0,0,2,pal);
    }
    if(gHandoffState.inn_reward && sChestTile && (PX(gPlayer->y)<=HUB_CHEST_Y)==front)
        draw_sprite(HUB_CHEST_X-16-gCamX,HUB_CHEST_Y-29-gCamY,
                    SHEET_INTERACTIVECHEST,sChestTile,0,0,2,
                    interactivechest_frame_pal[F_INTERACTIVECHEST_BRASS_CLOSED]);
}

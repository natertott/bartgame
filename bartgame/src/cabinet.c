#include "cabinet.h"
#include "actor.h"
#include "arcade.h"
#include "game.h"
#include "player.h"
#include "room.h"
#include "video.h"

u8 gCabinetActive;
s16 gCabinetX,gCabinetY;
static u16 sCabinetTile;

void cabinet_room_reset(void) {
    gCabinetActive=0;
    sCabinetTile=0;
}

void cabinet_spawn(int px,int py) {
    sCabinetTile=sprite_load_sheet(SHEET_ARCADE);
    if (!sCabinetTile) return;
    gCabinetX=px;gCabinetY=py;
    gCabinetActive=1;
}

bool8 cabinet_box_solid(int x0,int y0,int x1,int y1) {
    return gCabinetActive && x0<=gCabinetX+11 && x1>=gCabinetX-12 &&
           y0<=gCabinetY && y1>=gCabinetY-13;
}

bool8 cabinet_try_interact(void) {
    int dx,dy;
    if (!gCabinetActive || gGame.area!=AREA_SEWER || gPlayer->state!=PS_NORMAL ||
        gPlayer->facing!=FACE_N) return FALSE;
    dx=PX(gPlayer->x)-gCabinetX;dy=PX(gPlayer->y)-gCabinetY;
    if (dx<-23 || dx>23 || dy<7 || dy>34) return FALSE;
    arcade_open();
    return TRUE;
}

void cabinet_draw(bool8 front) {
    bool8 closer;
    if (!gCabinetActive || gGame.area!=AREA_SEWER) return;
    closer=PX(gPlayer->y)<=gCabinetY;
    if (closer!=front) return;
    /* Native contact point is(16,62), not the padded canvas bottom. */
    draw_sprite(gCabinetX-16-gCamX,gCabinetY-62-gCamY,SHEET_ARCADE,sCabinetTile,
                (gFrame>>6)&1,0,2,PAL_OBJ_FX);
}

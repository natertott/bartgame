/* Large, legible interactive scenery. The logical tile still owns collision,
   reward, persistence and transitions; these two streamed images own display.
   A generated room has at most one chest (pocket hoards are pickup actors),
   and at most one mystery entrance/exit, so each needs only one live frame. */
#include "gba.h"
#include "video.h"
#include "room.h"
#include "actor.h"
#include "player.h"
#include "game.h"
#include "world.h"
#include "myst.h"
#include "interactive.h"

static u16 sChestTile, sEntryTile;
static u8 sChestFrame, sEntryFrame;
static s8 sChestX, sChestY, sEntryX, sEntryY;
static u8 sEntryInterior;

bool8 interactive_chest_tile(u16 mt) {
    return mt == MT_CHEST || mt == MT_CHEST_OPEN;
}

bool8 interactive_chest_overlay(u16 mt) {
    return mt == MT_MYST_CHEST || mt == MT_MYST_CHEST_OPEN;
}

bool8 interactive_mouth_tile(u16 mt) {
    return mt == MT_MOUTH_CAVE || mt == MT_MOUTH_HOLLOW || mt == MT_MOUTH_THICKET;
}

bool8 interactive_chest_ready(void) { return sChestTile != 0; }
bool8 interactive_entry_ready(void) { return sEntryTile != 0; }

int interactive_chest_tier(void) {
    const Cell* cell = &gWorld.cells[gGame.cell];
    if (cell->role == ROLE_KEYITEM || cell->role == ROLE_KEYCHEST)
        return 2;
    if (gGame.area == AREA_MYST)
        return MIN(MYST_SIZE(gWorld.myst[gGame.cell]), 2);
    switch (cell->role_arg) {
        case CHEST_GILT:
        case CHEST_BOMBS: return 0;
        case CHEST_HEART_PIECE:
        case CHEST_MAP: return 1;
        default: return 2;
    }
}

static bool8 has_chest(int x, int y) {
    return room_type(x,y) == TT_CHEST || room_get(x,y) == MT_CHEST_OPEN ||
           interactive_chest_overlay(room_get_overlay(x,y));
}

void interactive_cell_changed(int x, int y) {
    if (has_chest(x,y)) {
        sChestX = x;
        sChestY = y;
    } else if (sChestX == x && sChestY == y) {
        sChestX = sChestY = -1;
    }
}

void interactive_room_reset(void) {
    int x,y;
    sChestTile = sEntryTile = 0;
    sChestFrame = sEntryFrame = 0xFF;
    sChestX = sChestY = sEntryX = sEntryY = -1;
    sEntryInterior = 0;
    if (gGame.area == AREA_SEWER)
        return;
    for (y=0;y<gRoom.h;y++) for (x=0;x<gRoom.w;x++) {
        interactive_cell_changed(x,y);
        if (interactive_mouth_tile(room_get(x,y))) {
            sEntryX=x;
            sEntryY=y;
        }
    }
    /* Some trials create their one chest only after being won. Reserve its
       slot now, so opening a menu cannot consume its future allocation. */
    if (sChestX >= 0 || gGame.area == AREA_MYST)
        sChestTile = sprite_alloc(sheets[SHEET_INTERACTIVECHEST].frame_tiles);
    if (gGame.area == AREA_MYST) {
        sEntryInterior=1;
        sEntryX=gRoom.w/2-1;
        sEntryY=gRoom.h-1;
    }
    if (sEntryX >= 0)
        sEntryTile = sprite_alloc(sheets[SHEET_INTERACTIVEENTRY].frame_tiles);
    /* The first room render precedes sprite allocation. Apply enlarged
       display suppression now; failed allocations retain the old BG art. */
    room_render();
}

static int entry_frame(void) {
    int style;
    if (sEntryInterior) {
        style = MYST_STYLE(gWorld.myst[gGame.cell]);
        return style + (room_type(sEntryX,sEntryY) == TT_MYST ? 0 : 3);
    }
    u16 mt=room_get(sEntryX,sEntryY);
    return mt == MT_MOUTH_CAVE ? 0 : mt == MT_MOUTH_HOLLOW ? 1 : 2;
}

static void stream_frame(int sheet,int frame,u16 tile,u8* previous) {
    if (*previous != frame) {
        const SpriteSheet* sh=&sheets[sheet];
        vram_queue(sh->tiles+frame*sh->frame_tiles*16,OBJ_TILE(tile),sh->frame_tiles*32);
        *previous=frame;
    }
}

void interactive_draw(bool8 behind) {
    if (sEntryTile && sEntryX >= 0 && behind) {
        /* A forest threshold is centred on one logical entrance tile;
           an interior threshold spans the existing pair of exit tiles. */
        int sx=sEntryX*16-(sEntryInterior?0:8)-gCamX;
        int sy=sEntryY*16-48-gCamY;
        int frame=entry_frame();
        stream_frame(SHEET_INTERACTIVEENTRY,frame,sEntryTile,&sEntryFrame);
        /* The open portal is scenery behind the approaching actor, including
           its black interior. A closed trial grille must cover the old
           foreground wall at the existing solid exit, hence priority one. */
        int priority=sEntryInterior && room_type(sEntryX,sEntryY)!=TT_MYST ? 1 : 2;
        draw_sprite(sx,sy,SHEET_INTERACTIVEENTRY,sEntryTile,0,0,priority,PAL_OBJ_LIFT);
    }
    if (sChestTile && sChestX >= 0) {
        /* At equal priority the earlier OAM entry is in front. Keep the
           chest in front when Bloom stands north of its physical footprint,
           and behind Bloom after his feet pass its south edge. */
        bool8 far = PX(gPlayer->y) >= (sChestY+1)*16;
        if (far == behind) {
            u16 ground=room_get(sChestX,sChestY),overlay=room_get_overlay(sChestX,sChestY);
            int open=ground==MT_CHEST_OPEN || overlay==MT_MYST_CHEST_OPEN;
            int frame=interactive_chest_tier()*2+open;
            int sx=sChestX*16-8-gCamX,sy=sChestY*16-16-gCamY;
            stream_frame(SHEET_INTERACTIVECHEST,frame,sChestTile,&sChestFrame);
            /* Flat litter can promote Bloom to priority one. A near chest
               must still cover his feet when he stands north of its lid. */
            draw_sprite(sx,sy,SHEET_INTERACTIVECHEST,sChestTile,0,0,far ? 2 : 1,PAL_OBJ_LIFT);
        }
    }
}

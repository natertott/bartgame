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
#if BART_FOREST_VARIANT >= 6
#include "util.h"
#include "roomgen.h"
static u16 sLandmarkTile[4];
static u8 sLandmarkFrame[4];
static s16 sLockX[4],sLockY[4];

/* One marker per gate pair; its single keyhole does not promise two keys. */
static void scan_locks(void) {
    int side;
    for(side=0;side<4;side++) {
        int x0,y0,x1,y1;
        sLockX[side]=sLockY[side]=-1;
        if(gGame.area!=AREA_FOREST)continue;
        roomgen_gate_tiles(side,&x0,&y0,&x1,&y1);
        if(room_get(x0,y0)==MT_DOOR_LOCKED || room_get(x1,y1)==MT_DOOR_LOCKED) {
            sLockX[side]=(x0+x1)*8+8;
            sLockY[side]=(y0+y1)*8+16;
        }
    }
}

bool8 interactive_landmark_tile(int x,int y) {
    if(gGame.area!=AREA_FOREST)return FALSE;
    if(sLandmarkTile[0] && gSpots.has_relic &&
       !(gWorld.cells[gGame.cell].flags&CF_RELIC_TAKEN) &&
       x==gSpots.relic.x && y==gSpots.relic.y)return TRUE;
    return sLandmarkTile[1] && gSpots.has_shrine &&
           x==gSpots.shrine.x && y==gSpots.shrine.y;
}
#endif

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
#if BART_FOREST_VARIANT >= 6
    memset(sLandmarkTile,0,sizeof(sLandmarkTile));
    memset(sLandmarkFrame,255,sizeof(sLandmarkFrame));
    memset(sLockX,255,sizeof(sLockX));
    memset(sLockY,255,sizeof(sLockY));
#endif
    if (gGame.area == AREA_SEWER || gGame.area>=AREA_CREAM)
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
#if BART_FOREST_VARIANT >= 6
    if(gGame.area==AREA_FOREST) {
        if(gSpots.has_relic)sLandmarkTile[0]=sprite_alloc(sheets[SHEET_FORESTLANDMARK].frame_tiles);
        if(gSpots.has_shrine)sLandmarkTile[1]=sprite_alloc(sheets[SHEET_FORESTLANDMARK].frame_tiles);
        /* Two live frame uploads suffice: all lock instances share one frame. */
        scan_locks();
        for(x=0;x<4;x++)if(sLockX[x]>=0) {
            sLandmarkTile[3]=sprite_alloc(sheets[SHEET_FORESTLANDMARK].frame_tiles);break;
        }
    }
#endif
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

#if BART_FOREST_VARIANT >= 6
static void draw_landmark(int slot,int frame,int x,int y,bool8 behind) {
    bool8 far=PX(gPlayer->y)>=y;
    if(!sLandmarkTile[slot] || far!=behind)return;
    stream_frame(SHEET_FORESTLANDMARK,frame,sLandmarkTile[slot],&sLandmarkFrame[slot]);
    draw_sprite(x-8-gCamX,y-32-gCamY,SHEET_FORESTLANDMARK,sLandmarkTile[slot],
                0,0,slot==3?1:(far?2:1),forestlandmark_frame_pal[frame]);
}
#endif

void interactive_draw(bool8 behind) {
    if(gGame.area>=AREA_CREAM)return;
#if BART_FOREST_VARIANT >= 6
    if(gGame.area==AREA_FOREST) {
        int side;
        if(gSpots.has_relic && !(gWorld.cells[gGame.cell].flags&CF_RELIC_TAKEN))
            draw_landmark(0,F_FORESTLANDMARK_RELIC,gSpots.relic.x*16+8,
                          gSpots.relic.y*16+16,behind);
        if(gSpots.has_shrine)
            draw_landmark(1,(gWorld.cells[gGame.cell].flags&CF_SHRINE_USED)?
                          F_FORESTLANDMARK_SHRINE_SPENT:F_FORESTLANDMARK_SHRINE_AVAILABLE,
                          gSpots.shrine.x*16+8,gSpots.shrine.y*16+16,behind);
        scan_locks();
        for(side=0;side<4;side++)if(sLockX[side]>=0)
            draw_landmark(3,F_FORESTLANDMARK_KEYLOCK,sLockX[side],sLockY[side],behind);
    }
#endif
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
        draw_sprite(sx,sy,SHEET_INTERACTIVEENTRY,sEntryTile,0,0,priority,interactiveentry_frame_pal[frame]);
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
#if BART_FOREST_VARIANT >= 6
            if(frame<2 && (hash32(gWorld.seed,gGame.cell)&1))
                frame=F_INTERACTIVECHEST_WOODEN_B_CLOSED+open;
#endif
            int sx=sChestX*16-8-gCamX,sy=sChestY*16-16-gCamY;
            stream_frame(SHEET_INTERACTIVECHEST,frame,sChestTile,&sChestFrame);
            /* Flat litter can promote Bloom to priority one. A near chest
               must still cover his feet when he stands north of its lid. */
            draw_sprite(sx,sy,SHEET_INTERACTIVECHEST,sChestTile,0,0,far ? 2 : 1,interactivechest_frame_pal[frame]);
        }
    }
}

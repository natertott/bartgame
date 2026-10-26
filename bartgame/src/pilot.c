/* BARTGAME: the Drain art pilot, a temporary screen for the artist's
   native 240x160 scene (art/ref/drain_pilot, kept as delivered). Its own
   characters fill charblock 0, its ground map is BG2 and its canopies BG1
   (32x32 maps, scroll 0,0), its 13 BG banks take slots 0-12, and its three
   sprites stand where layout.json puts them. No HUD, no world actors, no
   collision: a fixed frame to compare with master_240x160.png, not a level.

   The pilot's OBJ banks 0-2 are moved to slots 13-15, since the game's
   colours hold 0-13: 14 and 15 are free, and 13 is the 32x32 folk's, whose
   Peddler and Gatekeeper this scene draws on its own. Leaving puts 13
   back. Its OBJ tiles sit above the resident ones, where the sheets load
   again at a room's start. */
#include "gba.h"
#include "video.h"
#include "room.h"
#include "actor.h"
#include "game.h"
#include "pilot.h"

#define PILOT_OBJ_PAL 13  /* the pilot's OBJ bank 0 lands here, 1 and 2 after */
#define PILOT_OBJ_TILE 72 /* OBJ_TILE_FIRST_FREE */

static u16 sTile[PILOT_SPRITE_COUNT];
static u8 sLeaving;

/* an OBJ's shape and size bits, from its width and height */
static void obj_shape(int w, int h, u16* attr0, u16* attr1) {
    static const u8 dims[3][4][2] = {
        { { 8, 8 }, { 16, 16 }, { 32, 32 }, { 64, 64 } },
        { { 16, 8 }, { 32, 8 }, { 32, 16 }, { 64, 32 } },
        { { 8, 16 }, { 8, 32 }, { 16, 32 }, { 32, 64 } },
    };
    int s, z;
    for (s = 0; s < 3; s++)
        for (z = 0; z < 4; z++)
            if (dims[s][z][0] == w && dims[s][z][1] == h) {
                *attr0 = s << 14;
                *attr1 = ATTR1_SIZE(z);
                return;
            }
}

void pilot_show(void) {
    int i;
    u16 tile = PILOT_OBJ_TILE;
    gAnimTiles = 0; /* the water's frames would write over the pilot's characters */
    actors_clear();
    REG_BLDCNT = 0;
    dma3_copy32(pilot_chr, CHARBLOCK(0), PILOT_TILE_COUNT * 32);
    dma3_copy32(pilot_overlay_map, SCREENBLOCK(24), 2048);
    dma3_copy32(pilot_ground_map, SCREENBLOCK(28), 2048);
    REG_BG1CNT = BGCNT_PRIO(1) | BGCNT_CHARBASE(0) | BGCNT_SCREENBASE(24) | BGCNT_SIZE_32x32;
    REG_BG2CNT = BGCNT_PRIO(2) | BGCNT_CHARBASE(0) | BGCNT_SCREENBASE(28) | BGCNT_SIZE_32x32;
    gBgScroll[1][0] = gBgScroll[1][1] = gBgScroll[2][0] = gBgScroll[2][1] = 0;
    for (i = 0; i < 13; i++)
        pal_set_bg(i, &pilot_bg_pal[i * 16]);
    for (i = 0; i < PILOT_SPRITE_COUNT; i++) {
        const PilotSprite* sp = &pilot_sprites[i];
        pal_set_obj(PILOT_OBJ_PAL + sp->pal, &pilot_obj_pal[sp->pal * 16]);
        dma3_copy32(sp->tiles, OBJ_TILE(tile), sp->tile_count * 32);
        sTile[i] = tile;
        tile += sp->tile_count;
    }
    sLeaving = 0;
    gGame.state = GS_PILOT;
    fade_set(16);
    fade_start(0, 2);
    video_show(DCNT_BG1 | DCNT_BG2 | DCNT_OBJ);
}

bool8 pilot_update(void) {
    int i;
    for (i = 0; i < PILOT_SPRITE_COUNT; i++) {
        const PilotSprite* sp = &pilot_sprites[i];
        OamEntry* o = oam_alloc();
        u16 a0 = 0, a1 = 0;
        obj_shape(sp->w, sp->h, &a0, &a1);
        o->attr0 = ATTR0_Y(sp->y) | a0;
        o->attr1 = ATTR1_X(sp->x) | a1;
        o->attr2 = ATTR2_TILE(sTile[i]) | ATTR2_PRIO(2) | ATTR2_PAL(PILOT_OBJ_PAL + sp->pal);
    }
    if (!sLeaving && (gKeysDown & KEY_START)) {
        sLeaving = 1;
        fade_start(16, 2);
    }
    if (!sLeaving || !fade_done())
        return 0;
    /* the game's maps are 64x64 and its folk keep slot 13 */
    REG_BG1CNT = BGCNT_PRIO(1) | BGCNT_CHARBASE(0) | BGCNT_SCREENBASE(24) | BGCNT_SIZE_64x64;
    REG_BG2CNT = BGCNT_PRIO(2) | BGCNT_CHARBASE(0) | BGCNT_SCREENBASE(28) | BGCNT_SIZE_64x64;
    pal_set_obj(PAL_OBJ_FOLK32, &pal_obj[PAL_OBJ_FOLK32 * 16]);
    sprites_reset();
    return 1;
}

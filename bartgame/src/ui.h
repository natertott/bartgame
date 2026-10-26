#ifndef UI_H
#define UI_H
#include "gba.h"
#include "vwf.h"

/* The UI kit's frames laid into a map of 32 tiles to a row: BG0's, over
   the world, or BG3's, the backdrop of the shop and the pause menu. On
   BG3 every clear pixel of the kit is the panel's own navy. */
#define UI_BG0 46 /* the kit's first tile in BG0's charblock */
#define UI_BG3 1  /* and in BG3's; tile 0 there is the panel's fill */
#define UI_PAL PAL_SLOT_MENU
#define UI_HF 0x400
#define UI_VF 0x800

/* a frame's corner, edge, side and fill */
enum { FR_PANEL, FR_SLOT, FR_SEL, FR_EMPTY, FR_ROW, FR_SROW, FR_BUB };
/* two tiles tall: a name plate, a tab, the open tab */
enum { PL_PLATE, PL_TAB, PL_TABON };

extern u16 gBg3[32 * 32];
extern u8 gBg3Dirty; /* pushed with BG0's map at the VBlank */

void ui_put(u16* map, int tx, int ty, u16 entry);
void ui_tile(u16* map, int base, int tx, int ty, int tile, u16 flips);
void ui_frame(u16* map, int base, int tx, int ty, int w, int h, int kind);
void ui_plate(u16* map, int base, int tx, int ty, int w, int kind);
/* a plate drawn into a canvas at any pixel, w tiles wide */
void ui_plate_px(Canvas* c, int x, int y, int w, int kind);
/* the width in tiles of a plate round w pixels of text, pad each side */
int ui_plate_tiles(int w, int pad);

/* BG3 over the world: the kit in charblock 3 (whose room maps are drawn
   again by room_render on the way out), the map all fill */
void ui_backdrop_open(void);
void ui_backdrop_clear(void); /* gBg3 all fill again */
void ui_backdrop_flush(void); /* gBg3 to its screenblock now */

#endif

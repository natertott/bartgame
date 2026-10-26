#ifndef TEXT_H
#define TEXT_H
#include "gba.h"
#include "vwf.h"

void text_init(void);
void text_flush(void);
void bg0_clear(void);
void bg0_put(int tx, int ty, u16 tile);
void bg0_fill(int tx, int ty, int w, int h, u16 tile);
u16* bg0_map(void); /* the shadow map, to be pushed at the next VBlank */
/* the text pool starts again: a new box of words over the world, the
   HUD's purse kept; or a new page over the whole screen, the purse too */
void bg0_pool_reset(void);
void bg0_pool_reset_full(void);
/* a clear canvas mapped at (tx, ty) in the kit's palette */
bool8 bg0_canvas(Canvas* c, int tx, int ty, int tw, int th);
/* a canvas shown at (tx, ty), or its place cleared */
void bg0_show(const Canvas* c, int tx, int ty, bool8 on);
/* a name plate of s centred, its foot over a box's top edge when edge
   is set (the plate is a canvas, its art and its words as one) */
void bg0_plate(Canvas* c, int tx, int ty, const char* s, int ink, bool8 edge);

/* the message box: plain, or with a speaker's name and face */
void textbox_open(const char* s);
void textbox_open_named(const char* name, int face, const char* s);
void textbox_update(void);
void textbox_draw(void);
bool8 textbox_active(void);
void textbox_close(void);

/* the speaker's face: its sprite resident, its palette loaded */
void face_load(int face); /* a frame of the face sheet: F_FACE_* */
void face_draw(int x, int y, int prio); /* the face's 48 pixels square at (x, y) */

/* the shop: the keeper's face and words, the wares, the one chosen */
enum { OWN_NONE, OWN_BOMBS, OWN_ARROWS };
typedef struct {
    const char* name;
    const char* desc;   /* set to the panel's width */
    const char* effect; /* in red under it */
    u16 price;
    u8 icon;            /* a frame of the items sheet */
    u8 own;             /* OWN_*: what the hero already carries of it */
} ShopItem;
void shop_open(int face, const char* greet, const ShopItem* items, int n);
void shop_update(void);
void shop_draw(void);
void shop_close(void);
int shop_result(void); /* -2 open, -1 left, else the choice */
bool8 shop_active(void);

/* the HUD and the mini-map: hud_draw lays the panels and draws its
   sprites, so it goes first in OAM */
void hud_draw(void);
void minimap_render(void);

#endif

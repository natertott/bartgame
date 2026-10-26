#ifndef VWF_H
#define VWF_H
#include "gba.h"

/* Text set in the UI's own face (art/ui_font.py) a pixel at a time into
   a canvas: tiles of BG0 held from a pool, mapped where they show. In a
   string, a byte below a space changes the ink for what follows. */
#define INK_BASE "\x01" /* the ink the text was set in */
#define INK_HIGH "\x02" /* a word that matters */
#define INK_RED "\x03"  /* what a thing does */
#define INK_GOLD "\x04" /* a name */
#define INK_DIM "\x05"

/* what is drawn round the letters */
enum { FX_NONE, FX_SHADOW, FX_OUTLINE };

typedef struct {
    u16 tile;          /* the first tile, in BG0's charblock or OBJ VRAM */
    u8 tw, th;         /* in tiles */
    u8 obj;            /* set: its tiles are a sprite's, in OBJ 1D order */
    u32* px;           /* tw * th tiles of eight words, 4bpp, row-major by tile */
} Canvas;

void vwf_pool(int first, int end); /* the pool starts again */
bool8 vwf_canvas(Canvas* c, int tw, int th);
/* a canvas of BG0's tiles held for good at tile, outside the pool */
void vwf_canvas_at(Canvas* c, int tile, int tw, int th);
/* a canvas for a sprite: buf of tw * th * 8 words, copied to OBJ tile */
void vwf_canvas_obj(Canvas* c, u32* buf, int tile, int tw, int th);
void vwf_clear(Canvas* c, int ink); /* every pixel the one ink; 0 is clear */
/* a kit tile into one of the canvas's tiles: over what is there (its
   clear pixels leave it), or copied whole; hflip 1, vflip 2 */
void vwf_kit(Canvas* c, int tx, int ty, int ui_tile, int flip, bool8 over);
/* a kit tile's art at any pixel of the canvas, its clear pixels left */
void vwf_kit_px(Canvas* c, int x, int y, int ui_tile, int flip);
void vwf_pixel(Canvas* c, int x, int y, int ink);
int vwf_glyph(Canvas* c, int x, int y, int ch, int ink); /* the advance */
int vwf_text(Canvas* c, int x, int y, const char* s, int ink);
/* the text over its shadow or inside an outline of fx_ink */
int vwf_text_fx(Canvas* c, int x, int y, const char* s, int ink, int fx_ink, int fx);
int vwf_width(const char* s);
/* the ink a colour code selects, base for INK_BASE */
int vwf_ink(int code, int base);
int vwf_advance(int ch);
/* the next line of s that fits in w pixels, broken at a space: its
   length in bytes (at least one word) */
int vwf_fit(const char* s, int w);
/* s set within w pixels from (x, y), a line every pitch pixels, at most
   lines lines: the lines set */
int vwf_block(Canvas* c, int x, int y, int w, int pitch, const char* s, int ink, int lines);
/* the canvas into VRAM: at once, or at the next VBlank */
void vwf_flush(Canvas* c, bool8 now);
/* the canvas's tiles in a map of 32 tiles to a row, at (tx, ty), palette pal */
void vwf_map(const Canvas* c, u16* map, int tx, int ty, int pal);
/* n as figures, at least width of them (spaces before) */
char* vwf_num(char* buf, int n, int width);

#endif

/* BARTGAME: the UI kit's frames (art/ui_kit.py), laid tile by tile. A
   frame is its corner, edge and side turned for the other three, so
   every frame is the same all round. */
#include "gba.h"
#include "ui.h"
#include "vwf.h"
#include "assets.h"

#define BG3_SB 22

u16 gBg3[32 * 32] EWRAM_BSS;
u8 gBg3Dirty;

static const u8 sFrames[][4] = {
    /* corner, edge, side, fill (0xFF: leave what is there) */
    { UI_PANEL_TL, UI_PANEL_T, UI_PANEL_L, UI_FILL },
    { UI_SLOT_TL, UI_SLOT_T, UI_SLOT_L, UI_SLOT_FILL },
    { UI_SEL_TL, UI_SEL_T, UI_SEL_L, UI_SLOT_FILL },
    { UI_EMPTY_TL, UI_EMPTY_T, UI_EMPTY_L, 0xFF },
    { UI_ROW_TL, UI_ROW_T, UI_ROW_L, UI_SLOT_FILL },
    { UI_SROW_TL, UI_SROW_T, UI_SROW_L, UI_SLOT_FILL },
    { UI_BUB_TL, UI_BUB_T, UI_BUB_L, UI_BUB_FILL },
    { UI_HUD_TL, UI_HUD_T, UI_HUD_L, UI_FILL },
};

static const u8 sPlates[][4] = {
    /* end, top; end, bottom; middle, top; middle, bottom */
    { UI_PLATE_L_TOP, UI_PLATE_L_BOT, UI_PLATE_M_TOP, UI_PLATE_M_BOT },
    { UI_TAB_L_TOP, UI_TAB_L_BOT, UI_TAB_M_TOP, UI_TAB_M_BOT },
    { UI_TABON_L_TOP, UI_TABON_L_BOT, UI_TABON_M_TOP, UI_TABON_M_BOT },
};

void ui_put(u16* map, int tx, int ty, u16 entry) {
    if (tx < 0 || ty < 0 || tx >= 32 || ty >= 32)
        return;
    map[ty * 32 + tx] = entry;
}

void ui_tile(u16* map, int base, int tx, int ty, int tile, u16 flips) {
    ui_put(map, tx, ty, (base + tile) | flips | (UI_PAL << 12));
}

void ui_frame(u16* map, int base, int tx, int ty, int w, int h, int kind) {
    const u8* k = sFrames[kind];
    int x, y;
    for (y = 0; y < h; y++)
        for (x = 0; x < w; x++) {
            bool8 top = y == 0, bot = y == h - 1, left = x == 0, right = x == w - 1;
            u16 fl = (right ? UI_HF : 0) | (bot ? UI_VF : 0);
            int t;
            if ((top || bot) && (left || right)) {
                t = k[0];
            } else if (top || bot) {
                t = k[1];
                fl &= UI_VF;
            } else if (left || right) {
                t = k[2];
                fl &= UI_HF;
            } else {
                t = k[3];
                fl = 0;
            }
            if (t != 0xFF)
                ui_tile(map, base, tx + x, ty + y, t, fl);
        }
}

void ui_plate(u16* map, int base, int tx, int ty, int w, int kind) {
    const u8* k = sPlates[kind];
    int x;
    for (x = 0; x < w; x++) {
        bool8 end = x == 0 || x == w - 1;
        u16 fl = (x == w - 1) ? UI_HF : 0;
        ui_tile(map, base, tx + x, ty, end ? k[0] : k[2], fl);
        ui_tile(map, base, tx + x, ty + 1, end ? k[1] : k[3], fl);
    }
}

void ui_plate_px(Canvas* c, int x, int y, int w, int kind) {
    const u8* k = sPlates[kind];
    int i;
    for (i = 0; i < w; i++) {
        bool8 end = i == 0 || i == w - 1;
        int fl = (i == w - 1) ? 1 : 0;
        vwf_kit_px(c, x + i * 8, y, end ? k[0] : k[2], fl);
        vwf_kit_px(c, x + i * 8, y + 8, end ? k[1] : k[3], fl);
    }
}

int ui_plate_tiles(int w, int pad) {
    return (w + pad * 2 + 7) / 8;
}

void ui_backdrop_open(void) {
    static u16 kit[UI_TILE_COUNT * 16] EWRAM_BSS;
    const u16* tiles = ui_current_tiles();
    int i, n;
    /* clear pixels take the panel's navy */
    for (i = 0; i < UI_TILE_COUNT * 16; i++) {
        u16 w = tiles[i], o = 0;
        for (n = 0; n < 4; n++) {
            u16 v = (w >> (n * 4)) & 15;
            o |= (v ? v : UI_INK_NAVY) << (n * 4);
        }
        kit[i] = o;
    }
    dma3_copy32(tiles + UI_FILL * 16, CHARBLOCK(3), 32);
    dma3_copy32(kit, CHARBLOCK(3) + UI_BG3 * 16, UI_TILE_COUNT * 32);
    ui_backdrop_clear();
    ui_backdrop_flush();
}

void ui_backdrop_clear(void) {
    int i;
    for (i = 0; i < 32 * 32; i++)
        gBg3[i] = UI_PAL << 12;
    gBg3Dirty = 1;
}

void ui_backdrop_flush(void) {
    dma3_copy32(gBg3, SCREENBLOCK(BG3_SB), sizeof(gBg3));
}

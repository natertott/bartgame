/* BARTGAME: BG0 text, the message box, the HUD. BG0 is 32x32 tiles at
   screenblock 23, charblock 2, palette 15. Tiles 0..94 are the font
   (ASCII 32..126), then the HUD tiles. */
#include "gba.h"
#include "video.h"
#include "text.h"
#include "player.h"
#include "sound.h"
#include "assets.h"

#define BG0_MAP SCREENBLOCK(23)
#define PAL15 (15 << 12)

static u16 sBg0[32 * 32] ALIGN4;
static u8 sBg0Dirty;

void text_init(void) {
    dma3_copy32(font_tiles, CHARBLOCK(2), FONT_GLYPHS * 32);
    dma3_copy32(hud_tiles, CHARBLOCK(2) + FONT_GLYPHS * 16, HUD_TILE_COUNT * 32);
    bg0_clear();
}

void bg0_clear(void) {
    memset32(sBg0, 0, sizeof(sBg0));
    sBg0Dirty = 1;
}

void bg0_put(int tx, int ty, u16 tile) {
    if (tx < 0 || ty < 0 || tx >= 32 || ty >= 32)
        return;
    sBg0[ty * 32 + tx] = tile ? (tile | PAL15) : 0;
    sBg0Dirty = 1;
}

void bg0_print(int tx, int ty, const char* s) {
    while (*s) {
        char ch = *s++;
        if (ch >= 32 && ch < 127)
            bg0_put(tx, ty, ch == ' ' ? 0 : (ch - 32));
        tx++;
    }
}

void bg0_print_num(int tx, int ty, int n, int width) {
    char buf[8];
    int i = 7;
    buf[i] = 0;
    if (n < 0)
        n = 0;
    do {
        buf[--i] = '0' + n % 10;
        n /= 10;
    } while (n && i > 0);
    while (7 - i < width && i > 0)
        buf[--i] = ' ';
    bg0_print(tx, ty, &buf[i]);
}

void bg0_fill(int tx, int ty, int w, int h, u16 tile) {
    int x, y;
    for (y = 0; y < h; y++)
        for (x = 0; x < w; x++)
            bg0_put(tx + x, ty + y, tile);
}

/* a framed box: gold rule corners, dark fill */
void bg0_frame(int tx, int ty, int w, int h) {
    int x, y;
    for (y = 0; y < h; y++) {
        for (x = 0; x < w; x++) {
            u16 t = HT_BOX_FILL;
            u16 fl = 0;
            if (y == 0)
                t = (x == 0) ? HT_BOX_TL : (x == w - 1) ? HT_BOX_TL : HT_BOX_T;
            else if (y == h - 1)
                t = (x == 0) ? HT_BOX_BL : (x == w - 1) ? HT_BOX_BL : HT_BOX_B;
            else if (x == 0 || x == w - 1)
                t = HT_BOX_L;
            if (x == w - 1 && t != HT_BOX_T && t != HT_BOX_B)
                fl = ATTR1_HFLIP >> 2; /* 0x400: BG hflip */
            bg0_put(tx + x, ty + y, t | fl);
        }
    }
}

/* Push the shadow map at VBlank. */
void text_flush(void) {
    if (sBg0Dirty) {
        dma3_copy32(sBg0, BG0_MAP, sizeof(sBg0));
        sBg0Dirty = 0;
    }
}

/* ----------------------------------------------------------- text box -- */
#define TB_X 1
#define TB_Y 14
#define TB_W 28
#define TB_H 6
#define TB_COLS 25
#define TB_ROWS 3

static const char* sTbText;
static const char* sTbPos;   /* next char to type */
static u8 sTbActive, sTbCol, sTbRow, sTbWait, sTbDone;
static const char* const* sMenuOpts;
static s8 sMenuCount, sMenuCursor, sMenuResult;

static void tb_clear_lines(void) {
    bg0_fill(TB_X + 2, TB_Y + 1, TB_COLS, TB_ROWS, HT_BOX_FILL);
    sTbCol = 0;
    sTbRow = 0;
}

void textbox_open(const char* s) {
    sTbText = s;
    sTbPos = s;
    sTbActive = 1;
    sTbDone = 0;
    sTbWait = 0;
    bg0_frame(TB_X, TB_Y, TB_W, TB_H);
    tb_clear_lines();
}

bool8 textbox_active(void) {
    return sTbActive;
}

void textbox_close(void) {
    sTbActive = 0;
    sMenuCount = 0;
    bg0_fill(TB_X, TB_Y, TB_W, TB_H, 0);
}

/* A prompt on the first line, then up to two options with a cursor. */
void textbox_open_menu(const char* prompt, const char* const* options, int count) {
    textbox_open(prompt);
    sMenuOpts = options;
    sMenuCount = count > 2 ? 2 : count;
    sMenuCursor = 0;
    sMenuResult = -2;
}

int textbox_menu_result(void) {
    return sMenuResult;
}

static void menu_draw(void) {
    int i;
    for (i = 0; i < sMenuCount; i++) {
        bg0_put(TB_X + 2, TB_Y + 2 + i, (i == sMenuCursor) ? HT_CURSOR : HT_BOX_FILL);
        bg0_print(TB_X + 4, TB_Y + 2 + i, sMenuOpts[i]);
    }
}

static int word_len(const char* s) {
    int n = 0;
    while (s[n] && s[n] != ' ' && s[n] != '\n' && s[n] != '|')
        n++;
    return n;
}

/* Types two characters a frame. '|' is a page break, '\n' a line break.
   A advances a full page, B shows the whole page at once. */
void textbox_update(void) {
    int i;
    if (!sTbActive)
        return;
    if (sTbDone) {
        if (sMenuCount) {
            menu_draw();
            if (gKeysDown & KEY_UP) {
                sMenuCursor = (sMenuCursor + sMenuCount - 1) % sMenuCount;
                sfx_play(SFX_MENU);
            }
            if (gKeysDown & KEY_DOWN) {
                sMenuCursor = (sMenuCursor + 1) % sMenuCount;
                sfx_play(SFX_MENU);
            }
            if (gKeysDown & KEY_A)
                sMenuResult = sMenuCursor;
            if (gKeysDown & KEY_B)
                sMenuResult = -1;
            return;
        }
        /* waiting on the page */
        if (gFrame & 16)
            bg0_put(TB_X + TB_W - 3, TB_Y + TB_H - 2, HT_ARROW);
        else
            bg0_put(TB_X + TB_W - 3, TB_Y + TB_H - 2, HT_BOX_FILL);
        if (gKeysDown & (KEY_A | KEY_B)) {
            if (*sTbPos == '|')
                sTbPos++;
            if (*sTbPos == 0) {
                textbox_close();
                return;
            }
            tb_clear_lines();
            sTbDone = 0;
            sfx_play(SFX_TEXT);
        }
        return;
    }
    int per = (gKeysHeld & KEY_B) ? 40 : 2;
    for (i = 0; i < per; i++) {
        char ch = *sTbPos;
        if (ch == 0 || ch == '|') {
            sTbDone = 1;
            if (sMenuCount)
                sMenuResult = -2;
            return;
        }
        if (ch == '\n') {
            sTbPos++;
            sTbCol = 0;
            sTbRow++;
        } else if (ch == ' ' && sTbCol == 0) {
            sTbPos++;
        } else {
            /* wrap whole words */
            if (sTbCol > 0 && ch != ' ' && sTbCol + word_len(sTbPos) > TB_COLS) {
                sTbCol = 0;
                sTbRow++;
            }
            if (sTbRow >= TB_ROWS) {
                sTbDone = 1;
                return;
            }
            bg0_put(TB_X + 2 + sTbCol, TB_Y + 1 + sTbRow, ch == ' ' ? HT_BOX_FILL : (ch - 32));
            sTbCol++;
            sTbPos++;
            if ((i & 3) == 0 && ch != ' ')
                sfx_play(SFX_TEXT);
        }
        if (sTbRow >= TB_ROWS) {
            sTbDone = 1;
            return;
        }
    }
}

/* ---------------------------------------------------------------- HUD -- */
void hud_clear(void) {
    bg0_fill(0, 0, 32, 3, 0);
}

void hud_draw(void) {
    int i;
    int hearts = (gPl.hp_max + 7) / 8;
    int hp = gPl.hp;
    for (i = 0; i < hearts && i < 10; i++) {
        u16 t;
        if (hp >= 8)
            t = HT_HEART_FULL;
        else if (hp >= 4)
            t = HT_HEART_HALF;
        else
            t = HT_HEART_EMPTY;
        hp -= 8;
        bg0_put(1 + i, 1, t);
    }
    /* gilt, keys, bombs on the right */
    bg0_put(21, 1, HT_GILT);
    bg0_print_num(22, 1, gPl.gilt, 3);
    bg0_put(26, 1, HT_KEY);
    bg0_print_num(27, 1, gPl.keys, 1);
    if (gPl.items & ITEM_BOMBS) {
        bg0_put(13, 1, HT_BOMB);
        bg0_print_num(14, 1, gPl.bombs, 2);
    }
    /* the B item */
    bg0_put(17, 1, HT_ITEM_BOX);
    switch (gPl.bitem) {
        case BITEM_BOMBS: bg0_put(17, 1, HT_BOMB); break;
        case BITEM_LAMP: bg0_put(17, 1, HT_LAMP); break;
        case BITEM_CLOAK: bg0_put(17, 1, HT_CLOAK); break;
        default: break;
    }
}

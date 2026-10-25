/* BARTGAME: BG0 text, the message box with portraits, the shop, the HUD
   and the mini-map. BG0 is 32x32 tiles at screenblock 23, charblock 2,
   palette 15 (palette 14 is the same with gold ink). Tiles 0..94 are the
   font (ASCII 32..126), then the HUD tiles. */
#include "gba.h"
#include "video.h"
#include "text.h"
#include "player.h"
#include "sound.h"
#include "actor.h"
#include "objects.h"
#include "world.h"
#include "game.h"
#include "assets.h"

#define BG0_MAP SCREENBLOCK(23)
#define PAL15 (15 << 12)
#define PAL14 (14 << 12)
#define SWORD_TILE 32    /* player.c keeps the sword sheet here */
#define SHIELD_TILE 44   /* and the shield after it */
#define PORTRAIT_TILE 56 /* the speaker's face, 16 tiles */
#define MINIMAP_TILE OBJ_TILE_MINIMAP /* 16 OBJ tiles the CPU draws the map into */
/* the font again with the box's own dark fill behind every glyph, for
   text inside a box: nothing of the world shows through a letter */
#define FONT_BOX (FONT_GLYPHS + HUD_TILE_COUNT)
#define MENU_PAL 8
#define BOX_INK 0xE      /* the hud palette's box fill */

static u16 sBg0[32 * 32] ALIGN4;
static u8 sBg0Dirty;

void text_init(void) {
    int i, n;
    vu16* box = CHARBLOCK(2) + FONT_BOX * 16;
    dma3_copy32(font_tiles, CHARBLOCK(2), FONT_GLYPHS * 32);
    dma3_copy32(hud_tiles, CHARBLOCK(2) + FONT_GLYPHS * 16, HUD_TILE_COUNT * 32);
    for (i = 0; i < FONT_GLYPHS * 16; i++) {
        u16 w = font_tiles[i], o = 0;
        for (n = 0; n < 4; n++) {
            u16 v = (w >> (n * 4)) & 15;
            o |= (v ? v : BOX_INK) << (n * 4);
        }
        box[i] = o;
    }
    /* the menu's tiles after the box font: the carved frames draw with them */
    dma3_copy32(menu_tiles, CHARBLOCK(2) + MENU_TILE_BASE * 16, MENU_TILE_COUNT * 32);
    dma3_copy32(font_bold_tiles, CHARBLOCK(2) + FONT_BOLD_BASE * 16, FONT_GLYPHS * 32);
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

void bg0_put_pal(int tx, int ty, u16 tile, int pal) {
    if (tx < 0 || ty < 0 || tx >= 32 || ty >= 32)
        return;
    sBg0[ty * 32 + tx] = tile ? (tile | (pal << 12)) : 0;
    sBg0Dirty = 1;
}

/* opaque: the box font, spaces filled; else the plain font over the world */
static void bg0_print_pal(int tx, int ty, const char* s, u16 pal, bool8 opaque) {
    while (*s) {
        char ch = *s++;
        if (tx >= 0 && tx < 29 && ty >= 0 && ty < 32) {
            if (ch >= 32 && ch < 127) {
                if (opaque)
                    sBg0[ty * 32 + tx] = (FONT_BOX + ch - 32) | pal;
                else
                    sBg0[ty * 32 + tx] = (ch == ' ') ? 0 : ((ch - 32) | pal);
            }
        }
        tx++;
    }
    sBg0Dirty = 1;
}

void bg0_print(int tx, int ty, const char* s) {
    bg0_print_pal(tx, ty, s, PAL15, TRUE);
}

void bg0_print_gold(int tx, int ty, const char* s) {
    bg0_print_pal(tx, ty, s, PAL14, TRUE);
}

void bg0_print_hud(int tx, int ty, const char* s) {
    bg0_print_pal(tx, ty, s, PAL15, FALSE);
}

void bg0_print_big(int tx, int ty, const char* s, bool8 gold) {
    u16 pal = gold ? PAL14 : PAL15;
    while (*s) {
        char ch = *s++;
        if (tx >= 0 && tx < 30 && ty >= 0 && ty < 32 && ch >= 32 && ch < 127)
            sBg0[ty * 32 + tx] = (ch == ' ') ? 0 : ((FONT_BOLD_BASE + ch - 32) | pal);
        tx++;
    }
    sBg0Dirty = 1;
}

static void print_num(int tx, int ty, int n, int width, bool8 opaque) {
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
    bg0_print_pal(tx, ty, &buf[i], PAL15, opaque);
}

void bg0_print_num(int tx, int ty, int n, int width) {
    print_num(tx, ty, n, width, TRUE);
}

void bg0_print_num_hud(int tx, int ty, int n, int width) {
    print_num(tx, ty, n, width, FALSE);
}

void bg0_fill(int tx, int ty, int w, int h, u16 tile) {
    int x, y;
    for (y = 0; y < h; y++)
        for (x = 0; x < w; x++)
            bg0_put(tx + x, ty + y, tile);
}

/* a framed box: the UI board's gold frame round its navy fill (the
   right side is the left turned) */
void bg0_frame(int tx, int ty, int w, int h) {
    int x, y;
    for (y = 0; y < h; y++) {
        for (x = 0; x < w; x++) {
            u16 t, fl = 0;
            if (y == 0)
                t = (x == 0 || x == w - 1) ? HT_BOX_TL : HT_BOX_T;
            else if (y == h - 1)
                t = (x == 0 || x == w - 1) ? HT_BOX_BL : HT_BOX_B;
            else if (x == 0 || x == w - 1)
                t = HT_BOX_L;
            else
                t = HT_BOX_FILL;
            if (x == w - 1 && t != HT_BOX_T && t != HT_BOX_B && t != HT_BOX_FILL)
                fl = 0x400;
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
#define TB_ROWS 3

static const char* sTbText;
static const char* sTbPos;   /* next char to type */
u8 gTbActive; /* probes read it */
static u8 sTbCol, sTbRow, sTbWait, sTbDone;
static const char* const* sMenuOpts;
static s8 sMenuCount, sMenuCursor, sMenuResult;
static s8 sTbPortrait = -1;

static int tb_text_x(void) {
    return TB_X + (sTbPortrait >= 0 ? 6 : 2);
}

static int tb_text_y(void) {
    return TB_Y + (sTbPortrait >= 0 ? 2 : 1);
}

static int tb_cols(void) {
    return sTbPortrait >= 0 ? 21 : 25;
}

static void tb_clear_lines(void) {
    bg0_fill(tb_text_x(), tb_text_y(), tb_cols(), TB_ROWS, HT_BOX_FILL);
    sTbCol = 0;
    sTbRow = 0;
}

/* A speaker's name in gold over the text, their portrait at the left. */
void textbox_open_named(const char* name, int portrait, const char* s) {
    sTbPortrait = portrait;
    if (portrait >= 0) {
        /* only the speaker's face is resident, in its own 16 tiles, and
           each face has a palette of its own */
        const SpriteSheet* sh = &sheets[SHEET_PORTRAIT];
        dma3_copy32(sh->tiles + portrait * sh->frame_tiles * 16, OBJ_TILE(PORTRAIT_TILE), sh->frame_tiles * 32);
        pal_set_obj(PAL_OBJ_PORTRAIT, &pal_portrait[portrait * 16]);
    }
    sTbText = s;
    sTbPos = s;
    gTbActive = 1;
    sTbDone = 0;
    sTbWait = 0;
    sMenuCount = 0;
    bg0_frame(TB_X, TB_Y, TB_W, TB_H);
    if (name)
        bg0_print_gold(tb_text_x(), TB_Y + 1, name);
    tb_clear_lines();
}

void textbox_open(const char* s) {
    textbox_open_named(NULL, -1, s);
}

bool8 textbox_active(void) {
    return gTbActive;
}

void textbox_close(void) {
    gTbActive = 0;
    sMenuCount = 0;
    sTbPortrait = -1;
    bg0_fill(TB_X, TB_Y, TB_W, TB_H, 0);
}

void textbox_draw(void) {
    if (!gTbActive || sTbPortrait < 0)
        return;
    draw_sprite(TB_X * 8 + 8, TB_Y * 8 + 8, SHEET_PORTRAIT, PORTRAIT_TILE, 0, 0, 0, PAL_OBJ_PORTRAIT);
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
        bg0_put(tb_text_x(), tb_text_y() + 1 + i, (i == sMenuCursor) ? HT_CURSOR : HT_BOX_FILL);
        bg0_print(tb_text_x() + 2, tb_text_y() + 1 + i, sMenuOpts[i]);
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
    if (!gTbActive)
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
    int cols = tb_cols();
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
            if (sTbCol > 0 && ch != ' ' && sTbCol + word_len(sTbPos) > cols) {
                sTbCol = 0;
                sTbRow++;
            }
            if (sTbRow >= TB_ROWS) {
                sTbDone = 1;
                return;
            }
            bg0_put(tb_text_x() + sTbCol, tb_text_y() + sTbRow, FONT_BOX + ch - 32);
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

/* --------------------------------------------------------------- shop -- */
#define SH_X 1
#define SH_Y 5
#define SH_W 28
#define SH_H 15
#define SH_DESC (SH_Y + 10) /* the description rows, under three wares */

static const ShopItem* sShopItems;
static u8 sShopCount, sShopCursor, sShopActive;
static s8 sShopResult;
static u16 sShopIconTile;

static void shop_refresh(void) {
    int i;
    for (i = 0; i < sShopCount; i++)
        bg0_put(SH_X + 3, SH_Y + 3 + i * 2, (i == sShopCursor) ? HT_CURSOR : HT_BOX_FILL);
    bg0_fill(SH_X + 2, SH_DESC, SH_W - 4, 2, HT_BOX_FILL);
    bg0_print(SH_X + 2, SH_DESC, sShopItems[sShopCursor].desc1);
    bg0_print(SH_X + 2, SH_DESC + 1, sShopItems[sShopCursor].desc2);
}

void shop_open(const char* title, const ShopItem* items, int n) {
    int i;
    sShopItems = items;
    sShopCount = n > 3 ? 3 : n;
    sShopCursor = 0;
    sShopResult = -2;
    sShopActive = 1;
    sShopIconTile = items_sheet_tile();
    bg0_frame(SH_X, SH_Y, SH_W, SH_H);
    bg0_print_gold(SH_X + 2, SH_Y + 1, title);
    for (i = 0; i < 26; i++)
        bg0_put(SH_X + 1 + i, SH_Y + 2, HT_RULE);
    for (i = 0; i < sShopCount; i++) {
        int row = SH_Y + 3 + i * 2;
        bg0_print(SH_X + 7, row, items[i].name);
        bg0_put(SH_X + 21, row, HT_GILT);
        bg0_print_num(SH_X + 22, row, items[i].price, 3);
    }
    for (i = 0; i < 26; i++)
        bg0_put(SH_X + 1 + i, SH_DESC - 1, HT_RULE);
    bg0_print(SH_X + 2, SH_Y + SH_H - 2, "A: buy  B: leave");
    bg0_put(SH_X + 20, SH_Y + SH_H - 2, HT_GILT);
    bg0_print_num(SH_X + 21, SH_Y + SH_H - 2, gPl.gilt, 4);
    shop_refresh();
}

void shop_update(void) {
    if (!sShopActive)
        return;
    if ((gKeysDown & KEY_UP) && sShopCursor > 0) {
        sShopCursor--;
        sfx_play(SFX_MENU);
        shop_refresh();
    }
    if ((gKeysDown & KEY_DOWN) && sShopCursor + 1 < sShopCount) {
        sShopCursor++;
        sfx_play(SFX_MENU);
        shop_refresh();
    }
    if (gKeysDown & KEY_A)
        sShopResult = sShopCursor;
    if (gKeysDown & KEY_B)
        sShopResult = -1;
}

void shop_draw(void) {
    int i;
    if (!sShopActive)
        return;
    for (i = 0; i < sShopCount; i++)
        draw_sprite((SH_X + 4) * 8 + 2, (SH_Y + 3 + i * 2) * 8 - 4, SHEET_ITEMS, sShopIconTile, sShopItems[i].icon, 0, 0, PAL_OBJ_ITEMS);
}

void shop_close(void) {
    sShopActive = 0;
    bg0_fill(SH_X, SH_Y, SH_W, SH_H, 0);
}

int shop_result(void) {
    return sShopResult;
}

bool8 shop_active(void) {
    return sShopActive;
}

/* ---------------------------------------------------------------- HUD -- */
void hud_clear(void) {
    bg0_fill(0, 0, 32, 3, 0);
}

static void slot(int tx, int lit) {
    bg0_put(tx, 0, lit ? HT_SLOT_LIT_TL : HT_SLOT_TL);
    bg0_put(tx + 1, 0, lit ? HT_SLOT_LIT_TR : HT_SLOT_TR);
    bg0_put(tx, 1, lit ? HT_SLOT_LIT_BL : HT_SLOT_BL);
    bg0_put(tx + 1, 1, lit ? HT_SLOT_LIT_BR : HT_SLOT_BR);
}

/* the icon of what a button holds, as a sprite over the slot */
void hud_equip_icon(int eq, int px, int py, int prio) {
    switch (eq) {
        case EQ_SWORD: draw_sprite(px, py, SHEET_SWORD, SWORD_TILE, F_SWORD_BLADE_S, 0, prio, PAL_OBJ_GEAR); break;
        case EQ_BOMBS: draw_sprite(px, py, SHEET_ITEMS, items_sheet_tile(), F_ITEMS_BOMBS, 0, prio, PAL_OBJ_ITEMS); break;
        case EQ_LAMP: draw_sprite(px, py, SHEET_ITEMS, items_sheet_tile(), F_ITEMS_LAMP, 0, prio, PAL_OBJ_ITEMS); break;
        case EQ_CLOAK: draw_sprite(px, py, SHEET_ITEMS, items_sheet_tile(), F_ITEMS_CLOAK, 0, prio, PAL_OBJ_ITEMS); break;
        case EQ_SHIELD: draw_sprite(px, py, SHEET_SHIELD, SHIELD_TILE, F_SHIELD_FRONT, 0, prio, PAL_OBJ_GEAR); break;
        case EQ_BOW: draw_sprite(px, py, SHEET_ITEMS, items_sheet_tile(), F_ITEMS_BOW, 0, prio, PAL_OBJ_ITEMS); break;
        case EQ_HUBCAP: draw_sprite(px, py, SHEET_ITEMS, items_sheet_tile(), F_ITEMS_HUBCAP, 0, prio, PAL_OBJ_ITEMS); break;
        default: break;
    }
}

static const u8 sSlotX[SLOT_COUNT] = { 12, 15, 18 };
static const u16 sSlotBtn[SLOT_COUNT] = { HT_BTN_A, HT_BTN_B, HT_BTN_L };

static void hud_bar(void);

void hud_draw(void) {
    hud_bar();
    /* the mini-map at the top right */
    {
        OamEntry* o = oam_alloc();
        if (o) {
            o->attr0 = ATTR0_Y(0) | ATTR0_SQUARE;
            o->attr1 = ATTR1_X(206) | ATTR1_SIZE(2);
            o->attr2 = ATTR2_TILE(MINIMAP_TILE) | ATTR2_PRIO(0) | ATTR2_PAL(PAL_OBJ_UI);
        }
    }
}

void hud_draw_bar(void) {
    hud_bar();
}

static void hud_bar(void) {
    int i;
    int hearts = (gPl.hp_max + 7) / 8;
    int hp = gPl.hp;
    /* hearts along the top, the purse and the keys under them */
    for (i = 0; i < hearts && i < 10; i++) {
        u16 t;
        if (hp >= 8)
            t = HT_HEART_FULL;
        else if (hp >= 4)
            t = HT_HEART_HALF;
        else
            t = HT_HEART_EMPTY;
        hp -= 8;
        bg0_put(1 + i, 0, t);
    }
    bg0_put(1, 1, HT_GILT);
    bg0_print_num_hud(2, 1, gPl.gilt, 3);
    bg0_put(6, 1, HT_KEY);
    bg0_print_num_hud(7, 1, gPl.keys, 1);
    /* the three buttons and what they hold, then R's hand */
    for (i = 0; i < SLOT_COUNT; i++) {
        int eq = gPl.equip[i];
        bg0_put(sSlotX[i] - 1, 0, sSlotBtn[i]);
        slot(sSlotX[i], eq != EQ_NONE);
        if (eq == EQ_BOMBS)
            bg0_print_num_hud(sSlotX[i], 2, gPl.bombs, 2);
        else if (eq == EQ_BOW)
            bg0_print_num_hud(sSlotX[i], 2, gPl.arrows, 2);
        else
            bg0_print_hud(sSlotX[i], 2, "  ");
        hud_equip_icon(eq, sSlotX[i] * 8, 0, 0);
    }
    bg0_put(20, 0, HT_BTN_R);
    bg0_put(21, 0, HT_HAND);
}

/* ----------------------------------------------------------- mini-map -- */
/* A 32x32 sprite drawn by the CPU: a parchment in a gold frame, the five
   by five cells of the wood, green where seen, gold at the Heart, a red
   dot where the hero stands (blue at the entry while he is below). */
static u16 sMapTiles[16 * 16];

void minimap_render(void) {
    static u8 buf[32 * 32];
    int x, y, i;
    for (y = 0; y < 32; y++) {
        for (x = 0; x < 32; x++) {
            u8 col = 2;
            int edge = (x == 0 || y == 0 || x == 31 || y == 31);
            int inner = (x == 1 || y == 1 || x == 30 || y == 30);
            if (edge)
                col = 4;
            else if (inner)
                col = 5;
            else if (x == 2 || y == 2 || x == 29 || y == 29)
                col = 3;
            if ((x < 2 && y < 2) || (x > 29 && y < 2) || (x < 2 && y > 29) || (x > 29 && y > 29))
                col = 0;
            buf[y * 32 + x] = col;
        }
    }
    for (i = 0; i < CELLS; i++) {
        Cell* c = &gWorld.cells[i];
        int cx = 4 + (i % MAZE_W) * 5, cy = 4 + (i / MAZE_W) * 5;
        u8 col = 3;
        if (c->flags & CF_VISITED)
            col = (i == gWorld.goal) ? 5 : 8;
        for (y = 0; y < 4; y++)
            for (x = 0; x < 4; x++)
                buf[(cy + y) * 32 + cx + x] = col;
        if (col == 8) {
            buf[cy * 32 + cx] = 7;
            buf[(cy + 3) * 32 + cx + 3] = 7;
        }
        if ((gGame.area == AREA_FOREST && i == gGame.cell) || (gGame.area != AREA_FOREST && i == gWorld.entry)) {
            u8 dot = (gGame.area == AREA_FOREST) ? 9 : 0xb;
            buf[(cy + 1) * 32 + cx + 1] = dot;
            buf[(cy + 1) * 32 + cx + 2] = dot;
            buf[(cy + 2) * 32 + cx + 1] = dot;
            buf[(cy + 2) * 32 + cx + 2] = dot;
            buf[(cy + 1) * 32 + cx + 1] = 0xa;
        }
    }
    /* pack to 4bpp tiles, 4x4 tiles in row order */
    for (i = 0; i < 16; i++) {
        int tx = (i % 4) * 8, ty = (i / 4) * 8;
        for (y = 0; y < 8; y++) {
            for (x = 0; x < 8; x += 4) {
                const u8* p = &buf[(ty + y) * 32 + tx + x];
                sMapTiles[i * 16 + y * 2 + x / 4] = ui_ink[p[0]] | (ui_ink[p[1]] << 4) | (ui_ink[p[2]] << 8) | (ui_ink[p[3]] << 12);
            }
        }
    }
    dma3_copy32(sMapTiles, OBJ_TILE(MINIMAP_TILE), sizeof(sMapTiles));
}

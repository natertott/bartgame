/* BARTGAME: BG0, the layer over the world: the HUD, the message box
   with its speaker's face and name plate, and the shop. BG0 is 32x32
   tiles at screenblock 23 in charblock 2, whose tiles stay under 384
   (screenblocks 22 and 23 follow them): 0 is clear, 1..10 the HUD's
   figures, then the HUD's tiles, then the UI kit, then the pool the
   words are set into a pixel at a time (vwf.c). */
#include "gba.h"
#include "video.h"
#include "text.h"
#include "ui.h"
#include "room.h"
#include "player.h"
#include "sound.h"
#include "actor.h"
#include "objects.h"
#include "world.h"
#include "game.h"
#include "assets.h"

#define BG0_MAP SCREENBLOCK(23)
#define PAL15 (15 << 12)
#define DIGIT_TILE 1
#define POOL_FIRST (UI_BG0 + UI_TILE_COUNT)
#define POOL_END 384
#define SWORD_TILE 32    /* player.c keeps the sword sheet here */
#define SHIELD_TILE 44   /* and the shield after it */
#define MINIMAP_TILE OBJ_TILE_MINIMAP /* 16 OBJ tiles the CPU draws the map into */

#if HUD_TILE_BASE + HUD_TILE_COUNT > UI_BG0
#error "the HUD's tiles run into the kit's"
#endif

static u16 sBg0[32 * 32] ALIGN4;
static u8 sBg0Dirty;

void text_init(void) {
    const SpriteSheet* marks = &sheets[SHEET_UIMARKS];
    dma3_fill32(0, CHARBLOCK(2), 32);
    dma3_copy32(font_tiles + ('0' - ' ') * 16, CHARBLOCK(2) + DIGIT_TILE * 16, 10 * 32);
    dma3_copy32(hud_tiles, CHARBLOCK(2) + HUD_TILE_BASE * 16, HUD_TILE_COUNT * 32);
    dma3_copy32(ui_tiles, CHARBLOCK(2) + UI_BG0 * 16, UI_TILE_COUNT * 32);
    /* the marks over the boxes stay resident above the sheets */
    dma3_copy32(marks->tiles, OBJ_TILE(OBJ_TILE_UI), marks->tile_count * 32);
    bg0_pool_reset();
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

void bg0_fill(int tx, int ty, int w, int h, u16 tile) {
    int x, y;
    for (y = 0; y < h; y++)
        for (x = 0; x < w; x++)
            bg0_put(tx + x, ty + y, tile);
}

u16* bg0_map(void) {
    sBg0Dirty = 1;
    return sBg0;
}

void bg0_print_num_hud(int tx, int ty, int n, int width) {
    char buf[8];
    int i;
    vwf_num(buf, n, width);
    for (i = 0; buf[i]; i++)
        bg0_put(tx + i, ty, buf[i] == ' ' ? 0 : DIGIT_TILE + buf[i] - '0');
}

void bg0_pool_reset(void) {
    vwf_pool(POOL_FIRST, POOL_END);
}

bool8 bg0_canvas(Canvas* c, int tx, int ty, int tw, int th) {
    if (!vwf_canvas(c, tw, th))
        return FALSE;
    vwf_clear(c, 0);
    vwf_map(c, sBg0, tx, ty, UI_PAL);
    sBg0Dirty = 1;
    return TRUE;
}

void bg0_show(const Canvas* c, int tx, int ty, bool8 on) {
    if (on)
        vwf_map(c, sBg0, tx, ty, UI_PAL);
    else
        bg0_fill(tx, ty, c->tw, c->th, 0);
    sBg0Dirty = 1;
}

void bg0_plate(Canvas* c, int tx, int ty, const char* s, int ink, bool8 edge) {
    int w = vwf_width(s), n = ui_plate_tiles(w, 6), i;
    if (!bg0_canvas(c, tx, ty, n, 2))
        return;
    for (i = 0; i < n; i++) {
        bool8 end = i == 0 || i == n - 1;
        int fl = (i == n - 1) ? 1 : 0;
        if (edge)
            vwf_kit(c, i, 1, UI_PANEL_T, 0, FALSE); /* the box's edge under the plate's foot */
        vwf_kit(c, i, 0, end ? UI_PLATE_L_TOP : UI_PLATE_M_TOP, fl, TRUE);
        vwf_kit(c, i, 1, end ? UI_PLATE_L_BOT : UI_PLATE_M_BOT, fl, TRUE);
    }
    vwf_text(c, (n * 8 - w) / 2, 4, s, ink);
}

/* Push the shadow maps at VBlank. */
void text_flush(void) {
    if (sBg0Dirty) {
        dma3_copy32(sBg0, BG0_MAP, sizeof(sBg0));
        sBg0Dirty = 0;
    }
    if (gBg3Dirty) {
        ui_backdrop_flush();
        gBg3Dirty = 0;
    }
}

/* -------------------------------------------------------------- face -- */
void face_load(int face) {
    const SpriteSheet* sh = &sheets[SHEET_FACE];
    dma3_copy32(sh->tiles + face * sh->frame_tiles * 16, OBJ_TILE(OBJ_TILE_FACE), sh->frame_tiles * 32);
    pal_set_obj(PAL_OBJ_PORTRAIT, &pal_face[face * 16]);
}

void face_draw(int x, int y, int prio) {
    draw_sprite(x, y, SHEET_FACE, OBJ_TILE_FACE, 0, 0, prio, PAL_OBJ_PORTRAIT);
}

/* ----------------------------------------------------------- text box -- */
/* A navy box in the gold frame along the foot of the screen; with a
   speaker, their face at the left behind a divider and their name on a
   plate over the top edge. The words type into a canvas: two letters a
   frame, wrapped by their width; '|' ends a page, '\n' a line. */
#define TB_X 1
#define TB_Y 13
#define TB_W 28
#define TB_H 7
#define TB_DIV 7   /* the divider's column, after the face */
#define TB_LINES 3
#define TB_PITCH 13
#define TB_TOP 2   /* the first line in the canvas */
#define FACE_X 12
#define FACE_Y 108

static Canvas sTbCanvas, sTbName;
static const char* sTbText;
static const char* sTbPos; /* the next letter to type */
u8 gTbActive;              /* probes read it */
static u8 sTbLine, sTbDone, sTbInk, sTbDirty;
static u8 sTbX0, sTbW;     /* where the lines start in the canvas, how wide they run */
static s16 sTbX;
static s8 sTbFace = -1;

static void tb_page(void) {
    vwf_clear(&sTbCanvas, UI_INK_NAVY);
    sTbLine = 0;
    sTbX = sTbX0;
    sTbDirty = 1;
}

static void tb_newline(void) {
    sTbLine++;
    sTbX = sTbX0;
    if (sTbLine >= TB_LINES)
        sTbDone = 1;
}

void textbox_open_named(const char* name, int face, const char* s) {
    u16* m = bg0_map();
    int y, ctx = face >= 0 ? TB_DIV + 1 : TB_X + 1;
    sTbFace = face;
    if (face >= 0)
        face_load(face);
    sTbText = s;
    sTbPos = s;
    gTbActive = 1;
    sTbDone = 0;
    sTbInk = UI_INK_CREAM;
    bg0_pool_reset();
    bg0_fill(0, TB_Y - 1, 32, TB_H + 1, 0);
    ui_frame(m, UI_BG0, TB_X, TB_Y, TB_W, TB_H, FR_PANEL);
    if (face >= 0) {
        ui_tile(m, UI_BG0, TB_DIV, TB_Y, UI_DIV_T, 0);
        for (y = TB_Y + 1; y < TB_Y + TB_H - 1; y++)
            ui_tile(m, UI_BG0, TB_DIV, y, UI_DIV_M, 0);
        ui_tile(m, UI_BG0, TB_DIV, TB_Y + TB_H - 1, UI_DIV_T, UI_VF);
    }
    if (name) {
        bg0_plate(&sTbName, ctx, TB_Y - 1, name, UI_INK_GOLD, TRUE);
        vwf_flush(&sTbName, FALSE);
    }
    sTbX0 = face >= 0 ? 6 : 4;
    sTbW = face >= 0 ? 140 : 192;
    vwf_canvas(&sTbCanvas, TB_X + TB_W - 1 - ctx, TB_H - 2);
    vwf_map(&sTbCanvas, m, ctx, TB_Y + 1, UI_PAL);
    tb_page();
}

void textbox_open(const char* s) {
    textbox_open_named(NULL, -1, s);
}

bool8 textbox_active(void) {
    return gTbActive;
}

void textbox_close(void) {
    gTbActive = 0;
    sTbFace = -1;
    bg0_fill(0, TB_Y - 1, 32, TB_H + 1, 0);
}

/* the face, and the arrow that bobs while the page waits; first in OAM,
   for between sprites the order rules and not the priority */
void textbox_draw(void) {
    static const u8 bob[4] = { 0, 1, 2, 1 };
    if (!gTbActive)
        return;
    if (sTbDone)
        draw_sprite(214, 143 + bob[(gFrame >> 3) & 3], SHEET_UIMARKS, OBJ_TILE_UI, F_UIMARKS_NEXT, 0, 0, PAL_OBJ_UIKIT);
    if (sTbFace >= 0)
        face_draw(FACE_X, FACE_Y, 0);
}

/* the width of the word at s, to the next space or break */
static int word_px(const char* s) {
    int w = 0;
    while (*s && *s != ' ' && *s != '\n' && *s != '|')
        w += vwf_advance((u8)*s++);
    return w;
}

/* A turns a full page, B shows the rest of the page at once */
void textbox_update(void) {
    int n, per;
    if (!gTbActive)
        return;
    if (sTbDone) {
        if (gKeysDown & (KEY_A | KEY_B)) {
            if (*sTbPos == '|')
                sTbPos++;
            while (*sTbPos == ' ' || *sTbPos == '\n')
                sTbPos++;
            if (*sTbPos == 0) {
                textbox_close();
                return;
            }
            tb_page();
            sTbDone = 0;
            sfx_play(SFX_TEXT);
        }
    } else {
        per = (gKeysHeld & KEY_B) ? 40 : 2;
        for (n = 0; n < per && !sTbDone;) {
            u8 ch = (u8)*sTbPos;
            if (ch == 0 || ch == '|') {
                sTbDone = 1;
                break;
            }
            sTbPos++;
            if (ch == '\n') {
                tb_newline();
                continue;
            }
            if (ch < ' ') {
                sTbInk = vwf_ink(ch, UI_INK_CREAM);
                continue;
            }
            n++;
            if (ch == ' ') {
                if (sTbX > sTbX0)
                    sTbX += VWF_SPACE;
                continue;
            }
            /* a word that would run past the edge starts the next line */
            if (sTbX > sTbX0 && (sTbPos - 1 == sTbText || (u8)sTbPos[-2] <= ' ') &&
                sTbX + word_px(sTbPos - 1) - 1 > sTbX0 + sTbW) {
                tb_newline();
                if (sTbDone) {
                    sTbPos--;
                    break;
                }
            }
            sTbX += vwf_glyph(&sTbCanvas, sTbX, TB_TOP + sTbLine * TB_PITCH, ch, sTbInk);
            sTbDirty = 1;
            if ((n & 3) == 1)
                sfx_play(SFX_TEXT);
        }
    }
    if (sTbDirty) {
        vwf_flush(&sTbCanvas, FALSE);
        sTbDirty = 0;
    }
}

/* --------------------------------------------------------------- shop -- */
/* The whole screen, on BG3's backdrop with the words on BG0 over it:
   the keeper's face in a gold frame and their words in a bubble, the
   wares in rows down the left with the purse on the list's edge, the
   chosen one at the right. The world is not drawn behind it. */
#define SH_FACE_X 12
#define SH_FACE_Y 12
#define SH_ROW_X 3
#define SH_ROW_W 13
#define SH_ROW_Y(i) (9 + (i) * 3)
#define SH_ICON_X 27
#define SH_DET_X 17

static const ShopItem* sShopItems;
static u8 sShopCount, sShopCursor, sShopActive, sShopFace;
static s8 sShopResult;
static u16 sShopIconTile;
static Canvas sShopRows[3], sShopName, sShopDesc, sShopPurse, sShopBubble, sShopHints;

static void shop_row(int i) {
    const ShopItem* it = &sShopItems[i];
    Canvas* c = &sShopRows[i];
    char buf[8];
    int w;
    ui_frame(gBg3, UI_BG3, SH_ROW_X, SH_ROW_Y(i), SH_ROW_W, 2, i == sShopCursor ? FR_SROW : FR_ROW);
    gBg3Dirty = 1;
    vwf_clear(c, 0);
    vwf_text(c, 6, 4, it->name, UI_INK_CREAM);
    vwf_num(buf, it->price, 0);
    w = vwf_width(buf);
    vwf_kit_px(c, 75 - w, 3, UI_COIN, 0);
    vwf_text(c, 85 - w, 4, buf, gPl.gilt >= it->price ? UI_INK_CREAM : UI_INK_RED);
}

static void shop_detail(void) {
    const ShopItem* it = &sShopItems[sShopCursor];
    char buf[24];
    int n;
    vwf_clear(&sShopName, 0);
    vwf_text(&sShopName, 2, 2, it->name, UI_INK_GOLD);
    vwf_clear(&sShopDesc, 0);
    n = vwf_block(&sShopDesc, 0, 0, 82, 10, it->desc, UI_INK_CREAM, 3);
    if (it->effect)
        vwf_block(&sShopDesc, 0, n * 10 + 1, 82, 10, it->effect, UI_INK_RED, 4 - n);
    if (it->own != OWN_NONE) {
        int x = vwf_text(&sShopDesc, 0, 41, "Owned: ", UI_INK_CREAM);
        vwf_text(&sShopDesc, x, 41, vwf_num(buf, it->own == OWN_BOMBS ? gPl.bombs : gPl.arrows, 0), UI_INK_HIGH);
    }
}

void shop_open(int face, const char* greet, const ShopItem* items, int n) {
    int i, x;
    char buf[8];
    sShopItems = items;
    sShopCount = n > 3 ? 3 : n;
    sShopCursor = 0;
    sShopResult = -2;
    sShopActive = 1;
    sShopFace = face;
    sShopIconTile = items_sheet_tile();
    face_load(face);
    video_show(DCNT_BG0 | DCNT_BG3 | DCNT_OBJ);
    bg0_clear();
    bg0_pool_reset();
    ui_backdrop_open();
    ui_frame(gBg3, UI_BG3, 0, 0, 30, 20, FR_PANEL);
    /* the keeper's face, and their words in a bubble that points at it */
    ui_frame(gBg3, UI_BG3, 1, 1, 7, 7, FR_SEL);
    ui_frame(gBg3, UI_BG3, 10, 1, 19, 5, FR_BUB);
    ui_tile(gBg3, UI_BG3, 9, 3, UI_BUB_TAIL, 0);
    ui_tile(gBg3, UI_BG3, 10, 3, UI_BUB_JOIN, 0);
    bg0_canvas(&sShopBubble, 11, 1, 17, 5);
    vwf_block(&sShopBubble, 2, 4, 130, 10, greet, UI_INK_BROWN, 3);
    /* the wares, the purse on the list's top edge, the buttons at its foot */
    ui_frame(gBg3, UI_BG3, 1, 8, 16, 11, FR_PANEL);
    ui_plate(gBg3, UI_BG3, 11, 7, 5, PL_PLATE);
    bg0_canvas(&sShopPurse, 11, 7, 5, 2);
    vwf_num(buf, gPl.gilt, 0);
    x = (40 - 10 - vwf_width(buf)) / 2;
    vwf_kit_px(&sShopPurse, x, 3, UI_COIN, 0);
    vwf_text(&sShopPurse, x + 10, 4, buf, UI_INK_CREAM);
    for (i = 0; i < sShopCount; i++)
        bg0_canvas(&sShopRows[i], SH_ROW_X + 2, SH_ROW_Y(i), SH_ROW_W - 2, 2);
    ui_tile(gBg3, UI_BG3, 3, 17, UI_BADGE_A, 0);
    ui_tile(gBg3, UI_BG3, 8, 17, UI_BADGE_B, 0);
    bg0_canvas(&sShopHints, 4, 17, 12, 2);
    vwf_text(&sShopHints, 2, 1, "Buy", UI_INK_CREAM);
    vwf_text(&sShopHints, 42, 1, "Leave", UI_INK_CREAM);
    /* the chosen ware */
    ui_frame(gBg3, UI_BG3, SH_DET_X, 8, 12, 11, FR_PANEL);
    ui_tile(gBg3, UI_BG3, SH_DET_X + 1, 11, UI_RULE_END, UI_HF);
    for (i = SH_DET_X + 2; i < SH_DET_X + 10; i++)
        ui_tile(gBg3, UI_BG3, i, 11, UI_RULE, 0);
    ui_tile(gBg3, UI_BG3, SH_DET_X + 10, 11, UI_RULE_END, 0);
    bg0_canvas(&sShopName, SH_DET_X + 3, 9, 9, 2);
    bg0_canvas(&sShopDesc, SH_DET_X + 1, 12, 11, 7);
    for (i = 0; i < sShopCount; i++)
        shop_row(i);
    shop_detail();
    vwf_flush(&sShopBubble, TRUE);
    vwf_flush(&sShopPurse, TRUE);
    vwf_flush(&sShopHints, TRUE);
    for (i = 0; i < sShopCount; i++)
        vwf_flush(&sShopRows[i], TRUE);
    vwf_flush(&sShopName, TRUE);
    vwf_flush(&sShopDesc, TRUE);
    gBg3Dirty = 1;
}

void shop_update(void) {
    int old = sShopCursor;
    if (!sShopActive)
        return;
    if ((gKeysDown & KEY_UP) && sShopCursor > 0)
        sShopCursor--;
    if ((gKeysDown & KEY_DOWN) && sShopCursor + 1 < sShopCount)
        sShopCursor++;
    if (sShopCursor != old) {
        sfx_play(SFX_MENU);
        shop_row(old);
        shop_row(sShopCursor);
        shop_detail();
        vwf_flush(&sShopRows[old], FALSE);
        vwf_flush(&sShopRows[sShopCursor], FALSE);
        vwf_flush(&sShopName, FALSE);
        vwf_flush(&sShopDesc, FALSE);
    }
    if (gKeysDown & KEY_A)
        sShopResult = sShopCursor;
    if (gKeysDown & KEY_B)
        sShopResult = -1;
}

void shop_draw(void) {
    static const u8 nudge[4] = { 0, 1, 2, 1 };
    int i;
    if (!sShopActive)
        return;
    draw_sprite(14 + nudge[(gFrame >> 3) & 3], SH_ROW_Y(sShopCursor) * 8 + 4, SHEET_UIMARKS, OBJ_TILE_UI, F_UIMARKS_PICK, 0, 0, PAL_OBJ_UIKIT);
    face_draw(SH_FACE_X, SH_FACE_Y, 0);
    for (i = 0; i < sShopCount; i++)
        draw_sprite(SH_ICON_X, SH_ROW_Y(i) * 8, SHEET_ITEMS, sShopIconTile, sShopItems[i].icon, 0, 0, PAL_OBJ_ITEMS);
    draw_sprite(SH_DET_X * 8 + 6, 70, SHEET_ITEMS, sShopIconTile, sShopItems[sShopCursor].icon, 0, 0, PAL_OBJ_ITEMS);
}

void shop_close(void) {
    sShopActive = 0;
    bg0_clear();
    room_render(); /* the room maps get their block back */
    video_show(DCNT_BG0 | DCNT_BG1 | DCNT_BG2 | DCNT_OBJ);
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
            bg0_fill(sSlotX[i], 2, 2, 1, 0);
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

/* BARTGAME: BG0, the layer over the world: the HUD, the message box
   with its speaker's face and name plate, and the shop. BG0 is 32x32
   tiles at screenblock 23 in charblock 2, whose tiles stay under 384
   (screenblocks 22 and 23 follow them): 0 is clear, then the hearts and
   R's hand, then the UI kit, then the HUD's purse, then the pool the
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
#define PAL_HUD (PAL_SLOT_HUD << 12) /* the hearts, R's hand */
#define HUD_PURSE_TILE (UI_BG0 + UI_TILE_COUNT) /* the purse's own tiles */
#define HUD_PURSE_TW 12
#define HUD_VITALS_TH 3
/* a box over the world keeps the HUD's purse; the pages that fill the
   screen take its tiles too, and the purse is set again after them */
#define POOL_FULL HUD_PURSE_TILE
#define POOL_FIRST (HUD_PURSE_TILE + HUD_PURSE_TW * HUD_VITALS_TH)
#define POOL_END 384

#if HUD_TILE_BASE + HUD_TILE_COUNT > UI_BG0
#error "the HUD's tiles run into the kit's"
#endif

static u16 sBg0[32 * 32] ALIGN4;
static u8 sBg0Dirty;

static void hud_init(void);
static void hud_stale(void);

void text_init(void) {
    const SpriteSheet* marks = &sheets[SHEET_UIMARKS];
    dma3_fill32(0, CHARBLOCK(2), 32);
    dma3_copy32(hud_tiles, CHARBLOCK(2) + HUD_TILE_BASE * 16, HUD_TILE_COUNT * 32);
    dma3_copy32(ui_tiles, CHARBLOCK(2) + UI_BG0 * 16, UI_TILE_COUNT * 32);
    /* the marks over the boxes stay resident above the sheets */
    dma3_copy32(marks->tiles, OBJ_TILE(OBJ_TILE_UI), marks->tile_count * 32);
    hud_init();
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
    sBg0[ty * 32 + tx] = tile ? (tile | PAL_HUD) : 0;
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

void bg0_pool_reset(void) {
    vwf_pool(POOL_FIRST, POOL_END);
}

void bg0_pool_reset_full(void) {
    vwf_pool(POOL_FULL, POOL_END);
    hud_stale();
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
    /* Mode 3's bitmap occupies the normal BG0/BG3 map addresses. Keep
       their shadows pending until the tiled world has been restored. */
    if ((REG_DISPCNT & 7) == DCNT_MODE3)
        return;
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
    bg0_pool_reset_full();
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
        draw_sprite(SH_ICON_X, SH_ROW_Y(i) * 8, SHEET_ITEMS, sShopIconTile, sShopItems[i].icon, 0, 0, items_frame_pal[sShopItems[i].icon]);
    draw_sprite(SH_DET_X * 8 + 6, 70, SHEET_ITEMS, sShopIconTile, sShopItems[sShopCursor].icon, 0, 0, items_frame_pal[sShopItems[sShopCursor].icon]);
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
/* Panels in the kit's HUD frame, two pixels in from the screen's edge:
   at the left the hearts over the purse, the keys and R's hand; at the
   right the three buttons' slots by the mini-map, each holding the pause
   menu's own 32x32 icon of what it holds, its button's badge on its
   corner and the count of its seeds or arrows. The frames, the hearts and
   the purse are BG0's; the icons, badges, counts and the mini-map are
   sprites, first in OAM, so nothing of the world cuts into them. */
#define HUD_H (HUD_HEIGHT_PIXELS / 8)
#define HUD_SLOT_TX(s) (14 + (s) * 4)
#define HUD_MAP_TX 26

static Canvas sPurse, sCount[SLOT_COUNT];
static u32 sCountPix[SLOT_COUNT][4 * 8];
static s16 sHudHp, sHudHpMax;
static s16 sPurseGilt, sPurseKeys;       /* what the purse shows */
static u8 sHudEq[SLOT_COUNT];            /* whose icons are resident */
static u8 sHudIconFrame[SLOT_COUNT];     /* also tracks shield design changes */
static s16 sHudCount[SLOT_COUNT];        /* what each count shows, -1 none */

static void hud_init(void) {
    int s;
    vwf_canvas_at(&sPurse, HUD_PURSE_TILE, HUD_PURSE_TW, HUD_VITALS_TH);
    for (s = 0; s < SLOT_COUNT; s++) {
        vwf_canvas_obj(&sCount[s], sCountPix[s], OBJ_TILE_HUD_COUNTS + s * 4, 2, 2);
        sHudEq[s] = 0xFF;
        sHudIconFrame[s] = 0xFF;
        sHudCount[s] = -1;
    }
    hud_stale();
}

static void hud_stale(void) {
    sPurseGilt = -1;
    sHudHp = sHudHpMax = -1;
}

/* the icon a button's item has in the pause menu, or -1 */
static int hud_icon(int eq) {
    switch (eq) {
        case EQ_SWORD: return F_ICON32_SWORD;
        case EQ_SHIELD: return player_shield_icon();
        case EQ_BOMBS: return F_ICON32_BOMBS;
        case EQ_LAMP: return F_ICON32_LAMP;
        case EQ_CLOAK: return F_ICON32_CLOAK;
        case EQ_BOW: return F_ICON32_BOW;
        case EQ_HUBCAP: return F_ICON32_HUBCAP;
        default: return -1;
    }
}

/* what a button's item counts: the seeds, the arrows; else -1 */
static int hud_count(int eq) {
    return eq == EQ_BOMBS ? gPl.bombs : eq == EQ_BOW ? gPl.arrows : -1;
}

/* A complete native24px vitals panel. Its own palette contains the heart
   ramp, brass, cream and panel inks, avoiding tile-aligned rows that force
   the old32px HUD. The fixed36-tile canvas stays outside dialogue's pool. */
#define VI_OUTLINE 1
#define VI_PANEL 2
#define VI_EMPTY 3
#define VI_RED_DARK 5
#define VI_RED 6
#define VI_RED_LIGHT 7
#define VI_IVORY 8
#define VI_TEXT 9
#define VI_GOLD_DARK 11
#define VI_GOLD 12
#define VI_BROWN 13
#define VI_GOLD_LIGHT 14

static void vitals_line(int x0,int y0,int x1,int y1,int ink) {
    int x,y;
    for(y=y0;y<=y1;y++)for(x=x0;x<=x1;x++)vwf_pixel(&sPurse,x,y,ink);
}

static void vitals_heart(int x,int y,int fill) {
    static const u8 shape[8]={0x66,0xFF,0xFF,0xFF,0x7E,0x3C,0x18,0};
    int xx,yy;
    for(yy=0;yy<7;yy++)for(xx=0;xx<8;xx++)if(shape[yy]&(1<<xx)) {
        bool8 edge=xx==0 || xx==7 || yy==0 || yy==6 ||
            !(shape[yy]&(1<<(xx?xx-1:0))) || !(shape[yy]&(1<<(xx<7?xx+1:7)));
        int ink=edge ? VI_OUTLINE : (fill>=8 || (fill>=4 && xx<4)) ? (yy>=4 ? VI_RED_DARK : VI_RED) : VI_EMPTY;
        vwf_pixel(&sPurse,x+xx,y+yy,ink);
    }
    if(fill>=4) {vwf_pixel(&sPurse,x+1,y+1,VI_IVORY);vwf_pixel(&sPurse,x+2,y+1,VI_RED_LIGHT);}
}

static void vitals_key(int x,int y) {
    vitals_line(x+1,y+1,x+4,y+4,VI_OUTLINE);
    vitals_line(x+2,y+2,x+3,y+3,VI_GOLD);
    vwf_pixel(&sPurse,x+2,y+2,VI_IVORY);
    vwf_pixel(&sPurse,x+4,y+4,VI_GOLD);vwf_pixel(&sPurse,x+5,y+5,VI_GOLD);
    vwf_pixel(&sPurse,x+6,y+6,VI_GOLD);vwf_pixel(&sPurse,x+7,y+5,VI_GOLD);
}

static void hud_purse(void) {
    char buf[6];int x,y,i,hp=gPl.hp,hearts=MIN(10,(gPl.hp_max+7)/8);
    vwf_clear(&sPurse,0);
    vitals_line(1,1,94,22,VI_OUTLINE);vitals_line(2,2,93,21,VI_PANEL);
    vitals_line(3,1,92,1,VI_GOLD_DARK);vitals_line(2,2,2,20,VI_GOLD_DARK);
    vwf_pixel(&sPurse,2,1,VI_GOLD_LIGHT);vwf_pixel(&sPurse,93,21,VI_GOLD);
    for(i=0;i<hearts;i++,hp-=8)vitals_heart(7+i*8,4,hp);
    /* Coin and key are native8px symbols in this panel's own colour bank. */
    vitals_line(8,14,12,19,VI_GOLD_DARK);vitals_line(9,13,11,20,VI_GOLD_DARK);
    vitals_line(9,14,12,18,VI_GOLD);vwf_pixel(&sPurse,9,14,VI_IVORY);
    x=vwf_text(&sPurse,17,13,vwf_num(buf,gPl.gilt,0),VI_TEXT);
    vitals_key(x+3,13);vwf_text(&sPurse,x+13,13,vwf_num(buf,gPl.keys,0),VI_TEXT);
    /* R and a lifting hand stay visible without borrowing the heart row. */
    vitals_line(77,13,83,20,VI_OUTLINE);vitals_line(78,14,82,19,VI_EMPTY);
    vwf_glyph(&sPurse,78,13,'R',VI_TEXT);
    for(y=0;y<8;y++)for(x=0;x<8;x++) {
        int at=(HT_HAND-HUD_TILE_BASE)*16+y*2+x/4;
        int ink=(hud_tiles[at]>>((x&3)*4))&15;
        if(ink)vwf_pixel(&sPurse,85+x,13+y,ink);
    }
    vwf_flush(&sPurse,FALSE);
}

/* the icons copied in when a button takes another item, the counts set
   when they change */
static void hud_refresh(void) {
    const SpriteSheet* icons = &sheets[SHEET_HUDITEMS];
    int s;
    if (gPl.gilt != sPurseGilt || gPl.keys != sPurseKeys || gPl.hp != sHudHp || gPl.hp_max != sHudHpMax) {
        sPurseGilt = gPl.gilt;
        sPurseKeys = gPl.keys;
        sHudHp = gPl.hp; sHudHpMax = gPl.hp_max;
        hud_purse();
    }
    for (s = 0; s < SLOT_COUNT; s++) {
        int eq = gPl.equip[s], n = hud_count(eq), f = hud_icon(eq);
        if (eq != sHudEq[s] || sHudIconFrame[s] != (u8)f) {
            sHudEq[s] = eq;
            sHudIconFrame[s] = f;
            if (f >= 0)
                vram_queue(icons->tiles + f * icons->frame_tiles * 16, OBJ_TILE(OBJ_TILE_HUD_ICONS + s * 16),
                           icons->frame_tiles * 32);
        }
        if (n != sHudCount[s]) {
            sHudCount[s] = n;
            if (n >= 0) {
                char buf[6];
                vwf_num(buf, n, 0);
                vwf_clear(&sCount[s], 0);
                vwf_text_fx(&sCount[s], 14 - vwf_width(buf), 5, buf, UI_INK_CREAM, UI_INK_DARK, FX_OUTLINE);
                vwf_flush(&sCount[s], FALSE);
            }
        }
    }
}

/* The complete vitals canvas and three24px equipment panels occupy rows0..2.
   Inventory illustrations remain32px elsewhere; HUD equipment is a distinct
   native16px drawing, never clipped or filtered down. */
static void hud_bar(void) {
    u16* m=bg0_map();int s;
    memset32(m,0,HUD_H*32*2);
    vwf_map(&sPurse,m,0,0,PAL_SLOT_HUD);
    for(s=0;s<SLOT_COUNT;s++)ui_frame(m,UI_BG0,HUD_SLOT_TX(s),0,4,HUD_H,FR_HUD);
    ui_frame(m,UI_BG0,HUD_MAP_TX,0,4,HUD_H,FR_HUD);
}

static void obj_square(int x, int y, int size, int tile, int pal) {
    OamEntry* o = oam_alloc();
    if (!o)
        return;
    o->attr0 = ATTR0_Y(y) | ATTR0_SQUARE;
    o->attr1 = ATTR1_X(x) | ATTR1_SIZE(size);
    o->attr2 = ATTR2_TILE(tile) | ATTR2_PRIO(0) | ATTR2_PAL(pal);
}

/* the badges and counts over the icons, then the icons, the mini-map */
static void hud_sprites(void) {
    int s;
    for (s = 0; s < SLOT_COUNT; s++) {
        int x = HUD_SLOT_TX(s) * 8;
        draw_sprite(x + 2, 2, SHEET_UIMARKS, OBJ_TILE_UI, F_UIMARKS_BADGE_A + s, 0, 0, PAL_OBJ_UIKIT);
        if (sHudCount[s] >= 0)
            obj_square(x + 14, 8, 1, OBJ_TILE_HUD_COUNTS + s * 4, PAL_OBJ_UIKIT);
    }
    for (s = 0; s < SLOT_COUNT; s++)
        if (hud_icon(sHudEq[s]) >= 0)
            obj_square(HUD_SLOT_TX(s) * 8 + 8, 4, 1, OBJ_TILE_HUD_ICONS + s * 16, huditems_frame_pal[sHudIconFrame[s]]);
    obj_square(HUD_MAP_TX * 8, 0, 2, OBJ_TILE_MINIMAP, PAL_OBJ_UIKIT);
}

void hud_draw(void) {
    hud_refresh();
    hud_bar();
    hud_sprites();
}

/* ----------------------------------------------------------- mini-map -- */
/* A 32x32 sprite drawn by the CPU inside the HUD's frame: the five by
   five cells of the wood at four pixels each, the panels' navy with a
   faint grid where nothing is seen yet, green with a lit edge where the
   hero has been, gold at the Heart; a red dot where he stands, a pale
   one at the way in while he is below. */
static u16 sMapTiles[16 * 16];

void minimap_render(void) {
    static u8 buf[32 * 32];
    int x, y, i, here = (gGame.area == AREA_FOREST) ? gGame.cell : gWorld.entry;
    memset32(buf, 0, sizeof(buf));
    for (i = 0; i < CELLS; i++) {
        Cell* c = &gWorld.cells[i];
        int cx = 8 + (i % MAZE_W) * 3, cy = 4 + (i / MAZE_W) * 3;
        bool8 seen = (c->flags & CF_VISITED) != 0, goal = i == gWorld.goal;
        for (y = 0; y < 3; y++)
            for (x = 0; x < 3; x++) {
                bool8 edge = x == 0 || y == 0;
                u8 col;
                if (!seen)
                    col = edge ? UI_INK_RAISED : UI_INK_NAVY;
                else if (goal)
                    col = edge ? UI_INK_PALE : UI_INK_GOLD;
                else
                    col = edge ? OBJ_INK_GREEN_LIT : OBJ_INK_GREEN;
                buf[(cy + y) * 32 + cx + x] = col;
            }
        if (i == here) {
            u8 dot = (gGame.area == AREA_FOREST) ? UI_INK_RED : UI_INK_CREAM;
            buf[(cy + 1) * 32 + cx + 1] = UI_INK_PALE;
            buf[(cy + 1) * 32 + cx + 2] = dot;
            buf[(cy + 2) * 32 + cx + 1] = dot;
            buf[(cy + 2) * 32 + cx + 2] = dot;
        }
    }
    /* pack to 4bpp tiles, 4x4 tiles in row order */
    for (i = 0; i < 16; i++) {
        int tx = (i % 4) * 8, ty = (i / 4) * 8;
        for (y = 0; y < 8; y++) {
            for (x = 0; x < 8; x += 4) {
                const u8* p = &buf[(ty + y) * 32 + tx + x];
                sMapTiles[i * 16 + y * 2 + x / 4] = p[0] | (p[1] << 4) | (p[2] << 8) | (p[3] << 12);
            }
        }
    }
    dma3_copy32(sMapTiles, OBJ_TILE(OBJ_TILE_MINIMAP), sizeof(sMapTiles));
}

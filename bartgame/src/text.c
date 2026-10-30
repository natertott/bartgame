/* BARTGAME: BG0, the layer over the world: the HUD, the message box
   with its speaker's face and name plate, and the shop. BG0 is 32x32
   tiles at screenblock 23 in charblock 2, whose tiles stay under 384
   (screenblocks 22 and 23 follow them): 0 is clear, then the hearts and
   native hearts, then the UI kit, then the transparent HUD canvas, then the pool the
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
#define PAL_HUD (PAL_SLOT_HUD << 12) /* native heart tiles */
#define HUD_PURSE_TILE (UI_BG0 + UI_TILE_COUNT) /* the purse's own tiles */
#define HUD_PURSE_TW 30
#define HUD_VITALS_TH 2
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
static void hud_panel_base(void);

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
/* Health, gilt, equipped items, their relevant ammunition and a small map
   remain on the playfield.
   Every painted top-HUD pixel fits within twelve rows. The open centre at x116..147
   leaves northern doors, ladder arrows and enemies visible. Item pictograms
   are authored at ten pixels inside a hardware-valid16x16 sprite canvas. */
#define HUD_MAP_ROWS 2
#define HUD_EQUIP_X(s) (148 + (s) * 30)

static Canvas sPurse;
static u32 sVitalsBase[HUD_PURSE_TW * HUD_VITALS_TH * 8] EWRAM_BSS;
static s16 sHudHp, sHudHpMax;
static s32 sPurseGilt;
static u8 sHudEq[SLOT_COUNT];
static u8 sHudIconFrame[SLOT_COUNT];
static s16 sHudCount[SLOT_COUNT];

#define VI_OUTLINE 1
#define VI_PANEL 2
#define VI_EMPTY 3
#define VI_IVORY 8
#define VI_TEXT 9
#define VI_GOLD_DARK 11
#define VI_GOLD 12
#define VI_BROWN 13
#define VI_GOLD_LIGHT 14

static void vitals_line(int x0,int y0,int x1,int y1,int ink) {
    int x,y;
    u32 pixels=(ink&15)*0x11111111u;
    x0=MAX(0,x0);y0=MAX(0,y0);
    x1=MIN(sPurse.tw*8-1,x1);y1=MIN(HUD_HEIGHT_PIXELS-1,y1);
    for(y=y0;y<=y1;y++)for(x=x0;x<=x1;) {
        int first=x&7,count=MIN(8-first,x1-x+1);
        u32* dst=sPurse.px+((y>>3)*sPurse.tw+(x>>3))*8+(y&7);
        if(count==8)*dst=pixels;
        else {
            u32 mask=((1u<<(count*4))-1)<<(first*4);
            *dst=(*dst&~mask)|(pixels&mask);
        }
        x+=count;
    }
}

/* A shadowed local backing never becomes an opaque full-width ribbon.
   Each study borrows its menu's shape language in a few native corner pixels. */
static void hud_pod(int x,int width) {
#if BART_UI_VARIANT == 2
    vitals_line(x+1,1,x+width-2,10,VI_PANEL);
    vitals_line(x,2,x+width-1,9,VI_PANEL);
    vwf_pixel(&sPurse,x+width-2,1,VI_GOLD);
    vwf_pixel(&sPurse,x+width-1,2,VI_GOLD_DARK);
#elif BART_UI_VARIANT == 3
    vitals_line(x+2,0,x+width-3,0,VI_GOLD);
    vitals_line(x+1,1,x+width-2,10,VI_PANEL);
    vwf_pixel(&sPurse,x,2,VI_GOLD);
    vwf_pixel(&sPurse,x+width-1,9,VI_GOLD_DARK);
#elif BART_UI_VARIANT == 4
    vitals_line(x+1,1,x+width-2,10,VI_PANEL);
    vwf_pixel(&sPurse,x,2,VI_GOLD_DARK);
    vwf_pixel(&sPurse,x+1,1,VI_GOLD_LIGHT);
    vwf_pixel(&sPurse,x+width-2,10,VI_GOLD);
#elif BART_UI_VARIANT == 5
    vitals_line(x,1,x+width-1,10,VI_PANEL);
    vwf_pixel(&sPurse,x,1,VI_GOLD_DARK);
    vwf_pixel(&sPurse,x+width-1,10,VI_GOLD_DARK);
#else
    vitals_line(x+1,1,x+width-2,10,VI_PANEL);
    vitals_line(x,2,x,4,VI_GOLD_DARK);
    vitals_line(x+width-1,7,x+width-1,9,VI_GOLD_DARK);
#endif
}

static void hud_heart(int x,int fill) {
    int tile=fill>=8?HT_HEART_FULL:fill>=4?HT_HEART_HALF:HT_HEART_EMPTY;
    int xx,yy;
    for(yy=0;yy<8;yy++)for(xx=0;xx<8;xx++) {
        int at=(tile-HUD_TILE_BASE)*16+yy*2+xx/4;
        int ink=(hud_tiles[at]>>((xx&3)*4))&15;
        vwf_pixel(&sPurse,x+xx,2+yy,ink);
    }
}

static int vitals_heart_style(int hp) {
    return hp>=8?2:hp>=4?1:0;
}

/* Native3x5 figures keep even the full16-bit gilt amount in a small footprint.
   Their one-pixel dark outline survives both pale stone and black caves. */
static void hud_digits(int origin_x,int origin_y,unsigned value) {
    static const u8 digits[10][5]={
        {7,5,5,5,7},{2,6,2,2,7},{7,1,7,4,7},{7,1,7,1,7},
        {5,5,7,1,1},{7,4,7,1,7},{7,4,7,5,7},{7,1,1,1,1},
        {7,5,7,5,7},{7,5,7,1,7}
    };
    char buf[6];int n=0,i,x,y,pass,dx,dy;
    do {buf[n++]='0'+value%10;value/=10;}while(value && n<5);
    for(pass=0;pass<2;pass++)for(i=0;i<n;i++)for(y=0;y<5;y++)for(x=0;x<3;x++)
        if(digits[(int)buf[n-i-1]-'0'][y]&(4>>x)) {
            int px=origin_x+i*4+x,py=origin_y+y;
            if(!pass)for(dy=-1;dy<=1;dy++)for(dx=-1;dx<=1;dx++)
                vwf_pixel(&sPurse,px+dx,py+dy,VI_OUTLINE);
            else vwf_pixel(&sPurse,px,py,VI_TEXT);
        }
}

static void hud_coin(void) {
    vitals_line(86,2,89,9,VI_OUTLINE);
    vitals_line(84,4,91,7,VI_OUTLINE);
    vitals_line(85,3,90,8,VI_GOLD_DARK);
    vitals_line(86,3,89,7,VI_GOLD);
    vitals_line(86,3,88,3,VI_IVORY);
    vitals_line(87,4,87,6,VI_GOLD_LIGHT);
}

/* Tiny assignment letters belong to their equipped pictograms; empty slots
   are wholly transparent rather than adding another box to the HUD. */
static void hud_assignment(int x,int slot) {
    static const u8 letters[3][5]={{2,5,7,5,5},{6,5,6,5,6},{4,4,4,4,7}};
    int px,py,pass,dx,dy;
    for(pass=0;pass<2;pass++)for(py=0;py<5;py++)for(px=0;px<3;px++)
        if(letters[slot][py]&(4>>px)) {
            if(!pass)for(dy=-1;dy<=1;dy++)for(dx=-1;dx<=1;dx++)
                vwf_pixel(&sPurse,x+px+dx,3+py+dy,VI_OUTLINE);
            else vwf_pixel(&sPurse,x+px,3+py,VI_TEXT);
        }
}

static int hud_icon(int eq) {
    switch(eq) {
        case EQ_SWORD:return F_ICON32_SWORD;
        case EQ_SHIELD:return player_shield_icon();
        case EQ_BOMBS:return F_ICON32_BOMBS;
        case EQ_LAMP:return F_ICON32_LAMP;
        case EQ_CLOAK:return F_ICON32_CLOAK;
        case EQ_BOW:return F_ICON32_BOW;
        case EQ_HUBCAP:return F_ICON32_HUBCAP;
        default:return -1;
    }
}

static void hud_panel_base(void) {
    vwf_clear(&sPurse,0);
    hud_coin();
    memcpy32(sVitalsBase,sPurse.px,sizeof(sVitalsBase));
}

static void hud_stale(void) {
    sPurseGilt=-1;sHudHp=sHudHpMax=-1;
}

static void hud_init(void) {
    int s;
    vwf_canvas_at(&sPurse,HUD_PURSE_TILE,HUD_PURSE_TW,HUD_VITALS_TH);
    for(s=0;s<SLOT_COUNT;s++) {
        sHudEq[s]=0xFF;sHudIconFrame[s]=0xFF;sHudCount[s]=-1;
    }
    hud_panel_base();hud_stale();
}

static void hud_refresh(void) {
    const SpriteSheet* icons=&sheets[SHEET_HUDITEMS];
    int s,i,hearts=MIN(10,(gPl.hp_max+7)/8);
    bool8 reset=sPurseGilt<0 || sHudHp<0 || sHudHpMax!=gPl.hp_max;
    bool8 dirty=reset;
    if(reset)memcpy32(sPurse.px,sVitalsBase,sizeof(sVitalsBase));
    for(i=0;i<hearts;i++)
        if(reset || vitals_heart_style(gPl.hp-i*8)!=vitals_heart_style(sHudHp-i*8)) {
            hud_heart(2+i*8,gPl.hp-i*8);dirty=TRUE;
        }
    if(reset || sPurseGilt!=gPl.gilt) {
        vitals_line(93,1,115,9,0);
        hud_digits(94,3,gPl.gilt);dirty=TRUE;
    }
    for(s=0;s<SLOT_COUNT;s++) {
        int eq=gPl.equip[s],f=hud_icon(eq),x=HUD_EQUIP_X(s);
        int count=eq==EQ_BOMBS?gPl.bombs:eq==EQ_BOW?gPl.arrows:-1;
        if(reset || eq!=sHudEq[s] || sHudIconFrame[s]!=(u8)f || count!=sHudCount[s]) {
            vitals_line(x,0,x+29,11,0);
            if(f>=0) {
                int width=count<0?20:count>=100?30:count>=10?26:22;
                hud_pod(x,width);hud_assignment(x+1,s);
                if(count>=0)hud_digits(x+17,3,count);
            }
            sHudCount[s]=count;
            if(eq!=sHudEq[s] || sHudIconFrame[s]!=(u8)f) {
                sHudEq[s]=eq;sHudIconFrame[s]=f;
                if(f>=0)vram_queue(icons->tiles+f*icons->frame_tiles*16,
                    OBJ_TILE(OBJ_TILE_HUD_ICONS+s*16),icons->frame_tiles*32);
            }
            dirty=TRUE;
        }
    }
    if(dirty)vwf_flush(&sPurse,FALSE);
    sPurseGilt=gPl.gilt;sHudHp=gPl.hp;sHudHpMax=gPl.hp_max;
}

static void hud_bar(void) {
    u16* m=bg0_map();
    memset32(m,0,HUD_MAP_ROWS*32*2);
    vwf_map(&sPurse,m,0,0,PAL_SLOT_HUD);
}

static void obj_square(int x,int y,int size,int tile,int pal) {
    OamEntry* o=oam_alloc();
    if(!o)return;
    o->attr0=ATTR0_Y(y)|ATTR0_SQUARE;
    o->attr1=ATTR1_X(x)|ATTR1_SIZE(size);
    o->attr2=ATTR2_TILE(tile)|ATTR2_PRIO(0)|ATTR2_PAL(pal);
}

static void hud_sprites(void) {
    int s;
    for(s=0;s<SLOT_COUNT;s++)if(hud_icon(sHudEq[s])>=0)
        obj_square(HUD_EQUIP_X(s)+4,0,1,OBJ_TILE_HUD_ICONS+s*16,
                   huditems_frame_pal[sHudIconFrame[s]]);
    obj_square(222,142,1,OBJ_TILE_MINIMAP,PAL_OBJ_UIKIT);
}

void hud_draw(void) {
    hud_refresh();hud_bar();hud_sprites();
}

/* The compact map occupies a small lower-right corner, leaving the northern
   playfield open. Five by five cells are drawn natively, not scaled from the
   pause-map illustration. Room-entry calls keep fog and the current cell live. */
static u16 sMapTiles[4 * 16];

void minimap_render(void) {
    u8 buf[16 * 16];
    int x,y,i,here=gGame.area==AREA_FOREST?gGame.cell:gWorld.entry;
    for(y=0;y<16;y++)for(x=0;x<16;x++)
        buf[y*16+x]=(x==0 || y==0 || x==15 || y==15)?UI_INK_DARK:UI_INK_NAVY;
    buf[0]=UI_INK_PALE;buf[15]=buf[240]=UI_INK_GOLD;
    for(i=0;i<CELLS;i++) {
        Cell* cell=&gWorld.cells[i];
        int cx=1+(i%MAZE_W)*3,cy=1+(i/MAZE_W)*3;
        bool8 seen=(cell->flags&CF_VISITED)!=0,goal=i==gWorld.goal;
        for(y=0;y<2;y++)for(x=0;x<2;x++) {
            int ink=!seen?UI_INK_RAISED:goal?UI_INK_GOLD:(y==0?OBJ_INK_GREEN_LIT:OBJ_INK_GREEN);
            if(i==here)ink=gGame.area==AREA_FOREST?(x==0?UI_INK_PALE:UI_INK_RED):UI_INK_CREAM;
            buf[(cy+y)*16+cx+x]=ink;
        }
    }
    for(i=0;i<4;i++) {
        int tx=(i%2)*8,ty=(i/2)*8;
        for(y=0;y<8;y++)for(x=0;x<8;x+=4) {
            const u8* row=&buf[(ty+y)*16+tx+x];
            sMapTiles[i*16+y*2+x/4]=row[0]|(row[1]<<4)|(row[2]<<8)|(row[3]<<12);
        }
    }
    dma3_copy32(sMapTiles,OBJ_TILE(OBJ_TILE_MINIMAP),sizeof(sMapTiles));
}

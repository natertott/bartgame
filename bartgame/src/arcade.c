/* The Drain's memory cabinet: familiar native folio frames around a compact
   collection index and a readable full-notes page. Browsing borrows only the
   face's reserved OBJ window, never growing the world's sprite allocation. */
#include "gba.h"
#include "video.h"
#include "actor.h"
#include "room.h"
#include "game.h"
#include "text.h"
#include "ui.h"
#include "sound.h"
#include "journal.h"
#include "arcade.h"

#define ARCADE_ROWS 6
#define PREVIEW_TILE OBJ_TILE_FACE
#define PREVIEW_PAL PAL_OBJ_PORTRAIT
#define PREVIEW_MAX_TILES 32

u8 gArcadePage, gArcadeCursor, gArcadeTop, gArcadeDetail, gArcadeSeen;
u8 gArcadePreviewSheet, gArcadePreviewFrame, gArcadePreviewSourcePalette;
u16 gArcadePreviewTiles;

static u8 sActive, sCursor[2], sTop[2], sRepeat, sOldAnim;
static u16 sOldDisplay, sOldBg3, sOldBlend, sOldAlpha, sOldBrightness;
static s16 sOldScroll[2];
static u16 sJournalRevision;
static u16 sWorldPreviewPal[16] ALIGN4;
static u32 sWorldPreview[PREVIEW_MAX_TILES * 8] EWRAM_BSS;
static Canvas sHeader, sList, sInfo, sNote, sFooter;

static int entry_count(void) {
    return journal_list_count(gArcadePage);
}

static bool8 seen(int index) {
    int raw=journal_list_id(gArcadePage,index);
    return gArcadePage ? journal_enemy_seen(raw) : journal_item_seen(raw);
}

/* No undiscovered name, stat, frame or palette reaches presentation code. */
static const JournalEntry* entry(int index,JournalEntry* storage) {
    if (!seen(index)) return NULL;
    return journal_entry(gArcadePage,journal_list_id(gArcadePage,index),storage) ? storage : NULL;
}

static char* append(char* out, const char* text) {
    while (*text) *out++ = *text++;
    *out = 0;
    return out;
}

static char* append_num(char* out, int value) {
    char number[8];
    vwf_num(number, value, 0);
    return append(out, number);
}

static void count_label(char* out, const char* name, int found, int total) {
    out = append(out, name);
    out = append(out, " ");
    out = append_num(out, found);
    out = append(out, "/");
    append_num(out, total);
}

static void fit_text(Canvas* c, int x, int y, int width, const char* text, int ink) {
    char line[64];
    int n = 0, pixels = 0, dots = vwf_width("...");
    if (vwf_width(text) <= width) {
        vwf_text(c, x, y, text, ink);
        return;
    }
    while (text[n] && n < (int)sizeof(line)-4) {
        int advance = vwf_advance((u8)text[n]);
        if (pixels + advance + dots > width) break;
        pixels += advance;
        line[n] = text[n];
        n++;
    }
    line[n++] = '.'; line[n++] = '.'; line[n++] = '.'; line[n] = 0;
    vwf_text(c, x, y, line, ink);
}

static void sync_cursor(void) {
    int count = entry_count();
    if (sCursor[gArcadePage] >= count)
        sCursor[gArcadePage] = count ? count-1 : 0;
    if (sTop[gArcadePage] > sCursor[gArcadePage])
        sTop[gArcadePage] = sCursor[gArcadePage];
    if (sCursor[gArcadePage] >= sTop[gArcadePage] + ARCADE_ROWS)
        sTop[gArcadePage] = sCursor[gArcadePage] - ARCADE_ROWS + 1;
    sTop[gArcadePage] = MIN(sTop[gArcadePage], MAX(0, count-ARCADE_ROWS));
    gArcadeCursor = sCursor[gArcadePage];
    gArcadeTop = sTop[gArcadePage];
    gArcadeSeen = seen(gArcadeCursor);
}

static void load_preview(void) {
    JournalEntry storage;
    const JournalEntry* e = entry(gArcadeCursor,&storage);
    const SpriteSheet* sh;
    const u16 *pixels, *palette;
    gArcadePreviewTiles = 0;
    gArcadePreviewSheet = gArcadePreviewFrame = gArcadePreviewSourcePalette = 0xFF;
    if (!e) return;
    sh = &sheets[e->sheet];
    if (!sh->frame_tiles || sh->frame_tiles > PREVIEW_MAX_TILES ||
        (int)e->frame * sh->frame_tiles + sh->frame_tiles > sh->tile_count)
        return;
    pixels = sh->tiles + (int)e->frame * sh->frame_tiles * 16;
    palette = pal_obj + (int)e->palette * 16;
    /* Menu illustrations own their exact inks. All world bodies retain
       their native material-bank indices and actual final-size pixels. */
    if (e->sheet == SHEET_ICON32) {
        pixels = icon32_exact_tiles + (int)e->frame * sh->frame_tiles * 16;
        palette = icon32_exact_pal + (int)e->frame * 16;
    }
    vram_queue(pixels, OBJ_TILE(PREVIEW_TILE), sh->frame_tiles * 32);
    pal_set_obj(PREVIEW_PAL, palette);
    gArcadePreviewSheet = e->sheet;
    gArcadePreviewFrame = e->frame;
    gArcadePreviewSourcePalette = e->palette;
    gArcadePreviewTiles = sh->frame_tiles;
}

static void flush_canvas(Canvas* c) {
    vwf_flush(c, FALSE);
}

static void draw_header(void) {
    char label[40];
    int page;
    bg0_canvas(&sHeader, 1, 1, 28, 2);
    for (page = 0; page < 2; page++) {
        int x = page * 112;
        count_label(label, page ? "Enemies" : "Items",
                    journal_list_found(page), journal_list_count(page));
        ui_plate_px(&sHeader, x, 0, 14, page == gArcadePage ? PL_TABON : PL_TAB);
        vwf_text(&sHeader, x + (112-vwf_width(label))/2, 4, label,
                 page == gArcadePage ? UI_INK_HIGH : UI_INK_CREAM);
    }
    flush_canvas(&sHeader);
}

static void draw_index(void) {
    JournalEntry chosenStorage,rowStorage;
    const JournalEntry* chosen = entry(gArcadeCursor,&chosenStorage);
    int row;
    ui_frame(gBg3, UI_BG3, 1, 4, 14, 14, FR_PANEL);
    ui_frame(gBg3, UI_BG3, 15, 4, 14, 14, FR_PANEL);
    bg0_canvas(&sList, 2, 5, 11, 12);
    for (row = 0; row < ARCADE_ROWS && gArcadeTop+row < entry_count(); row++) {
        int index = gArcadeTop+row;
        const JournalEntry* e = entry(index,&rowStorage);
        int ink = e ? UI_INK_CREAM : UI_INK_DIM;
        if (index == gArcadeCursor) {
            ui_plate_px(&sList, 0, row * 16, 11, PL_TABON);
            ink = UI_INK_HIGH;
        }
        fit_text(&sList, 4, row * 16 + 4, 80, e ? e->name : "???", ink);
    }
    flush_canvas(&sList);
    bg0_canvas(&sInfo, 17, 5, 11, 4);
    if (chosen) {
        vwf_block(&sInfo, 0, 1, 88, 10, chosen->name, UI_INK_GOLD, 2);
        if (gArcadePage) {
            char stats[40];
            if(chosen->hp==255)append(stats,"Special defenses");
            else {
                char* out=append(stats,"HP ");
                out=append_num(out,chosen->hp);out=append(out," / touch ");
                append_num(out,chosen->damage);
            }
            fit_text(&sInfo, 0, 22, 88, stats, UI_INK_CREAM);
        }
    } else {
        vwf_text(&sInfo, 30, 1, "???", UI_INK_DIM);
        vwf_text(&sInfo, 0, 22, "Not recorded", UI_INK_DIM);
    }
    flush_canvas(&sInfo);
    bg0_canvas(&sNote, 17, 14, 11, 3);
    if (!chosen)
        vwf_block(&sNote, 0, 0, 88, 10, "Encounter it to reveal this memory.", UI_INK_DIM, 2);
    else if (sheets[chosen->sheet].h <= 32)
        vwf_block(&sNote, 0, 0, 88, 10, gArcadePage ? "A: combat notes" : "A: item notes", UI_INK_CREAM, 2);
    flush_canvas(&sNote);
    bg0_canvas(&sFooter, 2, 18, 26, 2);
    fit_text(&sFooter, 0, 3, 208, "L/R Tabs  D-pad Browse  A Notes  B Exit", UI_INK_CREAM);
    flush_canvas(&sFooter);
}

static void draw_notes(void) {
    JournalEntry storage;
    const JournalEntry* e = entry(gArcadeCursor,&storage);
    char label[40];
    /* Unlike the compact index, the full notes never truncate an entry's
       name or description. Native image, stat units and text have their
       own spaces. The largest Heart view stays within its64px hardware box. */
    bg0_canvas(&sHeader, 2, 1, 26, 2);
    fit_text(&sHeader, 0, 3, 208, e ? e->name : "An unrecorded memory", UI_INK_GOLD);
    flush_canvas(&sHeader);
    ui_frame(gBg3, UI_BG3, 2, 5, 8, 11, e ? FR_SLOT : FR_EMPTY);
    ui_frame(gBg3, UI_BG3, 10, 4, 19, 13, FR_PANEL);
    bg0_canvas(&sInfo, 11, 5, 17, 11);
    if (!e) {
        vwf_block(&sInfo, 0, 4, 136, 11,
                  "Explore the wood. This memory appears after you encounter it.", UI_INK_DIM, 7);
    } else if (gArcadePage) {
        char* out;
        if(e->hp==255)append(label,"Special defenses");
        else {out=append(label,"Health: ");out=append_num(out,e->hp);append(out," HP");}
        vwf_text(&sInfo, 0, 0, label, UI_INK_HIGH);
        out = append(label, "Touch: ");
        out = append_num(out, e->damage);
        append(out, " HP");
        vwf_text(&sInfo, 0, 11, label, UI_INK_CREAM);
        vwf_text(&sInfo, 0, 22, "One heart = 8 HP", UI_INK_DIM);
        vwf_block(&sInfo, 0, 36, 136, 10, e->description, UI_INK_CREAM, 5);
    } else {
        vwf_block(&sInfo, 0, 4, 136, 11, e->description, UI_INK_CREAM, 7);
    }
    flush_canvas(&sInfo);
    bg0_canvas(&sFooter, 2, 18, 26, 2);
    fit_text(&sFooter, 0, 3, 208, "D-pad Entry  B Index  Start Leave", UI_INK_CREAM);
    flush_canvas(&sFooter);
}

static void draw_page(void) {
    bg0_clear();
    bg0_pool_reset_full();
    ui_backdrop_clear();
    ui_frame(gBg3, UI_BG3, 0, 0, 30, 20, FR_PANEL);
    if (gArcadeDetail) draw_notes();
    else { draw_header(); draw_index(); }
    gBg3Dirty = 1;
    sJournalRevision = gJournalRevision;
}

static void draw_preview(void) {
    int cx, cy;
    const SpriteSheet* sh;
    if (!gArcadePreviewTiles) return;
    sh = &sheets[gArcadePreviewSheet];
    cx = gArcadeDetail ? 48 : 180;
    cy = gArcadeDetail ? 84 : sh->h > 32 ? 100 : 92;
    draw_sprite(cx-sh->w/2, cy-sh->h/2, gArcadePreviewSheet,
                PREVIEW_TILE, 0, 0, 0, PREVIEW_PAL);
}

static void arcade_close(void) {
    dma3_copy32(sWorldPreview, OBJ_TILE(PREVIEW_TILE), sizeof(sWorldPreview));
    pal_set_obj(PREVIEW_PAL, sWorldPreviewPal);
    bg0_clear();
    gBg3Dirty = 0;
    gAnimTiles = sOldAnim;
    REG_BG3CNT = sOldBg3;
    gBgScroll[3][0] = sOldScroll[0];
    gBgScroll[3][1] = sOldScroll[1];
    gGame.state = GS_PLAY;
    room_render();
    video_show(sOldDisplay);
    REG_BLDCNT = sOldBlend;
    REG_BLDALPHA = sOldAlpha;
    REG_BLDY = sOldBrightness;
    sActive = 0;
    gKeysDown = 0;
    sfx_play(SFX_MENU);
}

void arcade_open(void) {
    if (sActive) return;
    sOldDisplay = REG_DISPCNT;
    sOldBg3 = REG_BG3CNT;
    sOldScroll[0] = gBgScroll[3][0]; sOldScroll[1] = gBgScroll[3][1];
    sOldBlend = REG_BLDCNT; sOldAlpha = REG_BLDALPHA; sOldBrightness = REG_BLDY;
    sOldAnim = gAnimTiles;
    dma3_copy32((const void*)OBJ_TILE(PREVIEW_TILE), sWorldPreview, sizeof(sWorldPreview));
    memcpy32(sWorldPreviewPal, gPalObj + PREVIEW_PAL * 16, sizeof(sWorldPreviewPal));
    gAnimTiles = 0;
    REG_BG3CNT = BGCNT_PRIO(3)|BGCNT_CHARBASE(3)|BGCNT_SCREENBASE(22)|BGCNT_SIZE_32x32;
    gBgScroll[3][0] = gBgScroll[3][1] = 0;
    REG_BLDCNT = REG_BLDY = 0;
    ui_backdrop_open();
    gGame.state = GS_ARCADE;
    video_show(DCNT_BG0|DCNT_BG3|DCNT_OBJ);
    sActive = 1; sRepeat = 0; gArcadeDetail = 0;
    sync_cursor(); load_preview(); draw_page(); draw_preview();
    gKeysDown = 0;
    sfx_play(SFX_MENU);
}

bool8 arcade_active(void) { return sActive; }

void arcade_update(void) {
    u16 movement = gKeysDown & (KEY_UP|KEY_DOWN|KEY_LEFT|KEY_RIGHT);
    int old = gArcadeCursor, next = old;
    bool8 dirty = FALSE;
    if (!sActive) return;
    if (gKeysDown & KEY_START) { arcade_close(); return; }
    if (gKeysDown & KEY_B) {
        if (!gArcadeDetail) { arcade_close(); return; }
        gArcadeDetail = 0; dirty = TRUE;
    } else if (gKeysDown & (KEY_L|KEY_R)) {
        gArcadePage ^= 1;
        gArcadeDetail = 0;
        sync_cursor(); load_preview(); dirty = TRUE;
    } else if ((gKeysDown & KEY_A) && !gArcadeDetail) {
        gArcadeDetail = 1; dirty = TRUE;
    } else {
        u16 held = gKeysHeld & (KEY_UP|KEY_DOWN|KEY_LEFT|KEY_RIGHT);
        if (movement || !held) sRepeat = 18;
        else if (sRepeat) sRepeat--;
        else { movement = held; sRepeat = 4; }
        if (movement & KEY_UP) next--;
        else if (movement & KEY_DOWN) next++;
        else if (movement & KEY_LEFT) next -= gArcadeDetail ? 1 : ARCADE_ROWS;
        else if (movement & KEY_RIGHT) next += gArcadeDetail ? 1 : ARCADE_ROWS;
        next = CLAMP(next, 0, MAX(0, entry_count()-1));
        if (next != old) {
            sCursor[gArcadePage] = next;
            sync_cursor(); load_preview(); dirty = TRUE;
        }
    }
    if (sJournalRevision != gJournalRevision) {
        sync_cursor(); load_preview(); dirty = TRUE;
    }
    if (dirty) { draw_page(); sfx_play(SFX_MENU); }
    draw_preview();
}

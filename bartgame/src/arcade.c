/* The Drain Trophy Case reads the permanent journal and expedition records.
   The case backdrop and exhibit own separate BG layers. The exhibit borrows
   no world OBJ slots and never changes a discovery or inventory by browsing. */
#include "arcade.h"
#include "game.h"
#include "handoff_events.h"
#include "journal.h"
#include "room.h"
#include "sound.h"
#include "text.h"
#include "trading_cards.h"
#include "trophy_data.h"
#include "ui.h"
#include "video.h"

enum { TAB_MILESTONES, TAB_ITEMS, TAB_CREATURES, TAB_CARDS, TAB_COUNT };
enum { ROWS = 5, NO_ENTRY = 255, TEXT_WIDTH = 132, NOTE_PITCH = 10 };
enum {
    CASE_PAL = 8, EXHIBIT_PAL = 9, EXHIBIT_MAP = 30,
    EXHIBIT_WIDTH = 8, EXHIBIT_HEIGHT = 7,
    EXHIBIT_BLANK = TROPHY_CASE_TILE_COUNT, EXHIBIT_TILE = EXHIBIT_BLANK + 1
};
enum { MUTED = 15, GOLD = 12, IVORY = 13 };
_Static_assert(EXHIBIT_TILE + EXHIBIT_WIDTH * EXHIBIT_HEIGHT <= (EXHIBIT_MAP - 24) * 64,
               "Trophy art and its screenblock must not overlap");
_Static_assert((int)JI_COUNT < NO_ENTRY && JOURNAL_ENEMY_COUNT < NO_ENTRY && (int)CARD_COUNT < NO_ENTRY,
               "Trophy entry IDs must fit in a byte");
_Static_assert(78 + 24 + 187 + 38 <= 384 - (UI_BG0 + UI_TILE_COUNT),
               "Trophy detail text must fit in BG0's full-screen pool");

typedef struct {
    const char* name;
    const char* notes;
    u8 sheet, frame, palette, hp, damage;
    bool8 found;
} Exhibit;

u8 gArcadePage, gArcadeCursor, gArcadeTop, gArcadeDetail, gArcadeSeen;
u8 gArcadeEntry, gArcadeCount, gArcadeFilter;
u8 gArcadePreviewSheet, gArcadePreviewFrame, gArcadePreviewSourcePalette;
u16 gArcadePreviewTiles;

static const char* const sTabs[TAB_COUNT] = { "Milestones", "Items", "Creatures", "Cards" };
static const char* const sRarities[CARD_RARITY_COUNT] = { "Common", "Uncommon", "Rare", "Ultra-rare" };
static u8 sCursor[TAB_COUNT], sOrder[NO_ENTRY], sRepeat, sFound, sTotal, sNoteOffset, sNoteLimit;
static u8 sOldAnim;
static u16 sDisplay, sBg1, sBg3, sBlend, sAlpha, sBrightness;
static s16 sScroll[2][2];
static u16 sPalettes[3][16] EWRAM_BSS ALIGN4;
static u16 sExhibitMap[32 * 32] EWRAM_BSS ALIGN4;
static u32 sExhibitPixels[EXHIBIT_WIDTH * EXHIBIT_HEIGHT * 8] EWRAM_BSS;

static int tab_count(void) {
    switch (gArcadePage) {
        case TAB_MILESTONES: return trophy_milestone_count();
        case TAB_ITEMS: return journal_list_count(0);
        case TAB_CREATURES: return journal_list_count(1);
        default: return CARD_COUNT;
    }
}

static Exhibit exhibit(int id) {
    Exhibit result = {0};
    if (id == NO_ENTRY) return result;
    if (gArcadePage == TAB_MILESTONES) {
        TrophyMilestone entry;
        if (trophy_milestone_entry(id, &entry))
            result = (Exhibit){entry.name, entry.description, entry.sheet, entry.frame, entry.palette, 0, 0, entry.earned};
    } else if (gArcadePage == TAB_CARDS) {
        if (!trophy_card_seen(id)) return result;
        const TradingCardDef* card = &gTradingCards[id];
        result = (Exhibit){card->name, card->description, NO_ENTRY, id, card->rarity, 0, 0, TRUE};
    } else {
        JournalEntry entry;
        bool8 found = gArcadePage == TAB_ITEMS ? journal_item_seen(id) : journal_enemy_seen(id);
        if (found && journal_entry(gArcadePage - TAB_ITEMS, id, &entry))
            result = (Exhibit){entry.name, entry.description, entry.sheet, entry.frame,
                               entry.palette, entry.hp, entry.damage, TRUE};
    }
    return result;
}

static void sync_cursor(void) {
    int index = MIN(sCursor[gArcadePage], MAX(0, gArcadeCount - 1));
    sCursor[gArcadePage] = index;
    gArcadeCursor = index;
    gArcadeTop = index / ROWS * ROWS;
    gArcadeEntry = gArcadeCount ? sOrder[index] : NO_ENTRY;
    gArcadeSeen = exhibit(gArcadeEntry).found;
}

static void build_list(int keep) {
    sTotal = tab_count();
    sFound = 0;
    gArcadeCount = 0;
    for (int i = 0; i < sTotal; i++) {
        int id = i;
        if (gArcadePage == TAB_ITEMS || gArcadePage == TAB_CREATURES)
            id = journal_list_id(gArcadePage - TAB_ITEMS, i);
        bool8 found = exhibit(id).found;
        sFound += found;
        if (gArcadeFilter && !found) continue;
        if (id == keep) sCursor[gArcadePage] = gArcadeCount;
        sOrder[gArcadeCount++] = id;
    }
    sync_cursor();
}

static int number(Canvas* canvas, int x, int y, int value, int ink) {
    char text[12];
    return vwf_text(canvas, x, y, vwf_num(text, value, 0), ink);
}

static void centered(Canvas* canvas, int x, int y, int width, const char* text, int ink) {
    vwf_text(canvas, x + MAX(0, (width - vwf_width(text)) / 2), y, text, ink);
}

static void fit(Canvas* canvas, int x, int y, int width, const char* text, int ink) {
    if (vwf_width(text) <= width) {
        vwf_text(canvas, x, y, text, ink);
        return;
    }
    char line[64];
    int n = MIN(vwf_fit(text, width - vwf_width("...") - 2), (int)sizeof(line) - 4);
    for (int i = 0; i < n; i++) line[i] = text[i];
    line[n++] = '.';
    line[n++] = '.';
    line[n++] = '.';
    line[n] = 0;
    vwf_text(canvas, x, y, line, ink);
}

static void place_backdrop(const u16* map, int x, int y, int w, int h) {
    for (int row = 0; row < h; row++)
        for (int col = 0; col < w; col++)
            gBg3[(y + row) * 32 + x + col] = *map++ | (CASE_PAL << 12);
}

static void exhibit_map(const Exhibit* selected) {
    u16 blank = EXHIBIT_BLANK | (EXHIBIT_PAL << 12);
    memset32(sExhibitMap, (u32)blank * 0x10001u, sizeof(sExhibitMap));
    gArcadePreviewTiles = 0;
    gArcadePreviewSheet = gArcadePreviewFrame = gArcadePreviewSourcePalette = NO_ENTRY;
    if (!selected->found && gArcadeCount) {
        const u16* stamp = gArcadeDetail ? trophy_case_detail_sealed : trophy_case_sealed;
        int left = gArcadeDetail ? 4 : 20;
        for (int y = 0; y < 4; y++)
            for (int x = 0; x < 4; x++)
                sExhibitMap[(7 + y) * 32 + left + x] = *stamp++ | (CASE_PAL << 12);
    } else if (selected->found) {
        int width, height;
        const u16* tiles;
        const u16* colors;
        if (gArcadePage == TAB_CARDS) {
            width = height = 48;
            tiles = trading_card_art[selected->frame];
            colors = trading_card_palettes[selected->frame];
        } else {
            const SpriteSheet* sheet = &sheets[selected->sheet];
            width = sheet->w;
            height = sheet->h;
            if (!sheet->frame_tiles || (selected->frame + 1) * sheet->frame_tiles > sheet->tile_count) goto done;
            if (selected->sheet == SHEET_ICON32) {
                tiles = icon32_exact_tiles + selected->frame * sheet->frame_tiles * 16;
                colors = icon32_exact_pal + selected->frame * 16;
            } else {
                tiles = sheet->tiles + selected->frame * sheet->frame_tiles * 16;
                colors = pal_obj + selected->palette * 16;
            }
        }
        int side = MAX(width, height);
        int extent = side <= 16 ? side * 2 : MIN(side, gArcadeDetail ? 48 : 40);
        int w = width * extent / side, h = height * extent / side;
        int left = (gArcadeDetail ? 30 : 36) - w / 2;
        int top = 50 - h; /* Pixels bottom-align to the brass shelf at y82. */
        Canvas art;
        vwf_canvas_obj(&art, sExhibitPixels, 0, EXHIBIT_WIDTH, EXHIBIT_HEIGHT);
        vwf_clear(&art, 0);
        const u32* source = (const u32*)tiles;
        int source_tw = width / 8;
        u8 sample[48];
        for (int x = 0; x < w; x++) sample[x] = x * width / w;
        for (int y = 0; y < h; y++) {
            int sy = y * height / h;
            const u32* source_row = source + (sy / 8) * source_tw * 8 + sy % 8;
            for (int x = 0; x < w; x++) {
                int sx = sample[x];
                vwf_pixel(&art, left + x, top + y, (source_row[(sx / 8) * 8] >> (sx % 8 * 4)) & 15);
            }
        }
        pal_set_bg(EXHIBIT_PAL, colors);
        vram_queue(sExhibitPixels, CHARBLOCK(3) + EXHIBIT_TILE * 16, sizeof(sExhibitPixels));
        const int preview_x = gArcadeDetail ? 2 : 18;
        for (int y = 0; y < EXHIBIT_HEIGHT; y++)
            for (int x = 0; x < EXHIBIT_WIDTH; x++)
                sExhibitMap[(4 + y) * 32 + preview_x + x] = (EXHIBIT_TILE + y * EXHIBIT_WIDTH + x) | (EXHIBIT_PAL << 12);
        gArcadePreviewSheet = selected->sheet;
        gArcadePreviewFrame = selected->frame;
        gArcadePreviewSourcePalette = selected->palette;
        gArcadePreviewTiles = EXHIBIT_WIDTH * EXHIBIT_HEIGHT;
    }
done:
    vram_queue(sExhibitMap, SCREENBLOCK(EXHIBIT_MAP), sizeof(sExhibitMap));
}

static void draw_header(void) {
    Canvas header, tabs;
    bg0_canvas(&header, 2, 1, 26, 1);
    vwf_text(&header, 2, 0, "TROPHY CASE", IVORY);
    char value[12];
    const char* label = gArcadeFilter ? "Found only" : "All entries";
    int x = 207 - vwf_width(label);
    vwf_text(&header, x, 0, label, GOLD);
    const char* count_word = gArcadePage == TAB_MILESTONES ? " earned" : " found";
    x -= vwf_width(count_word) + 12;
    vwf_text(&header, x, 0, count_word, IVORY);
    if (gArcadePage == TAB_MILESTONES || gArcadePage == TAB_CARDS) {
        const char* total = vwf_num(value, sTotal, 0);
        x -= vwf_width(total) + 1;
        vwf_text(&header, x, 0, total, IVORY);
        x -= 5;
        vwf_text(&header, x, 0, "/", GOLD);
    }
    const char* found = vwf_num(value, sFound, 0);
    vwf_text(&header, x - vwf_width(found) - 1, 0, found, IVORY);
    vwf_flush(&header, FALSE);
    bg0_canvas(&tabs, 1, 2, 26, 2);
    for (int i = 0; i < TAB_COUNT; i++) {
        centered(&tabs, i * 56, 3, 56, sTabs[i], i == gArcadePage ? IVORY : GOLD);
    }
    vwf_flush(&tabs, FALSE);
}

static const char* status(const Exhibit* selected) {
    if (gArcadeEntry == NO_ENTRY) return "No entries";
    if (!selected->found) return gArcadePage == TAB_MILESTONES ? "Unearned" : "Undiscovered";
    if (gArcadePage == TAB_CARDS) return sRarities[selected->palette];
    return gArcadePage == TAB_MILESTONES ? "Earned" : "Recorded";
}

static void draw_index(const Exhibit* selected) {
    Canvas list, plaque;
    bg0_canvas(&list, 2, 4, 11, 13);
    for (int row = 0; row < ROWS && gArcadeTop + row < gArcadeCount; row++) {
        int index = gArcadeTop + row;
        const Exhibit item = exhibit(sOrder[index]);
        if (item.found) {
            vwf_pixel(&list, 1, 15 + 16 * row, GOLD);
            vwf_pixel(&list, 2, 14 + 16 * row, GOLD);
            vwf_pixel(&list, 2, 15 + 16 * row, IVORY);
            vwf_pixel(&list, 2, 16 + 16 * row, GOLD);
            vwf_pixel(&list, 3, 15 + 16 * row, GOLD);
        }
        fit(&list, 7, 11 + 16 * row, 80, item.name ? item.name : "Undiscovered",
            item.found || index == gArcadeCursor ? IVORY : MUTED);
    }
    if (!gArcadeCount) centered(&list, 0, 37, 88, "No discoveries yet", IVORY);
    if (gArcadePage == TAB_MILESTONES) {
        int x = vwf_text(&list, 0, 92, "Rank ", GOLD);
        x = number(&list, x, 92, gHandoffState.rank, IVORY);
        x = number(&list, x + 5, 92, MIN(gHandoffState.score, 999999u), IVORY);
        vwf_text(&list, x, 92, " pts", GOLD);
    }
    if (gArcadeCount) {
        char size[12], pos[12];
        vwf_num(size, gArcadeCount, 0);
        vwf_num(pos, gArcadeCursor + 1, 0);
        int x = 88 - vwf_width(size) - vwf_width(pos) - 8;
        x = vwf_text(&list, x, 92, pos, IVORY);
        x = vwf_text(&list, x, 92, "/", GOLD);
        vwf_text(&list, x, 92, size, IVORY);
    }
    vwf_flush(&list, FALSE);

    bg0_canvas(&plaque, 17, 12, 11, 4);
    if (selected->name)
        vwf_block(&plaque, 0, 4, 88, 9, selected->name, IVORY, 2);
    else
        centered(&plaque, 0, 4, 88, gArcadeCount ? "Sealed exhibit" : "Empty shelf", IVORY);
    centered(&plaque, 0, 23, 88, status(selected), selected->found ? GOLD : MUTED);
    vwf_flush(&plaque, FALSE);
}

static const char* next_note_line(const char* text, int* length) {
    *length = vwf_fit(text, TEXT_WIDTH);
    text += *length;
    while (*text == ' ' || *text == '\n' || *text == '|') text++;
    return text;
}

static void draw_notes(const Exhibit* selected) {
    Canvas note, plaque;
    bg0_canvas(&plaque, 2, 12, 8, 3);
    centered(&plaque, 0, 5, 64, status(selected), GOLD);
    if (gArcadePage == TAB_CARDS && selected->found) {
        int x = vwf_text(&plaque, 2, 18, "Held ", IVORY);
        number(&plaque, x, 18, trading_card_count(gArcadeEntry), IVORY);
    }
    vwf_flush(&plaque, FALSE);

    bg0_canvas(&note, 11, 4, 17, 11);
    vwf_block(&note, 2, 3, TEXT_WIDTH, NOTE_PITCH, selected->name ? selected->name : "Sealed exhibit", IVORY, 2);
    const char* words = selected->notes;
    int y = 31;
    if (gArcadePage == TAB_CREATURES && selected->found) {
        if (selected->hp == 255) vwf_text(&note, 2, y, "Special defenses", GOLD);
        else {
            int x = vwf_text(&note, 2, y, "HP ", GOLD);
            x = number(&note, x, y, selected->hp, IVORY);
            x = vwf_text(&note, x + 7, y, "Contact ", GOLD);
            number(&note, x, y, selected->damage, IVORY);
        }
        y += 13;
    }
    if (!words) words = gArcadePage == TAB_CARDS ? "Find or receive this card to open its record."
                        : gArcadePage == TAB_ITEMS ? "Discover this item to open its record."
                        : "Encounter this creature to open its record.";
    int visible_lines = (80 - y) / NOTE_PITCH + 1;
    int lines = 0;
    for (const char* p = words; *p; ) {
        int length;
        p = next_note_line(p, &length);
        lines++;
    }
    sNoteLimit = MAX(0, lines - visible_lines);
    sNoteOffset = MIN(sNoteOffset, sNoteLimit);
    for (int line = 0; line < sNoteOffset; line++) {
        int length;
        words = next_note_line(words, &length);
    }
    for (int line = 0; line < visible_lines && *words; line++) {
        char buffer[64];
        int length;
        const char* next = next_note_line(words, &length);
        length = MIN(length, (int)sizeof(buffer) - 1);
        for (int i = 0; i < length; i++) buffer[i] = words[i];
        buffer[length] = 0;
        vwf_text(&note, 2, y + line * NOTE_PITCH, buffer, IVORY);
        words = next;
    }
    vwf_flush(&note, FALSE);
}

static void draw_footer(void) {
    Canvas foot;
    if (gArcadeDetail) {
        bg0_canvas(&foot, 5, 17, 19, 2);
        centered(&foot, 0, sNoteLimit ? 0 : 4, 152, "Left/Right  Exhibit    B  Back", IVORY);
        if (sNoteLimit) centered(&foot, 0, 8, 152, "Up/Down  Notes", GOLD);
    } else {
        bg0_canvas(&foot, 2, 17, 26, 2);
        centered(&foot, 0, 0, 208, "L/R Tabs   Up/Down Browse   A Inspect   B Exit", IVORY);
        centered(&foot, 0, 8, 208, "Left/Right Page   Select Filter   Start Options", GOLD);
    }
    vwf_flush(&foot, FALSE);
}

static void redraw(void) {
    const Exhibit selected = exhibit(gArcadeEntry);
    bg0_clear();
    bg0_pool_reset_full();
    place_backdrop(gArcadeDetail ? trophy_case_detail_map : trophy_case_map, 0, 0, 30, 20);
    place_backdrop(trophy_case_tab_focus, 1 + 7 * gArcadePage, 2, 7, 2);
    if (!gArcadeDetail && gArcadeCount)
        place_backdrop(trophy_case_focus, 1, 5 + 2 * (gArcadeCursor - gArcadeTop), 14, 2);
    gBg3Dirty = 1;
    draw_header();
    if (gArcadeDetail) draw_notes(&selected);
    else draw_index(&selected);
    draw_footer();
    exhibit_map(&selected);
}

static void arcade_close(void) {
    vram_flush_queue();
    REG_DISPCNT = DCNT_BLANK;
    REG_BG1CNT = sBg1;
    REG_BG3CNT = sBg3;
    for (int axis = 0; axis < 2; axis++) {
        gBgScroll[1][axis] = sScroll[0][axis];
        gBgScroll[3][axis] = sScroll[1][axis];
    }
    gAnimTiles = sOldAnim;
    pal_set_bg(CASE_PAL, sPalettes[0]);
    pal_set_bg(EXHIBIT_PAL, sPalettes[1]);
    pal_set_bg(UI_PAL, sPalettes[2]);
    bg0_clear();
    gBg3Dirty = 0;
    room_render();
    text_flush();
    video_flush();
    video_show(sDisplay);
    REG_BLDCNT = sBlend;
    REG_BLDALPHA = sAlpha;
    REG_BLDY = sBrightness;
    gGame.state = GS_PLAY;
    gKeysDown = 0;
}

void arcade_open(void) {
    if (arcade_active()) return;
    vram_flush_queue();
    sDisplay = REG_DISPCNT;
    sBg1 = REG_BG1CNT;
    sBg3 = REG_BG3CNT;
    sBlend = REG_BLDCNT;
    sAlpha = REG_BLDALPHA;
    sBrightness = REG_BLDY;
    sOldAnim = gAnimTiles;
    for (int axis = 0; axis < 2; axis++) {
        sScroll[0][axis] = gBgScroll[1][axis];
        sScroll[1][axis] = gBgScroll[3][axis];
        gBgScroll[1][axis] = gBgScroll[3][axis] = 0;
    }
    memcpy32(sPalettes[0], gPalBg + CASE_PAL * 16, 32);
    memcpy32(sPalettes[1], gPalBg + EXHIBIT_PAL * 16, 32);
    memcpy32(sPalettes[2], gPalBg + UI_PAL * 16, 32);
    REG_DISPCNT = DCNT_BLANK;
    REG_BG1CNT = BGCNT_PRIO(1) | BGCNT_CHARBASE(3) | BGCNT_SCREENBASE(EXHIBIT_MAP);
    REG_BG3CNT = BGCNT_PRIO(3) | BGCNT_CHARBASE(3) | BGCNT_SCREENBASE(22);
    REG_BLDCNT = REG_BLDY = 0;
    gAnimTiles = 0;
    pal_set_bg(CASE_PAL, trophy_case_palette);
    pal_set_bg(UI_PAL, trophy_case_palette);
    dma3_copy32(trophy_case_tiles, CHARBLOCK(3), sizeof(trophy_case_tiles));
    dma3_fill32(0, CHARBLOCK(3) + EXHIBIT_BLANK * 16, 32);
    gGame.state = GS_ARCADE;
    gArcadeDetail = 0;
    sRepeat = 0;
    sNoteOffset = 0;
    gKeysDown = 0;
    build_list(NO_ENTRY);
    redraw();
    vram_flush_queue();
    text_flush();
    video_flush();
    video_show(DCNT_BG0 | DCNT_BG1 | DCNT_BG3);
    sfx_play(SFX_MENU);
}

bool8 arcade_active(void) {
    return gGame.state == GS_ARCADE;
}

static u16 case_movement(void) {
    u16 pressed = gKeysDown & KEY_DPAD;
    u16 held = gKeysHeld & KEY_DPAD;
    if (pressed || !held) sRepeat = 18;
    else if (sRepeat) sRepeat--;
    else {
        sRepeat = 4;
        return held;
    }
    return pressed;
}

void arcade_update(void) {
    if (gKeysDown & KEY_B) {
        if (!gArcadeDetail) arcade_close();
        else {
            gArcadeDetail = 0;
            redraw();
        }
    } else if (!gArcadeDetail && (gKeysDown & KEY_START)) {
        arcade_close();
        handoff_open_run_options();
    } else if (gKeysDown & (KEY_L | KEY_R)) {
        gArcadePage = (gArcadePage + ((gKeysDown & KEY_R) ? 1 : TAB_COUNT - 1)) % TAB_COUNT;
        gArcadeDetail = 0;
        build_list(NO_ENTRY);
        redraw();
    } else if (!gArcadeDetail && (gKeysDown & KEY_SELECT)) {
        gArcadeFilter ^= 1;
        build_list(gArcadeEntry);
        redraw();
    } else if (!gArcadeDetail && (gKeysDown & KEY_A) && gArcadeCount) {
        gArcadeDetail = 1;
        sNoteOffset = 0;
        redraw();
    } else {
        u16 movement = case_movement();
        if (!movement) return;
        if (gArcadeDetail && !(movement & (KEY_LEFT | KEY_RIGHT))) {
            int offset = CLAMP(sNoteOffset + ((movement & KEY_UP) ? -1 : 1), 0, sNoteLimit);
            if (offset == sNoteOffset) return;
            sNoteOffset = offset;
            redraw();
            sfx_play(SFX_MENU);
            return;
        }
        int step = gArcadeDetail ? 1 : ROWS;
        int next = gArcadeCursor;
        if (movement & KEY_LEFT) next -= step;
        else if (movement & KEY_RIGHT) next += step;
        else if (movement & KEY_UP) next--;
        else if (movement & KEY_DOWN) next++;
        next = CLAMP(next, 0, MAX(0, gArcadeCount - 1));
        if (next == gArcadeCursor) return;
        sCursor[gArcadePage] = next;
        sNoteOffset = 0;
        sync_cursor();
        redraw();
    }
    sfx_play(SFX_MENU);
}

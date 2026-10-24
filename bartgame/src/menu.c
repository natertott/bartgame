/* BARTGAME: the pause menu, after The Minish Cap, on a backdrop of
   rotted planks. Three pages, R turns them: the items in a grid of four
   to a row that scrolls, with what a button holds shown over them and
   the chosen one described; the key items and the pieces of heart; and
   the map of the wood, drawn from the rooms themselves, that zooms into
   a cell to show what is marked there (its mouth into a mystery, who
   stands in it, a chest, a shrine, the Nun's relic once she has asked
   for it, and the Bloom). Select saves. */
#include "gba.h"
#include "video.h"
#include "util.h"
#include "room.h"
#include "actor.h"
#include "player.h"
#include "sound.h"
#include "text.h"
#include "world.h"
#include "roomgen.h"
#include "objects.h"
#include "game.h"
#include "save.h"
#include "menu.h"

/* BG3 carries the planks and the pictures: charblock 3, which the room
   maps own while the game plays and get back on the way out */
#define MENU_SB 22
#define MENU_PAL 8
#define PAL8 (MENU_PAL << 12)
#define PLANK_BASE 0
#define PIC_BASE 16
/* the overview: five cells of 32x24 at a pixel a tile, at (40, 32) */
#define OV_X 40
#define OV_Y 32
#define OV_W 160
#define OV_H 120
/* the zoomed cell: the interior 30x21 at four pixels a tile, at (60, 36) */
#define ZM_X 60
#define ZM_Y 36
#define ZM_W 120
#define ZM_H 84

/* the mask's kinds, as roomgen.c numbers them */
enum { M_WALL, M_FLOOR, M_WATER, M_BRIDGE_H, M_BRIDGE_V, M_LEDGE, M_RAMP, M_FALL };
#define P_MID 4

enum { PG_ITEMS, PG_KEYS, PG_MAP, PG_COUNT };
static u8 sPage, sZoom;
static u8 sCursor, sScroll;
static u8 sMapCur;
static u8 sSavedTimer;
static u8 sOverviewDone; /* the overview's tiles are in VRAM already */
static u16 sMarksTile, sDotsTile, sCursorTile;
static u16 sBg3[32 * 32] EWRAM_BSS;         /* BG3's map, built here and sent whole */
static u16 sTiles[(OV_W / 8) * (OV_H / 8) * 16] EWRAM_BSS; /* the picture's tiles, likewise */

typedef struct {
    u8 eq;          /* EQ_* when a button can hold it, else EQ_NONE */
    u16 bit;        /* owned when this bit of gPl.items is set; 0x100 and up: of gPl.items2; 0: always */
    u8 icon;        /* a frame of the items sheet, 0xFF: hud_equip_icon draws it */
    const char* name;
    const char* d1; /* what it is */
    const char* d2; /* what it does */
    const char* d3; /* how it is used */
} MenuItem;

static const MenuItem sItems[] = {
    { EQ_SWORD, ITEM_SWORD, 0xFF, "Sword", "A simple blade with a", "hopeful edge. Cuts bushes", "and turns seeds. Press it." },
    { EQ_SHIELD, ITEM_SHIELD, 0xFF, "Bark Shield", "Planks bound in brass.", "Turns bites and seeds", "from the front. Hold it." },
    { EQ_BOMBS, ITEM_BOMBS, F_ITEMS_BOMBS, "Blightseeds", "Seeds that burst. They", "open cracked walls and", "break stones. Press: set." },
    { EQ_LAMP, ITEM_LAMP, F_ITEMS_LAMP, "Grail Lamp", "A flame not of this wood.", "Burns webs and thorns,", "lights censers. Press it." },
    { EQ_CLOAK, ITEM_CLOAK, F_ITEMS_CLOAK, "Petal Cloak", "Petals that catch the air.", "Leaps chasms and pits.", "Press, walking, to jump." },
    { EQ_BOW, 0x100 | ITEM2_BOW, F_ITEMS_BOW, "Thorn Bow", "Yew and gut. An arrow for", "two hearts; walls stop it.", "Press to loose one." },
    { EQ_HUBCAP, 0x100 | ITEM2_HUBCAP, F_ITEMS_HUBCAP, "Drain Cap", "Iron from the hub. The", "muck opens and takes you", "home to the drain. Press." },
};
#define ITEM_COUNT ((int)(sizeof(sItems) / sizeof(sItems[0])))

static const MenuItem sKeys[] = {
    { EQ_NONE, 0, F_ITEMS_HEART_PIECE, "Pieces of Heart", "Quarters of a heart, from", "chests and mysteries.", "Four grow a whole heart." },
    { EQ_NONE, 0, F_ITEMS_KEY, "Small Keys", "The dead keep them, and", "chests do. Each opens one", "locked door: walk into it" },
    { EQ_NONE, ITEM_GAUNTLET, F_ITEMS_GAUNTLET, "Root Gauntlet", "Worn, not held. Roots", "that lift boulders out", "of the way: R before one." },
    { EQ_NONE, ITEM_RELIC, F_ITEMS_RELIC, "the Relic", "The Weeping Nun's, taken", "from another chamber.", "Bring it back to her." },
};
#define KEY_COUNT ((int)(sizeof(sKeys) / sizeof(sKeys[0])))

static const char* const sArchName[ARCH_COUNT] = { "a glade", "a grove", "ruins", "a pond", "a thicket", "a boneyard", "the Heart's glade", "the way in" };

static bool8 owned(const MenuItem* it) {
    if (it->bit == 0)
        return TRUE;
    if (it->bit >= 0x100)
        return (gPl.items2 & (it->bit >> 8)) != 0;
    return (gPl.items & it->bit) != 0;
}

/* the owned entries of a list, in order */
static int gather(const MenuItem* list, int n, u8* out) {
    int i, k = 0;
    for (i = 0; i < n; i++)
        if (owned(&list[i]))
            out[k++] = i;
    return k;
}

/* ------------------------------------------------------------ planks -- */
static void bg3_planks(void) {
    u16* map = sBg3;
    int x, y;
    dma3_copy32(menu_tiles, CHARBLOCK(3) + PLANK_BASE * 16, MENU_TILE_COUNT * 32);
    for (y = 0; y < 32; y++) {
        for (x = 0; x < 32; x++) {
            u32 h = hash32(x * 7 + 3, y * 13 + 5);
            int lower = y & 1, end = ((x + (y >> 1) * 3) & 7) == 6;
            u16 t;
            if (end)
                t = lower ? MN_PLANK_B_END : MN_PLANK_A_END;
            else if (lower)
                t = ((h & 15) == 0) ? MN_PLANK_MOSS : MN_PLANK_B;
            else
                t = ((h & 15) == 1) ? MN_PLANK_KNOT : ((h & 15) == 2) ? MN_PLANK_CRACK : MN_PLANK_A;
            map[y * 32 + x] = (PLANK_BASE + t) | PAL8 | ((!end && (h & 0x100)) ? 0x400 : 0);
        }
    }
    dma3_copy32(sBg3, SCREENBLOCK(MENU_SB), 32 * 32 * 2);
}

/* The pictures are built straight into tile words, four pixels at a
   time, from the masks: a byte a tile per cell, the trail in the high
   bit. The overview is a pixel a tile over the whole wood, the zoom
   four pixels a tile over one cell's interior. */
static u8 sMasks[CELLS][32 * 24] EWRAM_BSS;
static const u8 sColorOf[8] = { 7, 5, 8, 0xA, 0xA, 0xB, 0xA, 9 };

static u16 quad(u8 a, u8 b, u8 c, u8 d) {
    return a | (b << 4) | (c << 8) | (d << 12);
}

static u8 color_of(u8 v) {
    return (v & 0x80) ? 0xA : sColorOf[v & 7];
}

/* the cell's mask into sMasks, the gate openings marked as trail */
static void fetch_mask(int cell) {
    const u8* mask;
    const u8* path;
    Cell* c = &gWorld.cells[cell];
    u8* out = sMasks[cell];
    int i, s;
    roomgen_preview(cell, &mask, &path);
    for (i = 0; i < 32 * 24; i++)
        out[i] = mask[i] | ((path[i] & P_MID) ? 0x80 : 0);
    for (s = 0; s < 4; s++) {
        int x0, y0, x1, y1;
        if (c->gate[s] == GATE_WALL)
            continue;
        roomgen_gate_tiles(s, &x0, &y0, &x1, &y1);
        out[y0 * 32 + x0] = M_RAMP | 0x80;
        out[y1 * 32 + x1] = M_RAMP | 0x80;
        if (s == SIDE_N) {
            out[x0] = M_RAMP | 0x80;
            out[x1] = M_RAMP | 0x80;
        }
    }
}

/* the tiles in sTiles to VRAM, and their entries on BG3's map at (tx, ty) */
static void picture_show(int tx, int ty, int tw, int th) {
    int i, j;
    for (j = 0; j < th; j++)
        for (i = 0; i < tw; i++)
            sBg3[(ty + j) * 32 + tx + i] = (PIC_BASE + j * tw + i) | PAL8;
    dma3_copy32(sTiles, CHARBLOCK(3) + PIC_BASE * 16, tw * th * 32);
    dma3_copy32(sBg3, SCREENBLOCK(MENU_SB), 32 * 32 * 2);
}

/* the tiles are in VRAM already: only the map entries again, over the planks */
static void picture_show_again(int tx, int ty, int tw, int th) {
    int i, j;
    for (j = 0; j < th; j++)
        for (i = 0; i < tw; i++)
            sBg3[(ty + j) * 32 + tx + i] = (PIC_BASE + j * tw + i) | PAL8;
    dma3_copy32(sBg3, SCREENBLOCK(MENU_SB), 32 * 32 * 2);
}

/* the whole wood at a pixel a tile: visited cells as they are laid out,
   the rest parchment with a dotted edge */
static void overview_render(void) {
    static const u8 cy_of[15] = { 0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4 };
    static const u8 y_in[15] = { 0, 8, 16, 0, 8, 16, 0, 8, 16, 0, 8, 16, 0, 8, 16 };
    int i, j, y, k;
    for (i = 0; i < CELLS; i++)
        if (gWorld.cells[i].flags & CF_VISITED)
            fetch_mask(i);
    for (j = 0; j < OV_H / 8; j++) {
        for (i = 0; i < OV_W / 8; i++) {
            int cell = cy_of[j] * MAZE_W + (i >> 2), x0 = (i & 3) * 8;
            bool8 known = (gWorld.cells[cell].flags & CF_VISITED) != 0;
            const u8* m = sMasks[cell];
            u16* t = &sTiles[(j * (OV_W / 8) + i) * 16];
            for (y = 0; y < 8; y++) {
                int py = y_in[j] + y;
                u8 p[8];
                for (k = 0; k < 8; k++) {
                    int px = x0 + k;
                    if (known)
                        p[k] = color_of(m[py * 32 + px]);
                    else
                        p[k] = ((px == 0 || py == 0 || px == 31 || py == 23) && ((px + py) & 1)) ? 4 : 3;
                }
                t[y * 2] = quad(p[0], p[1], p[2], p[3]);
                t[y * 2 + 1] = quad(p[4], p[5], p[6], p[7]);
            }
        }
    }
    picture_show(OV_X / 8, OV_Y / 8, OV_W / 8, OV_H / 8);
}

/* a four-pixel run of one tile's colour, with water's light edge and a
   ledge's dark foot by the row within the tile */
static u16 run4(u8 col, int yin) {
    if (col == 8)
        return (yin == 0) ? quad(9, 9, 9, 9) : quad(9, 8, 8, 8);
    if (col == 0xB && yin == 3)
        return quad(7, 7, 7, 7);
    return quad(col, col, col, col);
}

/* one cell at four pixels a tile, its interior; unknown cells are parchment */
static void zoom_render(int cell) {
    Cell* c = &gWorld.cells[cell];
    int i, j, y;
    bool8 known = (c->flags & CF_VISITED) != 0;
    const u8* m = sMasks[cell];
    if (known)
        fetch_mask(cell);
    for (j = 0; j < (ZM_H + 7) / 8; j++) {
        for (i = 0; i < ZM_W / 8; i++) {
            u16* t = &sTiles[(j * (ZM_W / 8) + i) * 16];
            int mx = 1 + i * 2, my = 2 + j * 2;
            for (y = 0; y < 8; y++) {
                int row = my + (y >> 2);
                if (!known || row > 22) {
                    t[y * 2] = quad(3, 3, 3, 3);
                    t[y * 2 + 1] = quad(3, 3, 3, 3);
                } else {
                    t[y * 2] = run4(color_of(m[row * 32 + mx]), y & 3);
                    t[y * 2 + 1] = run4(color_of(m[row * 32 + mx + 1]), y & 3);
                }
            }
        }
    }
    picture_show(ZM_X / 8, ZM_Y / 8, ZM_W / 8, (ZM_H + 7) / 8);
}

/* ------------------------------------------------------------- pages -- */
static int strlen_(const char* s) {
    int n = 0;
    while (s[n])
        n++;
    return n;
}

static void page_header(const char* title, const char* hint) {
    bg0_fill(0, 3, 32, 17, 0);
    bg0_print_hud(1, 3, title);
    bg0_print_hud(29 - strlen_(hint), 3, hint);
}

static void slot_at(int tx, int ty, bool8 lit) {
    bg0_put(tx, ty, lit ? HT_SLOT_LIT_TL : HT_SLOT_TL);
    bg0_put(tx + 1, ty, lit ? HT_SLOT_LIT_TR : HT_SLOT_TR);
    bg0_put(tx, ty + 1, lit ? HT_SLOT_LIT_BL : HT_SLOT_BL);
    bg0_put(tx + 1, ty + 1, lit ? HT_SLOT_LIT_BR : HT_SLOT_BR);
}

static void describe(const MenuItem* it) {
    bg0_frame(1, 12, 28, 6);
    bg0_print_gold(3, 13, it->name);
    bg0_print(3, 14, it->d1);
    bg0_print(3, 15, it->d2);
    bg0_print(3, 16, it->d3);
}

/* the grid of four to a row: slots for the entries of rows sScroll and
   sScroll + 1, arrows where more rows lie above or below */
#define GRID_X(col) (3 + (col) * 6)
#define GRID_Y(row) (6 + ((row) - sScroll) * 3)
static void grid_draw(int count) {
    int i;
    for (i = 0; i < count; i++) {
        int row = i / 4, col = i % 4;
        if (row < sScroll || row > sScroll + 1)
            continue;
        slot_at(GRID_X(col), GRID_Y(row), i == sCursor);
    }
    if (sScroll > 0)
        bg0_put(27, 6, HT_ARROW | 0x800);
    if ((count + 3) / 4 > sScroll + 2)
        bg0_put(27, 10, HT_ARROW);
}

static void footer(const char* hint) {
    bg0_print_hud(2, 18, "R: next page");
    bg0_print_hud(18, 18, "Start: out");
    bg0_print_hud(2, 19, hint);
    bg0_print_hud(17, 19, sSavedTimer ? "      Saved." : "Select: save");
}

static void grid_icons(const MenuItem* list, const u8* idx, int count) {
    int i;
    for (i = 0; i < count; i++) {
        int row = i / 4, col = i % 4;
        const MenuItem* it = &list[idx[i]];
        if (row < sScroll || row > sScroll + 1)
            continue;
        if (it->icon == 0xFF)
            hud_equip_icon(it->eq, GRID_X(col) * 8, GRID_Y(row) * 8, 0);
        else
            draw_sprite(GRID_X(col) * 8, GRID_Y(row) * 8, SHEET_ITEMS, items_sheet_tile(), it->icon, 0, 0, PAL_OBJ_FX);
    }
}

static void items_page(void) {
    static u8 idx[ITEM_COUNT];
    int n = gather(sItems, ITEM_COUNT, idx), i;
    static const u8 slotx[SLOT_COUNT] = { 5, 11, 17 };
    page_header("ITEMS", "");
    if (sCursor >= n)
        sCursor = n ? n - 1 : 0;
    if (sCursor / 4 < sScroll)
        sScroll = sCursor / 4;
    if (sCursor / 4 > sScroll + 1)
        sScroll = sCursor / 4 - 1;
    /* what the buttons hold, beside the title */
    bg0_put(slotx[0] - 1, 4, HT_BTN_A);
    bg0_put(slotx[1] - 1, 4, HT_BTN_B);
    bg0_put(slotx[2] - 1, 4, HT_BTN_L);
    for (i = 0; i < SLOT_COUNT; i++)
        slot_at(slotx[i], 4, gPl.equip[i] != EQ_NONE);
    bg0_put(23, 4, HT_BTN_R);
    bg0_put(24, 4, HT_HAND);
    bg0_print_hud(25, 5, "lift");
    grid_draw(n);
    if (n) {
        const MenuItem* it = &sItems[idx[sCursor]];
        describe(it);
        if (it->eq == EQ_BOMBS || it->eq == EQ_BOW) {
            bg0_print(20, 13, "held");
            bg0_print_num(25, 13, it->eq == EQ_BOMBS ? gPl.bombs : gPl.arrows, 2);
        }
    }
    footer("A, B, L: take");
}

static void keys_page(void) {
    static u8 idx[KEY_COUNT];
    int n = gather(sKeys, KEY_COUNT, idx), i;
    page_header("KEY ITEMS", "");
    if (sCursor >= n)
        sCursor = n ? n - 1 : 0;
    sScroll = 0;
    /* the pieces of heart, lit as they are found, and the hearts grown */
    bg0_print_hud(2, 4, "pieces of heart");
    for (i = 0; i < 4; i++)
        bg0_put(18 + i, 4, (i < gPl.hearts_pieces) ? HT_HEART_FULL : HT_HEART_EMPTY);
    bg0_print_hud(21, 4, "hearts");
    bg0_print_num_hud(28, 4, gPl.hp_max / 8, 1);
    grid_draw(n);
    if (n) {
        const MenuItem* it = &sKeys[idx[sCursor]];
        describe(it);
        if (idx[sCursor] == 0) {
            bg0_print(20, 13, "found");
            bg0_print_num(26, 13, gPl.hearts_pieces, 1);
            bg0_print(27, 13, "/4");
        }
        if (idx[sCursor] == 1) {
            bg0_print(20, 13, "held");
            bg0_print_num(25, 13, gPl.keys, 2);
        }
    }
    footer("worn, not held");
}

static void map_banner(int cell) {
    Cell* c = &gWorld.cells[cell];
    bg0_frame(7, 16, 16, 3);
    if (c->flags & CF_VISITED)
        bg0_print(9, 17, sArchName[c->arch]);
    else if (cell == gWorld.entry)
        bg0_print(9, 17, "the way in");
    else
        bg0_print(9, 17, "unknown wood");
}

static void map_page(void) {
    page_header("THE WOOD", "");
    bg3_planks();
    if (sZoom) {
        zoom_render(sMapCur);
        sOverviewDone = 0;
    } else if (!sOverviewDone) {
        overview_render();
        sOverviewDone = 1;
    } else {
        picture_show_again(OV_X / 8, OV_Y / 8, OV_W / 8, OV_H / 8);
    }
    map_banner(sMapCur);
    footer(sZoom ? "B: back" : "A: look closer");
    /* the legend */
    bg0_print_hud(1, 7, "you");
    bg0_print_hud(1, 10, "door");
    bg0_print_hud(1, 13, "folk");
    bg0_print_hud(1, 16, "relic");
}

static void draw_page(void) {
    switch (sPage) {
        case PG_ITEMS: items_page(); break;
        case PG_KEYS: keys_page(); break;
        default: map_page(); break;
    }
}

/* ------------------------------------------------------------ sprites -- */
static void ensure_sheets(void) {
    if (!sMarksTile)
        sMarksTile = sprite_load_sheet(SHEET_MARKS);
    if (!sDotsTile)
        sDotsTile = sprite_load_sheet(SHEET_DOTS);
    if (!sCursorTile)
        sCursorTile = sprite_load_sheet(SHEET_CURSOR);
}

static void mark16(int px, int py, int frame) {
    draw_sprite(px - 8, py - 8, SHEET_MARKS, sMarksTile, frame, 0, 0, PAL_OBJ_UI);
}

static void dot8(int px, int py, int frame) {
    draw_sprite(px - 4, py - 4, SHEET_DOTS, sDotsTile, frame, 0, 0, PAL_OBJ_UI);
}

/* is the relic to be shown: the Nun has asked and it is not yet taken */
static int relic_cell(void) {
    int i, rc = -1, asked = 0;
    for (i = 0; i < CELLS; i++) {
        Cell* c = &gWorld.cells[i];
        if (c->role == ROLE_NPC_FETCH && (c->flags & CF_QUEST_ACTIVE) && !(c->flags & CF_QUEST_DONE))
            asked = 1;
        if (c->role == ROLE_RELIC && !(c->flags & CF_RELIC_TAKEN))
            rc = i;
    }
    return (asked && !(gPl.items & ITEM_RELIC)) ? rc : -1;
}

static bool8 quest_giver(const Cell* c) {
    return c->role == ROLE_NPC_HUNT || c->role == ROLE_NPC_FETCH || c->role == ROLE_NPC_TORCH;
}

static void map_sprites(void) {
    int i, rc = relic_cell();
    if (sZoom) {
        Cell* c = &gWorld.cells[sMapCur];
        const u8* m = gWorld.mark[sMapCur];
        if (c->flags & CF_VISITED) {
            if (m[MP_MOUTH * 2])
                mark16(ZM_X + (m[MP_MOUTH * 2] - 2) * 4 + 2, ZM_Y + (m[MP_MOUTH * 2 + 1] - 3) * 4 + 2, F_MARKS_DOOR);
            if (m[MP_NPC * 2])
                mark16(ZM_X + (m[MP_NPC * 2] - 2) * 4 + 2, ZM_Y + (m[MP_NPC * 2 + 1] - 3) * 4 + 2,
                       (quest_giver(c) && !(c->flags & CF_QUEST_DONE)) ? F_MARKS_QUEST : F_MARKS_FOLK);
            if (m[MP_CHEST * 2] && !(c->flags & CF_CHEST_OPEN))
                mark16(ZM_X + (m[MP_CHEST * 2] - 2) * 4 + 2, ZM_Y + (m[MP_CHEST * 2 + 1] - 3) * 4 + 2, F_MARKS_CHEST);
            if (m[MP_SHRINE * 2] && !(c->flags & CF_SHRINE_USED))
                mark16(ZM_X + (m[MP_SHRINE * 2] - 2) * 4 + 2, ZM_Y + (m[MP_SHRINE * 2 + 1] - 3) * 4 + 2, F_MARKS_HEART);
            if (rc == sMapCur && m[MP_RELIC * 2])
                mark16(ZM_X + (m[MP_RELIC * 2] - 2) * 4 + 2, ZM_Y + (m[MP_RELIC * 2 + 1] - 3) * 4 + 2, F_MARKS_RELIC);
        } else if (rc == sMapCur) {
            mark16(ZM_X + ZM_W / 2, ZM_Y + ZM_H / 2, F_MARKS_RELIC);
        }
        if (gGame.area == AREA_FOREST && gGame.cell == sMapCur)
            mark16(ZM_X + (PX(gPlayer->x) - 16) / 4, ZM_Y + (PX(gPlayer->y) - 32 - 8) / 4, F_MARKS_HERE);
        return;
    }
    /* the overview: the cursor, dots on what is known */
    draw_sprite(OV_X + (sMapCur % MAZE_W) * 32, OV_Y + (sMapCur / MAZE_W) * 24, SHEET_CURSOR, sCursorTile, F_CURSOR_CELL, 0, 0, PAL_OBJ_UI);
    for (i = 0; i < CELLS; i++) {
        Cell* c = &gWorld.cells[i];
        const u8* m = gWorld.mark[i];
        int ox = OV_X + (i % MAZE_W) * 32, oy = OV_Y + (i / MAZE_W) * 24;
        if (c->flags & CF_VISITED) {
            if (m[MP_MOUTH * 2])
                dot8(ox + m[MP_MOUTH * 2] - 1, oy + m[MP_MOUTH * 2 + 1] - 1, F_DOTS_DOOR);
            if (m[MP_NPC * 2])
                dot8(ox + m[MP_NPC * 2] - 1, oy + m[MP_NPC * 2 + 1] - 1, (quest_giver(c) && !(c->flags & CF_QUEST_DONE)) ? F_DOTS_QUEST : F_DOTS_FOLK);
        }
        if (rc == i)
            dot8(ox + ((c->flags & CF_VISITED) && m[MP_RELIC * 2] ? m[MP_RELIC * 2] - 1 : 16), oy + ((c->flags & CF_VISITED) && m[MP_RELIC * 2] ? m[MP_RELIC * 2 + 1] - 1 : 12), F_DOTS_RELIC);
    }
    if (gGame.area == AREA_FOREST)
        dot8(OV_X + (gGame.cell % MAZE_W) * 32 + PX(gPlayer->x) / 16, OV_Y + (gGame.cell / MAZE_W) * 24 + (PX(gPlayer->y) - 8) / 16, F_DOTS_HERE);
    else
        dot8(OV_X + (gWorld.entry % MAZE_W) * 32 + 16, OV_Y + (gWorld.entry / MAZE_W) * 24 + 22, F_DOTS_HERE);
    /* the legend */
    mark16(16, 44, F_MARKS_HERE);
    mark16(16, 68, F_MARKS_DOOR);
    mark16(16, 92, F_MARKS_QUEST);
    mark16(16, 116, F_MARKS_RELIC);
}

/* ------------------------------------------------------------- open -- */
void menu_open(void) {
    sPage = PG_ITEMS;
    sZoom = 0;
    sCursor = 0;
    sScroll = 0;
    sSavedTimer = 0;
    sOverviewDone = 0;
    sMapCur = (gGame.area == AREA_FOREST) ? gGame.cell : gWorld.entry;
    ensure_sheets();
    REG_BLDCNT = 0;
    REG_BLDY = 0;
    bg3_planks();
    draw_page();
    gGame.state = GS_MAP;
    video_show(DCNT_BG0 | DCNT_BG3 | DCNT_OBJ);
    sfx_play(SFX_MENU);
}

static void menu_close(void) {
    bg0_fill(0, 3, 32, 17, 0);
    room_render(); /* the room maps get their block back */
    video_show(DCNT_BG0 | DCNT_BG1 | DCNT_BG2 | DCNT_OBJ);
    gGame.state = GS_PLAY;
    gKeysDown = 0;
}

static void grid_move(int count) {
    int c = sCursor, moved = 0;
    if ((gKeysDown & KEY_RIGHT) && c + 1 < count) { c++; moved = 1; }
    if ((gKeysDown & KEY_LEFT) && c > 0) { c--; moved = 1; }
    if ((gKeysDown & KEY_DOWN) && c + 4 < count) { c += 4; moved = 1; }
    if ((gKeysDown & KEY_UP) && c >= 4) { c -= 4; moved = 1; }
    if (moved) {
        sCursor = c;
        sfx_play(SFX_MENU);
        draw_page();
    }
}

void menu_update(void) {
    static u8 idx[ITEM_COUNT];
    hud_draw();
    if (sSavedTimer && --sSavedTimer == 0)
        draw_page();
    if (gKeysDown & KEY_SELECT) {
        save_write();
        sSavedTimer = 90;
        sfx_play(SFX_SECRET);
        draw_page();
    }
    switch (sPage) {
        case PG_ITEMS: {
            int n = gather(sItems, ITEM_COUNT, idx), i;
            static const u8 slotx[SLOT_COUNT] = { 5, 11, 17 };
            for (i = 0; i < SLOT_COUNT; i++)
                hud_equip_icon(gPl.equip[i], slotx[i] * 8, 4 * 8, 0);
            grid_icons(sItems, idx, n);
            grid_move(n);
            if (n && (gKeysDown & (KEY_A | KEY_B | KEY_L))) {
                const MenuItem* it = &sItems[idx[sCursor]];
                int slot = (gKeysDown & KEY_A) ? SLOT_A : (gKeysDown & KEY_B) ? SLOT_B : SLOT_L;
                player_equip_set(slot, it->eq);
                sfx_play(SFX_ITEM);
                draw_page();
            }
            break;
        }
        case PG_KEYS: {
            int n = gather(sKeys, KEY_COUNT, idx);
            grid_icons(sKeys, idx, n);
            grid_move(n);
            break;
        }
        default: {
            map_sprites();
            if (sZoom) {
                if (gKeysDown & KEY_B) {
                    sZoom = 0;
                    sfx_play(SFX_MENU);
                    draw_page();
                }
            } else {
                int cx = sMapCur % MAZE_W, cy = sMapCur / MAZE_W, moved = 0;
                if ((gKeysDown & KEY_RIGHT) && cx + 1 < MAZE_W) { cx++; moved = 1; }
                if ((gKeysDown & KEY_LEFT) && cx > 0) { cx--; moved = 1; }
                if ((gKeysDown & KEY_DOWN) && cy + 1 < MAZE_H) { cy++; moved = 1; }
                if ((gKeysDown & KEY_UP) && cy > 0) { cy--; moved = 1; }
                if (moved) {
                    sMapCur = cy * MAZE_W + cx;
                    sfx_play(SFX_MENU);
                    map_banner(sMapCur);
                }
                if (gKeysDown & KEY_A) {
                    sZoom = 1;
                    sfx_play(SFX_ITEM);
                    draw_page();
                }
            }
            break;
        }
    }
    if (gKeysDown & KEY_R) {
        if (sPage == PG_MAP && sZoom) {
            sZoom = 0;
        } else {
            sPage = (sPage + 1) % PG_COUNT;
            sCursor = 0;
            sScroll = 0;
        }
        sfx_play(SFX_MENU);
        if (sPage != PG_MAP)
            bg3_planks();
        draw_page();
    }
    if (gKeysDown & KEY_START)
        menu_close();
}

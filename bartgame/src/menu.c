/* BARTGAME: the pause menu, after the boards' UI: three pages under
   tabs, R turns them, Start closes. The items in slots four to a row,
   what the buttons hold at the right and the chosen one described at
   the foot; the key items and the hearts; and the map of the wood,
   drawn from the rooms themselves on a navy grid, that zooms into a
   cell to show what is marked there. A mark stays while its business
   is open and goes when it is done: a mystery's mouth until the mystery
   is won, a quest giver until the quest is paid, a chest until opened,
   a shrine until used, the Nun's relic from her asking to its taking.
   The Map draws every cell; the Astrolabe adds the chests, the Heart
   and the barriers between rooms. Nothing is saved here: the game saves
   itself at a win and at a death.

   BG3 carries the panels and the map's picture (charblock 3, which the
   room maps own while the game plays and get back on the way out), the
   icons are sprites over it, and the words are on BG0 over them all. */
#include "gba.h"
#include "video.h"
#include "util.h"
#include "room.h"
#include "actor.h"
#include "player.h"
#include "sound.h"
#include "text.h"
#include "ui.h"
#include "world.h"
#include "roomgen.h"
#include "objects.h"
#include "myst.h"
#include "game.h"
#include "menu.h"

#define MAP_PAL PAL_SLOT_MAP
#define PIC_BASE (UI_BG3 + UI_TILE_COUNT) /* the map's picture after the kit */
#define PIC_X 2 /* the picture, in tiles */
#define PIC_Y 4
#define PIC_TW 20
#define PIC_TH 14
/* the overview: a cell 32x22 at a pixel a tile, its top and bottom rows
   left out, under a pixel of margin */
#define OV_X (PIC_X * 8)
#define OV_Y (PIC_Y * 8 + 1)
#define OV_CW 32
#define OV_CH 22
/* the zoomed cell: the interior 30x21 at five pixels a tile */
#define ZM_X (PIC_X * 8 + 5)
#define ZM_Y (PIC_Y * 8 + 3)
#define ZM_S 5
#define ZM_W (30 * ZM_S)
#define ZM_H (21 * ZM_S)

/* the mask's kinds, as roomgen.c numbers them */
enum { M_WALL, M_FLOOR, M_WATER, M_BRIDGE_H, M_BRIDGE_V, M_LEDGE, M_RAMP, M_FALL };
#define P_MID 4

/* the grid: four slots to a row, two rows */
#define GRID_TX(col) (2 + (col) * 5)
#define GRID_TY(row) (3 + (row) * 5)
#define GRID_ROWS 2
/* the chosen one's panel at the foot, its icon in a slot */
#define DESC_TY 13
#define DESC_SLOT_TY 14

enum { PG_ITEMS, PG_KEYS, PG_MAP, PG_COUNT };
static u8 sPage, sZoom;
static u8 sCursor;
static u8 sMapCur;
static u8 sOverviewDone;
static u16 sMarksTile, sDotsTile;
static u16 sTiles[PIC_TW * PIC_TH * 16] EWRAM_BSS;
static u8 sMasks[CELLS][32 * 24] EWRAM_BSS;
static Canvas sTabs, sDesc, sCount[2], sInfo, sLegend, sSide;
static u8 sCountAt[2]; /* the slots the counts are drawn over */

typedef struct {
    u8 eq;          /* EQ_* when a button can hold it, else EQ_NONE */
    u16 bit;        /* owned when this bit of gPl.items is set; 0x100 and up: of gPl.items2; 0: always */
    u8 icon;        /* a frame of the icon sheet */
    const char* name;
    const char* desc;
} MenuItem;

static const MenuItem sItems[] = {
    { EQ_SWORD, ITEM_SWORD, F_ICON32_SWORD, "Sword", "A simple blade with a hopeful edge. It cuts bushes and turns seeds back." },
    { EQ_SHIELD, ITEM_SHIELD, F_ICON32_SHIELD, "Bark Shield", "Planks bound in brass. Held up, it turns bites and seeds from the front." },
    { EQ_BOMBS, ITEM_BOMBS, F_ICON32_BOMBS, "Blightseeds", "Seeds that burst. They " INK_HIGH "open cracked walls" INK_BASE " and break the stones." },
    { EQ_LAMP, ITEM_LAMP, F_ICON32_LAMP, "Grail Lamp", "A flame not of this wood. It " INK_HIGH "burns webs and thorns" INK_BASE " and lights censers." },
    { EQ_CLOAK, ITEM_CLOAK, F_ICON32_CLOAK, "Petal Cloak", "Petals that catch the air. Press it walking to " INK_HIGH "leap a chasm" INK_BASE " or a pit." },
    { EQ_BOW, 0x100 | ITEM2_BOW, F_ICON32_BOW, "Thorn Bow", "Yew and gut. An arrow takes two hearts from a beast; the walls stop it." },
    { EQ_HUBCAP, 0x100 | ITEM2_HUBCAP, F_ICON32_HUBCAP, "Drain Cap", "Iron from the hub. The muck opens and " INK_HIGH "takes you home" INK_BASE " to the drain." },
};
#define ITEM_COUNT ((int)(sizeof(sItems) / sizeof(sItems[0])))

static const MenuItem sKeys[] = {
    { EQ_NONE, 0, F_ICON32_HEART_PIECE, "Pieces of Heart", "Quarters of a heart, from chests and mysteries. " INK_HIGH "Four grow a whole heart." INK_BASE },
    { EQ_NONE, 0, F_ICON32_KEY, "Small Keys", "The dead keep them, and chests. Each " INK_HIGH "opens a locked door" INK_BASE ": walk into it." },
    { EQ_NONE, ITEM_GAUNTLET, F_ICON32_GAUNTLET, "Root Gauntlet", "Worn, not held. Roots that " INK_HIGH "lift boulders" INK_BASE ": press R before one." },
    { EQ_NONE, ITEM_RELIC, F_ICON32_RELIC, "the Relic", "The Weeping Nun's, taken from another chamber. " INK_HIGH "Bring it back to her." INK_BASE },
    { EQ_NONE, 0x100 | ITEM2_MAP, F_ICON32_MAP, "Map of the Wood", "Every chamber drawn, seen or not. The marks still wait to be found." },
    { EQ_NONE, 0x100 | ITEM2_ASTROLABE, F_ICON32_ASTROLABE, "Astrolabe", "Brass that remembers. The map shows " INK_HIGH "chests, the Heart" INK_BASE " and the barriers." },
};
#define KEY_COUNT ((int)(sizeof(sKeys) / sizeof(sKeys[0])))

static const char* const sArchName[ARCH_COUNT] = { "a glade", "a grove", "ruins", "a pond", "a thicket", "a boneyard", "the Heart's glade", "the way in" };
static const char* const sTabName[PG_COUNT] = { "Items", "Key Items", "Map" };

static bool8 owned(const MenuItem* it) {
    if (it->bit == 0)
        return TRUE;
    if (it->bit >= 0x100)
        return (gPl.items2 & (it->bit >> 8)) != 0;
    return (gPl.items & it->bit) != 0;
}

static int gather(const MenuItem* list, int n, u8* out) {
    int i, k = 0;
    for (i = 0; i < n; i++)
        if (owned(&list[i]))
            out[k++] = i;
    return k;
}

/* ------------------------------------------------------------- frame -- */
/* the page's frame and its tabs, the open one gold, R's badge at the
   end. The tabs are drawn into a canvas on BG0, five pixels under the
   frame's edge, so the slots and the map clear them by a few. */
#define TAB_Y 5

static void page_frame(void) {
    int i, x = 0;
    ui_frame(gBg3, UI_BG3, 0, 0, 30, 20, FR_PANEL);
    bg0_canvas(&sTabs, 2, 0, 18, 3);
    for (i = 0; i < PG_COUNT; i++) {
        int w = vwf_width(sTabName[i]), n = ui_plate_tiles(w, 6);
        if (n < 4)
            n = 4;
        ui_plate_px(&sTabs, x, TAB_Y, n, i == sPage ? PL_TABON : PL_TAB);
        vwf_text(&sTabs, x + (n * 8 - w) / 2, TAB_Y + 4, sTabName[i], i == sPage ? UI_INK_DARK : UI_INK_CREAM);
        x += n * 8 + 6;
    }
    vwf_flush(&sTabs, FALSE);
    ui_tile(gBg3, UI_BG3, 27, 1, UI_BADGE_R, 0);
}

/* ---------------------------------------------------------- pictures -- */
static u16 quad(u8 a, u8 b, u8 c, u8 d) {
    return a | (b << 4) | (c << 8) | (d << 12);
}

/* the open ground of a mask: what is walked, swum or crossed */
static bool8 open_at(const u8* m, int x, int y) {
    if (x < 0 || y < 0 || x >= 32 || y >= 24)
        return FALSE;
    return (m[y * 32 + x] & 7) != M_WALL;
}

/* a tile of a mask as the map draws it: its kind, whether a path runs on
   it, and which of its sides are shut (a wall beyond) */
#define SH_N 0x10
#define SH_W 0x20
#define SH_S 0x40
#define SH_E 0x80

static u8 tile_desc(const u8* m, int x, int y) {
    u8 v = m[y * 32 + x];
    return (v & 7) | ((v & 0x80) ? 8 : 0) | (open_at(m, x, y - 1) ? 0 : SH_N) | (open_at(m, x - 1, y) ? 0 : SH_W) |
           (open_at(m, x, y + 1) ? 0 : SH_S) | (open_at(m, x + 1, y) ? 0 : SH_E);
}

/* a tile's colour on the map, 0 where the ground shows; (xin, yin) the
   pixel within it, last the last pixel of a side. The ways have a lit rim
   where the wall is above or left of them and a shadow where it is below
   or right, water a lit edge; the blight is violet. */
static u8 map_ink(u8 d, int xin, int yin, int last, bool8 blight) {
    int k = d & 7;
    bool8 lit, deep;
    if (k == M_WALL)
        return 0;
    if (k == M_FALL)
        return MAP_INK_OUTLINE;
    lit = (yin == 0 && (d & SH_N)) || (xin == 0 && (d & SH_W));
    deep = (yin == last && (d & SH_S)) || (xin == last && (d & SH_E));
    if (k == M_WATER)
        return lit ? MAP_INK_WATER_LIT : MAP_INK_WATER;
    if (k == M_BRIDGE_H || k == M_BRIDGE_V)
        return MAP_INK_BROWN;
    if (lit && !deep)
        return blight ? MAP_INK_BLIGHT_LIT : MAP_INK_LIT;
    if ((deep && !lit) || k == M_LEDGE)
        return blight ? MAP_INK_OUTLINE : MAP_INK_DEEP;
    if (d & 8)
        return blight ? MAP_INK_BLIGHT_LIT : MAP_INK_PALE;
    return blight ? MAP_INK_BLIGHT : MAP_INK_GREEN;
}

/* is the cell's layout to be drawn: visited, or the Map in hand */
static bool8 known(int cell) {
    return (gWorld.cells[cell].flags & CF_VISITED) || (gPl.items2 & ITEM2_MAP);
}

/* a cell's mask from the room generator, kept for the run: it is a pure
   function of the world's seed and the cell, and the first look at a map
   of every cell costs most of a second */
static u32 sMaskSeed, sMaskDone;

static void fetch_mask(int cell) {
    const u8* mask;
    const u8* path;
    Cell* c = &gWorld.cells[cell];
    u8* out = sMasks[cell];
    int i, s;
    if (sMaskSeed != gWorld.seed) {
        sMaskSeed = gWorld.seed;
        sMaskDone = 0;
    }
    if (sMaskDone & (1u << cell))
        return;
    sMaskDone |= 1u << cell;
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
    /* the overview's colour of each tile, in the mask's spare bits */
    {
        bool8 blight = roomgen_blighted(cell);
        int x, y;
        for (y = 0; y < 24; y++)
            for (x = 0; x < 32; x++)
                out[y * 32 + x] |= map_ink(tile_desc(out, x, y), 0, 0, 0, blight) << 3;
    }
}

static void picture_show(void) {
    int i, j;
    for (j = 0; j < PIC_TH; j++)
        for (i = 0; i < PIC_TW; i++)
            gBg3[(PIC_Y + j) * 32 + PIC_X + i] = (PIC_BASE + j * PIC_TW + i) | (MAP_PAL << 12);
    gBg3Dirty = 1;
}

static void picture_upload(void) {
    vram_queue(sTiles, CHARBLOCK(3) + PIC_BASE * 16, sizeof(sTiles));
    picture_show();
}

static void overview_render(void) {
    static s8 row_of[PIC_TH * 8], cell_y[PIC_TH * 8];
    bool8 kn[CELLS];
    int i, j, y, k;
    for (y = 0; y < PIC_TH * 8; y++) {
        int r = y - (OV_Y - PIC_Y * 8);
        row_of[y] = (r >= 0 && r < OV_CH * MAZE_H) ? r % OV_CH + 1 : -1;
        cell_y[y] = (r >= 0 && r < OV_CH * MAZE_H) ? r / OV_CH : 0;
    }
    for (i = 0; i < CELLS; i++) {
        kn[i] = known(i);
        if (kn[i])
            fetch_mask(i);
    }
    for (j = 0; j < PIC_TH; j++)
        for (y = 0; y < 8; y++) {
            int py = j * 8 + y, my = row_of[py], cy = cell_y[py];
            for (i = 0; i < PIC_TW; i++) {
                int cell = cy * MAZE_W + (i >> 2);
                const u8* row = (my >= 0 && kn[cell]) ? &sMasks[cell][my * 32 + (i & 3) * 8] : NULL;
                u16* t = &sTiles[(j * PIC_TW + i) * 16 + y * 2];
                u8 p[8];
                for (k = 0; k < 8; k++) {
                    u8 v = row ? (row[k] >> 3) & 15 : 0;
                    p[k] = v ? v : (k == 0 || y == 0) ? MAP_INK_GRID : MAP_INK_GROUND;
                }
                t[0] = quad(p[0], p[1], p[2], p[3]);
                t[1] = quad(p[4], p[5], p[6], p[7]);
            }
        }
    picture_upload();
}

static void zoom_render(int cell) {
    /* pixel to tile and to the pixel within it, without a divide */
    static u8 div5[PIC_TW * 8], mod5[PIC_TW * 8];
    static u8 desc[21][30];
    int i, j, y, k, d = 0, r = 0;
    bool8 kn = known(cell), blight = roomgen_blighted(cell);
    for (i = 0; i < PIC_TW * 8; i++) {
        div5[i] = d;
        mod5[i] = r;
        if (++r == ZM_S) {
            r = 0;
            d++;
        }
    }
    if (kn) {
        fetch_mask(cell);
        for (j = 0; j < 21; j++)
            for (i = 0; i < 30; i++)
                desc[j][i] = tile_desc(sMasks[cell], 1 + i, 2 + j);
    }
    for (j = 0; j < PIC_TH; j++)
        for (y = 0; y < 8; y++) {
            int py = j * 8 + y - (ZM_Y - PIC_Y * 8);
            bool8 in = kn && py >= 0 && py < ZM_H;
            const u8* drow = in ? desc[div5[py]] : NULL;
            int yin = in ? mod5[py] : 0;
            for (i = 0; i < PIC_TW; i++) {
                u16* t = &sTiles[(j * PIC_TW + i) * 16 + y * 2];
                u8 p[8];
                for (k = 0; k < 8; k++) {
                    int px = i * 8 + k - (ZM_X - PIC_X * 8);
                    u8 v = (drow && px >= 0 && px < ZM_W) ? map_ink(drow[div5[px]], mod5[px], yin, ZM_S - 1, blight) : 0;
                    p[k] = v ? v : (k == 0 || y == 0) ? MAP_INK_GRID : MAP_INK_GROUND;
                }
                t[0] = quad(p[0], p[1], p[2], p[3]);
                t[1] = quad(p[4], p[5], p[6], p[7]);
            }
        }
    picture_upload();
}

/* ------------------------------------------------------------- pages -- */
/* the slot's corner count, outlined over the icon */
static void slot_count(int k, int at, const char* s) {
    int tx = GRID_TX(at % 4) + 2, ty = GRID_TY(at / 4) + 2;
    if (!bg0_canvas(&sCount[k], tx, ty, 2, 2))
        return;
    vwf_text_fx(&sCount[k], 14 - vwf_width(s), 6, s, UI_INK_CREAM, UI_INK_DARK, FX_OUTLINE);
    vwf_flush(&sCount[k], FALSE);
    sCountAt[k] = at;
}

static void grid_draw(int count) {
    int i;
    for (i = 0; i < 4 * GRID_ROWS; i++)
        ui_frame(gBg3, UI_BG3, GRID_TX(i % 4), GRID_TY(i / 4), 4, 4, i >= count ? FR_EMPTY : i == sCursor ? FR_SEL : FR_SLOT);
    gBg3Dirty = 1;
}

static void grid_icons(const MenuItem* list, const u8* idx, int count) {
    int i;
    for (i = 0; i < count && i < 4 * GRID_ROWS; i++)
        draw_sprite(GRID_TX(i % 4) * 8, GRID_TY(i / 4) * 8, SHEET_ICON32, icon32_sheet_tile(), list[idx[i]].icon, 0, 1, PAL_OBJ_ICONS);
}

/* the chosen one at the foot: its icon in a slot, its name in gold and
   its words */
static void describe(const MenuItem* it) {
    vwf_clear(&sDesc, 0);
    vwf_text(&sDesc, 2, 5, it->name, UI_INK_GOLD);
    vwf_block(&sDesc, 2, 17, 162, 10, it->desc, UI_INK_CREAM, 2);
    vwf_flush(&sDesc, FALSE);
}

static void desc_panel(void) {
    ui_frame(gBg3, UI_BG3, 1, DESC_TY, 28, 6, FR_PANEL);
    ui_frame(gBg3, UI_BG3, 2, DESC_SLOT_TY, 4, 4, FR_SLOT);
    bg0_canvas(&sDesc, 7, DESC_TY, 21, 6);
}

/* what the three buttons hold, at the right of the grid */
#define SIDE_BADGE_TY(s) (4 + (s) * 3)

static void buttons_panel(void) {
    static const u8 badge[SLOT_COUNT] = { UI_BADGE_A, UI_BADGE_B, UI_BADGE_L };
    int s;
    ui_frame(gBg3, UI_BG3, 22, 3, 7, 9, FR_PANEL);
    for (s = 0; s < SLOT_COUNT; s++)
        ui_tile(gBg3, UI_BG3, 23, SIDE_BADGE_TY(s), badge[s], 0);
}

static void items_page(void) {
    static u8 idx[ITEM_COUNT];
    int n = gather(sItems, ITEM_COUNT, idx), i, k = 0;
    if (sCursor >= n)
        sCursor = n ? n - 1 : 0;
    grid_draw(n);
    buttons_panel();
    desc_panel();
    for (i = 0; i < n && k < 2; i++) {
        char buf[4];
        if (sItems[idx[i]].eq == EQ_BOMBS)
            slot_count(k++, i, vwf_num(buf, gPl.bombs, 0));
        else if (sItems[idx[i]].eq == EQ_BOW)
            slot_count(k++, i, vwf_num(buf, gPl.arrows, 0));
    }
    if (n)
        describe(&sItems[idx[sCursor]]);
}

/* the hearts grown and the pieces toward the next */
static void hearts_panel(void) {
    int i;
    ui_frame(gBg3, UI_BG3, 22, 3, 7, 9, FR_PANEL);
    bg0_canvas(&sSide, 23, 4, 5, 7);
    vwf_text(&sSide, 3, 0, "Hearts", UI_INK_GOLD);
    vwf_text(&sSide, 3, 30, "Pieces", UI_INK_GOLD);
    vwf_flush(&sSide, FALSE);
    for (i = 0; i < gPl.hp_max / 8 && i < 10; i++)
        bg0_put(23 + i % 5, 6 + i / 5, HT_HEART_FULL);
    for (i = 0; i < 4; i++)
        bg0_put(23 + i, 10, i < gPl.hearts_pieces ? HT_HEART_FULL : HT_HEART_EMPTY);
}

static void keys_page(void) {
    static u8 idx[KEY_COUNT];
    int n = gather(sKeys, KEY_COUNT, idx), i;
    char buf[6];
    if (sCursor >= n)
        sCursor = n ? n - 1 : 0;
    grid_draw(n);
    hearts_panel();
    desc_panel();
    for (i = 0; i < n; i++) {
        if (idx[i] == 0) {
            vwf_num(buf, gPl.hearts_pieces, 0);
            buf[1] = '/';
            buf[2] = '4';
            buf[3] = 0;
            slot_count(0, i, buf);
        } else if (idx[i] == 1) {
            slot_count(1, i, vwf_num(buf, gPl.keys, 0));
        }
    }
    if (n)
        describe(&sKeys[idx[sCursor]]);
}

static int explored(void) {
    int i, k = 0;
    for (i = 0; i < CELLS; i++)
        if (gWorld.cells[i].flags & CF_VISITED)
            k++;
    return k * 100 / CELLS;
}

/* the cell under the cursor and how much of the wood is seen */
static void map_info(int cell) {
    Cell* c = &gWorld.cells[cell];
    const char* name = known(cell) ? sArchName[c->arch] : (cell == gWorld.entry) ? "the way in" : "unknown wood";
    char buf[8];
    int x;
    vwf_clear(&sInfo, 0);
    vwf_block(&sInfo, 5, 5, 37, 9, name, known(cell) ? UI_INK_CREAM : UI_INK_DIM, 2);
    x = vwf_text(&sInfo, 5, 26, vwf_num(buf, explored(), 0), UI_INK_GOLD);
    vwf_text(&sInfo, x, 26, "%", UI_INK_GOLD);
    vwf_text(&sInfo, 5, 36, "seen", UI_INK_DIM);
    vwf_flush(&sInfo, FALSE);
}

static const char* const sLegendName[7] = { "You", "Door", "Quest", "Folk", "Chest", "Relic", "Heart" };
static const u8 sLegendDot[7] = { F_DOTS_HERE, F_DOTS_DOOR, F_DOTS_QUEST, F_DOTS_FOLK, F_DOTS_CHEST, F_DOTS_RELIC, F_DOTS_BOSS };

static void map_page(void) {
    int i;
    ui_frame(gBg3, UI_BG3, 1, 3, 22, 16, FR_PANEL);
    ui_frame(gBg3, UI_BG3, 23, 3, 6, 6, FR_PANEL);
    ui_frame(gBg3, UI_BG3, 23, 9, 6, 10, FR_PANEL);
    bg0_canvas(&sInfo, 23, 3, 6, 6);
    map_info(sMapCur);
    bg0_canvas(&sLegend, 24, 9, 5, 10);
    for (i = 0; i < 7; i++)
        vwf_text(&sLegend, 10, 4 + i * 10, sLegendName[i], UI_INK_CREAM);
    vwf_flush(&sLegend, FALSE);
    if (sZoom) {
        zoom_render(sMapCur);
        sOverviewDone = 0;
    } else if (!sOverviewDone) {
        overview_render();
        sOverviewDone = 1;
    } else {
        picture_upload();
    }
}

static void draw_page(void) {
    bg0_clear();
    bg0_pool_reset();
    ui_backdrop_clear();
    page_frame();
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
}

static void mark16(int px, int py, int frame) {
    draw_sprite(px - 8, py - 8, SHEET_MARKS, sMarksTile, frame, 0, 0, PAL_OBJ_UI);
}

static void dot8(int px, int py, int frame) {
    draw_sprite(px - 4, py - 4, SHEET_DOTS, sDotsTile, frame, 0, 0, PAL_OBJ_UI);
}

/* a corner of the cell cursor, turned to its corner */
static void corner(int x, int y, bool8 hf, bool8 vf) {
    OamEntry* o = oam_alloc();
    if (!o)
        return;
    o->attr0 = ATTR0_Y(y) | ATTR0_SQUARE;
    o->attr1 = ATTR1_X(x) | ATTR1_SIZE(0) | (hf ? ATTR1_HFLIP : 0) | (vf ? ATTR1_VFLIP : 0);
    o->attr2 = ATTR2_TILE(OBJ_TILE_UI + F_UIMARKS_CORNER) | ATTR2_PRIO(0) | ATTR2_PAL(PAL_OBJ_UIKIT);
}

static void cell_cursor(int cell) {
    int x0 = OV_X + (cell % MAZE_W) * OV_CW - 1, y0 = OV_Y + (cell / MAZE_W) * OV_CH - 1;
    int x1 = x0 + OV_CW + 2 - 8, y1 = y0 + OV_CH + 2 - 8;
    corner(x0, y0, FALSE, FALSE);
    corner(x1, y0, TRUE, FALSE);
    corner(x0, y1, FALSE, TRUE);
    corner(x1, y1, TRUE, TRUE);
}

/* the relic's cell while the Nun has asked and it is not yet taken, else -1 */
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

static bool8 has_chest(const Cell* c) {
    return (c->role == ROLE_CHEST || c->role == ROLE_KEYITEM || c->role == ROLE_KEYCHEST) && !(c->flags & CF_CHEST_OPEN);
}

/* a barrier's mark, or -1 for an open way */
static int gate_mark(int cell, int side) {
    int g = gWorld.cells[cell].gate[side];
    if (g == GATE_WALL || g == GATE_OPEN || g == GATE_EXIT || world_gate_open(cell, side))
        return -1;
    switch (g) {
        case GATE_THORN: return F_MARKS_THORN;
        case GATE_CRACK: return F_MARKS_CRACK;
        case GATE_WEB: return F_MARKS_WEB;
        case GATE_LOCK: return F_MARKS_LOCK;
        default: return F_MARKS_CHASM;
    }
}

static int gate_dot(int mark) {
    switch (mark) {
        case F_MARKS_THORN: return F_DOTS_THORN;
        case F_MARKS_CRACK: return F_DOTS_CRACK;
        case F_MARKS_WEB: return F_DOTS_WEB;
        case F_MARKS_LOCK: return F_DOTS_LOCK;
        default: return F_DOTS_CHASM;
    }
}

/* a mark's place in the zoom, from a tile */
static int zx(int tx) { return ZM_X + (tx - 1) * ZM_S + ZM_S / 2; }
static int zy(int ty) { return ZM_Y + (ty - 2) * ZM_S + ZM_S / 2; }

/* and in the overview, from a cell's tile: its top and bottom rows are
   not drawn */
static int ox_of(int cell, int tx) { return OV_X + (cell % MAZE_W) * OV_CW + tx; }
static int oy_of(int cell, int ty) { return OV_Y + (cell / MAZE_W) * OV_CH + CLAMP(ty - 1, 0, OV_CH - 1); }

static void legend_sprites(void) {
    int i;
    for (i = 0; i < 7; i++)
        dot8(24 * 8 + 3, 9 * 8 + 8 + i * 10, sLegendDot[i]);
}

static void zoom_sprites(void) {
    Cell* c = &gWorld.cells[sMapCur];
    const u8* m = gWorld.mark[sMapCur];
    bool8 visited = (c->flags & CF_VISITED) != 0, astro = (gPl.items2 & ITEM2_ASTROLABE) != 0;
    int rc = relic_cell(), s;
    if (visited) {
        if (m[MP_MOUTH * 2] && !(gWorld.myst_flags[sMapCur] & MF_DONE))
            mark16(zx(m[MP_MOUTH * 2] - 1), zy(m[MP_MOUTH * 2 + 1] - 1), F_MARKS_DOOR);
        if (m[MP_NPC * 2] && !(quest_giver(c) && (c->flags & CF_QUEST_DONE)))
            mark16(zx(m[MP_NPC * 2] - 1), zy(m[MP_NPC * 2 + 1] - 1), quest_giver(c) ? F_MARKS_QUEST : F_MARKS_FOLK);
        if (m[MP_CHEST * 2] && has_chest(c))
            mark16(zx(m[MP_CHEST * 2] - 1), zy(m[MP_CHEST * 2 + 1] - 1), F_MARKS_CHEST);
        if (m[MP_SHRINE * 2] && !(c->flags & CF_SHRINE_USED))
            mark16(zx(m[MP_SHRINE * 2] - 1), zy(m[MP_SHRINE * 2 + 1] - 1), F_MARKS_HEART);
        if (rc == sMapCur && m[MP_RELIC * 2])
            mark16(zx(m[MP_RELIC * 2] - 1), zy(m[MP_RELIC * 2 + 1] - 1), F_MARKS_RELIC);
    } else {
        if (rc == sMapCur)
            mark16(zx(16), zy(12), F_MARKS_RELIC);
        if (astro && has_chest(c))
            mark16(zx(16), zy(12), F_MARKS_CHEST);
    }
    if (astro && sMapCur == gWorld.goal && !(c->flags & CF_CLEARED))
        mark16(zx(16), zy(11), F_MARKS_BOSS);
    if (astro)
        for (s = 0; s < 4; s++) {
            int mk = gate_mark(sMapCur, s), x0, y0, x1, y1;
            if (mk < 0)
                continue;
            roomgen_gate_tiles(s, &x0, &y0, &x1, &y1);
            mark16((zx(x0) + zx(x1)) / 2, (zy(y0) + zy(y1)) / 2, mk);
        }
    if (gGame.area == AREA_FOREST && gGame.cell == sMapCur)
        mark16(ZM_X + (PX(gPlayer->x) - 16) * ZM_S / 16, ZM_Y + (PX(gPlayer->y) - 8 - 32) * ZM_S / 16, F_MARKS_HERE);
}

static void overview_sprites(void) {
    int i, rc = relic_cell();
    bool8 astro = (gPl.items2 & ITEM2_ASTROLABE) != 0;
    cell_cursor(sMapCur);
    if (gGame.area == AREA_FOREST)
        dot8(ox_of(gGame.cell, PX(gPlayer->x) / 16), oy_of(gGame.cell, (PX(gPlayer->y) - 8) / 16), F_DOTS_HERE);
    else
        dot8(ox_of(gWorld.entry, 16), oy_of(gWorld.entry, 22), F_DOTS_HERE);
    for (i = 0; i < CELLS; i++) {
        Cell* c = &gWorld.cells[i];
        const u8* m = gWorld.mark[i];
        int s;
        bool8 visited = (c->flags & CF_VISITED) != 0;
        if (visited) {
            if (m[MP_MOUTH * 2] && !(gWorld.myst_flags[i] & MF_DONE))
                dot8(ox_of(i, m[MP_MOUTH * 2] - 1), oy_of(i, m[MP_MOUTH * 2 + 1] - 1), F_DOTS_DOOR);
            if (m[MP_NPC * 2] && !(quest_giver(c) && (c->flags & CF_QUEST_DONE)))
                dot8(ox_of(i, m[MP_NPC * 2] - 1), oy_of(i, m[MP_NPC * 2 + 1] - 1), quest_giver(c) ? F_DOTS_QUEST : F_DOTS_FOLK);
            if (astro && m[MP_CHEST * 2] && has_chest(c))
                dot8(ox_of(i, m[MP_CHEST * 2] - 1), oy_of(i, m[MP_CHEST * 2 + 1] - 1), F_DOTS_CHEST);
        } else if (astro && has_chest(c)) {
            dot8(ox_of(i, 16), oy_of(i, 12), F_DOTS_CHEST);
        }
        if (rc == i) {
            bool8 at = visited && m[MP_RELIC * 2];
            dot8(ox_of(i, at ? m[MP_RELIC * 2] - 1 : 16), oy_of(i, at ? m[MP_RELIC * 2 + 1] - 1 : 12), F_DOTS_RELIC);
        }
        if (astro && i == gWorld.goal && !(c->flags & CF_CLEARED))
            dot8(ox_of(i, 16), oy_of(i, 11), F_DOTS_BOSS);
        if (astro)
            for (s = 0; s < 4; s++) {
                int mk = gate_mark(i, s);
                if (mk < 0 || (s != SIDE_N && s != SIDE_W))
                    continue;
                dot8(s == SIDE_N ? ox_of(i, 16) : ox_of(i, 1), s == SIDE_N ? oy_of(i, 1) : oy_of(i, 12), gate_dot(mk));
            }
    }
}

/* -------------------------------------------------------------- open -- */
void menu_open(void) {
    sPage = PG_ITEMS;
    sZoom = 0;
    sCursor = 0;
    sOverviewDone = 0;
    sMapCur = (gGame.area == AREA_FOREST) ? gGame.cell : gWorld.entry;
    ensure_sheets();
    icon32_sheet_tile();
    REG_BLDCNT = 0;
    REG_BLDY = 0;
    video_show(DCNT_BG0 | DCNT_BG3 | DCNT_OBJ);
    ui_backdrop_open();
    draw_page();
    gGame.state = GS_MAP;
    sfx_play(SFX_MENU);
}

static void menu_close(void) {
    bg0_clear();
    room_render(); /* the room maps get their block back */
    video_show(DCNT_BG0 | DCNT_BG1 | DCNT_BG2 | DCNT_OBJ);
    gGame.state = GS_PLAY;
    gKeysDown = 0;
}

/* the cursor about the grid: the slots' frames and the words redrawn */
static void grid_move(const MenuItem* list, const u8* idx, int count) {
    int c = sCursor, moved = 0;
    if ((gKeysDown & KEY_RIGHT) && c + 1 < count) { c++; moved = 1; }
    if ((gKeysDown & KEY_LEFT) && c > 0) { c--; moved = 1; }
    if ((gKeysDown & KEY_DOWN) && c + 4 < count) { c += 4; moved = 1; }
    if ((gKeysDown & KEY_UP) && c >= 4) { c -= 4; moved = 1; }
    if (moved) {
        sCursor = c;
        sfx_play(SFX_MENU);
        grid_draw(count);
        describe(&list[idx[c]]);
    }
}

void menu_update(void) {
    static u8 idx[ITEM_COUNT];
    switch (sPage) {
        case PG_ITEMS: {
            int n = gather(sItems, ITEM_COUNT, idx), s;
            grid_icons(sItems, idx, n);
            if (n)
                draw_sprite(2 * 8, DESC_SLOT_TY * 8, SHEET_ICON32, icon32_sheet_tile(), sItems[idx[sCursor]].icon, 0, 1, PAL_OBJ_ICONS);
            for (s = 0; s < SLOT_COUNT; s++)
                hud_equip_icon(gPl.equip[s], 25 * 8, SIDE_BADGE_TY(s) * 8 - 4, 1);
            grid_move(sItems, idx, n);
            if (n && (gKeysDown & (KEY_A | KEY_B | KEY_L))) {
                const MenuItem* it = &sItems[idx[sCursor]];
                int slot = (gKeysDown & KEY_A) ? SLOT_A : (gKeysDown & KEY_B) ? SLOT_B : SLOT_L;
                player_equip_set(slot, it->eq);
                sfx_play(SFX_ITEM);
            }
            break;
        }
        case PG_KEYS: {
            int n = gather(sKeys, KEY_COUNT, idx);
            grid_icons(sKeys, idx, n);
            if (n)
                draw_sprite(2 * 8, DESC_SLOT_TY * 8, SHEET_ICON32, icon32_sheet_tile(), sKeys[idx[sCursor]].icon, 0, 1, PAL_OBJ_ICONS);
            grid_move(sKeys, idx, n);
            break;
        }
        default: {
            legend_sprites();
            if (sZoom) {
                zoom_sprites();
                if (gKeysDown & KEY_B) {
                    sZoom = 0;
                    sfx_play(SFX_MENU);
                    draw_page();
                }
            } else {
                int cx = sMapCur % MAZE_W, cy = sMapCur / MAZE_W, moved = 0;
                overview_sprites();
                if ((gKeysDown & KEY_RIGHT) && cx + 1 < MAZE_W) { cx++; moved = 1; }
                if ((gKeysDown & KEY_LEFT) && cx > 0) { cx--; moved = 1; }
                if ((gKeysDown & KEY_DOWN) && cy + 1 < MAZE_H) { cy++; moved = 1; }
                if ((gKeysDown & KEY_UP) && cy > 0) { cy--; moved = 1; }
                if (moved) {
                    sMapCur = cy * MAZE_W + cx;
                    sfx_play(SFX_MENU);
                    map_info(sMapCur);
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
        }
        sfx_play(SFX_MENU);
        draw_page();
    }
    if (gKeysDown & KEY_START)
        menu_close();
}

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
#include "menu_studies.h"

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
/* The page's frame and tabs, with a theme-aware selected ink and R's
   badge at the end. The tabs are drawn into a canvas on BG0, five pixels under the
   frame's edge, so the slots and the map clear them by a few. */
#define TAB_Y 5

static void page_frame(void) {
    int i, x = 0;
    /* Legacy tabs have a bright gold selected field; the new themes use
       their normal base field. HIGH is light on the dark studies and dark
       on vellum, so the selected label remains readable in all five. */
    int selected_ink = BART_UI_VARIANT ? UI_INK_HIGH : UI_INK_DARK;
    ui_frame(gBg3, UI_BG3, 0, 0, 30, 20, FR_PANEL);
    bg0_canvas(&sTabs, 2, 0, 18, 3);
    for (i = 0; i < PG_COUNT; i++) {
        int w = vwf_width(sTabName[i]), n = ui_plate_tiles(w, 6);
        if (n < 4)
            n = 4;
        ui_plate_px(&sTabs, x, TAB_Y, n, i == sPage ? PL_TABON : PL_TAB);
        vwf_text(&sTabs, x + (n * 8 - w) / 2, TAB_Y + 4, sTabName[i], i == sPage ? selected_ink : UI_INK_CREAM);
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
    /* These figures float over variable item art, rather than a guaranteed
       pale/dark panel. Use a light ink with a dark contour in every theme. */
    vwf_text_fx(&sCount[k], 14 - vwf_width(s), 6, s, UI_INK_PALE, UI_INK_DARK, FX_OUTLINE);
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
    for (i = 0; i < count && i < 4 * GRID_ROWS; i++) {
        int frame=list[idx[i]].eq==EQ_SHIELD?player_shield_icon():list[idx[i]].icon;
        draw_sprite(GRID_TX(i % 4) * 8, GRID_TY(i / 4) * 8, SHEET_ICON32, icon32_frame_tile(frame), 0, 0, 1, icon32_frame_palette(frame));
    }
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
    bg0_pool_reset_full();
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
    /* The allocator's cache resets on every room load. Resolve these
       again so reopening the map cannot reuse another room's tile bases. */
    sMarksTile = sprite_load_sheet(SHEET_MARKS);
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

#if BART_MENU_VARIANT
/* Optional layout studies borrow paused-world BG character memory. The full
   native 240x160 page fits600 4bpp tiles across charblocks0/1. We retain those
   world bytes and HUD-resident icon bytes, then restore them on return. */
#define MS_TILES (30*20)
static u32 sStudyPixels[MS_TILES*8] EWRAM_BSS;
static u32 sStudyWorld[32768/4] EWRAM_BSS;
static u32 sStudyBase[3][MS_TILES*8] EWRAM_BSS;
static u8 sStudyBaseReady;
static u32 sStudyMapPicture[MS_TILES*8] EWRAM_BSS;
static MSRect sStudyMapRect;
static u8 sStudyMapMode,sStudyMapReady;
static u32 sStudyHud[60*8] EWRAM_BSS;
static Canvas sStudyCanvas;
static u16 sStudyBg3;
static u8 sStudyAnim,sStudyHaveFocus,sStudyFocus[2];
static u32 sStudySeed;
static const MenuLayout* sStudy;
/* Word-based native drawing keeps cursor updates within a video frame;
   the VBlank latch also retains quick taps while a cold terrain map charts. */
static u32 sStudyKit[4][UI_TILE_COUNT][8] EWRAM_BSS;
static u32 sStudyKitMask[4][UI_TILE_COUNT][8] EWRAM_BSS;
static u32 sStudyBitMask[256] EWRAM_BSS;
static u8 sStudyKitReady;
static void (*sStudyOldHook)(void);
static volatile u16 sStudyInput[32];
static volatile u8 sStudyInputRead,sStudyInputWrite;
static u16 sStudyHeld;
u16 gMenuStudyDrawFrames;
static void ms_input_irq(void){
    u16 now=~REG_KEYINPUT&KEY_ANY,down=now&~sStudyHeld;
    if(down){u8 next=(sStudyInputWrite+1)&31;if(next!=sStudyInputRead){sStudyInput[sStudyInputWrite]=down;sStudyInputWrite=next;}}
    sStudyHeld=now;if(sStudyOldHook)sStudyOldHook();
}
static void ms_cache_kit(void){
    int b,f,t,y,i;
    if(sStudyKitReady)return;
    for(b=0;b<256;b++){u32 w=0;for(i=0;i<8;i++)if(b&(1<<i))w|=15u<<(i*4);sStudyBitMask[b]=w;}
    for(f=0;f<4;f++)for(t=0;t<UI_TILE_COUNT;t++)for(y=0;y<8;y++){
        const u32* src=(const u32*)ui_tiles+t*8;u32 w=src[f&2?7-y:y],o=0,m=0;
        for(i=0;i<8;i++){int v=(w>>(i*4))&15,shift=(f&1?7-i:i)*4;o|=(u32)v<<shift;if(v)m|=15u<<shift;}
        sStudyKit[f][t][y]=o;sStudyKitMask[f][t][y]=m;
    }sStudyKitReady=1;
}
static void ms_kit(int tx,int ty,int tile,int flip){
    u32* dst=sStudyPixels+(ty*30+tx)*8;const u32* src=sStudyKit[flip][tile],*mask=sStudyKitMask[flip][tile];int y;
    for(y=0;y<8;y++)dst[y]=mask[y]==~0u?src[y]:(dst[y]&~mask[y])|src[y];
}
static int ms_glyph(int x,int y,int ch,int ink){
    int g,r,shift=(x&7)*4;
    if(ch==' ')return VWF_SPACE;
    g=(ch&255)-VWF_FIRST;if(g<0||g>=VWF_COUNT)g='?'-VWF_FIRST;
    for(r=0;r<VWF_HEIGHT;r++)if(y+r>=0&&y+r<160&&x>=0&&x<240){
        u32 mask=sStudyBitMask[vwf_bits[g*VWF_HEIGHT+r]],word=(mask&0x11111111u)*(ink&15);u32* d=sStudyPixels+(((y+r)>>3)*30+(x>>3))*8+((y+r)&7);
        d[0]=(d[0]&~(mask<<shift))|(word<<shift);
        if(shift&&x+8<248){u32 hi=mask>>(32-shift);if(hi&&x/8<29)d[8]=(d[8]&~hi)|(word>>(32-shift));}
    }return vwf_w[g]+1;
}
static int ms_text(int x,int y,const char* s,int base){
    int ink=base;for(;*s;s++){u8 ch=*s;if(ch<32)ink=vwf_ink(ch,base);else x+=ms_glyph(x,y,ch,ink);}return x;
}
static void menu_close(void);

static bool8 ms_valid(MSRect r){return r.w>0 && r.h>0;}
static inline void ms_pixel(int x,int y,int ink){u32* w;int shift;if(x<0||y<0||x>=240||y>=160)return;w=sStudyPixels+((y>>3)*30+(x>>3))*8+(y&7);shift=(x&7)*4;*w=(*w&~(15u<<shift))|((u32)(ink&15)<<shift);}
static void ms_line(int x0,int y0,int x1,int y1,int ink){
    int dx=ABS(x1-x0),sx=x0<x1?1:-1,dy=-ABS(y1-y0),sy=y0<y1?1:-1,e=dx+dy;
    for(;;){int v;ms_pixel(x0,y0,ink);if(x0==x1&&y0==y1)break;v=2*e;if(v>=dy){e+=dy;x0+=sx;}if(v<=dx){e+=dx;y0+=sy;}}
}
static void ms_fill(int x,int y,int w,int h,int ink){
    int row;u32 color=(ink&15)*0x11111111u;
    for(row=MAX(0,y);row<MIN(160,y+h);row++){
        int a=MAX(0,x),end=MIN(240,x+w);u32* dst;
        if(a>=end)continue;
        dst=sStudyPixels+((row>>3)*30+(a>>3))*8+(row&7);
        while(a<end){int span=MIN(end-a,8-(a&7)),shift=(a&7)*4;u32 mask=span==8?~0u:((1u<<(span*4))-1)<<shift;*dst=(*dst&~mask)|(color&mask);a+=span;dst+=8;}
    }
}
static void ms_box(int x,int y,int w,int h,int ink){if(w<1||h<1)return;ms_line(x,y,x+w-1,y,ink);ms_line(x,y+h-1,x+w-1,y+h-1,ink);ms_line(x,y,x,y+h-1,ink);ms_line(x+w-1,y,x+w-1,y+h-1,ink);}
static void ms_frame(MSRect r,int kind){
    static const u8 parts[][4]={
        {UI_PANEL_TL,UI_PANEL_T,UI_PANEL_L,UI_FILL},
        {UI_SLOT_TL,UI_SLOT_T,UI_SLOT_L,UI_SLOT_FILL},
        {UI_SEL_TL,UI_SEL_T,UI_SEL_L,UI_SLOT_FILL},
        {UI_EMPTY_TL,UI_EMPTY_T,UI_EMPTY_L,UI_FILL}
    };
    int x,y,tw=r.w/8,th=r.h/8;const u8* p=parts[CLAMP(kind,0,3)];
    if(!ms_valid(r))return;
    for(y=0;y<th;y++)for(x=0;x<tw;x++){
        bool8 lr=x==0||x==tw-1,tb=y==0||y==th-1;
        int t=tb?(lr?p[0]:p[1]):(lr?p[2]:p[3]);
        int flip=(x==tw-1?1:0)|(y==th-1?2:0);
        if(!tb)flip&=1;
        if(!lr)flip&=2;
        ms_kit(r.x/8+x,r.y/8+y,t,flip);
    }
}
static void ms_textfit(int x,int y,int w,const char* text,int ink){
    char out[96];int i=0,width=0;
    if(w<=0)return;
    while(text[i]&&i<91){int a=vwf_advance((u8)text[i]);if(width+a-1>w)break;out[i]=text[i];width+=a;i++;}
    if(text[i]&&i>2){out[i-1]='.';out[i-2]='.';}out[i]=0;
    ms_text(x,y,out,ink);
}
/* Bounded wrapping understands the original inline ink bytes. Long words
   break at a native glyph instead of escaping the information panel. */
static void ms_wrap(MSRect r,const char* text,int base,int pitch){
    const u8* s=(const u8*)text;int x=r.x,y=r.y,ink=base;
    while(*s&&y+8<=r.y+r.h){
        int ww=0;const u8* end=s;
        if(*s<32){ink=vwf_ink(*s++,base);continue;}
        if(*s==' '){if(x>r.x)x+=vwf_advance(' ');
            s++;continue;}
        while(*end&&*end!=' '){if(*end>=32)ww+=vwf_advance(*end);end++;}
        if(x>r.x&&x+ww>r.x+r.w){x=r.x;y+=pitch;if(y+8>r.y+r.h)break;}
        while(s<end){int ch=*s++,a;if(ch<32){ink=vwf_ink(ch,base);continue;}a=vwf_advance(ch);
            if(x+a>r.x+r.w){x=r.x;y+=pitch;if(y+8>r.y+r.h)return;}
            x+=ms_glyph(x,y,ch,ink);
        }
    }
}
static const char* ms_verb(int eq){
    switch(eq){case EQ_SWORD:return "Cut";case EQ_SHIELD:return "Guard";case EQ_BOMBS:return "Blast";case EQ_LAMP:return "Burn";case EQ_CLOAK:return "Leap";case EQ_BOW:return "Shoot";case EQ_HUBCAP:return "Return";default:return "Keep";}
}
static const char* ms_use(const MenuItem* item){
    if(item==&sKeys[0])return "Four make one heart.";
    if(item==&sKeys[1])return "Unlock a door.";
    if(item==&sKeys[2])return "R: lift boulders.";
    if(item==&sKeys[3])return "Back to the Nun.";
    if(item==&sKeys[4])return "Chart every room.";
    if(item==&sKeys[5])return "Show chests, gates.";
    switch(item->eq){case EQ_SWORD:return "Cut brush. Turn seeds.";case EQ_SHIELD:return "Block frontal attacks.";case EQ_BOMBS:return "Blast cracked stone.";case EQ_LAMP:return "Burn webs and brush.";case EQ_CLOAK:return "Leap pits and chasms.";case EQ_BOW:return "Arrows stop at walls.";case EQ_HUBCAP:return "Return to the Drain.";default:return item->desc;}
}
static int ms_count(const MenuItem* item){
    if(item->eq==EQ_BOMBS)return gPl.bombs;
    if(item->eq==EQ_BOW)return gPl.arrows;
    if(item==&sKeys[0])return gPl.hearts_pieces;
    if(item==&sKeys[1])return gPl.keys;
    return -1;
}
static int ms_frame_of(const MenuItem* item){return item->eq==EQ_SHIELD?player_shield_icon():item->icon;}
static int ms_hud_pal(int original){
    switch(original){case PAL_OBJ_HERO:return 7;case PAL_OBJ_BUGS:return 8;case PAL_OBJ_BLIGHT:return 9;case PAL_OBJ_IRON:return 10;default:return 11;}
}
static void ms_icon(int frame,int x,int y,int size,int slot){
    if(size==32){draw_sprite(x,y,SHEET_ICON32,icon32_frame_tile(frame),0,0,1,icon32_frame_palette(frame));}
    else{
        const SpriteSheet* sh=&sheets[SHEET_HUDITEMS];int tile=OBJ_TILE_HUD_ICONS+slot*4,pal=huditems_frame_pal[frame],mp=ms_hud_pal(pal);
        vram_queue(sh->tiles+frame*sh->frame_tiles*16,OBJ_TILE(tile),sh->frame_tiles*32);
        pal_set_obj(mp,&pal_obj[pal*16]);
        draw_sprite(x,y,SHEET_HUDITEMS,tile,0,0,1,mp);
    }
}
static MSPoint ms_slot(int compact,int original){return sStudy->slots[sStudy->mode==MS_WHEEL?original:compact];}
static int ms_label_width(MSPoint p){
    int edge=232;MSRect r[4]={sStudy->detail,sStudy->equipment,sStudy->status,sStudy->preview};int i;
    for(i=0;i<4;i++)if(ms_valid(r[i])&&r[i].x>p.x&&r[i].y<p.y+16&&r[i].y+r[i].h>p.y)edge=MIN(edge,r[i].x-4);
    for(i=0;i<7;i++){MSPoint q=sStudy->slots[i];if(q.x>p.x&&q.y<p.y+sStudy->icon_size&&q.y+sStudy->icon_size>p.y)edge=MIN(edge,q.x-4);}
    return edge-(p.x+sStudy->icon_size+4);
}
static void ms_assignments(void){
    static const char* const badge[3]={"A","B","L"};int s;
    MSRect r=sStudy->equipment;
    if(!(sStudy->flags&MS_EQUIPMENT)||!ms_valid(r))return;
    ms_frame(r,0);
    for(s=0;s<3;s++){
        bool8 row=r.w>=r.h;int dx=row?(r.w-8)/3:0,dy=row?0:(r.h-8)/3;
        int x=r.x+4+(row?s*dx:0),y=r.y+4+(!row?s*dy:0);
        ms_textfit(x,y,8,badge[s],UI_INK_GOLD);
    }
}
/* Designs without a separate loadout panel still expose all assignments.
   Stable columns replace the subtitle while the pack page is open. */
static void ms_assignment_line(void){
    static const char* const button[3]={"A","B","L"};
    static const char* const shortname[8]={"--","Sword","Seeds","Lamp","Cloak","Shield","Bow","Cap"};
    int s;if(sPage!=PG_ITEMS||(sStudy->flags&MS_EQUIPMENT))return;
    ms_fill(7,13,226,10,UI_INK_NAVY);
    for(s=0;s<3;s++){int eq=gPl.equip[s],x=8+s*76;ms_text(x,14,button[s],UI_INK_GOLD);ms_textfit(x+10,14,64,eq<8?shortname[eq]:"--",UI_INK_CREAM);}
}
static void ms_status(void){
    MSRect r=sStudy->status;char b[24],num[8];int y,x;
    if(!(sStudy->flags&MS_STATUS)||!ms_valid(r))return;
    ms_frame(r,0);y=r.y+4;
    x=ms_text(r.x+4,y,"Gilt ",UI_INK_DIM);ms_text(x,y,vwf_num(num,gPl.gilt,0),UI_INK_CREAM);y+=10;
    if(y+8<r.y+r.h){x=ms_text(r.x+4,y,"Keys ",UI_INK_DIM);ms_text(x,y,vwf_num(num,gPl.keys,0),UI_INK_CREAM);y+=10;}
    if(y+8<r.y+r.h){x=ms_text(r.x+4,y,"Seen ",UI_INK_DIM);x=ms_text(x,y,vwf_num(num,explored(),0),UI_INK_CREAM);ms_text(x,y,"%",UI_INK_DIM);}
    (void)b;
}
static void ms_count_overlay(int k,MSPoint p,int size,int value){
    char buf[5];int tx=(p.x+size-16)/8,ty=(p.y+size-16)/8;
    if(k>=2||!bg0_canvas(&sCount[k],tx,ty,2,2))return;
    vwf_num(buf,value,0);vwf_text_fx(&sCount[k],14-vwf_width(buf),6,buf,UI_INK_PALE,UI_INK_DARK,FX_OUTLINE);vwf_flush(&sCount[k],FALSE);
}
static void ms_details(const MenuItem* item){
    MSRect r=sStudy->detail,body;int x,y,w;
    if(!ms_valid(r))return;
    ms_frame(r,0);if(!item)return;
    x=r.x+4;y=r.y+4;w=r.w-8;
    if(sStudy->mode==MS_FOCUS&&r.w>=112){x+=40;w-=40;}
    {int count=ms_count(item);
     if(r.w>=112&&r.h<=48&&(item->eq==EQ_BOMBS||item->eq==EQ_BOW)){
        char b[8];int cw;vwf_num(b,count,0);cw=vwf_width(b);ms_textfit(x,y,w-cw-8,item->name,UI_INK_HIGH);ms_text(x+w-cw,y,b,UI_INK_GOLD);
     }else ms_textfit(x,y,w,item->name,UI_INK_HIGH);}
    y+=11;
    {int count=ms_count(item);if(count>=0&&r.h>=56){char b[8];int nx=ms_text(x,y,item->eq==EQ_BOW?"Arrows ":item->eq==EQ_BOMBS?"Seeds ":"Held ",UI_INK_GOLD);ms_text(nx,y,vwf_num(b,count,0),UI_INK_CREAM);y+=10;}}
    body=(MSRect){x,y,w,r.y+r.h-y-4};
    ms_wrap(body,r.w<96||r.h<=48?ms_use(item):item->desc,UI_INK_CREAM,9);
}
static void ms_marker(int x,int y,int kind,int ink){
    if(kind==5||kind==6||kind==7||kind==8){ms_text(x-2,y-3,kind==5?"H":kind==6?"F":kind==7?"R":"G",ink);return;}
    if(kind==0){ms_pixel(x,y,ink);ms_pixel(x-1,y,ink);ms_pixel(x+1,y,ink);ms_pixel(x,y-1,ink);ms_pixel(x,y+1,ink);}
    else if(kind==1){ms_box(x-2,y-2,5,5,ink);ms_pixel(x,y,ink);}
    else if(kind==2){ms_line(x,y-2,x,y+1,ink);ms_pixel(x,y+3,ink);}
    else{ms_box(x-1,y-1,3,3,ink);}
}
static void ms_map_copy(MSRect r,bool8 save){
    int y,x;for(y=r.y/8;y<(r.y+r.h)/8;y++)for(x=r.x/8;x<(r.x+r.w)/8;x++){
        int off=(y*30+x)*8;if(save)memcpy32(sStudyMapPicture+off,sStudyPixels+off,32);else memcpy32(sStudyPixels+off,sStudyMapPicture+off,32);
    }
}
static void ms_map_bank(MSRect r){int x,y;for(y=r.y/8;y<(r.y+r.h)/8;y++)for(x=r.x/8;x<(r.x+r.w)/8;x++)if(x>=0&&x<30&&y>=0&&y<20)gBg3[y*32+x]=(y*30+x)|(MAP_PAL<<12);}
static void ms_map(MSRect box,int zoom,int mode){
    int x,y,cell,cw,ch,base_x,base_y;u8 tx_at[48],ty_at[48];bool8 astro=(gPl.items2&ITEM2_ASTROLABE)!=0;
    if(!ms_valid(box))return;
    if(!zoom&&sStudyMapReady&&sStudyMapMode==mode&&box.x==sStudyMapRect.x&&box.y==sStudyMapRect.y&&box.w==sStudyMapRect.w&&box.h==sStudyMapRect.h){
        ms_map_copy(box,FALSE);ms_map_bank(box);goto cursor;
    }
    ms_fill(box.x,box.y,box.w,box.h,MAP_INK_GROUND);ms_map_bank(box);
    if(zoom){
        int sw=30,sh=21,scale=MIN(box.w/sw,box.h/sh);bool8 kn=known(sMapCur);scale=MAX(1,scale);
        base_x=box.x+(box.w-sw*scale)/2;base_y=box.y+(box.h-sh*scale)/2;
        if(kn){const u8* m;fetch_mask(sMapCur);m=sMasks[sMapCur];
            for(y=0;y<sh;y++)for(x=0;x<sw;x++){
                int d=tile_desc(m,x+1,y+2),ink=(m[(y+2)*32+x+1]>>3)&15;
                if(!ink)ink=MAP_INK_GROUND;
                ms_fill(base_x+x*scale,base_y+y*scale,scale,scale,ink);
                if((d&7)!=M_WALL&&(d&7)!=M_WATER){
                    if(d&SH_N)ms_fill(base_x+x*scale,base_y+y*scale,scale,1,MAP_INK_LIT);
                    if(d&SH_W)ms_fill(base_x+x*scale,base_y+y*scale,1,scale,MAP_INK_LIT);
                }
            }
            {Cell* c=&gWorld.cells[sMapCur];const u8* marks=gWorld.mark[sMapCur];int rc=relic_cell();
             if(c->flags&CF_VISITED){
                if(marks[MP_MOUTH*2]&&!(gWorld.myst_flags[sMapCur]&MF_DONE))ms_marker(base_x+(marks[MP_MOUTH*2]-2)*scale,base_y+(marks[MP_MOUTH*2+1]-3)*scale,1,MAP_INK_CREAM);
                if(marks[MP_NPC*2]&&!(quest_giver(c)&&(c->flags&CF_QUEST_DONE)))ms_marker(base_x+(marks[MP_NPC*2]-2)*scale,base_y+(marks[MP_NPC*2+1]-3)*scale,quest_giver(c)?2:6,MAP_INK_GOLD);
                if(astro&&marks[MP_CHEST*2]&&has_chest(c))ms_marker(base_x+(marks[MP_CHEST*2]-2)*scale,base_y+(marks[MP_CHEST*2+1]-3)*scale,3,MAP_INK_GOLD);
                if(rc==sMapCur&&marks[MP_RELIC*2])ms_marker(base_x+(marks[MP_RELIC*2]-2)*scale,base_y+(marks[MP_RELIC*2+1]-3)*scale,7,MAP_INK_CREAM);
             }
             if(astro&&sMapCur==gWorld.goal&&!(c->flags&CF_CLEARED))ms_marker(base_x+15*scale,base_y+10*scale,5,MAP_INK_GOLD);
             if(astro){int side;for(side=0;side<4;side++)if(gate_mark(sMapCur,side)>=0){int gx=side==SIDE_E?29:side==SIDE_W?0:15,gy=side==SIDE_N?0:side==SIDE_S?20:10;ms_marker(base_x+gx*scale,base_y+gy*scale,8,MAP_INK_GOLD);}}
            }
            if(gGame.area==AREA_FOREST&&gGame.cell==sMapCur)ms_marker(base_x+CLAMP((PX(gPlayer->x)-16)/16,0,29)*scale,base_y+CLAMP((PX(gPlayer->y)-40)/16,0,20)*scale,0,MAP_INK_CREAM);
        }else{
            ms_textfit(box.x+4,box.y+box.h/2-4,box.w-8,"Not charted",MAP_INK_CREAM);
        }
        ms_box(box.x,box.y,box.w,box.h,MAP_INK_GRID);return;
    }
    /* Terrain keeps a single scale in both axes; diagram styles may use a
       freer topology grid, but never change north or invent unknown links. */
    if(mode==MS_MAP_TERRAIN){cw=MIN(box.w/5,(box.h/5)*32/22);cw=MAX(5,cw);ch=MAX(5,cw*22/32);}
    else{cw=box.w/5;ch=box.h/5;}
    base_x=box.x+(box.w-cw*5)/2;base_y=box.y+(box.h-ch*5)/2;
    for(x=0;x<cw;x++)tx_at[x]=x*32/cw;
    for(y=0;y<ch;y++)ty_at[y]=1+y*22/ch;
    for(cell=0;cell<CELLS;cell++){
        bool8 kn=known(cell);Cell* c=&gWorld.cells[cell];int cx=base_x+(cell%5)*cw,cy=base_y+(cell/5)*ch;
        if(kn&&(mode==MS_MAP_TERRAIN||mode==MS_MAP_PARCHMENT))fetch_mask(cell);
        if(mode==MS_MAP_TERRAIN||mode==MS_MAP_PARCHMENT){
            for(y=1;y<ch-1;y++)for(x=1;x<cw-1;x++){
                int ink=MAP_INK_GROUND;
                if(kn){ink=(sMasks[cell][ty_at[y]*32+tx_at[x]]>>3)&15;if(!ink)ink=MAP_INK_GROUND;}
                ms_pixel(cx+x,cy+y,ink);
            }
            ms_box(cx,cy,cw,ch,kn?MAP_INK_GRID:MAP_INK_UNKNOWN_EDGE);
        }else{
            int rx=cx+MAX(2,cw/6),ry=cy+MAX(2,ch/6),rw=cw-MAX(4,cw/3),rh=ch-MAX(4,ch/3);
            if(kn){int side;for(side=SIDE_E;side<=SIDE_S;side++){int nb=cell_neighbor(cell,side);if(nb>=0&&known(nb)&&c->gate[side]!=GATE_WALL){int ink=MAP_INK_GRID;if(astro){ink=world_gate_open(cell,side)?MAP_INK_LIT:MAP_INK_GRID;if(gate_mark(cell,side)>=0)ink=MAP_INK_GOLD;}ms_line(cx+cw/2,cy+ch/2,cx+cw/2+(side==SIDE_E?cw:0),cy+ch/2+(side==SIDE_S?ch:0),ink);}}}
            ms_fill(rx,ry,rw,rh,kn?(c->flags&CF_VISITED?MAP_INK_GREEN:MAP_INK_DEEP):MAP_INK_GROUND);
            ms_box(rx,ry,rw,rh,kn?MAP_INK_LIT:MAP_INK_UNKNOWN_EDGE);
            if(mode==MS_MAP_ROUTE&&kn&&c->flags&CF_VISITED)ms_line(rx+1,ry+rh-2,rx+rw-2,ry+rh-2,MAP_INK_GOLD);
        }
        if(c->flags&CF_VISITED){
            const u8* m=gWorld.mark[cell];
            if(m[MP_NPC*2]&&!(quest_giver(c)&&(c->flags&CF_QUEST_DONE)))ms_marker(cx+cw/2,cy+ch/2,quest_giver(c)?2:6,MAP_INK_CREAM);
            if(m[MP_MOUTH*2]&&!(gWorld.myst_flags[cell]&MF_DONE))ms_marker(cx+cw/3,cy+ch/2,1,MAP_INK_LIT);
        }
        if(astro&&has_chest(c))ms_marker(cx+cw/2,cy+ch/2,3,MAP_INK_GOLD);
        if(astro&&cell==gWorld.goal&&!(c->flags&CF_CLEARED))ms_marker(cx+cw/2,cy+ch/2,5,MAP_INK_GOLD);
        if(relic_cell()==cell)ms_marker(cx+cw/2,cy+ch/2,7,MAP_INK_CREAM);
    }
    cell=gGame.area==AREA_FOREST?gGame.cell:gWorld.entry;
    ms_marker(base_x+(cell%5)*cw+cw/2,base_y+(cell/5)*ch+ch/2,0,MAP_INK_CREAM);
    ms_box(box.x,box.y,box.w,box.h,MAP_INK_GRID);
    ms_map_copy(box,TRUE);sStudyMapRect=box;sStudyMapMode=mode;sStudyMapReady=1;
cursor:
    if(mode==MS_MAP_TERRAIN){cw=MIN(box.w/5,(box.h/5)*32/22);cw=MAX(5,cw);ch=MAX(5,cw*22/32);}else{cw=box.w/5;ch=box.h/5;}
    base_x=box.x+(box.w-cw*5)/2;base_y=box.y+(box.h-ch*5)/2;
    ms_box(base_x+(sMapCur%5)*cw+1,base_y+(sMapCur/5)*ch+1,cw-2,ch-2,MAP_INK_GOLD);
}
static void ms_map_info(MSRect r){
    Cell* c=&gWorld.cells[sMapCur];char b[8];int y;
    if(!ms_valid(r))return;
    ms_frame(r,0);
    if(r.h<=24){ms_textfit(r.x+4,r.y+4,r.w-8,"+You []Door !Task FFolk oChest RRelic HHeart GGate",UI_INK_CREAM);return;}

    ms_wrap((MSRect){r.x+4,r.y+4,r.w-8,18},known(sMapCur)?sArchName[c->arch]:"Unknown wood",UI_INK_HIGH,9);y=r.y+24;
    if(r.h>=112&&y+8<r.y+r.h){int x=ms_text(r.x+4,y,vwf_num(b,explored(),0),UI_INK_GOLD);ms_text(x,y,"% seen",UI_INK_DIM);y+=10;}
    {static const char* const legend[]={"+ You","[] Door","! Task","F Folk","o Chest","R Relic","H Heart","G Gate"};int i;
     for(i=0;i<8&&y+9<=r.y+r.h-3;i++,y+=9)ms_textfit(r.x+4,y,r.w-8,legend[i],UI_INK_DIM);}

}
static void ms_upload(void){
    vram_queue(sStudyPixels,CHARBLOCK(0),sizeof(sStudyPixels));gBg3Dirty=1;
}
static void ms_sync(void){gMenuStudyPage=sPage;gMenuStudyCursor=sCursor;gMenuStudyMapCell=sMapCur;gMenuStudyZoom=sZoom;}
static void ms_draw(void){
    u32 start=gFrame;int i,n,count_at=0;u8 idx[7];const MenuItem* list=sPage==PG_KEYS?sKeys:sItems;
    bg0_clear();bg0_pool_reset_full();
    sStudyCanvas=(Canvas){0,30,20,0,sStudyPixels};
    for(i=0;i<32*32;i++)gBg3[i]=UI_PAL<<12;
    for(i=0;i<MS_TILES;i++)gBg3[(i/30)*32+i%30]=i|(UI_PAL<<12);
    if(sStudyBaseReady&(1<<sPage))dma3_copy32(sStudyBase[sPage],sStudyPixels,sizeof(sStudyPixels));
    else{
        vwf_clear(&sStudyCanvas,UI_INK_NAVY);
    ms_frame((MSRect){0,0,240,160},0);
    ms_textfit(7,3,150,sStudy->name,UI_INK_GOLD);
    ms_textfit(170,3,64,sTabName[sPage],UI_INK_HIGH);
    ms_textfit(7,14,224,sStudy->purpose,UI_INK_DIM);
    ms_line(4,146,235,146,UI_INK_GOLD_DARK);
        dma3_copy32(sStudyPixels,sStudyBase[sPage],sizeof(sStudyPixels));sStudyBaseReady|=1<<sPage;
    }
    if(sPage==PG_MAP){
        MSRect primary=sStudy->overview;
        if(sStudy->map_info.h<=24){
            const char* name=known(sMapCur)?sArchName[gWorld.cells[sMapCur].arch]:"Unknown";char b[8];
            if(sStudy->map_mode==MS_MAP_DUAL&&!sZoom){ms_text(primary.x,24,"Region",UI_INK_GOLD);ms_textfit(sStudy->chamber.x,24,sStudy->chamber.w,"Chamber",UI_INK_GOLD);ms_textfit(sStudy->chamber.x+44,24,sStudy->chamber.w-44,name,UI_INK_CREAM);}
            else{int x=ms_text(8,24,sZoom?"Chamber: ":"Region: ",UI_INK_GOLD);ms_textfit(x,24,144-x,name,UI_INK_CREAM);x=ms_text(180,24,vwf_num(b,explored(),0),UI_INK_GOLD);ms_text(x,24,"% seen",UI_INK_DIM);}
        }
        if(sZoom){MSRect z=sStudy->chamber;if(!ms_valid(z)||sStudy->map_mode==MS_MAP_DUAL)z=(MSRect){8,32,224,112};ms_map(z,1,sStudy->map_mode);if(sStudy->map_mode!=MS_MAP_DUAL)ms_map_info(sStudy->map_info);}
        else{ms_map(primary,0,sStudy->map_mode);if(sStudy->map_mode==MS_MAP_DUAL)ms_map(sStudy->chamber,1,sStudy->map_mode);ms_map_info(sStudy->map_info);}
        ms_textfit(7,149,226,sZoom?"B overview  R page  Start close":"D-pad browse  A zoom  R page  Start close",UI_INK_CREAM);
    }else{
        n=gather(list,sPage==PG_KEYS?KEY_COUNT:ITEM_COUNT,idx);
        if(sCursor>=n)sCursor=n?n-1:0;
        if((sStudy->flags&MS_PREVIEW)){MSRect p=ms_valid(sStudy->preview)?sStudy->preview:sStudy->overview;ms_map(p,0,sStudy->map_mode);}
        ms_assignments();ms_status();
        if(sStudy->mode==MS_WHEEL){for(i=0;i<7;i++){MSPoint p=sStudy->slots[i];ms_frame((MSRect){p.x,p.y,32,32},3);}}
        for(i=0;i<n;i++){
            MSPoint p=ms_slot(i,idx[i]);int frame=sStudy->icon_size;
            ms_frame((MSRect){p.x,p.y,frame,frame},i==sCursor?2:1);
            if((sStudy->flags&MS_LABELS)||sStudy->mode==MS_LIST){const char* label=(sStudy->flags&MS_PURPOSE)&&sPage==PG_ITEMS?ms_verb(list[idx[i]].eq):list[idx[i]].name;ms_textfit(p.x+frame+4,p.y+(frame-8)/2,ms_label_width(p),label,i==sCursor?UI_INK_HIGH:UI_INK_CREAM);}
            if(i==sCursor&&list[idx[i]].eq!=EQ_NONE){int s;for(s=0;s<3;s++)if(gPl.equip[s]==list[idx[i]].eq){static const char* const l[3]={"A","B","L"};ms_textfit(p.x+2+s*6,p.y+frame-9,6,l[s],UI_INK_PALE);}}
            {int count=ms_count(&list[idx[i]]);if(count>=0&&frame==32)ms_count_overlay(count_at++,p,frame,count);
             else if(count>=0&&sStudy->mode==MS_LIST){char b[5];int width=ms_label_width(p);vwf_num(b,count,0);ms_textfit(p.x+frame+4+MAX(0,width-vwf_width(b)),p.y+4,vwf_width(b),b,UI_INK_GOLD);}}
        }
        ms_details(n?&list[idx[sCursor]]:NULL);
        if(!n)ms_textfit(12,32,200,"Nothing carried yet",UI_INK_DIM);
        ms_textfit(7,149,226,sPage==PG_ITEMS?"A/B/L equip   R page   Start close":"R page   Start close",UI_INK_CREAM);
    }
    ms_assignment_line();ms_upload();ms_sync();gMenuStudyDrawFrames=gFrame-start;
}
static void ms_sprites(void){
    int i,n;u8 idx[7];const MenuItem* list=sPage==PG_KEYS?sKeys:sItems;
    if(sPage==PG_MAP)return;
    n=gather(list,sPage==PG_KEYS?KEY_COUNT:ITEM_COUNT,idx);
    for(i=0;i<n;i++){MSPoint p=ms_slot(i,idx[i]);ms_icon(ms_frame_of(&list[idx[i]]),p.x,p.y,sStudy->icon_size,i);}
    if(n&&sStudy->mode==MS_FOCUS&&sStudy->detail.w>=112)ms_icon(ms_frame_of(&list[idx[sCursor]]),sStudy->detail.x+4,sStudy->detail.y+12,32,0);
    if((sStudy->flags&MS_EQUIPMENT)&&ms_valid(sStudy->equipment)){
        MSRect r=sStudy->equipment;bool8 row=r.w>=r.h;
        for(i=0;i<3;i++){int j;for(j=0;j<ITEM_COUNT;j++)if(sItems[j].eq==gPl.equip[i]){int x=r.x+4+(row?i*(r.w-8)/3:0),y=r.y+4+(!row?i*(r.h-8)/3:0);ms_icon(ms_frame_of(&sItems[j]),x+10,y,16,12+i);break;}}
    }
}
static void ms_restore(void){
    int i,set=gGame.area==AREA_SEWER?TS_SEWER:gGame.area==AREA_MYST?TS_MYST:TS_FOREST;const Tileset* ts=&tilesets[set];
    dma3_copy32(sStudyWorld,CHARBLOCK(0),sizeof(sStudyWorld));
    dma3_copy32(sStudyHud,OBJ_TILE(OBJ_TILE_HUD_ICONS),sizeof(sStudyHud));
    for(i=0;i<ts->anim_count;i++){const TileAnim* a=&ts->anims[i];int f;if(!a->frames||!a->speed)continue;f=(gFrame/a->speed)%a->frames;dma3_copy32(a->data+f*64,CHARBLOCK(0)+a->tile*16,128);}
    REG_BG3CNT=sStudyBg3;gAnimTiles=sStudyAnim;gVBlankHook=sStudyOldHook;
}
static void ms_open(void){
    int n,i;u8 idx[7];
    sStudy=menu_study_layout(BART_MENU_VARIANT);ms_cache_kit();sStudyMapReady=0;
    sStudyInputRead=sStudyInputWrite=0;sStudyHeld=~REG_KEYINPUT&KEY_ANY;sStudyOldHook=gVBlankHook;gVBlankHook=ms_input_irq;
    if(!sStudyHaveFocus||sStudySeed!=gWorld.seed){sStudyFocus[0]=sStudyFocus[1]=0;sMapCur=gGame.area==AREA_FOREST?gGame.cell:gWorld.entry;sZoom=0;sStudySeed=gWorld.seed;sStudyHaveFocus=1;}
    sPage=PG_ITEMS;n=gather(sItems,ITEM_COUNT,idx);sCursor=0;for(i=0;i<n;i++)if(idx[i]==sStudyFocus[0])sCursor=i;
    icon32_menu_begin();bg0_clear();bg0_pool_reset_full();
    dma3_copy32((const void*)CHARBLOCK(0),sStudyWorld,sizeof(sStudyWorld));dma3_copy32((const void*)OBJ_TILE(OBJ_TILE_HUD_ICONS),sStudyHud,sizeof(sStudyHud));
    sStudyBg3=REG_BG3CNT;sStudyAnim=gAnimTiles;gAnimTiles=0;
    REG_BG3CNT=(sStudyBg3&~(3<<2))|BGCNT_CHARBASE(0);REG_BLDCNT=0;REG_BLDY=0;
    video_show(DCNT_BG0|DCNT_BG3|DCNT_OBJ);ms_draw();gGame.state=GS_MAP;sfx_play(SFX_MENU);
}
static int ms_move(int n,const u8* idx){
    int axis=0,sign=0,i,best=sCursor,bestscore=0x7fffffff;MSPoint a;
    if(gKeysDown&KEY_RIGHT){axis=0;sign=1;}else if(gKeysDown&KEY_LEFT){axis=0;sign=-1;}else if(gKeysDown&KEY_DOWN){axis=1;sign=1;}else if(gKeysDown&KEY_UP){axis=1;sign=-1;}else return 0;
    if(!n)return 0;
    a=ms_slot(sCursor,idx[sCursor]);
    for(i=0;i<n;i++)if(i!=sCursor){MSPoint b=ms_slot(i,idx[i]);int dx=b.x-a.x,dy=b.y-a.y,along=axis?dy:dx,off=axis?ABS(dx):ABS(dy),score;
        if(along*sign<=0)continue;
        score=along*along+off*off*3;if(score<bestscore){bestscore=score;best=i;}}
    if(best==sCursor)return 0;
    sCursor=best;return 1;
}
static void ms_update(void){
    u8 idx[7];const MenuItem* list=sPage==PG_KEYS?sKeys:sItems;int n=gather(list,sPage==PG_KEYS?KEY_COUNT:ITEM_COUNT,idx),dirty=0;
    gKeysDown=0;if(sStudyInputRead!=sStudyInputWrite){gKeysDown=sStudyInput[sStudyInputRead];sStudyInputRead=(sStudyInputRead+1)&31;}
    if(gKeysDown&KEY_START){ms_restore();menu_close();return;}
    if(gKeysDown&KEY_R){
        if(sPage<PG_MAP&&n)sStudyFocus[sPage]=idx[sCursor];
        sPage=(sPage+1)%PG_COUNT;
        if(sPage<PG_MAP){int i;n=gather(sPage==PG_KEYS?sKeys:sItems,sPage==PG_KEYS?KEY_COUNT:ITEM_COUNT,idx);sCursor=0;for(i=0;i<n;i++)if(idx[i]==sStudyFocus[sPage])sCursor=i;}
        dirty=1;
    }else if(sPage==PG_MAP){
        int x=sMapCur%5,y=sMapCur/5;
        if(gKeysDown&KEY_RIGHT)x=MIN(4,x+1);
        if(gKeysDown&KEY_LEFT)x=MAX(0,x-1);
        if(gKeysDown&KEY_DOWN)y=MIN(4,y+1);
        if(gKeysDown&KEY_UP)y=MAX(0,y-1);
        if(sMapCur!=y*5+x){sMapCur=y*5+x;dirty=1;}
        if((gKeysDown&KEY_A)&&!sZoom){sZoom=1;dirty=1;}if((gKeysDown&KEY_B)&&sZoom){sZoom=0;dirty=1;}
    }else{
        if(sCursor>=n)sCursor=n?n-1:0;
        if(ms_move(n,idx)){sStudyFocus[sPage]=idx[sCursor];dirty=1;}
        if(sPage==PG_ITEMS&&n&&(gKeysDown&(KEY_A|KEY_B|KEY_L))){int slot=gKeysDown&KEY_A?SLOT_A:gKeysDown&KEY_B?SLOT_B:SLOT_L;player_equip_set(slot,list[idx[sCursor]].eq);sfx_play(SFX_ITEM);dirty=1;}
    }
    if(dirty){ms_draw();sfx_play(SFX_MENU);}ms_sprites();ms_sync();
}
#endif

/* -------------------------------------------------------------- open -- */
void menu_open(void) {
#if BART_MENU_VARIANT
    ms_open();
    return;
#endif
    sPage = PG_ITEMS;
    sZoom = 0;
    sCursor = 0;
    sOverviewDone = 0;
    sMapCur = (gGame.area == AREA_FOREST) ? gGame.cell : gWorld.entry;
    icon32_menu_begin();
    ensure_sheets();
    REG_BLDCNT = 0;
    REG_BLDY = 0;
    video_show(DCNT_BG0 | DCNT_BG3 | DCNT_OBJ);
    ui_backdrop_open();
    draw_page();
    gGame.state = GS_MAP;
    sfx_play(SFX_MENU);
}

static void menu_close(void) {
    icon32_menu_end();
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

/* the icon of what a button holds, small, for the side panel; the blade
   and the shield stay resident at these tiles (player.c) */
#define SWORD_TILE OBJ_TILE_SWORD
#define SHIELD_TILE OBJ_TILE_SHIELD
static void equip_icon(int eq, int px, int py, int prio) {
    switch (eq) {
        case EQ_SWORD: draw_sprite(px, py, SHEET_SWORD, SWORD_TILE, F_SWORD_BLADE_S, 0, prio, sheets[SHEET_SWORD].pal); break;
        case EQ_BOMBS: draw_sprite(px, py, SHEET_ITEMS, items_sheet_tile(), F_ITEMS_BOMBS, 0, prio, items_frame_pal[F_ITEMS_BOMBS]); break;
        case EQ_LAMP: draw_sprite(px, py, SHEET_ITEMS, items_sheet_tile(), F_ITEMS_LAMP, 0, prio, items_frame_pal[F_ITEMS_LAMP]); break;
        case EQ_CLOAK: draw_sprite(px, py, SHEET_ITEMS, items_sheet_tile(), F_ITEMS_CLOAK, 0, prio, items_frame_pal[F_ITEMS_CLOAK]); break;
        case EQ_SHIELD: draw_sprite(px, py, SHEET_SHIELD, SHIELD_TILE, player_shield_frame(F_SHIELD_FRONT), 0, prio, player_shield_palette(F_SHIELD_FRONT)); break;
        case EQ_BOW: draw_sprite(px, py, SHEET_ITEMS, items_sheet_tile(), F_ITEMS_BOW, 0, prio, items_frame_pal[F_ITEMS_BOW]); break;
        case EQ_HUBCAP: draw_sprite(px, py, SHEET_ITEMS, items_sheet_tile(), F_ITEMS_HUBCAP, 0, prio, items_frame_pal[F_ITEMS_HUBCAP]); break;
        default: break;
    }
}

void menu_update(void) {
#if BART_MENU_VARIANT
    ms_update();
    return;
#endif
    static u8 idx[ITEM_COUNT];
    /* Restore actor palettes before submitting any icon draws for the
       closing frame. The game redraws the world after this state change. */
    if (gKeysDown & KEY_START) {
        menu_close();
        return;
    }
    switch (sPage) {
        case PG_ITEMS: {
            int n = gather(sItems, ITEM_COUNT, idx), s;
            grid_icons(sItems, idx, n);
            if (n) {
                int frame=sItems[idx[sCursor]].eq==EQ_SHIELD?player_shield_icon():sItems[idx[sCursor]].icon;
                draw_sprite(2 * 8, DESC_SLOT_TY * 8, SHEET_ICON32, icon32_frame_tile(frame), 0, 0, 1, icon32_frame_palette(frame));
            }
            for (s = 0; s < SLOT_COUNT; s++)
                equip_icon(gPl.equip[s], 25 * 8, SIDE_BADGE_TY(s) * 8 - 4, 1);
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
                draw_sprite(2 * 8, DESC_SLOT_TY * 8, SHEET_ICON32, icon32_frame_tile(sKeys[idx[sCursor]].icon), 0, 0, 1, icon32_frame_palette(sKeys[idx[sCursor]].icon));
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
}

/* BARTGAME: the pause menu, after The Minish Cap, on one great plank of
   rotted wood. Three pages, R turns them, Start closes: the items in a
   grid of four to a row that scrolls, the buttons' items along the top
   and the chosen one described; the key items and the pieces of heart;
   and the map of the wood, drawn from the rooms themselves, that zooms
   into a cell to show what is marked there. A mark stays while its
   business is open and goes when it is done: a mystery's mouth until
   the mystery is won, a quest giver until the quest is paid, a chest
   until opened, a shrine until used, the Nun's relic from her asking to
   its taking. The Map draws every cell; the Astrolabe adds the chests,
   the Heart and the barriers between rooms. Nothing is saved here: the
   game saves itself at a win and at a death. */
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
#include "myst.h"
#include "game.h"
#include "menu.h"

/* BG3 carries the plank and the pictures: charblock 3, which the room
   maps own while the game plays and get back on the way out */
#define MENU_SB 22
#define MENU_PAL 8
#define PAL8 (MENU_PAL << 12)
#define PIC_BASE PLANKS_TILE_COUNT
/* the overview: five cells of 32x24 at a pixel a tile */
#define OV_X 40
#define OV_Y 16
#define OV_W 160
#define OV_H 120
/* the zoomed cell: the interior 30x21 at six pixels a tile */
#define ZM_X 32
#define ZM_Y 8
#define ZM_W 180
#define ZM_H 126
#define ZM_TW 23
#define ZM_TH 16

/* the mask's kinds, as roomgen.c numbers them */
enum { M_WALL, M_FLOOR, M_WATER, M_BRIDGE_H, M_BRIDGE_V, M_LEDGE, M_RAMP, M_FALL };
#define P_MID 4

enum { PG_ITEMS, PG_KEYS, PG_MAP, PG_COUNT };
static u8 sPage, sZoom;
static u8 sCursor, sScroll;
static u8 sMapCur;
static u8 sOverviewDone;
static u16 sMarksTile, sDotsTile, sCursorTile;
static u16 sBg3[32 * 32] EWRAM_BSS;
static u16 sTiles[ZM_TW * ZM_TH * 16] EWRAM_BSS;
static u8 sMasks[CELLS][32 * 24] EWRAM_BSS;

typedef struct {
    u8 eq;          /* EQ_* when a button can hold it, else EQ_NONE */
    u16 bit;        /* owned when this bit of gPl.items is set; 0x100 and up: of gPl.items2; 0: always */
    u8 icon;        /* a frame of the icon sheet */
    const char* name;
    const char* d1;
    const char* d2;
    const char* d3;
} MenuItem;

static const MenuItem sItems[] = {
    { EQ_SWORD, ITEM_SWORD, F_ICON32_SWORD, "Sword", "A simple blade with a", "hopeful edge. Cuts bushes", "and turns seeds. Press it." },
    { EQ_SHIELD, ITEM_SHIELD, F_ICON32_SHIELD, "Bark Shield", "Planks bound in brass.", "Turns bites and seeds", "from the front. Hold it." },
    { EQ_BOMBS, ITEM_BOMBS, F_ICON32_BOMBS, "Blightseeds", "Seeds that burst. They", "open cracked walls and", "break stones. Press: set." },
    { EQ_LAMP, ITEM_LAMP, F_ICON32_LAMP, "Grail Lamp", "A flame not of this wood.", "Burns webs and thorns,", "lights censers. Press it." },
    { EQ_CLOAK, ITEM_CLOAK, F_ICON32_CLOAK, "Petal Cloak", "Petals that catch the air.", "Leaps chasms and pits.", "Press, walking, to jump." },
    { EQ_BOW, 0x100 | ITEM2_BOW, F_ICON32_BOW, "Thorn Bow", "Yew and gut. An arrow for", "two hearts; walls stop it.", "Press to loose one." },
    { EQ_HUBCAP, 0x100 | ITEM2_HUBCAP, F_ICON32_HUBCAP, "Drain Cap", "Iron from the hub. The", "muck opens and takes you", "home to the drain. Press." },
};
#define ITEM_COUNT ((int)(sizeof(sItems) / sizeof(sItems[0])))

static const MenuItem sKeys[] = {
    { EQ_NONE, 0, F_ICON32_HEART_PIECE, "Pieces of Heart", "Quarters of a heart, from", "chests and mysteries.", "Four grow a whole heart." },
    { EQ_NONE, 0, F_ICON32_KEY, "Small Keys", "The dead keep them, and", "chests do. Each opens one", "locked door: walk into it" },
    { EQ_NONE, ITEM_GAUNTLET, F_ICON32_GAUNTLET, "Root Gauntlet", "Worn, not held. Roots", "that lift boulders out", "of the way: R before one." },
    { EQ_NONE, ITEM_RELIC, F_ICON32_RELIC, "the Relic", "The Weeping Nun's, taken", "from another chamber.", "Bring it back to her." },
    { EQ_NONE, 0x100 | ITEM2_MAP, F_ICON32_MAP, "Map of the Wood", "Every chamber drawn,", "seen or not. The marks", "still wait to be found." },
    { EQ_NONE, 0x100 | ITEM2_ASTROLABE, F_ICON32_ASTROLABE, "Astrolabe", "Brass that remembers. The", "map shows chests, the", "Heart and the barriers." },
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

static int gather(const MenuItem* list, int n, u8* out) {
    int i, k = 0;
    for (i = 0; i < n; i++)
        if (owned(&list[i]))
            out[k++] = i;
    return k;
}

static int strlen_(const char* s) {
    int n = 0;
    while (s[n])
        n++;
    return n;
}

/* ------------------------------------------------------------- plank -- */
static void bg3_plank(void) {
    int x, y;
    dma3_copy32(planks_tiles, CHARBLOCK(3), PLANKS_TILE_COUNT * 32);
    for (y = 0; y < 32; y++)
        for (x = 0; x < 32; x++)
            sBg3[y * 32 + x] = ((x < 30 && y < 20) ? planks_map[y * 30 + x] : 0) | PAL8;
    dma3_copy32(sBg3, SCREENBLOCK(MENU_SB), 32 * 32 * 2);
}

/* ---------------------------------------------------------- pictures -- */
static const u8 sColorOf[8] = { 7, 5, 8, 0xA, 0xA, 0xB, 0xA, 9 };

static u16 quad(u8 a, u8 b, u8 c, u8 d) {
    return a | (b << 4) | (c << 8) | (d << 12);
}

static u8 color_of(u8 v) {
    return (v & 0x80) ? 0xA : sColorOf[v & 7];
}

/* is the cell's layout to be drawn: visited, or the Map in hand */
static bool8 known(int cell) {
    return (gWorld.cells[cell].flags & CF_VISITED) || (gPl.items2 & ITEM2_MAP);
}

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

static void picture_show(int tx, int ty, int tw, int th) {
    int i, j;
    for (j = 0; j < th; j++)
        for (i = 0; i < tw; i++)
            sBg3[(ty + j) * 32 + tx + i] = (PIC_BASE + j * tw + i) | PAL8;
    dma3_copy32(sTiles, CHARBLOCK(3) + PIC_BASE * 16, tw * th * 32);
    dma3_copy32(sBg3, SCREENBLOCK(MENU_SB), 32 * 32 * 2);
}

static void picture_show_again(int tx, int ty, int tw, int th) {
    int i, j;
    for (j = 0; j < th; j++)
        for (i = 0; i < tw; i++)
            sBg3[(ty + j) * 32 + tx + i] = (PIC_BASE + j * tw + i) | PAL8;
    dma3_copy32(sBg3, SCREENBLOCK(MENU_SB), 32 * 32 * 2);
}

static void overview_render(void) {
    static const u8 cy_of[15] = { 0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4 };
    static const u8 y_in[15] = { 0, 8, 16, 0, 8, 16, 0, 8, 16, 0, 8, 16, 0, 8, 16 };
    int i, j, y, k;
    for (i = 0; i < CELLS; i++)
        if (known(i))
            fetch_mask(i);
    for (j = 0; j < OV_H / 8; j++) {
        for (i = 0; i < OV_W / 8; i++) {
            int cell = cy_of[j] * MAZE_W + (i >> 2), x0 = (i & 3) * 8;
            bool8 kn = known(cell);
            const u8* m = sMasks[cell];
            u16* t = &sTiles[(j * (OV_W / 8) + i) * 16];
            for (y = 0; y < 8; y++) {
                int py = y_in[j] + y;
                u8 p[8];
                for (k = 0; k < 8; k++) {
                    int px = x0 + k;
                    if (kn)
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

/* a four-pixel run of a tile's colour at six pixels a tile: pixel 0..5
   of the tile row; water has a light rim, a ledge a dark foot */
static u8 zpix(u8 col, int xin, int yin) {
    if (col == 8)
        return (yin == 0 || xin == 0) ? 9 : 8;
    if (col == 0xB && yin >= 4)
        return 7;
    if (col == 5 && ((xin == 2 && yin == 3) || (xin == 5 && yin == 0)))
        return 6;
    return col;
}

static void zoom_render(int cell) {
    /* pixel to tile and to the pixel within it, without a divide */
    static u8 div6[ZM_TW * 8], mod6[ZM_TW * 8];
    int i, j, y, k, d = 0, r = 0;
    bool8 kn = known(cell);
    const u8* m = sMasks[cell];
    for (i = 0; i < ZM_TW * 8; i++) {
        div6[i] = d;
        mod6[i] = r;
        if (++r == 6) {
            r = 0;
            d++;
        }
    }
    if (kn)
        fetch_mask(cell);
    for (j = 0; j < ZM_TH; j++) {
        for (i = 0; i < ZM_TW; i++) {
            u16* t = &sTiles[(j * ZM_TW + i) * 16];
            for (y = 0; y < 8; y++) {
                int py = j * 8 + y;
                u8 p[8];
                for (k = 0; k < 8; k++) {
                    int px = i * 8 + k;
                    if (!kn || px >= ZM_W || py >= ZM_H) {
                        p[k] = 3;
                    } else {
                        int tx = 1 + div6[px], ty = 2 + div6[py];
                        p[k] = zpix(color_of(m[ty * 32 + tx]), mod6[px], mod6[py]);
                    }
                }
                t[y * 2] = quad(p[0], p[1], p[2], p[3]);
                t[y * 2 + 1] = quad(p[4], p[5], p[6], p[7]);
            }
        }
    }
    picture_show(ZM_X / 8, ZM_Y / 8, ZM_TW, ZM_TH);
}

/* ------------------------------------------------------------- pages -- */
#define GRID_X(col) (2 + (col) * 7)
#define GRID_Y(row) (3 + ((row) - sScroll) * 5)

/* a carved hollow four tiles square, lit for the chosen one */
static void well(int tx, int ty, bool8 lit) {
    int x, y;
    u16 tl = lit ? MN_WELL_LIT_TL : MN_WELL_TL, t = lit ? MN_WELL_LIT_T : MN_WELL_T, l = lit ? MN_WELL_LIT_L : MN_WELL_L;
    for (y = 0; y < 4; y++)
        for (x = 0; x < 4; x++) {
            u16 tile, fl = 0;
            if (y == 0)
                tile = (x == 0 || x == 3) ? tl : t;
            else if (y == 3)
                tile = (x == 0 || x == 3) ? tl : t;
            else
                tile = (x == 0 || x == 3) ? l : MN_WELL_FILL;
            if (x == 3)
                fl |= 0x400;
            if (y == 3)
                fl |= 0x800;
            bg0_put_pal(tx + x, ty + y, (MENU_TILE_BASE + tile) | fl, MENU_PAL);
        }
}

static void grid_draw(int count) {
    int i;
    for (i = 0; i < count; i++) {
        int row = i / 4, col = i % 4;
        if (row < sScroll || row > sScroll + 1)
            continue;
        well(GRID_X(col), GRID_Y(row), i == sCursor);
    }
    if (sScroll > 0)
        bg0_put(29, 3, HT_ARROW | 0x800);
    if ((count + 3) / 4 > sScroll + 2)
        bg0_put(29, 11, HT_ARROW);
}

static void grid_icons(const MenuItem* list, const u8* idx, int count) {
    int i;
    for (i = 0; i < count; i++) {
        int row = i / 4, col = i % 4;
        if (row < sScroll || row > sScroll + 1)
            continue;
        draw_sprite(GRID_X(col) * 8, GRID_Y(row) * 8, SHEET_ICON32, icon32_sheet_tile(), list[idx[i]].icon, 0, 0, PAL_OBJ_ICONS);
    }
}

static void describe(const MenuItem* it) {
    bg0_print_big(2, 13, it->name, TRUE);
    bg0_print_big(2, 14, it->d1, FALSE);
    bg0_print_big(2, 15, it->d2, FALSE);
    bg0_print_big(2, 16, it->d3, FALSE);
}

static void held(int n) {
    bg0_print_big(20, 13, "held", FALSE);
    {
        char buf[4];
        buf[0] = '0' + (n / 10) % 10;
        buf[1] = '0' + n % 10;
        buf[2] = 0;
        bg0_print_big(25, 13, buf, TRUE);
    }
}

static void items_page(void) {
    static u8 idx[ITEM_COUNT];
    int n = gather(sItems, ITEM_COUNT, idx);
    bg0_fill(0, 3, 32, 17, 0);
    if (sCursor >= n)
        sCursor = n ? n - 1 : 0;
    if (sCursor / 4 < sScroll)
        sScroll = sCursor / 4;
    if (sCursor / 4 > sScroll + 1)
        sScroll = sCursor / 4 - 1;
    grid_draw(n);
    if (n) {
        const MenuItem* it = &sItems[idx[sCursor]];
        describe(it);
        if (it->eq == EQ_BOMBS)
            held(gPl.bombs);
        if (it->eq == EQ_BOW)
            held(gPl.arrows);
    }
}

static void keys_page(void) {
    static u8 idx[KEY_COUNT];
    int n = gather(sKeys, KEY_COUNT, idx), i;
    bg0_fill(0, 0, 32, 20, 0);
    if (sCursor >= n)
        sCursor = n ? n - 1 : 0;
    sScroll = 0;
    /* the pieces of heart, lit as they are found, and the hearts grown */
    for (i = 0; i < 4; i++)
        bg0_put(2 + i, 1, (i < gPl.hearts_pieces) ? HT_HEART_FULL : HT_HEART_EMPTY);
    for (i = 0; i < gPl.hp_max / 8 && i < 10; i++)
        bg0_put(18 + i, 1, HT_HEART_FULL);
    grid_draw(n);
    if (n) {
        const MenuItem* it = &sKeys[idx[sCursor]];
        describe(it);
        if (idx[sCursor] == 1)
            held(gPl.keys);
    }
}

static void map_banner(int cell) {
    Cell* c = &gWorld.cells[cell];
    const char* name = known(cell) ? sArchName[c->arch] : (cell == gWorld.entry) ? "the way in" : "unknown wood";
    int w = strlen_(name) + 4, x = 15 - w / 2;
    bg0_fill(0, 17, 32, 3, 0);
    bg0_frame(x, 17, w, 3);
    bg0_print_big(x + 2, 18, name, FALSE);
}

static void map_page(void) {
    bg0_fill(0, 0, 32, 20, 0);
    bg3_plank();
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
static int zx(int tx) { return ZM_X + (tx - 1) * 6 + 3; }
static int zy(int ty) { return ZM_Y + (ty - 2) * 6 + 3; }

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
        mark16(ZM_X + (PX(gPlayer->x) - 16) * 6 / 16, ZM_Y + (PX(gPlayer->y) - 8 - 32) * 6 / 16, F_MARKS_HERE);
}

static void overview_sprites(void) {
    int i, rc = relic_cell();
    bool8 astro = (gPl.items2 & ITEM2_ASTROLABE) != 0;
    draw_sprite(OV_X + (sMapCur % MAZE_W) * 32, OV_Y + (sMapCur / MAZE_W) * 24, SHEET_CURSOR, sCursorTile, F_CURSOR_CELL, 0, 0, PAL_OBJ_UI);
    for (i = 0; i < CELLS; i++) {
        Cell* c = &gWorld.cells[i];
        const u8* m = gWorld.mark[i];
        int ox = OV_X + (i % MAZE_W) * 32, oy = OV_Y + (i / MAZE_W) * 24, s;
        bool8 visited = (c->flags & CF_VISITED) != 0;
        if (visited) {
            if (m[MP_MOUTH * 2] && !(gWorld.myst_flags[i] & MF_DONE))
                dot8(ox + m[MP_MOUTH * 2] - 1, oy + m[MP_MOUTH * 2 + 1] - 1, F_DOTS_DOOR);
            if (m[MP_NPC * 2] && !(quest_giver(c) && (c->flags & CF_QUEST_DONE)))
                dot8(ox + m[MP_NPC * 2] - 1, oy + m[MP_NPC * 2 + 1] - 1, quest_giver(c) ? F_DOTS_QUEST : F_DOTS_FOLK);
            if (astro && m[MP_CHEST * 2] && has_chest(c))
                dot8(ox + m[MP_CHEST * 2] - 1, oy + m[MP_CHEST * 2 + 1] - 1, F_DOTS_CHEST);
        } else if (astro && has_chest(c)) {
            dot8(ox + 16, oy + 12, F_DOTS_CHEST);
        }
        if (rc == i)
            dot8(ox + ((visited && m[MP_RELIC * 2]) ? m[MP_RELIC * 2] - 1 : 16), oy + ((visited && m[MP_RELIC * 2]) ? m[MP_RELIC * 2 + 1] - 1 : 12), F_DOTS_RELIC);
        if (astro && i == gWorld.goal && !(c->flags & CF_CLEARED))
            dot8(ox + 16, oy + 11, F_DOTS_BOSS);
        if (astro)
            for (s = 0; s < 4; s++) {
                int mk = gate_mark(i, s);
                if (mk < 0 || (s != SIDE_N && s != SIDE_W))
                    continue;
                dot8(s == SIDE_N ? ox + 16 : ox + 1, s == SIDE_N ? oy + 1 : oy + 12, gate_dot(mk));
            }
    }
    if (gGame.area == AREA_FOREST)
        dot8(OV_X + (gGame.cell % MAZE_W) * 32 + PX(gPlayer->x) / 16, OV_Y + (gGame.cell / MAZE_W) * 24 + (PX(gPlayer->y) - 8) / 16, F_DOTS_HERE);
    else
        dot8(OV_X + (gWorld.entry % MAZE_W) * 32 + 16, OV_Y + (gWorld.entry / MAZE_W) * 24 + 22, F_DOTS_HERE);
}

/* -------------------------------------------------------------- open -- */
void menu_open(void) {
    sPage = PG_ITEMS;
    sZoom = 0;
    sCursor = 0;
    sScroll = 0;
    sOverviewDone = 0;
    sMapCur = (gGame.area == AREA_FOREST) ? gGame.cell : gWorld.entry;
    ensure_sheets();
    icon32_sheet_tile();
    REG_BLDCNT = 0;
    REG_BLDY = 0;
    bg3_plank();
    draw_page();
    gGame.state = GS_MAP;
    video_show(DCNT_BG0 | DCNT_BG3 | DCNT_OBJ);
    sfx_play(SFX_MENU);
}

static void menu_close(void) {
    bg0_fill(0, 0, 32, 20, 0);
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
    switch (sPage) {
        case PG_ITEMS: {
            int n = gather(sItems, ITEM_COUNT, idx);
            hud_draw_bar();
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
            bg3_plank();
        bg0_fill(0, 0, 32, 20, 0);
        draw_page();
    }
    if (gKeysDown & KEY_START)
        menu_close();
}

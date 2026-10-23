/* BARTGAME: the game state machine, areas, room transitions, chests,
   spawning a room's monsters. */
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
#include "enemy.h"
#include "objects.h"
#include "items.h"
#include "boss.h"
#include "npc.h"
extern u16 items_sheet_tile(void);
#include "react.h"
#include "game.h"

GameState gGame;
u32 gSeedOverride; /* probes set this before pressing Start */

static void draw_world(void);

/* pending transition */
static u8 sNextArea, sNextCell, sNextSide;
static u8 sTransPhase;

static const char* const sKeyItemText[4] = {
    "",
    "You found the BLIGHTSEED BOMBS!|Dark seeds that burst. Set one with B beside a cracked wall.",
    "You found the GRAIL LAMP!|A flame that is not of this wood. Swing it with B to burn webs and light censers.",
    "You found the PETAL CLOAK!|Press B to leap. A chasm is only a breath wide.",
};

/* --------------------------------------------------------- darkness -- */
/* The gardener's rooms are dark: a window of light around the hero that
   grows with every censer lit and flares while the lamp swings. */
static u8 sDark;

static void dark_off(void) {
    sDark = 0;
    REG_DISPCNT &= ~DCNT_WIN0;
    REG_BLDCNT = 0;
    REG_BLDY = 0;
}

static void dark_update(void) {
    if (!sDark)
        return;
    int unlit = room_torches_unlit();
    if (unlit == 0) {
        dark_off();
        return;
    }
    int r = 40 + (4 - unlit) * 22 + (gPl.lamp_timer ? 14 : 0);
    int cx = PX(gPlayer->x) - gCamX, cy = PX(gPlayer->y) - 16 - gCamY;
    int x0 = CLAMP(cx - r, 0, 240), x1 = CLAMP(cx + r, 0, 240);
    int y0 = CLAMP(cy - r, 0, 160), y1 = CLAMP(cy + r, 0, 160);
    REG_WIN0H = (x0 << 8) | x1;
    REG_WIN0V = (y0 << 8) | y1;
    REG_WININ = 0x001F;  /* every layer, no effect inside the light */
    REG_WINOUT = 0x003F; /* darkened outside */
    REG_BLDCNT = 0x00C0 | 0x0016; /* brightness down on BG1, BG2 and OBJ */
    REG_BLDY = 11;
    REG_DISPCNT |= DCNT_WIN0;
}

/* ----------------------------------------------------- cell objects -- */
static void spawn_cell_objects(void) {
    Cell* c = &gWorld.cells[gGame.cell];
    int i;
    enemy_load_sheets_for_theme(c->theme);
    objects_room_reset();
    for (i = 0; i < gSpots.spawn_count; i++) {
        int type = enemy_pick_type(c->theme, c->stage, hash32(gWorld.seed, gGame.cell * 31 + i));
        enemy_spawn(type, gSpots.spawns[i].x * 16 + 8, gSpots.spawns[i].y * 16 + 14);
    }
    if (gSpots.has_boss && !(c->flags & CF_CLEARED))
        boss_spawn(gSpots.boss.x * 16 + 16, gSpots.boss.y * 16 + 16);
    if (gSpots.has_npc) {
        int type = c->role == ROLE_NPC_HUNT ? NPC_HERMIT : c->role == ROLE_NPC_FETCH ? NPC_NUN : NPC_GARDENER;
        npc_spawn(type, gSpots.npc.x * 16 + 8, gSpots.npc.y * 16 + 14);
    }
    if (gSpots.has_relic)
        pickup_spawn(PK_RELIC, gSpots.relic.x * 16 + 8, gSpots.relic.y * 16 + 12);
    /* fireflies over the living rooms, a few, each on its own loop */
    if (c->stage < 3 && c->arch != ARCH_ARENA) {
        for (i = 0; i < 6; i++) {
            u32 h = hash32(gWorld.seed, gGame.cell * 97 + i);
            Actor* f = fx_spawn(FX_FIREFLY, 32 + h % (room_px_w() - 64), 40 + (h >> 8) % (room_px_h() - 72));
            if (f)
                f->v[0] = (h >> 16) & 31;
        }
    }
    /* the alcove's hoard: gilt that waits behind its bush or boulder */
    if (gSpots.has_treasure && !(c->opened & CELL_LOOTED)) {
        Actor* a = pickup_spawn(PK_GILT_BIG, gSpots.treasure.x * 16 + 8, gSpots.treasure.y * 16 + 12);
        if (a)
            a->v[2] = 1;
    }
}

/* ------------------------------------------------------------- areas -- */
static void load_sewer(int at_drain) {
    const RoomDef* def = &room_defs[ROOM_SEWER_MAIN];
    int i, sx = 8 * 16 + 8, sy = 11 * 16 + 14, facing = FACE_S;
    gGame.area = AREA_SEWER;
    room_load_def(def);
    actors_clear();
    sprites_reset();
    objects_room_reset();
    npc_room_reset();
    gDbg[4] = def->object_count;
    for (i = 0; i < def->object_count; i++) {
        const u8* ob = &def->objects[i * 4];
        gDbg[5] = (gDbg[5] << 4) | ob[0];
        if (ob[0] == OBJ_NPC)
            npc_spawn(NPC_SAGE, ob[1] * 16 + 8, ob[2] * 16 + 14);
        if (ob[0] == OBJ_SHOP)
            npc_spawn(NPC_MERCHANT, ob[1] * 16 + 8, ob[2] * 16 + 14);
        if (ob[0] == OBJ_SPAWN && !at_drain) {
            sx = ob[1] * 16 + 8;
            sy = ob[2] * 16 + 14;
            facing = ob[3];
        }
        if (ob[0] == OBJ_EXIT && at_drain) {
            sx = ob[1] * 16 + 8;
            sy = ob[2] * 16 + 16 + 14;
            facing = FACE_S;
        }
    }
    player_init(sx, sy, facing);
    camera_update(sx, sy - 16, TRUE);
    dark_off();
    minimap_render();
}

static void load_forest(int cell, int from_side) {
    int px, py;
    gGame.area = AREA_FOREST;
    gGame.cell = cell;
    gWorld.cells[cell].flags |= CF_VISITED;
    roomgen_build(cell);
    actors_clear();
    sprites_reset();
    npc_room_reset();
    roomgen_door_pos(from_side, &px, &py);
    player_init(px, py, (from_side + 2) & 3);
    camera_update(px, py - 16, TRUE);
    spawn_cell_objects();
    dark_off();
    minimap_render();
    {
        Cell* c = &gWorld.cells[cell];
        if (c->role == ROLE_NPC_TORCH && !(c->flags & CF_QUEST_DONE))
            sDark = 1;
    }
}

static void begin_transition(int area, int cell, int side) {
    sNextArea = area;
    sNextCell = cell;
    sNextSide = side;
    sTransPhase = 0;
    gGame.state = GS_TRANSITION;
    fade_start(16, 2);
}

/* --------------------------------------------------------- chests -- */
static void give_chest(Cell* c) {
    switch (c->role) {
        case ROLE_KEYITEM: {
            int item = c->role_arg;
            int bit = item == 1 ? ITEM_BOMBS : item == 2 ? ITEM_LAMP : ITEM_CLOAK;
            if (item == 1)
                gPl.bombs = 10;
            player_item_get(bit, item);
            textbox_open(sKeyItemText[item]);
            break;
        }
        case ROLE_KEYCHEST:
            gPl.keys++;
            player_item_get(0, 4);
            textbox_open("A SMALL KEY. Somewhere a lock remembers it.");
            sfx_play(SFX_KEY);
            break;
        default:
            switch (c->role_arg) {
                case CHEST_HEART_PIECE:
                    gPl.hearts_pieces++;
                    player_item_get(0, 5);
                    if (gPl.hearts_pieces >= 4) {
                        gPl.hearts_pieces = 0;
                        gPl.hp_max += 8;
                        gPl.hp = gPl.hp_max;
                        textbox_open("A fourth PIECE OF HEART. They beat as one: a new heart grows on the stalk.");
                    } else {
                        textbox_open("A PIECE OF HEART. Four make a whole.");
                    }
                    break;
                case CHEST_BOMBS:
                    gPl.bombs += 8;
                    if (gPl.bombs > 30)
                        gPl.bombs = 30;
                    player_item_get(0, 1);
                    textbox_open("Eight BLIGHTSEEDS, still warm.");
                    break;
                case CHEST_HEART_CONTAINER:
                    gPl.hp_max += 8;
                    gPl.hp = gPl.hp_max;
                    player_item_get(0, 6);
                    textbox_open("A HEART CONTAINER. Something in the dark decided you should live longer.");
                    break;
                case CHEST_GAUNTLET:
                    player_item_get(ITEM_GAUNTLET, F_ITEMS_GAUNTLET);
                    textbox_open("The ROOT GAUNTLET. Roots wrap the arm and remember the strength of trees: boulders lift now.");
                    break;
                default:
                    gPl.gilt += 30;
                    player_item_get(0, 7);
                    textbox_open("Thirty GILT. The dead have no use for it.");
                    break;
            }
            break;
    }
    c->flags |= CF_CHEST_OPEN;
    sfx_play(SFX_CHEST);
}

static void check_chest(void) {
    Actor* a = gPlayer;
    if (gGame.area != AREA_FOREST || a->state != PS_NORMAL)
        return;
    if (!(a->coll & COLL_N) || a->facing != FACE_N)
        return;
    int tx = PX(a->x) >> 4, ty = (PX(a->y) - 6 - 8) >> 4;
    if (room_type(tx, ty) != TT_CHEST)
        return;
    Cell* c = &gWorld.cells[gGame.cell];
    if (c->flags & CF_CHEST_OPEN)
        return;
    room_change(tx, ty, MT_CHEST_OPEN);
    give_chest(c);
}

/* ----------------------------------------------------------- shrine -- */
static void check_shrine(void) {
    Actor* a = gPlayer;
    if (gGame.area != AREA_FOREST || !gSpots.has_shrine)
        return;
    Cell* c = &gWorld.cells[gGame.cell];
    if (c->flags & CF_SHRINE_USED)
        return;
    int tx = PX(a->x) >> 4, ty = (PX(a->y) - 4) >> 4;
    if (tx == gSpots.shrine.x && ty == gSpots.shrine.y + 1) {
        c->flags |= CF_SHRINE_USED;
        gPl.hp = gPl.hp_max;
        room_change(tx, ty, MT_MOSSY_STONE);
        fx_spawn(FX_FLAME, tx * 16 + 8, ty * 16 + 4);
        sfx_play(SFX_SECRET);
        textbox_open("A shrine the blight forgot. It remembers the sun. Your wounds close.");
    }
    if (actor_find(AK_PICKUP, PK_RELIC) == NULL && gSpots.has_relic && (gPl.items & ITEM_RELIC))
        c->flags |= CF_RELIC_TAKEN;
}

/* ------------------------------------------------------------ exits -- */
static void check_exits(void) {
    Actor* a = gPlayer;
    int px = PX(a->x), py = PX(a->y);
    if (a->state == PS_FALL || a->state == PS_DEAD || a->state == PS_ITEMGET)
        return;
    if (gGame.area == AREA_SEWER) {
        if (room_type_px(px, py - 6) == TT_EXIT)
            begin_transition(AREA_FOREST, gWorld.entry, SIDE_S);
        return;
    }
    int cell = gGame.cell;
    if (room_type_px(px, py - 6) == TT_STAIRS) {
        begin_transition(AREA_SEWER, 0, 0);
        return;
    }
    /* the feet box stops 12 px short of the top edge and 6 of the sides */
    int side = -1;
    if (py < 14)
        side = SIDE_N;
    else if (py > room_px_h() - 2)
        side = SIDE_S;
    else if (px < 8)
        side = SIDE_W;
    else if (px > room_px_w() - 8)
        side = SIDE_E;
    if (side < 0)
        return;
    int n = cell_neighbor(cell, side);
    if (n < 0 || gWorld.cells[cell].gate[side] == GATE_WALL) {
        a->x = CLAMP(px, 8, room_px_w() - 8) << 16;
        a->y = CLAMP(py, 8, room_px_h() - 8) << 16;
        return;
    }
    begin_transition(AREA_FOREST, n, (side + 2) & 3);
}

/* ------------------------------------------------------------ title -- */
static u8 sTitlePhase;
static u32 sTitleSeed;
static u8 sDiedFlag;

static void title_show(void) {
    /* the title art lives in the world's charblock while it is shown */
    dma3_copy32(title_tiles, CHARBLOCK(0), TITLE_TILE_COUNT * 32);
    dma3_copy32(title_map, SCREENBLOCK(28), 32 * 20 * 2);
    dma3_fill32(0, SCREENBLOCK(24), 0x2000);
    pal_set_bg(0, title_pal);
    gBgScroll[1][0] = gBgScroll[1][1] = gBgScroll[2][0] = gBgScroll[2][1] = 0;
    actors_clear();
    bg0_clear();
    bg0_print_hud(10, 14, "PRESS START");
    bg0_print_hud(8, 17, "a game of the drain");
    gGame.state = GS_TITLE;
    gAnimTiles = 0;
    dark_off();
    sTitlePhase = 0;
    sTitleSeed = 0x5EED;
    fade_set(16);
    fade_start(0, 1);
    video_show(DCNT_BG0 | DCNT_BG2);
    bgm_play(BGM_TITLE);
}

static void start_run(u32 seed) {
    gGame.seed = seed;
    gGame.run_frames = 0;
    gGame.deaths = 0;
    gGame.kills = 0;
    world_generate(seed);
    player_new_game();
    tiles_init();
    gAnimTiles = 1;
    bg0_clear();
    load_sewer(0);
    gGame.state = GS_PLAY;
    fade_set(16);
    fade_start(0, 1);
    video_show(DCNT_BG0 | DCNT_BG1 | DCNT_BG2 | DCNT_OBJ);
    bgm_play(BGM_SEWER);
    textbox_open("You wake in the drain. The stalk you grew on is your spine now. Up the ladder is the wood.");
}

static void update_title(void) {
    sTitleSeed = sTitleSeed * 1103515245u + 12345u + gFrame;
    if ((gFrame & 32) == 0)
        bg0_print_hud(10, 14, "PRESS START");
    else
        bg0_print_hud(10, 14, "           ");
    if (sTitlePhase == 0 && (gKeysDown & KEY_START)) {
        sTitlePhase = 1;
        fade_start(16, 2);
        sfx_play(SFX_MENU);
    }
    if (sTitlePhase == 1 && fade_done())
        start_run(gSeedOverride ? gSeedOverride : (sTitleSeed >> 4));
}

/* ------------------------------------------------------------ pause -- */
/* The pause menu, after The Minish Cap: an items page where the cursor
   picks a thing and A, B or L takes it; R turns to the map page. */
typedef struct {
    u8 eq;        /* EQ_* when a button can hold it, else EQ_NONE */
    u8 item_bit;  /* owned when this bit is set (0: always shown) */
    u8 icon;      /* frame of the items sheet, or 0xFF for the sword */
    const char* name;
    const char* d1;
    const char* d2;
} PauseItem;

static const PauseItem sPauseItems[] = {
    { EQ_SWORD, ITEM_SWORD, 0xFF, "Sword", "A simple blade with a", "hopeful edge. Cuts bushes." },
    { EQ_SHIELD, ITEM_SHIELD, 0xFF, "Bark Shield", "Planks bound in brass. Held", "up, it turns bites and seeds." },
    { EQ_BOMBS, ITEM_BOMBS, F_ITEMS_BOMBS, "Blightseeds", "Seeds that burst and open", "cracked walls." },
    { EQ_LAMP, ITEM_LAMP, F_ITEMS_LAMP, "Grail Lamp", "A flame not of this wood.", "Burns webs, lights censers." },
    { EQ_CLOAK, ITEM_CLOAK, F_ITEMS_CLOAK, "Petal Cloak", "Petals that catch the air.", "Leaps chasms and pits." },
    { EQ_NONE, ITEM_GAUNTLET, F_ITEMS_GAUNTLET, "Root Gauntlet", "Worn, not held. Roots that", "lift boulders out of the way." },
    { EQ_NONE, ITEM_RELIC, F_ITEMS_RELIC, "the Relic", "The Weeping Nun's. Bring it", "back to her." },
};
#define PAUSE_ITEM_COUNT ((int)(sizeof(sPauseItems) / sizeof(sPauseItems[0])))

static u8 sPausePage;   /* 0 items, 1 map */
static u8 sPauseCursor; /* index into the owned list */
static u8 sPauseOwned[PAUSE_ITEM_COUNT];
static u8 sPauseOwnedCount;
static const u8 sPauseSlotX[SLOT_COUNT] = { 5, 11, 17 };

static void pause_items_page(void) {
    int i;
    bg0_fill(0, 3, 32, 17, 0);
    bg0_frame(1, 3, 28, 17);
    bg0_print_gold(3, 4, "ITEMS");
    bg0_print(15, 4, "R: map  Start: out");
    /* the three buttons */
    bg0_put(sPauseSlotX[0] - 1, 6, HT_BTN_A);
    bg0_put(sPauseSlotX[1] - 1, 6, HT_BTN_B);
    bg0_put(sPauseSlotX[2] - 1, 6, HT_BTN_L);
    for (i = 0; i < SLOT_COUNT; i++) {
        int x = sPauseSlotX[i], lit = gPl.equip[i] != EQ_NONE;
        bg0_put(x, 6, lit ? HT_SLOT_LIT_TL : HT_SLOT_TL);
        bg0_put(x + 1, 6, lit ? HT_SLOT_LIT_TR : HT_SLOT_TR);
        bg0_put(x, 7, lit ? HT_SLOT_LIT_BL : HT_SLOT_BL);
        bg0_put(x + 1, 7, lit ? HT_SLOT_LIT_BR : HT_SLOT_BR);
    }
    bg0_put(23, 6, HT_BTN_R);
    bg0_put(24, 6, HT_HAND);
    bg0_print(22, 7, "lift");
    for (i = 0; i < 26; i++)
        bg0_put(2 + i, 9, HT_RULE);
    /* what the hero owns, in a row */
    sPauseOwnedCount = 0;
    for (i = 0; i < PAUSE_ITEM_COUNT; i++)
        if (gPl.items & sPauseItems[i].item_bit)
            sPauseOwned[sPauseOwnedCount++] = i;
    if (sPauseCursor >= sPauseOwnedCount)
        sPauseCursor = 0;
    for (i = 0; i < sPauseOwnedCount; i++) {
        int x = 3 + i * 4, lit = (i == sPauseCursor);
        bg0_put(x, 10, lit ? HT_SLOT_LIT_TL : HT_SLOT_TL);
        bg0_put(x + 1, 10, lit ? HT_SLOT_LIT_TR : HT_SLOT_TR);
        bg0_put(x, 11, lit ? HT_SLOT_LIT_BL : HT_SLOT_BL);
        bg0_put(x + 1, 11, lit ? HT_SLOT_LIT_BR : HT_SLOT_BR);
    }
    if (sPauseOwnedCount) {
        const PauseItem* it = &sPauseItems[sPauseOwned[sPauseCursor]];
        bg0_print_gold(3, 13, it->name);
        if (it->eq == EQ_BOMBS) {
            bg0_print(16, 13, "held");
            bg0_print_num(21, 13, gPl.bombs, 2);
        }
        bg0_print(3, 14, it->d1);
        bg0_print(3, 15, it->d2);
    }
    bg0_print(3, 17, "small keys");
    bg0_print_num(14, 17, gPl.keys, 1);
    bg0_print(3, 18, "A, B or L takes the item");
}

static const char* quest_status(int role) {
    int i;
    for (i = 0; i < CELLS; i++) {
        Cell* c = &gWorld.cells[i];
        if (c->role != role)
            continue;
        if (c->flags & CF_QUEST_DONE)
            return "done";
        if (c->flags & CF_QUEST_ACTIVE)
            return "open";
        if (c->flags & CF_VISITED)
            return "found";
        return "unknown";
    }
    return "none";
}

static void pause_map_page(void) {
    int x, y;
    bg0_fill(0, 3, 32, 17, 0);
    bg0_frame(1, 3, 28, 17);
    bg0_print_gold(3, 4, "THE WOOD");
    bg0_print(13, 4, "R: items  Start: out");
    for (y = 0; y < MAZE_H; y++) {
        for (x = 0; x < MAZE_W; x++) {
            int i = y * MAZE_W + x;
            Cell* c = &gWorld.cells[i];
            u16 t = HT_MAP_UNKNOWN;
            if (c->flags & CF_VISITED)
                t = HT_MAP_CELL;
            if (i == gWorld.goal && (c->flags & CF_VISITED))
                t = HT_MAP_GOAL;
            if (gGame.area == AREA_FOREST && i == gGame.cell)
                t = HT_MAP_HERE;
            bg0_put(3 + x, 6 + y, t);
        }
    }
    bg0_put(9, 6, HT_MAP_HERE);
    bg0_print(10, 6, "you");
    bg0_put(9, 7, HT_MAP_GOAL);
    bg0_print(10, 7, "Heart");
    bg0_put(9, 8, HT_MAP_CELL);
    bg0_print(10, 8, "seen");
    bg0_print_gold(17, 6, "QUESTS");
    bg0_print(17, 7, "hunt");
    bg0_print(23, 7, quest_status(ROLE_NPC_HUNT));
    bg0_print(17, 8, "relic");
    bg0_print(23, 8, quest_status(ROLE_NPC_FETCH));
    bg0_print(17, 9, "fire");
    bg0_print(23, 9, quest_status(ROLE_NPC_TORCH));
    bg0_print_gold(3, 12, "THE RUN");
    bg0_print(3, 13, "gilt");
    bg0_print_num(8, 13, gPl.gilt, 3);
    bg0_print(13, 13, "keys");
    bg0_print_num(18, 13, gPl.keys, 1);
    bg0_print(21, 13, "slain");
    bg0_print_num(26, 13, gGame.kills, 2);
    bg0_print(3, 14, "deaths");
    bg0_print_num(10, 14, gGame.deaths, 2);
    bg0_print(13, 14, "seeds");
    bg0_print_num(19, 14, gPl.bombs, 2);
    bg0_print(3, 16, "The Heart waits in the");
    bg0_print(3, 17, "deepest glade. Cut it out.");
}

static void map_open(void) {
    sPausePage = 0;
    pause_items_page();
    gGame.state = GS_MAP;
    sfx_play(SFX_MENU);
}

static void update_map(void) {
    int i;
    draw_world();
    if (sPausePage == 0) {
        for (i = 0; i < SLOT_COUNT; i++)
            hud_equip_icon(gPl.equip[i], sPauseSlotX[i] * 8, 6 * 8, 0);
        for (i = 0; i < sPauseOwnedCount; i++) {
            const PauseItem* it = &sPauseItems[sPauseOwned[i]];
            if (it->icon == 0xFF)
                hud_equip_icon(it->eq, (3 + i * 4) * 8, 10 * 8, 0);
            else
                draw_sprite((3 + i * 4) * 8, 10 * 8, SHEET_ITEMS, items_sheet_tile(), it->icon, 0, 0, PAL_OBJ_FX);
        }
        if ((gKeysDown & KEY_RIGHT) && sPauseCursor + 1 < sPauseOwnedCount) {
            sPauseCursor++;
            sfx_play(SFX_MENU);
            pause_items_page();
        }
        if ((gKeysDown & KEY_LEFT) && sPauseCursor > 0) {
            sPauseCursor--;
            sfx_play(SFX_MENU);
            pause_items_page();
        }
        if (sPauseOwnedCount && (gKeysDown & (KEY_A | KEY_B | KEY_L))) {
            const PauseItem* it = &sPauseItems[sPauseOwned[sPauseCursor]];
            int slot = (gKeysDown & KEY_A) ? SLOT_A : (gKeysDown & KEY_B) ? SLOT_B : SLOT_L;
            if (it->eq != EQ_NONE) {
                player_equip_set(slot, it->eq);
                sfx_play(SFX_ITEM);
            } else {
                sfx_play(SFX_BUMP);
            }
            pause_items_page();
        }
    }
    if (gKeysDown & KEY_R) {
        sPausePage ^= 1;
        sfx_play(SFX_MENU);
        if (sPausePage)
            pause_map_page();
        else
            pause_items_page();
    }
    if (gKeysDown & KEY_START) {
        bg0_fill(0, 3, 32, 17, 0);
        gGame.state = GS_PLAY;
        gKeysDown = 0;
    }
}

/* -------------------------------------------------------------- win -- */
static u16 sWinTimer;

void game_win(void) {
    gGame.state = GS_WIN;
    sWinTimer = 0;
    fade_start(16, 1);
    bgm_play(BGM_WIN);
}

static void update_win(void) {
    sWinTimer++;
    if (sWinTimer < 40) {
        draw_world();
        return;
    }
    if (sWinTimer == 40) {
        int secs = gGame.run_frames / 60;
        actors_clear();
        video_show(DCNT_BG0);
        bg0_clear();
        bg0_print(6, 4, "THE HEART IS CUT.");
        bg0_print(2, 7, "The wood breathes again,");
        bg0_print(2, 8, "slowly. Somewhere a king");
        bg0_print(2, 9, "stops dreaming.");
        bg0_print(4, 12, "gilt");
        bg0_print_num(9, 12, gPl.gilt, 3);
        bg0_print(14, 12, "time");
        bg0_print_num(19, 12, secs / 60, 2);
        bg0_print(21, 12, ":");
        bg0_print_num(22, 12, (secs % 60) / 10, 1);
        bg0_print_num(23, 12, secs % 10, 1);
        bg0_print(4, 13, "deaths");
        bg0_print_num(11, 13, gGame.deaths, 2);
        bg0_print(4, 14, "slain");
        bg0_print_num(11, 14, gGame.kills, 3);
        bg0_print(9, 17, "PRESS START");
        fade_start(0, 1);
    }
    if (sWinTimer > 120 && (gKeysDown & KEY_START))
        title_show();
}

/* ----------------------------------------------------------- states -- */
void game_init(void) {
    title_show();
}

static void draw_world(void) {
    player_draw();
    enemies_draw();
    npcs_draw();
    objects_draw();
    hud_draw();
    textbox_draw();
    shop_draw();
}

u32 gDbgSpawn; /* probes: (count << 8) | type, spawns around the hero */

static void debug_spawn(void) {
    if (!gDbgSpawn)
        return;
    int type = gDbgSpawn & 0xFF, n = gDbgSpawn >> 8, i;
    gDbgSpawn = 0;
    for (i = 0; i < n; i++) {
        int px = PX(gPlayer->x) - 60 + (i % 8) * 16;
        int py = PX(gPlayer->y) - 60 + (i / 8) * 20;
        enemy_spawn(type, CLAMP(px, 24, room_px_w() - 24), CLAMP(py, 40, room_px_h() - 24));
    }
}

static void update_play(void) {
    debug_spawn();
    if (npc_dialogue_active()) {
        npc_dialogue_update();
        npcs_update();
        draw_world();
        return;
    }
    if (textbox_active()) {
        textbox_update();
        draw_world();
        return;
    }
    if ((gKeysDown & KEY_A) && npc_try_talk()) {
        gKeysDown &= ~KEY_A;
        draw_world();
        return;
    }
    player_update();
    if (gPlayer->state == PS_DEAD) {
        if (gPl.dead_timer > 120) {
            gPl.hp = gPl.hp_max;
            gGame.deaths++;
            sDiedFlag = 1;
            begin_transition(AREA_SEWER, 0, 0);
        }
        draw_world();
        return;
    }
    if (gKeysDown & KEY_START) {
        map_open();
        return;
    }
    items_update();
    enemies_update();
    npcs_update();
    objects_update();
    check_chest();
    check_shrine();
    check_exits();
    camera_update(PX(gPlayer->x), PX(gPlayer->y) - 16, FALSE);
    dark_update();
    draw_world();
}

static void update_transition(void) {
    draw_world();
    if (sTransPhase == 0) {
        if (!fade_done())
            return;
        if (sNextArea == AREA_SEWER) {
            load_sewer(1);
            bgm_play(BGM_SEWER);
        } else {
            int was_forest = (gGame.area == AREA_FOREST);
            load_forest(sNextCell, sNextSide);
            if (!was_forest)
                bgm_play(BGM_FOREST);
        }
        sTransPhase = 1;
        fade_start(0, 2);
        return;
    }
    if (fade_done()) {
        gGame.state = GS_PLAY;
        if (sDiedFlag) {
            sDiedFlag = 0;
            textbox_open_named("The Bloom", F_PORTRAIT_HERO_SURPRISED, "The muck takes me back. It always does. The wood keeps what I opened...");
        }
    }
}

void game_update(void) {
    if (gGame.state == GS_PLAY || gGame.state == GS_TRANSITION)
        gGame.run_frames++;
    switch (gGame.state) {
        case GS_TITLE: update_title(); break;
        case GS_PLAY: update_play(); break;
        case GS_TRANSITION: update_transition(); break;
        case GS_MAP: update_map(); break;
        case GS_WIN: update_win(); break;
        default: break;
    }
}

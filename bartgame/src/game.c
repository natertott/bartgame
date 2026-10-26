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
#include "ui.h"
#include "world.h"
#include "roomgen.h"
#include "myst.h"
#include "enemy.h"
#include "objects.h"
#include "items.h"
#include "boss.h"
#include "npc.h"
extern u16 items_sheet_tile(void);
#include "react.h"
#include "menu.h"
#include "save.h"
#include "game.h"

GameState gGame;
u32 gSeedOverride; /* probes set this before pressing Start */

static void draw_world(void);

/* pending transition */
static u8 sNextArea, sNextCell, sNextSide;
static u8 sTitleCursor, sTitleHasSave; /* the title's choice when a save exists */
static u8 sTransPhase;
static u8 sHubcap; /* the pending transition is the Drain Cap's: drop in at the spawn */

static const char* const sKeyItemText[4] = {
    "",
    "You found the " INK_HIGH "Blightseeds" INK_BASE "!|Dark seeds that burst. Set one with " INK_GOLD "B" INK_BASE " beside a cracked wall.",
    "You found the " INK_HIGH "Grail Lamp" INK_BASE "!|A flame that is not of this wood. Swing it with " INK_GOLD "B" INK_BASE " to burn webs and light censers.",
    "You found the " INK_HIGH "Petal Cloak" INK_BASE "!|Press " INK_GOLD "B" INK_BASE " to leap. A chasm is only a breath wide.",
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
    tiles_load(TS_SEWER);
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
    tiles_load(TS_FOREST);
    roomgen_build(cell);
    actors_clear();
    sprites_reset();
    npc_room_reset();
    if (from_side == SIDE_MOUTH && gSpots.has_mouth) {
        px = gSpots.mouth.x * 16 + 8;
        py = (gSpots.mouth.y + 1) * 16 + 14;
        player_init(px, py, FACE_S);
    } else {
        roomgen_door_pos(from_side, &px, &py);
        player_init(px, py, (from_side + 2) & 3);
    }
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

/* a mystery room: the hero stands over its way out, facing in */
static void load_myst(int cell) {
    int px, py;
    gGame.area = AREA_MYST;
    gGame.cell = cell;
    tiles_load(TS_MYST);
    myst_build(cell);
    actors_clear();
    sprites_reset();
    objects_room_reset();
    npc_room_reset();
    enemy_load_sheets_for_theme(gWorld.cells[cell].theme);
    myst_start_pos(&px, &py);
    player_init(px, py, FACE_N);
    camera_update(px, py - 16, TRUE);
    dark_off();
    myst_enter();
}

static void begin_transition(int area, int cell, int side) {
    sNextArea = area;
    sNextCell = cell;
    sNextSide = side;
    sTransPhase = 0;
    gGame.state = GS_TRANSITION;
    fade_start(16, 2);
}

void game_return_to_hub(void) {
    sHubcap = 1;
    begin_transition(AREA_SEWER, 0, 0);
}

/* --------------------------------------------------------- chests -- */
static void give_chest(Cell* c) {
    switch (c->role) {
        case ROLE_KEYITEM: {
            int item = c->role_arg;
            int bit = item == 1 ? ITEM_BOMBS : item == 2 ? ITEM_LAMP : ITEM_CLOAK;
            if (item == 1)
                gPl.bombs = 10;
            player_item_get(bit, item == 1 ? F_ICON32_BOMBS : item == 2 ? F_ICON32_LAMP : F_ICON32_CLOAK);
            textbox_open(sKeyItemText[item]);
            break;
        }
        case ROLE_KEYCHEST:
            gPl.keys++;
            player_item_get(0, F_ICON32_KEY);
            textbox_open("A " INK_HIGH "small key" INK_BASE ". Somewhere a lock remembers it.");
            sfx_play(SFX_KEY);
            break;
        default:
            switch (c->role_arg) {
                case CHEST_HEART_PIECE:
                    gPl.hearts_pieces++;
                    player_item_get(0, F_ICON32_HEART_PIECE);
                    if (gPl.hearts_pieces >= 4) {
                        gPl.hearts_pieces = 0;
                        gPl.hp_max += 8;
                        gPl.hp = gPl.hp_max;
                        textbox_open("A fourth " INK_HIGH "piece of heart" INK_BASE ". They beat as one: a new heart grows on the stalk.");
                    } else {
                        textbox_open("A " INK_HIGH "piece of heart" INK_BASE ". Four make a whole.");
                    }
                    break;
                case CHEST_BOMBS:
                    gPl.bombs += 8;
                    if (gPl.bombs > 30)
                        gPl.bombs = 30;
                    player_item_get(0, F_ICON32_BOMBS);
                    textbox_open("Eight " INK_HIGH "blightseeds" INK_BASE ", still warm.");
                    break;
                case CHEST_BOW:
                    gPl.items2 |= ITEM2_BOW;
                    gPl.arrows = 20;
                    player_item_get(0, F_ICON32_BOW);
                    player_auto_equip(EQ_BOW);
                    textbox_open("You found the " INK_HIGH "Thorn Bow" INK_BASE "!|Twenty arrows with it. Loose one with its button. The dead drop more; the Peddler sells them.");
                    break;
                case CHEST_MAP:
                    gPl.items2 |= ITEM2_MAP;
                    player_item_get(0, F_ICON32_MAP);
                    textbox_open("You found the " INK_HIGH "Map of the Wood" INK_BASE "!|Every chamber is drawn on it now. Look at it from the pause menu.");
                    break;
                case CHEST_ASTROLABE:
                    gPl.items2 |= ITEM2_ASTROLABE;
                    player_item_get(0, F_ICON32_ASTROLABE);
                    textbox_open("You found the " INK_HIGH "Astrolabe" INK_BASE "!|Brass that remembers. The map shows chests, the Heart and what bars the ways.");
                    break;
                case CHEST_HEART_CONTAINER:
                    gPl.hp_max += 8;
                    gPl.hp = gPl.hp_max;
                    player_item_get(0, F_ICON32_HEART_CONTAINER);
                    textbox_open("A " INK_HIGH "heart container" INK_BASE ". Something in the dark decided you should live longer.");
                    break;
                case CHEST_GAUNTLET:
                    player_item_get(ITEM_GAUNTLET, F_ICON32_GAUNTLET);
                    textbox_open("The " INK_HIGH "Root Gauntlet" INK_BASE ". Roots wrap the arm and remember the strength of trees: boulders lift now.");
                    break;
                default:
                    gPl.gilt += 30;
                    player_item_get(0, F_ICON32_GILT_BIG);
                    textbox_open("Thirty " INK_HIGH "gilt" INK_BASE ". The dead have no use for it.");
                    break;
            }
            break;
    }
    c->flags |= CF_CHEST_OPEN;
    sfx_play(SFX_CHEST);
}

static void check_chest(void) {
    Actor* a = gPlayer;
    if ((gGame.area != AREA_FOREST && gGame.area != AREA_MYST) || a->state != PS_NORMAL)
        return;
    if (!(a->coll & COLL_N) || a->facing != FACE_N)
        return;
    int tx = PX(a->x) >> 4, ty = (PX(a->y) - 6 - 8) >> 4;
    if (room_type(tx, ty) != TT_CHEST)
        return;
    if (gGame.area == AREA_MYST) {
        myst_chest_opened(tx, ty);
        return;
    }
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
    if (gGame.area == AREA_MYST) {
        /* the way out is in the bottom wall; the mouth, back in the wood */
        if (room_type_px(px, py - 6) == TT_MYST)
            begin_transition(AREA_FOREST, cell, SIDE_MOUTH);
        return;
    }
    if (room_type_px(px, py - 6) == TT_STAIRS) {
        begin_transition(AREA_SEWER, 0, 0);
        return;
    }
    if (room_type_px(px, py - 6) == TT_MYST) {
        begin_transition(AREA_MYST, cell, 0);
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

static Canvas sTitlePress, sTitleTag, sTitleMenu;

/* a canvas of words centred across the screen at tile row ty, outlined
   in the dark so the title's art does not swallow them */
static void title_words(Canvas* c, int ty, int tw, int th) {
    bg0_canvas(c, (30 - tw) / 2, ty, tw, th);
}

static void title_line(Canvas* c, int y, const char* s, int ink) {
    vwf_text_fx(c, (c->tw * 8 - vwf_width(s)) / 2, y, s, ink, UI_INK_DARK, FX_OUTLINE);
}

/* the choice when a save exists: the chosen one in gold */
static void title_menu(void) {
    vwf_clear(&sTitleMenu, 0);
    title_line(&sTitleMenu, 2, "Continue", sTitleCursor == 0 ? UI_INK_GOLD : UI_INK_CREAM);
    title_line(&sTitleMenu, 14, "New Game", sTitleCursor == 1 ? UI_INK_GOLD : UI_INK_CREAM);
    vwf_flush(&sTitleMenu, FALSE);
}

static void title_show(void) {
    /* the title art lives in the world's charblock while it is shown */
    dma3_copy32(title_tiles, CHARBLOCK(0), TITLE_TILE_COUNT * 32);
    dma3_copy32(title_map, SCREENBLOCK(28), 32 * 20 * 2);
    dma3_fill32(0, SCREENBLOCK(24), 0x2000);
    pal_set_bg(0, title_pal);
    gBgScroll[1][0] = gBgScroll[1][1] = gBgScroll[2][0] = gBgScroll[2][1] = 0;
    actors_clear();
    bg0_clear();
    bg0_pool_reset();
    sTitleHasSave = save_exists();
    sTitleCursor = 0;
    if (sTitleHasSave) {
        title_words(&sTitleMenu, 13, 8, 4);
        title_menu();
    } else {
        title_words(&sTitlePress, 14, 8, 2);
        title_line(&sTitlePress, 3, "Press Start", UI_INK_CREAM);
        vwf_flush(&sTitlePress, TRUE);
    }
    title_words(&sTitleTag, 16, 12, 2);
    title_line(&sTitleTag, 3, "a game from the drain", UI_INK_GOLD);
    vwf_flush(&sTitleTag, TRUE);
    gGame.state = GS_TITLE;
    gAnimTiles = 0;
    dark_off();
    sTitlePhase = 0;
    sTitleSeed = 0x5EED;
    fade_set(16);
    fade_start(0, 1);
    video_show(DCNT_BG0 | DCNT_BG2 | DCNT_OBJ);
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

/* a saved run wakes in the drain with everything it had */
static void continue_run(void) {
    if (!save_load()) {
        start_run(sTitleSeed >> 4);
        return;
    }
    tiles_init();
    gAnimTiles = 1;
    bg0_clear();
    load_sewer(0);
    gGame.state = GS_PLAY;
    fade_set(16);
    fade_start(0, 1);
    video_show(DCNT_BG0 | DCNT_BG1 | DCNT_BG2 | DCNT_OBJ);
    bgm_play(BGM_SEWER);
    textbox_open("You wake in the drain again. The wood remembers what you opened, and so do you.");
}

static void update_title(void) {
    sTitleSeed = sTitleSeed * 1103515245u + 12345u + gFrame;
    if (sTitleHasSave) {
        /* a saved run: continue it, or begin anew */
        static const u8 nudge[4] = { 0, 1, 2, 1 };
        if (sTitlePhase == 0 && (gKeysDown & (KEY_UP | KEY_DOWN))) {
            sTitleCursor ^= 1;
            title_menu();
            sfx_play(SFX_MENU);
        }
        int x = ((30 - 8) / 2) * 8 + (64 - vwf_width("Continue")) / 2 - 10;
        draw_sprite(x + nudge[(gFrame >> 3) & 3], 13 * 8 + 2 + sTitleCursor * 12, SHEET_UIMARKS, OBJ_TILE_UI, F_UIMARKS_PICK, 0, 0, PAL_OBJ_UIKIT);
    } else {
        /* Press Start blinks */
        bg0_show(&sTitlePress, (30 - 8) / 2, 14, (gFrame & 32) == 0);
    }
    if (sTitlePhase == 0 && (gKeysDown & (KEY_START | KEY_A))) {
        sTitlePhase = 1;
        fade_start(16, 2);
        sfx_play(SFX_MENU);
    }
    if (sTitlePhase == 1 && fade_done()) {
        if (sTitleHasSave && sTitleCursor == 0)
            continue_run();
        else
            start_run(gSeedOverride ? gSeedOverride : (sTitleSeed >> 4));
    }
}

/* -------------------------------------------------------------- win -- */
static u16 sWinTimer;

void game_win(void) {
    save_write(); /* the run is kept at a win */
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
        static Canvas plate, body, stats, press;
        int secs = gGame.run_frames / 60, i, x;
        char buf[12];
        u16* m;
        actors_clear();
        video_show(DCNT_BG0);
        bg0_clear();
        bg0_pool_reset();
        m = bg0_map();
        /* the tale's end in a panel under a gold plate, the run's count in
           two columns under a rule */
        ui_frame(m, UI_BG0, 3, 4, 24, 12, FR_PANEL);
        x = ui_plate_tiles(vwf_width("The Heart is cut"), 6);
        bg0_plate(&plate, (30 - x) / 2, 3, "The Heart is cut", UI_INK_GOLD, TRUE);
        bg0_canvas(&body, 4, 6, 22, 3);
        vwf_clear(&body, UI_INK_NAVY); /* BG0 alone: nothing behind the panel */
        title_line(&body, 2, "The wood breathes again, slowly.", UI_INK_CREAM);
        title_line(&body, 13, "Somewhere a king stops dreaming.", UI_INK_CREAM);
        ui_tile(m, UI_BG0, 6, 10, UI_RULE_END, UI_HF);
        for (i = 7; i < 23; i++)
            ui_tile(m, UI_BG0, i, 10, UI_RULE, 0);
        ui_tile(m, UI_BG0, 23, 10, UI_RULE_END, 0);
        bg0_canvas(&stats, 5, 11, 20, 4);
        vwf_clear(&stats, UI_INK_NAVY);
        vwf_text(&stats, 4, 2, "Gilt", UI_INK_DIM);
        vwf_text(&stats, 40, 2, vwf_num(buf, gPl.gilt, 0), UI_INK_GOLD);
        vwf_text(&stats, 84, 2, "Time", UI_INK_DIM);
        x = vwf_text(&stats, 120, 2, vwf_num(buf, secs / 60, 0), UI_INK_GOLD);
        x = vwf_text(&stats, x, 2, ":", UI_INK_GOLD);
        buf[0] = '0' + (secs % 60) / 10;
        buf[1] = '0' + secs % 10;
        buf[2] = 0;
        vwf_text(&stats, x, 2, buf, UI_INK_GOLD);
        vwf_text(&stats, 4, 16, "Deaths", UI_INK_DIM);
        vwf_text(&stats, 40, 16, vwf_num(buf, gGame.deaths, 0), UI_INK_GOLD);
        vwf_text(&stats, 84, 16, "Slain", UI_INK_DIM);
        vwf_text(&stats, 120, 16, vwf_num(buf, gGame.kills, 0), UI_INK_GOLD);
        bg0_canvas(&press, 11, 17, 8, 2);
        title_line(&press, 3, "Press Start", UI_INK_CREAM);
        vwf_flush(&plate, TRUE);
        vwf_flush(&body, TRUE);
        vwf_flush(&stats, TRUE);
        vwf_flush(&press, TRUE);
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
    textbox_draw(); /* first in OAM: between sprites the order rules */
    npcs_draw_front();
    player_draw();
    enemies_draw();
    npcs_draw();
    objects_draw();
    hud_draw();
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
        if (shop_active()) {
            shop_draw(); /* the whole screen: no world behind it */
            return;
        }
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
        if (shop_active())
            shop_draw();
        else
            draw_world();
        return;
    }
    player_update();
    if (gPlayer->state == PS_DEAD) {
        if (gPl.dead_timer > 120) {
            gPl.hp = gPl.hp_max;
            gGame.deaths++;
            sDiedFlag = 1;
            save_write(); /* and at a death: the wood keeps what was opened */
            begin_transition(AREA_SEWER, 0, 0);
        }
        draw_world();
        return;
    }
    if (gKeysDown & KEY_START) {
        menu_open();
        return;
    }
    items_update();
    enemies_update();
    npcs_update();
    objects_update();
    if (gGame.area == AREA_MYST)
        myst_update();
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
            load_sewer(sHubcap ? 0 : 1);
            if (sHubcap) {
                sHubcap = 0;
                player_drop_in();
            }
            bgm_play(BGM_SEWER);
        } else if (sNextArea == AREA_MYST) {
            load_myst(sNextCell);
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
            textbox_open_named("The Bloom", F_FACE_BLOOM_SURPRISED, "The muck takes me back. It always does. The wood keeps what I opened...");
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
        case GS_MAP: menu_update(); break;
        case GS_WIN: update_win(); break;
        default: break;
    }
}

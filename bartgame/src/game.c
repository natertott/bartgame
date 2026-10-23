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
#include "game.h"

GameState gGame;

/* pending transition */
static u8 sNextArea, sNextCell, sNextSide;
static u8 sTransPhase;

static const char* const sKeyItemText[4] = {
    "",
    "You found the BLIGHTSEED BOMBS!|Dark seeds that burst. Set one with B beside a cracked wall.",
    "You found the GRAIL LAMP!|A flame that is not of this wood. Swing it with B to burn webs and light censers.",
    "You found the PETAL CLOAK!|Press B to leap. A chasm is only a breath wide.",
};

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
    for (i = 0; i < def->object_count; i++) {
        const u8* ob = &def->objects[i * 4];
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

/* ----------------------------------------------------------- states -- */
void game_init(void) {
    gGame.state = GS_PLAY;
    gGame.seed = 0xB4A7;
    world_generate(gGame.seed);
    player_new_game();
    load_sewer(0);
    fade_set(16);
    fade_start(0, 1);
    video_show(DCNT_BG0 | DCNT_BG1 | DCNT_BG2 | DCNT_OBJ);
}

static void draw_world(void) {
    player_draw();
    enemies_draw();
    npcs_draw();
    objects_draw();
    hud_draw();
}

static void update_play(void) {
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
            begin_transition(AREA_SEWER, 0, 0);
        }
        draw_world();
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
    draw_world();
}

static void update_transition(void) {
    draw_world();
    if (sTransPhase == 0) {
        if (!fade_done())
            return;
        if (sNextArea == AREA_SEWER)
            load_sewer(1);
        else
            load_forest(sNextCell, sNextSide);
        sTransPhase = 1;
        fade_start(0, 2);
        return;
    }
    if (fade_done())
        gGame.state = GS_PLAY;
}

void game_update(void) {
    gGame.run_frames++;
    switch (gGame.state) {
        case GS_PLAY: update_play(); break;
        case GS_TRANSITION: update_transition(); break;
        default: break;
    }
}

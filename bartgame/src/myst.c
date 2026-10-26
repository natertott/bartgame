/* BARTGAME: the mystery rooms. A cave, a hollow or a thicket of one of
   three sizes, built from the cell's mystery, holding one event:

     POTS      six pots, one holds a prize: lift or break them
     CHEST     a chest, plainly, with a prize by the room's size
     NPC       a stranger who sells a piece of heart for ten gilt
     FAIRY     a spring that fills the hearts
     WAVES     the way out shuts; two or three waves of monsters, then a chest
     SURVIVE   the way out shuts; monsters come for a while, then a chest
     MINIBOSS  the way out shuts; a knight captain and his beetles, then a chest
     SWITCHES  step on every stone plate, then a chest
     TORCHES   light every censer with the lamp, then a chest
     BOULDERS  lift every boulder (the gauntlet), then a chest

   The small rooms draw the quiet kinds and the gauntlets; the miniboss,
   the plates, the censers and the boulders need the floor of a medium or
   large room. Censers and boulders stand on grass, so they live in
   thickets. */
#include "gba.h"
#include "video.h"
#include "util.h"
#include "room.h"
#include "actor.h"
#include "player.h"
#include "sound.h"
#include "text.h"
#include "world.h"
#include "enemy.h"
#include "objects.h"
#include "npc.h"
#include "react.h"
#include "game.h"
#include "myst.h"

/* a style's tiles: its wall, the wall's face along the top and crown
   along the bottom, its floors, the floor's edges by the walls beside it
   (edge + bits - 1; 1 N, 2 E, 4 S, 8 W), its things and its spring */
typedef struct {
    u16 wall, face, crown, floor0, floor1, edge, prop, glow, exit, fsw, flift, fchest, spring;
} Style;
static const Style kStyle[3] = {
    { MT_CAVE_WALL, MT_CAVE_FACE, MT_CAVE_CROWN, MT_CAVE_FLOOR0, MT_CAVE_FLOOR1, MT_CAVE_EDGE_1, MT_CAVE_PROP, MT_CAVE_GLOW, MT_CAVE_EXIT,
      MT_CAVE_FLOOR_SWITCH, MT_CAVE_FLOOR_LIFT, MT_CAVE_FLOOR_CHEST, MT_CAVE_SPRING },
    { MT_HOLLOW_WALL, MT_HOLLOW_FACE, MT_HOLLOW_CROWN, MT_HOLLOW_FLOOR0, MT_HOLLOW_FLOOR1, MT_HOLLOW_EDGE_1, MT_HOLLOW_PROP, MT_HOLLOW_GLOW, MT_HOLLOW_EXIT,
      MT_HOLLOW_FLOOR_SWITCH, MT_HOLLOW_FLOOR_LIFT, MT_HOLLOW_FLOOR_CHEST, MT_HOLLOW_SPRING },
    { MT_THICKET_WALL, MT_THICKET_FACE, MT_THICKET_CROWN, MT_THICKET_FLOOR0, MT_THICKET_FLOOR1, MT_THICKET_EDGE_1, MT_THICKET_PROP, MT_THICKET_GLOW, MT_THICKET_EXIT,
      MT_THICKET_FLOOR_SWITCH, MT_THICKET_FLOOR_LIFT, MT_THICKET_FLOOR_CHEST, MT_THICKET_SPRING },
};
static const u8 kSize[3][2] = { { 12, 9 }, { 18, 12 }, { 24, 16 } };

static Rng sR;
static int sCell, sKind, sSize, sStyle, sW, sH;
static int sPhase, sTimer, sWave, sCount, sTotal;
static u8 sPrizeX, sPrizeY;
static u8 sDoorShut;

static int cx(void) { return sW / 2; }
static int cy(void) { return sH / 2; }
static u8 flags(void) { return gWorld.myst_flags[sCell]; }
bool8 myst_done(void) { return (flags() & MF_DONE) != 0; }
int myst_kind(void) { return sKind; }

/* the plain floor at (x, y): shaded toward the walls it lies beside */
static int edge_bits(int x, int y) {
    return (y == 2 ? 1 : 0) | (x == sW - 2 ? 2 : 0) | (y == sH - 2 ? 4 : 0) | (x == 1 ? 8 : 0);
}

u16 myst_ground(int x, int y) {
    const Style* st = &kStyle[sStyle];
    int b = edge_bits(x, y);
    return b ? st->edge + b - 1 : st->floor0;
}

static bool8 is_open_floor(int x, int y) {
    return x >= 1 && y >= 2 && x <= sW - 2 && y <= sH - 2 && room_type(x, y) == TT_FLOOR && room_get_overlay(x, y) == MT_NONE;
}

/* the lane from the way out up to the middle stays clear */
static bool8 in_lane(int x, int y) {
    return x >= cx() - 2 && x <= cx() + 1 && y >= sH - 4;
}

static void set_door(bool8 shut) {
    const Style* st = &kStyle[sStyle];
    sDoorShut = shut;
    room_change(cx() - 1, sH - 1, shut ? st->crown : st->exit);
    room_change(cx(), sH - 1, shut ? st->crown : st->exit);
}

static void place_chest(int x, int y, bool8 open) {
    const Style* st = &kStyle[sStyle];
    room_change(x, y, open ? myst_ground(x, y) : st->fchest);
    room_change_overlay(x, y, open ? MT_MYST_CHEST_OPEN : MT_MYST_CHEST);
}

void myst_build(int cell) {
    u8 m = gWorld.myst[cell];
    const Style* st;
    int x, y, i, n;
    bool8 done = (gWorld.myst_flags[cell] & MF_DONE) != 0;
    sCell = cell;
    sKind = MYST_KIND(m);
    sSize = MYST_SIZE(m);
    sStyle = MYST_STYLE(m);
    st = &kStyle[sStyle];
    sW = kSize[sSize][0];
    sH = kSize[sSize][1];
    rng_seed(&sR, hash32(gWorld.seed, cell * 131 + 7));
    sPhase = sTimer = sWave = sCount = sTotal = 0;
    room_clear(sW, sH, st->wall);
    for (y = 0; y < sH; y++)
        for (x = 0; x < sW; x++) {
            room_set_overlay(x, y, MT_NONE);
            if (x >= 1 && x <= sW - 2 && y >= 2 && y <= sH - 2)
                room_set(x, y, edge_bits(x, y) ? myst_ground(x, y) : (rng_range(&sR, 14) == 0) ? st->floor1 : st->floor0);
            else if (y == 1 && x >= 1 && x <= sW - 2)
                room_set(x, y, st->face);
            else if (y == sH - 1 && x >= 1 && x <= sW - 2)
                room_set(x, y, st->crown);
        }
    /* glowing things and solid things, off the lane and the middle */
    n = 4 + sSize * 3;
    for (i = 0; i < n * 6; i++) {
        x = 1 + rng_range(&sR, sW - 2);
        y = 2 + rng_range(&sR, sH - 3);
        if (!is_open_floor(x, y) || edge_bits(x, y) || in_lane(x, y) || (ABS(x - cx()) <= 2 && ABS(y - cy()) <= 2))
            continue;
        if (room_get(x, y) == st->glow || room_get(x, y) == st->prop)
            continue;
        room_set(x, y, (i & 1) ? st->glow : st->prop);
        if (--n == 0)
            break;
    }
    /* the event's furniture */
    switch (sKind) {
        case MK_POTS: {
            static const s8 at[6][2] = { { -3, -2 }, { 0, -2 }, { 3, -2 }, { -3, 2 }, { 0, 2 }, { 3, 2 } };
            int prize = rng_range(&sR, 6);
            for (i = 0; i < 6; i++) {
                x = cx() + at[i][0];
                y = cy() + at[i][1];
                if (x < 1 || x > sW - 2 || y < 2 || y > sH - 2)
                    continue;
                if (done) {
                    room_set(x, y, myst_ground(x, y));
                    continue;
                }
                room_set(x, y, st->flift);
                room_set_overlay(x, y, MT_MYST_POT);
                if (i == prize) {
                    sPrizeX = x;
                    sPrizeY = y;
                }
            }
            break;
        }
        case MK_CHEST:
            place_chest(cx(), cy(), done);
            break;
        case MK_FAIRY:
            room_set(cx(), cy(), st->spring);
            break;
        case MK_SWITCHES: {
            static const s8 at[4][2] = { { 3, 3 }, { -4, 3 }, { 3, -4 }, { -4, -4 } };
            sTotal = (sSize == MS_SMALL) ? 3 : 4;
            for (i = 0; i < sTotal; i++) {
                x = cx() + at[i][0];
                y = cy() + at[i][1];
                if (y < 2)
                    y = 2;
                room_set(x, y, done ? myst_ground(x, y) : st->fsw);
                room_set_overlay(x, y, done ? MT_MYST_SWITCH_DOWN : MT_MYST_SWITCH);
            }
            if (done)
                place_chest(cx(), cy(), TRUE);
            break;
        }
        case MK_TORCHES: {
            static const s8 at[3][2] = { { -4, 0 }, { 0, -3 }, { 4, 0 } };
            sTotal = 3;
            for (i = 0; i < 3; i++)
                room_set(cx() + at[i][0], cy() + at[i][1], done ? MT_TORCH_LIT : MT_TORCH);
            if (done)
                place_chest(cx(), cy() + 2, TRUE);
            break;
        }
        case MK_BOULDERS: {
            static const s8 at[4][2] = { { -4, -2 }, { 4, -2 }, { -4, 2 }, { 4, 2 } };
            sTotal = (sSize == MS_LARGE) ? 4 : 3;
            for (i = 0; i < sTotal; i++)
                if (!done)
                    room_set(cx() + at[i][0], cy() + at[i][1], MT_BOULDER);
            if (done)
                place_chest(cx(), cy(), TRUE);
            break;
        }
        case MK_WAVES:
        case MK_SURVIVE:
        case MK_MINIBOSS:
            if (done)
                place_chest(cx(), cy(), TRUE);
            break;
        default:
            break;
    }
    /* the way out, in the bottom wall; shut for a fight until it is won */
    set_door(!done && (sKind == MK_WAVES || sKind == MK_SURVIVE || sKind == MK_MINIBOSS));
    room_render();
}

void myst_start_pos(int* px, int* py) {
    *px = cx() * 16;
    *py = (sH - 2) * 16 + 12;
}

/* a monster on open floor, away from the hero */
static void spawn_one(int type) {
    int i;
    for (i = 0; i < 40; i++) {
        int x = 1 + rng_range(&sR, sW - 2), y = 2 + rng_range(&sR, sH - 3);
        int px = x * 16 + 8, py = y * 16 + 14;
        if (!is_open_floor(x, y) || in_lane(x, y))
            continue;
        if (ABS(px - PX(gPlayer->x)) < 40 && ABS(py - PX(gPlayer->y)) < 40)
            continue;
        {
            Actor* e = enemy_spawn(type, px, py);
            if (e)
                fx_spawn(FX_PUFF, px, py - 8);
        }
        return;
    }
}

static void spawn_wave(int n) {
    Cell* c = &gWorld.cells[sCell];
    int i;
    for (i = 0; i < n; i++)
        spawn_one(enemy_pick_type(c->theme, c->stage, hash32(gWorld.seed, sCell * 53 + sWave * 7 + i)));
}

static void finish(void) {
    sPhase = 9;
    set_door(FALSE);
    place_chest(cx(), (sKind == MK_TORCHES) ? cy() + 2 : cy(), FALSE);
    fx_spawn(FX_SPARK, cx() * 16 + 8, cy() * 16 + 8);
    sfx_play(SFX_SECRET);
}

void myst_enter(void) {
    gWorld.myst_flags[sCell] |= MF_SEEN;
    sPhase = 0;
    sTimer = 0;
    sWave = 0;
    sCount = 0;
    if (sKind == MK_NPC)
        npc_spawn(NPC_STRANGER, cx() * 16 + 8, cy() * 16 + 14);
    if (myst_done())
        sPhase = 9;
}

static int survive_limit(void) {
    return (sSize == MS_SMALL) ? 15 * 60 : (sSize == MS_MEDIUM) ? 20 * 60 : 25 * 60;
}

void myst_update(void) {
    Actor* a = gPlayer;
    int i;
    if (sPhase == 9) {
        /* the spring keeps giving */
        if (sKind == MK_FAIRY && room_get(PX(a->x) >> 4, (PX(a->y) - 4) >> 4) == kStyle[sStyle].spring && gPl.hp < gPl.hp_max && (gFrame & 15) == 0) {
            player_heal(2);
            if ((gFrame & 31) == 0)
                sfx_play(SFX_HEART);
        }
        return;
    }
    switch (sKind) {
        case MK_WAVES:
            if (sPhase == 0) {
                if (++sTimer > 40) {
                    spawn_wave(2 + sSize + (sWave > 0));
                    sPhase = 1;
                    sTimer = 0;
                }
            } else if (enemies_alive() == 0) {
                if (++sTimer > 45) {
                    sTimer = 0;
                    if (++sWave < 2 + (sSize == MS_LARGE))
                        spawn_wave(2 + sSize + sWave);
                    else
                        finish();
                }
            } else {
                sTimer = 0;
            }
            break;
        case MK_SURVIVE:
            sTimer++;
            if ((sTimer % 90) == 30 && enemies_alive() < 3 + sSize)
                spawn_wave(1);
            if (sTimer >= survive_limit()) {
                for (i = 1; i < ACTOR_MAX; i++)
                    if (gActors[i].kind == AK_ENEMY)
                        enemy_kill(&gActors[i]);
                finish();
            }
            break;
        case MK_MINIBOSS:
            if (sPhase == 0) {
                if (++sTimer > 40) {
                    Actor* k;
                    sPhase = 1;
                    spawn_one(EN_KNIGHT);
                    k = actor_find(AK_ENEMY, EN_KNIGHT);
                    if (k) {
                        k->hp = 20; /* twice a knight: ten sword hits */
                        k->damage = 4;
                    }
                    spawn_one(EN_BEETLE);
                    spawn_one(EN_BEETLE);
                }
            } else if (enemies_alive() == 0) {
                finish();
            }
            break;
        case MK_SWITCHES: {
            int tx = PX(a->x) >> 4, ty = (PX(a->y) - 4) >> 4;
            if (room_get_overlay(tx, ty) == MT_MYST_SWITCH) {
                room_change_overlay(tx, ty, MT_MYST_SWITCH_DOWN);
                room_change(tx, ty, myst_ground(tx, ty));
                sfx_play(SFX_BUMP);
                if (++sCount >= sTotal)
                    finish();
            }
            break;
        }
        case MK_TORCHES:
            if ((gFrame & 7) == 0 && room_torches_unlit() == 0)
                finish();
            break;
        case MK_FAIRY: {
            int tx = PX(a->x) >> 4, ty = (PX(a->y) - 4) >> 4;
            if (room_get(tx, ty) == kStyle[sStyle].spring && gPl.hp < gPl.hp_max) {
                player_heal(gPl.hp_max);
                sfx_play(SFX_HEART);
                fx_spawn(FX_SPARK, PX(a->x), PX(a->y) - 16);
                textbox_open("The water is kind. Every heart on the stalk beats full.");
                sPhase = 9;
            }
            break;
        }
        default:
            break;
    }
}

static void give_prize(void) {
    switch (sSize) {
        case MS_SMALL:
            gPl.gilt += 10;
            textbox_open("Ten gilt, dusty, and a hush in the dark.");
            break;
        case MS_MEDIUM:
            player_heart_piece();
            textbox_open("A PIECE OF HEART, warm in the cold. Four make a whole.");
            break;
        default:
            gPl.keys++;
            gPl.gilt += 20;
            textbox_open("A SMALL KEY, and twenty gilt beside it. Somewhere a lock remembers.");
            break;
    }
    if (gPl.gilt > 999)
        gPl.gilt = 999;
    gWorld.myst_flags[sCell] |= MF_DONE;
    sfx_play(SFX_CHEST);
}

void myst_chest_opened(int tx, int ty) {
    if (myst_done())
        return;
    room_change(tx, ty, myst_ground(tx, ty));
    room_change_overlay(tx, ty, MT_MYST_CHEST_OPEN);
    give_prize();
}

void myst_tile_cleared(int tx, int ty) {
    if (sPhase == 9 || myst_done())
        return;
    if (sKind == MK_POTS && tx == sPrizeX && ty == sPrizeY) {
        int px = tx * 16 + 8, py = ty * 16 + 12;
        pickup_spawn(PK_GILT_BIG, px, py);
        if (sSize >= MS_MEDIUM)
            pickup_spawn(PK_GILT_BIG, px + 8, py);
        pickup_spawn(PK_HEART, px - 8, py);
        gWorld.myst_flags[sCell] |= MF_DONE;
        sPhase = 9;
        sfx_play(SFX_SECRET);
    }
    if (sKind == MK_BOULDERS) {
        int x, y, left = 0;
        for (y = 0; y < sH; y++)
            for (x = 0; x < sW; x++)
                if (room_get(x, y) == MT_BOULDER)
                    left++;
        if (left == 0)
            finish();
    }
}

bool8 myst_stranger_trade(void) {
    if (myst_done() || gPl.gilt < 10)
        return FALSE;
    gPl.gilt -= 10;
    player_heart_piece();
    gWorld.myst_flags[sCell] |= MF_DONE;
    sfx_play(SFX_SECRET);
    return TRUE;
}

/* BARTGAME: projectiles, pickups, effects, bombs. All are actors. */
#include "gba.h"
#include "video.h"
#include "util.h"
#include "room.h"
#include "actor.h"
#include "player.h"
#include "sound.h"
#include "objects.h"
#include "enemy.h"
#include "react.h"
#include "game.h"
#include "world.h"

static u16 sItemsTile, sFxTile, sProjTile, sLiftTile;

static void ensure_sheets(void) {
    if (!sItemsTile)
        sItemsTile = sprite_load_sheet(SHEET_ITEMS);
    if (!sFxTile)
        sFxTile = sprite_load_sheet(SHEET_FX);
    if (!sProjTile)
        sProjTile = sprite_load_sheet(SHEET_PROJ);
    if (!sLiftTile)
        sLiftTile = sprite_load_sheet(SHEET_LIFT);
}

void objects_room_reset(void) {
    sItemsTile = sFxTile = sProjTile = sLiftTile = 0;
    ensure_sheets();
}

u16 lift_sheet_tile(void) {
    ensure_sheets();
    return sLiftTile;
}

u16 items_sheet_tile(void) {
    ensure_sheets();
    return sItemsTile;
}

/* ------------------------------------------------------- projectiles -- */
Actor* proj_spawn(int type, int px, int py, int dir, int speed, int damage, bool8 from_player) {
    ensure_sheets();
    Actor* a = actor_new(AK_PROJ, type, px, py);
    if (!a)
        return NULL;
    actor_set_sheet(a, SHEET_PROJ, sProjTile);
    a->frame = type == PJ_SEED ? F_PROJ_SEED : type == PJ_SPORE ? F_PROJ_SPORE : F_PROJ_SHARD;
    a->dir = dir;
    a->speed = speed;
    a->damage = damage;
    a->hitbox = HB_PROJ;
    a->flags = AF_FLYING | AF_PRIO1;
    a->timer = 0;
    a->v[0] = from_player;
    a->z = Q16(6);
    a->prio = 1;
    return a;
}

static void proj_update(Actor* a) {
    actor_move_free(a, a->speed, a->dir);
    int px = PX(a->x), py = PX(a->y);
    if (++a->timer > 150 || px < 0 || py < 0 || px > room_px_w() || py > room_px_h()) {
        actor_free(a);
        return;
    }
    if (a->type == PJ_SPORE)
        a->frame = F_PROJ_SPORE;
    /* walls stop seeds and shards; spores drift through canopy */
    if (a->type != PJ_SPORE && room_solid_px(px, py - 4)) {
        fx_spawn(FX_SPARK, px, py);
        actor_free(a);
        return;
    }
    if (!a->v[0]) {
        if (actors_overlap(a, gPlayer) && player_is_vulnerable()) {
            player_hurt(a->damage, a->dir);
            actor_free(a);
            return;
        }
        /* the sword knocks seeds away */
        int x0, y0, x1, y1;
        if (player_sword_box(&x0, &y0, &x1, &y1) && actor_box_overlap(a, x0, y0, x1, y1)) {
            fx_spawn(FX_CLANG, px, py);
            sfx_play(SFX_BUMP);
            actor_free(a);
            return;
        }
    }
}

/* ----------------------------------------------------------- pickups -- */
Actor* pickup_spawn(int type, int px, int py) {
    ensure_sheets();
    Actor* a = actor_new(AK_PICKUP, type, px, py);
    if (!a)
        return NULL;
    actor_set_sheet(a, SHEET_ITEMS, sItemsTile);
    static const u8 frames[] = { F_ITEMS_HEART, F_ITEMS_GILT, F_ITEMS_BOMB_PICKUP, F_ITEMS_GILT_BIG, F_ITEMS_KEY, F_ITEMS_RELIC, F_ITEMS_GRAIL };
    a->frame = frames[type];
    a->hitbox = HB_SMALL;
    a->timer = 0;
    a->z = Q16(8);
    a->zvel = Q16(1.0);
    a->prio = 2;
    return a;
}

static void pickup_update(Actor* a) {
    actor_gravity(a);
    if (a->timer < 255)
        a->timer++;
    /* floor drops fade after ten seconds; keys, relics and a placed
       hoard (v[2]) stay */
    if (a->type <= PK_GILT_BIG && !a->v[2]) {
        a->v[0]++;
        if (a->v[0] == 0)
            a->v[1]++;
        if (a->v[1] >= 3 && (gFrame & 2))
            a->flags |= AF_HIDDEN;
        else
            a->flags &= ~AF_HIDDEN;
        if (a->v[1] >= 4) {
            actor_free(a);
            return;
        }
    }
    if (a->timer > 6 && actors_overlap(a, gPlayer)) {
        switch (a->type) {
            case PK_HEART: player_heal(8); sfx_play(SFX_HEART); break;
            case PK_GILT: gPl.gilt += 1; sfx_play(SFX_PICKUP); break;
            case PK_GILT_BIG: gPl.gilt += 10; sfx_play(SFX_PICKUP); break;
            case PK_BOMB:
                if (gPl.items & ITEM_BOMBS) {
                    gPl.bombs += 3;
                    if (gPl.bombs > 30)
                        gPl.bombs = 30;
                }
                sfx_play(SFX_PICKUP);
                break;
            case PK_KEY: gPl.keys++; sfx_play(SFX_KEY); break;
            case PK_RELIC: gPl.items |= ITEM_RELIC; sfx_play(SFX_SECRET); break;
            case PK_GRAIL: game_win(); sfx_play(SFX_WIN); break;
        }
        if (gPl.gilt > 999)
            gPl.gilt = 999;
        if (a->v[2])
            gWorld.cells[gGame.cell].opened |= CELL_LOOTED;
        actor_free(a);
    }
}

void drop_roll(int px, int py, u32 roll) {
    int r = roll % 16;
    if (r < 4)
        pickup_spawn(PK_HEART, px, py);
    else if (r < 9)
        pickup_spawn(PK_GILT, px, py);
    else if (r < 10)
        pickup_spawn(PK_GILT_BIG, px, py);
    else if (r < 12 && (gPl.items & ITEM_BOMBS))
        pickup_spawn(PK_BOMB, px, py);
}

/* ----------------------------------------------------------- effects -- */
Actor* fx_spawn(int type, int px, int py) {
    ensure_sheets();
    Actor* a = actor_new(AK_FX, type, px, py);
    if (!a)
        return NULL;
    actor_set_sheet(a, SHEET_FX, sFxTile);
    a->timer = 0;
    a->prio = 1;
    a->flags = AF_FLYING | AF_NOSHADOW;
    switch (type) {
        case FX_PUFF: a->frame = F_FX_PUFF1; break;
        case FX_CLANG: a->frame = F_FX_CLANG; break;
        case FX_BLAST: a->frame = F_FX_BLAST1; a->hitbox = HB_BLAST; break;
        case FX_FLAME: a->frame = F_FX_FLAME1; a->hitbox = HB_MED; break;
        case FX_SPARK: a->frame = F_FX_PUFF1; break;
        case FX_FIREFLY:
            a->frame = F_FX_FIREFLY1;
            a->z = Q16(10);
            a->prio = 0;
            break;
        default: break;
    }
    a->y += Q16(8); /* effects sit on their center */
    return a;
}

static void fx_update(Actor* a) {
    int t = ++a->timer;
    switch (a->type) {
        case FX_PUFF:
            a->frame = t < 6 ? F_FX_PUFF1 : t < 12 ? F_FX_PUFF2 : F_FX_PUFF3;
            if (t >= 18)
                actor_free(a);
            break;
        case FX_SPARK:
            if (t >= 6)
                actor_free(a);
            break;
        case FX_CLANG:
            if (t >= 8)
                actor_free(a);
            break;
        case FX_BLAST:
            a->frame = t < 4 ? F_FX_BLAST1 : t < 12 ? F_FX_BLAST2 : F_FX_BLAST3;
            if (t >= 18)
                actor_free(a);
            break;
        case FX_FLAME:
            a->frame = (t & 4) ? F_FX_FLAME1 : F_FX_FLAME2;
            if (t >= 20)
                actor_free(a);
            break;
        case FX_FIREFLY: {
            /* a slow loop in the air, a glow that swells and goes dark */
            int ph = (gFrame + a->v[0] * 8) & 255;
            a->x += SIN(ph);
            a->y += SIN((ph * 2 + 64) & 255) >> 1;
            a->frame = ((gFrame + a->v[0] * 4) & 32) ? F_FX_FIREFLY1 : F_FX_FIREFLY2;
            if (((gFrame + a->v[0] * 8) & 127) < 24)
                a->flags |= AF_HIDDEN;
            else
                a->flags &= ~AF_HIDDEN;
            a->timer = 0;
            break;
        }
        default:
            actor_free(a);
            break;
    }
}

/* ------------------------------------------------------------- bombs -- */
/* TMC: 150 frames of fuse, then the blast. The last 80 frames flash. */
void bomb_place(int px, int py) {
    ensure_sheets();
    Actor* a = actor_new(AK_OBJECT, FX_BOMB_OBJ, px, py);
    if (!a)
        return;
    actor_set_sheet(a, SHEET_FX, sFxTile);
    a->frame = F_FX_BOMB1;
    a->timer = 0;
    a->timer2 = 0;
    a->prio = 2;
    a->hitbox = HB_SMALL;
    a->flags = AF_SOLID;
    sfx_play(SFX_BOMB_SET);
}

int bombs_live(void) {
    int i, n = 0;
    for (i = 1; i < ACTOR_MAX; i++)
        if (gActors[i].kind == AK_OBJECT && gActors[i].type == FX_BOMB_OBJ)
            n++;
    return n;
}

/* ------------------------------------------------------- thrown loads -- */
/* A bush, pot or stone thrown from over the head: 2.5 px a frame, falling
   from 24 px up, about three tiles. Breaks on the ground, on a wall or on
   a monster, which it hurts for 2 (a bush or pot) or 4 (a stone). */
Actor* thrown_spawn(int kind, int px, int py, int facing) {
    ensure_sheets();
    Actor* a = actor_new(AK_OBJECT, OBJ_THROWN, px, py);
    if (!a)
        return NULL;
    actor_set_sheet(a, SHEET_LIFT, sLiftTile);
    a->frame = kind - 1;
    a->dir = facing * 8;
    a->speed = Q8(2.5);
    a->z = Q16(24);
    a->zvel = Q16(0.5);
    a->damage = (kind == CARRY_ROCK || kind == CARRY_BOULDER) ? 4 : 2;
    a->hitbox = HB_SMALL;
    a->flags = AF_FLYING;
    a->prio = 1;
    a->v[0] = kind;
    a->timer = 0;
    return a;
}

static void thrown_break(Actor* a) {
    int px = PX(a->x), py = PX(a->y);
    fx_spawn(FX_PUFF, px, py - PX(a->z));
    sfx_play(SFX_BUMP);
    if ((a->v[0] == CARRY_BUSH || a->v[0] == CARRY_POT) && (hash32(gGame.run_frames, px) & 3) == 0)
        drop_roll(px, py, hash32(py, px));
    actor_free(a);
}

static void thrown_update(Actor* a) {
    int i;
    actor_move_free(a, a->speed, a->dir);
    a->z += a->zvel;
    a->zvel -= Q16(0.125);
    if (++a->timer > 120) {
        thrown_break(a);
        return;
    }
    int px = PX(a->x), py = PX(a->y);
    if (a->z <= 0 || px < 8 || py < 8 || px > room_px_w() - 8 || py > room_px_h() - 8 || (a->timer > 4 && room_solid_px(px, py - 4))) {
        a->z = 0;
        thrown_break(a);
        return;
    }
    for (i = 1; i < ACTOR_MAX; i++) {
        Actor* e = &gActors[i];
        if (e->kind != AK_ENEMY || !(e->flags & AF_HITTABLE) || e->iframes)
            continue;
        if (actors_overlap(a, e)) {
            enemy_hurt(e, a->damage, a->dir, Q8(1.5));
            thrown_break(a);
            return;
        }
    }
}

/* The blast: a 40x40 box. Hurts enemies for 8, the player for 4, and
   opens cracked walls whose tile touches the box. */
static void bomb_explode(Actor* a) {
    int px = PX(a->x), py = PX(a->y);
    int x0 = px - 20, y0 = py - 24, x1 = px + 20, y1 = py + 16;
    int i, tx, ty;
    Actor* fx = fx_spawn(FX_BLAST, px, py - 8);
    (void)fx;
    sfx_play(SFX_BOMB);
    for (i = 1; i < ACTOR_MAX; i++) {
        Actor* e = &gActors[i];
        if (e->kind != AK_ENEMY)
            continue;
        if (actor_box_overlap(e, x0, y0, x1, y1))
            enemy_hurt(e, 8, actor_dir_to(a, e), Q8(2.0));
    }
    if (actor_box_overlap(gPlayer, x0, y0, x1, y1))
        player_hurt(4, actor_dir_to(a, gPlayer));
    for (ty = (y0 >> 4); ty <= (y1 >> 4); ty++)
        for (tx = (x0 >> 4); tx <= (x1 >> 4); tx++) {
            if (room_type(tx, ty) == TT_CRACK)
                room_crack_open(tx, ty);
            else if (room_type(tx, ty) == TT_LIFT1)
                room_break_lift(tx, ty);
        }
    actor_free(a);
}

static void bomb_update(Actor* a) {
    a->timer2++;
    if (a->timer2 >= 150) {
        bomb_explode(a);
        return;
    }
    if (a->timer2 >= 70 && (a->timer2 & 4))
        a->frame = F_FX_BOMB2;
    else
        a->frame = F_FX_BOMB1;
}

/* ------------------------------------------------------------ update -- */
void objects_update(void) {
    int i;
    for (i = 1; i < ACTOR_MAX; i++) {
        Actor* a = &gActors[i];
        switch (a->kind) {
            case AK_PROJ: proj_update(a); break;
            case AK_PICKUP: pickup_update(a); break;
            case AK_FX: fx_update(a); break;
            case AK_OBJECT:
                if (a->type == OBJ_THROWN)
                    thrown_update(a);
                else
                    bomb_update(a);
                break;
            default: break;
        }
    }
}

void objects_draw(void) {
    int i;
    for (i = 1; i < ACTOR_MAX; i++) {
        Actor* a = &gActors[i];
        if (a->kind == AK_PROJ || a->kind == AK_PICKUP || a->kind == AK_FX || a->kind == AK_OBJECT)
            actor_draw(a);
    }
}

/* BARTGAME: the monsters of the Blighted Wood. Each AI is a port of a
   TMC behavior with its numbers (docs/newgame/data/enemies.csv and the
   feel traces): the rot beetle (Beetle), the spore bat (Keese), the blight
   spitter (Octorok: walk 30/60/60/90, pause 24..80, spit facing the
   player three times in four), the gloom slime (ChuChu), the thorn knight
   (Darknut: 0.375 px/f, 10 hp, no shield: it is hit from any side). The Blight Heart boss is
   its own file. */
#include "gba.h"
#include "video.h"
#include "util.h"
#include "room.h"
#include "actor.h"
#include "player.h"
#include "sound.h"
#include "objects.h"
#include "enemy.h"
#include "boss.h"
#include "game.h"

const EnemyDef gEnemyDefs[EN_COUNT] = {
    [EN_BEETLE] = { SHEET_BEETLE, 2, Q8(0.5), 2, HB_SMALL, AF_HITTABLE | AF_HURTS, 0 },
    [EN_BAT] = { SHEET_BAT, 2, Q8(1.0), 2, HB_SMALL, AF_HITTABLE | AF_HURTS | AF_FLYING | AF_PRIO1, 0 },
    [EN_SPITTER] = { SHEET_SPITTER, 2, Q8(0.375), 2, HB_MED, AF_HITTABLE | AF_HURTS, 1 },
    [EN_SLIME] = { SHEET_SLIME, 4, Q8(0.125), 2, HB_MED, AF_HITTABLE | AF_HURTS, 1 },
    [EN_KNIGHT] = { SHEET_KNIGHT, 10, Q8(0.375), 4, HB_TALL, AF_HITTABLE | AF_HURTS | AF_SOLID, 2 }, /* five sword hits */
    [EN_BOSS] = { SHEET_KNIGHT, 40, Q8(0.5), 4, HB_BIG, AF_HITTABLE | AF_HURTS | AF_BOSS, 2 },
};

static u16 sSheetTile[EN_COUNT];
static u16 sKswordTile;
u8 gEnemyPresentedFrame[ACTOR_MAX];

/* enemy states */
enum { ES_IDLE, ES_WALK, ES_CHASE, ES_PAUSE, ES_SPIT, ES_HOP, ES_WINDUP, ES_SWING, ES_RECOVER, ES_DIE, ES_REST, ES_FLY };

void enemy_load_sheets_for_theme(int theme) {
    int i;
    (void)theme;
    for (i = 0; i < EN_COUNT; i++)
        sSheetTile[i] = 0;
    sKswordTile = 0;
}

static void ensure_sheet(int type) {
#if BART_ENEMY_VARIANT
    /* The boss owns one streamed frame. Loading the unused knight sheet
       here would waste192 OBJ tiles before boss_spawn replaces it. */
    if (type == EN_BOSS)
        return;
#endif
    if (!sSheetTile[type])
        sSheetTile[type] = sprite_load_sheet(gEnemyDefs[type].sheet);
    if (type == EN_KNIGHT && !sKswordTile)
        sKswordTile = sprite_load_sheet(SHEET_KSWORD);
}

/* Which monsters a room gets: by theme, with heavier picks at higher stages. */
int enemy_pick_type(int theme, int stage, u32 roll) {
    int r = roll % 100;
    switch (theme) {
        case 0: /* bugs */
            if (stage >= 2 && r < 15) return EN_KNIGHT;
            return r < 55 ? EN_BEETLE : EN_BAT;
        case 1: /* blight */
            if (stage >= 2 && r < 12) return EN_KNIGHT;
            return r < 50 ? EN_SPITTER : r < 80 ? EN_SLIME : EN_BEETLE;
        case 2: /* dead */
            if (stage >= 1 && r < 25) return EN_KNIGHT;
            return r < 60 ? EN_BAT : EN_SLIME;
        default:
            if (stage >= 2 && r < 15) return EN_KNIGHT;
            return r < 30 ? EN_BEETLE : r < 55 ? EN_BAT : r < 80 ? EN_SPITTER : EN_SLIME;
    }
}

Actor* enemy_spawn(int type, int px, int py) {
    const EnemyDef* d = &gEnemyDefs[type];
    Actor* a;
    ensure_sheet(type);
    a = actor_new(AK_ENEMY, type, px, py);
    if (!a)
        return NULL;
    actor_set_sheet(a, d->sheet, sSheetTile[type]);
    a->hp = d->hp;
    a->speed = d->speed;
    a->damage = d->damage;
    a->hitbox = d->hitbox;
    a->flags = d->flags;
    a->prio = (d->flags & AF_PRIO1) ? 1 : 2;
    a->state = ES_IDLE;
    a->timer = 10 + rand_range(30);
    a->dir = rand_range(4) * 8;
    a->facing = dir_to_facing(a->dir);
    if (type == EN_BAT) {
        a->state = ES_REST;
        a->timer = 30 + rand_range(90);
        a->z = Q16(12);
    }
    return a;
}

int enemies_alive(void) {
    int i, n = 0;
    for (i = 1; i < ACTOR_MAX; i++)
        if (gActors[i].kind == AK_ENEMY && gActors[i].state != ES_DIE)
            n++;
    return n;
}

void enemy_kill(Actor* e) {
    gGame.kills++;
    fx_spawn(FX_PUFF, PX(e->x), PX(e->y) - 8);
    drop_roll(PX(e->x), PX(e->y), rand_next());
    sfx_play(SFX_KILL);
    if (e->flags & AF_BOSS)
        boss_died(e);
    actor_free(e);
}

void enemy_hurt(Actor* e, int damage, int from_dir, int knockback) {
    if (e->iframes)
        return;
    e->hp -= damage;
    e->iframes = 12;
    e->kb_dir = from_dir;
    e->kb_speed = knockback;
    e->kb_timer = 12;
    if (e->flags & AF_BOSS)
        sfx_play(SFX_BOSS_HIT);
    else
        sfx_play(SFX_HIT);
    if (e->hp <= 0) {
        if (e->flags & AF_BOSS) {
            boss_defeated(e);
            return;
        }
        enemy_kill(e);
    }
}

/* ------------------------------------------------------------ the AIs -- */
static int toward_player_dir(Actor* e) {
    return actor_dir_to(e, gPlayer);
}

static int toward_player_4(Actor* e) {
    int d = toward_player_dir(e);
    return ((d + 4) >> 3 & 3) * 8;
}

static void beetle_update(Actor* e) {
    int d2 = actor_dist2(e, gPlayer);
    switch (e->state) {
        case ES_IDLE:
            if (--e->timer == 0) {
                e->state = ES_WALK;
                e->timer = 30 + rand_range(40);
                e->dir = rand_range(32);
            }
            if (d2 < 80 * 80) {
                e->state = ES_CHASE;
                e->timer = 0;
            }
            break;
        case ES_WALK:
            actor_move(e, Q8(0.5), e->dir);
            if (e->coll) {
                e->dir = (e->dir + 12 + rand_range(8)) & 31;
            }
            if (--e->timer == 0) {
                e->state = ES_IDLE;
                e->timer = 10 + rand_range(30);
            }
            if (d2 < 80 * 80) {
                e->state = ES_CHASE;
                e->timer = 0;
            }
            break;
        case ES_CHASE:
            if ((e->timer & 7) == 0)
                e->dir = toward_player_dir(e);
            e->timer++;
            actor_move(e, Q8(1.0), e->dir);
            if (e->coll) {
                e->dir = (e->dir + 8) & 31;
            }
            if (d2 > 120 * 120) {
                e->state = ES_IDLE;
                e->timer = 20;
            }
            break;
    }
    e->facing = dir_to_facing(e->dir);
    /* animation: 2 frames, faster when chasing */
    int step = (gFrame >> (e->state == ES_CHASE ? 2 : 3)) & 1;
    if (e->facing == FACE_E || e->facing == FACE_W) {
        e->frame = step ? F_BEETLE_WALK_E2 : F_BEETLE_WALK_E1;
        e->hflip = (e->facing == FACE_W);
    } else {
        e->frame = step ? F_BEETLE_WALK_S2 : F_BEETLE_WALK_S1;
        e->hflip = 0;
    }
}

static void bat_update(Actor* e) {
    switch (e->state) {
        case ES_REST:
            e->frame = F_BAT_REST;
            if (--e->timer == 0) {
                e->state = ES_FLY;
                e->timer = 60 + rand_range(60);
                e->dir = toward_player_dir(e);
                e->v[0] = rand_range(32);
            }
            break;
        case ES_FLY: {
            /* wobble around the heading, re-aim at the player now and then */
            e->v[0] += 3;
            int wob = (SIN(e->v[0] * 8) * 4) >> 14;
            if ((e->timer & 15) == 0)
                e->dir = toward_player_dir(e);
            int d = (e->dir + wob) & 31;
            actor_move_free(e, Q8(1.0), d);
            /* keep inside the room */
            int px = PX(e->x), py = PX(e->y);
            if (px < 24 || px > room_px_w() - 24 || py < 40 || py > room_px_h() - 16) {
                e->dir = (e->dir + 16) & 31;
                e->x = CLAMP(px, 24, room_px_w() - 24) << 16;
                e->y = CLAMP(py, 40, room_px_h() - 16) << 16;
            }
            e->z = Q16(12) + ((SIN(gFrame * 6) * 4) >> 14 << 16);
            e->frame = (gFrame & 4) ? F_BAT_FLY1 : F_BAT_FLY2;
            if (--e->timer == 0) {
                e->state = ES_REST;
                e->timer = 40 + rand_range(80);
            }
            break;
        }
    }
}

/* The Octorok port. Walk 30/60/60/90 frames in a 4-way direction, pause
   24..80, and at a walk's end spit if facing the player, 3 in 4. */
static void spitter_update(Actor* e) {
    static const u8 walk_dur[4] = { 30, 60, 60, 90 };
    switch (e->state) {
        case ES_IDLE:
            if (--e->timer == 0) {
                e->state = ES_WALK;
                e->timer = walk_dur[rand_range(4)];
                /* turn: toward the player half the time, else random */
                e->dir = (rand_next() & 1) ? toward_player_4(e) : rand_range(4) * 8;
                e->facing = dir_to_facing(e->dir);
            }
            break;
        case ES_WALK:
            actor_move(e, Q8(0.375), e->dir);
            if (e->coll) {
                e->dir = (e->dir + 16) & 31;
                e->facing = dir_to_facing(e->dir);
            }
            if (--e->timer == 0) {
                int faces = (toward_player_4(e) == e->dir);
                if (faces && (rand_range(4) != 0)) {
                    e->state = ES_SPIT;
                    e->timer = 24;
                } else {
                    e->state = ES_IDLE;
                    e->timer = 24 + rand_range(57);
                }
            }
            break;
        case ES_SPIT:
            if (--e->timer == 12) {
                int px = PX(e->x), py = PX(e->y);
                switch (e->facing) {
                    case FACE_N: py -= 14; break;
                    case FACE_S: py += 2; break;
                    case FACE_E: px += 8; break;
                    default: px -= 8; break;
                }
                proj_spawn(PJ_SEED, px, py, e->dir, Q8(2.5), 2, FALSE);
                sfx_play(SFX_SPIT);
            }
            if (e->timer == 0) {
                e->state = ES_IDLE;
                e->timer = 24 + rand_range(57);
            }
            break;
    }
    /* frames by facing */
    int f = e->facing;
    int walking = (e->state == ES_WALK) && (gFrame & 8);
    int spitting = (e->state == ES_SPIT && e->timer < 18);
    if (f == FACE_N)
        e->frame = spitting ? F_SPITTER_SPIT_N : walking ? F_SPITTER_WALK_N : F_SPITTER_IDLE_N;
    else if (f == FACE_S)
        e->frame = spitting ? F_SPITTER_SPIT_S : walking ? F_SPITTER_WALK_S : F_SPITTER_IDLE_S;
    else
        e->frame = spitting ? F_SPITTER_SPIT_E : walking ? F_SPITTER_WALK_E : F_SPITTER_IDLE_E;
    e->hflip = (f == FACE_W);
}

static void slime_update(Actor* e) {
    int d2 = actor_dist2(e, gPlayer);
    switch (e->state) {
        case ES_IDLE:
            e->frame = F_SLIME_IDLE;
            if (--e->timer == 0) {
                e->state = ES_WALK;
                e->timer = 40 + rand_range(40);
                e->dir = rand_range(32);
            }
            if (d2 < 72 * 72) {
                e->state = ES_PAUSE;
                e->timer = 18;
            }
            break;
        case ES_WALK:
            e->frame = (gFrame & 16) ? F_SLIME_IDLE : F_SLIME_SQUASH;
            actor_move(e, Q8(0.125), e->dir);
            if (e->coll)
                e->dir = (e->dir + 16) & 31;
            if (--e->timer == 0) {
                e->state = ES_IDLE;
                e->timer = 30;
            }
            if (d2 < 72 * 72) {
                e->state = ES_PAUSE;
                e->timer = 18;
            }
            break;
        case ES_PAUSE:
            e->frame = F_SLIME_SQUASH;
            if (--e->timer == 0) {
                e->state = ES_HOP;
                e->dir = toward_player_dir(e);
                e->zvel = Q16(1.75);
                e->z = Q16(0.5);
            }
            break;
        case ES_HOP:
            e->frame = F_SLIME_JUMP;
            actor_move(e, Q8(1.25), e->dir);
            actor_gravity(e);
            if (e->z <= 0) {
                e->state = (d2 < 72 * 72) ? ES_PAUSE : ES_IDLE;
                e->timer = (e->state == ES_PAUSE) ? 24 : 30;
                e->frame = F_SLIME_SQUASH;
            }
            break;
    }
}

static void knight_update(Actor* e) {
    int d2 = actor_dist2(e, gPlayer);
    switch (e->state) {
        case ES_IDLE:
            if (--e->timer == 0) {
                e->state = ES_CHASE;
                e->timer = 0;
            }
            break;
        case ES_CHASE: {
            if ((e->timer & 15) == 0) {
                e->dir = toward_player_4(e);
                e->facing = dir_to_facing(e->dir);
            }
            e->timer++;
            actor_move(e, Q8(0.375), e->dir);
            if (e->coll && (e->timer & 15) != 0) {
                /* slide along: try the other axis toward the player */
                int d = toward_player_dir(e);
                e->dir = ((d + 4) >> 3 & 3) * 8;
                if (e->dir == e->facing * 8)
                    e->dir = (e->dir + 8) & 31;
            }
            /* in reach and roughly in front: attack */
            int dx = PX(gPlayer->x) - PX(e->x), dy = PX(gPlayer->y) - PX(e->y);
            int inreach = 0;
            switch (e->facing) {
                case FACE_N: inreach = dy < 0 && dy > -28 && ABS(dx) < 14; break;
                case FACE_S: inreach = dy > 0 && dy < 28 && ABS(dx) < 14; break;
                case FACE_E: inreach = dx > 0 && dx < 28 && ABS(dy) < 16; break;
                default: inreach = dx < 0 && dx > -28 && ABS(dy) < 16; break;
            }
            if (inreach && d2 < 32 * 32) {
                e->state = ES_WINDUP;
                e->timer = 16;
            }
            break;
        }
        case ES_WINDUP:
            if (--e->timer == 0) {
                e->state = ES_SWING;
                e->timer = 14;
                sfx_play(SFX_SWORD);
            }
            break;
        case ES_SWING: {
            /* the blade's box in front */
            int px = PX(e->x), py = PX(e->y) - 10;
            int x0, y0, x1, y1;
            switch (e->facing) {
                case FACE_N: x0 = px - 10; x1 = px + 10; y0 = py - 26; y1 = py - 6; break;
                case FACE_S: x0 = px - 10; x1 = px + 10; y0 = py + 2; y1 = py + 22; break;
                case FACE_E: x0 = px + 6; x1 = px + 26; y0 = py - 10; y1 = py + 10; break;
                default: x0 = px - 26; x1 = px - 6; y0 = py - 10; y1 = py + 10; break;
            }
            if (e->timer > 3 && e->timer < 12 && actor_box_overlap(gPlayer, x0, y0, x1, y1))
                player_hurt(4, facing_to_dir(e->facing));
            if (--e->timer == 0) {
                e->state = ES_RECOVER;
                e->timer = 24;
            }
            break;
        }
        case ES_RECOVER:
            if (--e->timer == 0) {
                e->state = ES_CHASE;
                e->timer = 0;
            }
            break;
    }
    int f = e->facing;
    int step = (gFrame >> 3) & 1;
    int attacking = (e->state == ES_WINDUP || e->state == ES_SWING);
    int walking = (e->state == ES_CHASE);
    if (f == FACE_N)
        e->frame = attacking ? F_KNIGHT_ATK_N : walking ? (step ? F_KNIGHT_WALK_N1 : F_KNIGHT_WALK_N2) : F_KNIGHT_IDLE_N;
    else if (f == FACE_S)
        e->frame = attacking ? F_KNIGHT_ATK_S : walking ? (step ? F_KNIGHT_WALK_S1 : F_KNIGHT_WALK_S2) : F_KNIGHT_IDLE_S;
    else
        e->frame = attacking ? F_KNIGHT_ATK_E : walking ? (step ? F_KNIGHT_WALK_E1 : F_KNIGHT_WALK_E2) : F_KNIGHT_IDLE_E;
    e->hflip = (f == FACE_W);
}

/* ------------------------------------------------------------ common -- */
static void enemy_common(Actor* e) {
    /* knockback overrides the AI's movement */
    if (e->kb_timer) {
        e->kb_timer--;
        if (e->flags & AF_FLYING)
            actor_move_free(e, e->kb_speed, e->kb_dir);
        else
            actor_move(e, e->kb_speed, e->kb_dir);
        return;
    }
    switch (e->type) {
        case EN_BEETLE: beetle_update(e); break;
        case EN_BAT: bat_update(e); break;
        case EN_SPITTER: spitter_update(e); break;
        case EN_SLIME: slime_update(e); break;
        case EN_KNIGHT: knight_update(e); break;
        case EN_BOSS: boss_update(e); break;
    }
}

void enemies_update(void) {
    int i;
    int sx0, sy0, sx1, sy1;
    bool8 sword = player_sword_box(&sx0, &sy0, &sx1, &sy1);
    for (i = 1; i < ACTOR_MAX; i++) {
        Actor* e = &gActors[i];
        if (e->kind != AK_ENEMY)
            continue;
        if (e->iframes)
            e->iframes--;
        enemy_common(e);
        if (e->kind != AK_ENEMY)
            continue; /* died in its update */
        /* the sword */
        if (sword && (e->flags & AF_HITTABLE) && !e->iframes && actor_box_overlap(e, sx0, sy0, sx1, sy1)) {
            int from = actor_dir_to(gPlayer, e);
            enemy_hurt(e, gPl.sword_dmg, from, Q8(1.5));
            if (e->kind != AK_ENEMY)
                continue;
        }
        /* contact: the hero is knocked back, and the biter recoils too
           (TMC: the enemy side of the matrix gets 1.0 px/f) */
        if ((e->flags & AF_HURTS) && player_is_vulnerable() && actors_overlap(e, gPlayer)) {
            player_hurt(e->damage, actor_dir_to(e, gPlayer));
            if (!(e->flags & AF_BOSS) && e->type != EN_KNIGHT) {
                e->kb_dir = actor_dir_to(gPlayer, e);
                e->kb_speed = Q8(1.0);
                e->kb_timer = 14;
            }
        }
        /* a solid enemy pushes the player out */
        if ((e->flags & AF_SOLID) && actors_overlap(e, gPlayer) && gPlayer->state != PS_HURT) {
            int d = actor_dir_to(e, gPlayer);
            actor_move(gPlayer, Q8(1.0), d);
        }
    }
}

static void knight_draw_sword(Actor* e) {
    if ((e->flags & AF_HIDDEN) || (e->iframes && (gFrame & 2)))
        return;
    static const s8 hand[4][2]={{5,-17},{7,-16},{4,-13},{-8,-16}};
    int px = PX(e->x) - gCamX, py = PX(e->y) - PX(e->z) - gCamY;
    int raised=e->state==ES_WINDUP, f=e->facing, hflip=f==FACE_W;
    int vertical=raised || f==FACE_N || f==FACE_S;
    int frame=vertical ? F_KSWORD_BLADE_S : F_KSWORD_BLADE_E;
    int vflip=vertical && (raised || f==FACE_N);
    int gx=vertical ? 8 : 2, gy=vertical ? 2 : 8;
    if(hflip)gx=15-gx;
    if(vflip)gy=15-gy;
    int sx=px+hand[f][0]-gx,sy=py+hand[f][1]-gy;
    int priority=room_prop_priority(PX(e->x),PX(e->y),PX(e->z),16,28,e->prio);
    int before=gOamCount;
    draw_sprite(sx, sy, SHEET_KSWORD, sKswordTile, frame, hflip, priority, sheets[SHEET_KSWORD].pal);
    if (vflip && gOamCount>before)
        gOam[gOamCount - 1].attr1 |= ATTR1_VFLIP;
}

static u8 enemy_presentation_frame(const Actor* e) {
#if BART_ENEMY_VARIANT
    int face = e->facing == FACE_N ? 0 : e->facing == FACE_S ? 2 : 1;
    if (e->type == EN_BEETLE && e->facing == FACE_N) {
        int step = (gFrame >> (e->state == ES_CHASE ? 2 : 3)) & 1;
        return step ? F_BEETLE_WALK_N2 : F_BEETLE_WALK_N1;
    }
    if (e->type == EN_BOSS)
        return boss_presentation_frame(e);
    if (e->type == EN_KNIGHT) {
        static const u8 poses[4][3] = {
            { F_KNIGHT_WINDUP_N, F_KNIGHT_WINDUP_E, F_KNIGHT_WINDUP_S },
            { F_KNIGHT_STRIKE_N, F_KNIGHT_STRIKE_E, F_KNIGHT_STRIKE_S },
            { F_KNIGHT_RECOVER_N, F_KNIGHT_RECOVER_E, F_KNIGHT_RECOVER_S },
            { F_KNIGHT_HURT_N, F_KNIGHT_HURT_E, F_KNIGHT_HURT_S }
        };
        if (e->iframes) return poses[3][face];
        if (e->state == ES_WINDUP) return poses[0][face];
        if (e->state == ES_SWING) return poses[1][face];
        if (e->state == ES_RECOVER) return poses[2][face];
    }
    if (e->type == EN_SPITTER && e->state == ES_SPIT && e->timer >= 18) {
        static const u8 charge[3] = { F_SPITTER_CHARGE_N, F_SPITTER_CHARGE_E, F_SPITTER_CHARGE_S };
        return charge[face];
    }
#endif
    return e->frame;
}

static void enemy_draw_body(Actor* e) {
    u8 ai_frame = e->frame;
    e->frame = enemy_presentation_frame(e);
    gEnemyPresentedFrame[e - gActors] = e->frame;
    if (e->type == EN_BOSS) boss_draw(e);
    else actor_draw(e);
    e->frame = ai_frame;
}

void enemies_draw(void) {
    int i;
    memset(gEnemyPresentedFrame, 255, sizeof(gEnemyPresentedFrame));
    for (i = 1; i < ACTOR_MAX; i++) {
        Actor* e = &gActors[i];
        if (e->kind != AK_ENEMY)
            continue;
        if (e->type == EN_KNIGHT && (e->state == ES_WINDUP || e->state == ES_SWING)) {
            if (e->facing == FACE_N) {
                enemy_draw_body(e);
                knight_draw_sword(e);
            } else {
                knight_draw_sword(e);
                enemy_draw_body(e);
            }
            continue;
        }
        enemy_draw_body(e);
    }
}

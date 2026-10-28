/* BARTGAME: the Blight Heart. The thing at the center of the wood.

   A swollen heart, drawn at native boss scale, 40 hp, in three moods:
     swollen  (hp > 26)  drifts toward the hero, bursts eight spores
     rotten   (hp > 12)  spawns rot beetles, spits aimed spore fans
     frantic  (hp <= 12) lunges, spores often
   It dies over two seconds of shaking and bursting, then drops the
   Grail. Picking that up ends the demo. */
#include "gba.h"
#include "video.h"
#include "util.h"
#include "room.h"
#include "actor.h"
#include "player.h"
#include "sound.h"
#include "objects.h"
#include "enemy.h"
#include "world.h"
#include "game.h"
#include "boss.h"

enum { BS_IDLE, BS_DRIFT, BS_BURST, BS_SPAWN, BS_LUNGE, BS_REST, BS_DIE };

static u16 sBossTile;
static u8 sDying;

void boss_spawn(int px, int py) {
    sBossTile = sprite_load_sheet(SHEET_BOSS);
    sDying = 0;
    Actor* e = enemy_spawn(EN_BOSS, px, py);
    if (!e)
        return;
    actor_set_sheet(e, SHEET_BOSS, sBossTile);
    e->hp = 40;
    e->hitbox = HB_HEART;
    e->flags = AF_HITTABLE | AF_HURTS | AF_BOSS | AF_FLYING;
    e->state = BS_IDLE;
    e->timer = 60;
    e->frame = F_BOSS_PULSE1;
    e->damage = 4;
    e->z = Q16(4);
    bgm_play(BGM_BOSS);
}

bool8 boss_is_dying(void) {
    return sDying;
}

static int mood(Actor* e) {
    return e->hp > 26 ? 0 : e->hp > 12 ? 1 : 2;
}

static void spore_ring(Actor* e, int n, int offset) {
    int i;
    for (i = 0; i < n; i++) {
        int d = (offset + i * (32 / n)) & 31;
        proj_spawn(PJ_SPORE, PX(e->x), PX(e->y) - 8, d, Q8(1.0), 2, FALSE);
    }
    sfx_play(SFX_SPIT);
}

static void spore_fan(Actor* e) {
    int d = actor_dir_to(e, gPlayer);
    proj_spawn(PJ_SPORE, PX(e->x), PX(e->y) - 8, d, Q8(1.5), 2, FALSE);
    proj_spawn(PJ_SPORE, PX(e->x), PX(e->y) - 8, (d + 3) & 31, Q8(1.25), 2, FALSE);
    proj_spawn(PJ_SPORE, PX(e->x), PX(e->y) - 8, (d + 29) & 31, Q8(1.25), 2, FALSE);
    sfx_play(SFX_SPIT);
}

/* Keep the heart over the arena floor: an ellipse of ground round the
   room's middle, a tile in from the trees. Outside it the heart is drawn
   back toward the middle a pixel a frame, so it slides along the rim. */
static void clamp_in_room(Actor* e) {
    int cx = room_px_w() / 2, cy = room_px_h() / 2 + 8;
    int rx = (room_px_w() / 2 - 80) >> 2, ry = (room_px_h() / 2 - 64) >> 2;
    int dx = (PX(e->x) - cx) >> 2, dy = (PX(e->y) - cy) >> 2;
    if (dx * dx * ry * ry + dy * dy * rx * rx > rx * rx * ry * ry) {
        if (dx > 0) e->x -= 1 << 16;
        if (dx < 0) e->x += 1 << 16;
        if (dy > 0) e->y -= 1 << 16;
        if (dy < 0) e->y += 1 << 16;
    }
}

void boss_update(Actor* e) {
    int m = mood(e);
    /* the pulse */
    e->z = Q16(4) + ((SIN(gFrame * 4) * 3) >> 14 << 16);
    e->frame = (gFrame & 16) ? F_BOSS_PULSE1 : F_BOSS_PULSE2;
    if (e->iframes)
        e->frame = F_BOSS_HURT;
    if (sDying) {
        e->state = BS_DIE;
        e->timer2++;
        e->x += ((gFrame & 2) ? 1 : -1) << 16;
        if ((e->timer2 & 7) == 0)
            fx_spawn(FX_PUFF, PX(e->x) - 12 + rand_range(24), PX(e->y) - 20 + rand_range(24));
        if ((e->timer2 & 15) == 0)
            sfx_play(SFX_BOSS_HIT);
        if (e->timer2 >= 120)
            boss_died(e);
        return;
    }
    switch (e->state) {
        case BS_IDLE:
            if (--e->timer == 0) {
                e->state = BS_DRIFT;
                e->timer = 90 - m * 20;
            }
            break;
        case BS_DRIFT:
            if ((gFrame & 7) == 0)
                e->dir = actor_dir_to(e, gPlayer);
            actor_move_free(e, Q8(0.25) + m * Q8(0.125), e->dir);
            clamp_in_room(e);
            if (--e->timer == 0) {
                if (m == 0) {
                    e->state = BS_BURST;
                    e->timer = 20;
                } else if (m == 1) {
                    e->state = (e->v[0]++ & 1) ? BS_SPAWN : BS_BURST;
                    e->timer = 20;
                } else {
                    e->state = BS_LUNGE;
                    e->timer = 40;
                    e->dir = actor_dir_to(e, gPlayer);
                }
            }
            break;
        case BS_BURST:
            if (--e->timer == 10) {
                if (m == 0)
                    spore_ring(e, 8, gFrame & 3);
                else
                    spore_fan(e);
            }
            if (e->timer == 0) {
                e->state = BS_REST;
                e->timer = 40 - m * 10;
            }
            break;
        case BS_SPAWN:
            if (--e->timer == 0) {
                if (enemies_alive() < 5) {
                    int i;
                    for (i = 0; i < 2; i++) {
                        Actor* b = enemy_spawn(EN_BEETLE, PX(e->x) - 20 + i * 40, PX(e->y) + 8);
                        if (b)
                            fx_spawn(FX_PUFF, PX(b->x), PX(b->y) - 8);
                    }
                    sfx_play(SFX_KILL);
                }
                e->state = BS_REST;
                e->timer = 50;
            }
            break;
        case BS_LUNGE:
            actor_move_free(e, Q8(1.75), e->dir);
            clamp_in_room(e);
            if (--e->timer == 0) {
                e->state = BS_BURST;
                e->timer = 20;
            }
            break;
        case BS_REST:
            if (--e->timer == 0) {
                e->state = BS_DRIFT;
                e->timer = 80 - m * 20;
            }
            break;
        default:
            break;
    }
}

void boss_draw(Actor* e) {
    actor_draw(e);
    /* a shadow of spores drifting under it: none; the heart glows on its own */
}

/* called when hp reaches 0: start dying */
void boss_defeated(Actor* e) {
    sDying = 1;
    e->state = BS_DIE;
    e->timer2 = 0;
    e->flags &= ~(AF_HURTS | AF_HITTABLE);
    bgm_stop();
    sfx_play(SFX_WIN);
}

/* after the death sequence: clear the cell, drop the Grail */
void boss_died(Actor* e) {
    int px = PX(e->x), py = PX(e->y);
    int i;
    gWorld.cells[gWorld.goal].flags |= CF_CLEARED;
    for (i = 0; i < 6; i++)
        fx_spawn(FX_BLAST, px - 24 + rand_range(48), py - 24 + rand_range(40));
    /* every beetle it spawned dies with it */
    for (i = 1; i < ACTOR_MAX; i++)
        if (gActors[i].kind == AK_ENEMY && &gActors[i] != e)
            enemy_kill(&gActors[i]);
    actor_free(e);
    pickup_spawn(PK_GRAIL, px, py + 8);
    sDying = 0;
}

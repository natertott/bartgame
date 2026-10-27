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

static u16 sItemsTile, sFxTile, sProjTile, sLiftTile, sArrowTile, sMouthTile, sPickTile, sIconTile;
#define ICON_CACHE_SLOTS 8
static u8 sIconFrame[ICON_CACHE_SLOTS], sIconAge[ICON_CACHE_SLOTS];
static u16 sIconWorldPal[256] ALIGN4;
static u8 sIconMenu;

static void icon32_invalidate(void) {
    memset(sIconFrame,0xFF,sizeof(sIconFrame));
    memset(sIconAge,0xFF,sizeof(sIconAge));
}

/* The paused bag can borrow actor palettes: none of those actors is drawn
   there. Retain the live colours (including portrait/orb animation), rather
   than rebuilding them from default ROM palettes when the bag closes. */
void icon32_menu_begin(void) {
    if (!sIconMenu)
        memcpy32(sIconWorldPal,gPalObj,sizeof(sIconWorldPal));
    sIconMenu=1;
    icon32_invalidate();
}

void icon32_menu_end(void) {
    if (sIconMenu) {
        memcpy32(gPalObj,sIconWorldPal,sizeof(sIconWorldPal));
        gPalDirty=1;
    }
    sIconMenu=0;
    icon32_invalidate();
}

static void ensure_sheets(void) {
    if (!sItemsTile)
        sItemsTile = sprite_load_sheet(SHEET_ITEMS);
    if (!sFxTile)
        sFxTile = sprite_load_sheet(SHEET_FX);
    if (!sProjTile)
        sProjTile = sprite_load_sheet(SHEET_PROJ);
    if (!sLiftTile)
        sLiftTile = sprite_load_sheet(SHEET_LIFT);
    if (!sPickTile)
        sPickTile = sprite_load_sheet(SHEET_PICK32);
}

/* The bag shows at most seven distinct 32px icons at once; the selected
   description reuses one of them. Keep eight frames rather than the whole
   sheet, leaving room for combat sprites after opening the bag. */
u16 icon32_frame_tile(int frame) {
    int i, slot = -1;
    const SpriteSheet* sh = &sheets[SHEET_ICON32];
    if (!sIconTile) {
        sIconTile = sprite_alloc(ICON_CACHE_SLOTS * sh->frame_tiles);
        if (!sIconTile)
            return 0;
    }
    for (i=0;i<ICON_CACHE_SLOTS;i++)
        if (sIconFrame[i] == frame) {
            slot=i;
            break;
        }
    if (slot < 0) {
        for (i=0;i<ICON_CACHE_SLOTS;i++) {
            if (sIconFrame[i] == 0xFF) {
                slot=i;
                break;
            }
            if (slot < 0 || sIconAge[i] > sIconAge[slot])
                slot=i;
        }
        const u16* pixels=sIconMenu?icon32_exact_tiles:sh->tiles;
        vram_queue(pixels + frame * sh->frame_tiles * 16,
                   OBJ_TILE(sIconTile + slot * sh->frame_tiles), sh->frame_tiles * 32);
        if (sIconMenu)
            pal_set_obj(slot,&icon32_exact_pal[frame*16]);
        sIconFrame[slot]=frame;
    }
    /* Maintain exact LRU ranks on hits as well as uploads. A page that
       mixes cached and new icons must not evict an icon already drawn in
       this frame; simple FIFO replacement does not guarantee that. */
    int age=sIconAge[slot];
    for (i=0;i<ICON_CACHE_SLOTS;i++)
        if (i!=slot && sIconFrame[i]!=0xFF && sIconAge[i]<age)
            sIconAge[i]++;
    sIconAge[slot]=0;
    return sIconTile + slot * sh->frame_tiles;
}

int icon32_frame_palette(int frame) {
    if (sIconMenu) {
        int i;
        /* Resolve before looking up the palette slot; callers may request
           the palette before or after requesting the cached tile base. */
        icon32_frame_tile(frame);
        for (i=0;i<ICON_CACHE_SLOTS;i++)
            if (sIconFrame[i]==frame)
                return i;
    }
    return icon32_frame_pal[frame];
}

void objects_room_reset(void) {
    sItemsTile = sFxTile = sProjTile = sLiftTile = sArrowTile = sMouthTile = sPickTile = sIconTile = 0;
    icon32_menu_end();
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
    if (type == PJ_ARROW) {
        if (!sArrowTile)
            sArrowTile = sprite_load_sheet(SHEET_ARROW);
        actor_set_sheet(a, SHEET_ARROW, sArrowTile);
        a->frame = dir == DIR_N ? F_ARROW_N : dir == DIR_S ? F_ARROW_S : F_ARROW_E;
        a->hflip = (dir == DIR_W);
    } else {
        actor_set_sheet(a, SHEET_PROJ, sProjTile);
        a->frame = type == PJ_SEED ? F_PROJ_SEED : type == PJ_SPORE ? F_PROJ_SPORE : F_PROJ_SHARD;
    }
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
        /* the sword turns seeds and spores back the way the hero faces,
           his now; a shard it only breaks */
        int x0, y0, x1, y1;
        if (player_sword_box(&x0, &y0, &x1, &y1) && actor_box_overlap(a, x0, y0, x1, y1)) {
            fx_spawn(FX_CLANG, px, py);
            sfx_play(SFX_BUMP);
            if (a->type == PJ_SHARD) {
                actor_free(a);
                return;
            }
            a->dir = facing_to_dir(gPlayer->facing);
            a->speed = Q8(3.0);
            a->v[0] = 1;
            a->timer = 0;
        }
    } else {
        /* the hero's: it hurts the first monster it meets */
        int i;
        for (i = 1; i < ACTOR_MAX; i++) {
            Actor* e = &gActors[i];
            if (e->kind != AK_ENEMY || !(e->flags & AF_HITTABLE) || e->iframes)
                continue;
            if (actors_overlap(a, e)) {
                enemy_hurt(e, a->damage, a->dir, Q8(1.5));
                fx_spawn(FX_SPARK, px, py);
                actor_free(a);
                return;
            }
        }
    }
}

/* ----------------------------------------------------------- pickups -- */
Actor* pickup_spawn(int type, int px, int py) {
    ensure_sheets();
    Actor* a = actor_new(AK_PICKUP, type, px, py);
    if (!a)
        return NULL;
    actor_set_sheet(a, SHEET_PICK32, sPickTile);
    static const u8 frames[] = { F_PICK32_HEART, F_PICK32_GILT, F_PICK32_BOMB_PICKUP, F_PICK32_GILT_BIG, F_PICK32_KEY, F_PICK32_RELIC, F_PICK32_GRAIL,
                                 F_PICK32_ARROW1, F_PICK32_ARROW5, F_PICK32_ARROW10 };
    a->frame = frames[type];
    a->pal = pick32_frame_pal[a->frame];
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
    if ((a->type <= PK_GILT_BIG || a->type >= PK_ARROW1) && !a->v[2]) {
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
    /* the hero gathers it by touch, or with a sword swing that reaches it */
    int sx0, sy0, sx1, sy1;
    bool8 reached = actors_overlap(a, gPlayer) ||
                    (player_sword_box(&sx0, &sy0, &sx1, &sy1) && actor_box_overlap(a, sx0, sy0, sx1, sy1));
    if (a->timer > 6 && reached) {
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
            case PK_RELIC:
                gPl.items |= ITEM_RELIC;
                if (gGame.area == AREA_FOREST && gWorld.cells[gGame.cell].role == ROLE_RELIC)
                    gWorld.cells[gGame.cell].flags |= CF_RELIC_TAKEN;
                sfx_play(SFX_SECRET);
                break;
            case PK_GRAIL: game_win(); sfx_play(SFX_WIN); break;
            case PK_ARROW1: gPl.arrows += 1; sfx_play(SFX_PICKUP); break;
            case PK_ARROW5: gPl.arrows += 5; sfx_play(SFX_PICKUP); break;
            case PK_ARROW10: gPl.arrows += 10; sfx_play(SFX_PICKUP); break;
        }
        if (gPl.arrows > 50)
            gPl.arrows = 50;
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
    /* with the bow, the dead drop arrows: one often, five sometimes, ten rarely */
    else if (r >= 12 && (gPl.items2 & ITEM2_BOW))
        pickup_spawn(r < 14 ? PK_ARROW1 : r < 15 ? PK_ARROW5 : PK_ARROW10, px, py);
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
        case FX_FLAME:
            a->frame = F_FX_FLAME1;
            a->hitbox = HB_MED;
            /* Lamp fire shares the held tool's near/far presentation.
               Its direction is visual; the existing burn box stays fixed. */
            a->dir = facing_to_dir(gPlayer->facing);
            break;
        case FX_SPARK: a->frame = F_FX_PUFF1; break;
        case FX_FIREFLY:
            a->frame = F_FX_FIREFLY1;
            a->z = Q16(10);
            a->prio = 0;
            break;
        case FX_MOUTH:
            /* 32x32, on the ground under the hero's feet, drawn after him
               so it lies beneath */
            if (!sMouthTile)
                sMouthTile = sprite_load_sheet(SHEET_MOUTH);
            actor_set_sheet(a, SHEET_MOUTH, sMouthTile);
            a->frame = F_MOUTH_M1;
            a->prio = 2;
            a->y += Q16(8);
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
        case FX_MOUTH:
            a->frame = t < 10 ? F_MOUTH_M1 : t < 26 ? F_MOUTH_M2 : F_MOUTH_M3;
            if (t == 26)
                sfx_play(SFX_KILL);
            if (t >= 60)
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
    actor_set_sheet(a, SHEET_ITEMS, sItemsTile);
    a->frame = F_ITEMS_BOMBS;
    a->pal = items_frame_pal[a->frame];
    a->timer = 0;
    a->timer2 = 0;
    a->dir = facing_to_dir(gPlayer->facing); /* retain release-side depth through turns */
    a->prio = 2;
    a->hitbox = HB_SMALL;
    a->flags = AF_SOLID;
    /* Store the release point for an eight-frame hand-to-ground motion.
       Physics and the 150-frame fuse still start at the planted location. */
    static const s8 hand[4][2] = { {7,-10}, {10,-7}, {7,-3}, {-10,-7} };
    a->vx = PX(gPlayer->x)+hand[gPlayer->facing][0];
    a->vy = PX(gPlayer->y)+hand[gPlayer->facing][1];
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
        a->frame = F_ITEMS_BOMB_LIT;
    else
        a->frame = F_ITEMS_BOMBS;
    a->pal = items_frame_pal[a->frame];
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

static bool8 player_hand_composite(void) {
    return !(gPlayer->flags & AF_HIDDEN) && gPlayer->state != PS_FALL &&
           !(gPlayer->state == PS_DEAD && gPl.dead_timer > 60 && (gPl.dead_timer & 4));
}

/* A released load, player arrow or lamp flame keeps its hand-side depth while its
   visual rectangle still intersects Bloom. Physics and travel are wholly
   independent of this short composite stage. */
static bool8 player_release_overlap(Actor* a) {
    if ((a->kind != AK_OBJECT || a->type != OBJ_THROWN) &&
        (a->kind != AK_PROJ || a->type != PJ_ARROW || !a->v[0]) &&
        (a->kind != AK_FX || a->type != FX_FLAME))
        return FALSE;
    if (!player_hand_composite())
        return FALSE;
    int ax = PX(a->x) - a->w / 2;
    int ay = PX(a->y) - a->h - PX(a->z);
    int px = PX(gPlayer->x) - gPlayer->w / 2;
    int py = PX(gPlayer->y) - gPlayer->h - PX(gPlayer->z);
    return ax < px + gPlayer->w && ax + a->w > px &&
           ay < py + gPlayer->h && ay + a->h > py;
}

/* The released bomb is the actual object, ordered around Bloom with the
   other held tools. North is on the far side; every part uses this frame's
   resolved terrain priority. Once planted it joins ground props. */
void objects_draw_hand(bool8 behind) {
    int i;
    for (i=1;i<ACTOR_MAX;i++) {
        Actor* a=&gActors[i];
        if (player_release_overlap(a)) {
            if ((a->dir == DIR_N) == behind) {
                int sx = PX(a->x) - a->w / 2 - gCamX;
                int sy = PX(a->y) - a->h - PX(a->z) - gCamY;
                draw_sprite(sx, sy, a->sheet, a->tile, a->frame,
                            a->hflip, gPlayer->prio, a->pal);
            }
            continue;
        }
        if (a->kind!=AK_OBJECT || a->type!=FX_BOMB_OBJ || a->timer2>=8)
            continue;
        if (!player_hand_composite())
            continue;
        if ((a->dir == DIR_N) != behind)
            continue;
        int t=a->timer2;
        int x=(a->vx*(8-t)+PX(a->x)*t)/8;
        int y=(a->vy*(8-t)+PX(a->y)*t)/8;
        draw_sprite(x-a->w/2-gCamX,y-a->h-gCamY,a->sheet,a->tile,a->frame,0,gPlayer->prio,a->pal);
    }
}

void objects_draw(void) {
    int i;
    for (i = 1; i < ACTOR_MAX; i++) {
        Actor* a = &gActors[i];
        if (player_release_overlap(a))
            continue;
        if (a->kind==AK_OBJECT && a->type==FX_BOMB_OBJ && a->timer2<8 && player_hand_composite())
            continue;
        if (a->kind == AK_PROJ || a->kind == AK_PICKUP || a->kind == AK_FX || a->kind == AK_OBJECT)
            actor_draw(a);
    }
}

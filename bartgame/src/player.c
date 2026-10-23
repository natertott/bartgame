/* BARTGAME: the player. Bart, half man half plant, moves like Link.

   Constants are TMC's (docs/newgame/12_FROM_SCRATCH_ENGINE.md):
     walk 1.25 px/f, roll 24 frames (3.0, then 2.0, ramping back to 3.0),
     sword 15 frames, knockback 1.5 px/f for 8 frames with 30 iframes,
     gravity 0.125 px/f^2, cape jump zvel 2.0, pit fall costs 2. */
#include "gba.h"
#include "video.h"
#include "room.h"
#include "actor.h"
#include "player.h"
#include "sound.h"

Actor* gPlayer;
PlayerState gPl;

#define WALK_SPEED Q8(1.25)
#define ROLL_FRAMES 24
#define ATTACK_FRAMES 15
#define HURT_FRAMES 8
#define FALL_FRAMES 36
#define HERO_TILE 0
#define SWORD_TILE 8

static u8 sLastFrame = 0xFF;
static u8 sWalkTimer;

static void hero_set_frame(int frame) {
    if (frame == sLastFrame)
        return;
    sLastFrame = frame;
    const SpriteSheet* sh = &sheets[SHEET_HERO];
    vram_queue(sh->tiles + frame * sh->frame_tiles * 16, OBJ_TILE(HERO_TILE), sh->frame_tiles * 32);
}

void player_new_game(void) {
    memset(&gPl, 0, sizeof(gPl));
    gPl.hp_max = 24;
    gPl.hp = 24;
    gPl.items = ITEM_SWORD;
    gPl.sword_dmg = 2;
    gPl.bitem = BITEM_NONE;
}

void player_init(int px, int py, int facing) {
    Actor* a = &gActors[0];
    memset(a, 0, sizeof(*a));
    gPlayer = a;
    a->kind = AK_PLAYER;
    a->hitbox = HB_HERO;
    a->prio = 2;
    a->x = px << 16;
    a->y = py << 16;
    a->facing = facing;
    a->dir = facing_to_dir(facing);
    a->w = 16;
    a->h = 32;
    a->pal = PAL_OBJ_HERO;
    a->sheet = SHEET_HERO;
    a->tile = HERO_TILE;
    a->state = PS_NORMAL;
    gPl.safe_x = px;
    gPl.safe_y = py;
    sLastFrame = 0xFF;
    /* the sword blade sheet stays resident in tiles 8..19 */
    dma3_copy32(sheets[SHEET_SWORD].tiles, OBJ_TILE(SWORD_TILE), sheets[SHEET_SWORD].tile_count * 32);
}

void player_set_pos(int px, int py) {
    gPlayer->x = px << 16;
    gPlayer->y = py << 16;
    gPl.safe_x = px;
    gPl.safe_y = py;
}

void player_face(int facing) {
    gPlayer->facing = facing;
    gPlayer->dir = facing_to_dir(facing);
}

bool8 player_is_vulnerable(void) {
    Actor* a = gPlayer;
    if (a->iframes)
        return FALSE;
    if (a->state == PS_ROLL && a->timer < 18)
        return FALSE;
    if (a->state == PS_HURT || a->state == PS_FALL || a->state == PS_DEAD || a->state == PS_ITEMGET)
        return FALSE;
    return TRUE;
}

void player_hurt(int damage, int from_dir) {
    Actor* a = gPlayer;
    if (!player_is_vulnerable())
        return;
    gPl.hp -= damage;
    if (gPl.hp < 0)
        gPl.hp = 0;
    a->state = PS_HURT;
    a->timer = HURT_FRAMES;
    a->kb_dir = from_dir;
    a->kb_speed = Q8(1.5);
    a->iframes = 30;
    gPl.sword_active = 0;
    gPl.lamp_timer = 0;
    sfx_play(SFX_HURT);
    if (gPl.hp == 0) {
        a->state = PS_DEAD;
        a->timer = 0;
        gPl.dead_timer = 0;
    }
}

void player_heal(int amount) {
    gPl.hp += amount;
    if (gPl.hp > gPl.hp_max)
        gPl.hp = gPl.hp_max;
}

void player_item_get(int item_bit, int sprite_frame) {
    Actor* a = gPlayer;
    gPl.items |= item_bit;
    gPl.got_item = sprite_frame;
    gPl.got_timer = 0;
    a->state = PS_ITEMGET;
    a->timer = 0;
    a->facing = FACE_S;
    if (item_bit == ITEM_BOMBS && gPl.bitem == BITEM_NONE)
        gPl.bitem = BITEM_BOMBS;
    if (item_bit == ITEM_LAMP && gPl.bitem == BITEM_NONE)
        gPl.bitem = BITEM_LAMP;
    if (item_bit == ITEM_CLOAK && gPl.bitem == BITEM_NONE)
        gPl.bitem = BITEM_CLOAK;
    sfx_play(SFX_ITEM);
}

/* The sword's hit box: a box in front covering the swing's arc. */
bool8 player_sword_box(int* x0, int* y0, int* x1, int* y1) {
    if (!gPl.sword_active)
        return FALSE;
    Actor* a = gPlayer;
    int px = PX(a->x), py = PX(a->y) - 8;
    switch (a->facing) {
        case FACE_N: *x0 = px - 14; *x1 = px + 13; *y0 = py - 24; *y1 = py - 4; break;
        case FACE_S: *x0 = px - 14; *x1 = px + 13; *y0 = py + 2; *y1 = py + 20; break;
        case FACE_E: *x0 = px + 4; *x1 = px + 22; *y0 = py - 14; *y1 = py + 10; break;
        default: *x0 = px - 23; *x1 = px - 5; *y0 = py - 14; *y1 = py + 10; break;
    }
    return TRUE;
}

bool8 player_lamp_box(int* x0, int* y0, int* x1, int* y1) {
    if (!gPl.lamp_timer)
        return FALSE;
    Actor* a = gPlayer;
    int px = PX(a->x), py = PX(a->y) - 8;
    switch (a->facing) {
        case FACE_N: *x0 = px - 8; *x1 = px + 7; *y0 = py - 22; *y1 = py - 6; break;
        case FACE_S: *x0 = px - 8; *x1 = px + 7; *y0 = py + 4; *y1 = py + 20; break;
        case FACE_E: *x0 = px + 6; *x1 = px + 22; *y0 = py - 10; *y1 = py + 6; break;
        default: *x0 = px - 23; *x1 = px - 7; *y0 = py - 10; *y1 = py + 6; break;
    }
    return TRUE;
}

static int input_dir(void) {
    u16 k = gKeysHeld;
    int h = (k & KEY_RIGHT) ? 1 : (k & KEY_LEFT) ? -1 : 0;
    int v = (k & KEY_DOWN) ? 1 : (k & KEY_UP) ? -1 : 0;
    if (!h && !v)
        return DIR_NONE;
    if (h == 0)
        return v < 0 ? DIR_N : DIR_S;
    if (v == 0)
        return h > 0 ? DIR_E : DIR_W;
    if (v < 0)
        return h > 0 ? 4 : 28;
    return h > 0 ? 12 : 20;
}

/* Which way a dir leans for the sprite's facing, keeping the current
   facing when it is one of the two diagonal components (TMC keeps facing
   on diagonals when possible). */
static int facing_from_dir(int dir, int cur) {
    if ((dir & 7) == 0)
        return dir >> 3;
    /* diagonal: keep current if it is a component */
    int a = (dir - 4) >> 3, b = ((dir + 4) >> 3) & 3;
    if (cur == a || cur == b)
        return cur;
    return a & 3;
}

static void remember_safe_spot(void) {
    Actor* a = gPlayer;
    int px = PX(a->x), py = PX(a->y);
    u8 t = room_type_px(px, py - 4);
    if (t == TT_FLOOR || t == TT_SLOW || t == TT_DOOR_OPEN) {
        /* not next to a pit */
        if (room_type_px(px - 8, py - 4) != TT_PIT && room_type_px(px + 8, py - 4) != TT_PIT &&
            room_type_px(px, py - 12) != TT_PIT && room_type_px(px, py + 4) != TT_PIT &&
            room_type_px(px - 8, py - 4) != TT_WATER && room_type_px(px + 8, py - 4) != TT_WATER &&
            room_type_px(px, py - 12) != TT_WATER && room_type_px(px, py + 4) != TT_WATER) {
            if (++gPl.safe_timer >= 8) {
                gPl.safe_timer = 0;
                gPl.safe_x = px;
                gPl.safe_y = py;
            }
        }
    }
}

/* Ledge check: the tile the feet are walking into. Returns the ledge's
   drop direction if the player is pushing into it the right way. */
static int ledge_ahead(int dir) {
    Actor* a = gPlayer;
    if ((dir & 7) != 0)
        return -1;
    int px = PX(a->x), py = PX(a->y) - 6;
    int tx = px, ty = py;
    switch (dir) {
        case DIR_N: ty = py - 8; break;
        case DIR_S: ty = py + 8; break;
        case DIR_E: tx = px + 8; break;
        case DIR_W: tx = px - 8; break;
    }
    u8 t = room_type_px(tx, ty);
    if (t == TT_LEDGE_N && dir == DIR_N) return DIR_N;
    if (t == TT_LEDGE_S && dir == DIR_S) return DIR_S;
    if (t == TT_LEDGE_E && dir == DIR_E) return DIR_E;
    if (t == TT_LEDGE_W && dir == DIR_W) return DIR_W;
    return -1;
}

static void start_jump(int dir, int forward_speed, s32 zvel) {
    Actor* a = gPlayer;
    a->state = PS_JUMP;
    a->dir = dir;
    a->facing = dir_to_facing(dir);
    a->speed = forward_speed;
    a->zvel = zvel;
    a->z = Q16(0.5);
    a->timer = 0;
    gPl.sword_active = 0;
}

static void start_fall(void) {
    Actor* a = gPlayer;
    a->state = PS_FALL;
    a->timer = FALL_FRAMES;
    gPl.sword_active = 0;
    sfx_play(SFX_FALL);
}

static void check_floor(void) {
    Actor* a = gPlayer;
    if (a->z > 0)
        return;
    u8 t = room_type_px(PX(a->x), PX(a->y) - 4);
    if (t == TT_PIT || t == TT_WATER) {
        /* only when the feet center is well inside the tile */
        int fx = PX(a->x) & 15, fy = (PX(a->y) - 4) & 15;
        if (fx >= 3 && fx <= 12 && fy >= 3 && fy <= 12) {
            start_fall();
            return;
        }
    }
    if (t == TT_HURT && (gFrame & 31) == 0)
        player_hurt(2, (a->dir + 16) & 31);
    remember_safe_spot();
}

static void state_normal(void) {
    Actor* a = gPlayer;
    int dir = input_dir();
    if (gPl.item_cooldown)
        gPl.item_cooldown--;

    /* attack */
    if ((gKeysDown & KEY_A) || gPl.queued_attack) {
        gPl.queued_attack = 0;
        a->state = PS_ATTACK;
        a->timer = 0;
        gPl.sword_phase = 0;
        gPl.sword_active = 1;
        a->speed = 0;
        if (dir != DIR_NONE)
            a->facing = facing_from_dir(dir, a->facing);
        sfx_play(SFX_SWORD);
        return;
    }
    /* roll */
    if ((gKeysDown & KEY_R) && dir != DIR_NONE) {
        a->state = PS_ROLL;
        a->timer = 0;
        a->dir = (a->facing * 8);
        if ((dir & 7) == 0)
            a->dir = dir;
        a->facing = dir_to_facing(a->dir);
        sfx_play(SFX_ROLL);
        return;
    }
    if (dir == DIR_NONE) {
        a->speed = 0;
        gPl.push_timer = 0;
        sWalkTimer = 0;
    } else {
        a->facing = facing_from_dir(dir, a->facing);
        a->dir = dir;
        int ledge = ledge_ahead(dir);
        if (ledge >= 0) {
            if (++gPl.push_timer > 5) {
                gPl.push_timer = 0;
                start_jump(ledge, Q8(1.0), Q16(1.625));
                a->sub = 1; /* a ledge drop passes the ledge tile itself */
                sfx_play(SFX_JUMP);
                return;
            }
        } else {
            gPl.push_timer = 0;
        }
        a->speed = WALK_SPEED;
        actor_move(a, a->speed, dir);
        sWalkTimer++;
    }
    check_floor();
}

static void state_roll(void) {
    Actor* a = gPlayer;
    int t = a->timer;
    int speed;
    if (t == 0)
        speed = Q8(3.0);
    else if (t < 16)
        speed = Q8(2.0);
    else
        speed = Q8(2.0) + Q8(0.125) * (t - 15);
    a->speed = speed;
    actor_move(a, speed, a->dir);
    if (a->coll) {
        /* bounce off the wall: TMC's bounce, briefly */
        a->state = PS_NORMAL;
        a->timer = 0;
        a->kb_dir = (a->dir + 16) & 31;
        a->kb_speed = Q8(1.0);
        a->kb_timer = 6;
        a->zvel = Q16(1.0);
        a->z = Q16(0.5);
        sfx_play(SFX_BUMP);
        return;
    }
    if ((gKeysDown & KEY_A) && t >= 18)
        gPl.queued_attack = 1;
    if (++a->timer >= ROLL_FRAMES) {
        a->state = PS_NORMAL;
        a->timer = 0;
    }
    check_floor();
}

static void state_attack(void) {
    Actor* a = gPlayer;
    int t = a->timer;
    gPl.sword_phase = t < 5 ? 0 : t < 10 ? 1 : 2;
    gPl.sword_active = (t >= 1 && t <= 11);
    if (++a->timer >= ATTACK_FRAMES) {
        a->state = PS_NORMAL;
        gPl.sword_active = 0;
        gPl.sword_phase = 0;
    }
}

static void state_hurt(void) {
    Actor* a = gPlayer;
    actor_move(a, a->kb_speed, a->kb_dir);
    if (--a->timer == 0)
        a->state = PS_NORMAL;
}

static void state_fall(void) {
    Actor* a = gPlayer;
    if (--a->timer == 0) {
        a->x = gPl.safe_x << 16;
        a->y = gPl.safe_y << 16;
        a->state = PS_NORMAL;
        a->iframes = 20;
        gPl.hp -= 2;
        if (gPl.hp <= 0) {
            gPl.hp = 0;
            a->state = PS_DEAD;
            a->timer = 0;
        }
    }
}

static void state_jump(void) {
    Actor* a = gPlayer;
    a->z += a->zvel;
    a->zvel -= Q16(0.125);
    if (a->timer < 255)
        a->timer++;
    if (a->speed) {
        if (a->sub == 1)
            actor_move_free(a, a->speed, a->dir); /* ledge drop ignores walls */
        else
            actor_move(a, a->speed, a->dir);
    }
    if (a->z <= 0) {
        a->z = 0;
        a->zvel = 0;
        a->sub = 0;
        a->state = PS_NORMAL;
        a->speed = 0;
        check_floor();
    }
}

static void state_itemget(void) {
    Actor* a = gPlayer;
    if (++gPl.got_timer > 70 && (gKeysDown & (KEY_A | KEY_B | KEY_START))) {
        a->state = PS_NORMAL;
        gPl.got_item = 0;
    }
    if (gPl.got_timer > 180) {
        a->state = PS_NORMAL;
        gPl.got_item = 0;
    }
}

static void state_dead(void) {
    Actor* a = gPlayer;
    if (gPl.dead_timer < 255)
        gPl.dead_timer++;
    a->z = 0;
}

void player_update(void) {
    Actor* a = gPlayer;
    if (a->iframes)
        a->iframes--;
    /* a small residual knockback (bounces) applies in NORMAL too */
    if (a->kb_timer && a->state == PS_NORMAL) {
        actor_move(a, a->kb_speed, a->kb_dir);
        a->kb_timer--;
        if (a->z > 0 || a->zvel > 0) {
            a->z += a->zvel;
            a->zvel -= Q16(0.125);
            if (a->z < 0)
                a->z = 0;
        }
    }
    switch (a->state) {
        case PS_NORMAL: state_normal(); break;
        case PS_ROLL: state_roll(); break;
        case PS_ATTACK: state_attack(); break;
        case PS_HURT: state_hurt(); break;
        case PS_FALL: state_fall(); break;
        case PS_JUMP: state_jump(); break;
        case PS_ITEMGET: state_itemget(); break;
        case PS_DEAD: state_dead(); break;
        default: break;
    }
    if (gPl.lamp_timer)
        gPl.lamp_timer--;
}

/* Jumps with the Petal Cloak: forward 1.25, zvel 2.0, 32 frames in the
   air, so 40 px: two and a half tiles. A one-tile chasm is cleared from
   anywhere within a tile and a half of its edge. */
void player_cloak_jump(void) {
    Actor* a = gPlayer;
    if (a->state != PS_NORMAL)
        return;
    int dir = input_dir();
    if (dir == DIR_NONE)
        dir = facing_to_dir(a->facing);
    start_jump(dir, Q8(1.25), Q16(2.0));
    a->sub = 0;
    sfx_play(SFX_JUMP);
}

void player_ledge_jump_sub(void) {
    gPlayer->sub = 1;
}

/* ------------------------------------------------------------- drawing -- */
static const u8 sIdleFrame[4] = { F_HERO_IDLE_N, F_HERO_IDLE_E, F_HERO_IDLE_S, F_HERO_IDLE_E };
static const u8 sWalk1Frame[4] = { F_HERO_WALK_N1, F_HERO_WALK_E1, F_HERO_WALK_S1, F_HERO_WALK_E1 };
static const u8 sWalk2Frame[4] = { F_HERO_WALK_N2, F_HERO_WALK_E2, F_HERO_WALK_S2, F_HERO_WALK_E2 };
static const u8 sAtkFrame[4] = { F_HERO_ATK_N, F_HERO_ATK_E, F_HERO_ATK_S, F_HERO_ATK_E };
static const u8 sHurtFrame[4] = { F_HERO_HURT_N, F_HERO_HURT_E, F_HERO_HURT_S, F_HERO_HURT_E };

static void draw_sword(void) {
    Actor* a = gPlayer;
    int px = PX(a->x) - gCamX, py = PX(a->y) - PX(a->z) - gCamY;
    int phase = gPl.sword_phase;
    int frame, hflip = 0, vflip = 0, sx = px - 8, sy = py - 24;
    /* orientation per facing and phase: start side, forward, end side */
    static const s8 off[4][3][2] = {
        /* N: E side, up, W side */ { { 10, -24 }, { 0, -40 }, { -10, -24 } },
        /* E */ { { 10, -32 }, { 14, -20 }, { 10, -8 } },
        /* S: W side, down, E side */ { { -10, -14 }, { 0, -2 }, { 10, -14 } },
        /* W */ { { -10, -32 }, { -14, -20 }, { -10, -8 } },
    };
    static const u8 orient[4][3] = {
        { 1, 0, 1 },  /* N: diag NE?, up, NW */
        { 1, 2, 1 },  /* E: NE, E, SE */
        { 1, 0, 1 },  /* S: SW, S, SE */
        { 1, 2, 1 },  /* W: NW, W, SW */
    };
    (void)orient;
    /* frames: blade_s = 0 (down), blade_e = 1 (right), blade_se = 2 (diag) */
    switch (a->facing) {
        case FACE_N:
            if (phase == 1) { frame = F_SWORD_BLADE_S; vflip = 1; }
            else { frame = F_SWORD_BLADE_SE; vflip = 1; hflip = (phase == 2); }
            break;
        case FACE_S:
            if (phase == 1) { frame = F_SWORD_BLADE_S; }
            else { frame = F_SWORD_BLADE_SE; hflip = (phase == 0); }
            break;
        case FACE_E:
            if (phase == 1) { frame = F_SWORD_BLADE_E; }
            else { frame = F_SWORD_BLADE_SE; vflip = (phase == 0); }
            break;
        default:
            if (phase == 1) { frame = F_SWORD_BLADE_E; hflip = 1; }
            else { frame = F_SWORD_BLADE_SE; hflip = 1; vflip = (phase == 0); }
            break;
    }
    sx = px - 8 + off[a->facing][phase][0];
    sy = py - 8 + off[a->facing][phase][1];
    OamEntry* o = oam_alloc();
    if (!o)
        return;
    o->attr0 = ATTR0_Y(sy) | ATTR0_SQUARE;
    o->attr1 = ATTR1_X(sx) | ATTR1_SIZE(1) | (hflip ? ATTR1_HFLIP : 0) | (vflip ? ATTR1_VFLIP : 0);
    o->attr2 = ATTR2_TILE(SWORD_TILE + frame * 4) | ATTR2_PRIO(2) | ATTR2_PAL(PAL_OBJ_HERO);
}

void player_draw(void) {
    Actor* a = gPlayer;
    int frame;
    int f = a->facing;
    a->hflip = (f == FACE_W);
    switch (a->state) {
        case PS_ROLL: {
            int t = a->timer;
            frame = t < 6 ? F_HERO_ROLL_1 : t < 18 ? F_HERO_ROLL_2 : F_HERO_ROLL_3;
            a->hflip = (a->dir > 16);
            break;
        }
        case PS_ATTACK:
            frame = sAtkFrame[f];
            break;
        case PS_HURT:
        case PS_DEAD:
            frame = sHurtFrame[f];
            break;
        case PS_FALL:
            frame = sHurtFrame[FACE_S];
            break;
        case PS_JUMP:
            frame = sWalk1Frame[f];
            break;
        case PS_ITEMGET:
            frame = F_HERO_IDLE_S;
            break;
        default:
            if (a->speed && sWalkTimer) {
                int step = (sWalkTimer / 7) & 3; /* TMC: 30-frame cycle */
                frame = step == 1 ? sWalk1Frame[f] : step == 3 ? sWalk2Frame[f] : sIdleFrame[f];
            } else {
                frame = sIdleFrame[f];
            }
            break;
    }
    hero_set_frame(frame);
    a->frame = 0;
    if (a->state == PS_FALL) {
        /* sink: draw lower and lower, then vanish */
        int t = FALL_FRAMES - a->timer;
        if (t > 24)
            return;
        int sx = PX(a->x) - 8 - gCamX;
        int sy = PX(a->y) - 32 - gCamY + t;
        draw_sprite(sx, sy, SHEET_HERO, HERO_TILE, 0, a->hflip, a->prio, a->pal);
        return;
    }
    if (a->state == PS_DEAD && gPl.dead_timer > 60 && (gPl.dead_timer & 4))
        return;
    /* the found item, held up over the head */
    if (a->state == PS_ITEMGET && gPl.got_item) {
        extern u16 items_sheet_tile(void);
        int sx = PX(a->x) - 8 - gCamX;
        int sy = PX(a->y) - 48 - gCamY - ((gPl.got_timer < 16) ? (16 - gPl.got_timer) : 0);
        draw_sprite(sx, sy, SHEET_ITEMS, items_sheet_tile(), gPl.got_item, 0, 1, PAL_OBJ_FX);
    }
    /* the sword draws under the hero when swung north, over otherwise */
    if (a->state == PS_ATTACK && a->facing == FACE_N) {
        actor_draw(a);
        draw_sword();
    } else {
        if (a->state == PS_ATTACK)
            draw_sword();
        actor_draw(a);
    }
}

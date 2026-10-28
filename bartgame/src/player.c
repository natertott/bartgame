/* BARTGAME: the player. The Bloom, half man half plant, moves like Link.

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
#include "react.h"
#include "objects.h"

Actor* gPlayer;
PlayerState gPl;

#define WALK_SPEED Q8(1.25)
#define ROLL_FRAMES 24
#define ATTACK_FRAMES 15
#define HURT_FRAMES 8
#define FALL_FRAMES 36
#define HERO_TILE OBJ_TILE_HERO
#define SWORD_TILE OBJ_TILE_SWORD
#define SHIELD_TILE OBJ_TILE_SHIELD

static u8 sLastFrame = 0xFF;
static u8 sLastShieldFrame = 0xFF;
static u8 sWalkTimer;
/* Visual action state is transient, outside PlayerState/save data. One
   streamed 32x32 layer serves the sword, held tools and airborne cape. */
static u16 sActionTile, sLastActionFrame, sShadowTile;
static u8 sUseItem, sUseTimer, sUseLength, sUseFacing;

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
    gPl.items = ITEM_SWORD | ITEM_SHIELD;
    gPl.sword_dmg = 2;
    gPl.equip[SLOT_A] = EQ_NONE;
    gPl.equip[SLOT_B] = EQ_SWORD;
    gPl.equip[SLOT_L] = EQ_SHIELD;
    gPl.carry = CARRY_NONE;
    /* the Drain Cap is in the pack from the start, on no button */
    gPl.items2 = ITEM2_HUBCAP;
    gPl.arrows = 0;
}

/* ------------------------------------------------------------- equip -- */
u16 player_equip_keys(int eq) {
    u16 k = 0;
    if (gPl.equip[SLOT_A] == eq)
        k |= KEY_A;
    if (gPl.equip[SLOT_B] == eq)
        k |= KEY_B;
    if (gPl.equip[SLOT_L] == eq)
        k |= KEY_L;
    return k;
}

bool8 player_has_item(int eq) {
    switch (eq) {
        case EQ_SWORD: return (gPl.items & ITEM_SWORD) != 0;
        case EQ_BOMBS: return (gPl.items & ITEM_BOMBS) != 0;
        case EQ_LAMP: return (gPl.items & ITEM_LAMP) != 0;
        case EQ_CLOAK: return (gPl.items & ITEM_CLOAK) != 0;
        case EQ_SHIELD: return (gPl.items & ITEM_SHIELD) != 0;
        case EQ_BOW: return (gPl.items2 & ITEM2_BOW) != 0;
        case EQ_HUBCAP: return (gPl.items2 & ITEM2_HUBCAP) != 0;
        default: return FALSE;
    }
}

/* put eq on a button; an item sits on one button only */
void player_equip_set(int slot, int eq) {
    int i;
    if (eq != EQ_NONE && !player_has_item(eq))
        return;
    if (eq != EQ_NONE)
        for (i = 0; i < SLOT_COUNT; i++)
            if (gPl.equip[i] == eq)
                gPl.equip[i] = EQ_NONE;
    gPl.equip[slot] = eq;
}

/* a new item goes to the first free of B and L */
void player_auto_equip(int eq) {
    int i;
    for (i = 0; i < SLOT_COUNT; i++)
        if (gPl.equip[i] == eq)
            return;
    for (i = SLOT_B; i < SLOT_COUNT; i++)
        if (gPl.equip[i] == EQ_NONE) {
            gPl.equip[i] = eq;
            return;
        }
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
    a->w = sheets[SHEET_HERO].w; /* Native body canvas; weapons are separate. */
    a->h = sheets[SHEET_HERO].h;
    a->pal = PAL_OBJ_HERO;
    a->sheet = SHEET_HERO;
    a->tile = HERO_TILE;
    a->state = PS_NORMAL;
    gPl.safe_x = px;
    gPl.safe_y = py;
    sLastFrame = 0xFF;
    sLastActionFrame = 0xFFFF;
    sActionTile = sprite_alloc(16);
    sShadowTile = sprite_load_sheet(SHEET_BLOOMSHADOW);
    sUseItem = sUseTimer = sUseLength = 0;
    sWalkTimer = 0;
    gPl.sword_active = gPl.lamp_timer = gPl.shield_up = 0;
    /* The blade stays resident; one shield view streams into its original
       reservation so both designs cost no extra live OBJ allocation. */
    dma3_copy32(sheets[SHEET_SWORD].tiles, OBJ_TILE(SWORD_TILE), sheets[SHEET_SWORD].tile_count * 32);
    sLastShieldFrame=0xFF;
}

void player_shield_upgrade(void) {
    gPl.items2 |= ITEM2_SHIELD_UPGRADE;
}

int player_shield_icon(void) {
    return (gPl.items2&ITEM2_SHIELD_UPGRADE)?F_ICON32_SHIELD_UPGRADED:F_ICON32_SHIELD;
}

static int shield_source_frame(int view) {
    return view+((gPl.items2&ITEM2_SHIELD_UPGRADE)?F_SHIELD_UPGRADED_FRONT:F_SHIELD_FRONT);
}

int player_shield_frame(int view) {
    int source=shield_source_frame(view);
    if (sLastShieldFrame!=source) {
        const SpriteSheet* sh=&sheets[SHEET_SHIELD];
        sLastShieldFrame=source;
        vram_queue(sh->tiles+source*sh->frame_tiles*16,OBJ_TILE(SHIELD_TILE),sh->frame_tiles*32);
    }
    return 0;
}

int player_shield_palette(int view) {
    return shield_frame_pal[shield_source_frame(view)];
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
    if (a->state == PS_HURT || a->state == PS_FALL || a->state == PS_DEAD || a->state == PS_ITEMGET || a->state == PS_SWALLOWED)
        return FALSE;
    return TRUE;
}

bool8 player_hurt(int damage, int from_dir) {
    Actor* a = gPlayer;
    if (!player_is_vulnerable())
        return FALSE;
    /* the shield: a blow from the front, while it is held, is turned.
       from_dir is the way the blow pushes, so the front is the facing
       turned round. */
    if (gPl.shield_up) {
        int front = (facing_to_dir(a->facing) + 16) & 31;
        int d = (from_dir - front) & 31;
        if (d <= 5 || d >= 27) {
            int px = PX(a->x), py = PX(a->y) - 12;
            switch (a->facing) {
                case FACE_N: py -= 10; break;
                case FACE_S: py += 8; break;
                case FACE_E: px += 10; break;
                default: px -= 10; break;
            }
            fx_spawn(FX_CLANG, px, py);
            sfx_play(SFX_BUMP);
            a->kb_dir = from_dir;
            a->kb_speed = Q8(0.75);
            a->kb_timer = 6;
            return FALSE;
        }
    }
    gPl.hp -= damage;
    if (gPl.hp < 0)
        gPl.hp = 0;
    gPl.carry = CARRY_NONE;
    /* A hurt roll-bounce has an ordinary airborne recovery, not a cape.
       Actual jumps retain their cape/ledge/drop-in landing behaviour. */
    if (a->z > 0 && a->state != PS_JUMP)
        a->sub = 3;
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
    return TRUE;
}

void player_heart_piece(void) {
    gPl.hearts_pieces++;
    if (gPl.hearts_pieces >= 4) {
        gPl.hearts_pieces = 0;
        gPl.hp_max += 8;
        gPl.hp = gPl.hp_max;
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
    if (item_bit == ITEM_BOMBS)
        player_auto_equip(EQ_BOMBS);
    if (item_bit == ITEM_LAMP)
        player_auto_equip(EQ_LAMP);
    if (item_bit == ITEM_CLOAK)
        player_auto_equip(EQ_CLOAK);
    sfx_play(SFX_ITEM);
}

/* A single pose clock drives native blade pixels and their contact box.
   The art builder derives these inclusive bounds from the damaging blade
   and its short trail, excluding the grip and guard. */
static int sword_step(int age) {
    return age<2 ? 0 : age<5 ? 1 : age<9 ? 2 : age<13 ? 3 : 4;
}

static void sword_bounds(int* x0, int* y0, int* x1, int* y1) {
    Actor* a = gPlayer;
    const s8* r = &bloom_sword_hit[(a->facing*5+sword_step(a->timer))*4];
    int px = PX(a->x), py = PX(a->y)-PX(a->z);
    *x0 = px+r[0]; *y0 = py+r[1]; *x1 = px+r[2]; *y1 = py+r[3];
}

bool8 player_sword_box(int* x0, int* y0, int* x1, int* y1) {
    if (!gPl.sword_active)
        return FALSE;
    sword_bounds(x0, y0, x1, y1);
    return TRUE;
}

void player_item_pose(int item) {
    sUseItem = item;
    sUseLength = item == EQ_LAMP ? 20 : item == EQ_BOW ? 16 : 12;
    sUseTimer = sUseLength;
    sUseFacing = gPlayer->facing;
    gPl.shield_up = 0;
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
    int px = PX(a->x), py = PX(a->y) - 4;
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

/* into water (water TRUE) or a hole: the hero is drawn into the tile's
   middle and goes under there */
static void start_fall(bool8 water, int tx, int ty) {
    Actor* a = gPlayer;
    gPl.carry = CARRY_NONE;
    gPl.shield_up = 0;
    a->state = PS_FALL;
    a->sub = water ? 1 : 0;
    a->timer = FALL_FRAMES;
    a->x = (tx * 16 + 8) << 16;
    a->y = (ty * 16 + 13) << 16;
    gPl.sword_active = 0;
    sfx_play(SFX_FALL);
}

static void check_floor(void) {
    Actor* a = gPlayer;
    if (a->z > 0)
        return;
    /* the feet point: the moment it crosses into water or a hole, in */
    int px = PX(a->x), py = PX(a->y) - 4;
    u8 t = room_type_px(px, py);
    if (t == TT_PIT || t == TT_WATER) {
        start_fall(t == TT_WATER, px >> 4, py >> 4);
        return;
    }
    if (t == TT_HURT && (gFrame & 31) == 0)
        player_hurt(2, (a->dir + 16) & 31);
    remember_safe_spot();
}

/* --------------------------------------------------------- lifting -- */
#define LIFT_FRAMES 12

/* the tile one step ahead of the feet, where a bush or a stone would be */
static void facing_tile(int* tx, int* ty) {
    Actor* a = gPlayer;
    int px = PX(a->x), py = PX(a->y) - 4;
    switch (a->facing) {
        case FACE_N: py -= 11; break;
        case FACE_S: py += 11; break;
        case FACE_E: px += 11; break;
        default: px -= 11; break;
    }
    *tx = px >> 4;
    *ty = py >> 4;
}

/* R in front of a bush, a pot or a stone: lift it. Boulders want the
   gauntlet. Returns TRUE when R was spent. */
static bool8 try_lift(void) {
    Actor* a = gPlayer;
    int tx, ty;
    facing_tile(&tx, &ty);
    u8 t = room_type(tx, ty);
    if (t == TT_LIFT1 || (t == TT_LIFT2 && (gPl.items & ITEM_GAUNTLET))) {
        gPl.carry = room_lift(tx, ty);
        a->state = PS_LIFT;
        a->timer = 0;
        a->speed = 0;
        gPl.sword_active = 0;
        sfx_play(SFX_PICKUP);
        return TRUE;
    }
    if (t == TT_LIFT2) {
        sfx_play(SFX_BUMP);
        return TRUE;
    }
    return FALSE;
}

static void throw_carried(void) {
    Actor* a = gPlayer;
    thrown_spawn(gPl.carry, PX(a->x), PX(a->y), a->facing);
    gPl.carry = CARRY_NONE;
    a->state = PS_NORMAL;
    a->timer = 0;
    player_item_pose(EQ_NONE);
    sfx_play(SFX_ROLL);
}

static void state_lift(void) {
    Actor* a = gPlayer;
    if (++a->timer >= LIFT_FRAMES) {
        a->state = PS_CARRY;
        a->timer = 0;
    }
}

static void state_normal(void) {
    Actor* a = gPlayer;
    int dir = input_dir();
    if (gPl.item_cooldown)
        gPl.item_cooldown--;

    /* attack, with whichever button holds the sword */
    if ((gKeysDown & player_equip_keys(EQ_SWORD)) || gPl.queued_attack) {
        gPl.queued_attack = 0;
        a->state = PS_ATTACK;
        a->timer = 0;
        gPl.sword_phase = 0;
        gPl.sword_active = 0;
        gPl.shield_up = 0;
        sUseTimer = 0;
        a->speed = 0;
        if (dir != DIR_NONE)
            a->facing = facing_from_dir(dir, a->facing);
        sfx_play(SFX_SWORD);
        return;
    }
    /* R: lift what stands ahead, else roll when moving */
    if (gKeysDown & KEY_R) {
        if (try_lift())
            return;
        if (dir != DIR_NONE) {
            a->state = PS_ROLL;
            a->timer = 0;
            sUseTimer = 0;
            gPl.shield_up = 0;
            a->dir = (a->facing * 8);
            if ((dir & 7) == 0)
                a->dir = dir;
            a->facing = dir_to_facing(a->dir);
            sfx_play(SFX_ROLL);
            return;
        }
    }
    /* the shield: held up while its button is held, the hero slows and
       keeps facing the way the shield points */
    gPl.shield_up = ((gKeysHeld & player_equip_keys(EQ_SHIELD)) && !gPl.carry && !sUseTimer) ? 1 : 0;
    if (dir == DIR_NONE) {
        a->speed = 0;
        gPl.push_timer = 0;
        sWalkTimer = 0;
    } else {
        if (!gPl.shield_up)
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
        a->speed = gPl.shield_up ? WALK_SPEED / 2 : WALK_SPEED;
        actor_move(a, a->speed, dir);
        sWalkTimer++;
    }
    check_floor();
}

static void state_roll(void) {
    Actor* a = gPlayer;
    gPl.shield_up = 0;
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
    if ((gKeysDown & player_equip_keys(EQ_SWORD)) && t >= 18)
        gPl.queued_attack = 1;
    if (++a->timer >= ROLL_FRAMES) {
        a->state = PS_NORMAL;
        a->timer = 0;
    }
    check_floor();
}

/* walking with the load over the head; R throws it */
static void state_carry(void) {
    Actor* a = gPlayer;
    int dir = input_dir();
    if (gKeysDown & KEY_R) {
        throw_carried();
        return;
    }
    /* a sword swing drops the load at the feet, where it breaks, and
       the swing follows */
    if (gKeysDown & player_equip_keys(EQ_SWORD)) {
        Actor* t = thrown_spawn(gPl.carry, PX(a->x), PX(a->y), a->facing);
        if (t) {
            t->speed = 0;
            t->z = Q16(20);
            t->zvel = 0;
        }
        gPl.carry = CARRY_NONE;
        a->state = PS_NORMAL;
        a->timer = 0;
        gPl.queued_attack = 1;
        return;
    }
    if (dir == DIR_NONE) {
        a->speed = 0;
        sWalkTimer = 0;
    } else {
        a->facing = facing_from_dir(dir, a->facing);
        a->dir = dir;
        a->speed = WALK_SPEED;
        actor_move(a, a->speed, dir);
        sWalkTimer++;
    }
    check_floor();
}

static void state_attack(void) {
    Actor* a = gPlayer;
    int t = ++a->timer;
    gPl.sword_phase = t < 5 ? 0 : t < 9 ? 1 : 2;
    /* Two anticipation frames, eleven live frames, then recovery. The
       old input frame dealt an invisible hit before disabling again. */
    gPl.sword_active = (t >= 2 && t <= 12);
    if (t >= ATTACK_FRAMES) {
        a->state = PS_NORMAL;
        gPl.sword_active = 0;
        gPl.sword_phase = 0;
    }
}

static void state_hurt(void) {
    Actor* a = gPlayer;
    actor_move(a, a->kb_speed, a->kb_dir);
    if (--a->timer == 0) {
        a->state = a->z > 0 ? PS_JUMP : PS_NORMAL;
        if (a->state == PS_JUMP)
            a->timer = 4; /* continue the airborne pose, not a new takeoff */
    }
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
        if (a->sub == 2) {
            /* down from the drain's ceiling: a thump and a puff */
            fx_spawn(FX_PUFF, PX(a->x), PX(a->y) - 4);
            sfx_play(SFX_BUMP);
        }
        a->z = 0;
        a->zvel = 0;
        a->sub = 0;
        a->state = PS_NORMAL;
        a->speed = 0;
        check_floor();
    }
}

/* The Drain Cap's mouth has the hero: he flails, sinks, is gone; then
   the game takes him home (game_return_to_hub). */
static void state_swallowed(void) {
    Actor* a = gPlayer;
    a->speed = 0;
    if (a->timer < 255)
        a->timer++;
    if (a->timer == 30)
        a->flags |= AF_HIDDEN;
    if (a->timer == 44) {
        extern void game_return_to_hub(void);
        game_return_to_hub();
    }
}

void player_swallow(void) {
    Actor* a = gPlayer;
    if (a->state != PS_NORMAL)
        return;
    a->state = PS_SWALLOWED;
    a->timer = 0;
    a->speed = 0;
    a->facing = FACE_S;
    gPl.carry = CARRY_NONE;
    gPl.shield_up = 0;
    gPl.sword_active = 0;
    fx_spawn(FX_MOUTH, PX(a->x), PX(a->y));
    sfx_play(SFX_FALL);
}

void player_drop_in(void) {
    Actor* a = gPlayer;
    a->flags &= ~AF_HIDDEN;
    a->state = PS_JUMP;
    a->sub = 2;
    a->speed = 0;
    a->z = Q16(96);
    a->zvel = 0;
    a->timer = 0;
    a->facing = FACE_S;
}

/* the bow: an arrow from the chest, the way the hero faces */
bool8 player_shoot(void) {
    Actor* a = gPlayer;
    if (gPl.arrows == 0)
        return FALSE;
    /* The first rendered nock meets the authored hand after this update's
       3px movement and the arrow's 6px visual height. Source nocks are
       N(8,12), E(3,8), S(8,3), with west mirrored from east. */
    static const s8 origin[4][2]={{5,-4},{9,2},{3,7},{-9,2}};
    int px = PX(a->x)+origin[a->facing][0];
    int py = PX(a->y)+origin[a->facing][1];
    gPl.arrows--;
    proj_spawn(PJ_ARROW, px, py, facing_to_dir(a->facing), Q8(3.0), 2, TRUE);
    sfx_play(SFX_SPIT);
    return TRUE;
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
    bool8 landed = FALSE;
    if (sUseTimer)
        sUseTimer--;
    if (a->iframes)
        a->iframes--;
    /* Hurt and wall-bounce recovery must not freeze an existing flight.
       JUMP advances its own arc; all other live airborne poses keep the
       same gravity even after the short knockback timer has expired. */
    if (a->state != PS_JUMP && a->state != PS_FALL && a->state != PS_DEAD &&
        a->state != PS_SWALLOWED && (a->z > 0 || a->zvel > 0)) {
        a->z += a->zvel;
        a->zvel -= Q16(0.125);
        if (a->z <= 0) {
            a->z = 0;
            a->zvel = 0;
            landed = TRUE;
        }
    }
    /* a small residual knockback (bounces) applies in NORMAL too */
    if (a->kb_timer && a->state == PS_NORMAL) {
        actor_move(a, a->kb_speed, a->kb_dir);
        a->kb_timer--;
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
        case PS_LIFT: state_lift(); break;
        case PS_CARRY: state_carry(); break;
        case PS_SWALLOWED: state_swallowed(); break;
        default: break;
    }
    if (landed && a->state != PS_FALL && a->state != PS_DEAD && a->state != PS_SWALLOWED)
        check_floor();
    if (gPl.lamp_timer)
        gPl.lamp_timer--;
    if (a->state != PS_NORMAL || a->facing != sUseFacing)
        sUseTimer = 0;
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
static const u8 sAtkFrame[3][4] = {
    { F_HERO_ATK_N1, F_HERO_ATK_E1, F_HERO_ATK_S1, F_HERO_ATK_E1 }, /* the wind-up */
    { F_HERO_ATK_N, F_HERO_ATK_E, F_HERO_ATK_S, F_HERO_ATK_E },     /* the blow */
    { F_HERO_ATK_N3, F_HERO_ATK_E3, F_HERO_ATK_S3, F_HERO_ATK_E3 }, /* the follow-through */
};
static const u8 sHurtFrame[4] = { F_HERO_HURT_N, F_HERO_HURT_E, F_HERO_HURT_S, F_HERO_HURT_E };
static const u8 sGuardFrame[4] = { F_HERO_GUARD_N, F_HERO_GUARD_E, F_HERO_GUARD_S, F_HERO_GUARD_E };
static const u8 sGuardStep[2][4] = {
    { F_HERO_GUARD_N1, F_HERO_GUARD_E1, F_HERO_GUARD_S1, F_HERO_GUARD_E1 },
    { F_HERO_GUARD_N2, F_HERO_GUARD_E2, F_HERO_GUARD_S2, F_HERO_GUARD_E2 },
};
static const u8 sLiftFrame[3][4] = {
    { F_HERO_LIFT_N0, F_HERO_LIFT_E0, F_HERO_LIFT_S0, F_HERO_LIFT_E0 },
    { F_HERO_LIFT_N1, F_HERO_LIFT_E1, F_HERO_LIFT_S1, F_HERO_LIFT_E1 },
    { F_HERO_LIFT_N2, F_HERO_LIFT_E2, F_HERO_LIFT_S2, F_HERO_LIFT_E2 },
};
static const u8 sUseFrame[3][4] = {
    { F_HERO_USE_N1, F_HERO_USE_E1, F_HERO_USE_S1, F_HERO_USE_E1 },
    { F_HERO_USE_N2, F_HERO_USE_E2, F_HERO_USE_S2, F_HERO_USE_E2 },
    { F_HERO_USE_N3, F_HERO_USE_E3, F_HERO_USE_S3, F_HERO_USE_E3 },
};
static const u8 sBowFrame[3][4] = {
    { F_HERO_BOW_N0, F_HERO_BOW_E0, F_HERO_BOW_S0, F_HERO_BOW_E0 },
    { F_HERO_BOW_N1, F_HERO_BOW_E1, F_HERO_BOW_S1, F_HERO_BOW_E1 },
    { F_HERO_BOW_N2, F_HERO_BOW_E2, F_HERO_BOW_S2, F_HERO_BOW_E2 },
};
static const u8 sCapeFrame[3][4] = {
    { F_HERO_CAPE_N1, F_HERO_CAPE_E1, F_HERO_CAPE_S1, F_HERO_CAPE_E1 },
    { F_HERO_CAPE_N2, F_HERO_CAPE_E2, F_HERO_CAPE_S2, F_HERO_CAPE_E2 },
    { F_HERO_CAPE_N3, F_HERO_CAPE_E3, F_HERO_CAPE_S3, F_HERO_CAPE_E3 },
};
/* the load over the head: arms up, standing and the two walking steps */
static const u8 sCarryFrame[3][4] = {
    { F_HERO_CARRY_N, F_HERO_CARRY_E, F_HERO_CARRY_S, F_HERO_CARRY_E },
    { F_HERO_CARRY_N1, F_HERO_CARRY_E1, F_HERO_CARRY_S1, F_HERO_CARRY_E1 },
    { F_HERO_CARRY_N2, F_HERO_CARRY_E2, F_HERO_CARRY_S2, F_HERO_CARRY_E2 },
};

/* Lift from the actual object's tile to the raised hands. The final
   top-left (-8,-40) matches a thrown 16px object's initial z=24 exactly,
   so releasing it does not teleport the artwork away from the hands. */
static void draw_load(Actor* a) {
    if (a->flags & AF_HIDDEN || (a->iframes && (gFrame & 2)))
        return;
    int t = (a->state == PS_LIFT) ? a->timer : LIFT_FRAMES;
    int tx, ty;
    facing_tile(&tx, &ty);
    int gx = tx * 16, gy = ty * 16;
    int cx = PX(a->x) - 8, cy = PX(a->y) - 40;
    int ease = t * (2 * LIFT_FRAMES - t);
    int sx = gx + ((cx - gx) * ease) / (LIFT_FRAMES * LIFT_FRAMES) - gCamX;
    int sy = gy + ((cy - gy) * ease) / (LIFT_FRAMES * LIFT_FRAMES) - PX(a->z) - gCamY;
    draw_sprite(sx, sy, SHEET_LIFT, lift_sheet_tile(), gPl.carry - 1, 0, a->prio, lift_frame_pal[gPl.carry - 1]);
}

static int use_step(void) {
    int age = sUseLength - sUseTimer;
    return age < 4 ? 0 : age < sUseLength - 4 ? 1 : 2;
}

static int cape_step(Actor* a) {
    return a->timer < 4 ? 0 : a->zvel < 0 && a->z < Q16(6) ? 2 : 1;
}

static void action_frame(int frame, int sx, int sy, int flip, int prio) {
    if (!sActionTile)
        return;
    const SpriteSheet* sh = &sheets[SHEET_BLOOMFX];
    if (sLastActionFrame != frame) {
        sLastActionFrame = frame;
        vram_queue(sh->tiles + frame * sh->frame_tiles * 16, OBJ_TILE(sActionTile), sh->frame_tiles * 32);
    }
    draw_sprite(sx, sy, SHEET_BLOOMFX, sActionTile, 0, flip, prio, bloomfx_frame_pal[frame]);
}

/* Earlier OAM entries appear nearer to the viewer. North-facing held
   tools belong on the far side of the body; the back-worn cape belongs on
   the near side when Bloom faces north. The cutting sweep stays legible
   over the body and uses the gameplay reach rectangle as its anchor. */
static void draw_action(Actor* a, bool8 behind) {
    if (a->flags & AF_HIDDEN || (a->iframes && (gFrame & 2)))
        return;
    int f = a->facing;
    int sx = PX(a->x)-16-gCamX, sy = PX(a->y)-32-PX(a->z)-gCamY;
    if (a->state == PS_JUMP && a->sub == 0) {
        if (behind != (f != FACE_N))
            return;
        static const u8 cape[4] = { F_BLOOMFX_CAPE_N0, F_BLOOMFX_CAPE_E0, F_BLOOMFX_CAPE_S0, F_BLOOMFX_CAPE_E0 };
        action_frame(cape[f]+cape_step(a), sx, sy, f==FACE_W, a->prio);
        return;
    }
    if (a->state == PS_ATTACK) {
        if (behind)
            return;
        static const u8 sword[4] = { F_BLOOMFX_SWORD_N0, F_BLOOMFX_SWORD_E0, F_BLOOMFX_SWORD_S0, F_BLOOMFX_SWORD_W0 };
        const s8* origin=&bloom_sword_origin[f*2];
        int step=sword_step(a->timer);
        action_frame(sword[f]+step,PX(a->x)+origin[0]-gCamX,
                     PX(a->y)+origin[1]-PX(a->z)-gCamY,0,a->prio);
    } else if (a->state == PS_NORMAL && sUseTimer) {
        if (behind != (f == FACE_N))
            return;
        int base = -1;
        if (sUseItem == EQ_BOW) {
            static const u8 bow[4] = { F_BLOOMFX_BOW_N0, F_BLOOMFX_BOW_E0, F_BLOOMFX_BOW_S0, F_BLOOMFX_BOW_E0 };
            base=bow[f];
        } else if (sUseItem == EQ_LAMP) {
            static const u8 lamp[4] = { F_BLOOMFX_LAMP_N0, F_BLOOMFX_LAMP_E0, F_BLOOMFX_LAMP_S0, F_BLOOMFX_LAMP_E0 };
            base=lamp[f];
        }
        if (base>=0)
            /* The bow stays pinned to its hand through release/recovery;
               only Bloom's pose changes. Its three source prop frames are
               identical, so retain one streamed frame for the whole use. */
            action_frame(base+(sUseItem==EQ_BOW ? 0 : use_step()), sx, sy, f==FACE_W, a->prio);
    } else if (a->state == PS_NORMAL && gPl.shield_up) {
        if (behind != (f == FACE_N))
            return;
        /* Source grip (8,8), or (7,8) when mirrored, meets the same
           authored hand as the guard body in all four directions. */
        static const s8 at[4][2] = { { -3,-25 }, { -1,-20 }, { -8,-16 }, { -15,-20 } };
        static const u8 frame[4] = { F_SHIELD_BACK, F_SHIELD_SIDE, F_SHIELD_FRONT, F_SHIELD_SIDE };
        draw_sprite(PX(a->x)+at[f][0]-gCamX, PX(a->y)+at[f][1]-PX(a->z)-gCamY,
                    SHEET_SHIELD, SHIELD_TILE, player_shield_frame(frame[f]), f==FACE_W, a->prio, player_shield_palette(frame[f]));
    }
}

static void draw_ground_shadow(Actor* a) {
    if (!sShadowTile || a->state == PS_FALL || a->state == PS_DEAD || a->state == PS_SWALLOWED ||
        (a->flags & (AF_HIDDEN | AF_NOSHADOW)))
        return;
    int px = PX(a->x), py = PX(a->y);
    /* This footprint stays on the ground even when the airborne body is
       raised above a prop. Crowns and solid foreground still occlude it. */
    int prio = room_type_px(px, py - 1) == TT_FRONT ? 1 : 2;
    prio = room_prop_priority(px, py, 0, 16, 8, prio);
    draw_sprite(px - 8 - gCamX, py - 5 - gCamY, SHEET_BLOOMSHADOW,
                sShadowTile, 0, 0, prio, PAL_OBJ_HERO);
}

void player_draw(void) {
    Actor* a = gPlayer;
    int frame;
    int f = a->facing;
    a->hflip = (f == FACE_W);
    /* in front of a counter the hero is drawn over the overlay that
       hides the shopkeeper's legs (art/sw_hall.py) */
    a->prio = (room_type_px(PX(a->x), PX(a->y) - 1) == TT_FRONT) ? 1 : 2;
    a->prio=room_prop_priority(PX(a->x),PX(a->y),PX(a->z),18,24,a->prio);
    switch (a->state) {
        case PS_ROLL: {
            int t = a->timer;
            /* duck, the ball tumbling (four turns, three frames each,
               twice round), a squash on landing, up */
            frame = t < 3 ? F_HERO_ROLL_1 : t < 18 ? F_HERO_ROLL_2 + ((t - 3) / 3) % 4 : t < 21 ? F_HERO_ROLL_6 : F_HERO_ROLL_7;
            a->hflip = (a->dir > 16);
            if (t < 3 || t >= 18) {
                if (f == FACE_N) {
                    frame = t < 3 ? F_HERO_ROLL_N1 : t < 21 ? F_HERO_ROLL_N6 : F_HERO_ROLL_N7;
                    a->hflip = 0;
                } else if (f == FACE_S) {
                    frame = t < 3 ? F_HERO_ROLL_S1 : t < 21 ? F_HERO_ROLL_S6 : F_HERO_ROLL_S7;
                    a->hflip = 0;
                }
            }
            break;
        }
        case PS_ATTACK:
            frame = sAtkFrame[gPl.sword_phase][f];
            break;
        case PS_HURT:
            frame = sHurtFrame[f];
            break;
        case PS_DEAD:
            frame = gPl.dead_timer < 12 ? F_HERO_DEAD_0 : gPl.dead_timer < 26 ? F_HERO_DEAD_1 : F_HERO_DEAD_2;
            a->hflip = 0;
            break;
        case PS_FALL: {
            int t = FALL_FRAMES - a->timer;
            if (a->sub)
                frame = t < 12 ? F_HERO_DROWN_1 : t < 24 ? F_HERO_DROWN_2 : F_HERO_DROWN_3;
            else
                frame = t < 8 ? F_HERO_FALL_1 : t < 16 ? F_HERO_FALL_2 : F_HERO_FALL_3;
            a->hflip = 0;
            break;
        }
        case PS_JUMP:
            frame = sCapeFrame[cape_step(a)][f];
            break;
        case PS_ITEMGET:
            frame = F_HERO_ITEMGET;
            break;
        case PS_LIFT:
            frame = sLiftFrame[a->timer < 4 ? 0 : a->timer < 8 ? 1 : 2][f];
            break;
        case PS_SWALLOWED:
            /* startled, then shrinking into the mouth like into a hole */
            frame = a->timer < 10 ? F_HERO_JUMP_S : a->timer < 20 ? F_HERO_FALL_2 : F_HERO_FALL_3;
            a->hflip = 0;
            break;
        case PS_CARRY: {
            int step = (a->speed && sWalkTimer) ? (sWalkTimer / 7) & 3 : 0;
            frame = sCarryFrame[step == 1 ? 1 : step == 3 ? 2 : 0][f];
            break;
        }
        default:
            if (a->state == PS_NORMAL && sUseTimer) {
                /* EQ_NONE's transient visual pose is the carried-object
                   throw. Keep the raised hands through release before
                   bringing them down through the normal recovery poses. */
                if (sUseItem == EQ_NONE && use_step() == 0)
                    frame = sCarryFrame[0][f];
                else
                    frame = sUseItem == EQ_BOW ? sBowFrame[use_step()][f] : sUseFrame[use_step()][f];
                break;
            }
            if (a->state == PS_NORMAL && gPl.shield_up) {
                /* Guarding moves at half speed, so the feet take twice as
                   long to complete the same stride while the shield stays
                   planted at the hand. */
                int step = a->speed && sWalkTimer ? (sWalkTimer / 14) & 3 : 0;
                frame = step == 1 ? sGuardStep[0][f] : step == 3 ? sGuardStep[1][f] : sGuardFrame[f];
                break;
            }
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
        /* going under: the drowning frames in place, the hole's frames
           shrinking; the last frames show nothing */
        int t = FALL_FRAMES - a->timer;
        int sx = PX(a->x) - a->w / 2 - gCamX;
        int sy = PX(a->y) - a->h - gCamY;
        if (!a->sub && t >= 24)
            return;
        if (a->sub && t >= 32)
            return;
        draw_sprite(sx, sy, SHEET_HERO, HERO_TILE, 0, 0, a->prio, a->pal);
        return;
    }
    if (a->state == PS_DEAD && gPl.dead_timer > 60 && (gPl.dead_timer & 4))
        return;
    /* the found item, held up over the head */
    if (a->state == PS_ITEMGET && gPl.got_item) {
        int sx = PX(a->x) - 16 - gCamX;
        int sy = PX(a->y) - 60 - gCamY - ((gPl.got_timer < 16) ? (16 - gPl.got_timer) : 0);
        draw_sprite(sx, sy, SHEET_ICON32, icon32_frame_tile(gPl.got_item), 0, 0, 1, icon32_frame_palette(gPl.got_item));
    }
    /* Body and held parts share terrain priority, then their OAM order
       supplies directional depth. No prop is duplicated in body artwork. */
    if ((a->state == PS_LIFT || a->state == PS_CARRY) && gPl.carry && f != FACE_N)
        draw_load(a);
    objects_draw_hand(FALSE);
    draw_action(a,FALSE);
    actor_draw(a);
    draw_action(a,TRUE);
    objects_draw_hand(TRUE);
    if ((a->state == PS_LIFT || a->state == PS_CARRY) && gPl.carry && f == FACE_N)
        draw_load(a);
    draw_ground_shadow(a);
}

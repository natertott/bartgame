#ifndef ACTOR_H
#define ACTOR_H
#include "gba.h"
#include "assets.h"

/* Directions: 32 steps, N=0, E=8, S=16, W=24 (TMC's convention). */
#define DIR_N 0
#define DIR_E 8
#define DIR_S 16
#define DIR_W 24
#define DIR_NONE 0xFF
#define FACE_N 0
#define FACE_E 1
#define FACE_S 2
#define FACE_W 3
#define SIN(d8) sin_table[(d8) & 255]
#define COS(d8) sin_table[((d8) + 64) & 255]

/* actor kinds */
enum { AK_NONE, AK_PLAYER, AK_ENEMY, AK_PROJ, AK_PICKUP, AK_NPC, AK_OBJECT, AK_FX };

/* flags */
#define AF_FLYING 0x01   /* ignores tile collision */
#define AF_HITTABLE 0x02 /* takes hits from the player's weapons */
#define AF_SOLID 0x04    /* blocks the player */
#define AF_HURTS 0x08    /* contact hurts the player */
#define AF_NOSHADOW 0x10
#define AF_HIDDEN 0x20
#define AF_BOSS 0x40
#define AF_PRIO1 0x80    /* draw above the overlay layer */

/* collision bits from the last move */
#define COLL_N 1
#define COLL_E 2
#define COLL_S 4
#define COLL_W 8

typedef struct {
    s8 ox, oy; /* box center offset from the feet point */
    u8 hw, hh; /* half extents */
} Hitbox;

typedef struct Actor {
    u8 kind, type, state, sub;
    u8 timer, timer2, dir, facing;
    s32 x, y;     /* Q16.16 world pixels, the feet point */
    s32 z, zvel;  /* Q16.16 height above ground, positive up */
    s16 speed;    /* Q8.8 px per frame */
    s16 hp;
    u8 iframes, kb_timer, kb_dir, flags;
    s16 kb_speed;
    u8 hitbox, coll;
    u8 sheet, frame;
    u8 anim, anim_t;
    u8 prio, hflip;
    u8 w, h;
    u16 tile;
    u8 pal;
    u8 damage;
    u8 v[6];
    s16 vx, vy;
    u8 pad[4]; /* 64 bytes: the probe reads actors by this stride */
} Actor;

#define ACTOR_MAX 96
#define OBJ_TILE_MINIMAP 1008 /* the last 16 OBJ tiles: the HUD's mini-map, above the sheets */
extern Actor gActors[ACTOR_MAX];
extern const Hitbox gHitboxes[];
enum { HB_HERO, HB_HERO_FEET, HB_SMALL, HB_MED, HB_TALL, HB_BIG, HB_PROJ, HB_SWORD, HB_BLAST };

void actors_clear(void);
Actor* actor_new(u8 kind, u8 type, int px, int py);
void actor_free(Actor* a);
int actor_count(u8 kind);
Actor* actor_find(u8 kind, u8 type);
bool8 actor_move(Actor* a, int speed, int dir);
void actor_move_free(Actor* a, int speed, int dir);
bool8 actor_feet_box_solid(const Actor* a, int px, int py);
void actor_gravity(Actor* a);
bool8 actors_overlap(const Actor* a, const Actor* b);
bool8 actor_box_overlap(const Actor* a, int x0, int y0, int x1, int y1);
int actor_dir_to(const Actor* a, const Actor* b);
int actor_dist2(const Actor* a, const Actor* b);
int dir_to_facing(int dir);
int facing_to_dir(int facing);

/* sprites in OBJ VRAM */
void sprites_reset(void);
u16 sprite_load_sheet(int sheet);
u16 sprite_load_frame(int sheet, int frame); /* one frame resident; frame 0 of the result */
void actor_set_sheet(Actor* a, int sheet, u16 tile);
void actor_draw(Actor* a);
void draw_sprite(int sx, int sy, int sheet, u16 tile, int frame, int hflip, int prio, int pal);

/* VRAM uploads queued for the VBlank */
void vram_queue(const void* src, volatile void* dst, u32 bytes);
void vram_flush_queue(void);

#endif

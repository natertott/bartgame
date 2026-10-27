#ifndef PLAYER_H
#define PLAYER_H
#include "gba.h"
#include "actor.h"

enum { PS_NORMAL, PS_ROLL, PS_ATTACK, PS_HURT, PS_FALL, PS_JUMP, PS_ITEMGET, PS_DEAD, PS_TALK, PS_FROZEN, PS_LIFT, PS_CARRY, PS_SWALLOWED };

/* items, as bits in gPl.items */
#define ITEM_SWORD 0x01
#define ITEM_BOMBS 0x02
#define ITEM_LAMP 0x04
#define ITEM_CLOAK 0x08
#define ITEM_RELIC 0x10
#define ITEM_GAUNTLET 0x20 /* worn: lifts boulders */
#define ITEM_SHIELD 0x40   /* the Bark Shield */
/* more items, as bits in gPl.items2 */
#define ITEM2_BOW 0x01     /* the Thorn Bow, with its arrows */
#define ITEM2_HUBCAP 0x02  /* the Drain Cap: the way home */
#define ITEM2_MAP 0x04     /* the Map: every cell of the wood drawn */
#define ITEM2_ASTROLABE 0x08 /* the Astrolabe: chests, the Heart and the barriers marked */
#define ITEM2_SHIELD_UPGRADE 0x10 /* green-and-gold visual shield variant */

/* what a button holds: the pause menu assigns one to A, B and L */
enum { EQ_NONE, EQ_SWORD, EQ_BOMBS, EQ_LAMP, EQ_CLOAK, EQ_SHIELD, EQ_BOW, EQ_HUBCAP, EQ_COUNT };
enum { SLOT_A, SLOT_B, SLOT_L, SLOT_COUNT };

/* what the hero carries over his head */
enum { CARRY_NONE, CARRY_BUSH, CARRY_ROCK, CARRY_BOULDER, CARRY_POT };

typedef struct {
    s16 hp, hp_max;
    u16 gilt;
    u8 keys, bombs, items;
    u8 equip[SLOT_COUNT]; /* EQ_* per button: A, B, L */
    u8 sword_dmg;
    s16 safe_x, safe_y; /* last safe standing spot, room px */
    u8 safe_timer;
    u8 push_timer;      /* frames pushing into a ledge */
    u8 attack_timer;
    u8 sword_active;    /* sword hitbox live */
    u8 sword_phase;
    u8 lamp_timer;      /* lamp swing live */
    u8 dead_timer;
    u8 item_cooldown;
    u8 got_item;        /* item shown over the head during ITEMGET */
    u16 got_timer;
    u8 hearts_pieces;
    u8 input_lock;
    u8 queued_attack;
    u8 carry;           /* CARRY_* over the head */
    u8 shield_up;       /* the shield held before the hero this frame */
    u8 arrows;          /* for the bow, 50 at most */
    u8 items2;          /* ITEM2_* */
} PlayerState;

extern Actor* gPlayer;
extern PlayerState gPl;

void player_init(int px, int py, int facing);
void player_new_game(void);
void player_update(void);
void player_draw(void);
bool8 player_hurt(int damage, int from_dir); /* FALSE when the shield took it */
void player_heal(int amount);
void player_item_get(int item_bit, int sprite_frame);
bool8 player_sword_box(int* x0, int* y0, int* x1, int* y1);
bool8 player_lamp_box(int* x0, int* y0, int* x1, int* y1);
bool8 player_is_vulnerable(void);
void player_set_pos(int px, int py);
void player_face(int facing);
void player_cloak_jump(void);
u16 player_equip_keys(int eq);     /* the key bits of the buttons holding eq */
void player_equip_set(int slot, int eq);
bool8 player_has_item(int eq);
void player_heart_piece(void); /* a quarter heart; four make a whole */
void player_auto_equip(int eq); /* onto the first free of B and L */
void player_item_pose(int eq);  /* brief visual anticipation/use/recovery */
void player_swallow(void);      /* the Drain Cap: a mouth takes the hero under */
void player_drop_in(void);      /* arriving from the ceiling, falling to the feet */
bool8 player_shoot(void);       /* the bow: an arrow the way he faces, FALSE without one */
void player_shield_upgrade(void);
int player_shield_icon(void);
int player_shield_frame(int view); /* streamed resident view; draw with returned frame */
int player_shield_palette(int view);

#endif

#ifndef ENEMY_H
#define ENEMY_H
#include "gba.h"
#include "actor.h"

enum { EN_BEETLE, EN_BAT, EN_SPITTER, EN_SLIME, EN_KNIGHT, EN_BOSS,
    EN_GILT_LEECH, EN_ROOT_MAW, EN_RELIQUARY_SNOUT, EN_COUNT };
/* Historical lab names remain stable for saved diagnostics and capture tools. */
#define EN_PROTO_ROPE EN_GILT_LEECH
#define EN_PROTO_LEEVER EN_ROOT_MAW
#define EN_PROTO_HELMASAUR EN_RELIQUARY_SNOUT

typedef struct {
    u8 sheet;
    u8 hp;
    u16 speed;   /* Q8.8 */
    u8 damage;
    u8 hitbox;
    u8 flags;
    u8 drop;     /* drop table id */
} EnemyDef;

extern const EnemyDef gEnemyDefs[EN_COUNT];

Actor* enemy_spawn(int type, int px, int py);
void enemies_update(void);
void enemies_draw(void);
/* Dedicated native-frame upload queue, flushed during VBlank. */
void enemies_flush_frames(void);
void enemy_hurt(Actor* e, int damage, int from_dir, int knockback);
void enemy_kill(Actor* e);
int enemies_alive(void);
void enemy_load_sheets_for_theme(int theme);
int enemy_pick_type(int theme, int stage, u32 roll);
/* Read-only selected presentation frames; review never assigns these. */
extern u8 gEnemyPresentedFrame[ACTOR_MAX];

#endif

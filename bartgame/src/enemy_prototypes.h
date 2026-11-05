#ifndef ENEMY_PROTOTYPES_H
#define ENEMY_PROTOTYPES_H
#include "actor.h"

/* Actor.state and timer are observable lab evidence, never review inputs.
   All timers count update ticks; ordinary hit knockback pauses the AI. */
enum { EP_ROAM, EP_TELL, EP_ATTACK, EP_RECOVER,
       EP_BURIED, EP_EMERGE, EP_EXPOSED, EP_RETREAT };
enum { EP_EVENT_ROPE_CHARGE, EP_EVENT_MAW_EMERGE, EP_EVENT_ARMOR_BLOCK,
       EP_EVENT_HIT, EP_EVENT_UNSAFE, EP_EVENT_MAW_BURY,
       EP_EVENT_SNOUT_CHARGE, EP_EVENT_COUNT };
extern u16 gEnemyPrototypeEvents[EP_EVENT_COUNT];
#if BART_ENEMY_LAB
/* Request1..4 selects a single Rope/Leever/Helmasaur, then all three.
   Case, Spawned, Events and fixture positions are read-only diagnostics. */
extern u8 gEnemyPrototypeRequest, gEnemyPrototypeCase, gEnemyPrototypeSpawned;
extern s16 gEnemyPrototypePositions[8]; /* player x/y, then three spawn x/y */

void enemy_prototypes_enter(int case_index);
void enemy_prototypes_tick(void);
#endif
/* Production admission reads existing room geometry; never carves it. */
bool8 enemy_prototypes_spawn_point(int type, int* x, int* y);
void enemy_prototypes_init(Actor* e);
void enemy_prototypes_update(Actor* e);
void enemy_prototypes_recoil(Actor* e);
bool8 enemy_prototypes_accept_hit(Actor* e, int damage, int from_dir);
#endif

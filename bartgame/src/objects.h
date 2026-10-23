#ifndef OBJECTS_H
#define OBJECTS_H
#include "gba.h"
#include "actor.h"

/* projectiles */
enum { PJ_SEED, PJ_SPORE, PJ_SHARD };
/* pickups: frames in the items sheet */
enum { PK_HEART, PK_GILT, PK_BOMB, PK_GILT_BIG, PK_KEY, PK_RELIC };
/* effects */
enum { FX_PUFF, FX_CLANG, FX_BLAST, FX_FLAME, FX_SPARK, FX_BOMB_OBJ };

Actor* proj_spawn(int type, int px, int py, int dir, int speed, int damage, bool8 from_player);
Actor* pickup_spawn(int type, int px, int py);
Actor* fx_spawn(int type, int px, int py);
void drop_roll(int px, int py, u32 roll);
void objects_update(void);
void objects_draw(void);
void objects_room_reset(void);
void bomb_place(int px, int py);
int bombs_live(void);

#endif

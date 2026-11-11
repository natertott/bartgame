#ifndef BOMB_THROW_H
#define BOMB_THROW_H
#include "actor.h"
#define OBJ_IMPACT_BOMB 21
extern u8 gBombChargeTicks;
extern u16 gBombChargeKey;
int bomb_throw_range(int held_ticks);
Actor* bomb_throw_spawn(int px,int py,int facing,int range);
Actor* bomb_throw_remote_spawn(int px,int py,int facing,int range);
void bomb_throw_update(Actor* a);
void bomb_throw_draw(Actor* a);
void bomb_charge_update(void);
void bomb_charge_cancel(void);
void bomb_charge_draw(bool8 behind);
int bomb_throw_remote_count(void);
void bomb_throw_remote_detonate(void);
#endif

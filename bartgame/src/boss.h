#ifndef BOSS_H
#define BOSS_H
#include "gba.h"
#include "actor.h"

void boss_spawn(int px, int py);
void boss_update(Actor* e);
void boss_draw(Actor* e);
void boss_defeated(Actor* e);
void boss_died(Actor* e);
bool8 boss_is_dying(void);
u8 boss_presentation_frame(const Actor* e);

#endif

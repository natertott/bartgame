#ifndef NPC_H
#define NPC_H
#include "gba.h"
#include "actor.h"

enum { NPC_SAGE, NPC_MERCHANT, NPC_HERMIT, NPC_NUN, NPC_GARDENER, NPC_STRANGER, NPC_COUNT };

Actor* npc_spawn(int type, int px, int py);
void npc_room_reset(void);
void npcs_update(void);
void npcs_draw(void);
bool8 npc_try_talk(void);     /* A pressed: start a conversation if one is near */
void npc_dialogue_update(void); /* runs while a conversation owns the frame */
bool8 npc_dialogue_active(void);

#endif

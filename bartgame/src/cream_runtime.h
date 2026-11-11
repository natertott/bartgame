#ifndef CREAM_RUNTIME_H
#define CREAM_RUNTIME_H
#include "gba.h"
#include "cream_world.h"
#include "actor.h"
typedef struct {
    u32 seed,visited,chests[2],cleared[2],healed[2];
    u8 rewards,boss_dead,node,reserved;
} CreamProgress;
extern CreamProgress gCreamProgress;
extern u8 gCreamNode;
void cream_runtime_new_run(u32 seed);
u8 cream_runtime_tokens(void);
void cream_runtime_build(int node);
void cream_runtime_enter(void);
void cream_runtime_room_reset(void);
bool8 cream_runtime_pre_player(void);
void cream_runtime_update(void);
bool8 cream_runtime_interact(void);
void cream_runtime_draw(void);
bool8 cream_runtime_draw_player(void);
void cream_runtime_drop(int rows);
void cream_runtime_return(void);
void cream_runtime_track_enemy(Actor* enemy,const Actor* parent);
#endif

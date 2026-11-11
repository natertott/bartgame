#ifndef WORLD_TOKENS_H
#define WORLD_TOKENS_H
#include "gba.h"
#include "roomgen.h"
#define WT_NO_SITE 255u
enum { WT_BOSS_HEART=1, WT_BOSS_CREAM=2 };
/* A query is a conjunction. It does not spend keys or mutate puzzle state.
   Old items occupy low8 bits and items2 occupy high8 bits. Zero legacy ID,
   zero masks/counts and WT_NO_SITE mean that fact is not required. */
typedef struct {
    u16 old_items;
    u8 legacy_item, keys, fusions, gold;
    u8 switch_site, switch_mask, puzzle_site, boss_flags;
} WorldTokenNeed;
WorldTokenNeed world_tokens_empty(void);
bool8 world_tokens_meet(const WorldTokenNeed* need);
bool8 world_tokens_cream_open(u8 required);
u8 world_tokens_cream_mask(void);
enum { WH_CUT, WH_DIG, WH_BOMB };
/* On the actual current room, find an eligible feature with a dry reachable
   front. Ring search is deterministic and bounded to8; FALSE means callers
   must provide a visible fallback rather than hide content in invalid terrain. */
bool8 world_hidden_find(int kind,Spot origin,Spot start,int rings,Spot* out);
bool8 world_hidden_reachable(int kind,Spot candidate,Spot start);
#endif

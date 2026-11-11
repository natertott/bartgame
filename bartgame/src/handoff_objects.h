#ifndef HANDOFF_OBJECTS_H
#define HANDOFF_OBJECTS_H
#include "gba.h"
/* Reachable annex mechanism courses. Rendering/verbs are independent of old
   mystery rooms and terrain art. handoff_events owns dispatch exclusively. */
void handoff_objects_reset(void);
void handoff_objects_build(u32 seed);
/* Seeded, single-purpose regional interiors. Each has a permanent south exit
   and a reachable reward goal beyond its own mechanism, not a workshop menu. */
#define HANDOFF_REGIONAL_MECHANISMS 12
void handoff_objects_build_regional(u32 seed,int pattern);
bool8 handoff_objects_can_solve(int pattern);
bool8 handoff_objects_field_can_solve(int variant);
/* Small optional field objectives use only OBJ art over reserved dry ground. */
bool8 handoff_objects_build_field(u32 seed,int variant,int x,int y,int w,int h);
bool8 handoff_objects_build_fusion(u32 seed,int x,int y,int w,int h);
void handoff_objects_enter(void);
bool8 handoff_objects_pre_player(void);
void handoff_objects_update(void);
void handoff_objects_draw(void);
void handoff_objects_flush_frames(void);
bool8 handoff_objects_box_solid(int x0,int y0,int x1,int y1);
void handoff_objects_tool_box(int kind,int x0,int y0,int x1,int y1);
bool8 handoff_objects_support(int px,int py);
bool8 handoff_objects_complete(void);
int handoff_objects_variant(void);
#endif

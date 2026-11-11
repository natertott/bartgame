#ifndef HANDOFF_OBJECTS_H
#define HANDOFF_OBJECTS_H
#include "gba.h"
/* Reachable annex mechanism courses. Rendering/verbs are independent of old
   mystery rooms and terrain art. handoff_events owns dispatch exclusively. */
void handoff_objects_reset(void);
void handoff_objects_build(u32 seed);
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

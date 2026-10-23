#ifndef ROOMGEN_H
#define ROOMGEN_H
#include "gba.h"

#define FOREST_W 32
#define FOREST_H 24

/* places the generator found for things, in metatiles */
typedef struct {
    u8 x, y;
} Spot;

typedef struct {
    Spot spawns[12];
    u8 spawn_count;
    Spot chest;
    Spot npc;
    Spot relic;
    Spot torches[4];
    u8 torch_count;
    Spot boss;
    Spot shrine;
    Spot treasure;  /* the alcove's hoard, behind a bush or a boulder */
    Spot mouth;     /* the mystery's mouth in a wall */
    u8 has_chest, has_npc, has_relic, has_boss, has_shrine, has_treasure, has_mouth;
} RoomSpots;

extern RoomSpots gSpots;

void roomgen_build(int cell);
void roomgen_door_pos(int side, int* px, int* py);
void roomgen_gate_tiles(int side, int* x0, int* y0, int* x1, int* y1);

#endif

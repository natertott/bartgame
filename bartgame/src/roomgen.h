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
    /* Appended: old probe/save offsets above stay unchanged. */
    Spot pocket_gate;
    u8 pocket_kind; /* 1 bombs, 2 candle, 3 cape; optional, never progression */
} RoomSpots;

extern RoomSpots gSpots;

void roomgen_build(int cell);
bool8 roomgen_blighted(int cell); /* drawn in the blight's colours */
/* the cell's mask and trail lines as the build lays them, for the map:
   M_* values (roomgen.c) per tile, row-major 32x24 */
void roomgen_preview(int cell, const u8** mask, const u8** path);
/* Exact event positions for a charted room, without visiting it or changing
   the live room, saved discovery marks, RNG or video memory. Same x+1/y+1
   pairs as World.mark; callers enforce their map/discovery permissions. */
void roomgen_preview_events(int cell, u8* marks);
void roomgen_preview_details(int cell, u8* marks, const u8** mask, const u8** path);
void roomgen_door_pos(int side, int* px, int* py);
void roomgen_gate_tiles(int side, int* x0, int* y0, int* x1, int* y1);

#endif

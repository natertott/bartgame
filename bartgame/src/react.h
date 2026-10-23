#ifndef REACT_H
#define REACT_H
#include "gba.h"

/* Tiles reacting to tools: the only way doors open in this game. */
void room_crack_open(int tx, int ty);
void room_web_burn(int tx, int ty);
bool8 room_door_unlock(int tx, int ty);
void room_torch_light(int tx, int ty);
void room_thorn_cut(int tx, int ty);
void react_cut_box(int x0, int y0, int x1, int y1);
void react_burn_box(int x0, int y0, int x1, int y1);
int room_torches_unlit(void);
int tile_gate_side(int tx, int ty);
int room_lift(int tx, int ty);
void room_break_lift(int tx, int ty);

#endif

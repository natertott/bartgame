#ifndef CREAM_ROOM_H_INCLUDED
#define CREAM_ROOM_H_INCLUDED
#include "gba.h"
#include "cream_world.h"
#include "roomgen.h"

#define CREAM_ROOM_W 32
#define CREAM_ROOM_H 24
#define CREAM_SPAWN_MAX 6
/* An explicit edge describes the visual action as well as its target. A local
   physical climb only changes the active component: it must not reload actors. */
enum { CCR_NONE, CCR_WALK, CCR_CLIMB, CCR_DROP, CCR_CAVE, CCR_LOCAL_UP, CCR_LOCAL_DOWN };
typedef struct {
    u8 edge, mode, target, rows;
    s16 x,y; /* requested landing point in the target room */
} CreamRoomRoute;
typedef struct {
    Spot spawns[CREAM_SPAWN_MAX];
    u8 spawn_count, content;
    Spot chest,npc,heal,cache,mission;
} CreamTerraceSpots;
typedef struct {
    u8 cell, stage, motif, climb_x;
    u8 upper_bottom[CREAM_ROOM_W], lower_top[CREAM_ROOM_W];
    CreamTerraceSpots terrace[2];
    Spot return_door; /* entry-only, lower-left tile of the visible hub arch */
} CreamRoomInfo;
extern CreamRoomInfo gCreamRoom;
/* Persistent physical gates: one bit per outgoing graph edge, reset on a new
   generated area and included in the new-area save extension by the caller. */
extern u8 gCreamOpenEdges[CC_NODES];
void cream_room_reset_progress(void);
void cream_room_build(int cell);
u16 cream_room_floor(int tx,int ty);
int cream_room_terrace_at(int px,int py,int current);
/* Optional visitors must not occupy another feature's A-interaction front. */
bool8 cream_room_feature_reserved(int tx,int ty);
bool8 cream_room_node_floor(int node,int tx,int ty);
bool8 cream_room_route(int node,int px,int py,int facing,u16 intent,CreamRoomRoute* out);
void cream_room_arrival(int from_node,const CreamEdge* edge,int* px,int* py,int* facing);
/* React calls this after removing a gate tile. All cells belonging to the
   physical gate clear together, and later visits retain the open route. */
bool8 cream_room_gate_cleared(int tx,int ty);
bool8 cream_room_unlock_edge(int node,int edge_index);
void cream_room_set_chest_open(int node,bool8 opened);
/* Exact feature footprints/fronts for the area's reach/content validator. */
/* Pure selected-room map data. Labels:0blocked,1lower,2upper,3climb,4cave,5drop,6gate. */
void cream_room_preview(int cell,CreamRoomInfo* out,u8 mask[CREAM_ROOM_W*CREAM_ROOM_H]);
void cream_room_cave_pos(int terrace,int* px,int* py);
void cream_room_drop_pos(int node,int edge_index,int* px,int* py);
#endif

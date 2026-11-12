#ifndef CREAM_TOPOLOGY_H_INCLUDED
#define CREAM_TOPOLOGY_H_INCLUDED
#include "assets.h"
#include "cream_room.h"

#define CREAM_TOPO_CELLS (CREAM_ROOM_W*CREAM_ROOM_H)
#define CREAM_TOPO_LINK_MAX 8
enum {
    CT_HEIGHT_MASK=7, CT_UPPER=8, CT_SUPPORT=16, CT_CLIMB=32,
    CT_RESERVED=64, CT_DROP=128
};
enum {
    CT_OPEN_SHELF, CT_FOLDED_STAIR, CT_BROKEN_MESA, CT_SWITCHBACK,
    CT_HIGH_GROTTO, CT_NARROW_SPURS, CT_DOUBLE_RIDGE, CT_PEAK_ARENA,
    CT_ARCHETYPES
};
typedef struct {
    u8 x,top,bottom,owner,top_height,bottom_height;
} CreamTopologyClimb;
typedef struct {
    s16 x,y,landing_x,landing_y;
    u8 owner,height;
} CreamTopologyDrop;
typedef struct {
    u8 x,y,w,h,owner,height,content;
} CreamTopologyPlatform;
typedef struct {
    u8 active,cell,archetype,platforms,climbs,drops,max_height;
    /* Packed native-cell support, owner, true physical level and reservations.
       Unchanged macro climb has height7: defer component until its floor exit. */
    u8 cells[CREAM_TOPO_CELLS];
    CreamTopologyPlatform platform[CREAM_TOPO_LINK_MAX];
    CreamTopologyClimb climb[CREAM_TOPO_LINK_MAX];
    CreamTopologyDrop drop[CREAM_TOPO_LINK_MAX];
} CreamTopology;
extern CreamTopology gCreamTopology;

void cream_topology_prepare(void);
void cream_topology_apply(void);
void cream_topology_sync(void);
int cream_topology_component_at(int px,int py,int fallback);
bool8 cream_topology_local_drop(int px,int py,int facing,u16 intent,
                               int* lx,int* ly,int* height);
bool8 cream_topology_reserved(int tx,int ty);
int cream_topology_height_at(int tx,int ty);
/* Pure core-room preview. Does not call room_set/render or modify live state.
   Supplied info receives the same relocated feature coordinates as live apply. */
void cream_topology_preview(int cell,CreamRoomInfo* info,CreamTopology* out);

#endif

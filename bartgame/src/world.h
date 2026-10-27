#ifndef WORLD_H
#define WORLD_H
#include "gba.h"
#include "util.h"

/* The Blighted Wood: a MAZE_W x MAZE_H grid of cells. Each cell is a
   room; each side is a gate. The world is a pure function of the seed. */
#define MAZE_W 5
#define MAZE_H 5
#define CELLS (MAZE_W * MAZE_H)
#define SIDE_N 0
#define SIDE_E 1
#define SIDE_S 2
#define SIDE_W 3

enum { GATE_WALL, GATE_OPEN, GATE_THORN, GATE_CRACK, GATE_WEB, GATE_LOCK, GATE_CHASM, GATE_EXIT };
enum { ROLE_NONE, ROLE_ENTRY, ROLE_GOAL, ROLE_KEYITEM, ROLE_CHEST, ROLE_NPC_HUNT, ROLE_NPC_FETCH,
       ROLE_NPC_TORCH, ROLE_RELIC, ROLE_SHRINE, ROLE_KEYCHEST };
enum { ARCH_GLADE, ARCH_GROVE, ARCH_RUINS, ARCH_POND, ARCH_THICKET, ARCH_BONEYARD, ARCH_ARENA, ARCH_ENTRY, ARCH_COUNT };
enum { CHEST_GILT, CHEST_HEART_PIECE, CHEST_BOMBS, CHEST_KEY, CHEST_HEART_CONTAINER, CHEST_GAUNTLET, CHEST_BOW, CHEST_MAP, CHEST_ASTROLABE };
enum { THEME_BUGS, THEME_BLIGHT, THEME_DEAD, THEME_MIXED };

/* cell flags: run state */
#define CF_VISITED 0x01
#define CF_CHEST_OPEN 0x02
#define CF_QUEST_DONE 0x04
#define CF_ITEM_TAKEN 0x08
#define CF_RELIC_TAKEN 0x10
#define CF_CLEARED 0x20
#define CF_QUEST_ACTIVE 0x40
#define CF_SHRINE_USED 0x80
/* what the map marks in a visited cell, as pairs in World.mark */
enum { MP_MOUTH, MP_NPC, MP_CHEST, MP_RELIC, MP_SHRINE, MP_COUNT };

/* in Cell.opened above the four gate bits */
#define CELL_LOOTED 0x10 /* the alcove's hoard is taken */
#define CELL_POCKET_OPEN 0x20 /* an internal item-gated pocket is open */

typedef struct {
    u8 gate[4];
    u8 opened;   /* bit per side: a lock, crack or web that is open now */
    u8 role, role_arg;
    u8 stage;
    u8 arch;
    u8 density;
    u8 theme;
    u8 flags;
    u8 dist;     /* tree distance from the entry */
} Cell;

typedef struct {
    u32 seed;
    Cell cells[CELLS];
    u8 entry, goal;
    u8 gate_cell[3], gate_side[3]; /* the three key gates along the main path */
    u8 key_cell[3];                /* where bombs, lamp, cloak are */
    u8 path[CELLS];                /* entry..goal */
    u8 path_len;
    u8 stages;
    u8 myst[CELLS];       /* MYST_PACK(kind, size, style), 0 for none (myst.h) */
    u8 myst_flags[CELLS]; /* MF_* */
    u8 mark[CELLS][MP_COUNT * 2]; /* the map's marks per visited cell: x+1, y+1 pairs, 0 for none */
} World;

extern World gWorld;
extern u8 gWorldGenerationAttempts; /* bounded generation diagnostic */
extern u8 gWorldGenerationFallback; /* a certified skeleton was used */

/* Pacing is in room crossings, including returns for the three event rewards.
   Settings affect generation only; the saved World/Cell layout is unchanged. */
typedef struct {
    u8 min_crossings, max_crossings;
    u8 min_detours, min_optional;
    u8 spine_min, spine_max;
    u8 attempts; /* plus at most one certified fallback for named profiles */
} WorldTuning;
typedef struct {
    u8 spine_edges, required_crossings, required_cells;
    u8 detours, backtrack_edges, max_detour;
} WorldRouteMetrics;
enum { WORLD_FOCUSED, WORLD_BALANCED, WORLD_WANDERING, WORLD_PROFILE_COUNT };
extern const WorldTuning world_profiles[WORLD_PROFILE_COUNT];
void world_generate(u32 seed);
/* Named profiles have certified pacing bounds. Other target combinations are
   best effort under the given budget; inspect world_route_metrics afterward. */
void world_generate_tuned(u32 seed, const WorldTuning* tuning);
void world_route_metrics(WorldRouteMetrics* out);
int cell_neighbor(int cell, int side);
void world_open_gate(int cell, int side);
bool8 world_gate_open(int cell, int side);
int cell_x(int cell);
int cell_y(int cell);
const char* gate_name(int gate);

#endif

#ifndef CREAM_WORLD_H
#define CREAM_WORLD_H
#include "gba.h"

#define CC_WIDTH 5
#define CC_HEIGHT 5
#define CC_ROOMS 25
#define CC_TERRACES 2
#define CC_NODES 50
#define CC_EDGE_MAX 6
#define CC_TOKEN_ALL 7
#define CC_NO_NODE 255

enum { CC_LOWER, CC_UPPER };
enum { CC_EDGE_NONE, CC_WALK, CC_CLIMB, CC_DROP, CC_CAVE };
enum { CC_LONG_DROP=1, CC_LATE_SHORTCUT=2, CC_MISSION_GATE=4 };
enum {
    CC_CONTENT_ENEMIES=1, CC_CONTENT_CHEST=2, CC_CONTENT_NPC=4,
    CC_CONTENT_HEAL=8, CC_CONTENT_CACHE=16, CC_CONTENT_MISSION=32,
    CC_CONTENT_BOSS=64, CC_CONTENT_ENTRY=128
};
/* Capability proofs: Bombs, Lamp, then Cape AND Pacci. Inventory ownership
   lives in the main game; this compact graph never mutates the forest World. */
enum { CC_TOKEN_BOMB=1, CC_TOKEN_LAMP=2, CC_TOKEN_CAPE_PACCI=4 };

typedef struct {
    u8 target;  /* target room*2 + LOWER/UPPER, never an implicit room center */
    u8 kind;   /* WALK, CLIMB, DROP, CAVE */
    u8 require; /* all capability bits required before taking this edge */
    u8 flags;
} CreamEdge;

typedef struct {
    u32 seed;
    u8 entry_node, goal_node;
    u8 reward_node[3];
    u8 attempts, fallback;
    u8 degree[CC_NODES];
    CreamEdge edges[CC_NODES][CC_EDGE_MAX];
    u8 content[CC_NODES];
    u8 stage[CC_NODES];
    u8 corruption[CC_ROOMS]; /* 0 fresh,1 sick,2 deep; peak always2 */
    u8 required_rooms;
    u16 required_steps;
} CreamWorld;

extern CreamWorld gCreamWorld;
static inline int cream_node(int room,int terrace) {return room*2+terrace;}
static inline int cream_cell(int node) {return node/2;}
static inline int cream_terrace(int node) {return node&1;}
int cream_edge_count(int node);
const CreamEdge* cream_edge(int node,int index);
int cream_find_edge(int from,int target);
u8 cream_reward_bit(int node);
u8 cream_collect_tokens(int node,u8 tokens);
bool8 cream_edge_open(const CreamEdge* edge,u8 tokens);
bool8 cream_generate(u32 seed);
bool8 cream_generate_certified(u32 seed); /* explicit checked fallback/control */
bool8 cream_world_validate(void);
/* A legal shortest route with automatic mission completion. Output contains
   explicit component nodes; repetitions expose actual mandatory backtracking. */
int cream_solution(u8 start_tokens,u8* out,int capacity);
#endif

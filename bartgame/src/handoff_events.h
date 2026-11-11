#ifndef HANDOFF_EVENTS_H
#define HANDOFF_EVENTS_H
#include "gba.h"
#include "actor.h"

/* Added optional annex/interiors; old mystery kinds and saved IDs stay intact. */
enum {
    HS_HUB, HS_ITEM, HS_MINIBOSS, HS_NPC, HS_WAVES, HS_POTS, HS_FAIRY,
    HS_MEMORY_SHOW, HS_MEMORY_INPUT, HS_SWITCHES, HS_BLOCK_TEMPLATE,
    HS_BLOCK_MAZE, HS_TORCHES, HS_CLEANUP, HS_SURVIVE, HS_ARENA,
    HS_QUEST_POT, HS_QUEST_HUNT, HS_QUEST_SCAV, HS_QUEST_STEALTH,
    HS_QUEST_CARRY, HS_QUEST_COURIER, HS_QUEST_BLOCKS,
    HS_PORTAL, HS_POCKET, HS_BOSS, HS_GOLD_GATE, HS_TRAVERSAL, HS_OBJECT_COURSE, HS_COUNT
};
enum { HQ_NONE, HQ_POT, HQ_HUNT, HQ_SCAV, HQ_STEALTH, HQ_CARRY, HQ_COURIER, HQ_BLOCKS };
enum { HC_NONE, HC_EVENT, HC_WAVE, HC_BOSS, HC_QUEST, HC_ITEM };
enum { HN_EVENT, HN_WAVE, HN_BOSS, HN_QUEST, HN_ITEM };
enum { HF_SWORD_KNOCKBACK, HF_WALK_SPEED, HF_STEADFAST, HF_CURSE_KNOCKBACK,
       HF_CURSE_ENEMY_SPEED, HF_CURSE_FIRE_RATE, HF_IMMUNE_FIRE, HF_IMMUNE_ICE,
       HF_IMMUNE_SHOCK, HF_DROP_GILT, HF_DROP_KINSTONES, HF_DROP_HEARTS,
       HF_CHEAP_SHOP, HF_RARE_LUCK, HF_CURSE_ROT, HF_CURSE_BLUR, HF_CURSE_DIM,
       HF_SWORD_EDGE, HF_CURSE_BLUNT, HF_BEAM_ANY, HF_FLEET, HF_COUNT };
enum { HC_NAYRU=1, HC_FARORE=2, HC_DIN=4 };
enum { HDRAFT_NONE, HDRAFT_RUNNING, HDRAFT_DONE };
#define HTOOL_DIG 32
#define HTOOL_WATER 33
#define HANDOFF_FLEET 0x104
#define HANDOFF_SITE_LIMIT 256
#define HANDOFF_NO_REQUEST 255
#define HANDOFF_CONTRACT_BASE 128
#define HANDOFF_OBJECT_SITE1 29
#define HANDOFF_OBJECT_SITE2 30
#define HANDOFF_OBJECT_SITE3 31
#define HANDOFF_GOLD_FLOW 0x100
#define HANDOFF_GOLD_LEFT 0x101
#define HANDOFF_GOLD_MIDDLE 0x102
#define HANDOFF_GOLD_RIGHT 0x103

typedef struct {
    u8 kind, state, stake, difficulty;
    u8 origin_area, origin_cell, target_area, target_cell;
    u8 mode, progress, quota, wave;
    u8 cargo_held, cargo_ground, cargo_flying, reserved;
    u16 timer, count;
    s16 cargo_x, cargo_y, receiver_x, receiver_y;
} HandoffQuest;

typedef struct {
    /* Cross-run meta portion: parent persists this independently of run erasure. */
    u32 score;
    u16 wins, deaths, runs;
    u8 difficulty, highest_difficulty, entitlement_mode, rank;
    u32 food_mask;
    u8 charm_mask, draft_round, draft_state, gold_owned;
    u8 gold_fused, fusion_flags, heart_purchases, contract_step;
    u8 contract_kind, contract_state, contract_target;
    u8 shop_bought, memory_known;
    u8 memory_code[6], memory_length, memory_pair;
    u16 contract_item, draft[3], stock[6], prices[6], inn_reward;
    u8 kinstone_shapes[3][3];
    u8 fuser_cell[3], fuser_shape[3];
    u8 completed[32], won[32], visited[32];
    u16 wave[HANDOFF_SITE_LIMIT];
    u16 remaining[HANDOFF_SITE_LIMIT];
    HandoffQuest quest;
} HandoffState;
extern HandoffState gHandoffState;

/* Root extension-save owns serialization; these never write run SRAM. */
void handoff_init(void);
void handoff_new_run(u32 seed);
void handoff_on_win(void);
void handoff_on_death(void);
void handoff_room_enter(int area,int cell);
void handoff_build(int site,int kind,u32 seed);
void handoff_enter(void); /* after player_init and sprite reset */
void handoff_start_pos(int* px,int* py);
void handoff_update(void);
void handoff_draw(void);
bool8 handoff_try_interact(void);
bool8 handoff_pre_player(void);
bool8 handoff_box_solid(int x0,int y0,int x1,int y1);
bool8 handoff_wants_exit(void);
int handoff_requested_site(void);
void handoff_clear_request(void);
int handoff_current_site(void);
int handoff_current_kind(void);
bool8 handoff_menu_active(void);
void handoff_menu_update(void);

void handoff_notify(int kind,int area,int cell,int item);
void handoff_tile_cleared(int tx,int ty);
void handoff_tool_box(int kind,int x0,int y0,int x1,int y1);
void handoff_cargo_thrown(Actor* object);
bool8 handoff_cargo_land(Actor* object);
void handoff_on_enemy_killed(int type,int px,int py);
void handoff_kinstone_drop(int color,int shape,int px,int py);
int handoff_map_mark(int area,int cell); /* fuser/pocket marker, Compass only */

bool8 handoff_apply_item_effect(int item,int amount);
int handoff_outgoing_damage(int damage);
int handoff_incoming_damage(int damage);
int handoff_walk_speed(int speed);
int handoff_enemy_speed(int speed);
int handoff_enemy_fire_delay(int ticks);
int handoff_player_knockback(int speed);
int handoff_sword_knockback(int speed);
int handoff_immunities(void); /* fire1, ice2, shock4 */
bool8 handoff_beam_any_health(void);
int handoff_shop_price(int price);
int handoff_drop_bias(int kind); /* gilt0, kinstone1, heart2, rare3 */
int handoff_visual_dim(void);
int handoff_pick_enemy(int difficulty,int role_mask,u32 roll);
bool8 handoff_item_unlocked(int item);
bool8 handoff_event_unlocked(int kind);
bool8 handoff_region_unlocked(int area);
int handoff_difficulty_cap(void);
u8 handoff_switch_facts(int site);

/* Real push puzzle data and deterministic solver-backed pool. */
#define HANDOFF_BLOCKS 3
#define HANDOFF_PUZZLE_COUNT 1528
#define HANDOFF_SOLUTION_MAX 32

typedef struct {
    u32 walls, goals;
    u8 blocks[3], axes[3]; /* axis0free,1horizontal,2vertical */
    u8 player, entry, goal, kind;
    u8 minimum, length;
    u8 solution[HANDOFF_SOLUTION_MAX]; /* blockIndex*4+N/E/S/W */
} HandoffPuzzle;
const HandoffPuzzle* handoff_puzzle(int index);
bool8 handoff_puzzle_verify(const HandoffPuzzle* puzzle);
bool8 handoff_board_push(int direction);
void handoff_board_reset(void);
extern u16 gHandoffPuzzleIndex, gHandoffPushes;
extern u8 gHandoffBoardBlocks[3], gHandoffBoardPlayer, gHandoffBoardSolved;
#endif

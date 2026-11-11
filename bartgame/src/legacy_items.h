#ifndef LEGACY_ITEMS_H
#define LEGACY_ITEMS_H
#include "gba.h"
#include "actor.h"

/* Stable original vocabulary. These are independent of PlayerState's saved
   eight original equip/inventory IDs and are appended, never substituted. */
enum LegacyItem {
    LI_NONE = 0x00,
    LI_SMITH_SWORD = 0x01,
    LI_GREEN_SWORD = 0x02,
    LI_RED_SWORD = 0x03,
    LI_BLUE_SWORD = 0x04,
    LI_UNUSED_SWORD = 0x05,
    LI_FOURSWORD = 0x06,
    LI_BOMBS = 0x07,
    LI_REMOTE_BOMBS = 0x08,
    LI_BOW = 0x09,
    LI_LIGHT_ARROW = 0x0A,
    LI_BOOMERANG = 0x0B,
    LI_MAGIC_BOOMERANG = 0x0C,
    LI_SHIELD = 0x0D,
    LI_MIRROR_SHIELD = 0x0E,
    LI_LANTERN_OFF = 0x0F,
    LI_LANTERN_ON = 0x10,
    LI_GUST_JAR = 0x11,
    LI_PACCI_CANE = 0x12,
    LI_MOLE_MITTS = 0x13,
    LI_ROCS_CAPE = 0x14,
    LI_PEGASUS_BOOTS = 0x15,
    LI_FIRE_ROD = 0x16,
    LI_OCARINA = 0x17,
    LI_ORB_GREEN = 0x18,
    LI_ORB_BLUE = 0x19,
    LI_ORB_RED = 0x1A,
    LI_TRY_PICKUP_OBJECT = 0x1B,
    LI_BOTTLE1 = 0x1C,
    LI_BOTTLE2 = 0x1D,
    LI_BOTTLE3 = 0x1E,
    LI_BOTTLE4 = 0x1F,
    LI_BOTTLE_EMPTY = 0x20,
    LI_BOTTLE_BUTTER = 0x21,
    LI_BOTTLE_MILK = 0x22,
    LI_BOTTLE_HALF_MILK = 0x23,
    LI_BOTTLE_RED_POTION = 0x24,
    LI_BOTTLE_BLUE_POTION = 0x25,
    LI_BOTTLE_WATER = 0x26,
    LI_BOTTLE_MINERAL_WATER = 0x27,
    LI_BOTTLE_FAIRY = 0x28,
    LI_BOTTLE_PICOLYTE_RED = 0x29,
    LI_BOTTLE_PICOLYTE_ORANGE = 0x2A,
    LI_BOTTLE_PICOLYTE_YELLOW = 0x2B,
    LI_BOTTLE_PICOLYTE_GREEN = 0x2C,
    LI_BOTTLE_PICOLYTE_BLUE = 0x2D,
    LI_BOTTLE_PICOLYTE_WHITE = 0x2E,
    LI_CHARM_NAYRU = 0x2F,
    LI_CHARM_FARORE = 0x30,
    LI_CHARM_DIN = 0x31,
    LI_32 = 0x32,
    LI_33 = 0x33,
    LI_QST_SWORD = 0x34,
    LI_QST_BROKEN_SWORD = 0x35,
    LI_QST_DOGFOOD = 0x36,
    LI_QST_LONLON_KEY = 0x37,
    LI_QST_MUSHROOM = 0x38,
    LI_QST_BOOK1 = 0x39,
    LI_QST_BOOK2 = 0x3A,
    LI_QST_BOOK3 = 0x3B,
    LI_QST_GRAVEYARD_KEY = 0x3C,
    LI_QST_TINGLE_TROPHY = 0x3D,
    LI_QST_CARLOV_MEDAL = 0x3E,
    LI_SHELLS = 0x3F,
    LI_EARTH_ELEMENT = 0x40,
    LI_FIRE_ELEMENT = 0x41,
    LI_WATER_ELEMENT = 0x42,
    LI_WIND_ELEMENT = 0x43,
    LI_GRIP_RING = 0x44,
    LI_POWER_BRACELETS = 0x45,
    LI_FLIPPERS = 0x46,
    LI_MAP = 0x47,
    LI_SKILL_SPIN_ATTACK = 0x48,
    LI_SKILL_ROLL_ATTACK = 0x49,
    LI_SKILL_DASH_ATTACK = 0x4A,
    LI_SKILL_ROCK_BREAKER = 0x4B,
    LI_SKILL_SWORD_BEAM = 0x4C,
    LI_SKILL_GREAT_SPIN = 0x4D,
    LI_SKILL_DOWN_THRUST = 0x4E,
    LI_SKILL_PERIL_BEAM = 0x4F,
    LI_DUNGEON_MAP = 0x50,
    LI_COMPASS = 0x51,
    LI_BIG_KEY = 0x52,
    LI_SMALL_KEY = 0x53,
    LI_RUPEE1 = 0x54,
    LI_RUPEE5 = 0x55,
    LI_RUPEE20 = 0x56,
    LI_RUPEE50 = 0x57,
    LI_RUPEE100 = 0x58,
    LI_RUPEE200 = 0x59,
    LI_5A = 0x5A,
    LI_JABBERNUT = 0x5B,
    LI_KINSTONE = 0x5C,
    LI_BOMBS5 = 0x5D,
    LI_ARROWS5 = 0x5E,
    LI_HEART = 0x5F,
    LI_FAIRY = 0x60,
    LI_SHELLS30 = 0x61,
    LI_HEART_CONTAINER = 0x62,
    LI_HEART_PIECE = 0x63,
    LI_WALLET = 0x64,
    LI_BOMBBAG = 0x65,
    LI_LARGE_QUIVER = 0x66,
    LI_KINSTONE_BAG = 0x67,
    LI_BRIOCHE = 0x68,
    LI_CROISSANT = 0x69,
    LI_PIE = 0x6A,
    LI_CAKE = 0x6B,
    LI_BOMBS10 = 0x6C,
    LI_BOMBS30 = 0x6D,
    LI_ARROWS10 = 0x6E,
    LI_ARROWS30 = 0x6F,
    LI_ARROW_BUTTERFLY = 0x70,
    LI_DIG_BUTTERFLY = 0x71,
    LI_SWIM_BUTTERFLY = 0x72,
    LI_SKILL_FAST_SPIN = 0x73,
    LI_SKILL_FAST_SPLIT = 0x74,
    LI_SKILL_LONG_SPIN = 0x75,
    LI_COUNT,
    /* Source explicitly calls these drop values, not item inventory IDs. */
    LI_KINSTONE_RED=0xFC, LI_KINSTONE_BLUE, LI_KINSTONE_GREEN, LI_ENEMY_BEETLE
};

enum { LCAT_KEY=1, LCAT_REWARD=2, LCAT_WEAPON=4, LCAT_SKILL=8,
       LCAT_STAT=16, LCAT_CHARM=32, LCAT_QUEST=64 };
enum { LIF_REPEAT=1, LIF_HIDDEN=2, LIF_PASSIVE=4 };
/* Append equip IDs without changing the original EQ_COUNT==8 contract. */
enum { EQ_REMOTE_BOMBS=8, EQ_LIGHT_ARROW, EQ_BOOMERANG, EQ_MAGIC_BOOMERANG,
       EQ_MIRROR_SHIELD, EQ_GUST_JAR, EQ_PACCI_CANE, EQ_MOLE_MITTS,
       EQ_PEGASUS_BOOTS, EQ_FIRE_ROD, EQ_OCARINA, EQ_BOTTLE1, EQ_BOTTLE2,
       EQ_BOTTLE3, EQ_BOTTLE4, EQ_GREEN_SWORD, EQ_RED_SWORD, EQ_BLUE_SWORD,
       EQ_FOUR_SWORD, EQ_TOTAL };

typedef struct {
    const char* name;
    const char* description;
    u8 equip, category, tier, requirement;
    u8 flags, frame;
} LegacyItemDef;

typedef struct {
    u32 owned[4], seen[4];
    u16 skills, shells;
    u16 kinstones[3];
    u8 bottles[4];
    u8 sword_level, bomb_bag, quiver, dig_upgrade, swim_upgrade, bottle_charm;
    u8 reserved[2];
} LegacyInventory;
extern LegacyInventory gLegacyInventory;
extern const LegacyItemDef gLegacyItemDefs[LI_COUNT];
/* Per-attack context. Root wraps original sword/arrow/bomb/throw sources;
   all new tool projectiles call legacy_item_hit with an explicit weapon. */
extern u8 gLegacyHitKind;

void legacy_items_new_run(void);
void legacy_items_seed_owned(void);
int legacy_item_count(void);
Actor* legacy_item_spawn(int item,int px,int py);
bool8 legacy_items_actor_owned(const Actor* actor);
void legacy_items_actor_update(Actor* actor);
void legacy_items_actor_draw(Actor* actor);
void legacy_items_flush_frames(void);
const LegacyItemDef* legacy_item_def(int item);
bool8 legacy_item_owned(int item);
bool8 legacy_item_seen(int item);
void legacy_item_grant(int item,int amount);
void legacy_item_remove(int item);
bool8 legacy_equip_owned(int equip);
int legacy_equip_item(int equip);
bool8 legacy_equip_sword(int equip);
bool8 legacy_equip_shield(int equip);
int legacy_bomb_capacity(void);
int legacy_arrow_capacity(void);
void legacy_item_hit(Actor* target,int kind,int damage,int direction,int knockback);

/* Root calls pre before player_update; a true result owns movement for this
   tick and normal player_update is skipped. Post follows ordinary movement. */
bool8 legacy_items_pre_player(void);
void legacy_items_post_player(void);
void legacy_items_update(void);
void legacy_items_draw(void);
void legacy_items_room_reset(void);
bool8 legacy_player_handles_floor(int type);
int legacy_player_walk_speed(int q8);
int legacy_player_incoming_damage(int damage);
int legacy_player_outgoing_damage(int damage);
bool8 legacy_player_minish(void);
bool8 legacy_player_submerged(void);
int legacy_player_clone_count(void);
bool8 legacy_player_draw_override(void);

enum { LPS_SLOW, LPS_SILENCE, LPS_FREEZE, LPS_BURN, LPS_SHOCK,
       LPS_DRUGGED, LPS_CAPTURE, LPS_COUNT };
void legacy_player_status_apply(int kind,int ticks);
void legacy_player_capture(Actor* captor,int ticks);
int legacy_player_status(int kind);
void legacy_player_status_clear(int kind);
void legacy_player_on_hurt(void);
bool8 legacy_clone_position(int index,int* x,int* y);
bool8 legacy_minish_gap_at(int px,int py);

/* Surface mechanics supplied by new terrain sets; logical floor types keep
   original IDs and append only. The root renderer supplies these predicates. */
enum { LS_NONE, LS_SHALLOW, LS_ICE, LS_SWAMP, LS_DUST, LS_LAVA, LS_CLIMB,
       LS_LADDER, LS_DIG, LS_DIG_WALL, LS_SPRING, LS_MINISH_PORTAL,
       LS_MINISH_GAP, LS_CLONE_PLATE, LS_CRUMBLE, LS_CONVEYOR_N,
       LS_CONVEYOR_E, LS_CONVEYOR_S, LS_CONVEYOR_W, LS_SLOPE_X, LS_SLOPE_Y,
       LS_DASH_WALL, LS_ICE_BLOCK, LS_WATER_SPROUT, LS_MINECART };
int legacy_surface_at(int px,int py);
void legacy_surface_set(int tx,int ty,int surface);
void legacy_surface_clear(void);
#endif

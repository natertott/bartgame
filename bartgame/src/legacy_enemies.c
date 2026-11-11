/* Additive, source-audited translation of the curated migration roster.
   Original nine enemy IDs, artwork and behavior remain owned by enemy.c. */
#include "legacy_enemies.h"
#include "legacy_items.h"
#include "player.h"
#include "objects.h"
#include "room.h"
#include "video.h"
#include "sound.h"
#include "util.h"
#include "game.h"
#include "handoff_events.h"
#include "cream_runtime.h"

const LegacyEnemyDef gLegacyEnemyDefs[LEGACY_ENEMY_COUNT] = {
    {{SHEET_LEGACY_BEETLE_0,1,256,2,HB_SMALL,AF_HITTABLE|AF_HURTS,0},"Beetle","Clings to Bloom; shake it loose.",0x07,0,1,LF_BEETLE,1,6,33,4},
    {{SHEET_LEGACY_KEESE_0,2,256,2,HB_SMALL,AF_HITTABLE|AF_HURTS|AF_FLYING|AF_PRIO1,0},"Keese","Roosts, flaps, and banks through a low swoop.",0x08,0,1,LF_KEESE,1,6,41,5},
    {{SHEET_LEGACY_SMALL_PESTO_0,1,64,2,HB_SMALL,AF_HITTABLE|AF_HURTS|AF_FLYING|AF_PRIO1,0},"Small Pesto","Small weaving flyer; draw it away from its brood.",0x2D,0,1,LF_SMALL_PESTO,1,6,73,0},
    {{SHEET_LEGACY_TEKTITE_0,3,256,2,HB_MED,AF_HITTABLE|AF_HURTS,0},"Tektite","Crouch foretells the landing point of its hop.",0x26,0,1,LF_TEKTITE,1,6,33,4},
    {{SHEET_LEGACY_CROW_0,2,320,2,HB_SMALL,AF_HITTABLE|AF_HURTS|AF_FLYING|AF_PRIO1,0},"Crow","Perches before a committed diving pass.",0x31,0,1,LF_CROW,1,6,41,5},
    {{SHEET_LEGACY_MINI_SLIME_0,1,128,2,HB_SMALL,AF_HITTABLE|AF_HURTS,0},"Mini Slime","Small soft-bodied hopping remnant.",0x57,0,1,LF_MINI_SLIME,1,6,65,0},
    {{SHEET_LEGACY_OCTOROK_0,2,96,2,HB_SMALL,AF_HITTABLE|AF_HURTS,0},"Octorok","Faces a cardinal lane before spitting; shield reflects its stone.",0x00,0,1,LF_OCTOROK,1,6,69,0},
    {{SHEET_LEGACY_PEAHAT_0,4,128,2,HB_MED,AF_HITTABLE|AF_HURTS|AF_FLYING|AF_PRIO1,0},"Peahat","Whirling propeller protects its airborne body; gust or boomerang grounds it.",0x03,0,1,LF_PEAHAT,1,6,9,0},
    {{SHEET_LEGACY_CHUCHU_0,4,32,2,HB_MED,AF_HITTABLE|AF_HURTS,0},"Chuchu","Jelly crouches before leaping; elemental coats can be stunned.",0x01,0,1,LF_CHUCHU,1,6,65,0},
    {{SHEET_LEGACY_ROPE_0,4,128,2,HB_MED,AF_HITTABLE|AF_HURTS,0},"Rope","Aligns, braces, then rushes in one straight lane.",0x2C,0,1,LF_ROPE,1,6,17,0},
    {{SHEET_LEGACY_OCTOROK2_0,2,96,2,HB_SMALL,AF_HITTABLE|AF_HURTS,0},"Octorok2","Faces a cardinal lane before spitting; shield reflects its stone.",0x55,0,2,LF_OCTOROK,1,6,69,0},
    {{SHEET_LEGACY_OCTOROK_1,3,96,2,HB_MED,AF_HITTABLE|AF_HURTS,0},"Octorok / 1","Faces a cardinal lane before spitting; shield reflects its stone.",0x00,1,2,LF_OCTOROK,1,6,68,0},
    {{SHEET_LEGACY_SLIME_0,2,64,2,HB_SMALL,AF_HITTABLE|AF_HURTS,0},"Slime","A large jelly divides into smaller living jellies.",0x56,0,2,LF_SLIME,1,6,65,0},
    {{SHEET_LEGACY_STALFOS_0,4,224,2,HB_MED,AF_HITTABLE|AF_HURTS,0},"Stalfos","Evades nearby sword strokes; the second form throws bones.",0x42,0,2,LF_STALFOS,1,6,33,3},
    {{SHEET_LEGACY_STALFOS_1,4,224,2,HB_MED,AF_HITTABLE|AF_HURTS,0},"Stalfos / 1","Evades nearby sword strokes; the second form throws bones.",0x42,1,2,LF_STALFOS,1,6,33,3},
    {{SHEET_LEGACY_KEATON_0,4,256,2,HB_MED,AF_HITTABLE|AF_HURTS,0},"Keaton","A feint and sideways step precede its quick cut.",0x30,0,2,LF_KEATON,1,6,33,0},
    {{SHEET_LEGACY_HELMASAUR_0,4,256,2,HB_MED,AF_HITTABLE|AF_HURTS,0},"Helmasaur","Faceplate blocks the front; pull it away with the Gust Jar.",0x20,0,2,LF_HELMASAUR,1,6,32,0},
    {{SHEET_LEGACY_PESTO_0,4,64,2,HB_MED,AF_HITTABLE|AF_HURTS|AF_FLYING|AF_PRIO1,0},"Pesto","Hunts overhead and drops its burden in a visible lane.",0x11,0,2,LF_PESTO,1,6,73,4},
    {{SHEET_LEGACY_CHUCHU_2,4,32,2,HB_MED,AF_HITTABLE|AF_HURTS,0},"Chuchu / 2","Jelly crouches before leaping; elemental coats can be stunned.",0x01,2,2,LF_CHUCHU,1,6,65,2},
    {{SHEET_LEGACY_BOBOMB_0,255,128,2,HB_MED,AF_HITTABLE|AF_HURTS,0},"Bobomb","One hit lights its fuse; another stuns it for carrying.",0x22,0,2,LF_BOBOMB,1,6,64,1},
    {{SHEET_LEGACY_BOMBAROSSA_0,255,256,2,HB_MED,AF_HITTABLE|AF_HURTS|AF_FLYING|AF_PRIO1,0},"Bombarossa","A floating mine bobs in place; knock it into masonry.",0x33,0,2,LF_BOMBAROSSA,1,6,36,1},
    {{SHEET_LEGACY_LEEVER_0,6,128,2,HB_MED,AF_HITTABLE|AF_HURTS,0},"Leever","A soil mound warns of emergence; it returns to burrow.",0x02,0,2,LF_LEEVER,1,6,17,0},
    {{SHEET_LEGACY_MULLDOZER_0,6,96,2,HB_MED,AF_HITTABLE|AF_HURTS,0},"Mulldozer","Notices Bloom and commits to a scuttling charge.",0x32,0,2,LF_MULLDOZER,1,6,64,0},
    {{SHEET_LEGACY_TEKTITE_1,6,320,2,HB_MED,AF_HITTABLE|AF_HURTS,0},"Tektite / 1","Crouch foretells the landing point of its hop.",0x26,1,2,LF_TEKTITE,1,6,32,2},
    {{SHEET_LEGACY_LEEVER_1,8,128,2,HB_MED,AF_HITTABLE|AF_HURTS,0},"Leever / 1","A soil mound warns of emergence; it returns to burrow.",0x02,1,2,LF_LEEVER,1,6,16,2},
    {{SHEET_LEGACY_MOLDORM_0,10,384,2,HB_MED,AF_HITTABLE|AF_HURTS,0},"Moldorm","A fast segmented worm with a soft tail.",0x0D,0,3,LF_MOLDORM,5,2,32,4},
    {{SHEET_LEGACY_GHINI_0,9,256,2,HB_MED,AF_HITTABLE|AF_HURTS|AF_FLYING|AF_PRIO1,0},"Ghini","A waking ghost materializes for a hunting pass.",0x4E,0,3,LF_GHINI,1,6,40,3},
    {{SHEET_LEGACY_ARMOS_0,10,160,2,HB_TALL,AF_HITTABLE|AF_HURTS,0},"Armos","A dormant statue wakes; its back jewel is exposed between stomps.",0x2A,0,3,LF_ARMOS,2,6,80,0},
    {{SHEET_LEGACY_EYEGORE_0,3,256,4,HB_TALL,AF_HITTABLE|AF_HURTS,0},"Eyegore","Only an arrow or beam through the open front eye hurts it.",0x2B,0,3,LF_EYEGORE,2,6,68,0},
    {{SHEET_LEGACY_MULLDOZER_1,8,96,4,HB_MED,AF_HITTABLE|AF_HURTS,0},"Mulldozer / 1","Notices Bloom and commits to a scuttling charge.",0x32,1,3,LF_MULLDOZER,1,6,64,2},
    {{SHEET_LEGACY_PESTO_1,4,64,2,HB_MED,AF_HITTABLE|AF_HURTS|AF_FLYING|AF_PRIO1,0},"Pesto / 1","Hunts overhead and drops its burden in a visible lane.",0x11,1,3,LF_PESTO,1,6,73,4},
    {{SHEET_LEGACY_CHUCHU_1,4,32,2,HB_MED,AF_HITTABLE|AF_HURTS,0},"Chuchu / 1","Jelly crouches before leaping; elemental coats can be stunned.",0x01,1,3,LF_CHUCHU,1,6,65,0},
    {{SHEET_LEGACY_ROCK_CHUCHU_0,4,64,2,HB_MED,AF_HITTABLE|AF_HURTS,0},"Rock Chuchu","Break the rocky coat to expose the soft jelly.",0x0A,0,3,LF_ROCK_CHUCHU,1,6,64,0},
    {{SHEET_LEGACY_SPINY_CHUCHU_0,4,32,2,HB_MED,AF_HITTABLE|AF_HURTS,0},"Spiny Chuchu","Wait for its spikes to retract, or stun it first.",0x0B,0,3,LF_SPINY_CHUCHU,1,6,64,0},
    {{SHEET_LEGACY_SPIKED_BEETLE_0,4,96,2,HB_MED,AF_HITTABLE|AF_HURTS,0},"Spiked Beetle","A shield or Pacci shot overturns the armored shell.",0x1E,0,3,LF_SPIKED_BEETLE,1,6,80,4},
    {{SHEET_LEGACY_PUFFSTOOL_0,1,64,2,HB_SMALL,AF_HITTABLE|AF_HURTS,0},"Puffstool","Vacuum away the mushroom cap before striking the stem.",0x12,0,3,LF_PUFFSTOOL,1,6,65,0},
    {{SHEET_LEGACY_FIREBALL_GUY_0,4,64,2,HB_MED,AF_HITTABLE|AF_HURTS,0},"Fireball Guy","A nonfatal hit divides this hopping flame cluster into two smaller flames.",0x58,0,3,LF_FIREBALL,1,6,4,1},
    {{SHEET_LEGACY_MINI_FIREBALL_GUY_0,1,64,2,HB_SMALL,AF_HITTABLE|AF_HURTS,0},"Mini Fireball Guy","A small hopping flame; fire does not hurt it.",0x59,0,3,LF_MINI_FIREBALL,1,6,5,1},
    {{SHEET_LEGACY_BOMB_PEAHAT_0,4,192,2,HB_MED,AF_HITTABLE|AF_HURTS|AF_FLYING|AF_PRIO1,0},"Bomb Peahat","Hovers over a marked spot before dropping an explosive.",0x1B,0,3,LF_BOMB_PEAHAT,1,6,8,0},
    {{SHEET_LEGACY_CLOUD_PIRANHA_0,4,256,2,HB_MED,AF_HITTABLE|AF_HURTS|AF_FLYING|AF_PRIO1,0},"Cloud Piranha","A quivering cloud precedes an arcing ambush.",0x3F,0,3,LF_CLOUD_PIRANHA,1,6,16,0},
    {{SHEET_LEGACY_SPINY_BEETLE_0,4,352,2,HB_MED,AF_HITTABLE|AF_HURTS,0},"Spiny Beetle","A disguised object grows legs when Bloom comes close.",0x35,0,3,LF_SPINY_BEETLE,1,6,32,4},
    {{SHEET_LEGACY_ENEMY_50_0,9,256,2,HB_MED,AF_HITTABLE|AF_HURTS|AF_FLYING|AF_PRIO1,0},"Mirage Haunt","A lantern-sensitive phantom makes three decoys, then seizes Bloom.",0x50,0,3,LF_UNKNOWN50,4,2,32,0},
    {{SHEET_LEGACY_LIKE_LIKE_0,20,64,2,HB_TALL,AF_HITTABLE|AF_HURTS,0},"Like Like","A swallowing column grabs Bloom and steals a shield.",0x14,0,4,LF_LIKE_LIKE,2,3,194,0},
    {{SHEET_LEGACY_RUPEE_LIKE_0,16,96,2,HB_TALL,AF_HITTABLE|AF_HURTS,0},"Rupee Like","A false coin conceals a greedy swallowing creature.",0x17,0,4,LF_RUPEE_LIKE,2,3,130,0},
    {{SHEET_LEGACY_RUPEE_LIKE_2,16,96,2,HB_TALL,AF_HITTABLE|AF_HURTS,0},"Rupee Like / 2","A false coin conceals a greedy swallowing creature.",0x17,2,4,LF_RUPEE_LIKE,2,3,130,0},
    {{SHEET_LEGACY_RUPEE_LIKE_1,16,96,2,HB_TALL,AF_HITTABLE|AF_HURTS,0},"Rupee Like / 1","A false coin conceals a greedy swallowing creature.",0x17,1,4,LF_RUPEE_LIKE,2,3,130,0},
    {{SHEET_LEGACY_TAKKURI_0,4,320,2,HB_MED,AF_HITTABLE|AF_HURTS|AF_FLYING|AF_PRIO1,0},"Takkuri","A swooping thief carries stolen gilt until defeated.",0x45,0,4,LF_TAKKURI,1,3,168,5},
    {{SHEET_LEGACY_GOBDO_0,20,96,2,HB_TALL,AF_HITTABLE|AF_HURTS,0},"Gibdo","A wrapped grabber; fire burns the wrappings into a skeleton.",0x3B,0,4,LF_GIBDO,2,6,66,3},
    {{SHEET_LEGACY_SCISSORS_BEETLE_0,20,128,2,HB_TALL,AF_HITTABLE|AF_HURTS,0},"Scissors Beetle","Opening pincers attack ahead; its unarmored rear remains vulnerable.",0x40,0,4,LF_SCISSORS,2,6,2,4},
    {{SHEET_LEGACY_MOLDWORM_0,20,128,2,HB_MED,AF_HITTABLE|AF_HURTS,0},"Moldworm","An emerging worm swallows Bloom and carries him along its body.",0x0F,0,4,LF_MOLDWORM,9,1,2,4},
    {{SHEET_LEGACY_ENEMY_4D_0,16,128,4,HB_TALL,AF_HITTABLE|AF_HURTS,0},"Anchor Flailer","An anchored chain guard extends a long flail, pauses, then reels it in.",0x4D,0,4,LF_UNKNOWN4D,2,3,2,0},
    {{SHEET_LEGACY_BOW_MOBLIN_0,8,256,2,HB_MED,AF_HITTABLE|AF_HURTS,0},"Bow Moblin","An archer draws before firing along its facing lane.",0x46,0,4,LF_BOW_MOBLIN,1,6,36,0},
    {{SHEET_LEGACY_SPEAR_MOBLIN_0,8,256,2,HB_MED,AF_HITTABLE|AF_HURTS,0},"Spear Moblin","The spear point marks its thrust; attack the flank during recovery.",0x15,0,4,LF_SPEAR_MOBLIN,1,6,32,0},
    {{SHEET_LEGACY_ACRO_BANDIT_0,1,128,2,HB_SMALL,AF_HITTABLE|AF_HURTS,0},"Acro Bandit","A six-member stack climbs out, hops, and collapses when struck.",0x2E,0,4,LF_ACRO_BANDIT,6,2,1,0},
    {{SHEET_LEGACY_WIZZROBE_FIRE_0,8,192,2,HB_MED,AF_HITTABLE|AF_HURTS,2},"Wizzrobe Fire","Appears, aims a fire spell, then vanishes.",0x28,0,5,LF_WIZZROBE_FIRE,1,6,36,1},
    {{SHEET_LEGACY_WIZZROBE_ICE_0,8,192,2,HB_MED,AF_HITTABLE|AF_HURTS,2},"Wizzrobe Ice","Appears and casts freezing magic down its chosen lane.",0x29,0,5,LF_WIZZROBE_ICE,1,6,36,2},
    {{SHEET_LEGACY_WIZZROBE_WIND_0,8,192,2,HB_MED,AF_HITTABLE|AF_HURTS,2},"Wizzrobe Wind","A visible gust pushes Bloom before the caster vanishes.",0x27,0,5,LF_WIZZROBE_WIND,1,6,36,0},
    {{SHEET_LEGACY_TEKTITE_GOLDEN_0,64,576,2,HB_MED,AF_HITTABLE|AF_HURTS,2},"Tektite Golden","Crouch foretells the landing point of its hop.",0x3D,0,5,LF_TEKTITE,1,6,34,0},
    {{SHEET_LEGACY_OCTOROK_GOLDEN_0,64,96,2,HB_MED,AF_HITTABLE|AF_HURTS,2},"Octorok Golden","Faces a cardinal lane before spitting; shield reflects its stone.",0x3C,0,5,LF_OCTOROK,1,6,70,0},
    {{SHEET_LEGACY_ROPE_GOLDEN_0,64,128,2,HB_MED,AF_HITTABLE|AF_HURTS,2},"Rope Golden","Aligns, braces, then rushes in one straight lane.",0x3E,0,5,LF_ROPE,1,6,18,0},
    {{SHEET_LEGACY_ROLLOBITE_0,255,256,2,HB_MED,AF_HITTABLE|AF_HURTS,2},"Rollobite","A blow curls it into a liftable ball; throw it into a hole.",0x04,0,5,LF_ROLLOBITE,1,6,32,4},
    {{SHEET_LEGACY_WISP_0,255,128,2,HB_MED,AF_HITTABLE|AF_HURTS|AF_FLYING|AF_PRIO1,2},"Wisp","Contact seals item use for ten seconds; boomerang or arrow dispels it.",0x34,0,5,LF_WISP,1,6,8,3},
    {{SHEET_LEGACY_WISP_1,255,384,2,HB_MED,AF_HITTABLE|AF_HURTS|AF_FLYING|AF_PRIO1,2},"Wisp / 1","Contact seals item use for ten seconds; boomerang or arrow dispels it.",0x34,1,5,LF_WISP,1,6,40,3},
    {{SHEET_LEGACY_SPARK_0,255,256,2,HB_MED,AF_HITTABLE|AF_HURTS,2},"Spark","Follows the boundary clockwise; a boomerang releases a fairy.",0x1C,0,5,LF_SPARK,1,6,32,0},
    {{SHEET_LEGACY_LAKITU_0,6,128,2,HB_MED,AF_HITTABLE|AF_HURTS|AF_FLYING|AF_PRIO1,2},"Lakitu","Pacci or gust removes its cloud and exposes the fallen rider.",0x47,0,5,LF_LAKITU,1,6,12,0},
    {{SHEET_LEGACY_DARK_NUT_0,12,96,4,HB_TALL,AF_HITTABLE|AF_HURTS,2},"Dark Nut","Front armor parries; bait its committed sword cut and strike the rear.",0x05,0,6,LF_DARKNUT,2,2,66,0},
    {{SHEET_LEGACY_DARK_NUT_1,12,96,4,HB_TALL,AF_HITTABLE|AF_HURTS,2},"Dark Nut / 1","Front armor parries; bait its committed sword cut and strike the rear.",0x05,1,6,LF_DARKNUT,2,2,66,0},
    {{SHEET_LEGACY_DARK_NUT_2,20,96,4,HB_TALL,AF_HITTABLE|AF_HURTS,2},"Dark Nut / 2","Front armor parries; bait its committed sword cut and strike the rear.",0x05,2,6,LF_DARKNUT,2,2,66,0},
    {{SHEET_LEGACY_DARK_NUT_3,26,96,4,HB_TALL,AF_HITTABLE|AF_HURTS,2},"Dark Nut / 3","Front armor parries; bait its committed sword cut and strike the rear.",0x05,3,6,LF_DARKNUT,2,2,66,0},
    {{SHEET_LEGACY_BALL_CHAIN_SOLIDER_0,16,128,4,HB_TALL,AF_HITTABLE|AF_HURTS,2},"Ball Chain Soldier","The real orbiting flail is dangerous; its rear is open during the throw.",0x4C,0,6,LF_BALL_CHAIN,2,3,2,0},
    {{SHEET_LEGACY_MADDERPILLAR_0,255,224,2,HB_MED,AF_HITTABLE|AF_HURTS,2},"Madderpillar","The armored chain rages after a blow to its exposed tail.",0x18,0,6,LF_MADDERPILLAR,7,1,2,0},
    {{SHEET_LEGACY_GIANT_GREEN,24,128,4,HB_BIG,AF_HITTABLE|AF_HURTS|AF_BOSS,2},"Great Curd Jelly","Peel the gelatin with gusts or repeated weapon strokes; strike the toppled core.",0x13,0,6,LF_GIANT_CHUCHU,12,1,32,0},
    {{SHEET_LEGACY_GIANT_ELECTRIC,32,128,4,HB_BIG,AF_HITTABLE|AF_HURTS|AF_BOSS,2},"Storm Curd Jelly","Its charge must subside before the coat can be peeled; the fallen core is vulnerable.",0x13,4,6,LF_GIANT_CHUCHU,12,1,32,0},
    {{SHEET_LEGACY_BIG_OCTOROK,3,96,4,HB_BIG,AF_HITTABLE|AF_HURTS|AF_BOSS,2},"Great Brine Octorok","Reflect its stones; burn the frozen tail. Weapon hits also advance the original eight-phase fight.",0x39,0,6,LF_BIG_OCTOROK,16,1,32,0},
    {{SHEET_CREAM_BOSS,32,96,4,HB_BIG,AF_HITTABLE|AF_HURTS|AF_BOSS,2},"Peak Curd Wyrm","Flip the plated head with Pacci, climb its bowed back and strike the exposed purple core.",0x24,0,6,LF_GLEEROK,16,1,32,0},
};

/* Actor-local scratch: v0 coat/flip progress, v1 stun, v2 attack phase,
   v3 child marker, v4 parent index, v5 stolen/attachment payload.
   pad[0..3] holds the permanent spawn anchor: movement owns vx/vy.
   Four bounded 24-sample trails serve all multipart families; their pieces
   share a parent health pool and cannot strand invisible living actors. */
enum { LP_IDLE,LP_WALK1,LP_WALK2,LP_TELL,LP_ATTACK,LP_RECOVER,LP_HURT,LP_BURIED };
enum { ST_REST,ST_ROAM,ST_TELL,ST_ATTACK,ST_RECOVER,ST_HIDDEN,ST_RISE,
       ST_EXPOSED,ST_STUN,ST_CAPTURE,ST_CURL,ST_CARRY,ST_THROWN,ST_RETURN,
       ST_DECOY,ST_RAGE,ST_FLEE };
enum { LPR_STONE=96,LPR_BONE,LPR_FIRE,LPR_ICE,LPR_WIND,LPR_BOMB,LPR_SPORE,LPR_SHOCK };
enum { PART_ORB,PART_SEGMENT,PART_TAIL,PART_BONE,PART_FLAME,PART_ICE,
       PART_GUST,PART_BOMB,PART_STONE,PART_SPORE,PART_MARK,PART_FAIRY };
#define TRAIL_COUNT 4
#define TRAIL_LEN 24
typedef struct {u8 owner,head,count,clock;s16 xy[TRAIL_LEN][2];} EnemyTrail;
static EnemyTrail sTrails[TRAIL_COUNT] EWRAM_BSS;
static u16 sPartsTile;
static u8 sChildParent, sChildMode, sPlatformOwner;

const LegacyEnemyDef* legacy_enemy_def(int type) {
    if(type<LEGACY_ENEMY_BASE || type>=LEGACY_ENEMY_END) return 0;
    return &gLegacyEnemyDefs[type-LEGACY_ENEMY_BASE];
}
bool8 legacy_enemy_owns(int type) {return type>=LEGACY_ENEMY_BASE && type<LEGACY_ENEMY_END;}
static int family(const Actor* e) {return gLegacyEnemyDefs[e->type-LEGACY_ENEMY_BASE].family;}
static void pose(Actor* e,int p) {e->frame=p*4+e->facing;e->hflip=0;}
static void begin(Actor* e,int state,int ticks,int p) {
    if((gLegacyEnemyDefs[e->type-LEGACY_ENEMY_BASE].roles&LE_ROLE_RANGED)&&
       (state==ST_ROAM||state==ST_RECOVER))ticks=handoff_enemy_fire_delay(ticks);
    e->state=state;e->timer=ticks;pose(e,p);
}
static bool8 elapsed(Actor* e) {if(e->timer) --e->timer;return !e->timer;}
static int toward(Actor* e) {return actor_dir_to(e,gPlayer);}
static int cardinal(Actor* e) {return ((toward(e)+4)&24);}
static void face_dir(Actor* e) {e->facing=dir_to_facing(e->dir);}
static void aim(Actor* e) {e->dir=toward(e);face_dir(e);}
static void anchor(Actor* e,int x,int y) {e->pad[0]=x;e->pad[1]=x>>8;e->pad[2]=y;e->pad[3]=y>>8;}
static int ax(const Actor* e) {return (s16)(e->pad[0]|e->pad[1]<<8);}
static int ay(const Actor* e) {return (s16)(e->pad[2]|e->pad[3]<<8);}
static bool8 safe_floor(int x,int y) {
    int t;
    if(x<12 || y<20 || x>room_px_w()-12 || y>room_px_h()-8) return FALSE;
    t=room_type_px(x,y-3);
    return t!=TT_WATER && t!=TT_PIT && !room_box_solid(x-5,y-10,x+4,y-1);
}
static bool8 move(Actor* e,int speed,int dir) {
    s32 x=e->x,y=e->y;
    bool8 hit;
    e->dir=dir&31;
    hit=actor_move(e,speed,e->dir);
    if(!(e->flags&AF_FLYING) && e->z<=0 && !safe_floor(PX(e->x),PX(e->y))) {e->x=x;e->y=y;hit=TRUE;}
    if(e->flags&AF_FLYING) {
        int px=PX(e->x),py=PX(e->y);
        if(px<12||py<24||px>room_px_w()-12||py>room_px_h()-8) {
            e->x=x;e->y=y;hit=TRUE;
        }
    }
    face_dir(e);return !hit;
}
static void walk_pose(Actor* e) {pose(e,(gFrame&8)?LP_WALK1:LP_WALK2);}
static void roam(Actor* e,int speed,int interval) {
    if(elapsed(e)) {e->timer=interval+rand_range(16);e->dir=rand_range(4)*8;}
    if(!move(e,speed,e->dir)) {e->dir=(e->dir+8)&31;e->timer=12;}
    walk_pose(e);
}
static int lane(Actor* e,int width,int range) {
    int dx=PX(gPlayer->x)-PX(e->x),dy=PX(gPlayer->y)-PX(e->y),d,i;
    if(ABS(dx)<=width && ABS(dy)>16 && ABS(dy)<=range) d=dy<0?0:16;
    else if(ABS(dy)<=width && ABS(dx)>16 && ABS(dx)<=range) d=dx<0?24:8;
    else return -1;
    for(i=8;i<(ABS(dx)+ABS(dy));i+=8) {
        int x=PX(e->x)+(d==8?i:d==24?-i:0);
        int y=PX(e->y)+(d==16?i:d==0?-i:0);
        if(room_solid_px(x,y-5)) return -1;
    }
    return d;
}
static void touch_at(Actor* e,int x,int y,int hw,int hh,int damage,int status) {
    if(!gPlayer || !player_is_vulnerable() || PX(gPlayer->z)>12) return;
    if(actor_box_overlap(gPlayer,x-hw,y-hh,x+hw,y+hh) && player_hurt(damage,actor_dir_to(e,gPlayer)))
        if(status>=0) legacy_player_status_apply(status,status==LPS_FREEZE?90:status==LPS_BURN?120:45);
}
/* Source bites use the existing charm/food/fairy/death damage pipeline.
   Alive captives retain their held pose; capture is released on death. */
static void capture_damage(Actor* e,int amount) {
    u8 state,timer;
    if(!gPlayer||gPlayer->state==PS_DEAD||gPl.hp<=0)return;
    state=gPlayer->state;timer=gPlayer->timer;
    gPlayer->state=PS_NORMAL;gPlayer->iframes=0;gPl.shield_up=0;
    player_hurt(amount,actor_dir_to(e,gPlayer));
    if(gPl.hp>0&&gPlayer->state!=PS_DEAD) {gPlayer->state=state;gPlayer->timer=timer;gPlayer->kb_timer=0;}
    else legacy_player_status_clear(LPS_CAPTURE);
}
static EnemyTrail* trail(Actor* e,bool8 alloc) {
    int i,j,idx=e-gActors;
    for(i=0;i<TRAIL_COUNT;i++) if(sTrails[i].owner==idx) return &sTrails[i];
    if(!alloc) return 0;
    for(i=0;i<TRAIL_COUNT;i++) {
        if(sTrails[i].owner && gActors[sTrails[i].owner].kind!=AK_ENEMY) sTrails[i].owner=0;
        if(!sTrails[i].owner) {
            EnemyTrail* t=&sTrails[i];t->owner=idx;t->head=0;t->count=TRAIL_LEN;t->clock=0;
            for(j=0;j<TRAIL_LEN;j++) {t->xy[j][0]=PX(e->x);t->xy[j][1]=PX(e->y);}
            return t;
        }
    }
    return 0;
}
static void trail_tick(Actor* e) {
    EnemyTrail* t=trail(e,TRUE);
    if(t && ++t->clock>=3) {t->clock=0;t->head=(t->head+1)%TRAIL_LEN;t->xy[t->head][0]=PX(e->x);t->xy[t->head][1]=PX(e->y);}
}
static void trail_pos(EnemyTrail* t,int offset,int* x,int* y) {
    int i=(t->head+TRAIL_LEN-offset)%TRAIL_LEN;*x=t->xy[i][0];*y=t->xy[i][1];
}
static void draw_part(int x,int y,int z,int frame,int pal,int prio) {
    if(!sPartsTile) return;
    draw_sprite(x-gCamX-8,y-gCamY-8-z,SHEET_LEGACY_PARTS,sPartsTile,frame,0,prio,pal);
}
static Actor* projectile(Actor* e,int type,int dir,int speed,int damage) {
    Actor* p;
    if(actor_count(AK_PROJ)>=12) return 0;
    p=actor_new(AK_PROJ,type,PX(e->x),PX(e->y)-6);
    if(!p) return 0;
    actor_set_sheet(p,SHEET_LEGACY_PARTS,sPartsTile);
    p->dir=dir;p->speed=speed;p->damage=damage;p->hitbox=HB_PROJ;
    p->flags=AF_FLYING;p->timer=120;p->prio=1;p->pal=PAL_OBJ_BLIGHT;
    p->v[2]=e-gActors;p->z=e->z;
    p->frame=type==LPR_BONE?PART_BONE:type==LPR_FIRE?PART_FLAME:type==LPR_ICE?PART_ICE:
        type==LPR_WIND?PART_GUST:type==LPR_BOMB?PART_BOMB:type==LPR_SPORE?PART_SPORE:PART_STONE;
    return p;
}
static void shoot(Actor* e,int type,int speed) {projectile(e,type,facing_to_dir(e->facing),speed,2);sfx_play(SFX_SPIT);}
static void explosion(Actor* e) {
    int i,x=PX(e->x),y=PX(e->y);
    fx_spawn(FX_BLAST,x,y-5);sfx_play(SFX_BOMB);
    touch_at(e,x,y-5,23,23,4,-1);
    for(i=1;i<ACTOR_MAX;i++) {
        Actor* q=&gActors[i];if(q==e||q->kind!=AK_ENEMY||!(q->flags&AF_HITTABLE)) continue;
        if(actor_box_overlap(q,x-23,y-28,x+23,y+18)) legacy_item_hit(q,LE_HIT_BOMB,6,actor_dir_to(e,q),0);
    }
}
static bool8 teleport_near_anchor(Actor* e) {
    static const s8 p[13][2]={{0,0},{24,0},{-24,0},{0,24},{0,-24},{32,24},{-32,24},{32,-24},{-32,-24},{48,0},{-48,0},{0,48},{0,-48}};
    int start=rand_range(13),i;
    for(i=0;i<13;i++) {
        int j=(start+i)%13,x=ax(e)+p[j][0],y=ay(e)+p[j][1];
        if(!safe_floor(x,y) || (ABS(x-PX(gPlayer->x))+ABS(y-PX(gPlayer->y))<24)) continue;
        /* Stay in the same collision-connected neighborhood: do not skip a
           solid wall in either axis of this short teleport. */
        if(room_box_solid(MIN(x,ax(e))-3,MIN(y,ay(e))-8,MAX(x,ax(e))+3,MAX(y,ay(e)))) continue;
        e->x=Q16(x);e->y=Q16(y);return TRUE;
    }
    e->x=Q16(ax(e));e->y=Q16(ay(e));return FALSE;
}
void legacy_enemy_room_reset(void) {
    memset(sTrails,0,sizeof(sTrails));sChildParent=0;sChildMode=0;sPlatformOwner=0;
    sPartsTile=0;
}
static Actor* child(Actor* e,int type,int x,int y,int mode) {
    Actor* c;
    sChildParent=e-gActors;sChildMode=mode;c=enemy_spawn(type,x,y);sChildParent=0;sChildMode=0;
    if(c)cream_runtime_track_enemy(c,e);
    return c;
}
void legacy_enemy_init(Actor* e) {
    if(!sPartsTile)sPartsTile=sprite_load_sheet(SHEET_LEGACY_PARTS);
    int f=family(e);
    memset(e->v,0,sizeof(e->v));anchor(e,PX(e->x),PX(e->y));
    e->state=ST_ROAM;e->timer=30;e->dir=cardinal(e);face_dir(e);pose(e,LP_IDLE);
    if(sChildMode) {e->v[3]=sChildMode;e->v[4]=sChildParent;}
    if(f==LF_KEESE||f==LF_CROW) {e->state=ST_REST;e->timer=60;e->z=Q16(10);}
    if(f==LF_SMALL_PESTO||f==LF_PESTO||f==LF_PEAHAT||f==LF_BOMB_PEAHAT||f==LF_TAKKURI) e->z=Q16(10);
    if(f==LF_LEEVER||f==LF_MOLDWORM||f==LF_GHINI||f==LF_WIZZROBE_FIRE||f==LF_WIZZROBE_ICE||f==LF_WIZZROBE_WIND) {
        begin(e,ST_HIDDEN,60,LP_BURIED);e->flags&=~(AF_HURTS|AF_HITTABLE);
    }
    if(f==LF_RUPEE_LIKE||f==LF_SPINY_BEETLE||f==LF_ARMOS||f==LF_CLOUD_PIRANHA||f==LF_LAKITU) begin(e,ST_REST,60,LP_BURIED);
    if(f==LF_WISP||f==LF_SPARK) {e->flags|=AF_FLYING;e->z=Q16(2);}
    if(f==LF_MOLDORM||f==LF_MOLDWORM||f==LF_MADDERPILLAR) {
        trail(e,TRUE);if(f==LF_MADDERPILLAR) e->hp=32;
    }
    if(f==LF_UNKNOWN4D||f==LF_BALL_CHAIN) e->v[2]=e->dir*8;
    if(f==LF_BIG_OCTOROK) {e->hp=3;e->v[2]=0;begin(e,ST_TELL,60,LP_TELL);}
    if(f==LF_GLEEROK) {sPlatformOwner=e-gActors;begin(e,ST_ROAM,90,LP_IDLE);}
    if(f==LF_GIANT_CHUCHU) {e->v[0]=0;begin(e,ST_ROAM,90,LP_IDLE);}
    if(f==LF_UNKNOWN50 && !e->v[3]) {
        static const s8 off[3][2]={{24,0},{-24,0},{0,24}};int i;
        for(i=0;i<3;i++) if(safe_floor(PX(e->x)+off[i][0],PX(e->y)+off[i][1]))
            child(e,e->type,PX(e->x)+off[i][0],PX(e->y)+off[i][1],1);
    }
    if(f==LF_ACRO_BANDIT && !e->v[3]) {
        int i;for(i=1;i<6;i++) {Actor* c=child(e,e->type,PX(e->x),PX(e->y),2);if(c) {c->v[2]=i;c->z=Q16(i*9);}}
        begin(e,ST_TELL,20,LP_TELL);
    }
}

/* A line attack records its lane during the tell and never steers while it
   is active. Different families keep their original timing/speed tables. */
static void charge_ai(Actor* e,int tell,int speed,int chase_range,int cooldown) {
    if(e->state==ST_TELL) {
        pose(e,LP_TELL);if(elapsed(e)) begin(e,ST_ATTACK,90,LP_ATTACK);
    } else if(e->state==ST_ATTACK) {
        pose(e,LP_ATTACK);if(!move(e,speed,e->dir)||elapsed(e)) begin(e,ST_RECOVER,cooldown,LP_RECOVER);
    } else if(e->state==ST_RECOVER) {
        pose(e,LP_RECOVER);if(elapsed(e)) begin(e,ST_ROAM,30,LP_IDLE);
    } else {
        int d=lane(e,8,chase_range);
        if(d>=0) {e->dir=d;face_dir(e);begin(e,ST_TELL,tell,LP_TELL);}
        else roam(e,e->speed,30);
    }
}
static void hop_ai(Actor* e,int prepare,int jumps,int jump_speed) {
    if(e->state==ST_ROAM||e->state==ST_REST) {
        pose(e,LP_IDLE);if(elapsed(e)) {aim(e);e->v[2]=jumps;begin(e,ST_TELL,prepare,LP_TELL);}
    } else if(e->state==ST_TELL) {
        pose(e,LP_TELL);if(elapsed(e)) {e->zvel=jump_speed;begin(e,ST_ATTACK,90,LP_ATTACK);}
    } else if(e->state==ST_ATTACK) {
        move(e,e->speed,e->dir);actor_gravity(e);pose(e,LP_ATTACK);
        if(e->z<=0) {
            e->z=0;e->zvel=0;
            if(e->v[2]>1) {--e->v[2];aim(e);begin(e,ST_TELL,prepare,LP_TELL);}
            else begin(e,ST_RECOVER,20,LP_RECOVER);
        }
    } else if(elapsed(e)) begin(e,ST_ROAM,20+rand_range(24),LP_IDLE);
}
static void shooter_ai(Actor* e,bool8 golden,int projectile_kind) {
    static const u8 walks[]={30,60,60,90};
    if(e->state==ST_TELL) {
        pose(e,LP_TELL);
        if(elapsed(e)) {shoot(e,projectile_kind,384);e->v[2]=golden?2:0;begin(e,ST_ATTACK,golden?8:12,LP_ATTACK);}
    } else if(e->state==ST_ATTACK) {
        pose(e,LP_ATTACK);
        if(elapsed(e)) {
            if(e->v[2]) {--e->v[2];shoot(e,projectile_kind,448);e->timer=8;}
            else begin(e,ST_RECOVER,24+rand_range(57),LP_RECOVER);
        }
    } else if(e->state==ST_RECOVER) {
        pose(e,LP_RECOVER);if(elapsed(e)) {e->dir=rand_range(4)*8;begin(e,ST_ROAM,walks[rand_range(4)],LP_IDLE);}
    } else {
        move(e,e->speed,e->dir);walk_pose(e);
        if(elapsed(e)) {if(rand_range(4)) e->dir=cardinal(e);face_dir(e);begin(e,ST_TELL,golden?12:20,LP_TELL);}
    }
}
static void flyer_ai(Actor* e,int f) {
    int dist=actor_dist2(e,gPlayer);
    if(e->state==ST_EXPOSED) {
        e->flags&=~AF_FLYING;e->z=0;pose(e,LP_RECOVER);
        if(elapsed(e)) {e->flags|=AF_FLYING|AF_HURTS;e->z=Q16(10);begin(e,ST_ROAM,90,LP_IDLE);e->v[0]=0;}
        return;
    }
    if(e->state==ST_REST) {
        pose(e,LP_IDLE);
        if(dist<120*120 && elapsed(e)) {aim(e);begin(e,ST_TELL,f==LF_CROW?24:16,LP_TELL);}
    } else if(e->state==ST_TELL) {
        e->z=Q16(10);pose(e,LP_TELL);
        if(elapsed(e)) {aim(e);begin(e,ST_ATTACK,f==LF_CROW?64:120,LP_ATTACK);}
    } else if(e->state==ST_ATTACK) {
        int speed=f==LF_CROW?448:f==LF_TAKKURI?320:192;
        if((e->timer&15)==0 && f!=LF_CROW) {
            aim(e);if(f==LF_TAKKURI&&e->v[5]) e->dir=(e->dir+16)&31;
        }
        if(!move(e,speed,e->dir)) e->dir=(e->dir+12)&31;
        e->z=Q16(4+(ABS((int)(e->timer&31)-16)>>1));walk_pose(e);
        if((f==LF_BOMB_PEAHAT||f==LF_PESTO) && (e->timer==90||e->timer==45)) {
            Actor* p=projectile(e,f==LF_BOMB_PEAHAT?LPR_BOMB:LPR_SPORE,e->dir,e->type==LE_PESTO_1?128:0,2);
            if(p) {p->z=Q16(12);p->zvel=0;p->timer=45;}
        }
        if(elapsed(e)) begin(e,ST_RETURN,60,f==LF_PEAHAT?LP_IDLE:LP_RECOVER);
    } else if(e->state==ST_RETURN) {
        Actor a=*e;a.x=Q16(ax(e));a.y=Q16(ay(e));
        move(e,256,actor_dir_to(e,&a));walk_pose(e);
        if(actor_dist2(e,&a)<6*6||elapsed(e)) {
            if(f==LF_PEAHAT) {e->flags&=~AF_HURTS;begin(e,ST_EXPOSED,60,LP_RECOVER);e->z=0;}
            else begin(e,f==LF_CROW||f==LF_KEESE?ST_REST:ST_ROAM,60,LP_IDLE);
        }
    } else {
        int d;
        if((e->timer&15)==0) e->dir=(e->dir+rand_range(9)-4)&31;
        d=(e->dir+((SIN((gFrame+e->v[2])*8)*2)>>14))&31;
        if(!move(e,e->speed,d)) e->dir=(e->dir+16)&31;
        e->z=Q16(10);walk_pose(e);
        if(elapsed(e)) {aim(e);begin(e,ST_TELL,16,LP_TELL);}
    }
}
static void burrow_ai(Actor* e,int f) {
    if(e->state==ST_HIDDEN) {
        pose(e,LP_BURIED);e->flags&=~(AF_HURTS|AF_HITTABLE);
        if(elapsed(e)) {teleport_near_anchor(e);begin(e,ST_RISE,24,LP_TELL);}
    } else if(e->state==ST_RISE) {
        pose(e,LP_TELL);if(elapsed(e)) {e->flags|=AF_HURTS|AF_HITTABLE;aim(e);begin(e,ST_ATTACK,f==LF_MOLDWORM?180:180,LP_ATTACK);}
    } else if(e->state==ST_ATTACK) {
        if((e->timer&15)==0) aim(e);
        if(!move(e,e->speed,e->dir)) e->dir=(e->dir+8)&31;
        walk_pose(e);if(f==LF_MOLDWORM) trail_tick(e);
        if(elapsed(e)) begin(e,ST_RECOVER,20,LP_RECOVER);
    } else {
        pose(e,LP_RECOVER);if(elapsed(e)) begin(e,ST_HIDDEN,f==LF_LEEVER?240:120,LP_BURIED);
    }
}

static void skeleton_ai(Actor* e) {
    if(e->state==ST_TELL) {
        pose(e,LP_TELL);if(elapsed(e)) {e->zvel=Q16(2.5);e->dir=(toward(e)+16)&31;begin(e,ST_ATTACK,30,LP_ATTACK);}
    } else if(e->state==ST_ATTACK) {
        move(e,e->speed,e->dir);actor_gravity(e);pose(e,LP_ATTACK);
        if(e->z<=0) {e->z=0;begin(e,ST_RECOVER,30,LP_RECOVER);if(e->type==LE_STALFOS_1) {aim(e);shoot(e,LPR_BONE,384);}}
    } else if(e->state==ST_RECOVER) {pose(e,LP_RECOVER);if(elapsed(e)) begin(e,ST_ROAM,30,LP_IDLE);}
    else {
        roam(e,e->speed,30);
        if(actor_dist2(e,gPlayer)<40*40 && (gPl.sword_active||e->timer<4)) begin(e,ST_TELL,10,LP_TELL);
    }
}
static void jelly_ai(Actor* e,int f) {
    /* Blue/red coats and spikes are visible, timed, and removed by a real
       counter; the underlying hop remains readable across all forms. */
    if(f==LF_CHUCHU && e->type==LE_CHUCHU_2) e->v[0]=((gFrame+e-gActors)%120)<60;
    if(f==LF_SPINY_CHUCHU) e->v[0]=((gFrame+e-gActors)%150)<95;
    hop_ai(e,16,1,Q16(2));
    if(e->v[0] && e->state!=ST_TELL) pose(e,LP_TELL);
}
static void knight_ai(Actor* e,int f) {
    int form=legacy_enemy_def(e->type)->form;
    if(e->state==ST_TELL) {
        pose(e,LP_TELL);
        if(elapsed(e)) begin(e,ST_ATTACK,f==LF_DARKNUT?14:18,LP_ATTACK);
    } else if(e->state==ST_ATTACK) {
        int d=facing_to_dir(e->facing),reach=f==LF_SPEAR_MOBLIN?23:18;
        int x=PX(e->x)+((SIN(d*8)*reach)>>14),y=PX(e->y)-7-((COS(d*8)*reach)>>14);
        pose(e,LP_ATTACK);move(e,f==LF_DARKNUT?96:192,d);touch_at(e,x,y,8,8,f==LF_DARKNUT?4:2,-1);
        if(elapsed(e)) begin(e,ST_RECOVER,form>=2?24:40,LP_RECOVER);
    } else if(e->state==ST_RECOVER) {
        pose(e,LP_RECOVER);if(elapsed(e)) {aim(e);begin(e,ST_ROAM,40,LP_IDLE);}
    } else {
        if((e->timer&15)==0) aim(e);
        if(!move(e,e->speed,e->dir)) e->dir=(e->dir+8)&31;
        walk_pose(e);elapsed(e);
        if(actor_dist2(e,gPlayer)<(f==LF_SPEAR_MOBLIN?42*42:34*34)) {
            e->dir=cardinal(e);face_dir(e);begin(e,ST_TELL,f==LF_DARKNUT?18-form*2:32,LP_TELL);
        } else if(f==LF_DARKNUT && form>=2 && gPl.sword_active && actor_dist2(e,gPlayer)<60*60) {
            move(e,256,(toward(e)+8)&31);pose(e,LP_TELL);
        }
    }
}
static void keaton_ai(Actor* e) {
    if(e->state==ST_ROAM) {
        roam(e,e->speed,30);
        if(actor_dist2(e,gPlayer)<72*72) {aim(e);begin(e,ST_TELL,12,LP_TELL);}
    } else if(e->state==ST_TELL) {
        move(e,192,(toward(e)+8)&31);pose(e,LP_TELL);
        if(elapsed(e)) {aim(e);begin(e,ST_ATTACK,20,LP_ATTACK);}
    } else if(e->state==ST_ATTACK) {
        move(e,480,e->dir);pose(e,LP_ATTACK);if(elapsed(e)) begin(e,ST_RECOVER,30,LP_RECOVER);
    } else if(elapsed(e)) begin(e,ST_ROAM,30,LP_IDLE);
}
static void bomb_ai(Actor* e,int f) {
    if(e->state==ST_CARRY) {e->x=gPlayer->x;e->y=gPlayer->y;e->z=Q16(22);pose(e,LP_TELL);}
    else if(e->state==ST_THROWN) {
        move(e,e->speed,e->dir);actor_gravity(e);pose(e,LP_ATTACK);
        if(e->z<=0||e->coll) {explosion(e);enemy_kill(e);return;}
    } else if(f==LF_BOMBAROSSA) {
        e->z=Q16(2+((gFrame>>4)&3));pose(e,LP_IDLE);
        if(e->v[0]) {
            if(!move(e,384,e->dir)||elapsed(e)) {explosion(e);enemy_kill(e);return;}
            pose(e,LP_ATTACK);
        }
    } else if(e->v[0]) {
        if(!e->v[1] && e->state!=ST_CARRY) {if((e->timer&15)==0) aim(e);move(e,512,e->dir);}
        pose(e,(e->timer&4)?LP_TELL:LP_ATTACK);
    } else roam(e,128,30);
    if(f==LF_BOBOMB && e->v[0] && elapsed(e)) {explosion(e);enemy_kill(e);}
}
static void worm_ai(Actor* e,int f) {
    if(f==LF_MOLDWORM) {burrow_ai(e,f);return;}
    if(e->state==ST_RAGE) {
        if((e->timer&7)==0) aim(e);
        if(!move(e,f==LF_MADDERPILLAR?264:448,e->dir)) e->dir=(e->dir+8)&31;
        pose(e,LP_ATTACK);if(elapsed(e)) begin(e,ST_RECOVER,36,LP_RECOVER);
    } else if(e->state==ST_RECOVER) {
        pose(e,LP_RECOVER);if(elapsed(e)) begin(e,ST_ROAM,71,LP_IDLE);
    } else {
        if(elapsed(e)) {e->dir=(e->dir+((rand_range(2)?1:-1)*8))&31;e->timer=f==LF_MADDERPILLAR?71:30;}
        if(!move(e,f==LF_MADDERPILLAR?160:e->speed,e->dir)) e->dir=(e->dir+8)&31;
        walk_pose(e);
    }
    trail_tick(e);
}
static void statue_ai(Actor* e,int f) {
    if(e->state==ST_REST) {
        pose(e,LP_BURIED);e->flags&=~AF_HURTS;
        if(actor_dist2(e,gPlayer)<64*64) {aim(e);begin(e,ST_TELL,f==LF_ARMOS?40:24,LP_TELL);}
    } else if(e->state==ST_TELL) {
        pose(e,LP_TELL);if(elapsed(e)) {e->flags|=AF_HURTS;begin(e,ST_ATTACK,90,LP_ATTACK);}
    } else if(e->state==ST_ATTACK) {
        if((e->timer&15)==0) aim(e);
        move(e,e->speed,e->dir);walk_pose(e);
        if(f==LF_ARMOS && (e->timer%24)==0) {
            e->zvel=Q16(1.5);touch_at(e,PX(e->x),PX(e->y)-4,15,11,3,-1);
        }
        if(e->z>0||e->zvel>0) actor_gravity(e);
        if(elapsed(e)) begin(e,ST_RECOVER,48,LP_RECOVER);
    } else {
        pose(e,LP_RECOVER);if(elapsed(e)) {aim(e);begin(e,ST_TELL,24,LP_TELL);}
    }
}
static void mushroom_ai(Actor* e) {
    if(e->v[2]) {roam(e,64,40);pose(e,LP_RECOVER);return;}
    if(e->state==ST_TELL) {
        pose(e,LP_TELL);if(elapsed(e)) {
            int d;for(d=0;d<32;d+=8) projectile(e,LPR_SPORE,d,128,1);
            begin(e,ST_RECOVER,90,LP_RECOVER);
        }
    } else {roam(e,64,30);if(elapsed(e)||actor_dist2(e,gPlayer)<40*40) begin(e,ST_TELL,30,LP_TELL);}
}
static void flame_ai(Actor* e,int f) {
    if(e->state==ST_TELL) {
        pose(e,LP_TELL);if(elapsed(e)) {aim(e);begin(e,ST_ATTACK,48,LP_ATTACK);}
    } else if(e->state==ST_ATTACK) {
        move(e,f==LF_FIREBALL?192:256,e->dir);walk_pose(e);
        if(f==LF_FIREBALL && e->timer==24) shoot(e,LPR_FIRE,192);
        if(elapsed(e)) begin(e,ST_ROAM,60,LP_IDLE);
    } else {roam(e,64,30);if(actor_dist2(e,gPlayer)<80*80&&e->timer<8) begin(e,ST_TELL,24,LP_TELL);}
}
static void ambush_ai(Actor* e,int f) {
    if(e->state==ST_REST) {
        e->flags&=~AF_HURTS;pose(e,LP_BURIED);
        if(actor_dist2(e,gPlayer)<(f==LF_CLOUD_PIRANHA?72*72:40*40)) begin(e,ST_TELL,24,LP_TELL);
    } else if(e->state==ST_TELL) {
        pose(e,LP_TELL);if(elapsed(e)) {e->flags|=AF_HURTS;aim(e);e->zvel=Q16(f==LF_CLOUD_PIRANHA?3:1);begin(e,ST_ATTACK,90,LP_ATTACK);}
    } else if(e->state==ST_ATTACK) {
        move(e,e->speed,e->dir);if(e->z>0||e->zvel>0) actor_gravity(e);walk_pose(e);
        if(elapsed(e)) begin(e,ST_RECOVER,45,LP_RECOVER);
    } else if(elapsed(e)) begin(e,ST_REST,60,LP_BURIED);
}
static void grabber_ai(Actor* e,int f) {
    if(e->state==ST_CAPTURE) {
        pose(e,LP_ATTACK);
        if(e->timer) --e->timer;
        if(f==LF_GIBDO && e->timer && e->timer%24==0 && legacy_player_status(LPS_CAPTURE))capture_damage(e,8);
        if(!legacy_player_status(LPS_CAPTURE)||!e->timer) {
            if(f==LF_LIKE_LIKE && !e->v[5] && !e->timer) {
                if(legacy_item_owned(LI_MIRROR_SHIELD)) {legacy_item_remove(LI_MIRROR_SHIELD);e->v[5]=2;}
                else if(gPl.items&ITEM_SHIELD) {legacy_item_remove(LI_SHIELD);e->v[5]=1;}
                else capture_damage(e,1);
            }
            legacy_player_status_clear(LPS_CAPTURE);begin(e,ST_RECOVER,60,LP_RECOVER);
        } else if(f==LF_RUPEE_LIKE && (e->timer%12)==0 && gPl.gilt) {
            int n=MIN((legacy_enemy_def(e->type)->form+1)*2,gPl.gilt);
            n=MIN(n,255-e->v[5]);gPl.gilt-=n;e->v[5]+=n;
        }
    } else if(e->state==ST_REST) {
        pose(e,LP_BURIED);if(actor_dist2(e,gPlayer)<32*32) begin(e,ST_TELL,18,LP_TELL);
    } else if(e->state==ST_TELL) {
        pose(e,LP_TELL);if(elapsed(e)) begin(e,ST_ROAM,120,LP_IDLE);
    } else if(e->state==ST_RECOVER) {
        pose(e,LP_RECOVER);if(elapsed(e)) begin(e,ST_ROAM,30,LP_IDLE);
    } else {
        if((e->timer&15)==0) aim(e);
        move(e,e->speed,e->dir);walk_pose(e);if(elapsed(e)) e->timer=30;
    }
}
static void mirage_ai(Actor* e) {
    if(e->v[3] && (gActors[e->v[4]].kind!=AK_ENEMY||gActors[e->v[4]].type!=e->type)) {actor_free(e);return;}
    if(e->state==ST_CAPTURE) {
        pose(e,LP_ATTACK);if(e->timer)--e->timer;
        if(e->timer && e->timer%32==0 && legacy_player_status(LPS_CAPTURE))capture_damage(e,4);
        if(!legacy_player_status(LPS_CAPTURE)||!e->timer) {legacy_player_status_clear(LPS_CAPTURE);begin(e,ST_RECOVER,120,LP_RECOVER);}
    } else if(e->state==ST_RECOVER) {
        pose(e,LP_RECOVER);if(elapsed(e)) begin(e,ST_TELL,15,LP_TELL);
    } else if(e->state==ST_TELL) {
        pose(e,LP_TELL);if(elapsed(e)) {aim(e);begin(e,ST_ATTACK,60+rand_range(60),LP_ATTACK);}
    } else if(e->state==ST_ATTACK) {
        if((e->timer&7)==0) aim(e);
        move(e,256,e->dir);walk_pose(e);
        if(elapsed(e)) begin(e,ST_RECOVER,30,LP_RECOVER);
    } else {
        pose(e,LP_IDLE);
        if(gPl.lamp_timer || actor_dist2(e,gPlayer)<64*64) begin(e,ST_TELL,15,LP_TELL);
    }
}
static void wizard_ai(Actor* e,int f) {
    if(e->state==ST_HIDDEN) {
        e->flags&=~(AF_HURTS|AF_HITTABLE);pose(e,LP_BURIED);
        if(elapsed(e)) {teleport_near_anchor(e);begin(e,ST_RISE,40,LP_TELL);}
    } else if(e->state==ST_RISE) {
        pose(e,LP_TELL);if(elapsed(e)) {e->flags|=AF_HITTABLE|AF_HURTS;e->dir=cardinal(e);face_dir(e);begin(e,ST_TELL,f==LF_WIZZROBE_ICE?12:f==LF_WIZZROBE_FIRE?14:16,LP_TELL);}
    } else if(e->state==ST_TELL) {
        pose(e,LP_TELL);if(elapsed(e)) {shoot(e,f==LF_WIZZROBE_FIRE?LPR_FIRE:f==LF_WIZZROBE_ICE?LPR_ICE:LPR_WIND,320);begin(e,ST_ATTACK,32,LP_ATTACK);}
    } else if(e->state==ST_ATTACK) {pose(e,LP_ATTACK);if(elapsed(e)) begin(e,ST_RECOVER,56,LP_RECOVER);}
    else {pose(e,LP_RECOVER);if(elapsed(e)) begin(e,ST_HIDDEN,96,LP_BURIED);}
}
static void acro_ai(Actor* e) {
    if(e->v[3]) {
        Actor* p=&gActors[e->v[4]];
        if(p->kind==AK_ENEMY && p->type==e->type && p->state!=ST_RECOVER) {
            e->x=p->x;e->y=p->y;e->z=p->z+Q16(e->v[2]*9);e->facing=p->facing;pose(e,p->frame/4);return;
        }
        e->v[3]=0;e->z=0;e->zvel=Q16(2);begin(e,ST_ATTACK,45,LP_ATTACK);e->dir=rand_range(32);
    }
    if(e->state==ST_TELL) {pose(e,LP_TELL);if(elapsed(e)) {aim(e);e->zvel=Q16(2);begin(e,ST_ATTACK,60,LP_ATTACK);}}
    else if(e->state==ST_ATTACK) {
        move(e,128,e->dir);actor_gravity(e);walk_pose(e);
        if(e->z<=0) {e->z=0;e->zvel=Q16(2);aim(e);}
        if(elapsed(e)) begin(e,ST_RECOVER,60,LP_RECOVER);
    } else {roam(e,128,30);if(elapsed(e)) begin(e,ST_TELL,20,LP_TELL);}
}

static void flail_point(Actor* e,int* x,int* y,int* radius) {
    int f=family(e),r=24,a=e->v[2];
    if(f==LF_UNKNOWN4D) {
        if(e->state==ST_TELL) r=12;
        else if(e->state==ST_ATTACK) r=MIN(64,12+(90-e->timer)*3);
        else if(e->state==ST_RECOVER) r=MAX(12,e->timer);
        else r=40;
    } else if(e->state==ST_ATTACK) r=48;
    *x=PX(e->x)+((SIN(a)*r)>>14);*y=PX(e->y)-7-((COS(a)*r)>>14);*radius=r;
}
static void flail_ai(Actor* e,int f) {
    int x,y,r;
    if(e->state==ST_TELL) {
        pose(e,LP_TELL);if(elapsed(e)) {e->v[2]=facing_to_dir(e->facing)*8;begin(e,ST_ATTACK,90,LP_ATTACK);}
    } else if(e->state==ST_ATTACK) {
        if(f==LF_BALL_CHAIN) e->v[2]+=6;
        pose(e,LP_ATTACK);if(elapsed(e)) begin(e,ST_RECOVER,f==LF_UNKNOWN4D?60:45,LP_RECOVER);
    } else if(e->state==ST_RECOVER) {
        pose(e,LP_RECOVER);if(elapsed(e)) begin(e,ST_ROAM,30,LP_IDLE);
    } else {
        e->v[2]+=f==LF_UNKNOWN4D?10:4;
        if(f==LF_BALL_CHAIN) roam(e,e->speed,30);else pose(e,LP_IDLE);
        if(actor_dist2(e,gPlayer)<96*96 && e->timer<3) {e->dir=cardinal(e);face_dir(e);begin(e,ST_TELL,f==LF_UNKNOWN4D?15:30,LP_TELL);}
        if(f==LF_UNKNOWN4D) elapsed(e);
    }
    flail_point(e,&x,&y,&r);touch_at(e,x,y,7,7,4,-1);
}
static void rollobite_ai(Actor* e) {
    if(e->state==ST_CARRY) {e->x=gPlayer->x;e->y=gPlayer->y;e->z=Q16(22);pose(e,LP_RECOVER);return;}
    if(e->state==ST_THROWN) {
        int x,y;move(e,e->speed,e->dir);actor_gravity(e);pose(e,LP_ATTACK);
        if(e->z<=0||e->coll) {
            x=PX(e->x)>>4;y=(PX(e->y)-3)>>4;e->z=0;
            if(room_type(x,y)==TT_PIT) {
                /* Filling a logical pit changes only that one terrain cell;
                   the curled body persists as a visible plug until leaving. */
                {
                    static const s8 nearby[4][2]={{1,0},{-1,0},{0,1},{0,-1}};
                    int n;u16 floor=MT_MOSS0;
                    for(n=0;n<4;n++) if(room_type(x+nearby[n][0],y+nearby[n][1])==TT_FLOOR) {floor=room_get(x+nearby[n][0],y+nearby[n][1]);break;}
                    room_change(x,y,floor);
                }
                sfx_play(SFX_SECRET);enemy_kill(e);return;
            }
            begin(e,ST_CURL,180,LP_RECOVER);
        }
    } else if(e->state==ST_CURL) {
        pose(e,(e->timer<60&&(gFrame&8))?LP_HURT:LP_RECOVER);
        if(elapsed(e)) {e->flags|=AF_HURTS;begin(e,ST_ROAM,30,LP_IDLE);}
    } else roam(e,256,30);
}
static void wisp_ai(Actor* e,int f) {
    if(e->state==ST_HIDDEN) {
        e->flags&=~(AF_HURTS|AF_HITTABLE);pose(e,LP_BURIED);
        if(e->timer2) {if(elapsed(e)) {--e->timer2;e->timer=255;}return;}
        if(elapsed(e)) {e->flags|=AF_HURTS|AF_HITTABLE;e->flags&=~AF_HIDDEN;begin(e,ST_ROAM,60,LP_IDLE);}
        return;
    }
    if(f==LF_SPARK) {
        int old=e->dir;u8 flags=e->flags;bool8 collision;
        /* Sparks ignore floor hazards, but masonry is the rail they trace.
           Flying movement would otherwise pass straight through the wall. */
        e->flags&=~AF_FLYING;collision=actor_move(e,e->speed,e->dir);e->flags=flags;
        if(collision) e->dir=(old+8)&31;
        else if((gFrame&7)==0) {
            int side=(e->dir+24)&31,x=PX(e->x)+((SIN(side*8)*9)>>14),y=PX(e->y)-((COS(side*8)*9)>>14);
            if(!room_solid_px(x,y-5)) e->dir=side;
        }
        /* A short lookahead keeps sparks tracing masonry, not room edges. */
        face_dir(e);e->z=0;pose(e,(gFrame&8)?LP_WALK1:LP_WALK2);
    } else {
        if((gFrame&15)==0) aim(e);
        move(e,e->speed,(e->dir+((SIN(gFrame*8)*3)>>14))&31);walk_pose(e);
    }
}
static void lakitu_ai(Actor* e) {
    if(e->v[0]) {
        e->flags&=~AF_FLYING;
        if(e->z>0) actor_gravity(e);
        roam(e,128,30);pose(e,LP_RECOVER);return;
    }
    e->flags|=AF_FLYING;e->z=Q16(14);
    if(e->state==ST_REST) {
        pose(e,LP_BURIED);e->flags&=~AF_HURTS;
        if(actor_dist2(e,gPlayer)<120*120) begin(e,ST_TELL,30,LP_TELL);
    } else if(e->state==ST_TELL) {
        pose(e,LP_TELL);if(elapsed(e)) {e->dir=cardinal(e);face_dir(e);shoot(e,LPR_SHOCK,320);begin(e,ST_RECOVER,60,LP_RECOVER);}
    } else {
        if((gFrame&31)==0) aim(e);
        move(e,128,(e->dir+8)&31);walk_pose(e);
        if(elapsed(e)) begin(e,ST_TELL,30,LP_TELL);
    }
}
static void giant_jelly_ai(Actor* e) {
    bool8 electric=e->type==LE_GIANT_CHUCHU_ELECTRIC;
    if(e->state==ST_EXPOSED) {
        pose(e,LP_RECOVER);
        if(elapsed(e)) {e->v[0]=0;e->flags|=AF_HURTS;begin(e,ST_ROAM,90,LP_IDLE);}
    } else if(e->state==ST_TELL) {
        pose(e,LP_TELL);if(elapsed(e)) {aim(e);e->zvel=Q16(3);begin(e,ST_ATTACK,90,LP_ATTACK);}
    } else if(e->state==ST_ATTACK) {
        move(e,128,e->dir);actor_gravity(e);pose(e,LP_ATTACK);
        if(e->z<=0) {
            e->z=0;touch_at(e,PX(e->x),PX(e->y)-5,26,20,4,electric?LPS_SHOCK:-1);
            if(electric) {int d;for(d=0;d<32;d+=8) projectile(e,LPR_SHOCK,d,192,2);}
            begin(e,ST_ROAM,90,LP_IDLE);
        }
    } else {
        if((e->timer&15)==0) aim(e);
        move(e,96,e->dir);walk_pose(e);
        if(electric && (gFrame%180)<120) pose(e,LP_TELL);
        if(elapsed(e)) begin(e,ST_TELL,30,LP_TELL);
    }
}
static void big_octorok_ai(Actor* e) {
    if(e->state==ST_RECOVER) {pose(e,LP_RECOVER);if(elapsed(e)) begin(e,ST_TELL,40,LP_TELL);}
    else if(e->state==ST_TELL) {
        e->dir=cardinal(e);face_dir(e);pose(e,LP_TELL);
        if(elapsed(e)) {
            shoot(e,(e->v[2]&1)?LPR_ICE:LPR_STONE,384);begin(e,ST_ATTACK,24,LP_ATTACK);
        }
    } else if(e->state==ST_ATTACK) {pose(e,LP_ATTACK);if(elapsed(e)) begin(e,ST_ROAM,60,LP_IDLE);}
    else {move(e,96,e->dir);walk_pose(e);if(elapsed(e)) begin(e,ST_TELL,32,LP_TELL);}
}
static void gleerok_head(Actor* e,int* x,int* y) {
    int p=(e->frame/4)&7,hx=e->facing==FACE_E?22:e->facing==FACE_W?11:17;
    int hy=p==LP_ATTACK?16:11+(p==LP_WALK2?1:p==LP_TELL?-1:0);
    if(p==LP_RECOVER||p==LP_HURT) {hx=e->facing==FACE_W?10:22;hy=26;}
    *x=PX(e->x)+hx-16;*y=PX(e->y)-64+hy+5;
}
static void gleerok_aim(Actor* e) {
    Actor head=*e;int x,y;gleerok_head(e,&x,&y);head.x=Q16(x);head.y=Q16(y+6);
    e->dir=(actor_dir_to(&head,gPlayer)+4)&24;face_dir(e);
}
static Actor* gleerok_breath(Actor* e,int dir,int speed) {
    Actor* p=projectile(e,LPR_FIRE,dir,speed,2);int x,y;gleerok_head(e,&x,&y);
    if(p) {p->x=Q16(x);p->y=Q16(y+8);p->z=0;}return p;
}
/* The open neck and back are one temporary platform. Coordinates are the
   player's logical feet: at height16 their displayed feet sit on the painted
   folded neck (local y24..38) and broad back (local y38..59). The upper ramp
   is slightly to the right; the lower body widens around its central core.
   Only one summit boss is admitted, so cache its actor index rather than
   scanning all96 actors in every player's physics update. */
int legacy_enemy_platform_height(int px,int py) {
    Actor* e;
    int dx,dy;
    if(!sPlatformOwner || sPlatformOwner>=ACTOR_MAX)return -1;
    e=&gActors[sPlatformOwner];
    if(e->kind!=AK_ENEMY || e->type!=LE_CREAM_GLEEROK || e->hp<=0 || e->state!=ST_EXPOSED)return -1;
    dx=px-PX(e->x);dy=py-PX(e->y);
    if(dy < -24 || dy > 11)return -1;
    if(dy < -10) {if(dx < -8 || dx > 12)return -1;}
    else if(dx < -11 || dx > 11)return -1;
    return 16;
}
static void gleerok_ai(Actor* e) {
    if(e->state==ST_EXPOSED) {
        /* Support is queried by player physics BEFORE gravity and sword
           bounds. The AI must never change displayed z after hit testing. */
        pose(e,LP_RECOVER);
        if(elapsed(e)) {e->v[0]=0;begin(e,ST_RECOVER,60,LP_IDLE);}
    } else if(e->state==ST_TELL) {
        pose(e,LP_TELL);if(elapsed(e)) {begin(e,ST_ATTACK,36,LP_ATTACK);gleerok_breath(e,e->dir,320);gleerok_breath(e,(e->dir+2)&31,288);gleerok_breath(e,(e->dir-2)&31,288);}
    } else if(e->state==ST_ATTACK) {pose(e,LP_ATTACK);if(elapsed(e)) begin(e,ST_ROAM,90,LP_IDLE);}
    else if(e->state==ST_RECOVER) {pose(e,LP_IDLE);if(elapsed(e)) {e->flags|=AF_HURTS;begin(e,ST_ROAM,90,LP_IDLE);}}
    else {
        if((e->timer&31)==0) gleerok_aim(e);
        move(e,96,e->dir);walk_pose(e);if(elapsed(e)) {gleerok_aim(e);begin(e,ST_TELL,32,LP_TELL);}
    }
}

static void appearance(Actor* e,int f) {
    if((f==LF_HELMASAUR&&e->v[2]) || (f==LF_PUFFSTOOL&&e->v[2]) ||
       (f==LF_ROCK_CHUCHU&&e->v[0]) || (f==LF_LAKITU&&e->v[0]) ||
       (f==LF_BIG_OCTOROK&&(e->v[2]&1))) e->frame+=32;
}
void legacy_enemy_update(Actor* e) {
    int f;
    if(!legacy_enemy_owns(e->type)||!gPlayer) return;
    f=family(e);
    if(e->anim_t)--e->anim_t;
    if(f==LF_BIG_OCTOROK && e->timer2) --e->timer2;
    if(e->state==ST_CAPTURE && f==LF_PESTO) {
        e->z=Q16(20);move(e,128,(toward(e)+16)&31);pose(e,LP_ATTACK);
        if(e->timer)--e->timer;
        if(e->timer && e->timer%32==0 && legacy_player_status(LPS_CAPTURE))capture_damage(e,2);
        if(!legacy_player_status(LPS_CAPTURE)||!e->timer) {
            legacy_player_status_clear(LPS_CAPTURE);
            if(gPl.hp>0) {player_cloak_jump();gPlayer->z=Q16(18);}
            begin(e,ST_RETURN,60,LP_RECOVER);
        }
        return;
    }
    if(e->state==ST_CAPTURE && f==LF_MOLDWORM) {
        EnemyTrail* t=trail(e,FALSE);int x,y;
        if(t) {trail_pos(t,MIN((120-e->timer)/6,TRAIL_LEN-1),&x,&y);gPlayer->x=Q16(x);gPlayer->y=Q16(y);}
        pose(e,LP_ATTACK);if(e->timer)--e->timer;
        if(!legacy_player_status(LPS_CAPTURE)||!e->timer) {
            if(!e->timer)capture_damage(e,16);
            legacy_player_status_clear(LPS_CAPTURE);begin(e,ST_RECOVER,30,LP_RECOVER);
        }
        return;
    }
    if(e->v[1]) {--e->v[1];pose(e,LP_HURT);if(f==LF_BOBOMB) bomb_ai(e,f);
        appearance(e,f);
        return;}
    if(e->kb_timer) {
        --e->kb_timer;
        if(f!=LF_MOLDORM&&f!=LF_MOLDWORM&&f!=LF_MADDERPILLAR&&!(e->flags&AF_BOSS)) move(e,e->kb_speed,e->kb_dir);
        pose(e,LP_HURT);appearance(e,f);return;
    }
    switch(f) {
    case LF_BEETLE:
        if(e->state==ST_CAPTURE) {
            if(gKeysDown&(KEY_A|KEY_B|KEY_L|KEY_R)) e->timer=e->timer>8?e->timer-8:1;
            if(!legacy_player_status(LPS_SLOW)||elapsed(e)||gPlayer->z>Q16(2)) {begin(e,ST_RECOVER,40,LP_RECOVER);e->flags|=AF_HURTS;}
            else {e->x=gPlayer->x;e->y=gPlayer->y-Q16(2);e->z=Q16(4);pose(e,LP_ATTACK);}
        } else if(e->state==ST_RECOVER) {e->z=0;pose(e,LP_RECOVER);if(elapsed(e)) begin(e,ST_ROAM,30,LP_IDLE);}
        else {if((gFrame&7)==0) aim(e);move(e,ABS(PX(gPlayer->y)-PX(e->y))>12?192:384,e->dir);walk_pose(e);}break;
    case LF_KEESE:case LF_SMALL_PESTO:case LF_CROW:case LF_PEAHAT:case LF_PESTO:case LF_BOMB_PEAHAT:case LF_TAKKURI:
        flyer_ai(e,f);break;
    case LF_TEKTITE:hop_ai(e,e->type==LE_TEKTITE_GOLDEN_0?6:16,e->type==LE_TEKTITE_1?3:1,e->type==LE_TEKTITE_GOLDEN_0?Q16(3.5):Q16(2.5));break;
    case LF_MINI_SLIME:case LF_SLIME:hop_ai(e,12,1,Q16(1.5));break;
    case LF_OCTOROK:shooter_ai(e,e->type==LE_OCTOROK_GOLDEN_0,LPR_STONE);break;
    case LF_CHUCHU:case LF_ROCK_CHUCHU:case LF_SPINY_CHUCHU:jelly_ai(e,f);break;
    case LF_ROPE:charge_ai(e,30,e->type==LE_ROPE_GOLDEN_0?640:416,112,45);break;
    case LF_STALFOS:skeleton_ai(e);break;
    case LF_KEATON:keaton_ai(e);break;
    case LF_HELMASAUR:charge_ai(e,24,e->v[2]?384:768,96,30);break;
    case LF_BOBOMB:case LF_BOMBAROSSA:bomb_ai(e,f);break;
    case LF_LEEVER:burrow_ai(e,f);break;
    case LF_MULLDOZER:charge_ai(e,20,e->type==LE_MULLDOZER_1?448:352,96,36);break;
    case LF_MOLDORM:case LF_MOLDWORM:case LF_MADDERPILLAR:worm_ai(e,f);break;
    case LF_GHINI:
        if(e->state==ST_CAPTURE) {mirage_ai(e);break;}
        if(e->state==ST_HIDDEN) {pose(e,LP_BURIED);if(elapsed(e)) {e->flags|=AF_HITTABLE|AF_HURTS;begin(e,ST_TELL,30,LP_TELL);}}
        else flyer_ai(e,LF_SMALL_PESTO);
        break;
    case LF_ARMOS:case LF_EYEGORE:statue_ai(e,f);break;
    case LF_SPIKED_BEETLE:
        if(e->v[0]) {pose(e,(e->timer<60&&(gFrame&8))?LP_HURT:LP_RECOVER);if(elapsed(e)) {e->v[0]=0;e->flags|=AF_HURTS;begin(e,ST_ROAM,30,LP_IDLE);}}
        else {charge_ai(e,30,448,112,60);if(e->state==ST_RECOVER)pose(e,LP_IDLE);}
        break;
    case LF_PUFFSTOOL:mushroom_ai(e);break;
    case LF_FIREBALL:case LF_MINI_FIREBALL:flame_ai(e,f);break;
    case LF_CLOUD_PIRANHA:case LF_SPINY_BEETLE:ambush_ai(e,f);break;
    case LF_UNKNOWN50:mirage_ai(e);break;
    case LF_LIKE_LIKE:case LF_RUPEE_LIKE:case LF_GIBDO:grabber_ai(e,f);break;
    case LF_SCISSORS:charge_ai(e,30,320,96,60);break;
    case LF_UNKNOWN4D:case LF_BALL_CHAIN:flail_ai(e,f);break;
    case LF_BOW_MOBLIN:shooter_ai(e,FALSE,LPR_BONE);break;
    case LF_SPEAR_MOBLIN:case LF_DARKNUT:knight_ai(e,f);break;
    case LF_ACRO_BANDIT:acro_ai(e);break;
    case LF_WIZZROBE_FIRE:case LF_WIZZROBE_ICE:case LF_WIZZROBE_WIND:wizard_ai(e,f);break;
    case LF_ROLLOBITE:rollobite_ai(e);break;
    case LF_WISP:case LF_SPARK:wisp_ai(e,f);break;
    case LF_LAKITU:lakitu_ai(e);break;
    case LF_GIANT_CHUCHU:giant_jelly_ai(e);break;
    case LF_BIG_OCTOROK:big_octorok_ai(e);break;
    case LF_GLEEROK:gleerok_ai(e);
        if(e->state!=ST_EXPOSED&&e->state!=ST_RECOVER) {int hx,hy;gleerok_head(e,&hx,&hy);touch_at(e,hx,hy,8,9,4,-1);}
        break;
    }
    if((f==LF_MOLDORM||f==LF_MADDERPILLAR||f==LF_MOLDWORM) && e->state!=ST_HIDDEN && e->state!=ST_RISE) {
        EnemyTrail* t=trail(e,FALSE);int i,n=f==LF_MOLDWORM?8:f==LF_MADDERPILLAR?6:4,x,y;
        if(t) for(i=1;i<=n;i++) {trail_pos(t,MIN(i*3,TRAIL_LEN-1),&x,&y);touch_at(e,x,y-7,6,6,e->damage,-1);}
    }
    appearance(e,f);
}

static bool8 front_hit(const Actor* e,int from) {
    int d=(from+16-facing_to_dir(e->facing))&31;return d<=5||d>=27;
}
static bool8 blocked(Actor* e) {if(!e->anim_t){fx_spawn(FX_CLANG,PX(e->x),PX(e->y)-9);sfx_play(SFX_BUMP);e->anim_t=6;}return FALSE;}
static bool8 coat_progress(Actor* e,int amount,int target) {
    int n=e->v[0]+amount;e->v[0]=MIN(n,255);return n>=target;
}
static void expose(Actor* e,int ticks) {e->v[0]=1;e->flags&=~AF_HURTS;e->kb_timer=0;begin(e,ST_EXPOSED,ticks,LP_RECOVER);}
static bool8 gust_kind(int k) {return k==LE_HIT_GUST_SMALL||k==LE_HIT_GUST_BIG;}
static bool8 hot_kind(int k) {return k==LE_HIT_LANTERN||k==LE_HIT_FIRE;}
static bool8 actual_damage(int k) {return k==LE_HIT_SWORD||k==LE_HIT_ARROW||k==LE_HIT_BOMB||hot_kind(k)||k==LE_HIT_ICE||k==LE_HIT_THROWN||k==LE_HIT_BEAM||k==LE_HIT_REFLECTED;}

bool8 legacy_enemy_accept_hit(Actor* e,int kind,int* damage,int from_dir) {
    int f=family(e),front=front_hit(e,from_dir);
    bool8 gust=gust_kind(kind);
    if(e->state==ST_CARRY || e->state==ST_HIDDEN || e->state==ST_RISE) return FALSE;
    if(kind==LE_HIT_SHIELD && f!=LF_SPIKED_BEETLE && f!=LF_ROLLOBITE) return FALSE;
    switch(f) {
    case LF_HELMASAUR:
        if(gust && !e->v[2]) {
            if(coat_progress(e,kind==LE_HIT_GUST_BIG?30:1,60)) {e->v[0]=1;e->v[2]=1;e->v[1]=60;pose(e,LP_RECOVER);sfx_play(SFX_SECRET);}
            return FALSE;
        }
        if(!e->v[2] && front && kind!=LE_HIT_BOMB) return blocked(e);
        break;
    case LF_PEAHAT:
        if(e->state!=ST_EXPOSED) {
            if(kind==LE_HIT_BOOMERANG || (gust && coat_progress(e,kind==LE_HIT_GUST_BIG?30:1,60))) expose(e,150);
            else if(actual_damage(kind)) return blocked(e);
            return FALSE;
        }
        break;
    case LF_ROCK_CHUCHU:
        if(!e->v[0]) {
            if(kind==LE_HIT_BOMB || kind==LE_HIT_THROWN || (kind==LE_HIT_SWORD && *damage>=4)) {e->v[0]=1;e->v[1]=24;fx_spawn(FX_PUFF,PX(e->x),PX(e->y)-8);}
            else return blocked(e);
            return FALSE;
        }
        break;
    case LF_SPIKED_BEETLE:
        if(!e->v[0]) {
            if(kind==LE_HIT_SHIELD||kind==LE_HIT_PACCI||kind==LE_HIT_BOMB) {
                e->v[0]=1;e->flags&=~AF_HURTS;e->kb_timer=0;begin(e,ST_EXPOSED,150,LP_RECOVER);sfx_play(SFX_BUMP);
            } else return blocked(e);
            return FALSE;
        }
        break;
    case LF_PUFFSTOOL:
        if(!e->v[2]) {
            if(gust && coat_progress(e,kind==LE_HIT_GUST_BIG?30:1,60)) {e->v[2]=1;e->v[0]=1;pose(e,LP_RECOVER);sfx_play(SFX_SECRET);}
            return FALSE;
        }
        break;
    case LF_EYEGORE:
        if(!front || (kind!=LE_HIT_ARROW&&kind!=LE_HIT_BEAM)) return blocked(e);
        if(e->state==ST_REST) {aim(e);begin(e,ST_TELL,24,LP_TELL);return FALSE;}
        if(e->state!=ST_ATTACK&&e->state!=ST_RECOVER) return blocked(e);
        *damage=kind==LE_HIT_BEAM?e->hp:1;break;
    case LF_ARMOS:
        if(e->state==ST_REST) {aim(e);begin(e,ST_TELL,40,LP_TELL);return FALSE;}
        if(kind==LE_HIT_PACCI) {begin(e,ST_RECOVER,90,LP_RECOVER);return FALSE;}
        if(front && kind!=LE_HIT_BOMB && e->state!=ST_RECOVER) return blocked(e);
        break;
    case LF_DARKNUT:
        if(front && kind!=LE_HIT_BOMB && e->state!=ST_RECOVER) {
            if(kind==LE_HIT_PACCI) {begin(e,ST_RECOVER,24,LP_RECOVER);return FALSE;}
            return blocked(e);
        }
        if(kind==LE_HIT_BOOMERANG) {if(!front) e->v[1]=30;return FALSE;}
        break;
    case LF_SCISSORS:
        if(front && e->state!=ST_RECOVER && kind!=LE_HIT_BOMB) return blocked(e);
        break;
    case LF_SPINY_CHUCHU:
        if(kind==LE_HIT_BOOMERANG||kind==LE_HIT_ICE) {e->v[0]=0;e->v[1]=90;return FALSE;}
        if(e->v[0] && !e->v[1] && kind!=LE_HIT_BOMB) return blocked(e);
        break;
    case LF_CHUCHU:
        if(e->type==LE_CHUCHU_2 && (kind==LE_HIT_ARROW||kind==LE_HIT_BEAM)) {*damage=e->hp;return TRUE;}
        if(e->type==LE_CHUCHU_2 && e->v[0] && !e->v[1]) {
            if(kind==LE_HIT_BOOMERANG||kind==LE_HIT_ICE||gust) {e->v[0]=0;e->v[1]=90;return FALSE;}
            if(kind!=LE_HIT_BOMB) return blocked(e);
        }
        break;
    case LF_LAKITU:
        if(!e->v[0]) {
            if(kind==LE_HIT_PACCI || kind==LE_HIT_GUST_BIG) {
                e->v[0]=1;e->zvel=Q16(2);e->flags&=~AF_FLYING;begin(e,ST_EXPOSED,240,LP_RECOVER);sfx_play(SFX_BUMP);
            }
            return FALSE;
        }
        break;
    case LF_ROLLOBITE:
        if(actual_damage(kind)||kind==LE_HIT_PACCI||kind==LE_HIT_SHIELD||gust) {
            e->flags&=~AF_HURTS;e->kb_timer=0;begin(e,ST_CURL,180,LP_RECOVER);e->zvel=Q16(1);sfx_play(SFX_BUMP);
        }
        return FALSE;
    case LF_WISP:
        if(kind!=LE_HIT_BOOMERANG && kind!=LE_HIT_ARROW && kind!=LE_HIT_BEAM && !gust) return FALSE;
        if(gust && !coat_progress(e,kind==LE_HIT_GUST_BIG?30:1,60)) return FALSE;
        *damage=e->hp;return TRUE;
    case LF_SPARK:
        if(kind!=LE_HIT_BOOMERANG) return FALSE;
        *damage=e->hp;return TRUE;
    case LF_BOBOMB:
        if(!e->v[0]) {e->v[0]=1;e->timer=120;pose(e,LP_TELL);sfx_play(SFX_BOMB_SET);}
        else {e->v[1]=60;pose(e,LP_RECOVER);}
        if(kind==LE_HIT_BOMB||hot_kind(kind)) e->timer=MIN(e->timer,12);
        return FALSE;
    case LF_BOMBAROSSA:
        if(actual_damage(kind)) {e->v[0]=1;e->dir=from_dir;begin(e,ST_ATTACK,45,LP_ATTACK);}
        return FALSE;
    case LF_GIBDO:
        if(hot_kind(kind)) {
            /* Burning is a real form transition, preserving the actor and
               observation rather than spawning a duplicate untracked kill. */
            const LegacyEnemyDef* d=legacy_enemy_def(LE_STALFOS_0);
            e->type=LE_STALFOS_0;e->hp=d->base.hp;e->sheet=d->base.sheet;e->speed=d->base.speed;
            e->hitbox=d->base.hitbox;e->flags=d->base.flags;e->pal=sheets[e->sheet].pal;
            e->w=sheets[e->sheet].w;e->h=sheets[e->sheet].h;enemy_invalidate_frame(e);
            e->v[5]=0;e->v[0]=0;legacy_player_status_clear(LPS_CAPTURE);begin(e,ST_RECOVER,30,LP_RECOVER);
            fx_spawn(FX_FLAME,PX(e->x),PX(e->y)-10);return FALSE;
        }
        break;
    case LF_FIREBALL:case LF_MINI_FIREBALL:
        if(hot_kind(kind)) return FALSE;
        if(kind==LE_HIT_ICE) *damage=e->hp;
        if(f==LF_FIREBALL && *damage>0 && *damage<e->hp) {
            /* Source form0 splits into two linked miniature flames on the
               first nonfatal blow. Each child has its own hitbox and HP. */
            child(e,LE_MINI_FIREBALL_GUY_0,PX(e->x)-6,PX(e->y),0);
            child(e,LE_MINI_FIREBALL_GUY_0,PX(e->x)+6,PX(e->y),0);
            e->v[5]=1;enemy_kill(e);return FALSE;
        }
        break;
    case LF_MOLDORM:case LF_MADDERPILLAR:
        return blocked(e); /* The visible, collidable tail owns damage. */
    case LF_GIANT_CHUCHU:
        if(e->state!=ST_EXPOSED) {
            if(e->type==LE_GIANT_CHUCHU_ELECTRIC && (gFrame%180)<120) return blocked(e);
            if(kind==LE_HIT_BOMB||kind==LE_HIT_SHIELD||kind==LE_HIT_LANTERN) return FALSE;
            if(gust||actual_damage(kind)||kind==LE_HIT_BOOMERANG||kind==LE_HIT_PACCI) {
                int n=gust?(kind==LE_HIT_GUST_BIG?12:1):8;
                if(coat_progress(e,n,48)) expose(e,150);
                else {pose(e,LP_HURT);e->iframes=gust?3:12;}
            }
            return FALSE;
        }
        break;
    case LF_BIG_OCTOROK: {
        static const u8 hp[]={3,1,3,1,3,1,3,0};
        if(e->state==ST_RECOVER || e->timer2) return FALSE;
        if((e->v[2]&1) && hot_kind(kind) && !front) *damage=e->hp;
        else if(kind==LE_HIT_REFLECTED || (actual_damage(kind)&&kind!=LE_HIT_LANTERN) || kind==LE_HIT_BOOMERANG||kind==LE_HIT_PACCI) *damage=1;
        else return FALSE;
        if(*damage>=e->hp && e->v[2]<6) {
            ++e->v[2];e->hp=hp[e->v[2]];e->iframes=24;e->kb_timer=0;begin(e,ST_RECOVER,150,LP_RECOVER);fx_spawn(FX_PUFF,PX(e->x),PX(e->y)-12);sfx_play(SFX_BOSS_HIT);return FALSE;
        }
        e->timer2=24;
        break;
    }
    case LF_GLEEROK:
        /* The visible plated head has a separate spatial hitbox, handled by
           hit_parts; striking the lower body never substitutes for it. */
        if(e->state!=ST_EXPOSED) return blocked(e);
        /* Core damage is handled by its exact back hitbox, not the huge
           boss body. A ground-level swing into the plated snout does nothing. */
        return FALSE;
    case LF_UNKNOWN50:
        if(gust && coat_progress(e,kind==LE_HIT_GUST_BIG?30:1,60)) {*damage=e->hp;return TRUE;}
        if(e->v[3] && actual_damage(kind)) {e->v[1]=60;pose(e,LP_HURT);return FALSE;}
        break;
    default:break;
    }
    if(gust) {
        if(f==LF_BEETLE||f==LF_KEESE||f==LF_SMALL_PESTO||f==LF_PESTO||f==LF_GHINI) {
            if(coat_progress(e,kind==LE_HIT_GUST_BIG?30:1,60)) {*damage=e->hp;return TRUE;}
        }
        return FALSE;
    }
    if(kind==LE_HIT_PACCI||kind==LE_HIT_BOOMERANG) {e->v[1]=f==LF_DARKNUT?24:(f==LF_FIREBALL||f==LF_MINI_FIREBALL)?180:90;pose(e,LP_HURT);return FALSE;}
    if(kind==LE_HIT_ICE) {e->v[1]=90;pose(e,LP_HURT);}
    if(!actual_damage(kind)) return FALSE;
    return *damage>0;
}

bool8 legacy_enemy_contact(Actor* e) {
    int f=family(e),ticks=0;
    if(e->v[1] || e->state==ST_CARRY || e->state==ST_CURL) return TRUE;
    if(PX(gPlayer->z)>12 || e->state==ST_RECOVER || e->state==ST_EXPOSED) return FALSE;
    if(f==LF_BEETLE && e->state!=ST_CAPTURE) {
        legacy_player_status_apply(LPS_SLOW,180);e->flags&=~AF_HURTS;begin(e,ST_CAPTURE,180,LP_ATTACK);sfx_play(SFX_BUMP);return TRUE;
    }
    if(f==LF_PESTO && legacy_player_minish()) ticks=80;
    if(f==LF_LIKE_LIKE) ticks=95;
    if(f==LF_RUPEE_LIKE) ticks=60;
    if(f==LF_GIBDO) ticks=120;
    if((f==LF_UNKNOWN50||f==LF_GHINI)&&e->state==ST_ATTACK) ticks=224;
    if(f==LF_MOLDWORM) ticks=120;
    if(ticks) {
        if(!legacy_player_status(LPS_CAPTURE)) {legacy_player_capture(e,ticks);gPl.shield_up=0;begin(e,ST_CAPTURE,ticks,LP_ATTACK);}
        return TRUE;
    }
    if(f==LF_WISP) {
        legacy_player_status_apply(LPS_DRUGGED,600);sfx_play(SFX_BUMP);
        if(e->type==LE_WISP_1) enemy_kill(e);
        else {e->flags&=~(AF_HURTS|AF_HITTABLE);e->timer2=2;e->flags|=AF_HIDDEN;begin(e,ST_HIDDEN,126,LP_BURIED);}
        return TRUE;
    }
    if(f==LF_TAKKURI && !e->v[5]) {
        int n=MIN(gPl.gilt,gPl.gilt>=500?100:gPl.gilt>=100?25:5);
        gPl.gilt-=n;e->v[5]=n;e->dir=(toward(e)+16)&31;begin(e,ST_ATTACK,120,LP_ATTACK);
    }
    if(f==LF_SPIKED_BEETLE && gPl.shield_up && front_hit(gPlayer,actor_dir_to(e,gPlayer)) && e->state==ST_ATTACK) {
        int damage=0;legacy_enemy_accept_hit(e,LE_HIT_SHIELD,&damage,facing_to_dir(gPlayer->facing));sfx_play(SFX_BUMP);return TRUE;
    }
    if(f==LF_BOMBAROSSA) {explosion(e);enemy_kill(e);return TRUE;}
    if(f==LF_CHUCHU && e->type==LE_CHUCHU_2 && e->v[0]) legacy_player_status_apply(LPS_SHOCK,30);
    return FALSE;
}

void legacy_enemy_on_death(Actor* e) {
    int f=family(e),i;
    if(sPlatformOwner==e-gActors)sPlatformOwner=0;
    for(i=0;i<TRAIL_COUNT;i++) if(sTrails[i].owner==e-gActors) sTrails[i].owner=0;
    if(f==LF_LIKE_LIKE && e->v[5]) legacy_item_grant(e->v[5]==2?LI_MIRROR_SHIELD:LI_SHIELD,1);
    if((f==LF_RUPEE_LIKE||f==LF_TAKKURI) && e->v[5]) gPl.gilt=MIN(9999,gPl.gilt+e->v[5]);
    if(f==LF_LIKE_LIKE||f==LF_RUPEE_LIKE||f==LF_GIBDO||f==LF_MOLDWORM||f==LF_UNKNOWN50||f==LF_GHINI||f==LF_PESTO)
        if(e->state==ST_CAPTURE) legacy_player_status_clear(LPS_CAPTURE);
    if(f==LF_SLIME) {
        static const s8 off[2][2]={{-6,0},{6,0}};
        for(i=0;i<2;i++) if(safe_floor(PX(e->x)+off[i][0],PX(e->y)+off[i][1])) {
            Actor* c=child(e,LE_MINI_SLIME_0,PX(e->x)+off[i][0],PX(e->y)+off[i][1],0);
            if(c) {c->iframes=16;c->zvel=Q16(1.5);c->state=ST_ATTACK;c->dir=(i*11)&31;}
        }
    }
    if(f==LF_UNKNOWN50 && !e->v[3]) {
        for(i=1;i<ACTOR_MAX;i++) {
            Actor* c=&gActors[i];
            if(c->kind==AK_ENEMY && c->type==e->type && c->v[3] && c->v[4]==e-gActors) {
                fx_spawn(FX_PUFF,PX(c->x),PX(c->y)-8);actor_free(c);
            }
        }
    }
    if(f==LF_ACRO_BANDIT) {
        for(i=1;i<ACTOR_MAX;i++) {
            Actor* c=&gActors[i];
            if(c->kind==AK_ENEMY && c->type==e->type && c->v[3] && c->v[4]==e-gActors) {
                c->v[3]=0;c->zvel=Q16(2);c->z=MAX(0,c->z);c->dir=(i*7)&31;begin(c,ST_ATTACK,60,LP_ATTACK);
            }
        }
    }
    if(f==LF_SPARK) legacy_item_spawn(LI_FAIRY,PX(e->x),PX(e->y));
    if(e->flags&AF_BOSS) game_legacy_boss_defeated(e->type);
}

static bool8 box_hits(int x0,int y0,int x1,int y1,int x,int y,int hw,int hh) {
    return !(x+hw<x0||x-hw>x1||y+hh<y0||y-hh>y1);
}
static void part_hurt(Actor* e,int damage,int from_dir) {
    if(damage<=0||e->iframes) return;
    e->hp-=damage;e->iframes=18;e->kb_timer=0;
    fx_spawn(FX_SPARK,PX(e->x),PX(e->y)-8);sfx_play(e->flags&AF_BOSS?SFX_BOSS_HIT:SFX_HIT);
    if(e->hp<=0) enemy_kill(e);
    else {begin(e,ST_RAGE,120,LP_ATTACK);e->dir=(from_dir+8)&31;}
}
bool8 legacy_enemy_hit_parts(Actor* e,int x0,int y0,int x1,int y1,int kind,int damage,int from_dir) {
    int f=family(e),x,y,r,i,n;
    EnemyTrail* t;
    if(e->iframes||!(e->flags&AF_HITTABLE)) return FALSE;
    if(f==LF_MOLDORM||f==LF_MADDERPILLAR||f==LF_MOLDWORM) {
        t=trail(e,FALSE);if(!t||e->state==ST_HIDDEN||e->state==ST_RISE) return FALSE;
        n=f==LF_MOLDWORM?8:f==LF_MADDERPILLAR?6:4;
        for(i=n;i>0;i--) {
            trail_pos(t,MIN(i*3,TRAIL_LEN-1),&x,&y);y-=7;
            if(!box_hits(x0,y0,x1,y1,x,y,6,6)) continue;
            if(f==LF_MOLDWORM && i<n) return blocked(e),TRUE;
            if(i==n && actual_damage(kind)) {
                if(f==LF_MADDERPILLAR && e->state==ST_RAGE) {blocked(e);return TRUE;}
                part_hurt(e,damage,from_dir);
            } else if(kind==LE_HIT_BOOMERANG||kind==LE_HIT_ICE) e->v[1]=60;
            else blocked(e);
            return TRUE;
        }
    }
    if(f==LF_GLEEROK && e->state!=ST_EXPOSED) {
        gleerok_head(e,&x,&y);
        if(box_hits(x0,y0,x1,y1,x,y,8,10)) {
            if(kind==LE_HIT_PACCI && front_hit(e,from_dir)) {expose(e,210);sfx_play(SFX_SECRET);}
            else blocked(e);
            return TRUE;
        }
    }
    if(f==LF_GLEEROK && e->state==ST_EXPOSED) {
        x=PX(e->x);y=PX(e->y)-24;
        /* player_sword_box already includes Bloom's displayed z offset. */
        if(box_hits(x0,y0,x1,y1,x,y,7,8)) {
            if((kind==LE_HIT_SWORD&&PX(gPlayer->z)>=12)||kind==LE_HIT_ARROW||kind==LE_HIT_BEAM||kind==LE_HIT_BOMB) {
                int hp=e->hp;part_hurt(e,damage,from_dir);
                if(e->kind==AK_ENEMY) {e->state=ST_EXPOSED;e->timer=MIN(210,e->timer+30);if(hp!=e->hp) pose(e,LP_HURT);}
            } else blocked(e);
            return TRUE;
        }
    }
    if(f==LF_SCISSORS && e->state==ST_ATTACK) {
        int d=facing_to_dir(e->facing);
        x=PX(e->x)+((SIN(d*8)*19)>>14);y=PX(e->y)-7-((COS(d*8)*19)>>14);
        if(box_hits(x0,y0,x1,y1,x,y,8,6)) {if(kind==LE_HIT_BOOMERANG||kind==LE_HIT_PACCI) {e->v[1]=60;begin(e,ST_RECOVER,90,LP_RECOVER);}else blocked(e);return TRUE;}
    }
    if(f==LF_BALL_CHAIN||f==LF_UNKNOWN4D) {
        flail_point(e,&x,&y,&r);
        if(box_hits(x0,y0,x1,y1,x,y,7,7)) {
            if(kind==LE_HIT_BOOMERANG||kind==LE_HIT_PACCI) {e->v[1]=45;begin(e,ST_RECOVER,60,LP_RECOVER);}
            blocked(e);return TRUE;
        }
    }
    return FALSE;
}

void legacy_enemy_extra_draw(Actor* e) {
    int f=family(e),i,x,y,r,n;
    EnemyTrail* t;
    if(e->flags&AF_HIDDEN) return;
    if(f==LF_MOLDORM||f==LF_MOLDWORM||f==LF_MADDERPILLAR) {
        t=trail(e,FALSE);if(!t||e->state==ST_HIDDEN||e->state==ST_RISE) return;
        n=f==LF_MOLDWORM?8:f==LF_MADDERPILLAR?6:4;
        for(i=n;i>0;i--) {
            trail_pos(t,MIN(i*3,TRAIL_LEN-1),&x,&y);
            draw_part(x,y-7,0,i==n?(f==LF_MADDERPILLAR&&e->state==ST_RAGE?PART_ORB:PART_TAIL):PART_SEGMENT,PAL_OBJ_BLIGHT,2);
        }
    }
    if(f==LF_BALL_CHAIN||f==LF_UNKNOWN4D) {
        int sx=PX(e->x),sy=PX(e->y)-7;
        flail_point(e,&x,&y,&r);
        for(i=8;i<r;i+=8) {
            int dx=sx+((x-sx)*i)/r,dy=sy+((y-sy)*i)/r;
            draw_part(dx,dy,0,PART_BONE,PAL_OBJ_BLIGHT,2);
        }
        draw_part(x,y,0,PART_ORB,PAL_OBJ_BLIGHT,1);
    }
    if(f==LF_SCISSORS && (e->state==ST_TELL||e->state==ST_ATTACK)) {
        int d=facing_to_dir(e->facing),spread=e->state==ST_TELL?4:1;
        x=PX(e->x)+((SIN(d*8)*18)>>14);y=PX(e->y)-7-((COS(d*8)*18)>>14);
        draw_part(x-spread,y-2,0,PART_BONE,PAL_OBJ_BLIGHT,1);draw_part(x+spread,y+2,0,PART_BONE,PAL_OBJ_BLIGHT,1);
    }
}

bool8 legacy_enemy_liftable(const Actor* e) {
    if(!e||e->kind!=AK_ENEMY||!legacy_enemy_owns(e->type)) return FALSE;
    return (family(e)==LF_ROLLOBITE&&e->state==ST_CURL) || (family(e)==LF_BOBOMB&&e->v[0]&&e->v[1]);
}
bool8 legacy_enemy_lift(Actor* e) {
    if(!legacy_enemy_liftable(e)) return FALSE;
    e->flags&=~(AF_HURTS|AF_HITTABLE);e->kb_timer=0;begin(e,ST_CARRY,e->timer,LP_RECOVER);return TRUE;
}
bool8 legacy_enemy_throw(Actor* e,int direction,int distance) {
    if(!e||e->kind!=AK_ENEMY||!legacy_enemy_owns(e->type)||e->state!=ST_CARRY) return FALSE;
    e->flags|=AF_HITTABLE;e->dir=direction;face_dir(e);e->z=Q16(14);e->zvel=Q16(1.5);
    e->speed=CLAMP(distance,0,32)*8; /*32ballistic frames: distance/32 px per tick*/
    e->v[1]=0;begin(e,ST_THROWN,MIN(120,MAX(8,distance)),LP_ATTACK);return TRUE;
}

bool8 legacy_enemy_can_spawn(int type) {
    const LegacyEnemyDef* d=legacy_enemy_def(type);
    int i,n=0,trail_n=0,cost=0,f;
    if(!d) return FALSE;
    f=d->family;
    if(!sChildMode) {
        if(f==LF_WISP && !(gPl.items2&ITEM2_BOW) && !legacy_item_owned(LI_LIGHT_ARROW) &&
           !legacy_item_owned(LI_BOOMERANG) && !legacy_item_owned(LI_MAGIC_BOOMERANG) &&
           !legacy_item_owned(LI_GUST_JAR) && !legacy_item_owned(LI_SKILL_SWORD_BEAM))return FALSE;
        if(f==LF_SPARK&&!legacy_item_owned(LI_BOOMERANG)&&!legacy_item_owned(LI_MAGIC_BOOMERANG)) return FALSE;
        if(f==LF_LAKITU&&!legacy_item_owned(LI_PACCI_CANE)) return FALSE;
        if(f==LF_EYEGORE&&!(gPl.items2&ITEM2_BOW)&&!legacy_item_owned(LI_LIGHT_ARROW)&&!legacy_item_owned(LI_SKILL_SWORD_BEAM)) return FALSE;
        if(f==LF_PUFFSTOOL&&!legacy_item_owned(LI_GUST_JAR)) return FALSE;
        if(f==LF_ROCK_CHUCHU&&!(gPl.items&ITEM_BOMBS)&&!legacy_item_owned(LI_SKILL_ROCK_BREAKER)&&gPl.sword_dmg<4) return FALSE;
        if(f==LF_GLEEROK&&!legacy_item_owned(LI_PACCI_CANE)) return FALSE;
        if(f==LF_ROLLOBITE) {
            bool8 pit=FALSE;int x,y;
            for(y=1;y<gRoom.h-1&&!pit;y++) for(x=1;x<gRoom.w-1;x++) if(room_type(x,y)==TT_PIT) {pit=TRUE;break;}
            if(!pit) return FALSE;
        }
    }
    for(i=1;i<ACTOR_MAX;i++) {
        Actor* e=&gActors[i];const LegacyEnemyDef* q;
        if(e->kind!=AK_ENEMY) continue;
        q=legacy_enemy_def(e->type);
        if(!q) {cost++;continue;}
        if(e->v[3]) continue;
        if(q->family==f) n++;
        if(q->family==LF_MOLDORM||q->family==LF_MOLDWORM||q->family==LF_MADDERPILLAR) trail_n++;
        cost+=q->cost;
    }
    if(!sChildMode && (n>=d->cap||cost+d->cost>26)) return FALSE;
    if((f==LF_MOLDORM||f==LF_MOLDWORM||f==LF_MADDERPILLAR)&&trail_n>=TRAIL_COUNT) return FALSE;
    return actor_count(AK_ENEMY)<28;
}
int legacy_enemy_pick(int tier,u32 roll) {
    int i,start=roll%LEGACY_CURATED_COUNT;
    tier=MAX(1,MIN(6,tier));
    for(i=0;i<LEGACY_CURATED_COUNT;i++) {
        int n=(start+i)%LEGACY_CURATED_COUNT;
        if(gLegacyEnemyDefs[n].tier==tier && legacy_enemy_can_spawn(n+LEGACY_ENEMY_BASE)) return n+LEGACY_ENEMY_BASE;
    }
    for(i=0;i<LEGACY_CURATED_COUNT;i++) if(gLegacyEnemyDefs[i].tier<=tier&&legacy_enemy_can_spawn(i+LEGACY_ENEMY_BASE)) return i+LEGACY_ENEMY_BASE;
    return -1;
}

bool8 legacy_projectile_update(Actor* p) {
    int type=p->type,px,py,x0,y0,x1,y1,i;
    if(type<96||type>103) return FALSE;
    if(elapsed(p)) {actor_free(p);return TRUE;}
    if(type==LPR_BOMB) {
        if(p->speed) actor_move_free(p,p->speed,p->dir);
        actor_gravity(p);
        if(p->z<=0) {explosion(p);actor_free(p);return TRUE;}
        /* A small fixed ground ring telegraphs the real point of impact. */
        return TRUE;
    }
    actor_move_free(p,p->speed,p->dir);px=PX(p->x);py=PX(p->y);
    if(px<4||py<8||px>room_px_w()-4||py>room_px_h()-4||room_solid_px(px,py-6)) {
        fx_spawn(FX_SPARK,px,py-6);actor_free(p);return TRUE;
    }
    if(!p->v[0]) {
        bool8 contact=actors_overlap(p,gPlayer);
        bool8 blade=player_sword_box(&x0,&y0,&x1,&y1) && actor_box_overlap(p,x0,y0,x1,y1);
        bool8 shield=contact && gPl.shield_up && front_hit(gPlayer,p->dir);
        if((type==LPR_STONE||type==LPR_BONE) && (blade||shield)) {
            p->dir=facing_to_dir(gPlayer->facing);p->speed=768;p->v[0]=1;p->timer=90;p->z=0;
            fx_spawn(FX_CLANG,px,py-6);sfx_play(SFX_BUMP);return TRUE;
        }
        if(shield && type!=LPR_WIND) {fx_spawn(FX_CLANG,px,py-6);actor_free(p);return TRUE;}
        if(contact && player_is_vulnerable()) {
            if(type==LPR_WIND) {
                actor_move(gPlayer,448,p->dir);legacy_player_status_apply(LPS_SLOW,30);sfx_play(SFX_BUMP);
            } else if(player_hurt(p->damage,p->dir)) {
                if(type==LPR_FIRE) legacy_player_status_apply(LPS_BURN,120);
                if(type==LPR_ICE) legacy_player_status_apply(LPS_FREEZE,90);
                if(type==LPR_SHOCK) legacy_player_status_apply(LPS_SHOCK,45);
                if(type==LPR_SPORE) legacy_player_status_apply(LPS_SLOW,120);
            }
            actor_free(p);return TRUE;
        }
    } else {
        for(i=1;i<ACTOR_MAX;i++) {
            Actor* e=&gActors[i];
            if(e->kind!=AK_ENEMY || !(e->flags&AF_HITTABLE) || e->iframes) continue;
            if(legacy_enemy_owns(e->type) && legacy_enemy_hit_parts(e,px-4,py-10,px+4,py-2,LE_HIT_REFLECTED,p->damage,p->dir)) {actor_free(p);return TRUE;}
            if(actors_overlap(p,e)) {legacy_item_hit(e,LE_HIT_REFLECTED,p->damage,p->dir,0);actor_free(p);return TRUE;}
        }
    }
    return TRUE;
}
bool8 legacy_projectile_draw(Actor* p) {
    if(p->type<96||p->type>103) return FALSE;
    if(p->type==LPR_BOMB) draw_part(PX(p->x),PX(p->y)-4,0,PART_MARK,PAL_OBJ_BLIGHT,2);
    actor_draw(p);return TRUE;
}

/* Original additive challenge annex and handoff systems. No existing event,
   region, player art or default loadout is replaced. */
#include "handoff_events.h"
#include "legacy_items.h"
#include "legacy_enemies.h"
#include "player.h"
#include "room.h"
#include "world.h"
#include "game.h"
#include "video.h"
#include "objects.h"
#include "text.h"
#include "ui.h"
#include "sound.h"
#include "util.h"
#include "handoff_objects.h"
#include "handoff_mobility.h"
#include "world_tokens.h"
#include "cream_room.h"
#include "journal.h"
#include "save.h"

#define HBIT(a,n) (((a)[(unsigned)(n)>>3]>>((n)&7))&1)
#define HSET(a,n) ((a)[(unsigned)(n)>>3]|=1u<<((n)&7))
#define FOOD(n) ((gHandoffState.food_mask>>(n))&1u)
#define CARGO_MAGIC 0xCB
#define BOARD_X 7
#define BOARD_Y 8
#define NODE_X 16
#define NODE_Y 11
HandoffState gHandoffState EWRAM_BSS;
u16 gHandoffPuzzleIndex,gHandoffPushes;
u8 gHandoffBoardBlocks[3],gHandoffBoardPlayer,gHandoffBoardSolved;
static struct {
    u32 seed,clock,clean;
    Rng rng;
    u16 tile,timer,invulnerable,cadence,picolyte_ticks,sleep_timer;
    u8 sleep_choice;
    u8 picolyte;
    s16 recipient_x,recipient_y;
    u8 site,kind,phase,count,quota,request,exit,plate,last_plate;
    u8 memory_input,memory_show,prize,theme,scene_active,cargo_next;
    u8 switch_mask,stealth_alert,visited_courier,return_kind;
    u8 cast[5],shares[5],cast_count,flavor,wave_target;
} s __attribute__((section(".ewram_bss.handoff_runtime")));
static void quest_fail(void);
static void refresh_rank(void){u32 score=gHandoffState.score;gHandoffState.rank=score>=2000?4:score>=800?3:score>=250?2:score>=50?1:0;}
static const s8 sDX[4]={0,1,0,-1},sDY[4]={-1,0,1,0};
static const s16 sDesk[8][2]={{7,8},{12,8},{17,8},{22,8},{7,14},{12,14},{17,14},{22,14}};
static const char* const sSiteNames[HS_COUNT]={
 "Annex","Item Cache","Champion","Stranger","Three Waves","Hidden Pot","Fairy Well",
 "Memory: Learn","Memory: Recall","Floor Plates","Block Template","Block Maze","Censers","Clean-up",
 "Survival","Endless Arena","Pot Quest","Hunt Quest","Scavenger Quest","Stealth Quest","Carry Quest",
 "Courier Quest","Block Quest","Portal Trial","Secret Pocket","Boss Trial","Golden Fusion","Traversal Course","Object Workshop"};
static const u8 sFoodItems[20]={LI_BRIOCHE,LI_CROISSANT,LI_CAKE,LI_PIE,LI_QST_DOGFOOD,LI_QST_MUSHROOM,
 LI_QST_BOOK1,LI_QST_BOOK2,LI_QST_BOOK3,LI_QST_TINGLE_TROPHY,LI_JABBERNUT,LI_QST_CARLOV_MEDAL,
 LI_QST_BROKEN_SWORD,LI_SHELLS30,LI_ORB_GREEN,LI_ORB_BLUE,LI_ORB_RED,LI_QST_SWORD,LI_UNUSED_SWORD,LI_GREEN_SWORD};
static int sx(int tx){return tx*16+8;}
static int sy(int ty){return ty*16+14;}
static bool8 near(int x,int y,int radius){return gPlayer&&ABS(PX(gPlayer->x)-x)<=radius&&ABS(PX(gPlayer->y)-y)<=radius;}
static bool8 finished(void){return HBIT(gHandoffState.completed,s.site);}
static void say(const char* message){textbox_open(message);}
static void clear_bytes(void* p,int n){u8* out=p;while(n--)*out++=0;}
static char* cat(char* p,const char* t){while(*t)*p++=*t++;*p=0;return p;}
static char* num(char* p,int n){char tmp[12];vwf_num(tmp,n,0);return cat(p,tmp);}
static void give(int item){
 if(item>=HANDOFF_GOLD_FLOW&&item<=HANDOFF_GOLD_RIGHT){gHandoffState.gold_owned|=1<<(item-HANDOFF_GOLD_FLOW);journal_note_gold_half(item-HANDOFF_GOLD_FLOW);journal_note_legacy_item(LI_KINSTONE);sfx_play(SFX_KEY);handoff_notify(HN_ITEM,gGame.area,gGame.cell,item);}
 else if(item==HANDOFF_FLEET){gHandoffState.food_mask|=1u<<HF_FLEET;s.invulnerable=120;}
 else legacy_item_grant(item,1);
}
static const char* item_name(int item){
 static const char* const gold[]={"Flow gold half","Left gold half","Middle gold half","Right gold half"};
 const LegacyItemDef* d;
 if(item==HANDOFF_FLEET)return "Golden croissant: Fleet";
 if(item>=HANDOFF_GOLD_FLOW&&item<=HANDOFF_GOLD_RIGHT)return gold[item-HANDOFF_GOLD_FLOW];
 d=legacy_item_def(item);return d?d->name:"Fifty gilt";
}
static bool8 bottle_empty(void){int i;for(i=0;i<4;i++)if(legacy_item_owned(LI_BOTTLE1+i)&&!gLegacyInventory.bottles[i])return TRUE;return FALSE;}
static bool8 eligible(int item){
 const LegacyItemDef* d=legacy_item_def(item);int i;
 if(item>=HANDOFF_GOLD_FLOW)return !(gHandoffState.gold_owned&(1<<(item-HANDOFF_GOLD_FLOW)));
 if(!d)return FALSE;
 if(!handoff_item_unlocked(item))return FALSE;
 for(i=0;i<20;i++)if(sFoodItems[i]==item){if(FOOD(i))return FALSE;return item!=LI_GREEN_SWORD||legacy_item_owned(LI_SKILL_SWORD_BEAM);}
 if(!(d->flags&LIF_REPEAT)&&legacy_item_owned(item))return FALSE;
 if(item==LI_BOTTLE1){for(i=0;i<4;i++)if(!legacy_item_owned(LI_BOTTLE1+i))return TRUE;return FALSE;}
 if(item==LI_BOMBBAG)return legacy_item_owned(LI_BOMBS)&&gLegacyInventory.bomb_bag<3;
 if(item==LI_LARGE_QUIVER)return legacy_item_owned(LI_BOW)&&gLegacyInventory.quiver<3;
 if(item==LI_REMOTE_BOMBS)return legacy_item_owned(LI_BOMBS);
 if(item==LI_LIGHT_ARROW||item==LI_ARROW_BUTTERFLY)return legacy_item_owned(LI_BOW);
 if(item==LI_MAGIC_BOOMERANG)return legacy_item_owned(LI_BOOMERANG);
 if(item==LI_BLUE_SWORD)return legacy_item_owned(LI_RED_SWORD);
 if(item==LI_SKILL_DOWN_THRUST)return legacy_item_owned(LI_ROCS_CAPE);
 if(item==LI_SKILL_GREAT_SPIN||item>=LI_SKILL_FAST_SPIN)return legacy_item_owned(LI_SKILL_SPIN_ATTACK);
 if(item==LI_GREEN_SWORD)return legacy_item_owned(LI_SKILL_SWORD_BEAM)&&!FOOD(HF_BEAM_ANY);
 if(item==LI_DIG_BUTTERFLY)return legacy_item_owned(LI_MOLE_MITTS);
 if(item==LI_SWIM_BUTTERFLY)return legacy_item_owned(LI_FLIPPERS);
 if(item==LI_BOTTLE_BLUE_POTION||item==LI_BOTTLE_RED_POTION||item==LI_BOTTLE_FAIRY||
    (item>=LI_CHARM_NAYRU&&item<=LI_CHARM_DIN))return bottle_empty();
 return TRUE;
}
typedef struct{u16 item;u8 cat,tier,repeat;} Reward;
static const Reward sRewards[]={
 {LI_RUPEE50,LCAT_REWARD,0,1},
 {LI_HEART_PIECE,LCAT_REWARD,0,1},
 {LI_BOTTLE_BLUE_POTION,LCAT_REWARD,0,1},
 {LI_BOTTLE1,LCAT_REWARD,0,1},
 {LI_RUPEE100,LCAT_REWARD,1,1},
 {LI_BOTTLE_RED_POTION,LCAT_REWARD,1,1},
 {LI_RUPEE200,LCAT_REWARD,2,1},
 {LI_HEART_CONTAINER,LCAT_REWARD,2,1},
 {LI_BOTTLE_FAIRY,LCAT_REWARD,2,1},
 {LI_BOW,LCAT_WEAPON,0,0},
 {LI_BOMBS,LCAT_WEAPON | LCAT_KEY,0,0},
 {LI_BOOMERANG,LCAT_WEAPON,0,0},
 {LI_BOMBBAG,LCAT_WEAPON,0,1},
 {LI_LARGE_QUIVER,LCAT_WEAPON,0,1},
 {LI_REMOTE_BOMBS,LCAT_WEAPON,1,0},
 {LI_BOTTLE1,LCAT_WEAPON,1,1},
 {LI_GUST_JAR,LCAT_WEAPON,1,0},
 {LI_FIRE_ROD,LCAT_WEAPON,1,0},
 {LI_RED_SWORD,LCAT_WEAPON,1,0},
 {LI_BLUE_SWORD,LCAT_WEAPON,2,0},
 {LI_QST_LONLON_KEY,LCAT_KEY,1,0},
 {LI_QST_GRAVEYARD_KEY,LCAT_KEY,1,0},
 {HANDOFF_GOLD_FLOW,LCAT_KEY,1,0},
 {HANDOFF_GOLD_LEFT,LCAT_KEY,1,0},
 {HANDOFF_GOLD_MIDDLE,LCAT_KEY,1,0},
 {HANDOFF_GOLD_RIGHT,LCAT_KEY,1,0},
 {LI_MAGIC_BOOMERANG,LCAT_WEAPON,2,0},
 {LI_MIRROR_SHIELD,LCAT_WEAPON,2,0},
 {LI_LIGHT_ARROW,LCAT_WEAPON,2,0},
 {LI_SKILL_SPIN_ATTACK,LCAT_SKILL,0,0},
 {LI_SKILL_ROCK_BREAKER,LCAT_SKILL,0,0},
 {LI_SKILL_ROLL_ATTACK,LCAT_SKILL,0,0},
 {LI_SKILL_DASH_ATTACK,LCAT_SKILL,1,0},
 {LI_SKILL_PERIL_BEAM,LCAT_SKILL,1,0},
 {LI_SKILL_SWORD_BEAM,LCAT_SKILL,1,0},
 {LI_SKILL_DOWN_THRUST,LCAT_SKILL,2,0},
 {LI_SKILL_GREAT_SPIN,LCAT_SKILL,2,0},
 {LI_SKILL_FAST_SPIN,LCAT_SKILL,2,0},
 {LI_SKILL_FAST_SPLIT,LCAT_SKILL,2,0},
 {LI_SKILL_LONG_SPIN,LCAT_SKILL,2,0},
 {LI_ARROW_BUTTERFLY,LCAT_STAT,0,0},
 {LI_DIG_BUTTERFLY,LCAT_STAT,0,0},
 {LI_SWIM_BUTTERFLY,LCAT_STAT,0,0},
 {LI_CHARM_NAYRU,LCAT_STAT,2,1},
 {LI_CHARM_FARORE,LCAT_STAT,2,1},
 {LI_CHARM_DIN,LCAT_STAT,2,1},
 {LI_BRIOCHE,LCAT_CHARM,1,0},
 {LI_CROISSANT,LCAT_CHARM,1,0},
 {LI_CAKE,LCAT_CHARM,1,0},
 {LI_PIE,LCAT_CHARM,1,0},
 {LI_QST_DOGFOOD,LCAT_CHARM,1,0},
 {LI_QST_MUSHROOM,LCAT_CHARM,1,0},
 {LI_QST_BOOK1,LCAT_CHARM,1,0},
 {LI_QST_BOOK2,LCAT_CHARM,1,0},
 {LI_QST_BOOK3,LCAT_CHARM,1,0},
 {LI_QST_TINGLE_TROPHY,LCAT_CHARM,1,0},
 {LI_JABBERNUT,LCAT_CHARM,1,0},
 {LI_QST_CARLOV_MEDAL,LCAT_CHARM,1,0},
 {LI_QST_BROKEN_SWORD,LCAT_CHARM,1,0},
 {LI_SHELLS30,LCAT_CHARM,1,0},
 {LI_ORB_GREEN,LCAT_CHARM,2,0},
 {LI_ORB_BLUE,LCAT_CHARM,2,0},
 {LI_ORB_RED,LCAT_CHARM,2,0},
 {LI_QST_SWORD,LCAT_CHARM,1,0},
 {LI_UNUSED_SWORD,LCAT_CHARM,1,0},
 {LI_GREEN_SWORD,LCAT_CHARM,1,0},
 {LI_MAP,LCAT_WEAPON,2,0},
 {LI_COMPASS,LCAT_WEAPON,2,0},
 {LI_PEGASUS_BOOTS,LCAT_KEY,1,0},
 {LI_ROCS_CAPE,LCAT_KEY,1,0},
 {LI_MOLE_MITTS,LCAT_KEY,1,0},
 {LI_FLIPPERS,LCAT_KEY,1,0},
 {LI_LANTERN_OFF,LCAT_KEY,1,0},
 {LI_OCARINA,LCAT_KEY,1,0},
 {LI_PACCI_CANE,LCAT_KEY,2,0},
 {LI_GRIP_RING,LCAT_KEY,2,0},
 {LI_POWER_BRACELETS,LCAT_KEY,2,0},
};
static int reward_pick(int cats,int tier,u32 roll){
 int i,n=0,chosen=LI_RUPEE50,pass;
 for(pass=0;pass<3;pass++){
  n=0;
  for(i=0;i<ARRAY_COUNT(sRewards);i++){
   const Reward* r=&sRewards[i];
   if(!(r->cat&cats)||r->tier!=tier||!eligible(r->item))continue;
   if(!r->repeat&&r->item<LI_COUNT&&legacy_item_owned(r->item)&&r->item!=LI_GREEN_SWORD)continue;
   if(hash32(roll,i)%(++n)==0)chosen=r->item;
  }
  if(n)return chosen;
  tier=(tier+2)%3;
 }
 return LI_RUPEE50;
}
static int random_reward(int tier){
 if(tier<0){int r=rng_range(&s.rng,100);if(FOOD(HF_RARE_LUCK))r=MIN(99,r+10);tier=r<60?0:r<90?1:2;}
 return reward_pick(LCAT_KEY|LCAT_REWARD|LCAT_WEAPON|LCAT_SKILL|LCAT_STAT|LCAT_CHARM,tier,rng_next(&s.rng));
}
static void roll_draft(void){
 static const u8 fallback[]={LI_RUPEE50,LI_HEART_PIECE,LI_RUPEE20};
 int i,j,cats=gHandoffState.draft_round==0?LCAT_KEY:gHandoffState.draft_round==1?(LCAT_REWARD|LCAT_STAT):LCAT_SKILL;
 for(i=0;i<3;i++){
  for(j=0;j<64;j++){
   int item=reward_pick(cats,gHandoffState.draft_round==1?(j>24?1:j>12?0:2):(rng_range(&s.rng,10)<6?0:1),rng_next(&s.rng));
   if((i>0&&item==gHandoffState.draft[0])||(i>1&&item==gHandoffState.draft[1]))continue;
   gHandoffState.draft[i]=item;break;
  }
  if(j==64)for(j=0;j<3;j++){
   int item=fallback[j];if((i>0&&item==gHandoffState.draft[0])||(i>1&&item==gHandoffState.draft[1]))continue;
   gHandoffState.draft[i]=item;break;
  }
 }
}
static void shop_roll(void){
 int i;
 for(i=0;i<6;i++){
  int tier=i<3?0:i<5?1:2;
  gHandoffState.stock[i]=reward_pick(LCAT_REWARD|LCAT_WEAPON|LCAT_SKILL|LCAT_STAT,tier,rng_next(&s.rng));
  gHandoffState.prices[i]=i<3?75:i<5?200:450;
 }
 gHandoffState.stock[0]=LI_HEART_PIECE;gHandoffState.prices[0]=100;
 gHandoffState.stock[1]=LI_BOMBS5;gHandoffState.prices[1]=25;
 gHandoffState.stock[2]=LI_ARROWS10;gHandoffState.prices[2]=25;
}
void handoff_init(void){clear_bytes(&gHandoffState,sizeof(gHandoffState));clear_bytes(&s,sizeof(s));s.request=255;}
void handoff_new_run(u32 seed){
 u32 score=gHandoffState.score;u16 wins=gHandoffState.wins,deaths=gHandoffState.deaths,runs=gHandoffState.runs;
 u8 difficulty=gHandoffState.difficulty,highest=gHandoffState.highest_difficulty,mode=gHandoffState.entitlement_mode;
 clear_bytes(&gHandoffState,sizeof(gHandoffState));
 gHandoffState.score=score;gHandoffState.wins=wins;gHandoffState.deaths=deaths;gHandoffState.runs=runs+1;
 gHandoffState.difficulty=MIN(12,difficulty);gHandoffState.highest_difficulty=highest;gHandoffState.entitlement_mode=mode;
 gHandoffState.rank=score>=2000?4:score>=800?3:score>=250?2:score>=50?1:0;
 clear_bytes(&s,sizeof(s));s.request=255;rng_seed(&s.rng,seed^0xA44E177u);
 gHandoffState.fuser_cell[0]=gWorld.entry;gHandoffState.fuser_cell[1]=rng_range(&s.rng,25);gHandoffState.fuser_cell[2]=rng_range(&s.rng,25);
 gHandoffState.fuser_shape[0]=rng_range(&s.rng,3);gHandoffState.fuser_shape[1]=rng_range(&s.rng,3);gHandoffState.fuser_shape[2]=rng_range(&s.rng,3);
 gHandoffState.memory_length=4;
 for(int i=0;i<6;i++)gHandoffState.memory_code[i]=rng_range(&s.rng,4);
 shop_roll();
}
void handoff_on_win(void){gHandoffState.wins++;gHandoffState.score+=100+25*gHandoffState.difficulty;gHandoffState.difficulty=MIN(12,gHandoffState.difficulty+1);gHandoffState.highest_difficulty=MAX(gHandoffState.highest_difficulty,gHandoffState.difficulty);refresh_rank();}
void handoff_on_death(void){quest_fail();gHandoffState.deaths++;if(gHandoffState.difficulty>1)gHandoffState.difficulty--;else gHandoffState.difficulty=1;}
bool8 handoff_apply_item_effect(int item,int amount){
 int i;
 if(amount<=0)return FALSE;
 if(item>=LI_BOTTLE_PICOLYTE_RED&&item<=LI_BOTTLE_PICOLYTE_WHITE){s.picolyte=item-LI_BOTTLE_PICOLYTE_RED+1;s.picolyte_ticks=1800;return TRUE;}
 if(item==LI_SHELLS){s.invulnerable=180;return FALSE;}
 if(item>=LI_CHARM_NAYRU&&item<=LI_CHARM_DIN){gHandoffState.charm_mask|=1<<(item-LI_CHARM_NAYRU);return TRUE;}
 for(i=0;i<20;i++)if(sFoodItems[i]==item){
  if(item==LI_GREEN_SWORD&&!legacy_item_owned(LI_SKILL_SWORD_BEAM))return FALSE;
  gHandoffState.food_mask|=1u<<i;
   return TRUE;
 }
 return FALSE;
}
int handoff_outgoing_damage(int d){if(d<=0)return 0;d+=FOOD(HF_SWORD_EDGE);d-=FOOD(HF_CURSE_BLUNT);d=MAX(1,d);if(gHandoffState.charm_mask&HC_FARORE)d=d*3/2;if(gHandoffState.charm_mask&HC_DIN)d*=2;return MAX(1,d);}
int handoff_incoming_damage(int d){if(d<=0)return 0;if(s.invulnerable)return 0;if(gHandoffState.charm_mask&HC_NAYRU)d/=4;if(gHandoffState.charm_mask&HC_FARORE)d/=2;return MAX(1,d);}
int handoff_walk_speed(int v){return FOOD(HF_WALK_SPEED)?v*3/2:v;}
int handoff_enemy_speed(int v){return FOOD(HF_CURSE_ENEMY_SPEED)?v*3/2:v;}
int handoff_enemy_fire_delay(int v){return FOOD(HF_CURSE_FIRE_RATE)?MAX(1,v*2/3):v;}
int handoff_player_knockback(int v){if(FOOD(HF_STEADFAST))return 0;return FOOD(HF_CURSE_KNOCKBACK)?v*2:v;}
int handoff_sword_knockback(int v){return FOOD(HF_SWORD_KNOCKBACK)?v*2:v;}
int handoff_immunities(void){return (FOOD(HF_IMMUNE_FIRE)?1:0)|(FOOD(HF_IMMUNE_ICE)?2:0)|(FOOD(HF_IMMUNE_SHOCK)?4:0);}
bool8 handoff_beam_any_health(void){return FOOD(HF_BEAM_ANY);}
int handoff_shop_price(int p){return FOOD(HF_CHEAP_SHOP)?MIN(50,p):p;}
int handoff_drop_bias(int k){
 int base=k==0?FOOD(HF_DROP_GILT):k==1?FOOD(HF_DROP_KINSTONES):k==2?FOOD(HF_DROP_HEARTS):FOOD(HF_RARE_LUCK);
 int p=s.picolyte_ticks?s.picolyte:0;
 return base||(p==4)||(k==0&&(p==2||p==3))||(k==1&&p==5)||(k==2&&(p==1||p==2))||(k==3&&p==6);
}
int handoff_visual_dim(void){return FOOD(HF_CURSE_DIM)?5:0;}
/* Handoff difficulty table, including genuinely empty easy bands. */
static const u8 sTierWeights[13][6]={
 {100,0,0,0,0,0},{75,25,0,0,0,0},{50,45,5,0,0,0},{25,40,26,6,2,1},
 {18,37,32,10,2,1},{13,33,34,16,3,1},{9,27,35,22,6,1},{6,22,34,27,10,1},
 {4,17,32,31,15,1},{3,13,29,33,21,1},{3,10,25,34,26,2},{2,8,22,34,31,3},{1,7,19,34,35,4}};
int handoff_pick_enemy(int d,int role,u32 roll){
 int i,r=roll%100,tier=1,count=0,chosen=-1;d=CLAMP(d,0,12);
 for(i=0;i<6;i++){if(r<sTierWeights[d][i]){tier=i+1;break;}r-=sTierWeights[d][i];}
 for(i=LEGACY_ENEMY_BASE;i<LE_GIANT_CHUCHU_GREEN;i++){
  const LegacyEnemyDef*def=legacy_enemy_def(i);
  if(!def||def->tier!=tier||(role&&!(def->roles&role))||!legacy_enemy_can_spawn(i))continue;
  if(hash32(roll,i)%(++count)==0)chosen=i;
 }
 return chosen>=0?chosen:legacy_enemy_pick(tier,hash32(roll,d));
}
/* Opt-in entitlement rules never affect the ordinary world or required tool
   trials. The source's paused meta vision is exposed as a separate contract. */
bool8 handoff_item_unlocked(int item){
 const LegacyItemDef*d=legacy_item_def(item);if(!gHandoffState.entitlement_mode||!d)return TRUE;
 if(d->category&LCAT_KEY)return TRUE;
 if(d->tier==0)return TRUE;
 return d->tier==1?(gHandoffState.score>=500||gHandoffState.wins>=1):(gHandoffState.score>=1500||gHandoffState.wins>=2);
}
bool8 handoff_event_unlocked(int kind){
 if(!gHandoffState.entitlement_mode)return TRUE;
 if(kind==HS_POTS||kind==HS_QUEST_POT)return gHandoffState.score>=500;
 if(kind==HS_FAIRY)return gHandoffState.wins>=1;
 if(kind==HS_PORTAL||kind==HS_POCKET||kind==HS_BOSS)return gHandoffState.score>=1500||gHandoffState.wins>=2;
 if(kind==HS_MEMORY_SHOW||kind==HS_MEMORY_INPUT||kind==HS_BLOCK_TEMPLATE||kind==HS_BLOCK_MAZE||(kind>=HS_QUEST_HUNT&&kind<=HS_QUEST_BLOCKS))return gHandoffState.score>=500||gHandoffState.wins>=1;
 return TRUE;
}
bool8 handoff_region_unlocked(int area){return !gHandoffState.entitlement_mode||area!=AREA_CREAM||gHandoffState.score>=500||gHandoffState.wins>=1;}
int handoff_difficulty_cap(void){return gHandoffState.entitlement_mode?MIN(12,3+2*gHandoffState.wins+gHandoffState.score/1500):12;}
u8 handoff_switch_facts(int site){if((unsigned)site>=HANDOFF_SITE_LIMIT)return 0;if(HBIT(gHandoffState.completed,site))return 0xFF;return gGame.area==AREA_HANDOFF&&s.site==site&&s.kind==HS_SWITCHES?s.switch_mask:0;}

/* Native original push boards. These have certificates, not blind random
   blocks that happen to resemble a puzzle. */
#include "handoff_puzzles.inc"
const HandoffPuzzle* handoff_puzzle(int index){return &sPuzzlePool[(unsigned)index%HANDOFF_PUZZLE_COUNT];}
static int step(int c,int d){int x=c%5+sDX[d&3],y=c/5+sDY[d&3];return x<0||x>=5||y<0||y>=5?-1:y*5+x;}
static bool8 axis_ok(int a,int d){return !a||(a==1&&(d&1))||(a==2&&!(d&1));}
static u32 occupied(const u8* blocks){return (1u<<blocks[0])|(1u<<blocks[1])|(1u<<blocks[2]);}
static u32 flood(u32 walls,const u8* blocks,int at){
 u32 seen=0,old,blocked=walls|occupied(blocks);int c,d;
 if(at<0||at>=25||(blocked&(1u<<at)))return 0;
 seen=1u<<at;
 do{old=seen;for(c=0;c<25;c++)if(seen&(1u<<c))for(d=0;d<4;d++){int n=step(c,d);if(n>=0&&!(blocked&(1u<<n)))seen|=1u<<n;}}while(old!=seen);
 return seen;
}
bool8 handoff_puzzle_verify(const HandoffPuzzle* p){
 u8 b[3];int i,player=p->player;
 if(p->length>32||p->minimum>p->length||p->player>=25||p->entry>=25||p->goal>=25)return FALSE;
 for(i=0;i<3;i++){b[i]=p->blocks[i];if(b[i]>=25||p->axes[i]>2||(p->walls&(1u<<b[i])))return FALSE;}
 if(b[0]==b[1]||b[0]==b[2]||b[1]==b[2]||!(flood(p->walls,b,p->entry)&(1u<<player)))return FALSE;
 for(i=0;i<p->length;i++){
  int m=p->solution[i],which=m>>2,d=m&3,c,n,back;
  if(which>2)return FALSE;
  c=b[which];n=step(c,d);back=step(c,(d+2)&3);
  if(n<0||back<0||n==p->entry||n==p->goal||!axis_ok(p->axes[which],d)||((p->walls|occupied(b))&(1u<<n))||!(flood(p->walls,b,player)&(1u<<back)))return FALSE;
  b[which]=n;player=c;
 }
 return p->kind?!!(flood(p->walls,b,player)&(1u<<p->goal)):occupied(b)==p->goals;
}
static bool8 board_kind(void){return s.kind==HS_BLOCK_TEMPLATE||s.kind==HS_BLOCK_MAZE||s.kind==HS_QUEST_BLOCKS;}
static bool8 outside_entry(int x,int y,int c){
 return(c%5==0&&x==-1&&y==c/5)||(c%5==4&&x==5&&y==c/5)||(c/5==0&&y==-1&&x==c%5)||(c/5==4&&y==5&&x==c%5);
}
static void board_paint(void){
 const HandoffPuzzle* p=handoff_puzzle(gHandoffPuzzleIndex);int c,x,y;
 for(y=-1;y<=5;y++)for(x=-1;x<=5;x++){
  if(x>=0&&x<5&&y>=0&&y<5)continue;
  room_set(BOARD_X+x,BOARD_Y+y,(outside_entry(x,y,p->entry)||(p->kind&&outside_entry(x,y,p->goal)))?MT_CAVE_FLOOR0:MT_CAVE_WALL);
 }
 for(c=0;c<25;c++){
  u16 tile=p->walls&(1u<<c)?MT_CAVE_WALL:MT_CAVE_FLOOR0;
  room_set(BOARD_X+c%5,BOARD_Y+c/5,tile);
  if(!p->kind)room_set(19+c%5,BOARD_Y+c/5,p->goals&(1u<<c)?MT_CAVE_FLOOR_SWITCH:MT_CAVE_FLOOR0);
 }
}
void handoff_board_reset(void){
 const HandoffPuzzle* p=handoff_puzzle(gHandoffPuzzleIndex);int i;
 for(i=0;i<3;i++)gHandoffBoardBlocks[i]=p->blocks[i];
 gHandoffBoardPlayer=p->entry;gHandoffPushes=gHandoffBoardSolved=0;
 if(gPlayer)player_set_pos(sx(BOARD_X+p->entry%5),sy(BOARD_Y+p->entry/5));
 sfx_play(SFX_MENU);
}
bool8 handoff_board_push(int d){
 const HandoffPuzzle* p=handoff_puzzle(gHandoffPuzzleIndex);int i,c,next,back,bx,by;u32 region;
 if(!board_kind()||gHandoffBoardSolved||!gPlayer)return FALSE;
 bx=PX(gPlayer->x)/16-BOARD_X;by=PX(gPlayer->y)/16-BOARD_Y;
 if(bx<0||by<0||bx>=5||by>=5)return FALSE;
 c=bx+5*by;
 next=step(c,d);if(next<0)return FALSE;
 for(i=0;i<3;i++)if(gHandoffBoardBlocks[i]==next)break;
 if(i==3)return FALSE;
 back=step(next,d);
 if(back<0||back==p->entry||back==p->goal||!axis_ok(p->axes[i],d)||((p->walls|occupied(gHandoffBoardBlocks))&(1u<<back))){sfx_play(SFX_BUMP);return TRUE;}
 gHandoffBoardBlocks[i]=back;gHandoffBoardPlayer=next;gHandoffPushes++;
 player_set_pos(sx(BOARD_X+next%5),sy(BOARD_Y+next/5));sfx_play(SFX_HIT);
 region=flood(p->walls,gHandoffBoardBlocks,next);
 gHandoffBoardSolved=p->kind?!!(region&(1u<<p->goal)):occupied(gHandoffBoardBlocks)==p->goals;
 return TRUE;
}
bool8 handoff_box_solid(int x0,int y0,int x1,int y1){
 const HandoffPuzzle* p;int tx,ty,i;
 if(gGame.area!=AREA_HANDOFF)return FALSE;
 if(s.kind==HS_TRAVERSAL)return handoff_mobility_box_solid(x0,y0,x1,y1);
 if(s.kind==HS_OBJECT_COURSE)return handoff_objects_box_solid(x0,y0,x1,y1);
 if(!board_kind())return FALSE;
 p=handoff_puzzle(gHandoffPuzzleIndex);
 for(ty=y0/16;ty<=y1/16;ty++)for(tx=x0/16;tx<=x1/16;tx++){
  int x=tx-BOARD_X,y=ty-BOARD_Y,c=y*5+x;
  if(x>=0&&x<5&&y>=0&&y<5){if(p->walls&(1u<<c))return TRUE;for(i=0;i<3;i++)if(gHandoffBoardBlocks[i]==c)return TRUE;}
  /* Only the certified entry/goal pierce the board's ring. */
  else if(x>=-1&&x<=5&&y>=-1&&y<=5){
   int entry=p->entry,goal=p->goal;
   bool8 e=outside_entry(x,y,entry);
   bool8 g=outside_entry(x,y,goal);
   if(!e&&!(p->kind&&g&&gHandoffBoardSolved))return TRUE;
  }
 }
 return FALSE;
}
static void finish(void){
 if(finished())return;
 HSET(gHandoffState.completed,s.site);HSET(gHandoffState.won,s.site);
 s.phase=9;s.prize=1;room_change_overlay(NODE_X,NODE_Y,MT_MYST_CHEST);sfx_play(SFX_SECRET);fx_spawn(FX_SPARK,sx(NODE_X),sy(NODE_Y));
 handoff_notify(s.kind==HS_WAVES||s.kind==HS_ARENA?HN_WAVE:s.kind==HS_BOSS?HN_BOSS:HN_EVENT,AREA_HANDOFF,s.site,0);
}
static void claim(void){
 int item;if(!s.prize||!HBIT(gHandoffState.won,s.site))return;
 s.prize=0;room_change_overlay(NODE_X,NODE_Y,MT_MYST_CHEST_OPEN);gHandoffState.won[s.site>>3]&=~(1<<(s.site&7));
 item=gHandoffState.contract_state==1&&gHandoffState.contract_kind==HC_ITEM&&s.site==HANDOFF_CONTRACT_BASE+gHandoffState.contract_step?gHandoffState.contract_item:random_reward(s.kind==HS_BOSS?2:s.kind==HS_MINIBOSS?1:-1);give(item);sfx_play(SFX_CHEST);
}
typedef struct{u8 min_diff,weight,slots,percent,force;u8 role[5],share[5];} WaveShape;
/* Source's ten ordinary shapes plus its later Elite Trio addition. */
static const WaveShape sShapes[]={
 {0,30,3,100,0,{0,0,0},{34,33,33}},
 {0,12,1,150,0,{LE_ROLE_CHAFF},{100}},
 {2,14,5,100,0,{LE_ROLE_CHAFF,LE_ROLE_FAST,LE_ROLE_FLYER,LE_ROLE_AMBUSH,LE_ROLE_RANGED},{20,20,20,20,20}},
 {2,10,2,100,0,{LE_ROLE_FLYER|LE_ROLE_FAST,LE_ROLE_SLOW},{60,40}},
 {3,10,2,100,0,{LE_ROLE_AMBUSH,LE_ROLE_FAST},{65,35}},
 {4,10,3,90,0,{LE_ROLE_RANGED,LE_ROLE_RANGED,LE_ROLE_FAST},{35,35,30}},
 {4,8,3,100,0,{LE_ROLE_HEAVY,LE_ROLE_CHAFF,LE_ROLE_CHAFF},{15,45,40}},
 {5,6,2,100,0,{LE_ROLE_THIEF,LE_ROLE_FAST},{50,50}},
 {6,6,2,35,0,{LE_ROLE_HEAVY,LE_ROLE_HEAVY},{50,50}},
 {6,8,2,100,0,{LE_ROLE_RANGED,LE_ROLE_SLOW},{40,60}},
 {8,7,1,25,6,{LE_ROLE_HEAVY},{100}}
};
static void cast_wave(void){
 int i,j,total=0,roll,shape=0,budget=20;
 for(i=0;i<ARRAY_COUNT(sShapes);i++)if(sShapes[i].min_diff<=gHandoffState.difficulty)total+=sShapes[i].weight;
 roll=rng_range(&s.rng,total);
 for(i=0;i<ARRAY_COUNT(sShapes);i++)if(sShapes[i].min_diff<=gHandoffState.difficulty){if(roll<sShapes[i].weight){shape=i;break;}roll-=sShapes[i].weight;}
 s.theme=shape;s.cast_count=0;s.flavor=rng_range(&s.rng,4)==0?1+rng_range(&s.rng,5):0;
 for(i=0;i<sShapes[shape].slots;i++){
  int type=-1;
  for(j=0;j<48;j++){
   int n=sShapes[shape].force?legacy_enemy_pick(sShapes[shape].force,rng_next(&s.rng)):handoff_pick_enemy(gHandoffState.difficulty,sShapes[shape].role[i],rng_next(&s.rng));
   const LegacyEnemyDef*d=legacy_enemy_def(n);int k;
   if(!d||d->cost>budget||!legacy_enemy_can_spawn(n))continue;
   for(k=0;k<s.cast_count;k++)if(s.cast[k]==n)break;
   if(k<s.cast_count&&j<32)continue;
   if(s.flavor&&d->theme!=s.flavor&&j<24)continue;
   type=n;budget-=d->cost;break;
  }
  if(type>=0){s.cast[s.cast_count]=type;s.shares[s.cast_count]=sShapes[shape].share[i];s.cast_count++;}
 }
 if(!s.cast_count){s.cast[0]=handoff_pick_enemy(gHandoffState.difficulty,0,rng_next(&s.rng));s.shares[0]=100;s.cast_count=1;}
}
static int wave_pick(void){
 int i,total=0,r;for(i=0;i<s.cast_count;i++)total+=s.shares[i];if(!total)return handoff_pick_enemy(gHandoffState.difficulty,0,rng_next(&s.rng));
 r=rng_range(&s.rng,total);for(i=0;i<s.cast_count;i++){if(r<s.shares[i])return s.cast[i];r-=s.shares[i];}return s.cast[0];
}
static bool8 spawn_one(int forced){
 int attempt,chosen=forced;
 for(attempt=0;attempt<48;attempt++){
  int x=3+rng_range(&s.rng,26),y=4+rng_range(&s.rng,15),px=sx(x),py=sy(y);
  if(gPlayer&&ABS(px-PX(gPlayer->x))<56&&ABS(py-PX(gPlayer->y))<48)continue;
  if(room_box_solid(px-8,py-14,px+8,py)||room_type(x,y)!=TT_FLOOR)continue;
  if(forced<0){
   const LegacyEnemyDef* def;int budget=10+MIN(30,gHandoffState.wave[s.site]);
   chosen=s.cast_count&&attempt<32?wave_pick():handoff_pick_enemy(gHandoffState.difficulty,0,rng_next(&s.rng));def=legacy_enemy_def(chosen);
   if(def&&def->cost>budget/MAX(1,enemies_alive()+1))continue;
  }
  if(!legacy_enemy_can_spawn(chosen))continue;
  if(enemy_spawn(chosen,px,py)){fx_spawn(FX_PUFF,px,py-8);return TRUE;}
 }
 return FALSE;
}
static void refill(int target){int i;for(i=enemies_alive();i<target&&i<7;i++)if(!spawn_one(-1))break;}
static void wave_begin(void){
 int wave=gHandoffState.wave[s.site];
 if(!wave)gHandoffState.wave[s.site]=1;
 cast_wave();
 gHandoffState.remaining[s.site]=MAX(1,(3+MIN(9,wave/2)+gHandoffState.difficulty/3)*sShapes[s.theme].percent/100);
 s.wave_target=CLAMP(gHandoffState.remaining[s.site],1,7);
 refill(s.wave_target);
}
static void quest_fail(void){
 HandoffQuest* q=&gHandoffState.quest;u32 good=0;int i;
 if(q->state!=2)return;
 if(q->kind==HQ_CARRY&&q->cargo_held){q->cargo_held=0;gPl.carry=CARRY_NONE;}
 q->state=4;
 if(q->stake){int cost=q->stake==1?50:q->stake==2?100:200;gPl.gilt-=MIN(gPl.gilt,cost);}
 if(q->stake>=2&&gPl.hp>8)gPl.hp=MAX(1,gPl.hp/2);
 if(q->stake>=3){for(i=0;i<14;i++)if((i<3||i>=6)&&FOOD(i))good|=1u<<i;
  if(good){for(i=0;i<14;i++)if(good&(1u<<i)){gHandoffState.food_mask&=~(1u<<i);break;}}
  else gHandoffState.food_mask|=1u<<(HF_CURSE_KNOCKBACK+rng_range(&s.rng,3));
 }
 say("The contract is lost. Its announced stake has been paid. You can retry or leave.");
}
static void quest_win(void){
 HandoffQuest* q=&gHandoffState.quest;
 if(q->state==3)return;
 q->state=3;gHandoffState.score+=20+5*q->difficulty;refresh_rank();
 handoff_notify(HN_QUEST,gGame.area,gGame.cell,0);finish();
}
static void quest_start(int kind){
 HandoffQuest* q=&gHandoffState.quest;char msg[288];char* p;
 clear_bytes(q,sizeof(*q));q->kind=kind;q->state=1;q->difficulty=gHandoffState.difficulty;
 q->stake=q->difficulty<4?0:q->difficulty<8?1:q->difficulty<12?2:3;
 q->origin_area=AREA_HANDOFF;q->origin_cell=s.site;q->quota=kind==HQ_HUNT?7+rng_range(&s.rng,7):kind==HQ_POT?6:1;
 q->timer=kind==HQ_HUNT?1800:kind==HQ_STEALTH?2400:kind==HQ_SCAV?2700:0;
 q->target_area=AREA_FOREST;q->target_cell=gWorld.entry;
 q->cargo_x=sx(8);q->cargo_y=sy(17);q->receiver_x=sx(24);q->receiver_y=sy(5);q->cargo_ground=1;
 q->mode=rng_range(&s.rng,3);
 if(kind==HQ_SCAV&&q->mode==2&&!legacy_item_owned(LI_MOLE_MITTS))q->mode=1;
 if(kind==HQ_SCAV&&q->mode){
  Spot found,origin={23,8},start={16,20};
  if(q->mode==1)room_change(23,8,MT_CAVE_FLOOR_LIFT);
  else {room_change(23,8,MT_LH_DIG);legacy_surface_set(23,8,LS_DIG);}
  if(world_hidden_find(q->mode==1?WH_CUT:WH_DIG,origin,start,8,&found)){
   q->cargo_x=sx(found.x);q->cargo_y=sy(found.y);
  }else q->mode=0;
 }
 p=cat(msg,"Contract accepted. Failure costs ");p=cat(p,q->stake==0?"nothing":q->stake==1?"up to 50 gilt":q->stake==2?"up to 100 gilt and half health":"up to 200 gilt, half health and one good charm");
 p=cat(p,". ");cat(p,kind==HQ_POT?"Find the marked pot.":kind==HQ_HUNT?"Defeat the quota within 30 seconds.":kind==HQ_SCAV?"Find the glint: catch, cut, or dig it.":kind==HQ_STEALTH?"Reach the far seal without entering the watchers' gaze.":kind==HQ_CARRY?"Lift this pot with A, carry it to the receiver, and clear both ambushes. R throws it; recover it safely.":kind==HQ_COURIER?"Deliver the parcel to the fuser at the Forest entrance. Return for your prize.":"Push the blocks to match the reference. Select resets safely.");say(msg);
 if(kind==HQ_HUNT)refill(4);
 if(kind==HQ_COURIER)q->cargo_held=1;
}
/* The themed selection desk is a real transaction UI. It shares the approved
   menu frame/palette; no new global screen state or enlarged HUD is required. */
enum { HM_NONE,HM_DRAFT,HM_INN,HM_SHOP,HM_FUSE,HM_TROPHY,HM_HINT,HM_CHALLENGE,HM_CONTRACT,HM_DIFFICULTY };
static struct{u16 display,bg3,blend,alpha,brightness; s16 x,y;u8 active,cursor,top,repeat,old_anim;} m __attribute__((section(".ewram_bss.handoff_menu")));
static int menu_count(void){return m.active==HM_DRAFT?3:m.active==HM_INN?3:m.active==HM_SHOP?6:m.active==HM_FUSE?5:m.active==HM_TROPHY?3:m.active==HM_CHALLENGE?HS_COUNT+2:m.active==HM_CONTRACT?3:m.active==HM_DIFFICULTY?13:1;}
static const char* menu_title(void){return m.active==HM_DRAFT?"Three Gifts / choose one":m.active==HM_INN?"The Three Beds":m.active==HM_SHOP?"Annex Exchange":m.active==HM_FUSE?"Kinstone Fusions":m.active==HM_TROPHY?"Trophy & Entitlements":m.active==HM_HINT?"A Quiet Hint":m.active==HM_CHALLENGE?"Optional Challenges":m.active==HM_DIFFICULTY?"Difficulty 0 to 12":"Four-step Contract";}
static void menu_close(void){
 gAnimTiles=m.old_anim;bg0_clear();gBg3Dirty=0;REG_BG3CNT=m.bg3;gBgScroll[3][0]=m.x;gBgScroll[3][1]=m.y;
 room_render();video_show(m.display);REG_BLDCNT=m.blend;REG_BLDALPHA=m.alpha;REG_BLDY=m.brightness;m.active=0;gKeysDown=0;
}
static void contract_next(void){
 int step=gHandoffState.contract_step;u32 roll=rng_next(&s.rng);gHandoffState.contract_state=1;
 if(step>=4){gHandoffState.contract_state=2;gHandoffState.score+=200;refresh_rank();give(LI_HEART_CONTAINER);give(LI_FOURSWORD);say("Four seals fulfilled. Your optional contract is complete. The Forest Heart and the summit remain yours to seek.");return;}
 if(step==3){gHandoffState.contract_kind=HC_BOSS;gHandoffState.contract_target=HS_BOSS;}
 else if(step==2){gHandoffState.contract_kind=HC_ITEM;gHandoffState.contract_item=reward_pick(LCAT_KEY,1,roll);gHandoffState.contract_target=HS_POCKET;}
 else if(step==1){gHandoffState.contract_kind=(roll&1)?HC_QUEST:HC_WAVE;gHandoffState.contract_target=(roll&1)?HS_QUEST_HUNT:HS_WAVES;}
 else{gHandoffState.contract_kind=HC_EVENT;gHandoffState.contract_target=HS_POTS+(roll%2)*5;}
 /* Each seal owns a fresh site, independent of optional exploration. */
 {
  int site=HANDOFF_CONTRACT_BASE+step;
  gHandoffState.completed[site>>3]&=~(1u<<(site&7));
  gHandoffState.won[site>>3]&=~(1u<<(site&7));
  gHandoffState.wave[site]=gHandoffState.remaining[site]=0;
 }
}
static void menu_row(int index,char* out){
 char* p=out;out[0]=0;
 switch(m.active){
 case HM_DRAFT:p=cat(p,item_name(gHandoffState.draft[index]));break;
 case HM_INN:p=cat(p,index==0?"Plain bed / 50 gilt":index==1?"Soft bed + common / 200 gilt":"Canopy bed + uncommon / 500 gilt");break;
 case HM_SHOP:{int cost=gHandoffState.prices[index]+(index==0?25*gHandoffState.heart_purchases:0);p=cat(p,gHandoffState.shop_bought&(1<<index)?"SOLD":item_name(gHandoffState.stock[index]));p=cat(p," / ");p=num(p,handoff_shop_price(MIN(999,cost)));break;}
 case HM_FUSE:{static const char*const names[]={"Green wandering fuser","Blue wandering fuser","Red wandering fuser","Flow golden gate","Three golden statues"};p=cat(p,names[index]);break;}
 case HM_TROPHY:p=cat(p,index==0?"View rank and record":index==1?"Toggle optional entitlement challenge":"Choose run difficulty");break;
 case HM_CHALLENGE:p=cat(p,index+1<HS_COUNT?sSiteNames[index+1]:index==HS_COUNT-1?"Moving Crossing Workshop":index==HS_COUNT?"Secrets & Weather Workshop":"Tool Targets Workshop");break;
 case HM_DIFFICULTY:p=cat(p,"Difficulty ");p=num(p,index);p=cat(p,index==gHandoffState.difficulty?" / current":"");break;
 case HM_CONTRACT:p=cat(p,index==0?"Begin / inspect four-step contract":index==1?"Travel to the current contract":"Retire optional contract");break;
 default:p=cat(p,"Follow the small gilt lanterns.");break;
 }
 (void)p;
}
static const char* menu_note(void){
 if(m.active==HM_DRAFT){const LegacyItemDef*d=legacy_item_def(gHandoffState.draft[m.cursor]);return d?d->description:"A golden half opens an optional fusion gate.";}
 if(m.active==HM_INN)return m.cursor==0?"Restore 25% max health; at least one heart.":m.cursor==1?"Restore 50%; at least two hearts. Common chest.":"Restore all health. Uncommon chest; never rare.";
 if(m.active==HM_SHOP){const LegacyItemDef*d=legacy_item_def(gHandoffState.stock[m.cursor]);return d?d->description:"A practical supply.";}
 if(m.active==HM_FUSE)return "Match a colored shaped half; gold opens its own gate. No main trial is replaced.";
 if(m.active==HM_CHALLENGE)return "Optional annex rooms preserve every existing Forest trial. Exit south whenever safe.";
 if(m.active==HM_HINT)return "Paths tell one story. Lanterns can tell another. A keyhole, cracked rock, web or gap each asks for its tool.";
 if(m.active==HM_CONTRACT)return "Four adaptive steps: event, waves/quest, key item, boss. Current regions and boss wins are unchanged.";
 if(m.active==HM_DIFFICULTY)return "Higher difficulty changes optional wave tiers and announced quest stakes. Zero is a gentle first run.";
 return "Ranks unlock optional challenge access, never remove tools or access from the existing game.";
}
static void menu_paint(void){
 Canvas c;int row;char label[80],status[48];char*p;
 bg0_clear();bg0_pool_reset_full();ui_backdrop_clear();ui_frame(gBg3,UI_BG3,0,0,30,20,FR_PANEL);
 bg0_canvas(&c,2,1,26,2);vwf_text(&c,2,3,menu_title(),UI_INK_GOLD);vwf_flush(&c,FALSE);
 ui_frame(gBg3,UI_BG3,2,4,26,10,FR_PANEL);bg0_canvas(&c,3,5,22,8);
 for(row=0;row<4&&m.top+row<menu_count();row++){
  int index=m.top+row;menu_row(index,label);
  if(index==m.cursor)ui_plate_px(&c,0,row*16,22,PL_TABON);
  vwf_text(&c,3,row*16+3,label,index==m.cursor?UI_INK_HIGH:UI_INK_CREAM);
 }
 vwf_flush(&c,FALSE);bg0_canvas(&c,2,15,26,3);vwf_block(&c,0,0,208,10,menu_note(),UI_INK_CREAM,2);
 p=cat(status,"A Choose  B Back    Gilt ");num(p,gPl.gilt);vwf_text(&c,0,19,status,UI_INK_GOLD);vwf_flush(&c,FALSE);gBg3Dirty=1;
}
static void menu_open(int kind){
 if(m.active)return;
 m.display=REG_DISPCNT;m.bg3=REG_BG3CNT;m.x=gBgScroll[3][0];m.y=gBgScroll[3][1];m.blend=REG_BLDCNT;m.alpha=REG_BLDALPHA;m.brightness=REG_BLDY;m.old_anim=gAnimTiles;
 m.active=kind;m.cursor=m.top=0;m.repeat=16;gAnimTiles=0;
 REG_BG3CNT=BGCNT_PRIO(3)|BGCNT_CHARBASE(3)|BGCNT_SCREENBASE(22)|BGCNT_SIZE_32x32;gBgScroll[3][0]=gBgScroll[3][1]=0;REG_BLDCNT=REG_BLDY=0;
 ui_backdrop_open();video_show(DCNT_MODE0|DCNT_BG0|DCNT_BG3|DCNT_OBJ|DCNT_OBJ_1D);menu_paint();gKeysDown=0;sfx_play(SFX_MENU);
}
bool8 handoff_menu_active(void){return m.active!=0;}
static void fuse(int index){
 if(index<3){int shape=gHandoffState.fuser_shape[index];
  if(gHandoffState.fusion_flags&(1<<index)){say("This fuser's shortcut is already open.");return;}
  if(!gHandoffState.kinstone_shapes[index][shape]){char msg[130];char*p=cat(msg,"This fuser needs a ");p=cat(p,index==0?"green":index==1?"blue":"red");p=cat(p,shape==0?" upper-right tooth":" lower-right tooth");if(shape==1)p=cat(msg,index==0?"This fuser needs a green left tooth":index==1?"This fuser needs a blue left tooth":"This fuser needs a red left tooth");cat(p," half. No match; the fuser will wait.");say(msg);return;}
  gHandoffState.kinstone_shapes[index][shape]--;if(gLegacyInventory.kinstones[index])gLegacyInventory.kinstones[index]--;
  gHandoffState.fusion_flags|=1<<index;give(index==0?LI_KINSTONE_BAG:index==1?LI_RUPEE100:LI_BOTTLE1);
  say("Two halves meet. A cache, cave and crossing open in the annex. The old roads keep their gates.");
 }else if(index==3){if(!(gHandoffState.gold_owned&1)){say("The Flow seal needs its gold half.");return;}gHandoffState.gold_fused|=1;say("The golden Flow seal opens.");}
 else{if((gHandoffState.gold_owned&14)!=14){say("Three statue halves are needed: left, middle and right.");return;}gHandoffState.gold_fused|=14;say("Three golden statues awaken. Their final cache opens.");}
 sfx_play(SFX_SECRET);
}
void handoff_menu_update(void){
 u16 move=gKeysDown&(KEY_UP|KEY_DOWN);bool8 dirty=FALSE;
 if(!m.active)return;
 oam_clear();
 if(gKeysDown&(KEY_B|KEY_START)){menu_close();return;}
 if(!move&&(gKeysHeld&(KEY_UP|KEY_DOWN))){if(m.repeat)m.repeat--;else{move=gKeysHeld;m.repeat=5;}}else m.repeat=16;
 if(move){int old=m.cursor;m.cursor=CLAMP((int)m.cursor+((move&KEY_UP)?-1:1),0,menu_count()-1);if(m.cursor<m.top)m.top=m.cursor;if(m.cursor>=m.top+4)m.top=m.cursor-3;dirty=old!=m.cursor;}
 if(gKeysDown&KEY_A){int mode=m.active,choice=m.cursor;menu_close();
  switch(mode){
  case HM_DRAFT:
   give(gHandoffState.draft[choice]);gHandoffState.draft_round++;
   if(gHandoffState.draft_round>=3){gHandoffState.draft_state=HDRAFT_DONE;say("Three gifts chosen. These optional gifts join your normal starting equipment.");}
   else{roll_draft();menu_open(HM_DRAFT);}return;
  case HM_INN:{int price=handoff_shop_price(choice==0?50:choice==1?200:500);if(gPl.gilt<price){say("Not enough gilt for that bed.");return;}
   if(gHandoffState.inn_reward){say("Collect the chest beside your bed before buying another stay.");return;}
   gPl.gilt-=price;s.sleep_timer=150;s.sleep_choice=choice;gPlayer->state=PS_FROZEN;gPl.input_lock=1;fade_start(16,1);sfx_play(SFX_MENU);return;}
  case HM_SHOP:{int raw=MIN(999,gHandoffState.prices[choice]+(choice==0?25*gHandoffState.heart_purchases:0));int price=handoff_shop_price(raw);
   if(gHandoffState.shop_bought&(1<<choice)){say("That item has sold.");return;}if(gPl.gilt<price){say("Not enough gilt.");return;}
   if(choice>2&&!eligible(gHandoffState.stock[choice])){say("You already own that gift, or need its prerequisite. No gilt taken.");return;}
   gPl.gilt-=price;give(gHandoffState.stock[choice]);if(choice==0)gHandoffState.heart_purchases++;else if(choice>2)gHandoffState.shop_bought|=1<<choice;return;}
  case HM_FUSE:fuse(choice);return;
  case HM_TROPHY:
   if(choice==1){gHandoffState.entitlement_mode^=1;gHandoffState.difficulty=MIN(gHandoffState.difficulty,handoff_difficulty_cap());save_write();say(gHandoffState.entitlement_mode?"Optional entitlement challenges enabled. Existing world features remain available.":"Optional entitlement challenges disabled.");}
   else if(choice==2)menu_open(HM_DIFFICULTY);
   else{char msg[130];char*p=cat(msg,"Rank ");p=num(p,gHandoffState.rank);p=cat(p," / score ");p=num(p,gHandoffState.score);p=cat(p," / wins ");p=num(p,gHandoffState.wins);p=cat(p," / deaths ");p=num(p,gHandoffState.deaths);cat(p,". Ranks: 50, 250, 800, 2000 points.");say(msg);}return;
  case HM_DIFFICULTY:
   if(choice>handoff_difficulty_cap()){say("That optional difficulty is beyond this save's entitlement cap. Wins and score raise the cap; ordinary mode offers all twelve steps.");return;}
   gHandoffState.difficulty=choice;save_write();say("Optional challenge difficulty set. Accepted quests keep their announced stakes.");return;
  case HM_CHALLENGE:
   if(!handoff_event_unlocked(choice+1)){say("This optional event is not yet earned in entitlement mode. First win opens the fairy; 500 score opens pots and puzzles; 1500 score opens portal and boss contracts.");return;}
   if((choice+1==HS_TORCHES)&&!legacy_item_owned(LI_LANTERN_OFF)&&!legacy_item_owned(LI_FIRE_ROD)){say("The censers need a lantern or flame rod. Find one, then return.");return;}
   if((choice+1==HS_CLEANUP)&&!legacy_item_owned(LI_LANTERN_OFF)&&!legacy_item_owned(LI_FIRE_ROD)&&!legacy_item_owned(LI_GUST_JAR)){say("Clean-up needs a lantern or Gust Jar. Find either, then return.");return;}
   s.request=choice+1;return;
  case HM_CONTRACT:
   if(choice==2){gHandoffState.contract_state=0;say("Optional contract retired. The run continues.");return;}
   if(!gHandoffState.contract_state){gHandoffState.contract_step=0;contract_next();}
   if(choice==1&&gHandoffState.contract_state==1){if(!handoff_event_unlocked(gHandoffState.contract_target)){say("This contract seal awaits the optional entitlement unlock. Earn score or wins, or switch to ordinary mode.");return;}s.request=HANDOFF_CONTRACT_BASE+gHandoffState.contract_step;}
   else{char msg[150];char*p=cat(msg,"Seal ");p=num(p,gHandoffState.contract_step+1);p=cat(p," of 4: ");p=cat(p,sSiteNames[gHandoffState.contract_target]);
    if(gHandoffState.contract_kind==HC_ITEM){p=cat(p,". Seek ");p=cat(p,item_name(gHandoffState.contract_item));}cat(p,". Travel from this desk when ready.");say(msg);}return;
  default:say("Paths tell one story. Lanterns tell another. Follow gilt lamps to a feature, or search the unmarked corners.");return;
  }
 }
 if(dirty){menu_paint();sfx_play(SFX_MENU);}
}
/* Small native props have a single vocabulary: dark contour, gold highlight,
   and teal/wine axis marks. The original cave floor/wall art is reused. */
enum { HA_DESK,HA_FUSER,HA_GOLD,HA_PORTAL,HA_TOKEN,HA_BLOCK_FREE,HA_BLOCK_H,
 HA_BLOCK_V,HA_GOAL,HA_RESET,HA_WEB,HA_DUST,HA_TORCH_OFF,HA_TORCH_LIT,
 HA_WATCH_N,HA_WATCH_E,HA_WATCH_S,HA_WATCH_W,HA_PARCEL,HA_POT,HA_RECIPIENT,
 HA_GREEN_HALF,HA_GREEN_1,HA_GREEN_2,HA_BLUE_HALF,HA_BLUE_1,HA_BLUE_2,HA_RED_HALF,HA_RED_1,HA_RED_2,HA_LEAF,HA_COUNT };
typedef struct{ s16 x,y;u8 color,shape,age,active;} LooseHalf;
static LooseHalf sHalves[8] __attribute__((section(".ewram_bss.handoff_halves")));
static u16 sFieldTile __attribute__((section(".ewram_bss.handoff_field_tile")));
static u16 sHalfTile[3][3] __attribute__((section(".ewram_bss.handoff_half_tiles")));
static bool8 inside_hand(void){return gGame.area==AREA_HANDOFF;}
static void paint_border(void){
 int x,y;room_clear(32,24,MT_CAVE_FLOOR0);
 for(y=0;y<24;y++)for(x=0;x<32;x++){
  if(x<2||x>29||y<3||y>21)room_set(x,y,y==2?MT_CAVE_FACE:y==22?MT_CAVE_CROWN:MT_CAVE_WALL);
  else if((hash32(s.seed,x+y*32)&31)==0)room_set(x,y,MT_CAVE_FLOOR1);
 }
 room_set(15,22,MT_CAVE_EXIT);room_set(16,22,MT_CAVE_EXIT);
}
void handoff_build(int site,int kind,u32 seed){
 int i;u8 food_scene=s.scene_active;(void)food_scene;
 if(gHandoffState.quest.state==2&&gHandoffState.quest.kind!=HQ_COURIER&&gHandoffState.quest.origin_cell!=site)quest_fail();
 handoff_objects_reset();
 if(site>=HANDOFF_CONTRACT_BASE&&site<HANDOFF_CONTRACT_BASE+4)kind=gHandoffState.contract_state==1?gHandoffState.contract_target:HS_ITEM;
 if(site>=HANDOFF_OBJECT_SITE1&&site<=HANDOFF_OBJECT_SITE3){kind=HS_OBJECT_COURSE;seed=(seed&~0x300u)|((site-HANDOFF_OBJECT_SITE1+1)<<8);}
 else if(kind==HS_OBJECT_COURSE)seed&=~0x300u;
 s.site=CLAMP(site,0,255);s.kind=CLAMP(kind,0,HS_COUNT-1);s.seed=seed;s.clock=0;s.phase=0;s.count=0;s.quota=0;s.timer=0;s.plate=255;s.last_plate=255;s.memory_input=0;s.memory_show=0;s.exit=0;s.request=255;s.clean=0;s.switch_mask=0;s.cast_count=0;s.prize=HBIT(gHandoffState.won,s.site);s.recipient_x=s.recipient_y=-1;
 rng_seed(&s.rng,hash32(seed,site+kind*257));clear_bytes(sHalves,sizeof(sHalves));clear_bytes(sHalfTile,sizeof(sHalfTile));
 tiles_load(TS_MYST);paint_border();
 if(board_kind()){
  int base=s.kind==HS_BLOCK_MAZE?768:s.kind==HS_QUEST_BLOCKS?(rng_range(&s.rng,2)?768:0):0;
  gHandoffPuzzleIndex=base+rng_range(&s.rng,base?760:768);
  if(!handoff_puzzle_verify(handoff_puzzle(gHandoffPuzzleIndex)))gHandoffPuzzleIndex=base;
  board_paint();
  for(i=0;i<3;i++)gHandoffBoardBlocks[i]=handoff_puzzle(gHandoffPuzzleIndex)->blocks[i];
  gHandoffBoardPlayer=handoff_puzzle(gHandoffPuzzleIndex)->entry;gHandoffPushes=0;gHandoffBoardSolved=finished();
 }
 if(s.kind==HS_POTS||s.kind==HS_QUEST_POT){
  s.quota=6;for(i=0;i<6;i++){room_set(7+(i%3)*8,7+(i/3)*8,MT_CAVE_FLOOR_LIFT);room_set_overlay(7+(i%3)*8,7+(i/3)*8,MT_MYST_POT);}
  s.count=rng_range(&s.rng,6);
 }
 if(s.kind==HS_SWITCHES||s.kind==HS_MEMORY_SHOW||s.kind==HS_MEMORY_INPUT){
  for(i=0;i<4;i++)room_set_overlay(9+i*4,10,MT_MYST_SWITCH);
  s.theme=rng_range(&s.rng,3);
 }
 if(s.kind==HS_TORCHES){s.quota=3;s.clean=7;}
 if(s.kind==HS_CLEANUP){bool8 fire=legacy_item_owned(LI_LANTERN_OFF)||legacy_item_owned(LI_FIRE_ROD);s.theme=fire?0:1;s.quota=fire&&legacy_item_owned(LI_GUST_JAR)?12:6;s.clean=(1u<<s.quota)-1;}
 if(s.kind==HS_QUEST_STEALTH){
  /* Authored cover creates safe waiting pockets, never a sealed route. */
  for(i=0;i<3;i++){int x=9+i*6;room_set(x,9,MT_CAVE_WALL);room_set(x,10,MT_CAVE_WALL);room_set(x,13,MT_CAVE_WALL);room_set(x,14,MT_CAVE_WALL);}
 }
 if(s.kind==HS_GOLD_GATE&&((gHandoffState.gold_fused&15)!=15))for(i=11;i<=20;i++)room_set(i,8,MT_CAVE_WALL);
 if(s.kind==HS_FAIRY)room_set_overlay(NODE_X,NODE_Y,MT_MYST_SPRING);
 if(s.kind==HS_HUB&&gHandoffState.inn_reward)room_set_overlay(12,10,MT_MYST_CHEST);
 if(s.prize)room_set_overlay(NODE_X,NODE_Y,MT_MYST_CHEST);
 if(s.kind==HS_TRAVERSAL)handoff_mobility_build(seed);
 if(s.kind==HS_OBJECT_COURSE)handoff_objects_build(seed);
 HSET(gHandoffState.visited,s.site);room_build_solid();room_render();
}
void handoff_start_pos(int* x,int* y){
 *x=sx(16);*y=sy(20);
 if(board_kind()){const HandoffPuzzle*p=handoff_puzzle(gHandoffPuzzleIndex);*x=sx(BOARD_X+p->entry%5);*y=sy(BOARD_Y+p->entry/5);}
}
void handoff_enter(void){
 s.scene_active=1;sFieldTile=0;s.cadence=0;
 if(s.kind==HS_OBJECT_COURSE){s.tile=0;handoff_objects_enter();return;}
 if(s.kind==HS_TRAVERSAL){s.tile=0;return;}
 s.tile=sprite_load_sheet(SHEET_HANDOFF);
 if(FOOD(HF_FLEET))s.invulnerable=MAX(s.invulnerable,120);
 if(finished()){s.phase=9;return;}
 switch(s.kind){
 case HS_ITEM:case HS_NPC:s.phase=0;break;
 case HS_FAIRY:legacy_item_spawn(LI_FAIRY,sx(14),sy(11));legacy_item_spawn(LI_FAIRY,sx(18),sy(11));break;
 case HS_WAVES:case HS_ARENA:case HS_SURVIVE:wave_begin();s.timer=s.kind==HS_SURVIVE?1200:0;break;
 case HS_MINIBOSS:s.phase=spawn_one(LE_DARK_NUT_0)?1:0;break;
 case HS_BOSS:s.phase=spawn_one((s.seed&1)?LE_GIANT_CHUCHU_GREEN:LE_BIG_OCTOROK)?1:0;break;
 case HS_MEMORY_INPUT:
  if(!gHandoffState.memory_known)say("Four plates answer a memory from the paired Learn chamber. Visit it, then return. South remains open.");
  break;
 case HS_QUEST_POT:case HS_QUEST_HUNT:case HS_QUEST_SCAV:case HS_QUEST_STEALTH:case HS_QUEST_CARRY:case HS_QUEST_COURIER:case HS_QUEST_BLOCKS:
  if(gHandoffState.quest.state==2&&gHandoffState.quest.kind==HQ_COURIER&&s.kind==HS_QUEST_COURIER)break;
  quest_start(s.kind-HS_QUEST_POT+HQ_POT);break;
 case HS_PORTAL:say("The violet arch leads to a sealed pocket. Solve its trial; an escape tool will be supplied before entry if needed.");break;
 case HS_POCKET:
  if(!legacy_item_owned(LI_OCARINA)&&!legacy_item_owned(LI_ROCS_CAPE))give(LI_ROCS_CAPE);
  wave_begin();s.phase=1;break;
 default:break;
 }
}
static bool8 flood_from_hero(int tx,int ty){
 /* Recipient/fuser spawn within a short clear footpath from entry. */
 int px=PX(gPlayer->x),py=PX(gPlayer->y),x=sx(tx),y=sy(ty),i,n=MAX(ABS(x-px),ABS(y-py))/8+1;
 if(room_box_solid(x-6,y-10,x+6,y))return FALSE;
 for(i=0;i<=n;i++)if(room_box_solid(px+(x-px)*i/n-5,py+(y-py)*i/n-9,px+(x-px)*i/n+5,py+(y-py)*i/n))return FALSE;
 return TRUE;
}
void handoff_room_enter(int area,int cell){
 int i,r,tx,ty;
 handoff_objects_reset();
 if(gHandoffState.quest.state==2&&gHandoffState.quest.kind!=HQ_COURIER)quest_fail();
 s.scene_active=0;sFieldTile=0;s.recipient_x=s.recipient_y=-1;clear_bytes(sHalves,sizeof(sHalves));clear_bytes(sHalfTile,sizeof(sHalfTile));
 if(FOOD(HF_FLEET))s.invulnerable=MAX(s.invulnerable,120);
 if(!gPlayer)return;
 if(area!=AREA_FOREST&&area!=AREA_CREAM)return;
 for(i=0;i<3;i++)if(gHandoffState.fuser_cell[i]==cell&&!(gHandoffState.fusion_flags&(1<<i)))break;
 if(i==3&&!(gHandoffState.quest.state==2&&gHandoffState.quest.kind==HQ_COURIER&&gHandoffState.quest.target_area==area&&gHandoffState.quest.target_cell==cell))return;
 tx=PX(gPlayer->x)/16;ty=PX(gPlayer->y)/16;
 for(r=2;r<7;r++)for(int dy=-r;dy<=r;dy++)for(int dx=-r;dx<=r;dx++){
  int x=tx+dx,y=ty+dy;if(ABS(dx)!=r&&ABS(dy)!=r)continue;
  if(x<2||y<2||x>=gRoom.w-2||y>=gRoom.h-2||room_type(x,y)!=TT_FLOOR||room_get_overlay(x,y)!=MT_NONE||!flood_from_hero(x,y))continue;
  if(area==AREA_CREAM&&cream_room_feature_reserved(x,y))continue;
  s.recipient_x=sx(x);s.recipient_y=sy(y);s.visited_courier=i;
  sFieldTile=sprite_load_frame(SHEET_HANDOFF,HA_FUSER);return;
 }
}
int handoff_map_mark(int area,int cell){
 int i;if(!legacy_item_owned(LI_COMPASS)||(area!=AREA_FOREST&&area!=AREA_CREAM))return 0;
 for(i=0;i<3;i++)if(gHandoffState.fuser_cell[i]==cell&&!(gHandoffState.fusion_flags&(1<<i)))return 1;
 if(gHandoffState.quest.kind==HQ_COURIER&&gHandoffState.quest.state==2&&gHandoffState.quest.target_area==area&&gHandoffState.quest.target_cell==cell)return 2;
 return 0;
}
void handoff_notify(int kind,int area,int cell,int item){
 int match=0;int c=gHandoffState.contract_kind;
 if(gHandoffState.contract_state!=1)return;
 if(area==AREA_HANDOFF)cell=s.site;
 if(c==HC_ITEM)match=kind==HN_ITEM&&item==gHandoffState.contract_item;
 else if(area==AREA_HANDOFF&&cell==HANDOFF_CONTRACT_BASE+gHandoffState.contract_step){
  if(c==HC_EVENT)match=kind==HN_EVENT;
  else if(c==HC_WAVE)match=kind==HN_WAVE;
  else if(c==HC_BOSS)match=kind==HN_BOSS;
  else if(c==HC_QUEST)match=kind==HN_QUEST;
 }
 if(match){int element=LI_EARTH_ELEMENT+gHandoffState.contract_step;gHandoffState.contract_step++;give(element);contract_next();sfx_play(SFX_SECRET);} (void)area;
}
void handoff_kinstone_drop(int color,int shape,int px,int py){
 int i;color=CLAMP(color,0,2);shape=CLAMP(shape,0,2);
 for(i=0;i<8;i++)if(!sHalves[i].active){
  if(!inside_hand()&&!sHalfTile[color][shape]){
   const SpriteSheet*sh=&sheets[SHEET_HANDOFF];
   int frame=HA_GREEN_HALF+color*3+shape;
   u16 tile=sprite_alloc(4);
   if(!tile)return; /* optional drop never exists without a visible frame */
   sHalfTile[color][shape]=tile;
   vram_queue(sh->tiles+frame*sh->frame_tiles*16,OBJ_TILE(tile),128);
  }
  sHalves[i].x=px;sHalves[i].y=py;sHalves[i].color=color;sHalves[i].shape=shape;
  sHalves[i].age=0;sHalves[i].active=1;break;
 }
}
void handoff_on_enemy_killed(int type,int px,int py){
 HandoffQuest*q=&gHandoffState.quest;
 if(inside_hand()){
  if(gHandoffState.remaining[s.site])gHandoffState.remaining[s.site]--;
  if(q->state==2&&q->kind==HQ_HUNT&&q->origin_cell==s.site){q->count++;if(q->count>=q->quota)quest_win();}
  if(s.kind==HS_BOSS&&type>=LE_GIANT_CHUCHU_GREEN)finish();
 }
 if((hash32(gFrame,type)&31)<(FOOD(HF_DROP_KINSTONES)?6u:1u))handoff_kinstone_drop(hash32(gFrame,type)%3,hash32(type,gFrame)%3,px,py);
}
void handoff_tile_cleared(int tx,int ty){
 int i;if(!inside_hand())return;
 HandoffQuest*q=&gHandoffState.quest;
 if(q->state==2&&q->kind==HQ_SCAV&&q->mode==1&&q->origin_cell==s.site&&tx==q->cargo_x/16&&ty==q->cargo_y/16){quest_win();return;}
 if(s.kind==HS_POTS||s.kind==HS_QUEST_POT)for(i=0;i<6;i++)if(tx==7+(i%3)*8&&ty==7+(i/3)*8){
  s.clean|=1u<<i;
  if(i==s.count){if(s.kind==HS_QUEST_POT)quest_win();else finish();}break;
 }
}
void handoff_tool_box(int kind,int x0,int y0,int x1,int y1){
 HandoffQuest*q=&gHandoffState.quest;int i;
 if(!inside_hand())return;
 if(s.kind==HS_OBJECT_COURSE){handoff_objects_tool_box(kind,x0,y0,x1,y1);return;}
 if(s.kind==HS_CLEANUP||s.kind==HS_TORCHES)for(i=0;i<s.quota;i++){
  int x=sx(s.kind==HS_TORCHES?8+i*8:7+(i%4)*6),y=sy(s.kind==HS_TORCHES?10:7+(i/4)*5);
  bool8 correct=s.kind==HS_TORCHES?(kind==LE_HIT_LANTERN||kind==LE_HIT_FIRE):(i<6&&s.theme!=1)?(kind==LE_HIT_LANTERN||kind==LE_HIT_FIRE):(kind==LE_HIT_GUST_SMALL||kind==LE_HIT_GUST_BIG);
  if(correct&&x>=x0-8&&x<=x1+8&&y>=y0&&y<=y1+14)s.clean&=~(1u<<i);
 }
 if(q->state==2&&q->kind==HQ_SCAV&&q->origin_cell==s.site){
  int x=q->cargo_x,y=q->cargo_y;bool8 correct=q->mode==2?kind==HTOOL_DIG:q->mode==1?kind==LE_HIT_SWORD:FALSE;
  if(correct&&x>=x0-8&&x<=x1+8&&y>=y0&&y<=y1+14){room_change(x/16,y/16,MT_CAVE_FLOOR0);room_change_overlay(x/16,y/16,MT_NONE);quest_win();}
 }
}
void handoff_cargo_thrown(Actor*a){
 HandoffQuest*q=&gHandoffState.quest;
 if(!a||!inside_hand()||q->state!=2||q->kind!=HQ_CARRY||!q->cargo_held||a->v[0]!=CARRY_POT)return;
 a->v[5]=CARGO_MAGIC;q->cargo_held=0;q->cargo_flying=1;
}
bool8 handoff_cargo_land(Actor*a){
 HandoffQuest*q=&gHandoffState.quest;int x,y;
 if(!a||a->v[5]!=CARGO_MAGIC)return FALSE;
 x=PX(a->x);y=PX(a->y);q->cargo_flying=0;q->cargo_ground=1;
 if(room_type_px(x,y)!=TT_FLOOR){x=sx(8);y=sy(17);}
 q->cargo_x=x;q->cargo_y=y;actor_free(a);return TRUE;
}
static void draw_prop(int frame,int x,int y,int priority){
 if(x-gCamX<-16||y-gCamY<-16||x-gCamX>256||y-gCamY>176)return;
 draw_sprite(x-8-gCamX,y-16-gCamY,SHEET_HANDOFF,s.tile,frame,0,priority,PAL_OBJ_FX);
}
static int plate_at(void){
 int i;if(!gPlayer||PX(gPlayer->z)>1)return 255;
 for(i=0;i<4;i++)if(near(sx(9+i*4),sy(10),9))return i;
 return 255;
}
static void memory_tick(void){
 int plate=plate_at();
 if(s.kind==HS_MEMORY_SHOW){
  int t=s.clock%((gHandoffState.memory_length+2)*60);
  s.memory_show=t/60<gHandoffState.memory_length&&t%60<40?gHandoffState.memory_code[t/60]:255;
  if(t==(int)gHandoffState.memory_length*60){gHandoffState.memory_known=1;sfx_play(SFX_SECRET);}
 }else if(s.kind==HS_MEMORY_INPUT&&!finished()&&gHandoffState.memory_known){
  if(plate!=255&&plate!=s.last_plate){
   if(plate==gHandoffState.memory_code[s.memory_input]){s.memory_input++;sfx_play(SFX_KEY);if(s.memory_input>=gHandoffState.memory_length)finish();}
   else{s.memory_input=0;sfx_play(SFX_BUMP);}
  }
 }
 s.last_plate=plate;
}
static void switch_tick(void){
 int p=plate_at();
 if(p!=255&&p!=s.last_plate&&!finished()){
  if(s.theme==0)s.switch_mask|=1<<p;
  else if(s.theme==1)s.switch_mask^=(1<<p)|(1<<((p+1)&3));
  else{if(p==s.count){s.count++;s.timer=180;if(s.count==4)s.switch_mask=15;}else{s.count=0;sfx_play(SFX_BUMP);}}
  for(int i=0;i<4;i++)room_change_overlay(9+i*4,10,s.switch_mask&(1<<i)?MT_MYST_SWITCH_DOWN:MT_MYST_SWITCH);
  sfx_play(SFX_MENU);if(s.switch_mask==15)finish();
 }
 if(s.theme==2&&s.timer){s.timer--;if(!s.timer)s.count=0;}
 s.last_plate=p;
}
static bool8 watcher_sees(int wx,int wy,int face){
 int px=PX(gPlayer->x),py=PX(gPlayer->y),dx=px-wx,dy=py-wy,forward=dx*sDX[face]+dy*sDY[face],side=dx*sDY[face]-dy*sDX[face],n,i;
 if(forward<4||forward>76||ABS(side)>forward/2+6)return FALSE;
 n=MAX(ABS(dx),ABS(dy))/8+1;
 for(i=1;i<n;i++)if(room_solid_px(wx+dx*i/n,wy+dy*i/n))return FALSE;
 return TRUE;
}
bool8 handoff_try_interact(void){
 HandoffQuest*q=&gHandoffState.quest;int i;
 if(s.recipient_x>=0&&!inside_hand()&&near(s.recipient_x,s.recipient_y,24)){
  if(q->state==2&&q->kind==HQ_COURIER&&q->target_area==gGame.area&&q->target_cell==gGame.cell){
   q->state=3;gHandoffState.score+=30;refresh_rank();give(random_reward(1));handoff_notify(HN_QUEST,gGame.area,gGame.cell,0);
   HSET(gHandoffState.completed,HS_QUEST_COURIER);HSET(gHandoffState.won,HS_QUEST_COURIER);say("Parcel delivered. Your reward is safe. Return to the annex for the sealed cache.");
  }else fuse(MIN(2,s.visited_courier));return TRUE;
 }
 if(!inside_hand())return FALSE;
 if(s.kind==HS_TRAVERSAL)return handoff_mobility_interact();
 if(s.kind==HS_OBJECT_COURSE)return FALSE;
 if(s.kind==HS_HUB){
  if(gHandoffState.inn_reward&&near(sx(12),sy(10),22)){int item=gHandoffState.inn_reward;gHandoffState.inn_reward=0;room_change_overlay(12,10,MT_MYST_CHEST_OPEN);give(item);sfx_play(SFX_CHEST);return TRUE;}
  static const u8 service[8]={HM_DRAFT,HM_INN,HM_SHOP,HM_FUSE,HM_TROPHY,HM_HINT,HM_CHALLENGE,HM_CONTRACT};
  for(i=0;i<8;i++)if(near(sx(sDesk[i][0]),sy(sDesk[i][1]),22)){
   if(i==0){if(gHandoffState.draft_state==HDRAFT_DONE){say("You already chose three gifts this run.");return TRUE;}
    if(!gHandoffState.draft_state){gHandoffState.draft_state=HDRAFT_RUNNING;gHandoffState.draft_round=0;roll_draft();}}
   menu_open(service[i]);return TRUE;
  }
  /* Physical examples of optional soft fusion gates; opening never edits a
     pre-existing room gate. */
  if(near(sx(5),sy(5),24)){
   if(gHandoffState.fusion_flags&1){s.request=HS_ITEM;return TRUE;}say("A green shaped fusion half opens this cache.");return TRUE;}
  if(near(sx(25),sy(5),24)){
   if(gHandoffState.fusion_flags&2){s.request=HS_PORTAL;return TRUE;}say("A blue shaped fusion half opens this pocket cave.");return TRUE;}
  return FALSE;
 }
 if(s.prize&&near(sx(NODE_X),sy(NODE_Y),22)){claim();return TRUE;}
 if(board_kind()){
  if(near(sx(14),sy(15),22)){handoff_board_reset();return TRUE;}
  if(handoff_board_push(gPlayer->facing))return TRUE;
 }
 if(s.kind==HS_ITEM&&near(sx(NODE_X),sy(NODE_Y),24)&&!finished()){finish();claim();return TRUE;}
 if(s.kind==HS_FAIRY&&near(sx(NODE_X),sy(NODE_Y),24)){player_heal(gPl.hp_max);finish();sfx_play(SFX_HEART);return TRUE;}
 if(s.kind==HS_NPC&&near(sx(NODE_X),sy(NODE_Y),24)){
  if(!finished()&&gPl.gilt>=10){gPl.gilt-=10;give(LI_HEART_PIECE);finish();s.prize=0;}
  else say(finished()?"The stranger is at peace.":"Ten gilt buys a small piece of heart. No debt.");
  return TRUE;
 }
 if(s.kind==HS_PORTAL&&near(sx(NODE_X),sy(NODE_Y),28)){
  if(!legacy_item_owned(LI_OCARINA)&&!legacy_item_owned(LI_ROCS_CAPE))give(LI_ROCS_CAPE);
  finish();s.request=HS_POCKET;return TRUE;
 }
 if(s.kind==HS_POCKET&&finished()&&near(sx(16),sy(19),24)){s.request=HS_HUB;return TRUE;}
 if(s.kind==HS_GOLD_GATE){
  if(near(sx(12),sy(10),24)){fuse(3);if(gHandoffState.gold_fused&1)for(i=11;i<16;i++)room_change(i,8,MT_CAVE_FLOOR0);return TRUE;}
  if(near(sx(19),sy(10),24)){fuse(4);if((gHandoffState.gold_fused&14)==14)for(i=16;i<=20;i++)room_change(i,8,MT_CAVE_FLOOR0);return TRUE;}
  if(near(sx(16),sy(5),22)&&(gHandoffState.gold_fused&15)==15&&!finished()){finish();claim();return TRUE;}
 }
 if(q->state==2&&q->kind==HQ_CARRY&&q->origin_cell==s.site){
  if(q->cargo_ground&&near(q->cargo_x,q->cargo_y,22)&&!gPl.carry){
   q->cargo_ground=0;q->cargo_held=1;gPl.carry=CARRY_POT;gPlayer->state=PS_LIFT;gPlayer->timer=0;gPl.input_lock=0;sfx_play(SFX_ITEM);return TRUE;}
  if(q->cargo_held&&near(q->receiver_x,q->receiver_y,24)){
   if(q->wave<2||enemies_alive()){say("Keep the pot safe until both ambushes are clear.");return TRUE;}
   q->cargo_held=0;gPl.carry=CARRY_NONE;gPlayer->state=PS_NORMAL;quest_win();say("Not a crack. A careful delivery earns its keep.");return TRUE;}
 }
 if(q->kind==HQ_COURIER&&q->state==2&&s.kind==HS_QUEST_COURIER&&near(sx(8),sy(17),24)){say("Take the parcel to the wandering fuser at the Forest entry. It is marked with the Compass.");return TRUE;}
 if(q->state==4&&q->origin_cell==s.site&&near(sx(8),sy(17),24)){quest_start(q->kind);return TRUE;}
 return FALSE;
}
bool8 handoff_pre_player(void){
 if(!inside_hand()||!gPlayer)return FALSE;
 if(s.sleep_timer){gKeysDown=0;gKeysHeld=0;return TRUE;}
 if(s.kind==HS_TRAVERSAL)return handoff_mobility_pre_player();
 if(s.kind==HS_OBJECT_COURSE)return handoff_objects_pre_player();
 if(board_kind()){
  const HandoffPuzzle*p=handoff_puzzle(gHandoffPuzzleIndex);
  if(gKeysDown&KEY_SELECT){handoff_board_reset();return TRUE;}
  /* The 5x5 board is grounded: jumping cannot cross block/wall boundaries.
     Walking and deliberate one-cell pushes retain the usual controls. */
  if(PX(gPlayer->x)>=BOARD_X*16-8&&PX(gPlayer->x)<(BOARD_X+5)*16+8&&PX(gPlayer->y)>=BOARD_Y*16-8&&PX(gPlayer->y)<(BOARD_Y+5)*16+16){
   gKeysHeld&=~player_equip_keys(EQ_CLOAK);gKeysDown&=~player_equip_keys(EQ_CLOAK);
   if(gPlayer->state==PS_JUMP){gPlayer->z=0;gPlayer->state=PS_NORMAL;}
  }
  (void)p;
 }
 return FALSE;
}
void handoff_update(void){
 HandoffQuest*q=&gHandoffState.quest;int i,x0,y0,x1,y1;
 s.clock++;if(s.invulnerable)s.invulnerable--;if(s.picolyte_ticks)s.picolyte_ticks--;
 if(FOOD(HF_CURSE_ROT)&&(gFrame&255)==0&&gPl.hp>2)gPl.hp--;
 /* These effects are local visual overlays; normal menu/text blending remains
    in charge. The root applies handoff_visual_dim in its world video pass. */
 if(FOOD(HF_CURSE_BLUR)&&gGame.state==GS_PLAY){REG_MOSAIC=0x0011;REG_BG2CNT|=0x0040;}else if(gGame.state==GS_PLAY){REG_BG2CNT&=~0x0040;}
 for(i=0;i<8;i++)if(sHalves[i].active){
  if(sHalves[i].age<255)sHalves[i].age++;
  if(sHalves[i].age>12&&near(sHalves[i].x,sHalves[i].y,12)){
   int c=sHalves[i].color,a=sHalves[i].shape;sHalves[i].active=0;journal_note_legacy_item(LI_KINSTONE);gHandoffState.kinstone_shapes[c][a]=MIN(legacy_item_owned(LI_KINSTONE_BAG)?99:9,gHandoffState.kinstone_shapes[c][a]+1);gLegacyInventory.kinstones[c]=MIN(999,gLegacyInventory.kinstones[c]+1);sfx_play(SFX_PICKUP);
  }
 }
 if(!inside_hand())return;
 if(s.sleep_timer){
  s.sleep_timer--;
  if(s.sleep_timer==90){player_heal(s.sleep_choice==0?MAX(8,gPl.hp_max/4):s.sleep_choice==1?MAX(16,gPl.hp_max/2):gPl.hp_max);if(s.sleep_choice){gHandoffState.inn_reward=random_reward(s.sleep_choice-1);room_change_overlay(12,10,MT_MYST_CHEST);}}
  if(s.sleep_timer==45)fade_start(0,1);
  if(!s.sleep_timer){gPlayer->state=PS_NORMAL;gPl.input_lock=0;sfx_play(SFX_HEART);say(gHandoffState.inn_reward?"Rested. Your promised chest waits beside the bed.":"Rested. The Drain murmurs beyond the wall.");}
  return;
 }
 if(gPlayer&&PX(gPlayer->y)>22*16&&PX(gPlayer->x)>14*16&&PX(gPlayer->x)<18*16){
  if(s.kind==HS_POCKET){s.request=HS_HUB;return;}
  s.exit=1;return;
 }
 if(s.kind==HS_TRAVERSAL){handoff_mobility_update();return;}
 if(s.kind==HS_OBJECT_COURSE){handoff_objects_update();if(handoff_objects_complete()&&!finished()){HSET(gHandoffState.completed,s.site);give(random_reward(1));sfx_play(SFX_CHEST);handoff_notify(HN_EVENT,AREA_HANDOFF,s.site,0);}return;}
 if(q->state==1&&!textbox_active())q->state=2;
 if(q->state==2&&q->origin_area==AREA_HANDOFF&&q->origin_cell==s.site){
  if(q->timer&&!--q->timer)quest_fail();
  if(q->kind==HQ_HUNT&&s.cadence==0)refill(CLAMP((int)q->quota-q->count,3,6));
  if(q->kind==HQ_SCAV&&q->mode==0){int x=sx(23)+(int)((s.clock/45)%4)*8,y=sy(8);if(near(x,y,14))quest_win();}
  if(q->kind==HQ_STEALTH){
   for(i=0;i<3;i++)if(watcher_sees(sx(10+i*6),sy(7+i%2*9),((s.clock/90)+i)&3)){quest_fail();break;}
   if(near(sx(25),sy(5),15))quest_win();
  }
  if(q->kind==HQ_CARRY){
   if(q->cargo_held&&gPl.carry!=CARRY_POT&&!q->cargo_flying){q->cargo_held=0;q->cargo_ground=1;q->cargo_x=PX(gPlayer->x);q->cargo_y=PX(gPlayer->y);}
   if(q->cargo_held&&((q->wave==0&&PX(gPlayer->x)>14*16)||(q->wave==1&&!enemies_alive()&&PX(gPlayer->y)<10*16))){q->wave++;refill(q->wave+2);sfx_play(SFX_SPIT);}
  }
 }
 if(player_lamp_box(&x0,&y0,&x1,&y1))handoff_tool_box(LE_HIT_LANTERN,x0,y0,x1,y1);
 if(player_sword_box(&x0,&y0,&x1,&y1))handoff_tool_box(LE_HIT_SWORD,x0,y0,x1,y1);
 if(board_kind()&&!finished()&&gHandoffBoardSolved){if(s.kind==HS_QUEST_BLOCKS)quest_win();else finish();}
 if(s.kind==HS_MEMORY_SHOW||s.kind==HS_MEMORY_INPUT)memory_tick();
 if(s.kind==HS_SWITCHES)switch_tick();
 if((s.kind==HS_CLEANUP||s.kind==HS_TORCHES)&&!s.clean&&!finished())finish();
 if((s.kind==HS_MINIBOSS||s.kind==HS_BOSS)&&!s.phase&&!s.cadence)s.phase=spawn_one(s.kind==HS_MINIBOSS?LE_DARK_NUT_0:(s.seed&1)?LE_GIANT_CHUCHU_GREEN:LE_BIG_OCTOROK)?1:0;
 if(s.kind==HS_MINIBOSS&&s.phase==1&&!enemies_alive())finish();
 if(s.kind==HS_WAVES||s.kind==HS_ARENA||s.kind==HS_SURVIVE||s.kind==HS_POCKET){
  if(s.kind==HS_SURVIVE&&s.timer&&!--s.timer)finish();
  if(!s.cadence&&(!finished()||(s.prize&&(s.site<160||s.site>162))||s.kind==HS_ARENA)){
   if(!gHandoffState.remaining[s.site]&&s.kind!=HS_SURVIVE){
    if(s.kind==HS_ARENA){gHandoffState.wave[s.site]++;if(gHandoffState.wave[s.site]==5&&!FOOD(HF_FLEET)){give(HANDOFF_FLEET);say("Five waves. A golden croissant grants Fleet: brief safety on entering each room.");}if(!finished())finish();wave_begin();}
    else if(gHandoffState.wave[s.site]>=3)finish();
    else{gHandoffState.wave[s.site]++;wave_begin();}
   }
   /* Cleared challenge rooms never repopulate after prize collection. */
   if(enemies_alive()<MIN(3,s.wave_target))refill(MIN(3,s.wave_target));
  }
 }
 s.cadence=(s.cadence+1)%20;
}
void handoff_draw(void){
 int i;HandoffQuest*q=&gHandoffState.quest;
 if(!inside_hand()){
  if(s.recipient_x>=0&&sFieldTile)draw_sprite(s.recipient_x-8-gCamX,s.recipient_y-16-gCamY,SHEET_HANDOFF,sFieldTile,0,0,1,PAL_OBJ_FX);
  for(i=0;i<8;i++)if(sHalves[i].active){
   LooseHalf*h=&sHalves[i];u16 tile=sHalfTile[h->color][h->shape];
   if(tile)draw_sprite(h->x-8-gCamX,h->y-16-gCamY,SHEET_HANDOFF,tile,0,0,1,PAL_OBJ_FX);
  }
  return;
 }
 if(s.kind==HS_TRAVERSAL){handoff_mobility_draw();return;}
 if(s.kind==HS_OBJECT_COURSE){handoff_objects_draw();return;}
 if(!s.tile)return;
 if(s.kind==HS_HUB){
  for(i=0;i<8;i++)draw_prop(HA_DESK,sx(sDesk[i][0]),sy(sDesk[i][1]),1);
  draw_prop(HA_FUSER,sx(5),sy(5),1);draw_prop(HA_PORTAL,sx(25),sy(5),1);
 }
 if(s.kind==HS_MEMORY_SHOW||s.kind==HS_MEMORY_INPUT)for(i=0;i<4;i++)if((s.kind==HS_MEMORY_SHOW&&s.memory_show==i)||(s.kind==HS_MEMORY_INPUT&&i==s.memory_input-1))draw_prop(HA_TOKEN,sx(9+i*4),sy(10)-2,1);
 if(board_kind()){
  const HandoffPuzzle*p=handoff_puzzle(gHandoffPuzzleIndex);
  for(i=0;i<3;i++)draw_prop(HA_BLOCK_FREE+p->axes[i],sx(BOARD_X+gHandoffBoardBlocks[i]%5),sy(BOARD_Y+gHandoffBoardBlocks[i]/5),1);
  if(p->kind)draw_prop(HA_GOAL,sx(BOARD_X+p->goal%5),sy(BOARD_Y+p->goal/5),2);
  draw_prop(HA_RESET,sx(14),sy(15),1);
 }
 if(s.kind==HS_TORCHES)for(i=0;i<3;i++)draw_prop(s.clean&(1u<<i)?HA_TORCH_OFF:HA_TORCH_LIT,sx(8+i*8),sy(10),1);
 if(s.kind==HS_CLEANUP)for(i=0;i<s.quota;i++)if(s.clean&(1u<<i))draw_prop(i<6&&s.theme!=1?HA_WEB:HA_DUST,sx(7+(i%4)*6),sy(7+(i/4)*5),2);
 if(s.kind==HS_PORTAL||s.kind==HS_POCKET)draw_prop(HA_PORTAL,sx(16),sy(s.kind==HS_PORTAL?11:19),1);
 if(s.kind==HS_GOLD_GATE){draw_prop(HA_GOLD,sx(12),sy(10),1);draw_prop(HA_GOLD,sx(19),sy(10),1);}
 if(s.kind==HS_NPC)draw_prop(HA_FUSER,sx(NODE_X),sy(NODE_Y),1);
 if(s.kind==HS_ITEM&&!finished())draw_prop(HA_TOKEN,sx(NODE_X),sy(NODE_Y),1);
 if(q->state==2&&q->origin_cell==s.site){
  if(q->kind==HQ_SCAV)draw_prop(q->mode==0?HA_TOKEN:q->mode==1?HA_LEAF:HA_GOAL,q->mode==0?sx(23)+(int)((s.clock/45)%4)*8:q->cargo_x,q->mode==0?sy(8):q->cargo_y,2);
  if(q->kind==HQ_STEALTH){
   for(i=0;i<3;i++){
    int face=((s.clock/90)+i)&3,x=sx(10+i*6),y=sy(7+i%2*9),j;draw_prop(HA_WATCH_N+face,x,y,1);
    for(j=1;j<=3;j++)if(!room_solid_px(x+sDX[face]*j*16,y+sDY[face]*j*16))draw_prop(HA_GOAL,x+sDX[face]*j*16,y+sDY[face]*j*16,2);
   }
   draw_prop(HA_GOAL,sx(25),sy(5),2);
  }
  if(q->kind==HQ_CARRY){if(q->cargo_ground)draw_prop(HA_POT,q->cargo_x,q->cargo_y,1);draw_prop(HA_RECIPIENT,q->receiver_x,q->receiver_y,1);}
  if(q->kind==HQ_COURIER)draw_prop(HA_PARCEL,sx(8),sy(17),1);
 }
 for(i=0;i<8;i++)if(sHalves[i].active)draw_prop(HA_GREEN_HALF+sHalves[i].color*3+sHalves[i].shape,sHalves[i].x,sHalves[i].y,1);
}
bool8 handoff_wants_exit(void){return s.exit;}
int handoff_requested_site(void){return s.request;}
void handoff_clear_request(void){s.request=255;s.exit=0;}
int handoff_current_site(void){return s.site;}
int handoff_current_kind(void){return s.kind;}

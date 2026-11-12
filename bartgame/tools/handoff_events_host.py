#!/usr/bin/env python3
"""Compile and exercise the actual additive C module, without shared builds.
Not a screenshot/timing substitute. Covers all proof boards and source-exact
item/food machinery and regional chain admission using explicit graph/engine
fixtures. The fixture is not a replacement for actual room geometry or mGBA.
"""
import argparse,hashlib,json,subprocess,tempfile
from pathlib import Path
GAME=Path(__file__).resolve().parents[1]
HARNESS=r'''
#include <assert.h>
#include <stdio.h>
#include "handoff_events.c"
#include "legacy_items_metadata.inc"
LegacyInventory gLegacyInventory;
PlayerState gPl;
GameState gGame;
World gWorld;
Actor* gPlayer;
Actor gActors[ACTOR_MAX];
CreamProgress gCreamProgress;
RegionalContentSpots gRegionalSpots;
RegionalContentDiscovery gRegionalDiscovery[50];
static RegionalContentPlan fixturePlan[50];
static unsigned char fixtureReach[50];
static int spawnedGoal,winCalls,reachBatches;
bool8 regional_content_get(int area,int cell,RegionalContentPlan*out){int at=area==AREA_FOREST?cell:area==AREA_CREAM?25+cell:-1;if(at<0||at>=50)return FALSE;if(out)*out=fixturePlan[at];return TRUE;}
bool8 regional_content_reachable(int area,int cell){int at=area==AREA_FOREST?cell:area==AREA_CREAM?25+cell:-1;return at>=0&&at<50&&fixtureReach[at];}
void regional_content_reach_masks(u32 out[2]){reachBatches++;out[0]=out[1]=0;for(int i=0;i<50;i++)if(fixtureReach[i])out[i/25]|=1u<<(i%25);}
u8 regional_content_marks(int area,int cell,RegionalContentDiscovery*out){int at=area==AREA_FOREST?cell:area==AREA_CREAM?25+cell:-1;if(at<0||at>=50)return 0;*out=gRegionalDiscovery[at];return out->marks;}
bool8 regional_content_door_open(int area,int cell){RegionalContentPlan p;regional_content_get(area,cell,&p);return p.fusion_color!=1||(gHandoffState.fusion_flags&2);}
bool8 handoff_objects_can_solve(int pattern){return pattern<7;}
bool8 legacy_enemy_can_spawn(int type){(void)type;return TRUE;}
Actor*legacy_item_spawn(int item,int x,int y){(void)x;(void)y;if(item==LI_EARTH_ELEMENT)spawnedGoal++;return &gActors[1];}
void room_change_overlay(int x,int y,u16 mt){(void)x;(void)y;(void)mt;}
void game_win_chain(void){winCalls++;}
char* vwf_num(char*b,int n,int w){(void)w;sprintf(b,"%d",n);return b;}
static void plan_fixture(void){
 for(int i=0;i<50;i++){RegionalContentPlan*p=&fixturePlan[i];*p=(RegionalContentPlan){0};p->area=i<25?AREA_FOREST:AREA_CREAM;p->cell=i%25;p->field_site=32+i;p->interior_site=i<46?82+i:255;p->event_kind=HS_POTS;p->fusion_color=255;p->stage=i%4;p->mechanism_variant=0;fixtureReach[i]=i!=24;}
 fixturePlan[3].event_kind=HS_BOSS;fixturePlan[4].quest_kind=HQ_HUNT;fixturePlan[2].has_wave=fixturePlan[27].has_wave=1;fixturePlan[8].fusion_color=0;
}
static unsigned char owned[LI_COUNT];
const LegacyItemDef* legacy_item_def(int id){return id>=0&&id<LI_COUNT?&gLegacyItemDefs[id]:0;}
bool8 legacy_item_owned(int id){return id>=0&&id<LI_COUNT?owned[id]:0;}
static unsigned seed=1;
u32 hash32(u32 a,u32 b){u32 x=a^b*0x9e3779b9u;x^=x>>16;x*=0x7feb352du;x^=x>>15;x*=0x846ca68bu;return x^(x>>16);}
u32 rng_next(Rng*r){r->s^=r->s<<13;r->s^=r->s>>17;r->s^=r->s<<5;return r->s;}
u32 rng_range(Rng*r,u32 n){return n?rng_next(r)%n:0;}
void rng_seed(Rng*r,u32 n){r->s=n?n:1;}
void sfx_play(int id){(void)id;}
void journal_note_legacy_item(int id){(void)id;}
void journal_note_gold_half(int id){(void)id;}
void textbox_open(const char*p){(void)p;}
void legacy_item_grant(int id,int amount){if(id>0&&id<LI_COUNT&&amount)owned[id]=1;}
int main(void){
 int i,j,tests=0,seen[LI_COUNT+4]={0};
 for(i=0;i<HANDOFF_PUZZLE_COUNT;i++){assert(handoff_puzzle_verify(handoff_puzzle(i)));tests++;}
 for(i=0;i<1000;i++){
  HandoffPuzzle p=*handoff_puzzle(hash32(i,77)%HANDOFF_PUZZLE_COUNT);
  p.length=33;assert(!handoff_puzzle_verify(&p));
  p=*handoff_puzzle(i);p.entry=p.blocks[0];assert(!handoff_puzzle_verify(&p));tests+=2;
 }
 handoff_init();owned[LI_SKILL_SWORD_BEAM]=1;
 for(i=0;i<20;i++){assert(handoff_apply_item_effect(sFoodItems[i],1));assert(FOOD(i));assert(!eligible(sFoodItems[i]));tests+=3;}
 assert(handoff_outgoing_damage(0)==0);assert(handoff_incoming_damage(0)==0);
 assert(handoff_player_knockback(256)==0);assert(handoff_walk_speed(256)==384);
 assert(handoff_immunities()==7);assert(handoff_shop_price(999)==50);tests+=6;
 handoff_init();handoff_apply_item_effect(LI_CHARM_NAYRU,1);handoff_apply_item_effect(LI_CHARM_FARORE,1);handoff_apply_item_effect(LI_CHARM_DIN,1);
 assert(handoff_incoming_damage(24)==3);assert(handoff_outgoing_damage(4)==12);tests+=2;
 handoff_apply_item_effect(LI_SHELLS,1);assert(handoff_incoming_damage(100)==0);assert(s.invulnerable==180);tests+=2;
 handoff_init();for(i=0;i<LI_COUNT;i++)owned[i]=0;
 rng_seed(&s.rng,12345);
 for(i=0;i<1000;i++){
  gHandoffState.draft_round=i%3;roll_draft();
  for(j=0;j<3;j++){assert(gHandoffState.draft[j]);assert(eligible(gHandoffState.draft[j]));}
  assert(gHandoffState.draft[0]!=gHandoffState.draft[1]&&gHandoffState.draft[0]!=gHandoffState.draft[2]&&gHandoffState.draft[1]!=gHandoffState.draft[2]);tests+=7;
 }
 owned[LI_BOTTLE1]=owned[LI_RED_SWORD]=owned[LI_BLUE_SWORD]=1;
 for(i=0;i<10000;i++){
  int item=reward_pick(127,i%3,hash32(i,seed));assert(eligible(item));seen[item<LI_COUNT?item:LI_COUNT+item-HANDOFF_GOLD_FLOW]++;
 }
 for(i=0;i<ARRAY_COUNT(sRewards);i++){
  const Reward*r=&sRewards[i];if(eligible(r->item)&&!(r->cat==LCAT_SKILL&&r->item>=LI_SKILL_FAST_SPIN))assert(seen[r->item<LI_COUNT?r->item:LI_COUNT+r->item-HANDOFF_GOLD_FLOW]);
 }
 plan_fixture();gGame.seed=1;gGame.state=GS_PLAY;gGame.area=AREA_FOREST;gPlayer=&gActors[0];
 handoff_init();gHandoffState.contract_step=0;reachBatches=0;contract_next();assert(reachBatches==1);tests++;
 assert(gHandoffState.contract_kind==HC_EVENT&&gHandoffState.contract_target>=82&&gHandoffState.contract_target<128);tests++;
 {RegionalContentPlan p;assert(decode_site(gHandoffState.contract_target,&p)&&regional_content_reachable(p.area,p.cell));tests++;}
 handoff_init();gHandoffState.contract_step=1;contract_next();assert(gHandoffState.contract_kind==HC_WAVE);assert(gHandoffState.contract_target==34||gHandoffState.contract_target==59);tests+=2;
 handoff_init();gRegionalDiscovery[8].cache=(Spot){5,5};gRegionalDiscovery[8].marks=RC_MARK_CACHE;gRegionalDiscovery[6].cache=(Spot){9,9};gRegionalDiscovery[6].marks=RC_MARK_CACHE;
 gHandoffState.contract_step=2;contract_next();assert(gHandoffState.contract_kind==HC_ITEM&&gHandoffState.contract_target==38);tests++;
 gRegionalDiscovery[6].cache=(Spot){0,0};gHandoffState.contract_step=2;contract_next();assert(gHandoffState.contract_kind==HC_WAVE);tests++;
 handoff_init();for(i=0;i<3;i++){gWorld.key_cell[i]=i;gWorld.cells[i].flags=0;gWorld.myst_flags[i]=0;}
 gHandoffState.contract_step=3;contract_next();assert(!gHandoffState.contract_state&&!gHandoffState.contract_target);tests++;
 for(i=0;i<3;i++){gWorld.cells[i].flags=CF_ITEM_TAKEN;gWorld.myst_flags[i]=MF_WON;}
 contract_next();assert(gHandoffState.contract_state==1&&gHandoffState.contract_kind==HC_BOSS&&gHandoffState.contract_target==85);tests++;
 gGame.area=AREA_HANDOFF;s.site=85;spawnedGoal=winCalls=0;
 handoff_notify(HN_BOSS,AREA_HANDOFF,85,0);assert(gHandoffState.contract_step==4&&gHandoffState.contract_state==1&&spawnedGoal==1&&winCalls==0);tests++;
 handoff_notify(HN_ITEM,AREA_HANDOFF,85,LI_EARTH_ELEMENT);assert(gHandoffState.contract_state==2&&winCalls==1&&owned[LI_FOURSWORD]);tests++;
 gHandoffState.quest.origin_area=AREA_HANDOFF;gHandoffState.quest.state=2;handoff_resume_regional(TRUE);assert(gHandoffState.contract_step==0&&gHandoffState.contract_target>=82&&gHandoffState.quest.state==0&&owned[LI_FOURSWORD]);tests++;
 {int bosses[3]={0};for(i=0;i<300;i++){s.seed=i;int type=chamber_boss_type();if(type==LE_GIANT_CHUCHU_GREEN)bosses[0]++;else if(type==LE_GIANT_CHUCHU_ELECTRIC)bosses[1]++;else if(type==LE_BIG_OCTOROK)bosses[2]++;else assert(0);}assert(bosses[0]&&bosses[1]&&bosses[2]);tests++;}
 for(i=0;i<4;i++){
  handoff_init();gPl.hp=64;gPl.gilt=999;gHandoffState.food_mask=1u<<HF_WALK_SPEED;
  gHandoffState.quest.state=2;gHandoffState.quest.stake=i;gHandoffState.difficulty=12;
  quest_fail();assert(gHandoffState.quest.state==4);
  assert(gPl.gilt==(i==0?999:i==1?949:i==2?899:799));assert(gPl.hp==(i<2?64:32));
  assert(i==3?!FOOD(HF_WALK_SPEED):FOOD(HF_WALK_SPEED));tests+=4;
 }
 handoff_init();gHandoffState.entitlement_mode=1;
 assert(!handoff_event_unlocked(HS_POTS));assert(!handoff_event_unlocked(HS_FAIRY));assert(!handoff_region_unlocked(AREA_CREAM));assert(handoff_difficulty_cap()==3);tests+=4;
 gHandoffState.score=500;assert(handoff_event_unlocked(HS_POTS));assert(handoff_region_unlocked(AREA_CREAM));assert(!handoff_event_unlocked(HS_BOSS));tests+=3;
 gHandoffState.wins=1;assert(handoff_event_unlocked(HS_FAIRY));assert(handoff_difficulty_cap()==5);tests+=2;
 gHandoffState.score=1500;assert(handoff_event_unlocked(HS_BOSS));assert(handoff_difficulty_cap()==6);tests+=2;
 gHandoffState.entitlement_mode=0;gHandoffState.score=0;gHandoffState.wins=0;
 for(i=0;i<HS_COUNT;i++){assert(handoff_event_unlocked(i));tests++;}
 assert(handoff_region_unlocked(AREA_CREAM));assert(handoff_difficulty_cap()==12);tests+=2;
 gHandoffState.quest=(HandoffQuest){0};gHandoffState.contract_state=0;assert(!entitlement_would_strand_cream());tests++;
 gHandoffState.quest.kind=HQ_COURIER;gHandoffState.quest.state=2;gHandoffState.quest.origin_area=AREA_FOREST;gHandoffState.quest.target_area=AREA_CREAM;assert(entitlement_would_strand_cream());tests++;
 gHandoffState.quest.kind=HQ_HUNT;assert(!entitlement_would_strand_cream());tests++;
 gHandoffState.quest.origin_area=AREA_CREAM;assert(entitlement_would_strand_cream());tests++;
 gHandoffState.score=500;assert(!entitlement_would_strand_cream());gHandoffState.score=0;gHandoffState.quest.state=3;tests++;
 gHandoffState.contract_state=1;gHandoffState.contract_target=59;assert(entitlement_would_strand_cream());gHandoffState.contract_target=34;assert(!entitlement_would_strand_cream());tests+=2;
 for(i=0;i<13;i++){int total=0;for(j=0;j<6;j++)total+=sTierWeights[i][j];assert(total==100);tests++;}
 printf("{\"passed\":%d,\"pool_boards\":1528,\"corrupt_boards_rejected\":2000,\"draft_seeds\":1000,\"reward_draws\":10000,\"HandoffState_bytes\":%u}\n",tests,(unsigned)sizeof(HandoffState));return 0;
}
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--report',type=Path);a=p.parse_args()
 with tempfile.TemporaryDirectory(prefix='handoff-host-') as t:
  c=Path(t)/'test.c';binary=Path(t)/'test';c.write_text(HARNESS)
  cmd=['gcc','-std=gnu99','-Os','-ffunction-sections','-fdata-sections','-Wno-attributes','-I'+str(GAME/'src'),'-I'+str(GAME/'build/gen'),str(c),'-Wl,--gc-sections','-o',str(binary)]
  subprocess.run(cmd,check=True,capture_output=True,text=True)
  raw=subprocess.run([str(binary)],check=True,capture_output=True,text=True).stdout
  result=json.loads(raw)
  result['method']=__doc__
  result['scope']='Actual C event/economy/puzzle and adaptive-chain functions with explicit admitted-graph, actor-spawn and UI spies. Native movement, collision, pixels and timing require the separate mGBA tests.'
  result['source_sha256']={n:hashlib.sha256((GAME/n).read_bytes()).hexdigest() for n in ('src/handoff_events.c','src/handoff_field.inc','src/handoff_events.h','src/legacy_items_metadata.inc')}
  result['tool_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
  out=json.dumps(result,indent=2)+'\n'
  print(out,end='')
  if a.report:a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(out)
if __name__=='__main__':main()

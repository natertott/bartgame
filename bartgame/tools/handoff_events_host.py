#!/usr/bin/env python3
"""Compile and exercise the actual additive C module, without shared builds.
Not a screenshot/timing substitute. Covers all proof boards and source-exact
item/food/contract state machinery with small explicit engine stubs.
"""
import argparse,json,subprocess,tempfile
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
 for(i=0;i<10000;i++){
  int item=reward_pick(127,i%3,hash32(i,seed));assert(eligible(item));seen[item<LI_COUNT?item:LI_COUNT+item-HANDOFF_GOLD_FLOW]++;
 }
 for(i=0;i<ARRAY_COUNT(sRewards);i++){
  const Reward*r=&sRewards[i];if(eligible(r->item)&&!(r->cat==LCAT_SKILL&&r->item>=LI_SKILL_FAST_SPIN))assert(seen[r->item<LI_COUNT?r->item:LI_COUNT+r->item-HANDOFF_GOLD_FLOW]);
 }
 handoff_init();gHandoffState.contract_state=1;gHandoffState.contract_kind=HC_ITEM;gHandoffState.contract_item=LI_MOLE_MITTS;gHandoffState.contract_step=2;
 handoff_notify(HN_ITEM,AREA_FOREST,3,LI_BOW);assert(gHandoffState.contract_step==2);
 handoff_notify(HN_ITEM,AREA_FOREST,3,LI_MOLE_MITTS);assert(gHandoffState.contract_step==3&&gHandoffState.contract_kind==HC_BOSS);tests+=2;

 handoff_init();for(i=0;i<32;i++){gHandoffState.completed[i]=255;gHandoffState.won[i]=255;}gHandoffState.contract_step=0;contract_next();
 assert(!HBIT(gHandoffState.completed,HANDOFF_CONTRACT_BASE)&&!HBIT(gHandoffState.won,HANDOFF_CONTRACT_BASE));assert(HBIT(gHandoffState.completed,gHandoffState.contract_target));tests+=3;
 gHandoffState.contract_step=2;contract_next();assert(!HBIT(gHandoffState.completed,HANDOFF_CONTRACT_BASE+2));assert(gHandoffState.contract_kind==HC_ITEM&&gHandoffState.contract_target==HS_POCKET);tests+=2;
 handoff_init();gHandoffState.contract_state=1;gHandoffState.contract_kind=HC_ITEM;gHandoffState.contract_item=HANDOFF_GOLD_LEFT;gHandoffState.contract_step=2;
 handoff_notify(HN_ITEM,AREA_HANDOFF,HS_POCKET,HANDOFF_GOLD_FLOW);assert(gHandoffState.contract_step==2);tests++;
 handoff_notify(HN_ITEM,AREA_HANDOFF,HS_POCKET,HANDOFF_GOLD_LEFT);assert(gHandoffState.contract_step==3&&gHandoffState.contract_kind==HC_BOSS);tests++;
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
  out=subprocess.run([str(binary)],check=True,capture_output=True,text=True).stdout
  print(out,end='')
  if a.report:a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(out)
if __name__=='__main__':main()

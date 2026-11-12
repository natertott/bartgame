#!/usr/bin/env python3
"""Execute production enemy admission for intact and released Acro stacks.

Host actors and item/terrain queries are explicit fixtures. This tests the
actual budget/cap function, not AI, rendering, native timing or room placement.
"""
import argparse,hashlib,json,resource,subprocess,tempfile
from pathlib import Path
GAME=Path(__file__).resolve().parents[1]
HARNESS=r'''
#include <assert.h>
#include <stdio.h>
#include "legacy_enemies.c"
Actor gActors[ACTOR_MAX];
PlayerState gPl;
int actor_count(u8 kind){int count=0;for(int i=1;i<ACTOR_MAX;i++)count+=gActors[i].kind==kind;return count;}
bool8 legacy_item_owned(int item){(void)item;return FALSE;}
u8 room_type(int x,int y){(void)x;(void)y;return TT_FLOOR;}
Room gRoom;
static int checks;
#define CHECK(c) do{checks++;assert(c);}while(0)
static void add(int index,int type,int child){gActors[index].kind=AK_ENEMY;gActors[index].type=type;gActors[index].v[3]=child;}
static void stack(int first,int attached){for(int i=0;i<6;i++){add(first+i,LE_ACRO_BANDIT_0,attached&&i?2:0);gActors[first+i].v[2]=i;gActors[first+i].v[4]=first;}}
int main(void){
 const LegacyEnemyDef*acro=legacy_enemy_def(LE_ACRO_BANDIT_0);
 CHECK(acro&&acro->cost==6&&acro->cap==2);
 CHECK(legacy_enemy_def(LE_CHUCHU_0)->cost==1&&legacy_enemy_def(LE_OCTOROK_0)->cost==1);
 for(int attached=0;attached<2;attached++){
  memset(gActors,0,sizeof(gActors));stack(1,attached);
  for(int i=7;i<25;i++)add(i,LE_CHUCHU_0,0);
  CHECK(actor_count(AK_ENEMY)==24);
  CHECK(legacy_enemy_can_spawn(LE_OCTOROK_0)); /*6Acro+18=24, next1fits*/
  add(25,LE_CHUCHU_0,0);add(26,LE_CHUCHU_0,0);
  CHECK(actor_count(AK_ENEMY)==26);
  CHECK(!legacy_enemy_can_spawn(LE_OCTOROK_0)); /*26+1cannotfit*/
 }
 memset(gActors,0,sizeof(gActors));stack(1,1);
 CHECK(legacy_enemy_can_spawn(LE_ACRO_BANDIT_0)); /*oneintactstack, cap2*/
 stack(7,1);CHECK(!legacy_enemy_can_spawn(LE_ACRO_BANDIT_0)); /*twogroups*/
 for(int i=1;i<13;i++)gActors[i].v[3]=0;
 CHECK(!legacy_enemy_can_spawn(LE_ACRO_BANDIT_0)); /*releasedmembersstillcountforcap*/
 memset(gActors,0,sizeof(gActors));for(int i=1;i<=28;i++)add(i,LE_CHUCHU_0,1);
 CHECK(!legacy_enemy_can_spawn(LE_OCTOROK_0)); /*actor28ceilingsurvives*/
 printf("{\"checks\":%d,\"passed\":%d,\"Acro_stack_cost\":6,\"global_cost_cap\":26,\"actor_cap\":28}\n",checks,checks);
 return 0;
}
'''

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--report',type=Path)
    ap.add_argument('--negative-commit',help='Also require the same regression to fail against this old source commit.')
    a=ap.parse_args()
    with tempfile.TemporaryDirectory(prefix='legacy-spawn-budget-') as t:
        unit=Path(t)/'review.c';binary=Path(t)/'review';unit.write_text(HARNESS)
        command=['gcc','-std=gnu99','-Os','-ffunction-sections','-fdata-sections','-Wno-attributes','-I'+str(GAME/'src'),'-I'+str(GAME/'build/gen'),str(unit),'-Wl,--gc-sections','-o',str(binary)]
        subprocess.run(command,check=True,capture_output=True,text=True)
        report=json.loads(subprocess.run([str(binary)],check=True,capture_output=True,text=True).stdout)
        report.update(method=__doc__,source_sha256=hashlib.sha256((GAME/'src/legacy_enemies.c').read_bytes()).hexdigest(),tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),command=command)
        if a.negative_commit:
            old=Path(t)/'old-legacy-enemies.c'
            old.write_bytes(subprocess.check_output(['git','-C',str(GAME.parent),'show',a.negative_commit+':bartgame/src/legacy_enemies.c']))
            unit.write_text(HARNESS.replace('"legacy_enemies.c"',json.dumps(str(old))))
            subprocess.run(command,check=True,capture_output=True,text=True)
            result=subprocess.run([str(binary)],capture_output=True,text=True,preexec_fn=lambda:resource.setrlimit(resource.RLIMIT_CORE,(0,0)))
            if result.returncode==0:raise AssertionError('Old implementation unexpectedly passes the intact/released regression')
            report['negative_control']=dict(commit=a.negative_commit,source_sha256=hashlib.sha256(old.read_bytes()).hexdigest(),expected_failure=True,returncode=result.returncode,stderr=result.stderr)
        raw=json.dumps(report,indent=2)+'\n';print(raw,end='')
        if a.report:a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(raw)
if __name__=='__main__':main()

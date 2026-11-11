#!/usr/bin/env python3
"""Exercise actual additive save-extension C on private Linux SRAM.

Uses production serializable types and graph generation, with explicit small
initialization stubs for runtime-only modules. This establishes record selection,
profile isolation, validation and interrupted writes; it does not assert native
cartridge power-loss behavior, base-v1/v2 migration or gameplay UI behavior.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

GAME=Path(__file__).resolve().parents[1]
SHA=lambda x:hashlib.sha256(x).hexdigest()
def clean(s):return re.sub(r'^\s*#include[^\n]*$','',s,flags=re.M)
def fixture():
    src=GAME/'src'
    source='''#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <stddef.h>
#include <stdlib.h>
#include <sys/mman.h>
typedef uint8_t u8;typedef uint16_t u16;typedef uint32_t u32;
typedef int8_t s8;typedef int16_t s16;typedef int32_t s32;typedef u8 bool8;
#define TRUE 1
#define FALSE 0
#define EWRAM_BSS
#define ABS(a) ((a)<0?-(a):(a))
#define MIN(a,b) ((a)<(b)?(a):(b))
#define MAX(a,b) ((a)>(b)?(a):(b))
typedef struct Actor Actor;
'''
    for name in ('cream_world.h','legacy_items.h','handoff_events.h','cream_runtime.h','journal.h','run_extension.h'):
        source+=clean((src/name).read_text())+'\n'
    source+=re.search(r'u32 hash32\([^}]+\}',(src/'util.c').read_text())[0]+'\n'
    graph=(src/'cream_world.c').read_text().replace('#include "cream_world.h"','')
    source+=graph+'\n'
    source+='''LegacyInventory gLegacyInventory;
HandoffState gHandoffState;
CreamProgress gCreamProgress;
u8 gCreamNode,gCreamOpenEdges[CC_NODES];
static int seeded_items,seeded_handoff,seeded_cream;
void legacy_items_new_run(void) {memset(&gLegacyInventory,0,sizeof(gLegacyInventory));seeded_items++;}
void legacy_items_seed_owned(void) {gLegacyInventory.owned[0]|=1u<<LI_SMITH_SWORD;}
void handoff_new_run(u32 seed) {
    u8 prefix[16];(void)seed;memcpy(prefix,&gHandoffState,16);
    memset(&gHandoffState,0,sizeof(gHandoffState));memcpy(&gHandoffState,prefix,16);
    gHandoffState.runs++;gHandoffState.memory_length=4;seeded_handoff++;
}
void cream_runtime_new_run(u32 seed) {
    memset(&gCreamProgress,0,sizeof(gCreamProgress));memset(gCreamOpenEdges,0,sizeof(gCreamOpenEdges));
    gCreamProgress.seed=hash32(seed,0x43524541u);cream_generate(gCreamProgress.seed);
    gCreamNode=gCreamProgress.node=gCreamWorld.entry_node;seeded_cream++;
}
'''
    source+=clean((src/'run_extension.c').read_text())+'\n'
    return source

MAIN=r'''
static u8 *ram,snapshot[32768];
static int checks,guards;
#define CHECK(x) do {checks++;if(!(x)){fprintf(stderr,"line%d: %s\n",__LINE__,#x);exit(1);}}while(0)
#define GUARD(x) do {guards++;if(!(x)){fprintf(stderr,"guard line%d\n",__LINE__);exit(1);}}while(0)
static void fresh(void) {
    memset(ram,0xA7,32768);memset(&gHandoffState,0,sizeof(gHandoffState));run_extension_init();
    seeded_items=seeded_handoff=seeded_cream=0;
    seed_extension(42);gHandoffState.score=100;gHandoffState.difficulty=3;gHandoffState.highest_difficulty=3;
    gHandoffState.food_mask=1;gCreamProgress.rewards=1;gCreamProgress.visited=1;
    gCreamProgress.chests[1]=1;gCreamOpenEdges[0]=1;
    gLegacyInventory.owned[0]|=1u<<LI_PACCI_CANE;gLegacyInventory.bottles[0]=LI_BOTTLE_FAIRY;
}
static void guard_regions(void) {
    int i;
    for(i=0;i<32768;i++)
        if(!((i>=EX_BASE&&i<EX_BASE+2*EX_SLOT_BYTES)||(i>=PROFILE_BASE&&i<PROFILE_BASE+2*PROFILE_BYTES)))
            GUARD(ram[i]==0xA7);
}
static void publish_prefix(const void* record,int offset,int n,int count) {
    const u8* b=record;int i,k=0;
    for(i=0;i<4&&k<count;i++,k++)ram[offset+i]=0;
    for(i=4;i<n&&k<count;i++,k++)ram[offset+i]=b[i];
    for(i=0;i<4&&k<count;i++,k++)ram[offset+i]=b[i];
}
int main(void) {
    int i,n,slot;
    ExtraRun a,b;
    MetaRecord meta;
    ram=mmap((void*)0x0E000000u,32768,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);
    CHECK(ram!=(void*)-1);fresh();CHECK(sizeof(ExtraRun)<EX_SLOT_BYTES&&sizeof(MetaRecord)==32&&META_BYTES==16);
#if BART_ENEMY_LAB
    memcpy(snapshot,ram,32768);run_extension_write(0xABCD);run_profile_write();run_extension_erase();
    CHECK(memcmp(snapshot,ram,32768)==0);
    /* Readable valid profile fixtures are permitted in labs, never persisted. */
    memset(&meta,0,sizeof(meta));meta.magic=PROFILE_MAGIC;meta.version=1;meta.size=sizeof(meta);meta.generation=5;
    memcpy(meta.meta,&gHandoffState,META_BYTES);meta.sum=sum_bytes(&meta,offsetof(MetaRecord,sum));
    memcpy(ram+PROFILE_BASE,&meta,sizeof(meta));memcpy(snapshot,ram,32768);run_extension_init();
    CHECK(gHandoffState.score==100&&sProfileLoaded);run_profile_write();CHECK(memcmp(snapshot,ram,32768)==0);
#else
    run_extension_write(0xABCD);CHECK(find_extra(0xABCD)&&extra_valid());
    CHECK(!find_extra(0xEEEE)&&!run_extension_finished(0xEEEE));guard_regions();
    gHandoffState.score=900;gHandoffState.deaths=4;gHandoffState.difficulty=7;gHandoffState.entitlement_mode=1;
    run_profile_write();run_extension_init();CHECK(gHandoffState.score==900&&gHandoffState.deaths==4);
    memset(&gLegacyInventory,0,sizeof(gLegacyInventory));gCreamProgress.node=49;gCreamOpenEdges[0]=0;gHandoffState.food_mask=0;
    CHECK(run_extension_load(0xABCD,42));
    CHECK(gHandoffState.score==900&&gHandoffState.deaths==4&&gHandoffState.difficulty==7&&gHandoffState.entitlement_mode==1);
    CHECK(gHandoffState.food_mask==1&&gCreamProgress.chests[1]==1&&gCreamOpenEdges[0]==1);
    CHECK(gLegacyInventory.owned[0]&(1u<<LI_PACCI_CANE));CHECK(gLegacyInventory.bottles[0]==LI_BOTTLE_FAIRY);
    CHECK(gCreamNode==gCreamProgress.node&&gCreamWorld.seed==gCreamProgress.seed);
    /* Distinct complete base checksums select their own extension. */
    gCreamProgress.rewards=3;run_extension_write(0xBBBB);CHECK(run_extension_load(0xABCD,42)&&gCreamProgress.rewards==1);
    CHECK(run_extension_load(0xBBBB,42)&&gCreamProgress.rewards==3);
    CHECK(!run_extension_finished(0xBBBB));gCreamProgress.boss_dead=1;run_extension_write(0xBBBB);
    CHECK(run_extension_finished(0xBBBB)&&!run_extension_finished(0xABCD));
    /* Missing/mismatched extensions seed only additive systems, preserving
       the current profile. No base region or journal SRAM is modified. */
    memcpy(snapshot,ram,32768);i=seeded_items;
    CHECK(!run_extension_load(0xFFFF,42)&&seeded_items==i+1&&gHandoffState.score==900);
    CHECK(gCreamProgress.rewards==0&&gCreamProgress.seed==hash32(42,0x43524541u));
    CHECK(memcmp(snapshot,ram,32768)==0);
    CHECK(!run_extension_load(0xBBBB,999)&&gCreamProgress.seed==hash32(999,0x43524541u));
    fresh();run_extension_write(123);CHECK(find_extra(123));a=sExtra;
    /* A valid run can repair both missing profile slots without losing its
       cross-run prefix. This is separate from normal profile precedence. */
    ram[PROFILE_BASE]=ram[PROFILE_BASE+PROFILE_BYTES]=0;run_extension_init();
    CHECK(!sProfileLoaded&&gHandoffState.score==0);CHECK(run_extension_load(123,42)&&gHandoffState.score==100&&sProfileLoaded);
    /* Complete records with unsupported actionable fields reject safely. */
    sExtra=a;sExtra.cream.node=50;sExtra.sum=sum_bytes(&sExtra,offsetof(ExtraRun,sum));CHECK(!extra_valid());
    sExtra=a;sExtra.cream.visited=1u<<25;sExtra.sum=sum_bytes(&sExtra,offsetof(ExtraRun,sum));CHECK(!extra_valid());
    sExtra=a;sExtra.gates[49]=0x80;sExtra.sum=sum_bytes(&sExtra,offsetof(ExtraRun,sum));CHECK(!extra_valid());
    sExtra=a;sExtra.inventory.bottles[0]=250;sExtra.sum=sum_bytes(&sExtra,offsetof(ExtraRun,sum));CHECK(!extra_valid());
    sExtra=a;sExtra.inventory.owned[3]=0xFFFFFFFFu;sExtra.sum=sum_bytes(&sExtra,offsetof(ExtraRun,sum));CHECK(!extra_valid());
    sExtra=a;sExtra.handoff.memory_length=7;sExtra.sum=sum_bytes(&sExtra,offsetof(ExtraRun,sum));CHECK(!extra_valid());
    sExtra=a;sExtra.handoff.difficulty=13;sExtra.sum=sum_bytes(&sExtra,offsetof(ExtraRun,sum));CHECK(!extra_valid());
    /* Every incomplete byte prefix of a replacement keeps the old matching
       record. The last magic byte alone publishes the next generation. */
    sExtra=a;b=a;b.generation++;b.cream.rewards=7;b.sum=sum_bytes(&b,offsetof(ExtraRun,sum));
    n=sizeof(b);slot=1;
    for(i=0;i<n+4;i++) {
        memset(ram+EX_BASE+slot*EX_SLOT_BYTES,0xA7,EX_SLOT_BYTES);
        publish_prefix(&b,EX_BASE+slot*EX_SLOT_BYTES,n,i);
        CHECK(find_extra(123)&&sExtra.cream.rewards==a.cream.rewards);
    }
    publish_prefix(&b,EX_BASE+slot*EX_SLOT_BYTES,n,n+4);CHECK(find_extra(123)&&sExtra.cream.rewards==7);
    /* Serial comparison crosses wrap for run and profile generations. */
    a.generation=0xFFFFFFFFu;a.sum=sum_bytes(&a,offsetof(ExtraRun,sum));b.generation=0;b.sum=sum_bytes(&b,offsetof(ExtraRun,sum));
    memcpy(ram+EX_BASE,&a,sizeof(a));memcpy(ram+EX_BASE+EX_SLOT_BYTES,&b,sizeof(b));
    CHECK(find_extra(123)&&sGeneration==0&&sSlot==1);
    read_record(&meta,PROFILE_BASE+sProfileSlot*PROFILE_BYTES,sizeof(meta));meta.generation=0xFFFFFFFFu;
    meta.sum=sum_bytes(&meta,offsetof(MetaRecord,sum));memcpy(ram+PROFILE_BASE,&meta,sizeof(meta));
    meta.generation=0;meta.meta[0]=55;meta.sum=sum_bytes(&meta,offsetof(MetaRecord,sum));
    memcpy(ram+PROFILE_BASE+PROFILE_BYTES,&meta,sizeof(meta));run_extension_init();
    CHECK(sProfileSlot==1&&sProfileGeneration==0&&((u8*)&gHandoffState)[0]==55);
    /* Profile writes are independently atomic and never erase the run. */
    meta.generation=1;meta.meta[0]=66;meta.sum=sum_bytes(&meta,offsetof(MetaRecord,sum));
    for(i=0;i<(int)sizeof(meta)+4;i++) {
        memset(ram+PROFILE_BASE,0xA7,PROFILE_BYTES);publish_prefix(&meta,PROFILE_BASE,sizeof(meta),i);run_extension_init();
        CHECK(((u8*)&gHandoffState)[0]==55);
    }
    publish_prefix(&meta,PROFILE_BASE,sizeof(meta),sizeof(meta)+4);run_extension_init();CHECK(((u8*)&gHandoffState)[0]==66);
    gHandoffState.wins=5;run_extension_erase();CHECK(!find_extra(123));run_extension_init();
    CHECK(gHandoffState.wins==5&&((u8*)&gHandoffState)[0]==66);guard_regions();
#endif
    printf("{\"functional_checks\":%d,\"protected_byte_checks\":%d,\"extra_bytes\":%zu,\"profile_bytes\":%zu}\n",checks,guards,sizeof(ExtraRun),sizeof(MetaRecord));return 0;
}
'''

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True);p.add_argument('--cc',default='cc');a=p.parse_args()
    out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True);src=out/'run-extension-host.c';src.write_text(fixture()+MAIN)
    results=[]
    for lab in (0,1):
        binary=out/f'run-extension-{lab}'
        command=[a.cc,'-std=gnu11','-O2',f'-DBART_ENEMY_LAB={lab}','-I',str(GAME/'src'),str(src),'-o',str(binary)]
        result=subprocess.run(command,capture_output=True,text=True);(out/f'compile-{lab}.log').write_text(result.stdout+result.stderr);result.check_returncode()
        result=subprocess.run([str(binary)],capture_output=True,text=True);(out/f'run-{lab}.log').write_text(result.stdout+result.stderr);result.check_returncode()
        record=dict(lab=lab,passed=True,**json.loads(result.stdout));results.append(record);print(record,flush=True)
    inputs=['src/run_extension.c','src/run_extension.h','src/cream_world.c','src/cream_world.h','src/cream_world_fallback.inc','src/legacy_items.h','src/handoff_events.h','src/cream_runtime.h','src/journal.h','src/util.c']
    report=dict(passed=True,method=__doc__,results=results,source_hashes={n:SHA((GAME/n).read_bytes()) for n in inputs},tool_sha256=SHA(Path(__file__).read_bytes()),compiled_source_sha256=SHA(src.read_bytes()))
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()

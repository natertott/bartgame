/* Versioned records outside the untouched v1/v2 Forest checkpoint. Two
   checksummed slots keep interruption during an SRAM write recoverable. */
#include "run_extension.h"
#include "legacy_items.h"
#include "handoff_events.h"
#include "cream_runtime.h"
#include "cream_room.h"
#include "regional_content.h"
#include "game.h"
#include "util.h"
#include "journal.h"
#include <stddef.h>
#define SRAM_BYTES ((volatile u8*)0x0e000000)
#define EX_MAGIC 0x58455243u
#define EX_VERSION RUN_EXTENSION_VERSION /* actual map anchors append after v2 */
#define EX_LEGACY_VERSION RUN_EXTENSION_LEGACY_VERSION
#define PROFILE_MAGIC 0x50485242u
#define EX_SLOT_BYTES RUN_EXTENSION_SLOT_BYTES
#define EX_BASE RUN_EXTENSION_SRAM_BASE
#define PROFILE_BASE RUN_PROFILE_SRAM_BASE
#define PROFILE_BYTES RUN_PROFILE_SLOT_BYTES
#define META_BYTES offsetof(HandoffState,food_mask)
typedef struct {
    u32 magic,generation,base_sum;
    u16 version,size;
    LegacyInventory inventory;
    CreamProgress cream;
    u8 gates[CC_NODES];
    HandoffState handoff;
    RegionalContentDiscovery discovery[RC_ROOMS];
    u32 sum;
} ExtraRun;
#define EX_LEGACY_BYTES (offsetof(ExtraRun,discovery)+sizeof(u32))
typedef struct {
    u32 magic,generation;
    u16 version,size;
    u8 meta[META_BYTES];
    u32 sum;
} MetaRecord;
typedef char ExtraFitsSlot[(sizeof(ExtraRun)<=EX_SLOT_BYTES)?1:-1];
typedef char ProfileFitsSlot[(sizeof(MetaRecord)<=PROFILE_BYTES)?1:-1];
typedef char ExtensionBeforeProfile[(EX_BASE+2*EX_SLOT_BYTES<=PROFILE_BASE)?1:-1];
typedef char ProfileBeforeJournal[(PROFILE_BASE+2*PROFILE_BYTES<=JOURNAL_SRAM_OFFSET)?1:-1];
typedef char StableMetaPrefix[(META_BYTES==16)?1:-1];
typedef char StablePublishedV2[(EX_LEGACY_BYTES==RUN_EXTENSION_LEGACY_BYTES)?1:-1];
static ExtraRun sExtra EWRAM_BSS;
static u32 sGeneration,sProfileGeneration;
static u8 sSlot,sProfileSlot,sProfileLoaded;
static u32 sum_bytes(const void* src,int n) {
    const u8* b=src;u32 sum=0x9e3779b9;int i;
    for(i=0;i<n;i++)sum=(sum^b[i])*16777619u;
    return sum;
}
static void read_record(void* dst,int offset,int n) {u8* p=dst;int i;for(i=0;i<n;i++)p[i]=SRAM_BYTES[offset+i];}
static void write_record(const void* src,int offset,int n) {const u8* p=src;int i;for(i=0;i<4;i++)SRAM_BYTES[offset+i]=0;for(i=4;i<n;i++)SRAM_BYTES[offset+i]=p[i];for(i=0;i<4;i++)SRAM_BYTES[offset+i]=p[i];}
/* Checksums protect accidental damage; these bounds also keep a valid but
   unsupported record away from actor, catalogue and puzzle array indices. */
static bool8 meta_valid(const u8* meta) {
    return meta[10]<=12 && meta[11]<=12 && meta[12]<=1 && meta[13]<=4;
}
static bool8 inventory_valid(const LegacyInventory* p) {
    int i;
    u32 tail=(1u<<(LI_COUNT-96))-1u;
    if ((p->owned[3]&~tail) || (p->seen[3]&~tail) || (p->skills&~0x0FFFu) ||
        p->sword_level>4 || p->bomb_bag>3 || p->quiver>3 ||
        p->dig_upgrade>1 || p->swim_upgrade>1 || p->bottle_charm>1) return FALSE;
    for (i=0;i<4;i++)
        if (p->bottles[i] && (p->bottles[i]<LI_BOTTLE_BUTTER || p->bottles[i]>LI_CHARM_DIN)) return FALSE;
    return TRUE;
}
static bool8 discovery_spot_valid(Spot p) {
    return (p.x==255&&p.y==255) || (p.x<32&&p.y<24);
}
static bool8 handoff_valid(const HandoffState* p,bool8 legacy) {
    int i;
    if (!meta_valid((const u8*)p) || (p->food_mask>>HF_COUNT) ||
        (p->charm_mask&~7u) || p->draft_round>3 || p->draft_state>HDRAFT_DONE ||
        (p->gold_owned&~15u) || (p->gold_fused&~15u) || (p->fusion_flags&~7u) ||
        p->contract_step>4 || p->contract_kind>HC_ITEM || p->contract_state>2 ||
        p->memory_length>6 || p->memory_known>1 ||
        p->quest.kind>HQ_BLOCKS || p->quest.state>4) return FALSE;
    if(legacy) {
        if(p->contract_target>=HS_COUNT)return FALSE;
    } else if(p->contract_state==1) {
        if(!p->contract_kind || p->contract_target<RC_FIELD_BASE ||
           p->contract_target>=RC_INTERIOR_BASE+46)return FALSE;
        if((p->contract_kind==HC_WAVE || p->contract_kind==HC_QUEST) &&
           p->contract_target>=RC_INTERIOR_BASE)return FALSE;
    } else if(p->contract_target && (p->contract_target<RC_FIELD_BASE ||
               p->contract_target>=RC_INTERIOR_BASE+46))return FALSE;
    if(p->quest.state==2) {
        const HandoffQuest* q=&p->quest;
        if(q->kind==HQ_NONE)return FALSE;
        if((q->origin_area==AREA_FOREST || q->origin_area==AREA_CREAM) && q->origin_cell>=25)return FALSE;
        if(q->origin_area!=AREA_FOREST && q->origin_area!=AREA_CREAM && q->origin_area!=AREA_HANDOFF)return FALSE;
        if(q->kind==HQ_COURIER && ((q->target_area!=AREA_FOREST && q->target_area!=AREA_CREAM) || q->target_cell>=25))return FALSE;
    }
    for (i=0;i<6;i++) if (p->memory_code[i]>3) return FALSE;
    for (i=0;i<3;i++) if (p->fuser_cell[i]>=25 || p->fuser_shape[i]>=3) return FALSE;
    return TRUE;
}
static bool8 extra_valid(void) {
    int i;
    bool8 legacy=sExtra.version==EX_LEGACY_VERSION;
    const CreamProgress* c=&sExtra.cream;
    if(sExtra.magic!=EX_MAGIC)return FALSE;
    if(legacy) {
        u32 old_sum;
        /* The old footer occupies the first four appended bytes. Reading
           through the existing EWRAM buffer avoids a second 1.4KB stack copy. */
        memcpy(&old_sum,sExtra.discovery,sizeof(old_sum));
        if(sExtra.size!=EX_LEGACY_BYTES || old_sum!=sum_bytes(&sExtra,offsetof(ExtraRun,discovery)))return FALSE;
    } else if(sExtra.version!=EX_VERSION || sExtra.size!=sizeof(sExtra) ||
              sExtra.sum!=sum_bytes(&sExtra,offsetof(ExtraRun,sum)))return FALSE;
    if (!inventory_valid(&sExtra.inventory) || !handoff_valid(&sExtra.handoff,legacy) ||
        c->node>=CC_NODES || (c->rewards&~7u) || c->boss_dead>1 || c->reserved ||
        (c->visited>>CC_ROOMS) || (c->chests[1]>>18) || (c->cleared[1]>>18) ||
        (c->healed[1]>>18)) return FALSE;
    for (i=0;i<CC_NODES;i++) if (sExtra.gates[i]&~((1u<<CC_EDGE_MAX)-1u)) return FALSE;
    if(!legacy)for(i=0;i<RC_ROOMS;i++) {
        const RegionalContentDiscovery* d=&sExtra.discovery[i];
        if((d->marks&~127u) || d->terrace>1)return FALSE;
        if(!discovery_spot_valid(d->door) || !discovery_spot_valid(d->npc) ||
           !discovery_spot_valid(d->mechanism) || !discovery_spot_valid(d->cache))return FALSE;
    }
    return TRUE;
}
static bool8 profile_valid(const MetaRecord* p) {
    return p->magic==PROFILE_MAGIC && p->version==1 && p->size==sizeof(*p) &&
           meta_valid(p->meta) && p->sum==sum_bytes(p,offsetof(MetaRecord,sum));
}
static bool8 find_extra(u32 base_sum) {
    int i,best=-1;u32 generation=0;
    for(i=0;i<2;i++) {read_record(&sExtra,EX_BASE+i*EX_SLOT_BYTES,sizeof(sExtra));if(extra_valid()&&sExtra.base_sum==base_sum&&(best<0||(s32)(sExtra.generation-generation)>0)){best=i;generation=sExtra.generation;}}
    if(best<0)return FALSE;
    read_record(&sExtra,EX_BASE+best*EX_SLOT_BYTES,sizeof(sExtra));sGeneration=generation;sSlot=best;return TRUE;
}
void run_extension_init(void) {
    MetaRecord record,best;
    int i;
    sGeneration=sProfileGeneration=0;sSlot=sProfileSlot=1;sProfileLoaded=FALSE;
    for(i=0;i<2;i++) {
        read_record(&record,PROFILE_BASE+i*PROFILE_BYTES,sizeof(record));
        if (profile_valid(&record) && (!sProfileLoaded || (s32)(record.generation-best.generation)>0)) {
            best=record;sProfileLoaded=TRUE;sProfileSlot=i;
        }
    }
    memset(&gHandoffState,0,META_BYTES);
    if (sProfileLoaded) {memcpy(&gHandoffState,best.meta,META_BYTES);sProfileGeneration=best.generation;}
}
void run_profile_write(void) {
#if !BART_ENEMY_LAB
    MetaRecord record;
    memset(&record,0,sizeof(record));record.magic=PROFILE_MAGIC;
    record.generation=sProfileGeneration+1;record.version=1;record.size=sizeof(record);
    memcpy(record.meta,&gHandoffState,META_BYTES);
    record.sum=sum_bytes(&record,offsetof(MetaRecord,sum));
    write_record(&record,PROFILE_BASE+(sProfileSlot^1)*PROFILE_BYTES,sizeof(record));
    sProfileSlot^=1;sProfileGeneration=record.generation;sProfileLoaded=TRUE;
#endif
}
void run_extension_write(u32 base_sum) {
#if !BART_ENEMY_LAB
    memset(&sExtra,0,sizeof(sExtra));sExtra.magic=EX_MAGIC;
    sExtra.generation=sGeneration+1;sExtra.base_sum=base_sum;
    sExtra.version=EX_VERSION;sExtra.size=sizeof(sExtra);sExtra.inventory=gLegacyInventory;
    sExtra.cream=gCreamProgress;memcpy(sExtra.gates,gCreamOpenEdges,sizeof(sExtra.gates));
    sExtra.handoff=gHandoffState;memcpy(sExtra.discovery,gRegionalDiscovery,sizeof(sExtra.discovery));
    sExtra.sum=sum_bytes(&sExtra,offsetof(ExtraRun,sum));
    write_record(&sExtra,EX_BASE+(sSlot^1)*EX_SLOT_BYTES,sizeof(sExtra));
    sSlot^=1;sGeneration=sExtra.generation;run_profile_write();
#else
    (void)base_sum;
#endif
}
bool8 run_extension_finished(u32 base_sum) {return find_extra(base_sum)&&sExtra.cream.boss_dead;}
static void seed_extension(u32 seed) {
    legacy_items_new_run();legacy_items_seed_owned();handoff_new_run(seed);cream_runtime_new_run(seed);
    regional_content_new_run();
    handoff_resume_regional(FALSE);
}
bool8 run_extension_load(u32 base_sum,u32 seed) {
    u8 meta[META_BYTES];
    if (!find_extra(base_sum) || sExtra.cream.seed!=hash32(seed,0x43524541u)) {
        seed_extension(seed);return FALSE;
    }
    /* Run state may predate the latest death, difficulty or entitlement
       preference. Those profile facts belong to the independent record. */
    memcpy(meta,&gHandoffState,META_BYTES);
    if (!cream_generate(sExtra.cream.seed)) {seed_extension(seed);return FALSE;}
    gLegacyInventory=sExtra.inventory;gCreamProgress=sExtra.cream;gHandoffState=sExtra.handoff;
    if (sProfileLoaded) memcpy(&gHandoffState,meta,META_BYTES);
    else run_profile_write(); /* Recover a lost profile from a complete run. */
    memcpy(gCreamOpenEdges,sExtra.gates,sizeof(sExtra.gates));
    gCreamNode=gCreamProgress.node;
    if(sExtra.version==EX_LEGACY_VERSION)regional_content_new_run();
    else memcpy(gRegionalDiscovery,sExtra.discovery,sizeof(sExtra.discovery));
    handoff_resume_regional(sExtra.version==EX_LEGACY_VERSION);
    return TRUE;
}
void run_extension_erase(void) {
#if !BART_ENEMY_LAB
    int slot,i;
    for(slot=0;slot<2;slot++)for(i=0;i<4;i++)SRAM_BYTES[EX_BASE+slot*EX_SLOT_BYTES+i]=0;
    run_profile_write();
#endif
}

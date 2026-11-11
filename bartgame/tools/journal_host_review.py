#!/usr/bin/env python3
"""Exercise the actual journal C against private SRAM, without building assets.

Linux and a host C compiler are required. Only #include directives are removed
from journal.c/h; their code is compiled intact with fixed-width game types,
the actual PlayerState declaration/enums and source-contract art identifiers.
This establishes storage/data behavior, not native artwork or emulator timing.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess

GAME = Path(__file__).resolve().parents[1]
SHA = lambda data: hashlib.sha256(data).hexdigest()


def without_includes(source):
    return re.sub(r'^\s*#include[^\n]*$', '', source, flags=re.M)


def literal_assignment(path, name):
    for statement in ast.parse(path.read_text()).body:
        if isinstance(statement, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in statement.targets):
            return ast.literal_eval(statement.value)
    raise ValueError((str(path), name))


def fixture():
    player = (GAME/'src/player.h').read_text()
    enemy = (GAME/'src/enemy.h').read_text()
    appearance = (GAME/'src/appearance.h').read_text()
    declarations = ['''#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <stdlib.h>
typedef uint8_t u8; typedef uint16_t u16; typedef uint32_t u32;
typedef int8_t s8; typedef int16_t s16; typedef int32_t s32; typedef u8 bool8;
#define TRUE 1
#define FALSE 0
''']
    declarations.extend(re.findall(r'enum\s*\{[^}]+\}\s*;', player))
    declarations.append(re.search(r'typedef struct\s*\{.*?\}\s*PlayerState;', player, re.S)[0])
    declarations.extend(re.findall(r'^#define\s+ITEM\w*[^\n]*', player, re.M))
    declarations.append(re.search(r'enum\s*\{[^}]+\}\s*;', enemy)[0])
    declarations.extend(re.findall(r'^#define\s+EN_PROTO\w*[^\n]*', enemy, re.M))
    declarations.append(re.search(r'^#define\s+APPEARANCE_SRAM_OFFSET[^\n]*', appearance, re.M)[0])
    # Source identifiers suffice for storage tests; exact live art metadata is
    # qualified separately against the generated ROM by the native review.
    contract = json.loads((GAME/'art/reboot_contracts.json').read_text())
    for sheet in contract['sheets']:
        name = sheet['name'].upper()
        declarations.append('#define SHEET_%s %d' % (name, sheet['id']))
        for index, frame in enumerate(sheet['frames']):
            declarations.append('#define F_%s_%s %d' % (name, frame.upper(), index))
    palettes = literal_assignment(GAME/'art/palettes.py', 'OBJ_ALIASES')
    for index, (name, _) in enumerate(palettes):
        declarations.append('#define PAL_OBJ_%s %d' % (name.upper(), index))
    prototype = GAME/'art/enemy_prototypes.py'
    poses = literal_assignment(prototype, 'POSES')
    faces = literal_assignment(prototype, 'FACES')
    for offset, (name, _, _, _) in enumerate(literal_assignment(prototype, 'SPECS')):
        declarations.append('#define SHEET_%s %d' % (name.upper(), 100+offset))
        for index, (pose, face) in enumerate((p, f) for p in poses for f in faces):
            declarations.append('#define F_%s_%s_%s %d' % (name.upper(), pose.upper(), face.upper(), index))
    # Actual appended definitions are included, not invented names/stats.
    # Only native sprite-address data is stubbed: storage/metadata tests do
    # not claim to validate generated pixels or emulator presentation.
    declarations.append('typedef struct Actor Actor;')
    declarations.extend(re.findall(r'^#define\s+AF_\w*[^\n]*', (GAME/'src/actor.h').read_text(), re.M))
    declarations.append(re.search(r'enum\s*\{\s*HB_HERO[^}]+\}\s*;', (GAME/'src/actor.h').read_text(), re.S)[0])
    declarations.append(re.search(r'typedef struct\s*\{.*?\}\s*EnemyDef;', enemy, re.S)[0])
    declarations.append(without_includes((GAME/'src/legacy_items.h').read_text()))
    declarations.append(without_includes((GAME/'src/legacy_enemies.h').read_text()))
    declarations.append(without_includes((GAME/'src/handoff_events.h').read_text()))
    declarations.append('HandoffState gHandoffState;')
    legacy_enemies = re.search(r'const LegacyEnemyDef gLegacyEnemyDefs\[.*?^};',
                              (GAME/'src/legacy_enemies.c').read_text(), re.M|re.S)[0]
    extra_sheets = sorted(set(re.findall(r'SHEET_\w+', legacy_enemies)) | {'SHEET_HANDOFF_ITEMS'})
    for index,name in enumerate(extra_sheets):
        declarations.append('#define %s %d'%(name,128+index))
    declarations.append('typedef struct {u8 pal;} SpriteSheet;')
    declarations.append('static const SpriteSheet sheets[256] = {[0 ... 255]={3}};')
    declarations.append((GAME/'src/legacy_items_metadata.inc').read_text())
    declarations.append(legacy_enemies)
    declarations.append('''static u8 known_owned[LI_COUNT],known_seen[LI_COUNT];
const LegacyItemDef* legacy_item_def(int id) {return id>0&&id<LI_COUNT?&gLegacyItemDefs[id]:NULL;}
const LegacyEnemyDef* legacy_enemy_def(int id) {return id>=LEGACY_ENEMY_BASE&&id<LEGACY_ENEMY_END?&gLegacyEnemyDefs[id-LEGACY_ENEMY_BASE]:NULL;}
bool8 legacy_item_owned(int id) {return id>0&&id<LI_COUNT&&known_owned[id];}
bool8 legacy_item_seen(int id) {return id>0&&id<LI_COUNT&&known_seen[id];}
''')
    declarations.append(without_includes((GAME/'src/journal.h').read_text()))
    declarations.append('extern PlayerState gPl;')
    declarations.append(without_includes((GAME/'src/journal.c').read_text()))
    return '\n'.join(declarations)


MAIN = r'''
PlayerState gPl;
static int checks,guard_checks;
#define CHECK(test) do {checks++;if (!(test)) {fprintf(stderr,"FAIL line%d: %s\n",__LINE__,#test);exit(1);}} while(0)
#define GUARD(test) do {guard_checks++;if (!(test)) {fprintf(stderr,"FAIL protected byte line%d\n",__LINE__);exit(1);}} while(0)
static u8 snapshot[32768],*ram;
static void fresh(void) {
    memset(ram,0xA7,32768);memset(&gPl,0,sizeof(gPl));memset(&gHandoffState,0,sizeof(gHandoffState));
    memset(known_owned,0,sizeof(known_owned));memset(known_seen,0,sizeof(known_seen));
    journal_init();
}
static void unchanged_outer(void) {
    int i;
    for(i=0;i<JOURNAL_SRAM_OFFSET;i++)GUARD(ram[i]==0xA7);
    for(i=JOURNAL_SRAM_END;i<32768;i++)GUARD(ram[i]==0xA7);
}
static void write_v1(int slot,u32 gen,u32 items,u16 enemies) {
    JournalRecordV1 r;
    memset(&r,0,sizeof(r));r.magic=JOURNAL_V1_MAGIC;r.version=1;r.size=sizeof(r);
    r.generation=gen;r.items=items;r.enemies=enemies;r.sum=checksum_bytes(&r,sizeof(r));
    memcpy(ram+JOURNAL_V1_SRAM_OFFSET+slot*JOURNAL_V1_SLOT_BYTES,&r,sizeof(r));
}
static void write_v2(int slot,u32 gen,int item,int enemy) {
    JournalRecord r;
    memset(&r,0,sizeof(r));r.magic=JOURNAL_MAGIC;r.version=JOURNAL_VERSION;r.size=sizeof(r);r.generation=gen;
    if(item>=0)r.items[item>>3]|=1u<<(item&7);
    if(enemy>=0)r.enemies[enemy>>3]|=1u<<(enemy&7);
    r.sum=journal_checksum(&r);memcpy(ram+JOURNAL_SRAM_OFFSET+slot*JOURNAL_SLOT_BYTES,&r,sizeof(r));
}
int main(void) {
    int i,j;
    JournalRecord rec;
    JournalEntry a,b,saved;
    ram=mmap((void*)0x0E000000u,32768,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);
    CHECK(ram!=(void*)-1);fresh();CHECK(!gJournalItems&&!gJournalEnemies);
    CHECK(journal_item_count()==146&&journal_enemy_count()==84);
    CHECK(sizeof(JournalRecord)==64&&sizeof(JournalRecordV1)==32);
    memcpy(snapshot,ram,32768);
    journal_note_item(-1);journal_note_item(JI_COUNT);journal_note_enemy(-1);journal_note_enemy(JOURNAL_ENEMY_COUNT);
    journal_note_legacy_item(-1);journal_note_legacy_item(LI_NONE);journal_note_legacy_item(LI_COUNT);journal_note_gold_half(-1);journal_note_gold_half(4);
    CHECK(!journal_items_found()&&!journal_enemies_found());CHECK(memcmp(snapshot,ram,32768)==0);
    journal_note_item(JI_SWORD);journal_note_enemy(EN_BOSS);
    journal_note_legacy_item(LI_COUNT-1);journal_note_enemy(JOURNAL_ENEMY_COUNT-1);
    CHECK(journal_item_seen(JI_LEGACY_BASE+LI_COUNT-1)&&journal_enemy_seen(JOURNAL_ENEMY_COUNT-1));
    CHECK(gJournalItems==1&&gJournalEnemies==(1u<<EN_BOSS));
    CHECK(journal_items_found()==2&&journal_enemies_found()==2);
    memcpy(snapshot,ram,32768);j=gJournalRevision;
    journal_note_item(JI_SWORD);journal_note_enemy(JOURNAL_ENEMY_COUNT-1);
    CHECK(gJournalRevision==j&&memcmp(snapshot,ram,32768)==0);
#if BART_ENEMY_LAB
    fresh();memcpy(snapshot,ram,32768);
    for(i=0;i<JI_COUNT;i++)journal_note_item(i);
    for(i=0;i<JOURNAL_ENEMY_COUNT;i++)journal_note_enemy(i);
    CHECK(journal_items_found()==JI_COUNT&&journal_enemies_found()==JOURNAL_ENEMY_COUNT);
    CHECK(memcmp(snapshot,ram,32768)==0);
    /* Legacy profile knowledge may load, but migration is RAM-only in a lab. */
    fresh();write_v1(0,10,0x800001u,0x101u);memcpy(snapshot,ram,32768);journal_init();
    CHECK(gJournalItems==0x800001u&&gJournalEnemies==0x101u);
    CHECK(memcmp(snapshot,ram,32768)==0);
#else
    journal_init();CHECK(journal_items_found()==2&&journal_enemies_found()==2);
    journal_note_item(JI_BOW);CHECK(journal_item_seen(JI_BOW));
    /* Corrupt the current checksum: the other complete generation survives. */
    ram[JOURNAL_SRAM_OFFSET+sCurrentSlot*JOURNAL_SLOT_BYTES+63]^=0x80;
    journal_init();CHECK(!journal_item_seen(JI_BOW)&&journal_item_seen(JI_SWORD));
    CHECK(journal_item_seen(JI_LEGACY_END-1)&&journal_enemy_seen(JOURNAL_ENEMY_COUNT-1));
    read_slot(&rec,sCurrentSlot);rec.generation++;rec.items[JI_CLOAK>>3]|=1u<<(JI_CLOAK&7);rec.sum=journal_checksum(&rec);
    memcpy(ram+JOURNAL_SRAM_OFFSET+(sCurrentSlot^1)*JOURNAL_SLOT_BYTES,&rec,sizeof(rec));
    ram[JOURNAL_SRAM_OFFSET+(sCurrentSlot^1)*JOURNAL_SLOT_BYTES]=0;
    journal_init();CHECK(journal_item_seen(JI_SWORD)&&!journal_item_seen(JI_CLOAK));
    unchanged_outer();
    /* Every original discovery survives v1 migration; its old records and
       independent appearance bytes stay byte-for-byte unchanged. */
    fresh();write_v1(0,10,1u,1u);write_v1(1,11,0xFFFFFFu,0x1FFu);
    memcpy(snapshot,ram,32768);journal_init();
    CHECK(gJournalItems==0xFFFFFFu&&gJournalEnemies==0x1FFu);
    CHECK(journal_items_found()==24&&journal_enemies_found()==9&&sGeneration==12);
    CHECK(memcmp(ram+JOURNAL_V1_SRAM_OFFSET,snapshot+JOURNAL_V1_SRAM_OFFSET,32768-JOURNAL_V1_SRAM_OFFSET)==0);
    for(i=0;i<JOURNAL_SRAM_OFFSET;i++)GUARD(ram[i]==snapshot[i]);
    journal_note_legacy_item(LI_PACCI_CANE);journal_note_enemy(JOURNAL_ENEMY_COUNT-1);journal_init();
    CHECK(journal_item_seen(JI_LEGACY_BASE+LI_PACCI_CANE)&&journal_enemy_seen(JOURNAL_ENEMY_COUNT-1));
    /* An interrupted first migration still has its complete v1 source. */
    ram[JOURNAL_SRAM_OFFSET]=ram[JOURNAL_SRAM_OFFSET+JOURNAL_SLOT_BYTES]=0;journal_init();
    CHECK(journal_items_found()==24&&journal_enemies_found()==9);
    /* A valid new profile takes precedence over stale v1, even when older. */
    write_v2(0,1,JI_COUNT-1,JOURNAL_ENEMY_COUNT-1);journal_init();
    CHECK(journal_items_found()==1&&journal_enemies_found()==1);
    CHECK(journal_item_seen(JI_COUNT-1)&&!journal_item_seen(JI_SWORD));
    /* Serial generation comparison crosses unsigned wrap. */
    fresh();write_v2(0,0xFFFFFFFFu,JI_SWORD,EN_BEETLE);write_v2(1,0,JI_SHIELD,EN_BOSS);journal_init();
    CHECK(sCurrentSlot==1&&sGeneration==0&&journal_item_seen(JI_SHIELD)&&!journal_item_seen(JI_SWORD));
    /* Unsupported upper bits and nonzero reserved bytes reject even if the
       checksum is internally consistent. */
    read_slot(&rec,1);rec.items[JOURNAL_ITEM_BYTES-1]|=0x80;rec.sum=journal_checksum(&rec);CHECK(!valid_slot(&rec));
    read_slot(&rec,1);rec.enemies[JOURNAL_ENEMY_BYTES-1]|=0x80;rec.sum=journal_checksum(&rec);CHECK(!valid_slot(&rec));
    read_slot(&rec,1);rec.reserved[15]=1;rec.sum=journal_checksum(&rec);CHECK(!valid_slot(&rec));
    /* Validate all64 possible interrupted prefixes of a new-generation
       publication: before the final magic is complete, old wins. */
    for(j=0;j<68;j++) {
        int pos=0,slot;
        fresh();journal_note_item(JI_SWORD);slot=sCurrentSlot^1;
        read_slot(&rec,sCurrentSlot);rec.generation++;rec.items[JI_CLOAK>>3]|=1u<<(JI_CLOAK&7);rec.sum=journal_checksum(&rec);
        for(i=0;i<4&&pos<j;i++,pos++)ram[JOURNAL_SRAM_OFFSET+slot*64+i]=0;
        for(i=4;i<64&&pos<j;i++,pos++)ram[JOURNAL_SRAM_OFFSET+slot*64+i]=((u8*)&rec)[i];
        for(i=0;i<4&&pos<j;i++,pos++)ram[JOURNAL_SRAM_OFFSET+slot*64+i]=((u8*)&rec)[i];
        journal_init();CHECK(journal_item_seen(JI_SWORD)&&!journal_item_seen(JI_CLOAK));
    }
    fresh();
    for(i=0;i<JI_COUNT;i++)journal_note_item(i);
    for(i=0;i<JOURNAL_ENEMY_COUNT;i++)journal_note_enemy(i);
    CHECK(gJournalItems==0xFFFFFFFFu&&gJournalEnemies==0xFFFFu);
    CHECK(journal_items_found()==JI_COUNT&&journal_enemies_found()==JOURNAL_ENEMY_COUNT);journal_init();
    CHECK(journal_items_found()==JI_COUNT&&journal_enemies_found()==JOURNAL_ENEMY_COUNT);unchanged_outer();
#endif
    /* All metadata is actual production metadata, copied to independent
       storage: querying six list rows cannot alter the selected entry. */
    CHECK(!journal_entry(-1,0,&a)&&!journal_entry(2,0,&a)&&!journal_entry(0,-1,&a)&&!journal_entry(0,JI_COUNT,&a));
    CHECK(!journal_entry(1,JOURNAL_ENEMY_COUNT,&a)&&!journal_entry(0,0,NULL));
    for(i=0;i<JI_COUNT;i++) {
        CHECK(journal_entry(0,i,&a)&&a.name&&a.name[0]&&a.description&&a.description[0]);saved=a;
        for(j=0;j<6;j++)CHECK(journal_entry(1,j,&b));
        CHECK(memcmp(&a,&saved,sizeof(a))==0);
        if(i<JI_BASE_COUNT)CHECK(journal_item_entry(i)&&strcmp(journal_item_entry(i)->name,a.name)==0);
        else CHECK(a.sheet==SHEET_HANDOFF_ITEMS&&a.frame==i-JI_LEGACY_BASE);
    }
    for(i=0;i<JOURNAL_ENEMY_COUNT;i++) {
        CHECK(journal_entry(1,i,&a)&&a.name&&a.name[0]&&a.description&&a.description[0]&&a.hp&&a.damage);
        if(i>=JOURNAL_BASE_ENEMY_COUNT)CHECK(a.frame==2&&a.sheet==legacy_enemy_def(i)->base.sheet);
    }
    CHECK(journal_item_entry(-1)==NULL&&journal_item_entry(JI_BASE_COUNT)==NULL);
    CHECK(journal_enemy_entry(-1)==NULL&&journal_enemy_entry(JOURNAL_BASE_ENEMY_COUNT)==NULL);
    CHECK(journal_entry(1,LE_MADDERPILLAR_0,&a)&&a.hp==32);
    CHECK(journal_entry(1,LE_BIG_OCTOROK,&a)&&a.hp==15);
    CHECK(journal_entry(1,LE_BOBOMB_0,&a)&&a.hp==255);
    CHECK(journal_entry(0,JI_LAMP,&a)&&strstr(a.description,"mummy"));
    CHECK(!journal_item_seen(-1)&&!journal_item_seen(JI_COUNT)&&!journal_enemy_seen(-1)&&!journal_enemy_seen(JOURNAL_ENEMY_COUNT));
    fresh();journal_note_gold_half(3);CHECK(journal_item_seen(JI_GOLD_RIGHT)&&journal_items_found()==1);
    fresh();gHandoffState.gold_owned=15;journal_note_owned();CHECK(journal_items_found()==4&&journal_item_seen(JI_GOLD_MIDDLE));
    fresh();gPl.items=0x7F;gPl.items2=0x1F;gPl.keys=1;gPl.gilt=12;gPl.bombs=30;gPl.arrows=50;gPl.hearts_pieces=2;
    known_owned[LI_GUST_JAR]=1;known_seen[LI_PACCI_CANE]=1;journal_note_owned();
    CHECK(journal_items_found()==18&&journal_item_seen(JI_LEGACY_BASE+LI_GUST_JAR)&&journal_item_seen(JI_LEGACY_BASE+LI_PACCI_CANE));
    CHECK(!journal_item_seen(JI_HEART_CONTAINER)&&!journal_item_seen(JI_ARROW5)&&!journal_item_seen(JI_BOMB_PICKUP));
    fresh();for(i=0;i<10;i++)journal_note_pickup(i);CHECK(journal_items_found()==10&&journal_item_seen(JI_GRAIL));
    fresh();for(i=0;i<17;i++)journal_note_icon(i);CHECK(journal_items_found()==16&&!journal_item_seen(JI_HEART));
    fresh();journal_note_shop_icon(F_ITEMS_HEART);journal_note_shop_icon(F_ITEMS_BOMBS);journal_note_shop_icon(F_ITEMS_ARROW10);
    CHECK(journal_items_found()==3&&journal_item_seen(JI_HEALING_PETAL)&&journal_item_seen(JI_ARROW10));
    /* Visible ordinals preserve original order and stable rawIDs, excluding
       only source helpers; raw discovery counts remain backwards compatible. */
    fresh();CHECK(journal_list_count(-1)==0&&journal_list_count(2)==0&&journal_list_found(2)==0);
    CHECK(journal_list_id(-1,0)==-1&&journal_list_id(0,-1)==-1&&journal_list_id(1,JOURNAL_ENEMY_COUNT)==-1);
    {int visible=journal_list_count(0),previous=-1;
     CHECK(visible<JI_COUNT&&visible>JI_BASE_COUNT&&journal_list_count(1)==JOURNAL_ENEMY_COUNT);
     for(i=0;i<visible;i++) {
      int raw=journal_list_id(0,i);CHECK(raw>previous&&raw<JI_COUNT);previous=raw;
      if(i<JI_BASE_COUNT)CHECK(raw==i);
      if(raw>=JI_LEGACY_BASE&&raw<JI_LEGACY_END)CHECK(!(gLegacyItemDefs[raw-JI_LEGACY_BASE].flags&LIF_HIDDEN));
      journal_note_item(raw);
     }
     CHECK(journal_list_id(0,visible)==-1&&previous==JI_GOLD_RIGHT);
     CHECK(journal_list_found(0)==visible&&journal_items_found()==visible);
     for(i=0;i<JI_COUNT;i++)journal_note_item(i);
     CHECK(journal_items_found()==JI_COUNT&&journal_list_found(0)==visible);
     for(i=0;i<JOURNAL_ENEMY_COUNT;i++) {CHECK(journal_list_id(1,i)==i);journal_note_enemy(i);}
     CHECK(journal_list_found(1)==JOURNAL_ENEMY_COUNT);
    }
    printf("{\"functional_checks\":%d,\"protected_byte_checks\":%d}\n",checks,guard_checks);return 0;
}
'''


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',required=True)
    p.add_argument('--cc',default='cc')
    args=p.parse_args();out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=True)
    source=fixture()+MAIN
    cfile=out/'journal-host.c';cfile.write_text(source)
    results=[]
    for lab in (0,1):
        binary=out/('journal-host-%d'%lab)
        command=[args.cc,'-std=gnu11','-O2','-DBART_ENEMY_LAB=%d'%lab,str(cfile),'-o',str(binary)]
        compiled=subprocess.run(command,capture_output=True,text=True)
        (out/('compile-%d.log'%lab)).write_text(compiled.stdout+compiled.stderr)
        if compiled.returncode:
            raise RuntimeError('Compilation failed: '+str(out/('compile-%d.log'%lab)))
        result=subprocess.run([str(binary)],capture_output=True,text=True)
        (out/('run-%d.log'%lab)).write_text(result.stdout+result.stderr)
        result.check_returncode();counts=json.loads(result.stdout)
        row=dict(BART_ENEMY_LAB=lab,passed=True,command=command,**counts)
        results.append(row);print(row,flush=True)
    inputs=['src/journal.c','src/journal.h','src/player.h','src/enemy.h','src/appearance.h',
            'art/reboot_contracts.json','art/palettes.py','art/enemy_prototypes.py',
            'src/legacy_items.h','src/legacy_items_metadata.inc','src/legacy_enemies.h','src/legacy_enemies.c','src/handoff_events.h']
    report=dict(method=__doc__,passed=all(r['passed'] for r in results),results=results,
                source_hashes={n:SHA((GAME/n).read_bytes()) for n in inputs},
                compiled_source_sha256=SHA(cfile.read_bytes()),tool_sha256=SHA(Path(__file__).read_bytes()),
                limits='Private Linux SRAM simulation; no emulator or real cartridge write/power-loss claim. Art identifiers derive from contracts; native previews need separate ROM verification.')
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    return 0


if __name__=='__main__':raise SystemExit(main())

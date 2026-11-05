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
    declarations.append(without_includes((GAME/'src/journal.h').read_text()))
    declarations.append('extern PlayerState gPl;')
    declarations.append(without_includes((GAME/'src/journal.c').read_text()))
    return '\n'.join(declarations)


MAIN = r'''
PlayerState gPl;
static int checks, guard_checks;
#define CHECK(test) do {checks++;if (!(test)) {fprintf(stderr,"FAIL line%d: %s\n",__LINE__,#test);exit(1);}} while(0)
#define GUARD(test) do {guard_checks++;if (!(test)) {fprintf(stderr,"FAIL protected byte line%d\n",__LINE__);exit(1);}} while(0)
static unsigned char snapshot[32768];
static unsigned char* ram;
static void fresh(void) {memset(ram,0xA7,32768);memset(&gPl,0,sizeof(gPl));journal_init();}
static void unchanged_outer(void) {
    int i;
    for(i=0;i<JOURNAL_SRAM_OFFSET;i++)GUARD(ram[i]==0xA7);
    for(i=JOURNAL_SRAM_END;i<32768;i++)GUARD(ram[i]==0xA7);
}
int main(void) {
    int i;
    JournalRecord rec;
    ram=mmap((void*)0x0E000000u,32768,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);
    CHECK(ram!=(void*)-1);fresh();CHECK(!gJournalItems&&!gJournalEnemies);
    CHECK(journal_item_count()==24&&journal_enemy_count()==9);
#if BART_ENEMY_LAB
    memcpy(snapshot,ram,32768);
    for(i=0;i<24;i++)journal_note_item(i);
    for(i=0;i<9;i++)journal_note_enemy(i);
    CHECK(gJournalItems==0xFFFFFFu&&gJournalEnemies==0x1FF);
    CHECK(journal_items_found()==24&&journal_enemies_found()==9);
    CHECK(memcmp(snapshot,ram,32768)==0);
    /* Profile knowledge may load in the lab; new fixture discoveries stay RAM-only. */
    memset(&rec,0,sizeof(rec));rec.magic=JOURNAL_MAGIC;rec.version=JOURNAL_VERSION;rec.size=sizeof(rec);
    rec.items=1u<<JI_SWORD;rec.enemies=1u<<EN_BOSS;rec.sum=journal_checksum(&rec);
    memcpy(ram+JOURNAL_SRAM_OFFSET,&rec,sizeof(rec));memcpy(snapshot,ram,32768);
    journal_init();CHECK(journal_item_seen(JI_SWORD)&&journal_enemy_seen(EN_BOSS));
    journal_note_item(JI_SHIELD);journal_note_enemy(EN_GILT_LEECH);
    CHECK(journal_items_found()==2&&journal_enemies_found()==2);
    CHECK(memcmp(snapshot,ram,32768)==0);
#else
    memcpy(snapshot,ram,32768);journal_note_item(-1);journal_note_item(24);journal_note_enemy(-1);journal_note_enemy(9);
    CHECK(memcmp(snapshot,ram,32768)==0);
    journal_note_item(JI_SWORD);CHECK(journal_item_seen(JI_SWORD));CHECK(journal_items_found()==1);CHECK(sGeneration==1);
    memcpy(snapshot,ram,32768);journal_note_item(JI_SWORD);CHECK(memcmp(snapshot,ram,32768)==0);CHECK(sGeneration==1);
    journal_note_enemy(EN_BOSS);CHECK(journal_enemy_seen(EN_BOSS));CHECK(journal_enemies_found()==1);
    gJournalItems=gJournalEnemies=0;journal_init();CHECK(journal_item_seen(JI_SWORD)&&journal_enemy_seen(EN_BOSS));
    journal_note_item(JI_BOW);CHECK(journal_item_seen(JI_BOW));
    /* Latest checksum corruption falls back to the other complete generation. */
    ram[JOURNAL_SRAM_OFFSET+sCurrentSlot*JOURNAL_SLOT_BYTES+31]^=0x80;
    journal_init();CHECK(journal_item_seen(JI_SWORD)&&journal_enemy_seen(EN_BOSS));CHECK(!journal_item_seen(JI_BOW));
    /* A partially published target cannot replace a valid old generation. */
    read_slot(&rec,sCurrentSlot);rec.generation++;rec.items|=1u<<JI_CLOAK;rec.sum=journal_checksum(&rec);
    memcpy(ram+JOURNAL_SRAM_OFFSET+(sCurrentSlot^1)*JOURNAL_SLOT_BYTES,&rec,sizeof(rec));
    ram[JOURNAL_SRAM_OFFSET+(sCurrentSlot^1)*JOURNAL_SLOT_BYTES]=0;
    journal_init();CHECK(journal_item_seen(JI_SWORD)&&!journal_item_seen(JI_CLOAK));
    ram[JOURNAL_SRAM_OFFSET]=ram[JOURNAL_SRAM_OFFSET+JOURNAL_SLOT_BYTES]=0;
    memcpy(snapshot,ram,32768);journal_init();CHECK(!gJournalItems&&!gJournalEnemies);CHECK(memcmp(snapshot,ram,32768)==0);
    for(i=0;i<24;i++)journal_note_item(i);
    for(i=0;i<9;i++)journal_note_enemy(i);
    CHECK(gJournalItems==0xFFFFFFu&&gJournalEnemies==0x1FF);CHECK(journal_items_found()==24&&journal_enemies_found()==9);
    for(i=0;i<24;i++) {const JournalEntry* e=journal_item_entry(i);CHECK(e&&e->name[0]&&e->description[0]);CHECK(journal_item_seen(i));CHECK(strlen(e->description)<=160);}
    for(i=0;i<9;i++) {const JournalEntry* e=journal_enemy_entry(i);CHECK(e&&e->name[0]&&e->description[0]);CHECK(journal_enemy_seen(i));CHECK(e->hp&&e->damage);}
    CHECK(journal_item_entry(-1)==NULL&&journal_item_entry(24)==NULL&&journal_enemy_entry(-1)==NULL&&journal_enemy_entry(9)==NULL);
    CHECK(!journal_item_seen(-1)&&!journal_item_seen(24)&&!journal_enemy_seen(-1)&&!journal_enemy_seen(9));
    unchanged_outer();
    fresh();gPl.items=0x7F;gPl.items2=0x1F;gPl.keys=1;gPl.gilt=12;gPl.bombs=30;gPl.arrows=50;gPl.hearts_pieces=2;journal_note_owned();
    CHECK(journal_items_found()==16);CHECK(!journal_item_seen(JI_HEART_CONTAINER));CHECK(!journal_item_seen(JI_ARROW5)&&!journal_item_seen(JI_ARROW10));CHECK(!journal_item_seen(JI_BOMB_PICKUP)&&!journal_item_seen(JI_HEALING_PETAL));
    fresh();for(i=0;i<10;i++)journal_note_pickup(i);CHECK(journal_items_found()==10);CHECK(journal_item_seen(JI_BOMB_PICKUP)&&journal_item_seen(JI_GRAIL));
    fresh();for(i=0;i<17;i++)journal_note_icon(i);CHECK(journal_items_found()==16);CHECK(!journal_item_seen(JI_HEART)&&!journal_item_seen(JI_GILT));
    fresh();journal_note_shop_icon(F_ITEMS_HEART);journal_note_shop_icon(F_ITEMS_BOMBS);journal_note_shop_icon(F_ITEMS_ARROW10);CHECK(journal_items_found()==3);CHECK(journal_item_seen(JI_HEALING_PETAL)&&journal_item_seen(JI_ARROW10));
    unchanged_outer();
    fresh();memset(&rec,0,sizeof(rec));rec.magic=JOURNAL_MAGIC;rec.version=JOURNAL_VERSION;rec.size=sizeof(rec);rec.generation=0xFFFFFFFFu;rec.items=1u<<JI_SWORD;rec.sum=journal_checksum(&rec);memcpy(ram+JOURNAL_SRAM_OFFSET,&rec,sizeof(rec));
    rec.generation=0;rec.items|=1u<<JI_SHIELD;rec.sum=journal_checksum(&rec);memcpy(ram+JOURNAL_SRAM_OFFSET+JOURNAL_SLOT_BYTES,&rec,sizeof(rec));journal_init();CHECK(journal_items_found()==2&&sCurrentSlot==1&&sGeneration==0);
#endif
    printf("{\"functional_checks\":%d,\"protected_byte_checks\":%d}\n",checks,guard_checks);
    return 0;
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
            'art/reboot_contracts.json','art/palettes.py','art/enemy_prototypes.py']
    report=dict(method=__doc__,passed=all(r['passed'] for r in results),results=results,
                source_hashes={n:SHA((GAME/n).read_bytes()) for n in inputs},
                compiled_source_sha256=SHA(cfile.read_bytes()),tool_sha256=SHA(Path(__file__).read_bytes()),
                limits='Private Linux SRAM simulation; no emulator or real cartridge write/power-loss claim. Art identifiers derive from contracts; native previews need separate ROM verification.')
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    return 0


if __name__=='__main__':raise SystemExit(main())

#!/usr/bin/env python3
"""Differential test of the unlit-torch cache through actual room write APIs.

The original/candidate room mutation and torch-count C functions are compiled
against native ROM metadata. Video/forest/interactive rendering is stubbed,
while room geometry, collision rebuilding and barrier-substrate selection use
the extracted C. Preview-details uses its actual save/restore function with a
disclosed deterministic generator stub that calls the real room write APIs.
No generator, game, art or ARM build is changed by this test.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

from sewer_concept_audit import NativeRom

GAME = Path(__file__).resolve().parents[1]
REPO = GAME.parent
BASELINE = '11b872e9897320398fa02344cef1418733c04e9a'


def extract(source, name):
    match = re.search(r'^(?:static )?(?:void|bool8|int|u8|u16) '+name+r'\([^;]*?\)\s*\{', source, re.M)
    assert match, name
    pos = match.end()
    depth = 1
    while depth:
        depth += (source[pos] == '{')-(source[pos] == '}')
        pos += 1
    return source[match.start():pos]


def read_source(rev, name):
    if rev == 'WORKTREE':
        return (GAME/'src'/name).read_text()
    return subprocess.check_output(['git', 'show', rev+':bartgame/src/'+name], cwd=REPO, text=True)


def run(before_source=BASELINE, after_source='WORKTREE', bundle='/workspace/setup/performance/before/bundle'):
    native = NativeRom(bundle)
    names = ('room_get', 'room_get_overlay', 'room_type', 'solid_cell_update',
             'room_build_solid', 'barrier_floor', 'room_clear', 'room_set',
             'room_set_overlay', 'room_change', 'room_change_overlay',
             'room_render', 'room_load_def', 'room_torches_unlit', 'room_torch_light',
             'roomgen_preview_details', 'roomgen_build_internal')
    state = ('gRoom', 'gRoomRevision', 'gRoomTorchesDirty', 'sUnlitTorches',
             'gWorld', 'gSpots', 'sR', 'sMask', 'sPath', 'sPreviewRoom',
             'gForestCohesionInfo')
    sources = {}
    c = ['''#include <stdio.h>
#undef NULL
#include "room.h"
#include "world.h"
#include "roomgen.h"
#include "react.h"
#include "game.h"
#include "objects.h"
#include "sound.h"
#define SB_OVERLAY 24
#define SB_GROUND 28
static u16 fixture_maps[32*1024];
static u16 fixture_display;
#undef SCREENBLOCK
#define SCREENBLOCK(n) (fixture_maps+(n)*1024)
#undef REG_DISPCNT
#define REG_DISPCNT fixture_display
static void fixture_dma(u32 value,volatile void* dst,u32 bytes) {(void)value;(void)dst;(void)bytes;}
#define dma3_fill32 fixture_dma
static void* fixture_memcpy(void* dst,const void* src,u32 n) {u8* d=dst;const u8* s=src;while(n--)*d++=*s++;return dst;}
static void* fixture_memset(void* dst,int value,u32 n) {u8* d=dst;while(n--)*d++=(u8)value;return dst;}
#define memcpy fixture_memcpy
#define memset fixture_memset
GameState gGame;
static int fixture_forest;
static void render_cell(int x,int y) {(void)x;(void)y;}
static void interactive_cell_changed(int x,int y) {(void)x;(void)y;}
static void forest_trees_apply_cell(int x,int y) {(void)x;(void)y;}
static void forest_trees_plan(void) {}
static void forest_trees_render(void) {}
static bool8 forest_trees_active(void) {return fixture_forest;}
static u16 forest_trees_video(u16 flags) {return flags;}
bool8 roomgen_blighted(int cell) {return (cell&1)!=0;}
static u16 myst_ground(int x,int y) {return MT_CAVE_FLOOR1+(x+y)%3;}
Actor* fx_spawn(int type,int x,int y) {(void)type;(void)x;(void)y;return 0;}
void sfx_play(int id) {(void)id;}
''']
    for array in ('metatile_type', 'metatile_prop', 'metatile_coll'):
        data = native.array(array)
        c.append('const u8 %s[%d]={%s};' % (array, len(data), ','.join(map(str, data))))
    generator = '''static void roomgen_build_internal(int cell,bool8 render) {
    int i;
    room_clear(5+cell%28,3+(cell*7)%30,MT_MOSS0);
    for(i=0;i<30;i++)room_set(i%gRoom.w,(i*3)%gRoom.h,(i&1)?MT_TORCH:MT_TORCH_LIT);
    for(i=0;i<MP_COUNT*2;i++)gWorld.mark[cell][i]=cell+i;
    gSpots.spawn_count=cell+1;sR.s+=cell+123;
    gForestCohesionInfo[0]=cell+9;sMask[0][0]=cell;sPath[0][0]=cell+1;
    if(render)room_render();
}'''
    for prefix, revision in [('before', before_source), ('after', after_source)]:
        source = {name: read_source(revision, name) for name in ('room.c', 'react.c', 'roomgen.c')}
        sources[prefix] = source
        mapping = {name: prefix+'_'+name for name in names+state}
        pattern = re.compile(r'\b('+'|'.join(mapping)+r')\b')

        def rename(text):
            return pattern.sub(lambda m: mapping[m.group(1)], text)

        c.append(rename('''Room gRoom,sPreviewRoom;
World gWorld;
RoomSpots gSpots;
Rng sR;
u8 sMask[24][32],sPath[24][32];
u16 gForestCohesionInfo[16];
u8 gRoomTorchesDirty=1;
u32 gRoomRevision;
static s16 sUnlitTorches;
'''))
        c.append('static unsigned '+prefix+'_type_calls;')
        blocks = []
        for name in names:
            if name == 'roomgen_build_internal':
                block = generator
            else:
                filename = 'react.c' if name in ('room_torches_unlit','room_torch_light') else 'roomgen.c' if name == 'roomgen_preview_details' else 'room.c'
                block = extract(source[filename], name)
            block = rename(block)
            if name == 'room_type':
                block = block.replace(prefix+'_room_type(', prefix+'_room_type_raw(', 1)
                blocks.append(block)
                blocks.append('u8 %s_room_type(int x,int y) {%s_type_calls++;return %s_room_type_raw(x,y);}' % (prefix, prefix, prefix))
            else:
                blocks.append(block)
        for block in blocks:
            c.append(block[:block.index('{')].strip()+';')
        c.extend(blocks)
    c.append('''
static unsigned seed=0x789b4a7u,cases,checks,cache_hits,scan_calls,preview_cases,invalid_writes,torch_transitions;
static unsigned rnd(void) {seed^=seed<<13;seed^=seed>>17;seed^=seed<<5;return seed;}
static int same(const void* a,const void* b,unsigned n) {const u8* x=a;const u8* y=b;while(n--)if(*x++!=*y++)return 0;return 1;}
static void must(int ok,const char* why) {checks++;if(!ok){printf("FAIL case%u %s\\n",cases,why);__builtin_trap();}}
static unsigned raw_count(void) {
    unsigned x,y,n=0;
    for(y=0;y<after_gRoom.h;y++)for(x=0;x<after_gRoom.w;x++) {
        u16 mt=after_gRoom.ground[y*32+x];
        if(mt!=MT_NONE && metatile_type[mt]==TT_TORCH)n++;
    }
    return n;
}
static void verify(int expect_dirty) {
    int n,i,b,a;unsigned calls;
    must(same(&before_gRoom,&after_gRoom,sizeof(Room)),"logical room byte mismatch");
    if(expect_dirty)must(after_gRoomTorchesDirty==1,"room mutation did not invalidate torch cache");
    n=raw_count();calls=after_type_calls;
    b=before_room_torches_unlit();a=after_room_torches_unlit();
    must(a==n && b==n,"cached count differs from raw/original scan");
    if(expect_dirty)must(after_type_calls-calls==after_gRoom.w*after_gRoom.h,"dirty count did not scan actual dimensions");
    must(after_gRoomTorchesDirty==0,"query did not clear dirty flag");
    for(i=0;i<7;i++) {
        calls=after_type_calls;
        b=before_room_torches_unlit();a=after_room_torches_unlit();
        must(a==n && b==n,"repeated cached count differs");
        must(after_type_calls==calls,"unchanged room rescanned");cache_hits++;
    }
    must(same(&before_gRoom,&after_gRoom,sizeof(Room)),"query modified room");
    scan_calls=after_type_calls;cases++;
}
static void clear_case(int w,int h,u16 mt) {before_room_clear(w,h,mt);after_room_clear(w,h,mt);verify(1);}
static void mutate(int op,int x,int y,u16 mt) {
    if(x<0||y<0||x>=after_gRoom.w||y>=after_gRoom.h)invalid_writes++;
    switch(op) {
    case 0:before_room_set(x,y,mt);after_room_set(x,y,mt);break;
    case 1:before_room_set_overlay(x,y,mt);after_room_set_overlay(x,y,mt);break;
    case 2:before_room_change(x,y,mt);after_room_change(x,y,mt);break;
    default:before_room_change_overlay(x,y,mt);after_room_change_overlay(x,y,mt);break;
    }
    verify(1);
}
int main(void) {
    static u16 ground[1024],overlay[1024];
    static const u16 fixtures[]={MT_NONE,MT_MOSS0,MT_PATH,MT_TORCH,MT_TORCH_LIT,MT_THORN,MT_CRACK,MT_WEB,MT_DOOR_LOCKED,MT_DOOR_OPEN,MT_BUSH,MT_BOULDER};
    int i,j,x,y,w,h,op;u16 mt;
    for(w=1;w<=32;w+=w<8?1:4)for(h=1;h<=32;h+=h<8?1:4)for(j=0;j<3;j++)
        clear_case(w,h,j==0?MT_MOSS0:j==1?MT_TORCH:MT_NONE);
    clear_case(32,32,MT_TORCH);must(after_room_torches_unlit()==1024,"full room torch count truncated");
    for(i=0;i<80;i++) {
        w=1+rnd()%32;h=1+rnd()%32;
        for(j=0;j<w*h;j++){ground[j]=fixtures[rnd()%12];overlay[j]=fixtures[rnd()%12];}
        RoomDef def={w,h,ground,(i&1)?overlay:0,0,0};
        before_room_load_def(&def);after_room_load_def(&def);verify(1);
        before_room_render();after_room_render();verify(1);
    }
    clear_case(32,24,MT_MOSS0);
    for(i=0;i<12000;i++) {
        if(i%127==0)clear_case(1+rnd()%32,1+rnd()%32,fixtures[rnd()%12]);
        gGame.area=rnd()%3;gGame.cell=rnd()%25;fixture_forest=gGame.area==1;
        op=rnd()%4;x=(int)(rnd()%(after_gRoom.w+6))-3;y=(int)(rnd()%(after_gRoom.h+6))-3;
        mt=(i%7==0)?rnd()%METATILE_COUNT:fixtures[rnd()%12];
        mutate(op,x,y,mt);
    }
    clear_case(7,6,MT_MOSS0);
    for(i=0;i<42;i++) {
        x=i%7;y=i/7;
        mutate(0,x,y,MT_TORCH);
        before_room_torch_light(x,y);after_room_torch_light(x,y);verify(1);torch_transitions++;
    }
    for(i=-2;i<27;i++) {
        u8 before_marks[MP_COUNT*2],after_marks[MP_COUNT*2];
        const u8 *bm=(const u8*)1,*bp=(const u8*)1,*am=(const u8*)1,*ap=(const u8*)1;
        Room snapshot=after_gRoom;
        before_gWorld=after_gWorld;before_gSpots=after_gSpots;before_sR=after_sR;
        before_roomgen_preview_details(i,before_marks,&bm,&bp);
        after_roomgen_preview_details(i,after_marks,&am,&ap);
        must(same(&snapshot,&after_gRoom,sizeof(Room)),"preview changed live room");
        must(same(before_marks,after_marks,sizeof(before_marks)),"preview marks changed");
        must(same(&before_gWorld,&after_gWorld,sizeof(World)),"preview changed world restore");
        must(same(&before_gSpots,&after_gSpots,sizeof(RoomSpots)),"preview changed spots restore");
        must(same(&before_sR,&after_sR,sizeof(Rng)),"preview changed RNG restore");
        must((bm==0)==(am==0) && (bp==0)==(ap==0),"preview pointer validity changed");
        verify(i>=0 && i<CELLS);preview_cases++;
    }
    printf("{\\"passed\\":true,\\"cases\\":%u,\\"checks\\":%u,\\"cache_hits\\":%u,\\"room_type_calls\\":%u,\\"preview_cases\\":%u,\\"invalid_coordinate_writes\\":%u,\\"torch_lit_transitions\\":%u}\\n",cases,checks,cache_hits,scan_calls,preview_cases,invalid_writes,torch_transitions);
    return 0;
}
''')
    with tempfile.TemporaryDirectory(prefix='torch-equivalence-') as tmp:
        path = Path(tmp)
        (path/'test.c').write_text('\n'.join(c))
        subprocess.run(['gcc', '-std=c99', '-O2', '-fno-builtin', '-Wno-pointer-to-int-cast', '-I'+str(GAME/'src'), '-I'+str(Path(bundle)), str(path/'test.c'), '-o', str(path/'test')], check=True)
        result = json.loads(subprocess.check_output([str(path/'test')], text=True))
    return dict(method=__doc__.strip(), before_source=before_source, after_source=after_source,
                source_sha256={phase:{name:hashlib.sha256(text.encode()).hexdigest() for name,text in rows.items()} for phase,rows in sources.items()},
                native_rom_sha256=hashlib.sha256(native.rom).hexdigest(), **result)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--before-source', default=BASELINE)
    ap.add_argument('--after-source', default='WORKTREE')
    ap.add_argument('--bundle', default='/workspace/setup/performance/before/bundle')
    ap.add_argument('--out', default='/workspace/setup/performance/torch-equivalence.json')
    args = ap.parse_args()
    report = run(args.before_source, args.after_source, args.bundle)
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('method','source_sha256')}))


if __name__ == '__main__':
    main()

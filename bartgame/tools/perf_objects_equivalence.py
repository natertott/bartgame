#!/usr/bin/env python3
"""Compare actual object/hand painters after pool-kind rejection.

The original/candidate functions and their release-overlap helpers execute on
identical96-actor pools. The unchanged renderer/native sheet descriptors and
a deterministic pure terrain-priority stub record every painter call, OAM
byte and all gameplay state bytes. Fixtures include released loads, arrows,
flames, eight-frame bomb handoff, gated hoards, hidden/hurt states and full OAM.
Actual scene rendering/cycles remain the native performance suite's scope.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

from perf_actor_equivalence import function, source
from sewer_concept_audit import NativeRom

GAME = Path(__file__).resolve().parents[1]
BASELINE = '11b872e9897320398fa02344cef1418733c04e9a'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--before-source', default=BASELINE)
    ap.add_argument('--after-source', default='WORKTREE')
    ap.add_argument('--bundle', default='/workspace/setup/performance/before/bundle')
    ap.add_argument('--out', default='/workspace/setup/performance/objects-equivalence.json')
    args = ap.parse_args()
    native = NativeRom(args.bundle)
    metadata = []
    for name, index in sorted(native.sheet_ids.items(), key=lambda row: row[1]):
        m, _ = native.sheet(name)
        metadata.append('[%d]={0,%d,%d,%d,%d,%d,%d,%d}' %
                        (index, m['tile_count'], m['frame_tiles'], m['shape'], m['size'], m['pal'], m['width'], m['height']))
    before = source(args.before_source, 'objects.c')
    after = source(args.after_source, 'objects.c')
    actor = source(args.before_source, 'actor.c')
    c = ['''#include <stdio.h>
#undef NULL
#include "objects.h"
#include "player.h"
#include "video.h"
#include "world.h"
#include "game.h"
const SpriteSheet sheets[SHEET_COUNT]={''', ','.join(metadata), '''};
Actor gActors[ACTOR_MAX];Actor* gPlayer=&gActors[0];
PlayerState gPl;
World gWorld;
GameState gGame;
volatile u32 gFrame;
s16 gCamX,gCamY;
OamEntry gOam[128];u8 gOamCount;
static unsigned calls,release_calls;
typedef struct {int kind,args[9];} Call;
static Call trace[512],previous_trace[512];
static void call(int kind,int a,int b,int c,int d,int e,int f,int g,int h,int i) {
    if(calls>=512)__builtin_trap();
    trace[calls++]=(Call){kind,{a,b,c,d,e,f,g,h,i}};
}
OamEntry* oam_alloc(void) {return gOamCount<128?&gOam[gOamCount++]:0;}
int room_prop_priority(int x,int y,int z,int w,int h,int priority) {
    call(2,x,y,z,w,h,priority,0,0,0);return ((unsigned)(x^y^z^w^h^priority))&3;
}
int player_recoil_priority(const Actor* a,int p) {(void)a;return p;}
''']
    c += [function(actor, 'draw_sprite').replace('draw_sprite(', 'reference_draw_sprite('),
          '''void draw_sprite(int x,int y,int sheet,u16 tile,int frame,int flip,int priority,int pal) {
    call(0,x,y,sheet,tile,frame,flip,priority,pal,0);
    reference_draw_sprite(x,y,sheet,tile,frame,flip,priority,pal);
}''', function(actor, 'actor_visual_size'),
          function(actor, 'actor_draw').replace('actor_draw(', 'reference_actor_draw('),
          '''void actor_draw(Actor* a) {
    call(1,a-gActors,a->kind,a->type,a->sheet,a->frame,a->tile,a->prio,a->pal,a->hflip);
    reference_actor_draw(a);
}''']
    names = ('player_hand_composite', 'player_release_overlap', 'objects_draw_hand', 'objects_draw')
    for prefix, text in [('before', before), ('after', after)]:
        for name in names:
            body = function(text, name)
            for n in names:
                body = re.sub(r'\b'+n+r'\b', prefix+'_'+n, body)
            if name == 'player_release_overlap':
                at = body.index('{')+1
                body = body[:at]+'release_calls++;'+body[at:]
            c.append(body)
    c.append('''
static unsigned random_state=0x78ab43d1u;
static unsigned rnd(void) {random_state^=random_state<<13;random_state^=random_state>>17;random_state^=random_state<<5;return random_state;}
static int same(const void* a,const void* b,unsigned n) {
    const u8* x=a;const u8* y=b;while(n--)if(*x++!=*y++)return 0;return 1;
}
static void clear(void* a,unsigned n) {u8* x=a;while(n--)*x++=0;}
static unsigned cases,painter_calls,oam_entries,release_calls_avoided,full_oam_cases,nonempty_pools;
static Actor input[ACTOR_MAX];
static void compare(int initial) {
    OamEntry previous[128];PlayerState pl=gPl;World world=gWorld;GameState game=gGame;
    unsigned old_calls,old_release,old_oam,i;
    for(i=0;i<ACTOR_MAX;i++)input[i]=gActors[i];
    for(i=0;i<128;i++)gOam[i]=(OamEntry){0x1234,0x6789,0x2def,0xabcd};
    gOamCount=initial;calls=release_calls=0;
    before_objects_draw_hand(1);before_objects_draw_hand(0);before_objects_draw();
    old_calls=calls;old_release=release_calls;old_oam=gOamCount;
    if(!same(input,gActors,sizeof(input)) || !same(&pl,&gPl,sizeof(pl)) || !same(&world,&gWorld,sizeof(world)) || !same(&game,&gGame,sizeof(game)))__builtin_trap();
    for(i=0;i<old_calls;i++)previous_trace[i]=trace[i];
    for(i=0;i<128;i++){previous[i]=gOam[i];gOam[i]=(OamEntry){0x1234,0x6789,0x2def,0xabcd};}
    gOamCount=initial;calls=release_calls=0;
    after_objects_draw_hand(1);after_objects_draw_hand(0);after_objects_draw();
    if(calls!=old_calls || old_oam!=gOamCount || !same(previous_trace,trace,calls*sizeof(Call)) || !same(previous,gOam,sizeof(previous)) || !same(input,gActors,sizeof(input)) || !same(&pl,&gPl,sizeof(pl)) || !same(&world,&gWorld,sizeof(world)) || !same(&game,&gGame,sizeof(game)) || release_calls>old_release) {
        printf("FAIL case%u calls%u/%u OAM%u/%u\\n",cases,old_calls,calls,old_oam,gOamCount);__builtin_trap();
    }
    cases++;painter_calls+=calls;oam_entries+=gOamCount-initial;release_calls_avoided+=old_release-release_calls;full_oam_cases+=initial==128;
}
static void configure_player(int state,int dead,int hidden) {
    clear(gActors,sizeof(gActors));clear(&gPl,sizeof(gPl));clear(&gWorld,sizeof(gWorld));clear(&gGame,sizeof(gGame));
    gPlayer->kind=AK_PLAYER;gPlayer->sheet=SHEET_HERO;gPlayer->w=gPlayer->h=32;
    gPlayer->x=128*65536;gPlayer->y=104*65536;gPlayer->state=state;gPlayer->prio=1;
    gPlayer->flags=hidden?AF_HIDDEN:0;gPl.dead_timer=dead;gGame.area=AREA_FOREST;gGame.cell=13;gFrame=0;gCamX=gCamY=0;
}
static void configure_actor(Actor* a,int kind,int type) {
    const SpriteSheet* sh;
    a->kind=kind;a->type=type;
    a->sheet=kind==AK_FX?SHEET_FX:kind==AK_PROJ?SHEET_ARROW:kind==AK_OBJECT?SHEET_LIFT:SHEET_ITEMS;
    sh=&sheets[a->sheet];a->w=sh->w;a->h=sh->h;a->tile=500;a->pal=sh->pal;a->frame=0;a->prio=2;
    a->x=128*65536;a->y=104*65536;a->vx=133;a->vy=96;
}
int main(void) {
    static const int types[]={OBJ_THROWN,FX_BOMB_OBJ,PJ_ARROW,FX_FLAME,PK_GILT,PK_RELIC,255};
    static const int states[]={PS_NORMAL,PS_FALL,PS_DEAD};
    static const int dead[]={60,61,64,68};
    unsigned kind,type,timer,dir,state,d,h,a,b,i,j;
    for(kind=0;kind<8;kind++)for(type=0;type<7;type++)for(timer=0;timer<=8;timer++)for(dir=0;dir<4;dir++)for(state=0;state<3;state++)for(d=0;d<4;d++)for(a=0;a<2;a++)for(b=0;b<2;b++) {
        Actor* item=&gActors[1];
        configure_player(states[state],dead[d],(timer==8 && (dir&1)));
        configure_actor(item,kind,types[type]);item->timer2=timer;item->dir=dir*8;item->v[0]=a;item->v[2]=b;
        if(timer&1)gWorld.cells[gGame.cell].opened=CELL_POCKET_OPEN;
        item->iframes=timer%3?0:12;gFrame=dir;
        compare(cases%3==0?128:cases%3==1?127:0);
    }
    for(i=0;i<8192;i++) {
        configure_player(rnd()%13,rnd()%256,rnd()%8==0);
        gPlayer->z=(rnd()%30)*65536;gPlayer->prio=rnd()%4;
        gGame.area=rnd()%3;gGame.cell=rnd()%25;gWorld.cells[gGame.cell].opened=rnd()%256;
        gFrame=rnd();gCamX=rnd()%256;gCamY=rnd()%192;
        for(j=1;j<ACTOR_MAX;j++) {
            Actor* item=&gActors[j];const SpriteSheet* sh;
            configure_actor(item,rnd()%12,types[rnd()%7]);sh=&sheets[item->sheet];
            item->frame=rnd()%(sh->tile_count/sh->frame_tiles);item->hflip=rnd()&1;item->timer2=rnd()%10;
            item->dir=rnd()%32;item->v[0]=rnd()&1;item->v[2]=rnd()&1;item->iframes=rnd()%12;
            item->flags=rnd()%8==0?AF_HIDDEN:0;
            item->x=((int)(rnd()%640)-64)*65536;item->y=((int)(rnd()%480)-64)*65536;item->z=(rnd()%36)*65536;
            item->vx=(int)(rnd()%640)-64;item->vy=(int)(rnd()%480)-64;
        }
        nonempty_pools++;compare(rnd()%3==0?128:rnd()%3==0?127:0);
    }
    for(kind=0;kind<4;kind++)for(type=0;type<7;type++)for(h=0;h<2;h++)for(a=0;a<7;a++)for(b=0;b<7;b++) {
        static const int xy[]={-65,-32,-31,-1,0,31,32};Actor* item=&gActors[1];
        configure_player(PS_NORMAL,0,h);configure_actor(item,AK_PROJ+kind,types[type]);
        item->v[0]=1;item->v[2]=1;item->dir=DIR_N;item->x+=xy[a]*65536;item->y+=xy[b]*65536;
        compare(0);
    }
    if(!oam_entries || !release_calls_avoided)return 2;
    printf("{\\"passed\\":true,\\"cases\\":%u,\\"painter_calls\\":%u,\\"oam_entries\\":%u,\\"release_overlap_calls_avoided\\":%u,\\"full_oam_cases\\":%u,\\"randomized_96_actor_pools\\":%u}\\n",cases,painter_calls,oam_entries,release_calls_avoided,full_oam_cases,nonempty_pools);
    return 0;
}
''')
    with tempfile.TemporaryDirectory(prefix='object-equivalence-') as tmp:
        directory = Path(tmp)
        src = directory/'test.c'
        src.write_text('\n'.join(c))
        binary = directory/'test'
        subprocess.run(['gcc', '-std=c99', '-O2', '-fno-builtin', '-Wno-pointer-to-int-cast', '-I'+str(GAME/'src'),
                        '-I'+str(Path(args.bundle)), str(src), '-o', str(binary)], check=True)
        row = json.loads(subprocess.check_output([str(binary)], text=True))
    report = dict(method=__doc__.strip(), before_source=args.before_source, after_source=args.after_source,
                  tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  objects_before_sha256=hashlib.sha256(before.encode()).hexdigest(),
                  objects_after_sha256=hashlib.sha256(after.encode()).hexdigest(),
                  native_rom_sha256=hashlib.sha256(native.rom).hexdigest(), **row)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(row))


if __name__ == '__main__':
    main()

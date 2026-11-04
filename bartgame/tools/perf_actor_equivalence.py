#!/usr/bin/env python3
"""Host differential test for viewport culls and unchanged actor geometry.

Compile the actual old/new C draw functions against one pure deterministic
depth stub and the original OAM writer. Exhaustive native viewport edges and
random canvases compare all OAM bytes and Actor bytes, including full OAM,
hurt blinking, hidden actors and blades visible while their owner is outside
the viewport. This establishes cull equivalence; actual forest depth and
gameplay are qualified separately in the mGBA comparison suite.
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


def function(source, name):
    match = re.search(r'^(?:static )?(?:void|bool8|int) '+name+r'\([^;]*?\)\s*\{', source, re.M)
    assert match, name
    start = match.start()
    depth = 1
    pos = match.end()
    while depth:
        depth += (source[pos] == '{')-(source[pos] == '}')
        pos += 1
    return source[start:pos]


def source(rev, name):
    if rev == 'WORKTREE':
        return (GAME/'src'/name).read_text()
    return subprocess.check_output(['git', 'show', rev+':bartgame/src/'+name], cwd=REPO, text=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--before-source', default=BASELINE)
    ap.add_argument('--after-source', default='WORKTREE')
    ap.add_argument('--bundle', default='/workspace/setup/performance/before/bundle')
    ap.add_argument('--out', default='/workspace/setup/performance/actor-equivalence.json')
    args = ap.parse_args()
    native = NativeRom(args.bundle)
    sheet_rows = []
    for name, index in sorted(native.sheet_ids.items(), key=lambda pair: pair[1]):
        meta, _ = native.sheet(name)
        sheet_rows.append('[%d]={0,%d,%d,%d,%d,%d,%d,%d}' %
                          (index, meta['tile_count'], meta['frame_tiles'], meta['shape'], meta['size'], meta['pal'], meta['width'], meta['height']))
    old_actor = source(args.before_source, 'actor.c')
    new_actor = source(args.after_source, 'actor.c')
    old_enemy = source(args.before_source, 'enemy.c')
    new_enemy = source(args.after_source, 'enemy.c')
    c = ['''#include <stdio.h>
#undef NULL
#include "actor.h"
#include "video.h"
#define ES_WINDUP 6
const SpriteSheet sheets[SHEET_COUNT] = {''', ',\n'.join(sheet_rows), '''};
Actor gActors[ACTOR_MAX];
volatile u32 gFrame;
s16 gCamX,gCamY;
OamEntry gOam[128];
u8 gOamCount;
static u16 sKswordTile=720;
static unsigned depth_calls;
OamEntry* oam_alloc(void) {return gOamCount<128?&gOam[gOamCount++]:0;}
int room_prop_priority(int px,int py,int z,int w,int h,int p) {
    depth_calls++;
    return ((unsigned)(px^py^z^w^h^p))&3;
}
int player_recoil_priority(const Actor* a,int p) {(void)a;return p;}
''', function(old_actor, 'draw_sprite'), function(old_actor, 'actor_visual_size')]
    for prefix, actor, enemy in [('before', old_actor, old_enemy), ('after', new_actor, new_enemy)]:
        for name, text in [('actor_draw', actor), ('knight_draw_sword', enemy)]:
            c.append(function(text, name).replace('static void ', 'void ').replace(name+'(', prefix+'_'+name+'('))
    c.append('''
static unsigned rand_state=0xb4a76321u;
static unsigned rnd(void) {rand_state^=rand_state<<13;rand_state^=rand_state>>17;rand_state^=rand_state<<5;return rand_state;}
static int eq(const void* a,const void* b,unsigned n) {
    const u8* aa=a;const u8* bb=b;
    while(n--)if(*aa++!=*bb++)return 0;return 1;
}
static unsigned cases,body_calls_saved,blade_calls_saved,blade_owner_hidden;
static void compare(Actor* input,int knight,int initial) {
    OamEntry old[128];Actor a=*input,b=*input;
    unsigned old_calls,new_calls;int i,count;
    for(i=0;i<128;i++)gOam[i]=(OamEntry){0x1234,0x6789,0x2def,0xabcd};
    gOamCount=initial;depth_calls=0;
    if(knight)before_knight_draw_sword(&a);else before_actor_draw(&a);
    old_calls=depth_calls;count=gOamCount;
    for(i=0;i<128;i++){old[i]=gOam[i];gOam[i]=(OamEntry){0x1234,0x6789,0x2def,0xabcd};}
    gOamCount=initial;depth_calls=0;
    if(knight)after_knight_draw_sword(&b);else after_actor_draw(&b);
    new_calls=depth_calls;
    if(count!=gOamCount || !eq(old,gOam,sizeof(old)) || !eq(&a,&b,sizeof(a)) || !eq(&a,input,sizeof(a)) || new_calls>old_calls) {
        printf("FAIL case%u knight%d xy%d,%d camera%d,%d sheet%d canvas%d,%d count%d/%d\\n",cases,knight,PX(a.x),PX(a.y),gCamX,gCamY,a.sheet,a.w,a.h,count,gOamCount);
        __builtin_trap();
    }
    if(knight)blade_calls_saved+=old_calls-new_calls;
    else body_calls_saved+=old_calls-new_calls;
    if(knight && count>initial) {
        const SpriteSheet* sh=&sheets[SHEET_KNIGHT];
        int sx=PX(a.x)-a.w/2-gCamX,sy=PX(a.y)-a.h-PX(a.z)-gCamY;
        if(sx<=-sh->w || sx>=240 || sy<=-sh->h || sy>=160)blade_owner_hidden++;
    }
    cases++;
}
int main(void) {
    int sheet,x,y,variant,face,state,initial,i;
    for(sheet=0;sheet<SHEET_COUNT;sheet++)for(variant=0;variant<12;variant++) {
        const SpriteSheet* sh=&sheets[sheet];
        int xs[]={-sh->w-1,-sh->w,1-sh->w,-1,0,239,240,241};
        int ys[]={-sh->h-1,-sh->h,1-sh->h,-1,0,159,160,161};
        gFrame=variant&3;gCamX=113;gCamY=71;
        for(x=0;x<8;x++)for(y=0;y<8;y++) {
            Actor a={0};a.kind=AK_ENEMY;a.sheet=sheet;a.w=sh->w+(variant==4?8:0);a.h=sh->h;a.z=(variant%3)*65536;
            a.x=(xs[x]+gCamX+a.w/2)*65536;a.y=(ys[y]+gCamY+a.h+PX(a.z))*65536;
            a.flags=variant==5?AF_HIDDEN:0;a.iframes=variant%3==1?10:0;a.frame=3;a.hflip=variant&1;a.pal=sh->pal;a.tile=144;
            compare(&a,0,variant%3==0?0:variant%3==1?127:128);
        }
    }
    for(i=0;i<400000;i++) {
        Actor a={0};const SpriteSheet* sh;
        a.sheet=rnd()%SHEET_COUNT;sh=&sheets[a.sheet];
        a.kind=AK_PLAYER+rnd()%7;a.w=sh->w;a.h=sh->h;
        a.x=((int)(rnd()%1200)-200)*65536;a.y=((int)(rnd()%900)-200)*65536;a.z=(rnd()%40)*65536;
        a.flags=(rnd()%16==0)?AF_HIDDEN:0;a.iframes=rnd()%5;a.frame=rnd()%8;a.hflip=rnd()&1;a.pal=rnd()&15;a.tile=144;
        gFrame=rnd();gCamX=rnd()%512;gCamY=rnd()%384;
        compare(&a,0,rnd()%130>127?128:0);
    }
    for(x=-40;x<=280;x+=4)for(y=-60;y<=200;y+=4)for(face=0;face<4;face++)for(state=6;state<=7;state++)for(initial=0;initial<=128;initial+=128) {
        Actor a={0};a.kind=AK_ENEMY;a.type=4;a.sheet=SHEET_KNIGHT;a.w=sheets[SHEET_KNIGHT].w;a.h=sheets[SHEET_KNIGHT].h;
        a.x=x*65536;a.y=y*65536;a.facing=face;a.state=state;a.prio=2;
        gCamX=gCamY=0;gFrame=0;compare(&a,1,initial);
    }
    if(!body_calls_saved || !blade_calls_saved || !blade_owner_hidden)return 2;
    printf("{\\"cases\\":%u,\\"body_depth_calls_avoided\\":%u,\\"blade_depth_calls_avoided\\":%u,\\"visible_blades_with_offscreen_owner\\":%u,\\"passed\\":true}\\n",cases,body_calls_saved,blade_calls_saved,blade_owner_hidden);
    return 0;
}
''')
    with tempfile.TemporaryDirectory(prefix='actor-equivalence-') as tmp:
        directory = Path(tmp)
        src = directory/'test.c'
        src.write_text('\n'.join(c))
        binary = directory/'test'
        subprocess.run(['gcc', '-std=c99', '-O2', '-fno-builtin', '-Wno-pointer-to-int-cast', '-I'+str(GAME/'src'), '-I'+str(Path(args.bundle)), str(src), '-o', str(binary)], check=True)
        run = subprocess.check_output([str(binary)], text=True)
        row = json.loads(run)
    report = dict(method=__doc__.strip(), before_source=args.before_source, after_source=args.after_source,
                  actor_before_sha256=hashlib.sha256(old_actor.encode()).hexdigest(),
                  actor_after_sha256=hashlib.sha256(new_actor.encode()).hexdigest(),
                  enemy_before_sha256=hashlib.sha256(old_enemy.encode()).hexdigest(),
                  enemy_after_sha256=hashlib.sha256(new_enemy.encode()).hexdigest(),
                  **row)
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(row))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Compare the original and optimized glitter selection/HUD map algorithms.

The actual C source from the baseline revision and current checkout is compiled
for the host, with deterministic room/actor/render fixtures. Glitter calls,
ordering, priorities, frame counters and HUD shadow-map bytes must agree.
This establishes algorithm equivalence, not native GBA timing or full-game
visual correctness; the separate mGBA performance/render runs cover those.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

GAME = Path(__file__).resolve().parents[1]
SHA = lambda data: hashlib.sha256(data).hexdigest()


def aliases(source, prefix):
    names = re.findall(r'^(?!static\b)(?:void|bool8|int|u16\*|u16|Actor\*)\s+(\w+)\([^;]*?\)\s*\{', source, re.M)
    names += re.findall(r'^(?:u8|u16|u32)\s+(g\w+)(?:\[|\s*;)', source, re.M)
    names += re.findall(r'\bgAmbient\w+', source)
    return '\n'.join('#define %s %s_%s' % (name, prefix, name) for name in sorted(set(names)))+'\n'


WRAPPER = r'''
void @P@_map_setup(void) {
    memset32(sBg0,0,sizeof(sBg0));sBg0Dirty=0;
    sPurse.tile=56;sPurse.tw=30;sPurse.th=3;hud_stale();
}
void @P@_map_draw(u16* result,int* dirty) {
    hud_bar();memcpy32(result,sBg0,sizeof(sBg0));*dirty=sBg0Dirty;sBg0Dirty=0;
}
void @P@_map_op(int op,int x,int y,int value) {
    Canvas c={.tile=256,.tw=3,.th=2,.obj=0,.px=0};
    switch(op) {
    case0:break;
    case1:bg0_clear();break;
    case2:bg0_put(x,y,value);break;
    case3:bg0_fill(x,y,3,2,value);break;
    case4:{u16* m=bg0_map();m[(y&31)*32+(x&31)]=value;break;}
    case5:bg0_canvas(&c,x,y,3,2);break;
    case6:bg0_show(&c,x,y,TRUE);break;
    case7:bg0_show(&c,x,y,FALSE);break;
    case8:bg0_pool_reset_full();break;
    case9:hud_stale();break;
    }
}
void @P@_number(int x,int y,unsigned value,const u32* base,u32* result) {
    static u32 pixels[30*3*8];
    sPurse.tw=30;sPurse.th=3;sPurse.px=pixels;
    memcpy32(pixels,base,sizeof(pixels));hud_digits(x,y,value);
    memcpy32(result,pixels,sizeof(pixels));
}
'''.replace('case', 'case ')


FIXTURE = r'''
#include <stdio.h>
#include "gba.h"
#include "actor.h"
#include "room.h"
#include "world.h"
#include "game.h"
#include "vwf.h"

Room gRoom;World gWorld;GameState gGame;Actor gActors[ACTOR_MAX];
s16 gCamX,gCamY;volatile u32 gFrame;u8 gOamCount;u32 gRoomRevision;
const SpriteSheet sheets[SHEET_COUNT] = {
    [SHEET_GLITTER]={.tile_count=SHEET_GLITTER_FRAMES,.frame_tiles=1,.pal=14,.w=8,.h=8}
};
const u8 metatile_glitter[METATILE_COUNT] = {
    [1]=1,[2]=1,[5]=1,[MT_MYST_SWITCH]=1,[MT_MYST_SWITCH_DOWN]=1,
    [MT_SPARKLE]=1,[MT_SPARKLE_WHITE]=1,[MT_BLIGHT_MIST]=1
};
const u8 metatile_prop[METATILE_COUNT] = {[2]=1};
const u8 metatile_coll[METATILE_COUNT] = {[2]=15};
const u8 metatile_type[METATILE_COUNT] = {[5]=TT_CHEST};

static unsigned seed=0xb4a76321u;
static unsigned rnd(void){seed^=seed<<13;seed^=seed>>17;seed^=seed<<5;return seed;}
static int equal(const void* a,const void* b,unsigned bytes){
    const u8* x=a;const u8* y=b;while(bytes--)if(*x++!=*y++)return0;return1;
}
void memset32(void* dst,u32 value,u32 bytes){u32* d=dst;while(bytes>=4){*d++=value;bytes-=4;}}
void memcpy32(void* dst,const void* src,u32 bytes){u32* d=dst;const u32* s=src;while(bytes>=4){*d++=*s++;bytes-=4;}}
void* memset(void* dst,int value,u32 bytes){u8* d=dst;while(bytes--)*d++=value;return dst;}
u16 room_get(int x,int y){return x<0||y<0||x>=gRoom.w||y>=gRoom.h?MT_NONE:gRoom.ground[y*32+x];}
u16 room_get_overlay(int x,int y){return x<0||y<0||x>=gRoom.w||y>=gRoom.h?MT_NONE:gRoom.overlay[y*32+x];}
u32 hash32(u32 a,u32 b){u32 h=a*0x9E3779B1u^(b+0x7F4A7C15u);h^=h>>15;h*=0x85EBCA77u;h^=h>>13;h*=0xC2B2AE3Du;h^=h>>16;return h;}
u16 sprite_load_sheet(int sheet){(void)sheet;return37;}
static unsigned reads,visuals;
void actor_visual_size(const Actor* a,int* w,int* h){
    visuals++;
    if(a->kind==AK_PLAYER||a->kind==AK_NPC){*w=18;*h=24;}
    else if(a->sheet==SHEET_BOSS){*w=32;*h=50;}
    else if(a->sheet==SHEET_KNIGHT){*w=16;*h=28;}
    else{*w=a->w;*h=a->h;}
}
typedef struct {int x,y,sheet,tile,frame,flip,priority,palette;} Call;
static Call calls[64];static int call_count;
void draw_sprite(int x,int y,int sheet,u16 tile,int frame,int flip,int priority,int palette){
    calls[call_count++]=(Call){x,y,sheet,tile,frame,flip,priority,palette};gOamCount++;
}
void vwf_pool(int first,int last){(void)first;(void)last;}
bool8 vwf_canvas(Canvas* c,int tw,int th){*c=(Canvas){.tile=270,.tw=tw,.th=th};return TRUE;}
void vwf_clear(Canvas* c,int ink){(void)c;(void)ink;}
void vwf_pixel(Canvas* c,int x,int y,int ink){
    if(x<0||y<0||x>=c->tw*8||y>=c->th*8)return;
    u32* w=c->px+((y>>3)*c->tw+(x>>3))*8+(y&7);int s=(x&7)*4;
    *w=(*w&~(15u<<s))|((u32)(ink&15)<<s);
}
void vwf_map(const Canvas* c,u16* map,int tx,int ty,int pal){
    int x,y;for(y=0;y<c->th;y++)for(x=0;x<c->tw;x++)
        if(tx+x>=0&&tx+x<32&&ty+y>=0&&ty+y<32)
            map[(ty+y)*32+tx+x]=(c->tile+y*c->tw+x)|(pal<<12);
}
void before_ambient_room_reset(void),after_ambient_room_reset(void);
void before_ambient_draw(bool8),after_ambient_draw(bool8);
extern u16 before_gAmbientSiteCount,after_gAmbientSiteCount;
extern u8 before_gAmbientPotential,before_gAmbientVisible,before_gAmbientPeaks;
extern u8 after_gAmbientPotential,after_gAmbientVisible,after_gAmbientPeaks;
void before_map_setup(void),after_map_setup(void);
void before_map_op(int,int,int,int),after_map_op(int,int,int,int);
void before_map_draw(u16*,int*),after_map_draw(u16*,int*);
void before_number(int,int,unsigned,const u32*,u32*),after_number(int,int,unsigned,const u32*,u32*);

static unsigned glitter_cases,glitter_calls,before_visuals,after_visuals;
static int glitter_test(void) {
    int room,tick,i;
    for(room=0;room<512;room++) {
        gRoom.w=room<4?32:1+rnd()%32;gRoom.h=room<4?24:1+rnd()%32;
        gWorld.seed=rnd();gGame.area=rnd()%3;gGame.cell=rnd()%25;
        for(i=0;i<1024;i++) {
            int r=rnd()%10;
            gRoom.ground[i]=room==0?2:room==1?1:room==2?3:1+rnd()%5;
            gRoom.overlay[i]=r<6?MT_NONE:r==6?MT_SPARKLE:r==7?MT_BLIGHT_MIST:r==8?MT_MYST_SWITCH:3;
        }
        before_ambient_room_reset();after_ambient_room_reset();
        if(before_gAmbientSiteCount!=after_gAmbientSiteCount)return1;
        for(tick=0;tick<128;tick++) {
            Call expected[64];int expected_count,initial,extra,final_count;
            unsigned expected_vis;u8 stats[3];
            gFrame=room*128+tick;
            if((tick&7)==0)gFrame--; /* also repeated same-frame complete renders */
            if((tick&3)==0){gCamX=(int)(rnd()%600)-60;gCamY=(int)(rnd()%500)-60;}
            for(i=0;i<ACTOR_MAX;i++) {
                Actor* a=&gActors[i];memset(a,0,sizeof(*a));
                a->kind=room==0?AK_ENEMY:rnd()%8;a->flags=(rnd()%6==0?AF_HIDDEN:0);
                a->x=Q16((int)(rnd()%900)-180);a->y=Q16((int)(rnd()%700)-150);a->z=Q16((int)(rnd()%90)-20);
                a->sheet=rnd()%SHEET_COUNT;a->w=rnd()%65;a->h=rnd()%65;
            }
            if(tick%7==0){gRoom.ground[rnd()%1024]=3;gRoomRevision++;} /* opened/destroyed material */
            initial=rnd()%130;extra=rnd()%70;
            call_count=visuals=0;gOamCount=initial;
            before_ambient_draw(TRUE);gOamCount+=extra;before_ambient_draw(FALSE);
            expected_count=call_count;memcpy32(expected,calls,sizeof(calls));expected_vis=visuals;final_count=gOamCount;
            stats[0]=before_gAmbientPotential;stats[1]=before_gAmbientVisible;stats[2]=before_gAmbientPeaks;
            call_count=visuals=0;gOamCount=initial;
            after_ambient_draw(TRUE);gOamCount+=extra;after_ambient_draw(FALSE);
            if(expected_count!=call_count||!equal(expected,calls,call_count*sizeof(Call))||final_count!=gOamCount||
               stats[0]!=after_gAmbientPotential||stats[1]!=after_gAmbientVisible||stats[2]!=after_gAmbientPeaks){
                printf("glitter mismatch room%d tick%d calls%d/%d\n",room,tick,expected_count,call_count);return2;
            }
            glitter_cases++;glitter_calls+=call_count;before_visuals+=expected_vis;after_visuals+=visuals;
        }
    }
    return0;
}

static unsigned map_cases,before_uploads,after_uploads;
static int map_test(void){
    int i,x,y,value,op,old_dirty,new_dirty;u16 old[1024],new[1024];
    before_map_setup();after_map_setup();
    for(i=0;i<50000;i++) {
        op=i%8==0?rnd()%10:0;x=(int)(rnd()%40)-4;y=(int)(rnd()%40)-4;value=rnd()&65535;
        before_map_op(op,x,y,value);after_map_op(op,x,y,value);
        before_map_draw(old,&old_dirty);after_map_draw(new,&new_dirty);
        if(!equal(old,new,sizeof(old))){printf("map mismatch case%d op%d\n",i,op);return3;}
        before_uploads+=old_dirty!=0;after_uploads+=new_dirty!=0;map_cases++;
    }
    return0;
}
static unsigned number_cases;
static int compare_number(int x,int y,unsigned value) {
    u32 base[720],old[720],new[720];int i;
    for(i=0;i<720;i++)base[i]=rnd();
    before_number(x,y,value,base,old);after_number(x,y,value,base,new);
    if(!equal(old,new,sizeof(old))){printf("number mismatch value%u at%d,%d\n",value,x,y);return 4;}
    number_cases++;return0;
}
static int number_test(void) {
    unsigned value;int i,j,k,fail;
    static const int xs[]={-22,-3,0,2,225,238,239,240};
    static const int ys[]={-3,0,3,14,19,22,23,24};
    static const unsigned values[]={0,1,9,10,99,100,255,999,10000,65535,99999,1234567,0xffffffffu};
    for(value=0;value<=65535;value++) {
        fail=compare_number(94,3,value);if(fail)return fail;
        fail=compare_number(94+((value>>4)&7),3,value);if(fail)return fail;
    }
    for(value=0;value<=255;value++)for(i=0;i<3;i++)for(j=0;j<8;j++) {
        fail=compare_number(149+i*30+j,14,value);if(fail)return fail;
    }
    for(i=0;i<8;i++)for(j=0;j<8;j++)for(k=0;k<13;k++) {
        fail=compare_number(xs[i],ys[j],values[k]);if(fail)return fail;
    }
    return0;
}
int main(void){
    int fail=glitter_test();if(!fail)fail=map_test();if(!fail)fail=number_test();
    printf("{\"passed\":%s,\"glitter_cases\":%u,\"glitter_draw_calls\":%u,\"actor_visual_queries_before\":%u,\"actor_visual_queries_after\":%u,\"map_cases\":%u,\"map_uploads_before\":%u,\"map_uploads_after\":%u,\"number_cases\":%u}\n",
           fail?"false":"true",glitter_cases,glitter_calls,before_visuals,after_visuals,map_cases,before_uploads,after_uploads,number_cases);
    return fail;
}
'''.replace('return0', 'return 0').replace('return1', 'return 1').replace('return2', 'return 2').replace('return3', 'return 3').replace('return37', 'return 37')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--baseline', default='11b872e9897320398fa02344cef1418733c04e9a')
    ap.add_argument('--out', default='/workspace/setup/performance/effects-equivalence.json')
    args = ap.parse_args()
    output = Path(args.out).resolve()
    work = output.parent/(output.stem+'-build')
    work.mkdir(parents=True, exist_ok=True)
    objects, inputs = [], {}
    log = []
    for phase in ('before', 'after'):
        for stem in ('ambient', 'text'):
            path = 'bartgame/src/'+stem+'.c'
            data = subprocess.check_output(['git', 'show', args.baseline+':'+path], cwd=GAME.parent) if phase=='before' else (GAME/'src'/(stem+'.c')).read_bytes()
            inputs[phase+'/'+stem+'.c'] = SHA(data)
            source = data.decode()
            body = aliases(source, phase)+source
            if stem=='text': body += WRAPPER.replace('@P@', phase)
            src = work/(phase+'-'+stem+'.c');src.write_text(body)
            obj = src.with_suffix('.o')
            cmd = ['gcc', '-O2', '-fno-builtin', '-ffunction-sections', '-fdata-sections', '-w', '-Isrc', '-Ibuild/gen', '-c', str(src), '-o', str(obj)]
            result = subprocess.run(cmd, cwd=GAME, text=True, capture_output=True)
            log += [str(cmd), result.stdout, result.stderr]
            if result.returncode: raise RuntimeError(result.stderr)
            objects.append(str(obj))
    fixture = work/'fixture.c';fixture.write_text(FIXTURE)
    binary = work/'equivalence'
    cmd = ['gcc', '-O2', '-fno-builtin', '-w', '-Isrc', '-Ibuild/gen', '-Wl,--gc-sections', str(fixture), *objects, '-o', str(binary)]
    result = subprocess.run(cmd, cwd=GAME, text=True, capture_output=True)
    log += [str(cmd), result.stdout, result.stderr]
    (work/'compile.log').write_text('\n'.join(log))
    if result.returncode: raise RuntimeError(result.stderr)
    result = subprocess.run([str(binary)], text=True, capture_output=True)
    (work/'run.log').write_text(result.stdout+result.stderr)
    print(result.stdout)
    report = json.loads(result.stdout.splitlines()[-1])
    report.update(method=__doc__.strip(), baseline=args.baseline,
                  current_source_sha256=inputs, tool_sha256=SHA(Path(__file__).read_bytes()),
                  executable_sha256=SHA(binary.read_bytes()))
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n')
    return result.returncode


if __name__=='__main__':raise SystemExit(main())

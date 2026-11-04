#!/usr/bin/env python3
"""Compare packed canopy queries and Bloom guard against the original pixels.

Host execution maps a private fake GBA VRAM range, varies actual live entries,
tile alpha/flips, room bounds, legacy foliage and both tree planes, and compares
the optimized row query with32 original scalar calls. The complete original
prepare_canopy_visibility function is read from the frozen baseline revision;
all133 native poses, palette classifications, flips and both tree priorities
are compared byte-for-byte, including diagnostics and queue arguments. This
also compares240,000 depth queries with the complete original priority
function, varying planted owner rows and native body bounds. This is a
pure-query/guard equivalence check, not an emulator performance claim.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

GAME = Path(__file__).resolve().parents[1]
BASELINE = '11b872e9897320398fa02344cef1418733c04e9a'


def function(text, name):
    start = re.search(r'^(?:static )?(?:void|bool8|int) '+re.escape(name)+r'\(', text, re.M).start()
    end = text.index('{', start)+1
    depth = 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]


DRIVER = r'''
#include "gba.h"
#include "assets.h"
#include "room.h"
#include "forest_trees.h"
#include "game.h"
#include "actor.h"
#include "player.h"
extern int printf(const char*,...);
extern void* mmap(void*,unsigned long,int,int,int,long);
extern void harness_tree_state(int active);
extern int harness_reference_priority(int px,int py,int z,int width,int height,int priority);
extern int harness_reference_room_priority(int px,int py,int z,int width,int height,int priority);
extern int harness_player(int frame,int px,int py,int z,int flip,int priority,
                          int palette,int state,int hidden,int flicker);
GameState gGame;
volatile u32 gFrame;
u8 gRoomTorchesDirty;
static u8 chest_ready;
bool8 interactive_chest_ready(void) {return chest_ready;}
bool8 interactive_chest_tile(u16 mt) {return mt==MT_CHEST || mt==MT_CHEST_OPEN;}
bool8 interactive_chest_overlay(u16 mt) {return mt==MT_MYST_CHEST || mt==MT_MYST_CHEST_OPEN;}
static u32 random_state=0x2468ace1;
static u32 next(void) {
    random_state^=random_state<<13;random_state^=random_state>>17;
    random_state^=random_state<<5;return random_state;
}
static void fill_vram(void) {
    int i;
    vu16* tiles=CHARBLOCK(0);
    for(i=0;i<768*16;i++) {
        u32 bits=next();
        /* A substantial zero population exercises transparent nibble spans. */
        tiles[i]=bits&((next()&15)==0?0:0xf0ff);
    }
}
static void fill_metadata(void) {
    static const u16 types[]={MT_NONE,MT_MOSS0,MT_CANOPY,MT_CANOPY_BLIGHT,
        MT_BLIGHT_WALL,MT_F2_ARCH_0,MT_F2_ARCH_1,MT_TREE_TRUNK_W};
    int i;
    for(i=0;i<1024;i++) {
        gRoomVisualOverlay[i]=types[next()%8];
        gRoom.ground[i]=next()%11?next()%METATILE_COUNT:MT_NONE;
        gRoom.overlay[i]=next()%4?types[next()%8]:MT_MYST_SWITCH+(next()&1);
        gRoom.underlay[i]=gRoom.ground[i];
    }
    gRoomRevision++;
}
static int scalar_row(int px,int py,int priority,u32* value) {
    int x;u32 mask=0;
    for(x=0;x<32;x++)if(room_canopy_overlay_px(px+x,py) ||
        (priority==3 && forest_trees_base_px(px+x,py)))mask|=1u<<x;
    *value=mask;return 1;
}
int main(void) {
    int phase,i,frame,flip,priority,palette;
    unsigned long queries=0,poses=0,depths=0,props=0,mutations=0;
    if(mmap((void*)0x06000000,0x20000,3,0x32,-1,0)!=(void*)0x06000000)return 90;
    for(phase=0;phase<20;phase++) {
        gRoom.w=phase==16?32:phase%4==0?1:phase%4==1?8:phase%4==2?24:32;
        gRoom.h=phase%3==0?1:phase%3==1?24:32;
        gGame.area=phase==18?AREA_MYST:phase==19?AREA_SEWER:AREA_FOREST;
        fill_vram();fill_metadata();harness_tree_state(phase!=17);
        for(i=0;i<12000;i++) {
            int mx=next()%gRoom.w,my=next()%gRoom.h;
            if(i%31==0) {room_set(mx,my,next()%METATILE_COUNT);mutations++;}
            if(i%37==0) {room_set_overlay(mx,my,next()%2?MT_MYST_SWITCH:MT_NONE);mutations++;}
            if(i%41==0) {gRoomVisualOverlay[my*32+mx]=next()%METATILE_COUNT;gRoomRevision++;mutations++;}
            if(i%71==0)chest_ready^=1;
            if(i%97==0)gGame.area=(gGame.area+1)%3;
            if(i%1000==0) {
                Room saved=gRoom;
                room_set(mx,my,MT_CRACK);room_set_overlay(mx,my,MT_MYST_SWITCH);
                (void)room_prop_priority(mx*16+8,my*16+14,0,16,28,2);
                gRoom=saved;gRoomRevision++;mutations++;
            }
            int x=(int)(next()%(gRoom.w*16+80))-40;
            int y=(int)(next()%(gRoom.h*16+80))-40;
            int p=next()&3;
            u32 a,b=room_canopy_opaque_row(x,y,p);
            scalar_row(x,y,p,&a);queries++;
            if(a!=b) {
                printf("ROW FAIL phase=%d at=%d,%d priority=%d scalar=%08x packed=%08x\n",phase,x,y,p,a,b);
                return 1;
            }
            {
                int z=(int)(next()%65)-16,width=1+next()%64,height=1+next()%96;
                int a=harness_reference_priority(x,y,z,width,height,p);
                int b=forest_trees_priority(x,y,z,width,height,p);
                depths++;
                if(a!=b) {
                    printf("DEPTH FAIL phase=%d at=%d,%d z=%d width=%d height=%d priority=%d old=%d fast=%d\n",phase,x,y,z,width,height,p,a,b);
                    return 5;
                }
                a=harness_reference_room_priority(x,y,z,width,height,p);
                b=room_prop_priority(x,y,z,width,height,p);
                props++;
                if(a!=b) {
                    printf("PROP FAIL phase=%d i=%d at=%d,%d z=%d width=%d height=%d priority=%d old=%d fast=%d\n",phase,i,x,y,z,width,height,p,a,b);
                    return 6;
                }
            }
        }
        if(phase==16)for(frame=0;frame<SHEET_HERO_FRAMES;frame++)
            for(flip=0;flip<2;flip++)for(priority=2;priority<=3;priority++)
            for(palette=0;palette<16;palette++) {
                int z=(frame%5)*8;
                int x=(int)(next()%(gRoom.w*16+32))-16;
                int y=(int)(next()%(gRoom.h*16+48))-16;
                if(!harness_player(frame,x,y,z,flip,priority,palette,
                    frame%9==0?PS_FALL:PS_NORMAL,0,0))return 2;
                poses++;
            }
        for(i=0;i<1500;i++) {
            frame=next()%SHEET_HERO_FRAMES;flip=next()&1;priority=2+(next()&1);
            int x=(int)(next()%(gRoom.w*16+64))-32;
            int y=(int)(next()%(gRoom.h*16+64))-16;
            if(!harness_player(frame,x,y,(next()%6)*8,flip,priority,next()%16,
                next()%8==0?PS_FALL:PS_NORMAL,next()%19==0,next()%7==0))return 3;
            poses++;
        }
        for(i=-1;i<=1;i++)if(i) {
            if(!harness_player(i<0?-1:SHEET_HERO_FRAMES,16,32,16,0,2,0,PS_FALL,0,0))return 4;
            poses++;
        }
    }
    printf("PASS rows=%lu scalar_pixels=%lu native_guard_cases=%lu frames=%d depth_cases=%lu prop_cases=%lu mutations=%lu\n",
           queries,queries*32,poses,SHEET_HERO_FRAMES,depths,props,mutations);
    return 0;
}
'''

TREE_EXTRA = r'''
static unsigned tree_random=0xa5a5a5a5;
static u32 tree_next(void) {
    tree_random^=tree_random<<13;tree_random^=tree_random>>17;
    tree_random^=tree_random<<5;return tree_random;
}
void harness_tree_state(int active) {
    int x,y,n=0;
    sActive=active;
    for(y=0;y<64;y++)for(x=0;x<64;x++) {
        u16 top=tree_next()%768|((tree_next()&63)<<10);
        u16 base=tree_next()%768|((tree_next()&63)<<10);
        if((tree_next()&3)==0)top=0;
        if((tree_next()&3)==0)base=0;
        sUpper[y*64+x]=top;sLower[y*64+x]=base;
        *map_at(24,x,y)=(tree_next()&3)?top:(top^0x1000);
        *map_at(FOREST_TREES_SB_BASE,x,y)=(tree_next()&3)?base:0;
    }
    for(y=0;y<32;y++) {
        gForestTreeRootRows[y]=0;
        for(x=0;x<32;x++)gForestTreeRoots[y*32+x]=0;
    }
    for(y=0;y<gRoom.h;y++)for(x=0;x<gRoom.w;) {
        int frame=tree_next()%FOREST_TREE_FRAME_COUNT;
        int cells=forest_tree_width[frame]/16,dx;
        if((tree_next()&3)==0 || x+cells>gRoom.w || n>=FOREST_TREES_MAX) {x++;continue;}
        ForestTree* t=&gForestTrees[n];
        t->x=x*16;t->y=(y-1)*16;t->frame=frame;
        t->flags=FOREST_TREE_WOOD;t->root_mask[0]=t->root_mask[1]=15;
        for(dx=0;dx<cells;dx++) {
            gForestTreeRoots[y*32+x+dx]=n+1;
            gForestTreeRootRows[y]|=1u<<(x+dx);
        }
        n++;x+=cells;
    }
}
'''

PLAYER_EXTRA = r'''
static const void* queued_body;
static const void* queued_mask;
static volatile void* queued_body_dst;
static volatile void* queued_mask_dst;
static int queued;
void vram_queue_visibility(const void* body,volatile void* body_dst,
                           const void* mask,volatile void* mask_dst) {
    queued++;queued_body=body;queued_mask=mask;
    queued_body_dst=body_dst;queued_mask_dst=mask_dst;
}
extern int printf(const char*,...);
static void reset_guard(void) {
    int i;
    sCanopyTile=100;sCanopyReady=0;sCanopyCutoff=7;queued=0;
    queued_body=queued_mask=queued_body_dst=queued_mask_dst=0;
    for(i=0;i<256;i++)sCanopyPixels[i]=0x1234;
    for(i=0;i<12;i++)gForestV3Visibility[i]=0x55aa;
}
int harness_player(int frame,int px,int py,int z,int flip,int priority,
                   int palette,int state,int hidden,int flicker) {
    Actor a={0};int i;
    u16 saved_pixels[256],saved_diag[12];
    int saved_queued,saved_ready,saved_cutoff;
    const void* saved_body;const void* saved_mask;
    volatile void* saved_body_dst;volatile void* saved_mask_dst;
    a.x=Q16(px);a.y=Q16(py);a.z=Q16(z);a.hflip=flip;a.prio=priority;
    a.pal=palette;a.state=state;a.flags=hidden?AF_HIDDEN:0;
    a.iframes=flicker?1:0;gFrame=flicker?2:0;
    reset_guard();reference_prepare_canopy_visibility(&a,frame);
    for(i=0;i<256;i++)saved_pixels[i]=sCanopyPixels[i];
    for(i=0;i<12;i++)saved_diag[i]=gForestV3Visibility[i];
    saved_queued=queued;saved_ready=sCanopyReady;saved_cutoff=sCanopyCutoff;
    saved_body=queued_body;saved_mask=queued_mask;
    saved_body_dst=queued_body_dst;saved_mask_dst=queued_mask_dst;
    reset_guard();prepare_canopy_visibility(&a,frame);
    for(i=0;i<256;i++)if(saved_pixels[i]!=sCanopyPixels[i])goto fail;
    for(i=0;i<12;i++)if(saved_diag[i]!=gForestV3Visibility[i])goto fail;
    if(saved_queued!=queued || saved_ready!=sCanopyReady || saved_cutoff!=sCanopyCutoff ||
       saved_body!=queued_body || saved_mask!=queued_mask ||
       saved_body_dst!=queued_body_dst || saved_mask_dst!=queued_mask_dst)goto fail;
    return 1;
fail:
    printf("GUARD FAIL frame=%d at=%d,%d z=%d flip=%d priority=%d palette=%d state=%d hidden=%d flicker=%d\n",
           frame,px,py,z,flip,priority,palette,state,hidden,flicker);
    return 0;
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', default='/workspace/setup/performance/visibility-equivalence.json')
    args = parser.parse_args()
    out = Path(args.out).resolve()
    work = out.parent/'visibility-host'
    work.mkdir(parents=True, exist_ok=True)
    old = subprocess.check_output(['git', 'show', BASELINE+':bartgame/src/player.c'],
                                  cwd=GAME, text=True)
    reference = function(old, 'prepare_canopy_visibility').replace(
        'static void prepare_canopy_visibility(', 'static void reference_prepare_canopy_visibility(')
    old_trees = subprocess.check_output(['git', 'show', BASELINE+':bartgame/src/forest_trees.c'],
                                       cwd=GAME, text=True)
    ref_lower = function(old_trees, 'lower_box_ink').replace('lower_box_ink(', 'reference_lower_box_ink(')
    ref_depth = function(old_trees, 'forest_trees_priority').replace(
        'forest_trees_priority(', 'harness_reference_priority(').replace(
        'lower_box_ink(', 'reference_lower_box_ink(')
    old_room = subprocess.check_output(['git', 'show', BASELINE+':bartgame/src/room.c'],
                                      cwd=GAME, text=True)
    ref_overhead = function(old_room, 'overhead_at_body').replace('overhead_at_body(', 'reference_overhead_at_body(')
    ref_water = function(old_room, 'water_surface_at_body').replace('water_surface_at_body(', 'reference_water_surface_at_body(')
    ref_props = function(old_room, 'room_prop_priority').replace(
        'room_prop_priority(', 'harness_reference_room_priority(').replace(
        'overhead_at_body(', 'reference_overhead_at_body(').replace(
        'water_surface_at_body(', 'reference_water_surface_at_body(').replace(
        'forest_trees_priority(', 'harness_reference_priority(')
    (work/'driver.c').write_text(DRIVER)
    (work/'trees.c').write_text('#include "'+str(GAME/'src/forest_trees.c')+'"\n'+
                                ref_lower+'\n'+ref_depth+'\n'+TREE_EXTRA)
    (work/'player.c').write_text('#include "'+str(GAME/'src/player.c')+'"\n'+reference+'\n'+PLAYER_EXTRA)
    (work/'room.c').write_text('#include "'+str(GAME/'src/room.c')+'"\n'+
                              'extern int harness_reference_priority(int,int,int,int,int,int);\n'+
                              ref_overhead+'\n'+ref_water+'\n'+ref_props+'\n')
    command = ['gcc', '-O2', '-fno-builtin', '-fno-strict-aliasing', '-ffunction-sections', '-fdata-sections',
               '-Wno-attributes', '-Wno-pointer-to-int-cast', '-Wno-int-to-pointer-cast',
               '-I'+str(GAME/'src'), '-I'+str(GAME/'build/gen'),
               str(work/'driver.c'), str(work/'trees.c'), str(work/'player.c'),
               str(work/'room.c'), str(GAME/'src/forest_depth_iwram.c'), str(GAME/'build/gen/assets.c'),
               '-Wl,--gc-sections', '-o', str(work/'visibility')]
    result = subprocess.run(command, text=True, capture_output=True)
    (work/'compile.log').write_text(result.stdout+result.stderr)
    result.check_returncode()
    result = subprocess.run([str(work/'visibility')], text=True, capture_output=True)
    (work/'run.log').write_text(result.stdout+result.stderr)
    report = dict(method=__doc__.strip(), baseline_source=BASELINE,
                  passed=result.returncode==0, output=result.stdout,
                  source_sha256={str(p.relative_to(GAME)):hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in [GAME/'src/forest_trees.c', GAME/'src/forest_trees.h',
                                           GAME/'src/room.c', GAME/'src/room.h', GAME/'src/player.c',
                                           GAME/'src/forest_depth_iwram.c']},
                  compiler_command=command)
    counts=re.search(r'rows=(\d+) scalar_pixels=(\d+) native_guard_cases=(\d+) frames=(\d+) depth_cases=(\d+) prop_cases=(\d+) mutations=(\d+)', result.stdout)
    if counts:
        report['counts']=dict(zip(('row_queries','scalar_pixel_queries','native_guard_cases','hero_frames','depth_cases','prop_cases','mutations'),
                                  map(int, counts.groups())))
    out.write_text(json.dumps(report, indent=2)+'\n')
    print(result.stdout, end='')
    if result.stderr:
        print(result.stderr)
    result.check_returncode()


if __name__ == '__main__':
    main()

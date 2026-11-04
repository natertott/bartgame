#!/usr/bin/env python3
"""Differential host qualification for animation scheduling and torch caching.

The actual baseline/candidate animation C functions run against all three
linked ROM descriptor/payload sets and synthetic valid byte-sized descriptors.
Recorded DMA destinations, ordered bytes, palette writes and volatile clock
read counts must match. Explicit clock-read fixtures model wrap, reset and
interrupt changes between the due test and frame selection. These host tests
do not replace real mGBA progression, framebuffer or cycle measurements.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile

from perf_actor_equivalence import function, source
from sewer_concept_audit import NativeRom

GAME = Path(__file__).resolve().parents[1]
BASELINE = '11b872e9897320398fa02344cef1418733c04e9a'


def c_array(type_, name, data):
    return 'static const %s %s[%d]={%s};' % (type_, name, len(data), ','.join(str(v) for v in data))


def animation_test(args, directory):
    native = NativeRom(args.bundle)
    before = source(args.before_source, 'room.c')
    after = source(args.after_source, 'room.c')
    parts = ['''#include <stdio.h>
#undef NULL
#include "room.h"
#include "video.h"
#include "game.h"
GameState gGame;
u8 gAnimTiles;
static u16 destination[32768];
static unsigned events,clock_reads,iteration,read_in_iteration,read_changes,have_clock;
static u32 previous_clock;
static u32 first_tick[256],second_tick[256],fallback_tick;
typedef struct {unsigned kind,offset,size;u8 bytes[128];} Event;
static Event result[300],reference[300];
static u32 rnd_state=0xb4a76b1du;
static u32 rnd(void) {rnd_state^=rnd_state<<13;rnd_state^=rnd_state>>17;rnd_state^=rnd_state<<5;return rnd_state;}
static void test_iteration(int i) {iteration=i;read_in_iteration=0;}
static u32 test_clock(void) {
    u32 tick;
    clock_reads++;
    tick=iteration>=256?fallback_tick:read_in_iteration++?second_tick[iteration]:first_tick[iteration];
    if(have_clock && tick!=previous_clock)read_changes++;
    previous_clock=tick;have_clock=1;
    return tick;
}
static void test_dma(const void* src,volatile void* dst,u32 size) {
    unsigned i;const u8* p=src;Event* e=&result[events++];
    if(events>300 || size>128)__builtin_trap();
    e->kind=1;e->offset=(const volatile u8*)dst-(const volatile u8*)destination;e->size=size;
    for(i=0;i<size;i++)e->bytes[i]=p[i];
}
void pal_set_bg(int slot,const u16* src) {
    unsigned i;const u8* p=(const u8*)src;Event* e=&result[events++];
    if(events>300)__builtin_trap();
    e->kind=2;e->offset=slot*32;e->size=32;
    for(i=0;i<32;i++)e->bytes[i]=p[i];
}
void memset32(void* dst,u32 value,u32 bytes) {
    u32* p=dst;unsigned i;
    for(i=0;i<bytes/4;i++)p[i]=value;
}
#undef CHARBLOCK
#define CHARBLOCK(n) destination
#define dma3_copy32 test_dma
''']
    sets = []
    native_descriptors = []
    for index, name in enumerate(('sewer', 'forest', 'myst')):
        # Generated TS IDs, not a guessed order, select the actual area.
        index = native.defs['TS_'+name.upper()]
        ts = native.tileset(name)
        descriptors = []
        for j, row in enumerate(ts['animations']):
            label = 'data_%d_%d' % (index, j)
            parts.append(c_array('u16', label, struct.unpack('<%dH' % (len(row['data'])//2), row['data'])))
            descriptors.append('{%d,%d,%d,%s}' % (row['base'], row['frames'], row['speed'], label))
        parts.append('static const TileAnim animation_%d[%d]={%s};' % (index, len(descriptors), ','.join(descriptors)))
        sets.append('[%d]={0,0,0,animation_%d,%d,0,0}' % (index, index, len(descriptors)))
        native_descriptors.append(dict(area=name, index=index, descriptors=len(descriptors),
                                       speeds=sorted({r['speed'] for r in ts['animations']})))
    parts.append('const Tileset tilesets[TILESET_COUNT]={'+','.join(sets)+'};')
    slots = native.array('forest_v2_pulse_slots')
    colors = native.array('forest_v2_pulse_colors')
    parts.append('const u8 forest_v2_pulse_slots[TILESET_COUNT][FOREST_V2_PULSE_COUNT]={'+
                 ','.join('{'+','.join(str(v) for v in slots[i:i+native.defs['FOREST_V2_PULSE_COUNT']])+'}'
                          for i in range(0, len(slots), native.defs['FOREST_V2_PULSE_COUNT']))+'};')
    words = struct.unpack('<%dH' % (len(colors)//2), colors)
    banks = []
    for start in range(0, len(words), 64):
        banks.append('{'+','.join('{'+','.join(str(v) for v in words[start+phase*16:start+(phase+1)*16])+'}'
                                  for phase in range(4))+'}')
    parts.append('const u16 forest_v2_pulse_colors[FOREST_V2_PULSE_COUNT][4][16]={'+','.join(banks)+'};')
    parts.append('static const Tileset* sTs=&tilesets[0];')
    for prefix, text in [('before', before), ('after', after)]:
        body = function(text, 'tiles_animate').replace('tiles_animate(', prefix+'_tiles_animate(')
        body = re.sub(r'(for\s*\(i\s*=\s*0;\s*i\s*<\s*sTs->anim_count;\s*i\+\+\)\s*\{)',
                      r'\1\n        test_iteration(i);', body)
        body = re.sub(r'\bgFrame\b', 'test_clock()', body)
        parts.append(body)
    parts.append('''
static unsigned cases,dma_events,palette_events,synthetic_cases,observed_clock_changes,off_cases;
static void schedule(u32 base,int mode) {
    unsigned i;
    for(i=0;i<256;i++) {
        u32 first=base,second;
        if(mode==1 || mode==2)first+=i;
        else if(mode==3)first=(i%7==0)?0:rnd();
        else if(mode==4)first=0xfffffff0u+i;
        second=first;
        if(mode==2)second++;
        if(mode==3 && (i&1))second=rnd();
        first_tick[i]=first;second_tick[i]=second;
    }
    fallback_tick=base;
}
static void compare(u32 base,int mode,int synthetic) {
    unsigned i,j,n,old_reads,old_changes;
    schedule(base,mode);events=clock_reads=read_changes=have_clock=0;iteration=256;read_in_iteration=0;
    before_tiles_animate();n=events;old_reads=clock_reads;old_changes=read_changes;
    for(i=0;i<n;i++)reference[i]=result[i];
    events=clock_reads=read_changes=have_clock=0;iteration=256;read_in_iteration=0;
    after_tiles_animate();
    if(events!=n || old_reads!=clock_reads || old_changes!=read_changes) {
        printf("FAIL count case%u clock%u mode%d synthetic%d events%u/%u reads%u/%u\\n",cases,base,mode,synthetic,n,events,old_reads,clock_reads);__builtin_trap();
    }
    for(i=0;i<n;i++) {
        const Event *a=&reference[i],*b=&result[i];
        if(a->kind!=b->kind || a->offset!=b->offset || a->size!=b->size) {
            printf("FAIL event case%u event%u\\n",cases,i);__builtin_trap();
        }
        for(j=0;j<a->size;j++)if(a->bytes[j]!=b->bytes[j]) {
            printf("FAIL bytes case%u event%u byte%u clock%u mode%d synthetic%d\\n",cases,i,j,base,mode,synthetic);__builtin_trap();
        }
        if(a->kind==1)dma_events++;else palette_events++;
    }
    cases++;synthetic_cases+=synthetic;off_cases+=!gAnimTiles;observed_clock_changes+=old_changes;
}
int main(void) {
    static const u32 corners[]={0,1,2,3,7,8,15,16,31,32,63,64,127,128,255,256,65535,65536,0x7fffffffu,0x80000000u,0xfffffffeu,0xffffffffu};
    static u16 payload[256*64];
    static TileAnim mixed[255];Tileset synthetic={0};
    unsigned i,j,k,mode,speed,frames;
    for(i=0;i<256*64;i++)payload[i]=(i*7919u)^(i>>4)^0x6523;
    for(k=0;k<TILESET_COUNT;k++) {
        sTs=&tilesets[k];gGame.area=k==TS_SEWER?AREA_SEWER:k==TS_FOREST?AREA_FOREST:AREA_MYST;gGame.state=GS_PLAY;gAnimTiles=1;
        for(mode=0;mode<5;mode++) {
            for(i=0;i<2048;i++)compare(i,mode,0);
            for(i=0;i<512;i++)compare(rnd(),mode,0);
            for(i=0;i<sizeof(corners)/sizeof(corners[0]);i++)compare(corners[i],mode,0);
        }
        gAnimTiles=0;compare(0xffffffffu,2,0);gAnimTiles=1;
        gGame.state=GS_MAP;compare(128,0,0);
    }
    gGame.area=AREA_SEWER;gGame.state=GS_PLAY;gAnimTiles=1;
    synthetic.anims=mixed;synthetic.anim_count=1;sTs=&synthetic;
    for(speed=1;speed<256;speed++)for(frames=1;frames<256;frames++) {
        mixed[0]=(TileAnim){(speed+frames)%1020,frames,speed,payload};
        compare(speed*(frames+3),0,1);
        compare(speed*31,2,1); /* Includes speed1 clock advance between reads. */
        compare(0xffffffffu,3,1);
    }
    for(i=0;i<255;i++)mixed[i]=(TileAnim){(i*4)%1020,(i%11==0)?0:1+(i%255),i%11==0?0:1+(i%255),payload};
    synthetic.anim_count=255;
    for(mode=0;mode<5;mode++)for(j=0;j<2048;j++)compare(rnd(),mode,1);
    synthetic.anim_count=0;compare(0,0,1);
    printf("{\\"cases\\":%u,\\"synthetic_cases\\":%u,\\"dma_events\\":%u,\\"palette_events\\":%u,\\"clock_read_value_changes\\":%u,\\"disabled_animation_cases\\":%u,\\"passed\\":true}\\n",cases,synthetic_cases,dma_events,palette_events,observed_clock_changes,off_cases);
    return 0;
}
''')
    path = directory/'animation-test.c'
    path.write_text('\n'.join(parts))
    binary = directory/'animation-test'
    subprocess.run(['gcc', '-std=c99', '-O2', '-fno-builtin', '-Wno-pointer-to-int-cast',
                    '-I'+str(GAME/'src'), '-I'+str(Path(args.bundle)), str(path), '-o', str(binary)], check=True)
    result = json.loads(subprocess.check_output([str(binary)], text=True))
    result['native_descriptor_sets'] = native_descriptors
    result['frame_speed_pairs'] = 255*255
    result['zero_frame_descriptors_in_mixed_set'] = 24
    result['before_room_sha256'] = hashlib.sha256(before.encode()).hexdigest()
    result['after_room_sha256'] = hashlib.sha256(after.encode()).hexdigest()
    return result


def stack_usage(args, directory):
    compiler = shutil.which('arm-none-eabi-gcc')
    if not compiler:
        return dict(available=False, reason='ARM compiler is not on PATH; source activate.sh to collect static allocation.')
    rows = {}
    for label, revision in [('before', args.before_source), ('after', args.after_source)]:
        src = directory/(label+'-room.c')
        src.write_text(source(revision, 'room.c'))
        obj = directory/(label+'-room.o')
        command = [compiler, '-mcpu=arm7tdmi', '-mtune=arm7tdmi', '-mthumb', '-O2',
                   '-fomit-frame-pointer', '-ffunction-sections', '-fdata-sections',
                   '-fno-strict-aliasing', '-fno-builtin', '-nostdlib', '-fstack-usage',
                   '-I'+str(GAME/'src'), '-I'+str(Path(args.bundle)), '-c', str(src), '-o', str(obj)]
        subprocess.run(command, check=True, capture_output=True, text=True)
        text = obj.with_suffix('.su').read_text()
        match = re.search(r':tiles_animate\s+(\d+)\s+(\S+)', text)
        assert match, text
        rows[label] = dict(bytes=int(match.group(1)), compiler_kind=match.group(2))
    return dict(available=True, functions=rows,
                scope='Compiler-reported static tiles_animate stack allocation without profiling instrumentation; excludes callers, callees and interrupt stack.')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--before-source', default=BASELINE)
    ap.add_argument('--after-source', default='WORKTREE')
    ap.add_argument('--bundle', default='/workspace/setup/performance/before/bundle')
    ap.add_argument('--out', default='/workspace/setup/performance/system-equivalence.json')
    ap.add_argument('--skip-torches', action='store_true')
    args = ap.parse_args()
    with tempfile.TemporaryDirectory(prefix='system-equivalence-') as tmp:
        directory = Path(tmp)
        animation = animation_test(args, directory)
        stack = stack_usage(args, directory)
    report = dict(method=__doc__.strip(), before_source=args.before_source,
                  tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  native_rom_sha256=hashlib.sha256((Path(args.bundle)/'bartgame.gba').read_bytes()).hexdigest(),
                  after_source=args.after_source, animation=animation, animation_stack=stack)
    if not args.skip_torches:
        torch_out = str(Path(args.out).with_name('torch-equivalence.json'))
        subprocess.run([sys.executable, str(GAME/'tools/perf_torch_equivalence.py'),
                        '--before-source', args.before_source, '--after-source', args.after_source,
                        '--bundle', args.bundle, '--out', torch_out], check=True)
        report['torches'] = json.loads(Path(torch_out).read_text())
    report['passed'] = animation['passed'] and (args.skip_torches or report['torches']['passed'])
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(animation=animation, stack=stack, passed=report['passed'])))


if __name__ == '__main__':
    main()

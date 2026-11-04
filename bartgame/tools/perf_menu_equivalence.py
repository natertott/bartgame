#!/usr/bin/env python3
"""Exact native map/kit output tests for the small cold-menu optimizations.

Compile the actual old/new BG-map prefixes and kit-cache C functions. Compare
all1024 map entries, every ordered write, all four native kit flips, opacity
masks and glyph bit masks for the three linked frame styles. Palette roles
are tested across all16 banks; cache warm/cold behavior is retained. The real
nine style/color menu-frame comparison is a separate mGBA test.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import tempfile

from perf_actor_equivalence import function, source
from sewer_concept_audit import NativeRom

GAME = Path(__file__).resolve().parents[1]
BASELINE = '11b872e9897320398fa02344cef1418733c04e9a'


def map_prefix(text):
    body = function(text, 'ms_draw')
    start = body.index('for(i=0;i<32*32;i++)')
    end = body.index('if(sStudyBaseReady')
    body = body[start:end]
    return re.sub(r'gBg3\[(.*?)\]\s*=\s*(.*?);', r'put(\1,\2);', body, flags=re.S)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--before-source', default=BASELINE)
    ap.add_argument('--after-source', default='WORKTREE')
    ap.add_argument('--bundle', default='/workspace/setup/performance/before/bundle')
    ap.add_argument('--out', default='/workspace/setup/performance/menu-equivalence.json')
    args = ap.parse_args()
    native = NativeRom(args.bundle)
    before = source(args.before_source, 'menu.c')
    after = source(args.after_source, 'menu.c')
    kit_data = native.array('appearance_ui_tiles')
    kit_words = struct.unpack('<%dH' % (len(kit_data)//2), kit_data)
    c = ['''#include <stdio.h>
#undef NULL
#include "assets.h"
#define MS_TILES (30*20)
static unsigned bank,style,reads,writes;
#define UI_PAL bank
static u16 gBg3[1024],reference[1024];
typedef struct {unsigned at,value;} Write;
static Write trace[1624],old_trace[1624];
static void put(unsigned at,unsigned value) {if(at>=1024 || writes>=1624)__builtin_trap();trace[writes++]=(Write){at,value};gBg3[at]=value;}
const u16 appearance_ui_tiles[] ALIGN4={''', ','.join(str(v) for v in kit_words), '''};
const u16* ui_current_tiles(void) {reads++;return appearance_ui_tiles+style*UI_TILE_COUNT*16;}
static int same(const void* a,const void* b,unsigned n) {const u8* x=a;const u8* y=b;while(n--)if(*x++!=*y++)return 0;return 1;}
''']
    cache_names = ('sStudyKit', 'sStudyKitMask', 'sStudyBitMask', 'sStudyKitReady')
    for prefix, text in [('before', before), ('after', after)]:
        c.append('static void '+prefix+'_map(void) {int i,x,y;'+map_prefix(text)+'}')
        c += ['static u32 '+prefix+'_sStudyKit[4][UI_TILE_COUNT][8];',
              'static u32 '+prefix+'_sStudyKitMask[4][UI_TILE_COUNT][8];',
              'static u32 '+prefix+'_sStudyBitMask[256];',
              'static u8 '+prefix+'_sStudyKitReady;']
        body = function(text, 'ms_cache_kit').replace('ms_cache_kit(', prefix+'_ms_cache_kit(')
        for name in cache_names:
            body = re.sub(r'\b'+name+r'\b', prefix+'_'+name, body)
        c.append(body)
    c.append('''
int main(void) {
    unsigned i,old_writes,old_reads,map_cases=0,kit_cases=0,reads_avoided=0;
    for(bank=0;bank<16;bank++) {
        for(i=0;i<1024;i++)gBg3[i]=(i*7919u)^0x7342;
        writes=0;before_map();old_writes=writes;
        for(i=0;i<1024;i++){reference[i]=gBg3[i];gBg3[i]=(i*7919u)^0x7342;}
        for(i=0;i<old_writes;i++)old_trace[i]=trace[i];
        writes=0;after_map();
        if(writes!=1624 || old_writes!=writes || !same(old_trace,trace,sizeof(trace)) || !same(reference,gBg3,sizeof(reference))) {
            printf("FAIL map bank%u writes%u/%u\\n",bank,old_writes,writes);return 1;
        }
        map_cases++;
    }
    for(style=0;style<3;style++) {
        before_sStudyKitReady=after_sStudyKitReady=0;
        reads=0;before_ms_cache_kit();old_reads=reads;
        reads=0;after_ms_cache_kit();
        if(reads!=1 || old_reads!=4*UI_TILE_COUNT*8 ||
           !same(before_sStudyKit,after_sStudyKit,sizeof(before_sStudyKit)) ||
           !same(before_sStudyKitMask,after_sStudyKitMask,sizeof(before_sStudyKitMask)) ||
           !same(before_sStudyBitMask,after_sStudyBitMask,sizeof(before_sStudyBitMask)) ||
           before_sStudyKitReady!=after_sStudyKitReady) {
            printf("FAIL native kit style%u reads%u/%u\\n",style,old_reads,reads);return 2;
        }
        reads_avoided+=old_reads-reads;kit_cases++;
        reads=0;before_ms_cache_kit();after_ms_cache_kit();
        if(reads || !same(before_sStudyKit,after_sStudyKit,sizeof(before_sStudyKit)) ||
           !same(before_sStudyKitMask,after_sStudyKitMask,sizeof(before_sStudyKitMask)) ||
           !same(before_sStudyBitMask,after_sStudyBitMask,sizeof(before_sStudyBitMask)))return 3;
        kit_cases++;
    }
    printf("{\\"passed\\":true,\\"map_cases\\":%u,\\"ordered_map_writes_compared\\":%u,\\"native_kit_cases\\":%u,\\"native_frame_styles\\":3,\\"kit_lookup_calls_avoided\\":%u,\\"software_map_divisions_removed_per_redraw\\":1200}\\n",map_cases,map_cases*1624,kit_cases,reads_avoided);
    return 0;
}
''')
    with tempfile.TemporaryDirectory(prefix='menu-equivalence-') as tmp:
        directory = Path(tmp)
        src = directory/'test.c'
        src.write_text('\n'.join(c))
        binary = directory/'test'
        subprocess.run(['gcc', '-std=c99', '-O2', '-fno-builtin', '-fno-strict-aliasing', '-Wno-pointer-to-int-cast',
                        '-I'+str(GAME/'src'), '-I'+str(Path(args.bundle)), str(src), '-o', str(binary)], check=True)
        row = json.loads(subprocess.check_output([str(binary)], text=True))
    report = dict(method=__doc__.strip(), before_source=args.before_source, after_source=args.after_source,
                  tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  before_menu_sha256=hashlib.sha256(before.encode()).hexdigest(),
                  after_menu_sha256=hashlib.sha256(after.encode()).hexdigest(),
                  native_rom_sha256=hashlib.sha256(native.rom).hexdigest(), **row)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(row))


if __name__ == '__main__':
    main()

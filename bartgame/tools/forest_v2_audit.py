#!/usr/bin/env python3
"""Independent source/native/physical audit of forest concepts round two.

Direct painters supply expected 4bpp pixels. No asset packer, sprite assembler
or tile assembler is imported. Original release bytes, physical contracts,
conditional engine behavior, render aliases and actual captures are distinct
checks; diagnostic rooms are never represented as naturally generated rooms.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys

from sewer_concept_audit import NativeRom, decode_metatile, decode_sprite
from forest_concept_audit import native_image, native_palette, LEGAL_CANVASES
from enemy_study_audit import Audit as EnemyAudit, tokens

ROOT = Path(__file__).resolve().parents[1]
WORK = Path('/workspace/setup/forest-concepts-v2')
PREVIOUS = '69b69ba093a3e8a2cfc01fa5e657d2f53c592132'
PRODUCTION_SHA = '9330a44a4e27d99606a757134aa41a62adb122a74315c400e1ad3427048c8661'
BANKS = ('ground', 'foliage', 'water', 'stone', 'blight', 'decay_mix', 'rot_water')
SHA = lambda b: hashlib.sha256(b).hexdigest()
GLITTER = {'sparkle', 'sparkle_white'}
PORTRAITS = {'hermit', 'nun', 'gardener'}

HOST_CHECK = r'''
#include <stdio.h>
#include <stdlib.h>
#include "game.h"
#include "world.h"
#include "room.h"
#include "roomgen.h"
GameState gGame;
u32 gFrame;
/* Include the actual generator, allowing its existing non-render build path.
   No generator implementation or placement predicate is reproduced here. */
#include "ROOMGEN_SOURCE"
static unsigned char seen[4096];
static int queue[4096], failures, printed;
static unsigned long rooms, logs, pockets, requirements, worlds, arches;
static const int landing[4][2]={{15,2},{30,11},{15,22},{1,11}};
static void fail(unsigned seed,int cell,const char* reason,int x,int y) {
    failures++;
    if(printed++<24)printf("FAIL seed=%u cell=%d %s (%d,%d)\n",seed,cell,reason,x,y);
}
static unsigned graph_reach(int items) {
    unsigned seen=1u<<gWorld.entry;int changed=1,i,side;
    while(changed) {
        changed=0;
        for(i=0;i<CELLS;i++)if(seen&(1u<<i))for(side=0;side<4;side++) {
            int gate=gWorld.cells[i].gate[side],nx=i%5+(side==1)-(side==3),ny=i/5+(side==2)-(side==0),n;
            if(nx<0||ny<0||nx>=5||ny>=5)continue;
            n=ny*5+nx;
            if(gate==GATE_WALL||gate==GATE_LOCK||gate==GATE_EXIT||
               (gate==GATE_CRACK&&items<1)||(gate==GATE_WEB&&items<2)||(gate==GATE_CHASM&&items<3))continue;
            if(!(seen&(1u<<n))){seen|=1u<<n;changed=1;}
        }
    }
    return seen;
}
static void world_check(unsigned seed) {
    int item,cell,side;worlds++;
    for(item=0;item<3;item++) {
        int target=gWorld.key_cell[item];unsigned seen=graph_reach(item);
        if(!(seen&(1u<<target)))fail(seed,target,"mandatory prize blocked by future item/lock",item,0);
        if(seen&(1u<<gWorld.goal))fail(seed,gWorld.goal,"boss bypasses mandatory event",item,0);
        if(gWorld.cells[target].role!=ROLE_KEYITEM||gWorld.cells[target].role_arg!=item+1||!gWorld.myst[target])
            fail(seed,target,"mandatory task/reward missing",item,0);
        if(MYST_KIND(gWorld.myst[target])==MK_TORCHES||MYST_KIND(gWorld.myst[target])==MK_BOULDERS)
            fail(seed,target,"mandatory task needs unavailable optional equipment",item,0);
    }
    if(!(graph_reach(3)&(1u<<gWorld.goal)))fail(seed,gWorld.goal,"boss inaccessible with all three items",0,0);
    for(cell=0;cell<CELLS;cell++)for(side=0;side<4;side++) {
        int nx=cell%5+(side==1)-(side==3),ny=cell/5+(side==2)-(side==0);
        if(nx>=0&&ny>=0&&nx<5&&ny<5&&gWorld.cells[cell].gate[side]!=gWorld.cells[ny*5+nx].gate[(side+2)%4])
            fail(seed,cell,"asymmetric neighboring gates",side,0);
    }
}
static int blocked(int qx,int qy,int items) {
    int x=qx/2,y=qy/2,t;
    if(qx<0||qy<0||qx>=gRoom.w*2||qy>=gRoom.h*2)return 1;
    t=metatile_type[gRoom.ground[y*32+x]];
    if(t==TT_THORN||t==TT_LIFT1)return 0;
    if((items&1)&&t==TT_CRACK)return 0;
    if((items&2)&&t==TT_WEB)return 0;
    if((items&4)&&t==TT_PIT)return 0;
    if(t==TT_WATER||t==TT_PIT||t==TT_MYST||t==TT_EXIT)return 1;
    return gRoom.solid[qy*64+qx]!=0;
}
static void flood(int x,int y,int items) {
    int i,head=0,tail=0,dx,dy;
    static const int ax[4]={0,1,0,-1},ay[4]={-1,0,1,0};
    memset(seen,0,sizeof(seen));
    for(dy=0;dy<2;dy++)for(dx=0;dx<2;dx++) {
        int qx=x*2+dx,qy=y*2+dy,p=qy*64+qx;
        if(!blocked(qx,qy,items)&&!seen[p]){seen[p]=1;queue[tail++]=p;}
    }
    while(head<tail) {
        int p=queue[head++],qx=p%64,qy=p/64;
        for(i=0;i<4;i++) {
            int nx=qx+ax[i],ny=qy+ay[i],n=ny*64+nx;
            if(!blocked(nx,ny,items)&&!seen[n]){seen[n]=1;queue[tail++]=n;}
        }
    }
}
static int reaches(int x,int y) {
    if(x<0||y<0||x>=gRoom.w||y>=gRoom.h)return 0;
    return seen[y*2*64+x*2]||seen[y*2*64+x*2+1]||seen[(y*2+1)*64+x*2]||seen[(y*2+1)*64+x*2+1];
}
static void target(unsigned seed,int cell,const char*name,Spot p,int offset) {
    requirements++;
    if(!reaches(p.x,p.y+offset))fail(seed,cell,name,p.x,p.y+offset);
}
static void inspect(unsigned seed,int cell) {
    Cell* c=&gWorld.cells[cell];int side,start=-1,i,x,y;
    for(side=0;side<4;side++)if(c->gate[side]){start=side;break;}
    if(start<0){fail(seed,cell,"no room entrance",0,0);return;}
    room_build_solid();flood(landing[start][0],landing[start][1],0);
    for(side=0;side<4;side++)if(c->gate[side]&&!reaches(landing[side][0],landing[side][1]))
        fail(seed,cell,"door landing disconnected",landing[side][0],landing[side][1]);
    if(gSpots.has_chest)target(seed,cell,"chest approach",gSpots.chest,1);
    if(gSpots.has_npc)target(seed,cell,"NPC approach",gSpots.npc,1);
    if(gSpots.has_relic)target(seed,cell,"relic approach",gSpots.relic,0);
    if(gSpots.has_boss)target(seed,cell,"boss approach",gSpots.boss,0);
    if(gSpots.has_shrine)target(seed,cell,"shrine approach",gSpots.shrine,1);
    if(gSpots.has_mouth)target(seed,cell,"mouth approach",gSpots.mouth,1);
    if(c->role==ROLE_KEYITEM&&!gSpots.has_mouth)fail(seed,cell,"mandatory event has no mouth",0,0);
    if(c->role==ROLE_NPC_TORCH&&gSpots.torch_count!=4)fail(seed,cell,"torch quest count",0,0);
    for(i=0;i<gSpots.torch_count;i++)target(seed,cell,"torch approach",gSpots.torches[i],1);
    for(i=0;i<gSpots.spawn_count;i++)target(seed,cell,"spawn approach",gSpots.spawns[i],0);
    /* A two-cell log has two occupied cells, actual collision under both,
       and a safe original floor. This checks resulting geometry, not the
       generator's candidate/placement condition. */
    for(y=0;y<gRoom.h;y++)for(x=0;x<gRoom.w;x++) {
        int at=y*32+x,mt=gRoom.ground[at];
        if(mt==MT_HLOG_0) {
            int j;logs++;
            if(x+1>=gRoom.w||gRoom.ground[at+1]!=MT_HLOG_1)fail(seed,cell,"incomplete large log",x,y);
            for(j=0;j<2;j++) {
                int u=gRoom.underlay[at+j],dx,dy;
                if(metatile_coll[u]||metatile_type[u]==TT_WATER||metatile_type[u]==TT_PIT)
                    fail(seed,cell,"log substrate is not dry passable ground",x+j,y);
                for(dy=0;dy<2;dy++)for(dx=0;dx<2;dx++)
                    if(!gRoom.solid[(y*2+dy)*64+(x+j)*2+dx])
                        fail(seed,cell,"large log collision misses visible cell",x+j,y);
            }
        }
        if(mt==MT_HLOG_1&&(x<1||gRoom.ground[at-1]!=MT_HLOG_0))fail(seed,cell,"orphan large log half",x,y);
        if(gRoom.overlay[at]==MT_F2_ARCH_0) {
            int j;arches++;
            if(x+1>=gRoom.w||gRoom.overlay[at+1]!=MT_F2_ARCH_1)fail(seed,cell,"incomplete overhead arch",x,y);
            for(j=0;j<2;j++) {
                int ground=gRoom.ground[at+j],dx,dy;
                if(metatile_coll[ground]||metatile_type[ground]==TT_WATER||metatile_type[ground]==TT_PIT)
                    fail(seed,cell,"underpass visible lane is not actually passable",x+j,y);
                for(dy=0;dy<2;dy++)for(dx=0;dx<2;dx++)
                    if(gRoom.solid[(y*2+dy)*64+(x+j)*2+dx])fail(seed,cell,"underpass quarter is blocked",x+j,y);
            }
        }
        if(gRoom.overlay[at]==MT_F2_ARCH_1&&(x<1||gRoom.overlay[at-1]!=MT_F2_ARCH_0))fail(seed,cell,"orphan overhead arch half",x,y);
    }
    if(gSpots.has_treasure&&gSpots.pocket_kind>=1&&gSpots.pocket_kind<=3) {
        int item=1<<(gSpots.pocket_kind-1),opened=c->opened&CELL_POCKET_OPEN;
        Spot p=gSpots.treasure;pockets++;
        if(!opened&&reaches(p.x,p.y))fail(seed,cell,"item pocket bypassable with no future item",p.x,p.y);
        flood(landing[start][0],landing[start][1],item);
        if(!reaches(p.x,p.y))fail(seed,cell,"pocket inaccessible with its required item",p.x,p.y);
        flood(landing[start][0],landing[start][1],7^item);
        if(!opened&&reaches(p.x,p.y))fail(seed,cell,"pocket accepts wrong items",p.x,p.y);
    }
}
int main(int argc,char**argv) {
    unsigned seed,count=argc>1?strtoul(argv[1],0,0):20000;int cell,profile;
    gGame.area=AREA_FOREST;gGame.state=GS_PLAY;
    for(seed=1;seed<=count;seed++) {
        for(profile=0;profile<WORLD_PROFILE_COUNT;profile++) {
            world_generate_tuned(seed,&world_profiles[profile]);world_check(seed);
        }
        world_generate(seed);
        for(cell=0;cell<CELLS;cell++) {
            gGame.cell=cell;roomgen_build_internal(cell,FALSE);inspect(seed,cell);rooms++;
        }
        if(seed%500==0){printf("PROGRESS seeds=%u rooms=%lu failures=%d\n",seed,rooms,failures);fflush(stdout);}
        if(failures>100)break;
    }
    printf("RESULT {\"requested_seeds\":%u,\"seeds\":%lu,\"world_graphs\":%lu,\"rooms\":%lu,\"logs\":%lu,\"underpasses\":%lu,\"item_pockets\":%lu,\"required_approaches\":%lu,\"failures\":%d}\n",count,rooms/CELLS,worlds,rooms,logs,arches,pockets,requirements,failures);
    return failures?1:0;
}
'''


def valid_adjacencies():
    """A concave corner exists only between two connected cardinal sides."""
    touching = (9, 3, 6, 12)  # NW, NE, SE, SW; cardinal N/E/S/W bits.
    return [(m, c) for m in range(16) for c in range(16)
            if all(not(c & (1 << q)) or not(m & sides)
                   for q, sides in enumerate(touching))]


def direct_export(profile, inventory):
    assert 6 <= profile <= 10
    v = profile-5
    os.environ['BART_FOREST'] = str(profile)
    sys.path.insert(0, str(ROOT/'art'))
    import forest_concepts_v2_terrain as terrain
    import forest_concepts_v2_props as props
    import forest_concepts_v2_folk as folk
    inv = json.loads(Path(inventory).read_text())
    bg = dict(inv['palettes']['bg'])
    bg.update({n: terrain.palette(n, v) for n in BANKS})
    bg.update({n: list(c) for n, c in props.BG_PALETTE_ALIASES.items()})
    out = {'profile': profile, 'local_variant': v, 'tiles': {}, 'sprites': {},
           'bg_palettes': {n: native_palette(p) for n, p in bg.items()},
           'pulse_palettes': {n: [native_palette(p) for p in phases]
                              for n, phases in terrain.pulse_palettes(v).items()},
           'pulse_indices': {n: list(i) for n, i in terrain.PULSE_INDICES.items()},
           'portrait_palettes': {}, 'topology': []}
    def emit(name, images, bank, **spec):
        out['tiles'][name] = {'frames': [native_image(im, (16, 16)).hex() for im in images],
                              'bank': bank, **spec}
    for spec in inv['tiles']:
        name = spec['name']
        if name not in inv['required']['bg_names'] or name in GLITTER:
            continue
        a, b = props.supports_tile(name), terrain.supports(name)
        assert a != b, ('exactly one direct painter required', name, a, b)
        frames = [(props.paint_tile if a else terrain.paint)(name, phase, v)
                  for phase in range(spec['frames'])]
        assert len({bank for _, bank in frames}) == 1
        emit(name, [im for im, _ in frames], frames[0][1], parent=name,
             owner='props' if a else 'terrain', visual_only=False)
    # Alias names/semantics are derived independently from the public contract;
    # the production append() assembler is deliberately never called.
    assert len(valid_adjacencies()) == 47
    for kind, parent in enumerate(('canopy', 'blight_wall')):
        for quadrant in range(4):
            for mask, corners in valid_adjacencies():
                name = f'f2_canopy_{kind}_{quadrant}_{mask:x}{corners:x}'
                im, bank = terrain.paint_adjacency(parent+'@q'+str(quadrant), mask, corners, 0, v)
                record = dict(name=name, parent=parent, family='canopy', kind=kind+1,
                              quadrant=quadrant, mask=mask, corners=corners, visual_only=True)
                emit(name, [im], bank, **{k: value for k, value in record.items() if k != 'name'})
                out['topology'].append(record)
        for mask in range(1, 16):
            name = f'f2_fringe_{kind}_{mask:x}'
            im, bank = terrain.fringe(parent, mask, v)
            record = dict(name=name, parent='moss0', family='fringe', kind=kind+1,
                          mask=mask, visual_only=True, glitter=0)
            emit(name, [im], bank, **{k: value for k, value in record.items() if k != 'name'})
            out['topology'].append(record)
    specs = {t['name']: t for t in inv['tiles']}
    for mask,corners in valid_adjacencies():
        frames=[terrain.paint_adjacency('water',mask,corners,phase,v) for phase in range(2)]
        name=f'f2_water_{mask:x}{corners:x}'
        record=dict(name=name,parent='water',family='water',mask=mask,corners=corners,visual_only=True)
        emit(name,[im for im,_ in frames],frames[0][1],**{k:value for k,value in record.items() if k!='name'})
        out['topology'].append(record)
    for parent in ('water_lily', 'water_foam'):
        frames = [terrain.paint_adjacency(parent, 15, 0, phase, v)
                  for phase in range(specs[parent]['frames'])]
        name = f'f2_{parent}_isolated'
        record = dict(name=name, parent=parent, family='isolated_water', mask=15,
                      corners=0, visual_only=True)
        emit(name, [im for im, _ in frames], frames[0][1], **{k: value for k, value in record.items() if k != 'name'})
        out['topology'].append(record)
    arch, bank = terrain.arch_group(v)
    native_image(arch, (32, 16))
    for part in range(2):
        name = 'f2_arch_'+str(part)
        record = dict(name=name, parent='moss0', family='overhead_root_arch',
                      part=part, visual_only=False, glitter=1)
        emit(name, [arch.crop((part*16, 0, part*16+16, 16))], bank,
             **{k: value for k, value in record.items() if k != 'name'})
        out['topology'].append(record)
    # A pool's exterior must reveal its actual floor, rather than smuggling
    # a palette-colored 16px rectangle into dirt or corrupted grass.
    edge=[y*16+x for y in range(16) for x in range(16) if x in (0,15) or y in (0,15)]
    for name in ('water_f','f2_water_f0','f2_water_lily_isolated','f2_water_foam_isolated'):
        for phase,pixels in enumerate(out['tiles'][name]['frames']):
            values=bytes.fromhex(pixels)
            assert all(values[i]==0 for i in edge),(name,phase,'isolated pool exterior must be transparent')
            assert any(values), (name,phase,'pool body disappeared')
    sheets = {s['name']: s for s in inv['sheets']}
    need = inv['required']['sprite_frames'] + inv['required']['conditional_shared_lift_frames']
    need += [{'sheet': 'interactivechest', 'frame': n} for n in ('wooden_b_closed', 'wooden_b_open')]
    need += [{'sheet': 'forestlandmark', 'frame': n} for n in ('relic', 'shrine_available', 'shrine_spent', 'keylock')]
    for item in need:
        sheet, name = item['sheet'], item['frame']
        size = [16, 32] if sheet == 'forestlandmark' else sheets[sheet]['canvas']
        if sheet == 'face':
            image = folk.portrait(name, v); small = native_image(image, (48, 48))
            pixels = bytearray(4096)
            for y in range(48):pixels[y*64:y*64+48] = small[y*48:(y+1)*48]
            bank = 'portrait'
            out['portrait_palettes'][name] = native_palette(folk.portrait_palette(name, v))
        else:
            a, b = props.supports_frame(sheet, name), folk.supports_frame(sheet, name)
            assert a != b, ('exactly one sprite painter', sheet, name, a, b)
            image, bank = (props.paint_frame if a else folk.frame)(sheet, name, v)
            pixels = native_image(image, size)
        out['sprites'].setdefault(sheet, {})[name] = {'pixels': bytes(pixels).hex(),
                                                      'bank': bank, 'canvas': size}
    print(json.dumps(out, separators=(',', ':')))


class Audit:
    def __init__(self, args):
        self.args = args; self.rows = []; self.profiles = []; self.budgets = []
        self.inv = json.loads(Path(args.inventory).read_text())
        self.specs = {t['name']: t for t in self.inv['tiles']}
        self.base = NativeRom(args.baseline)

    def check(self, v, group, name, ok, detail=None):
        row = dict(variant=v, group=group, name=name, passed=bool(ok))
        if detail is not None:row['detail'] = detail
        self.rows.append(row)
        if not ok:print('FAIL', v, group, name, detail, flush=True)

    def equal(self, v, group, name, a, b):
        self.check(v, group, name, a == b, None if a == b else
                   dict(expected_sha256=SHA(a), actual_sha256=SHA(b), expected_bytes=len(a), actual_bytes=len(b)))

    def source_scope(self):
        integrations={'art/tiles.py','art/sprites.py','art/palettes.py','art/faces.py','art/forest_concepts.py'}
        engine={'src/room.c','src/room.h','src/roomgen.c','src/interactive.c','src/interactive.h','src/video.c',
                'src/player.c','src/player.h','src/actor.c'}
        # The only permitted Bloom/actor source edits are new conditional
        # presentation blocks. Projecting out those reviewed blocks must give
        # exactly the prior source tokens, protecting every original movement,
        # damage, item-use, collision and sword timing function wholesale.
        for rel in ('src/player.c','src/player.h','src/actor.c'):
            current=(ROOT/rel).read_text()
            projected=re.sub(r'^\s*#if BART_FOREST_VARIANT >= 6\s*\n.*?^\s*#endif\s*$', '',current,flags=re.M|re.S)
            previous=subprocess.check_output(['git','show',PREVIOUS+':bartgame/'+rel],cwd=ROOT,text=True)
            self.check('source','scope',rel+' all non-V2 presentation tokens exact',tokens(projected)==tokens(previous))
        paths=subprocess.check_output(['git','ls-tree','-r','--name-only',PREVIOUS,'bartgame/art','bartgame/src'],cwd=ROOT.parent,text=True).splitlines()
        for name in paths:
            rel=name.removeprefix('bartgame/')
            if rel in integrations or rel in engine:continue
            old=subprocess.check_output(['git','show',PREVIOUS+':'+name],cwd=ROOT.parent)
            actual=ROOT/rel
            self.check('source','scope',rel+' preserved file exists',actual.is_file())
            if actual.is_file():self.equal('source','scope',rel+' complete protected source bytes',old,actual.read_bytes())
        # Chest presentation may hash a location; it must not advance loot RNG.
        chest=(ROOT/'src/interactive.c').read_text()
        self.check('source','scope','interactive presentation never calls a mutable RNG',
                   not re.search(r'\b(?:rand_next|rand_range|rng_next|rng_range)\s*\(',chest))
        make=(ROOT/'Makefile').read_text()
        for key,number in [('BART_FOREST',0),('BART_ENEMY',11),('BART_UI',6),('BART_MENU',1),('BART_SEWER',9),('BART_SWING',3)]:
            self.check('source','defaults',key+' normal build default',bool(re.search(r'^'+key+r'\s*\?=\s*'+str(number)+r'\s*$',make,re.M)))
        self.check('source','baseline','production baseline SHA9330a44a',SHA(self.base.rom)==PRODUCTION_SHA)

    def provenance(self,v,rom,freeze):
        self.check(v,'freeze','ROM hash bound to freeze',freeze['rom_sha256']==SHA(rom.rom))
        self.check(v,'freeze','profile header matches directory',rom.defs['BART_FOREST_VARIANT']==v)
        for key,number in [('BART_ENEMY_VARIANT',11),('BART_UI_VARIANT',6),('BART_MENU_VARIANT',1),('BART_SEWER_VARIANT',9),('BLOOM_SWING_STUDY',3)]:
            self.check(v,'freeze',key+' selected context preserved',rom.defs.get(key)==number)
        for section in ('source_file_sha256','code_file_sha256'):
            self.check(v,'freeze',section+' complete record present',bool(freeze.get(section)))
            for rel,expected in freeze.get(section,{}).items():
                path=ROOT/rel
                self.check(v,'freeze',rel+' live input matches freeze',path.is_file() and SHA(path.read_bytes())==expected)
                original=subprocess.check_output(['git','show',freeze['source_commit']+':bartgame/'+rel],cwd=ROOT)
                self.check(v,'freeze',rel+' committed input matches freeze',SHA(original)==expected)

    def host_generator(self, variant=6, seeds=20000):
        """Compile real C generation/room semantics with frozen ROM metadata.

        Only video submission is suppressed. Independent flood-fill validates
        resulting room geometry, required approaches and item-gated pockets.
        Native metadata is decoded from the frozen ROM, not regenerated by the
        art packer. This is a host logic test, never an emulator capture.
        """
        rom=NativeRom(Path(self.args.frozen)/f'v{variant}')
        directory=Path(self.args.out).parent/'host'/f'v{variant}'
        directory.mkdir(parents=True,exist_ok=True)
        main=directory/'generator-check.c'
        main.write_text(HOST_CHECK.replace('ROOMGEN_SOURCE',str(ROOT/'src/roomgen.c')))
        wrapper=directory/'room-logic.c'
        wrapper.write_text('#define room_render qa_unused_hardware_room_render\n#include "'+str(ROOT/'src/room.c')+'"\n#undef room_render\nvoid room_render(void) {}\n')
        # Emit only native scalar arrays required by the real host logic.
        # Header types/dimensions are preserved even for multidimensional data.
        arrays=['#include "assets.h"']
        declared=re.findall(r'extern\s+const\s+(u8|u16)\s+(\w+)\s*((?:\[[^\]]*\])+)[ \t]*;',rom.header)
        for kind,name,dims in declared:
            if name not in rom.sections or not (name.startswith('metatile_') or name.startswith('forest_v2_')):continue
            data=rom.array(name)
            values=list(data) if kind=='u8' else struct.unpack('<%dH'%(len(data)//2),data)
            arrays.append('const %s %s%s = {%s};'%(kind,name,dims,','.join(map(str,values))))
        metadata=directory/'native-metadata.c';metadata.write_text('\n'.join(arrays)+'\n')
        binary=directory/'generator-check'
        command=['gcc','-O2','-fno-builtin','-w','-ffunction-sections','-fdata-sections',
                 '-I',str(ROOT/'src'),'-I',str(rom.directory),str(main),str(wrapper),
                 str(ROOT/'src/world.c'),str(ROOT/'src/util.c'),str(metadata),
                 '-Wl,--gc-sections','-o',str(binary)]
        build=subprocess.run(command,cwd=ROOT,text=True,capture_output=True)
        (directory/'compile.log').write_text(build.stdout+build.stderr)
        self.check(variant,'host_generator','actual C host harness compiles',build.returncode==0,
                   None if build.returncode==0 else build.stderr[-8000:])
        if build.returncode:return {'passed':False,'compile_log':str(directory/'compile.log')}
        with (directory/'run.log').open('w') as stream:
            result=subprocess.run([str(binary),str(seeds)],stdout=stream,stderr=subprocess.STDOUT,cwd=ROOT)
        output=(directory/'run.log').read_text()
        final=re.findall(r'^RESULT (\{[^\n]+\})$',output,re.M)
        stats=json.loads(final[-1]) if final else {}
        self.check(variant,'host_generator','all requested seeds/rooms checked',stats.get('seeds')==seeds and stats.get('rooms')==seeds*25,stats)
        self.check(variant,'host_generator','required routes/pockets/log footprints pass',result.returncode==0 and stats.get('failures')==0,stats)
        self.check(variant,'host_generator','allthree tuning graphs and nonvacuous log/pocket coverage',
                   stats.get('world_graphs')==seeds*3 and stats.get('logs',0)>0 and stats.get('item_pockets',0)>0 and stats.get('underpasses',0)>0,stats)
        record={'method':self.host_generator.__doc__.strip(),'variant':variant,'rom_sha256':SHA(rom.rom),
                'source_commit':json.loads((rom.directory/'freeze.json').read_text())['source_commit'] if (rom.directory/'freeze.json').exists() else None,
                'compiler':subprocess.check_output(['gcc','--version'],text=True).splitlines()[0],
                'command':command,'harness_sha256':SHA(main.read_bytes()),'wrapper_sha256':SHA(wrapper.read_bytes()),
                'native_metadata_sha256':SHA(metadata.read_bytes()),'binary_sha256':SHA(binary.read_bytes()),
                'source_sha256':{str(p.relative_to(ROOT)):SHA(p.read_bytes()) for p in
                                 (ROOT/'src/roomgen.c',ROOT/'src/room.c',ROOT/'src/world.c',ROOT/'src/util.c')},
                'statistics':stats,'exit_code':result.returncode,'run_log':str(directory/'run.log')}
        (directory/'report.json').write_text(json.dumps(record,indent=2)+'\n')
        return record

    def native(self, v, rom, source):
        counts = {}; changes = 0
        for bank in (*BANKS,'forest_obj_foliage','forest_obj_stone'):
            slot=rom.defs['PAL_BG_'+bank.upper()]
            self.equal(v,'native_palette',bank+' complete authored global bank',
                       struct.pack('<16H',*source['bg_palettes'][bank]),rom.array('pal_bg')[slot*32:(slot+1)*32])
        self.check(v, 'direct_coverage', 'all 461 retained owned IDs plus direct topology aliases',
                   set(source['tiles']) == (set(self.inv['required']['bg_names'])-GLITTER) |
                   {r['name'] for r in source['topology']})
        old_names = set(self.base.tile_ids)
        appended = {n.upper() for n in source['tiles'] if n.upper() not in old_names}
        self.check(v, 'identifiers', 'only approved new metatile IDs appended', set(rom.tile_ids)-old_names == appended)
        for offset,alias in enumerate(source['topology']):
            self.check(v,'identifiers',alias['name']+' stable append-order ID',
                       rom.tile_ids[alias['name'].upper()]==self.base.defs['METATILE_COUNT']+offset)
        for name, number in self.base.tile_ids.items():
            self.check(v, 'identifiers', name+' old ID stable', rom.tile_ids.get(name) == number)
        for field, key in [('metatile_type','type_id'), ('metatile_coll','coll'), ('metatile_prop','prop'), ('metatile_glitter','glitter')]:
            before, current = self.base.array(field), rom.array(field)
            self.equal(v, 'physical', field+' complete original prefix exact', before, current[:len(before)])
            for alias in source['topology']:
                index = rom.tile_ids[alias['name'].upper()]; parent = self.base.tile_ids[alias['parent'].upper()]
                expected = alias.get('glitter', before[parent]) if field == 'metatile_glitter' else before[parent]
                self.check(v, 'physical_alias', alias['name']+'.'+field+' semantic parent', current[index] == expected)
        overhead=rom.array('forest_v2_overhead')
        lowfringe=rom.array('forest_v2_low_fringe')
        parents=None
        if 'forest_v2_visual_parent' in rom.sections:
            data=rom.array('forest_v2_visual_parent');parents=struct.unpack('<%dH'%(len(data)//2),data)
        else:
            # This generated documentation table has no C consumer and is
            # garbage-collected. Physical semantics are checked against the
            # parent's actual native type/collision/prop/glitter words above.
            referenced=any('forest_v2_visual_parent' in p.read_text() for p in (ROOT/'src').glob('*.c'))
            self.check(v,'native_lookup','unlinked parent metadata has no gameplay consumer',not referenced,
                       'Unused generated table removed by linker; no native payload is claimed.')
        for alias in source['topology']:
            index=rom.tile_ids[alias['name'].upper()]
            if parents is not None:
                self.check(v,'physical_alias',alias['name']+' exact visual semantic parent lookup',parents[index]==rom.tile_ids[alias['parent'].upper()])
            self.check(v,'physical_alias',alias['name']+' correct foreground/depth classification',
                       overhead[index]==int(alias['family'] in ('canopy','fringe','overhead_root_arch')))
            self.check(v,'physical_alias',alias['name']+' low-fringe presentation flag',lowfringe[index]==int(alias['family']=='fringe'))
        def eligible(mask):
            return sum((1<<q) for q,sides in enumerate((9,3,6,12)) if not(mask&sides))
        canopy=[]
        for kind in range(2):
            for quadrant in range(4):
                for mask in range(16):
                    for corners in range(16):
                        canopy.append(rom.tile_ids[f'F2_CANOPY_{kind}_{quadrant}_{mask:X}{corners&eligible(mask):X}'])
        self.equal(v,'native_lookup','all2048canopy topology table entries independently resolved',
                   struct.pack('<2048H',*canopy),rom.array('forest_v2_canopy_alias'))
        water=[rom.tile_ids[f'F2_WATER_{m:X}{c&eligible(m):X}'] for m in range(16) for c in range(16)]
        self.equal(v,'native_lookup','all256water topology table entries independently resolved',struct.pack('<256H',*water),rom.array('forest_v2_water_alias'))
        fringe=[65535 if m==0 else rom.tile_ids[f'F2_FRINGE_{kind}_{m:X}'] for kind in range(2) for m in range(16)]
        self.equal(v,'native_lookup','all32fringe table entries independently resolved',struct.pack('<32H',*fringe),rom.array('forest_v2_fringe_alias'))
        self.equal(v,'native_lookup','two isolated specialwater bindings',
                   struct.pack('<2H',rom.tile_ids['F2_WATER_LILY_ISOLATED'],rom.tile_ids['F2_WATER_FOAM_ISOLATED']),rom.array('forest_v2_water_isolated'))
        healthy={'canopy','canopy2','canopy_s','canopy_n','canopy_lantern','canopy_glint',*(f'forest_canopy{i}' for i in range(4))}
        sick={'canopy_blight','canopy_blight2','blight_wall','blight_wall2','blight_wall_lit'}
        connectors={f'forest_blight_tree{i}' for i in range(6)}
        ordered=[n.lower() for n,i in sorted(rom.tile_ids.items(),key=lambda r:r[1])]
        classes=bytes(1 if n in healthy else 2 if n in sick else 3 if n in connectors else 0 for n in ordered)
        self.equal(v,'native_lookup','complete logical canopy/connector classification',classes,rom.array('forest_v2_canopy_kind'))
        waterclasses=bytes(2 if n=='water_lily' else 3 if n=='water_foam' else
                           1 if n=='water' or n.startswith('water_') else
                           4 if n in ('waterfall','bridge','bridge_v') or n.startswith('raft_') else 0 for n in ordered)
        self.equal(v,'native_lookup','complete logical water/connectivity classification',waterclasses,rom.array('forest_v2_water_kind'))
        special=bytes(int(n in connectors or n in ('dead_tree','forest_blight_dead_tree')) for n in ordered)
        self.equal(v,'native_lookup','all special tree bindings',special,rom.array('forest_v2_special_tree'))
        crowns=set()
        for group in self.inv['groups']:
            if group['role']=='tree':
                count=9 if len(group['members'])==12 else 4
                crowns.update(group['members'][:count])
        self.check(v,'native_lookup','alloriginal authored tree crown depth flags',
                   all(overhead[i]==int(n.lower() in crowns) for n,i in self.base.tile_ids.items()))
        self.equal(v,'native_lookup','original IDs never acquire low-fringe exception',bytes(self.base.defs['METATILE_COUNT']),lowfringe[:self.base.defs['METATILE_COUNT']])
        if parents is not None:
            self.check(v,'native_lookup','alloriginal IDs retain identity semantic lookup',all(parents[i]==i for i in range(self.base.defs['METATILE_COUNT'])))
        for area in ('forest','myst'):
            ts = rom.tileset(area); frames = 0
            for name, authored in source['tiles'].items():
                # Original membership is independently frozen. New render-only
                # topology pictures are forest-local unless explicitly mapped.
                if name in self.specs and area not in self.specs[name]['areas']:continue
                if name not in self.specs and area != 'forest':continue
                decoded = decode_metatile(rom, ts, name)
                parent = self.specs[authored['parent']]
                self.check(v, 'native', area+'.'+name+' frame count', len(decoded['frames']) == len(authored['frames']))
                speed = parent['anim_speed'] if len(authored['frames']) > 1 else None
                self.check(v, 'native', area+'.'+name+' declared clock', decoded['speed'] == speed)
                palette = source['bg_palettes'][authored['bank']]
                for q, entry in enumerate(decoded['entries']):
                    bank = entry >> 12
                    self.equal(v, 'material', area+'.'+name+' quadrant'+str(q)+' exact bank',
                               struct.pack('<16H',*palette), ts['palettes'][bank*32:(bank+1)*32])
                for phase, (expected, (indices, colors)) in enumerate(zip(authored['frames'],decoded['frames'])):
                    pixels = bytes.fromhex(expected); label = area+'.'+name+':'+str(phase)
                    self.equal(v, 'native', label+' direct pixels vs ROM nibbles', pixels, indices)
                    self.equal(v, 'native', label+' direct RGB555 base material',
                               struct.pack('<256H',*[palette[p] if p else 0x8000 for p in pixels]), colors)
                    frames += 1
            counts[area] = frames
        owned = {(s,f) for s, frames in source['sprites'].items() for f in frames}
        for sheet, images in source['sprites'].items():
            meta, raw = rom.sheet(sheet); stride = meta['frame_tiles']*32
            for name, image in images.items():
                index = rom.defs['F_'+sheet.upper()+'_'+name.upper()]
                actual = decode_sprite(raw[index*stride:(index+1)*stride],meta['width'],meta['height'])
                self.equal(v, 'native_sprite', sheet+'.'+name+' direct pixels', bytes.fromhex(image['pixels']), actual)
                self.check(v, 'native_sprite', sheet+'.'+name+' legal canvas', image['canvas'] == [meta['width'],meta['height']] and tuple(image['canvas']) in LEGAL_CANVASES)
                if sheet == 'face':
                    self.equal(v, 'portrait_palette', name+' direct native palette',
                               struct.pack('<16H',*source['portrait_palettes'][name]),rom.array('pal_face')[index*32:(index+1)*32])
                else:
                    route = rom.array(sheet+'_frame_pal')[index] if sheet+'_frame_pal' in rom.sections else meta['pal']
                    self.check(v, 'sprite_material', sheet+'.'+name+' direct OBJ route', route == rom.defs['PAL_OBJ_'+image['bank'].upper()])
        for sheet in self.inv['sheets']:
            name = sheet['name']; a, old = self.base.sheet(name); b, raw = rom.sheet(name)
            expected = dict(a)
            if name == 'interactivechest':expected['tile_count'] += a['frame_tiles']*2
            self.check(v, 'sprite_contract', name+' exact canvas/shape/approved count', expected == b)
            stride = a['frame_tiles']*32
            for frame in sheet['frames']:
                if (name, frame['name']) not in owned:
                    i = frame['id']; self.equal(v, 'protected_sprite', name+'.'+frame['name']+' exact pixels', old[i*stride:(i+1)*stride],raw[i*stride:(i+1)*stride])
                self.check(v, 'identifiers', name+'.'+frame['name']+' original frame ID stable',rom.defs['F_'+name.upper()+'_'+frame['name'].upper()] == frame['id'])
        self.check(v, 'identifiers', 'only appended landmark sheet', set(rom.sheet_ids)-set(self.base.sheet_ids) == {'forestlandmark'})
        for name,index in self.base.sheet_ids.items():
            self.check(v,'identifiers',name+' original sheet ID stable',rom.sheet_ids[name]==index)
        landmark,_=rom.sheet('forestlandmark')
        self.check(v,'sprite_contract','landmark exact four16x32 native frames, one8tile streamed canvas',
                   landmark['width']==16 and landmark['height']==32 and landmark['frame_tiles']==8 and landmark['tile_count']==32 and landmark['shape']==2 and landmark['size']==2)
        self.check(v,'identifiers','landmark sheet appended after alloriginals',rom.sheet_ids['forestlandmark']==self.base.defs['SHEET_COUNT'])
        self.check(v, 'identifiers', 'new wooden B pair appended as6/7',rom.defs['F_INTERACTIVECHEST_WOODEN_B_CLOSED'] == 6 and rom.defs['F_INTERACTIVECHEST_WOODEN_B_OPEN'] == 7)
        for index,name in enumerate(('relic','shrine_available','shrine_spent','keylock')):
            self.check(v,'identifiers','landmark '+name+' stable declared frame ID',rom.defs['F_FORESTLANDMARK_'+name.upper()]==index)
        for tile,frame in [('bush','bush'),('rock_small','rock'),('boulder','boulder'),('myst_pot','pot')]:
            a=source['tiles'][tile];b=source['sprites']['lift'][frame]
            self.check(v,'carry_identity',tile+' exact floor/carried native pixels',a['frames'][0]==b['pixels'])
            slot=rom.defs['PAL_OBJ_'+b['bank'].upper()]
            self.equal(v,'carry_identity',tile+' exact floor/carried material',
                       struct.pack('<16H',*source['bg_palettes'][a['bank']]),rom.array('pal_obj')[slot*32:(slot+1)*32])
        return {'unique_BG_IDs':len(source['tiles']), 'unique_BG_frames':sum(len(t['frames']) for t in source['tiles'].values()),
                'topology_IDs':len(source['topology']), 'OBJ_frame_instances':len(owned), 'area_frame_instances':counts}

    def pulses(self, v, rom, source):
        pulses = source['pulse_palettes']; indices = source['pulse_indices']
        for bank, phases in pulses.items():
            self.check(v, 'pulse', bank+' has four authored phases',len(phases) == 4)
            base = source['bg_palettes'][bank]
            self.check(v, 'pulse', bank+' phase0 matches authored base',phases[0] == base)
            self.check(v, 'pulse', bank+' changes only declared glow inks',
                       all(all(c == base[i] for i,c in enumerate(p) if i not in indices[bank]) for p in phases))
            self.check(v, 'pulse', bank+' genuinely changes native phase colors',len({tuple(p) for p in phases}) > 1)
        expected = b''.join(struct.pack('<16H',*p) for phases in pulses.values() for p in phases)
        self.equal(v, 'pulse', 'all direct four-phase palettes packed exactly',expected,rom.array('forest_v2_pulse_colors'))
        slots = rom.array('forest_v2_pulse_slots');n = len(pulses)
        self.check(v, 'pulse', 'slot table has three areas x pulse count',len(slots) == 3*n)
        for area in ('forest','sewer','myst'):
            ts = rom.tileset(area);area_id=rom.defs['TS_'+area.upper()]
            for i,bank in enumerate(pulses):
                slot=slots[area_id*n+i]
                if slot == 255:continue
                self.check(v, 'pulse', area+' pulse slot in world region',slot < ts['palette_count'] <= 12)
                self.equal(v, 'pulse', area+'.'+bank+' slot base palette exact',
                           struct.pack('<16H',*source['bg_palettes'][bank]),ts['palettes'][slot*32:(slot+1)*32])
            if area == 'sewer':self.check(v,'pulse','Drain has no forest pulse slots',all(s == 255 for s in slots[area_id*n:(area_id+1)*n]))
        return {'banks':list(pulses),'indices':indices,'phase_count':4}

    def preserved(self,v,rom):
        self.equal(v,'protected','all sixteen OBJ palette banks exact',self.base.array('pal_obj'),rom.array('pal_obj'))
        for name,number in self.base.defs.items():
            if name.startswith('PAL_OBJ_'):
                self.check(v,'protected',name+' physical palette slot stable',rom.defs.get(name)==number)
            if name.startswith('PAL_BG_') and name!='PAL_BG_COUNT':
                self.check(v,'protected',name+' original logical BGpalette ID stable',rom.defs.get(name)==number)
                if name[7:].lower() not in BANKS:
                    self.equal(v,'protected',name+' original nonterrain palette exact',
                               self.base.array('pal_bg')[number*32:(number+1)*32],rom.array('pal_bg')[number*32:(number+1)*32])
        for index in range(self.base.defs['SHEET_FACE_FRAMES']):
            if index not in {self.base.defs['F_FACE_'+n.upper()] for n in PORTRAITS}:
                self.equal(v,'protected','portrait bank'+str(index)+' exact',self.base.array('pal_face')[index*32:(index+1)*32],rom.array('pal_face')[index*32:(index+1)*32])
        for area in ('sewer',):
            a,b=self.base.tileset(area),rom.tileset(area)
            self.check(v,'protected',area+' exact tile/palette allocation',a['tile_count']==b['tile_count'] and a['palette_count']==b['palette_count'])
            for key in ('tiles','palettes'):self.equal(v,'protected',area+'.'+key,a[key],b[key])
            self.equal(v,'protected',area+' original logical mappings',a['map'],b['map'][:len(a['map'])])
            self.equal(v,'protected',area+' allnewforestalias mappings remain blank',bytes(len(b['map'])-len(a['map'])),b['map'][len(a['map']):])
            self.check(v,'protected',area+' animation descriptors and frame payloads',a['animations'] == b['animations'])
        rooms=json.loads((ROOT/'art/reboot_contracts.json').read_text())['rooms']
        self.check(v,'protected','authored roomcount stable',rom.defs['ROOM_COUNT']==self.base.defs['ROOM_COUNT'])
        for i,record in enumerate(rooms):
            a=struct.unpack('<BB2xIIIB3x',self.base.array('room_defs')[i*20:(i+1)*20])
            b=struct.unpack('<BB2xIIIB3x',rom.array('room_defs')[i*20:(i+1)*20])
            self.check(v,'protected',record['name']+' authored dimensions/objectcount exact',(a[0],a[1],a[5])==(b[0],b[1],b[5]))
            for at,name in ((2,'ground'),(3,'overlay'),(4,'objects')):
                self.check(v,'protected',record['name']+'.'+name+' resolved native target',b[at]==rom.symbols.get('room_'+record['name']+'_'+name,0))
        skip={'tilesets','sheets','room_defs','pal_bg','pal_face','metatile_type','metatile_coll','metatile_prop','metatile_glitter',
              'tile_anims_sewer','tile_anims_forest','tile_anims_myst','metatile_map_sewer'}
        changed={'npc','face','lift','interactiveentry','interactivechest'}
        for name in self.base.sections:
            if name in skip or name.startswith(('tileset_forest_','tileset_myst_','metatile_map_forest','metatile_map_myst','tile_anim_forest','tile_anim_myst')):continue
            if name in {'sheet_'+s+'_tiles' for s in changed} or name in {s+'_frame_pal' for s in changed}:continue
            self.check(v,'protected',name+' exists',name in rom.sections)
            if name in rom.sections:self.equal(v,'protected',name+' exact array',self.base.array(name),rom.array(name))
        for area in ('forest','myst'):
            for name in GLITTER:
                if area not in self.specs[name]['areas']:continue
                a=decode_metatile(self.base,self.base.tileset(area),name);b=decode_metatile(rom,rom.tileset(area),name)
                self.check(v,'protected',area+'.'+name+' exact indexed/RGB/clock',a['frames']==b['frames'] and a['speed']==b['speed'])
        for symbol,length in (('gEnemyDefs',48),('gHitboxes',48)):
            self.equal(v,'protected',symbol+' native combat table',self.base.read(self.base.symbols[symbol],length),rom.read(rom.symbols[symbol],length))

    def runtime(self):
        if not self.args.runtime:return {'status':'not_requested'}
        root=Path(self.args.runtime);baseline=json.loads((root/'v6/capture.json').read_text());profiles=[]
        visual={'oam','player_priority','bg_palette_sha256','obj_palette_sha256','depth_oam',
                'target_BG_ground_quarters','chest_stream','landmark_stream','depth_visibility',
                'protected_UI_palette_sha256','authored_BG_palette_phase','displayed_BG_palette_phase'}
        def logical(state):return {k:v for k,v in state.items() if k not in visual}
        old={r['name']:r for r in baseline['captures']}
        control_path=root/'control-v0/capture.json'
        control=json.loads(control_path.read_text());control_rom=NativeRom(Path(self.args.frozen)/'v0')
        control_freeze=json.loads((control_rom.directory/'freeze.json').read_text())
        self.check(0,'runtime_control','fresh production control source/ROM bound',
                   control['forest_variant']==0 and control['source_commit']==control_freeze['source_commit'] and control['rom_sha256']==SHA(control_rom.rom)==PRODUCTION_SHA)
        self.check(0,'runtime_control','production control all83 cases/checks pass',
                   control.get('complete') and len(control['captures'])==83 and control['passed']==control['total'] and not control['failures'])
        for v in range(6,11):
            report=json.loads((root/f'v{v}/capture.json').read_text());rom=NativeRom(Path(self.args.frozen)/f'v{v}')
            frozen=json.loads((rom.directory/'freeze.json').read_text())
            self.check(v,'runtime','actual capture ROM/source binding',report['rom_sha256']==SHA(rom.rom) and report['source_commit']==frozen['source_commit'])
            self.check(v,'runtime','round2 explicit native/diagnostic provenance',report.get('schema')==2 and report.get('forest_study_round')==2 and report.get('forest_variant')==v and report.get('display_variant')==v-5)
            self.check(v,'runtime','all actual harness checks pass',report['passed']==report['total'] and not report['failures'] and report.get('complete'))
            self.check(v,'runtime','new capture tool hash',report['capture_tool_sha256']==SHA((ROOT/'tools/forest_v2_review.py').read_bytes()))
            for name,expected in report['frozen_input_sha256'].items():
                self.check(v,'runtime','captured frozen '+name+' remains exact',SHA((rom.directory/name).read_bytes())==expected)
            for name,expected in report.get('capture_dependency_sha256',{}).items():
                self.check(v,'runtime','capture dependency '+name+' unchanged',SHA((ROOT/'tools'/name).read_bytes())==expected)
            current={r['name']:r for r in report['captures']}
            self.check(v,'runtime','same new-geometry baseline case names',set(current)==set(old))
            ticks=[]
            for name in sorted(set(current)&set(old)):
                a,b=old[name],current[name]
                for field in ('group','seed','cell','stage','role','archetype','action','frames','video_frames',
                              'position','target','facing','natural_mystery','physical_contract','final_physical_contract',
                              'maze_sha256','initial_progress_sha256','final_progress_sha256','initial_rng','final_rng','inputs','fixture_kind'):
                    if field in a or field in b:self.check(v,'runtime_contract',name+'.'+field+' exact profile6 baseline',a.get(field)==b.get(field))
                for field in ('initial','final'):
                    self.check(v,'runtime_contract',name+'.'+field+' logical state exact',logical(a[field])==logical(b[field]))
                at,bt=a['mechanic_transitions'],b['mechanic_transitions']
                self.check(v,'runtime_contract',name+' mechanical transition order', [r['state'] for r in at]==[r['state'] for r in bt])
                ticks.append({'name':name,'transition_ticks_exact':at==bt})
                if str(b.get('fixture_kind','')).startswith('diagnostic'):
                    self.check(v,'runtime_diagnostic',name+' labels injected semantic fixture',bool(b.get('diagnostic_room')))
                samples=b.get('hardware_samples',[])
                self.check(v,'runtime_hardware',name+' records actual hardware samples',bool(samples))
                for field in ('static_BG_bytes_match_ROM','animated_BG_bytes_are_authored_frames',
                              'world_palette_bytes_match_ROM','OAM_legal','actual_hardware_palette_is_authored_phase',
                              'selected_OBJ_palette_bytes_match_ROM','resolved_visual_mappings_valid'):
                    self.check(v,'runtime_hardware',name+'.'+field+' all sampled hardware checks true',
                               all(s.get(field) is True for s in samples))
                for key in ('phase_keyframes','pulse_phase_keyframes'):
                    for frame in b.get(key,[]):
                        self.check(v,'runtime_media',name+'.'+key+'.'+str(frame.get('tick'))+' native file bound',
                                   SHA((root/f'v{v}'/frame['path']).read_bytes())==frame['sha256'])
            self.check(v,'runtime_geometry','world generator graph exact across new styles',report['worlds']==baseline['worlds'])
            contracts=report.get('diagnostic_contracts',[])
            self.check(v,'runtime_diagnostic','exhaustive new adjacency contract corpus recorded',len(contracts)==457,len(contracts))
            identities=set()
            for c in contracts:
                family,kind,mask,corners,q=(c[k] for k in ('family','kind','cardinal_mask','inner_corner_mask','quadrant'))
                identities.add((family,kind,mask,corners,q))
                if family=='canopy':name=f'f2_canopy_{kind-1}_{q}_{mask:x}{corners:x}'
                elif family=='fringe':name=f'f2_fringe_{kind-1}_{mask:x}' if mask else None
                elif family=='water':name=f'f2_water_{mask:x}{corners:x}'
                elif family=='isolated-water':name='f2_water_'+{2:'lily',3:'foam'}[kind]+'_isolated'
                else:raise ValueError('unknown diagnostic family '+family)
                expected=rom.tile_ids[name.upper()] if name else 65535
                self.check(v,'runtime_diagnostic',str((family,kind,mask,corners,q))+' actual hardware/semantics/independent ID agree',
                           c['actual_visual_id']==c['expected_visual_id']==expected and c['hardware_map_matches_ROM'] and c['semantic_collision_preserved'] and c['passed'])
            expected_ids={('canopy',kind,mask,corners,q) for kind in (1,2) for q in range(4) for mask,corners in valid_adjacencies()}
            expected_ids|={('water',1,mask,corners,0) for mask,corners in valid_adjacencies()}
            expected_ids|={('fringe',kind,mask,0,0) for kind in (1,2) for mask in range(16)}
            expected_ids|={('isolated-water',kind,15,0,0) for kind in (2,3)}
            self.check(v,'runtime_diagnostic','all independently constructed457 distinct topology cases covered exactly',identities==expected_ids and len(identities)==len(contracts))
            deep=current['deep-blight'];pulse=deep['pulse_contract']
            slots=rom.array('forest_v2_pulse_slots');colors=rom.array('forest_v2_pulse_colors');n=len(colors)//128
            expected_banks=[{'slot':slots[rom.defs['TS_FOREST']*n+i],
                             'rgb555_phases':[list(struct.unpack_from('<16H',colors,i*128+p*32)) for p in range(4)]} for i in range(n)]
            self.check(v,'runtime_pulse','actual hardware proof uses exact native authored four-phase banks',pulse['authored_BG_banks']==expected_banks)
            self.check(v,'runtime_pulse','allfour glow phases really displayed with native OBJ stable',
                       pulse['actual_displayed_phases']==[0,1,2,3] and pulse['selected_OBJ_palette_bytes_match_ROM'] is True)
            self.check(v,'runtime_pulse','four exact phase image references retained',
                       {p['phase'] for p in deep['pulse_phase_keyframes']}==set(range(4)))
            trace=deep['trace']
            self.check(v,'runtime_pulse','glow trace contains allfour actual hardware phases',
                       {s['displayed_BG_palette_phase'] for s in trace}==set(range(4)))
            for field in ('obj_palette_sha256','protected_UI_palette_sha256'):
                self.check(v,'runtime_pulse',field+' stable across actual glow trace',
                           len({s[field] for s in trace})==1)
            restoration=[r['palette_restore'] for r in report['routes'] if 'palette_restore' in r]
            restores=restoration[0]['four_menu_entry_phases'] if len(restoration)==1 else []
            self.check(v,'runtime_pulse','ordinary menu restoration samples cover four actual phases',
                       {s.get('authored_palette_phase') for s in restores}==set(range(4)) and
                       all(s.get('actual_hardware_palette_is_authored_phase') and s.get('selected_OBJ_palette_bytes_match_ROM') for s in restores))
            profiles.append({'variant':v,'rom_sha256':SHA(rom.rom),'capture_count':len(current),
                             'natural_capture_count':report.get('natural_capture_count'),
                             'diagnostic_capture_count':report.get('diagnostic_capture_count'),
                             'passed':report['passed'],'total':report['total'],'transition_timing_observations':ticks})
        return {'status':'compared','baseline_profile':6,'profiles':profiles,
                'production_control':{'capture_count':len(control['captures']),'passed':control['passed'],'total':control['total'],'rom_sha256':control['rom_sha256']},
                'limits':'New log placement/overhangs intentionally differ from historical terrain. Diagnostic scenes inject disclosed semantic shapes; they are actual renderer outputs, not naturally generated rooms. Visual palette/OAM fields are excluded from cross-style logical equality and checked by native/hardware assertions separately.'}

    def existing_host(self,path):
        report=json.loads(Path(path).read_text());v=report['variant'];rom=NativeRom(Path(self.args.frozen)/f'v{v}')
        self.check(v,'host_generator','host report bound to same frozen ROM',report['rom_sha256']==SHA(rom.rom))
        for rel,expected in report['source_sha256'].items():
            self.check(v,'host_generator',rel+' host-tested source remains exact',SHA((ROOT/rel).read_bytes())==expected)
        stats=report['statistics'];count=stats['requested_seeds']
        self.check(v,'host_generator','recorded complete20K seed spatial checks andthree graph tunings',
                   report['exit_code']==0 and count>=20000 and stats['seeds']==count and stats['rooms']==count*25 and
                   stats['world_graphs']==count*3 and stats['failures']==0 and stats['logs']>0 and stats['item_pockets']>0 and stats['underpasses']>0,stats)
        return report

    def run(self):
        self.source_scope()
        for v in self.args.profiles:
            rom=NativeRom(Path(self.args.frozen)/f'v{v}');f=json.loads((rom.directory/'freeze.json').read_text())
            self.provenance(v,rom,f)
            if v<=5:
                old=NativeRom(Path(self.args.historical)/f'v{v}')
                self.equal(v,'historical','complete historical ROM bytes exact',old.rom,rom.rom)
                art={'status':'historical byte preservation'};pulse=None
            else:
                source=json.loads(subprocess.check_output([sys.executable,str(Path(__file__).resolve()),'--export-source',str(v),'--inventory',self.args.inventory],text=True,cwd=ROOT))
                art=self.native(v,rom,source);pulse=self.pulses(v,rom,source);self.preserved(v,rom)
            budgets={}
            for area in ('forest','myst','sewer'):
                ts=rom.tileset(area);budgets[area]={k:ts[k] for k in ('tile_count','palette_count')}
                self.check(v,'budget',area+' world BG budget',ts['tile_count']<=1024 and ts['palette_count']<=12,budgets[area])
                colors=struct.unpack('<%dH'%(len(ts['palettes'])//2),ts['palettes'])
                self.check(v,'budget',area+' native RGB555 palette words',all(c<32768 for c in colors))
                self.check(v,'budget',area+' <=255native animation allocations',len(ts['animations'])<=255,len(ts['animations']))
                bases={a['base'] for a in ts['animations']}
                for animation in ts['animations']:
                    start=animation['base']
                    self.check(v,'native_residency',area+' anim'+str(start)+' in-bounds allocation',start+4<=ts['tile_count'])
                    self.equal(v,'native_residency',area+' anim'+str(start)+' initial resident pixels equalphase0',
                               animation['data'][:128],ts['tiles'][start*32:(start+4)*32])
                for name,index in rom.tile_ids.items():
                    entries=struct.unpack_from('<4H',ts['map'],index*8)
                    self.check(v,'native_mapping',area+'.'+name+' valid native tile/palette references',
                               all((e&1023)<ts['tile_count'] and (e>>12)<ts['palette_count'] for e in entries))
                    if (entries[0]&1023) in bases:
                        start=entries[0]&1023
                        self.check(v,'native_residency',area+'.'+name+' animatedquarters sequential/unflipped',
                                   [e&4095 for e in entries]==[start+q for q in range(4)])
            memory={name:int(address,16) for address,name in re.findall(r'^\s+0x([0-9a-fA-F]+)\s+(__ewram_bss_end|__bss_end)\s*=',rom.linker,re.M)}
            self.check(v,'budget','EWRAM end below256KiB limit',memory.get('__ewram_bss_end',0xFFFFFFFF)<=0x02040000,memory)
            self.check(v,'budget','IWRAM code/data/BSS leave declared stack region',memory.get('__bss_end',0xFFFFFFFF)<=0x03007E00,memory)
            budgets['memory']={**memory,'ewram_used':memory.get('__ewram_bss_end',0)-0x02000000,'iwram_used':memory.get('__bss_end',0)-0x03000000}
            if v>=6:
                EnemyAudit.budget(self,v,rom,11)
                union={**self.budgets[-1],'allocations':dict(self.budgets[-1]['allocations'])}
                extra=4*rom.sheet('forestlandmark')[0]['frame_tiles']
                union['allocations']['four streamedlandmark slots']=extra
                union['used']+=extra;union['free']-=extra
                self.budgets[-1]=union
                self.check(v,'obj_budget','complete union includesfourlandmark slots',union['used']<=union['limit'],union)
            self.profiles.append(dict(variant=v,source_commit=f['source_commit'],rom_sha256=SHA(rom.rom),native_art=art,pulse=pulse,budgets=budgets))
        runtime=self.runtime()
        host=(self.host_generator(6,self.args.host_seeds) if self.args.host_seeds else
              self.existing_host(self.args.host_report) if self.args.host_report else {'status':'not_requested'})
        failed=[r for r in self.rows if not r['passed']]
        report=dict(method=__doc__,auditor_sha256=SHA(Path(__file__).read_bytes()),profiles=self.profiles,
                    runtime=runtime,host_generator=host,obj_budgets=self.budgets,passed=len(self.rows)-len(failed),total=len(self.rows),failures=failed,checks=self.rows,
                    limits='Source/native coverage includes retained unused IDs. Actual and diagnostic captures are distinguished. Finite room/seed tests do not assert universal solvability, CPU timing or aesthetic preference.')
        p=Path(self.args.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(report,indent=2)+'\n')
        print('RESULT',report['passed'],'/',report['total'],flush=True)
        return bool(failed)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inventory',default='/workspace/setup/forest-concepts/inventory.json')
    p.add_argument('--baseline',default='/workspace/setup/forest-concepts/baseline')
    p.add_argument('--historical',default='/workspace/setup/forest-concepts/frozen')
    p.add_argument('--frozen',default=str(WORK/'frozen'))
    p.add_argument('--profiles',nargs='+',type=int,default=[0,1,5,6,7,8,9,10])
    p.add_argument('--out',default=str(WORK/'audit/native.json'))
    p.add_argument('--host-seeds',type=int,default=0,help='Run actual host C room generation over this many seeds after native checks.')
    p.add_argument('--host-report',help='Reuse an already passing frozen/source-bound host result without repeating the seed corpus.')
    p.add_argument('--runtime')
    p.add_argument('--export-source',type=int)
    a=p.parse_args()
    if a.export_source is not None:direct_export(a.export_source,a.inventory);return 0
    return Audit(a).run()


if __name__=='__main__':raise SystemExit(main())

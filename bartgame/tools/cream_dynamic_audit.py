#!/usr/bin/env python3
"""Independent native art and actual-C topology audit for Cream profile12.

Physical geometry is intentionally new. Unlike the earlier art-only studies,
this audit does not require old room bytes: it checks the unchanged capability
graph, actual supported routes/content, genuine distinct elevation islands,
safe directed local drops, and complete native masked composition. It compiles
the pinned room/topology/compositor C with hardware uploads suppressed only.
Real mGBA actions, map rendering and visible water need separate capture proof.
"""
import argparse
import ast
from collections import Counter, deque
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys

import cream_polish_audit as P
import cream_graph_review as G
from cream_art_study_capture import Info
from cream_art_study_audit import BASELINE_SHA, native_color
from sewer_concept_audit import decode_metatile,decode_sprite

ROOT=Path(__file__).resolve().parents[1]
sha=lambda value:hashlib.sha256(value if isinstance(value,bytes) else Path(value).read_bytes()).hexdigest()


class Climb(C.Structure):
    _fields_=[(name,C.c_uint8) for name in ('x','top','bottom','owner','top_height','bottom_height')]


class Drop(C.Structure):
    _fields_=[(name,C.c_int16) for name in ('x','y','landing_x','landing_y')]+[(name,C.c_uint8) for name in ('owner','height')]


class Platform(C.Structure):
    _fields_=[(name,C.c_uint8) for name in ('x','y','w','h','owner','height','content')]


class Topology(C.Structure):
    _fields_=[(name,C.c_uint8) for name in ('active','cell','archetype','platforms','climbs','drops','max_height')]
    _fields_ += [('cells',C.c_uint8*768),('platform',Platform*8),('climb',Climb*8),('drop',Drop*8)]


class Route(C.Structure):
    _fields_=[(n,C.c_uint8) for n in ('edge','mode','target','rows')]+[(n,C.c_int16) for n in ('x','y')]


def export_source(options):
    for name,value in options.items():
        if name.startswith('BART_'):os.environ[name]=str(value)
    sys.path.insert(0,str(ROOT/'art'))
    import tiles,cream_terrain as terrain,cream_actors as actors,cream_polish_assets as art
    result=dict(palettes={n:[native_color(c) for c in bank] for n,bank in terrain.PALETTES.items()},
                tables=art.TABLES,tiles={})
    for mt in tiles.METATILES:
        if not mt['name'].startswith('cream_'):continue
        frames=[]
        for rows in mt.get('frames') or [mt['art']]:
            assert len(rows)==16 and all(len(r)==16 for r in rows)
            frames.append(bytes(0 if c in '. ' else int(c,16) for r in rows for c in r).hex())
        result['tiles'][mt['name'].upper()]=dict(frames=frames,palettes=mt.get('qpals') or [mt['pal']]*4,
            type=mt['type'],coll=mt.get('coll',tiles.default_coll(mt['type'])),prop=int(bool(mt.get('prop'))),
            glitter=int(bool(mt.get('glitter'))),speed=mt.get('anim_speed',8) if len(frames)>1 else None)
    door=next(s for s in actors.build_sheets() if s['name']=='creamdoors')
    result['cream_return']=bytes(0 if c in '. ' else int(c,16) for row in door['frames']['return'] for c in row).hex()
    print(json.dumps(result,separators=(',',':')))


class Audit(P.Audit):
    def provenance(self):
        self.profile=self.rom.defs.get('BART_CREAM_VARIANT');self.digest=sha(self.rom.rom)
        self.check('provenance','production baseline exact pin',sha(self.base.rom)==BASELINE_SHA)
        self.check('provenance','new Cream topology profile12',self.profile==12,self.profile)
        if self.args.pin:self.check('provenance','candidate supplied SHA256 exact',self.digest==self.args.pin)
        self.options=json.loads((Path(self.args.bundle)/'build-options.json').read_text())
        if 'options' in self.options:self.options=self.options['options']
        self.check('provenance','frozen option agrees with native header',int(self.options['BART_CREAM'])==12)
        self.check('provenance','frozen ROM hash exact',self.options.get('rom_sha256')==self.digest)
        self.commit=(Path(self.args.bundle)/'source-commit.txt').read_text().strip()
        files=list((ROOT/'art').glob('cream_*.py'))+[ROOT/'art/tiles.py',ROOT/'Makefile',ROOT/'tools/build_assets.py']
        files += [ROOT/'src'/name for name in ('cream_room.c','cream_room.h','cream_runtime.c','cream_runtime.h',
            'cream_topology.c','cream_topology.h','cream_polish.c','cream_polish_blend.c','cream_polish_blend.h',
            'game.c','room.c','gear_menu.c','menu.c','cream_map_concepts.c','cream_map_concepts.h',
            'cream_map_forms_a.c','cream_map_forms_b.c')]
        self.source_snapshot={str(p.relative_to(ROOT)):sha(p) for p in files if p.exists()}
        prefix=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','--show-prefix'],text=True).strip()
        mismatch=[]
        for name,digest in self.source_snapshot.items():
            blob=subprocess.run(['git','-C',str(ROOT),'show',self.commit+':'+prefix+name],capture_output=True)
            if blob.returncode or sha(blob.stdout)!=digest:mismatch.append(name)
        self.check('provenance','audited source matches pinned game/art commit',not mismatch,mismatch or self.commit)

    def source(self):
        command=[sys.executable,str(Path(__file__).resolve()),'--export-source','--source-options',json.dumps(self.options)]
        source=json.loads(subprocess.check_output(command,text=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')))
        self.source_data=source;(self.out.parent/'source-native.json').write_text(json.dumps(source,indent=2)+'\n')
        rom=self.rom;ts=rom.tileset('cream');mapping=rom.array('metatile_map_cream')
        resident={n for n,index in rom.tile_ids.items() if n.startswith('CREAM_') and mapping[index*8:index*8+8]!=bytes(8)}
        self.check('source','all resident Cream IDs have authored source',resident<=set(source['tiles']))
        self.check('native_limits','static BG leaves128 blend characters',ts['tile_count']<=896,ts['tile_count'])
        arrays={k:rom.array('metatile_'+k) for k in ('type','coll','prop','glitter')};total=0
        for name in sorted(resident):
            spec=source['tiles'][name];actual=decode_metatile(rom,ts,name);index=rom.tile_ids[name]
            self.check('source',name+' frames/timing',len(actual['frames'])==len(spec['frames']) and actual['speed']==spec['speed'])
            self.check('source_metadata',name+' exact physical contract',arrays['type'][index]==rom.defs['TT_'+spec['type']] and
                all(arrays[key][index]==spec[key] for key in ('coll','prop','glitter')))
            if name in self.added:
                alpha=('_PANEL_' in name or ('CLIMB' in name and spec['type']=='CLIMB'))
                self.check('appended_contract',name+' safe native visual terrain',
                    (spec['type'],spec['coll'],spec['prop']) in {('FLOOR',0,0),('SOLID',15,0),('CLIMB',0,0)} and
                    not spec['glitter'] and (alpha or all(0 not in bytes.fromhex(f) for f in spec['frames'])))
            for f,((indices,colors),expected_hex) in enumerate(zip(actual['frames'],spec['frames'])):
                expected=bytes.fromhex(expected_hex)
                self.equal('native_pixels',name+' frame'+str(f),expected,indices)
                rgb=struct.pack('<256H',*[source['palettes'][spec['palettes'][(y//8)*2+x//8]][expected[y*16+x]]
                    if expected[y*16+x] else 0x8000 for y in range(16) for x in range(16)])
                self.equal('native_colors',name+' frame'+str(f),rgb,colors);total+=1
        sheet,pixels=rom.sheet('creamdoors');stride=sheet['frame_tiles']*32;frame=rom.defs['F_CREAMDOORS_RETURN']
        self.equal('native_sprite','Cream return exact source',bytes.fromhex(source['cream_return']),
                   decode_sprite(pixels[frame*stride:(frame+1)*stride],sheet['width'],sheet['height']))
        classes=[]
        for i in range(ts['tile_count']):
            values=[c for b in ts['tiles'][i*32:(i+1)*32] for c in (b&15,b>>4)]
            classes.append(0 if not any(values) else 1 if all(values) else 2)
        self.equal('native_blend','alpha classes match actual4bpp',bytes(classes),rom.array('cream_polish_tile_alpha'))
        def flatten(values):
            for value in values:
                if isinstance(value,list):yield from flatten(value)
                elif isinstance(value,str):yield rom.tile_ids[value.upper()]
                elif value is None:yield 65535
                else:raise TypeError(type(value))
        for key,values in source['tables'].items():
            if key=='panels':
                symbol=next((n for n in ('cream_polish_panels','cream_visual_panels') if n in rom.sections),None)
                self.check('native_tables','whole-panel footprint table exists',symbol is not None)
                if symbol:self.equal('native_tables','whole-panel source starts/footprints',b''.join(
                    struct.pack('<HBB',rom.tile_ids[p['first'].upper()],p['w'],p['h']) for stage in values for p in stage),rom.array(symbol))
                continue
            symbol=next((prefix+key for prefix in ('cream_polish_','cream_visual_','cream_dynamic_') if prefix+key in rom.sections),None)
            # Profile12 nests design0 in the complete three-design table;
            # its unused standalone alias is correctly garbage-collected.
            if key=='climb' and symbol is None and 'cream_polish_dynamic_climb' in rom.sections:
                self.check('native_tables','legacy climb alias equals nested design0',
                           values==[stage[0] for stage in source['tables']['dynamic_climb']])
                continue
            self.check('native_tables',key+' table exists',symbol is not None)
            if symbol:
                ids=list(flatten(values));self.equal('native_tables',key+' exact authored IDs',struct.pack('<%dH'%len(ids),*ids),rom.array(symbol))
        blue=source['palettes']['cream_water']
        self.check('water','body remains visibly blue',sum(((c>>10)&31)-(c&31) for c in blue[3:9])>24)
        return total

    def host(self,label,rom,current=False):
        directory=self.out.parent/('host-'+label);directory.mkdir(parents=True,exist_ok=True)
        commit=(rom.directory/'source-commit.txt').read_text().strip()
        prefix=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','--show-prefix'],text=True).strip()
        repository=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','--show-toplevel'],text=True).strip()
        def show(name):return (ROOT/'src'/name).read_bytes() if current else subprocess.check_output(['git','-C',str(ROOT),'show',commit+':'+prefix+'src/'+name])
        names=[str(p) for p in (ROOT/'src').iterdir()] if current else subprocess.check_output(['git','-C',repository,'ls-tree','-r','--name-only',commit,'--',prefix+'src'],text=True).splitlines()
        for name in names:
            if name.endswith(('.h','.inc')):(directory/Path(name).name).write_bytes(show(Path(name).name))
        (directory/'assets.h').write_text(rom.header)
        sources=['cream_world.c','cream_room.c']+(['cream_topology.c','cream_polish.c','cream_polish_blend.c'] if label=='dynamic' else [])
        for name in sources:(directory/name).write_bytes(show(name))
        aliases=[];alias_names={}
        for index,name in enumerate(n for n in rom.sections if n.startswith(('metatile_','cream_visual_','cream_polish_','cream_dynamic_')) or n in ('tileset_cream_tiles','tileset_cream_pals')):
            data=rom.array(name);alias_names[name]='audit_asset_'+str(index)
            aliases.append('const unsigned char audit_asset_%d[] __asm__("%s") __attribute__((aligned(4)))={%s};'%
                           (index,name,','.join(map(str,data))))
        if label=='dynamic':
            ts=rom.tileset('cream')
            aliases.append('const Tileset tilesets[4]={[TS_CREAM]={.tiles=(const u16*)%s,.tile_count=%d,.map=(const u16*)%s,.anims=0,.anim_count=0,.pals=(const u16*)%s,.pal_count=%d}};'%
                           (alias_names['tileset_cream_tiles'],ts['tile_count'],alias_names['metatile_map_cream'],alias_names['tileset_cream_pals'],ts['palette_count']))
        (directory/'meta.inc').write_text('\n'.join(aliases)+'\n')
        syntax=ast.parse((ROOT/'tools/cream_room_review.py').read_text())
        fixture=next(ast.literal_eval(n.value) for n in syntax.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='FIXTURE' for t in n.targets))
        if label=='dynamic':fixture+='\n#include "cream_topology.h"\nunsigned audit_topology_size(void){return sizeof(CreamTopology);}\n'
        (directory/'host.c').write_text(fixture)
        command=['gcc','-shared','-fPIC','-O2','-w','-fno-builtin','-DCREAM_POLISH_HOST_AUDIT=1','-I',str(directory),
                 *[str(directory/name) for name in sources],str(directory/'host.c'),'-o',str(directory/'room.so')]
        result=subprocess.run(command,capture_output=True,text=True);(directory/'compile.log').write_text(result.stdout+result.stderr);result.check_returncode()
        lib=C.CDLL(str(directory/'room.so'))
        lib.cream_generate.argtypes=[C.c_uint32];lib.cream_generate.restype=C.c_uint8
        lib.cream_room_arrival.argtypes=[C.c_int,C.POINTER(G.Edge),C.POINTER(C.c_int),C.POINTER(C.c_int),C.POINTER(C.c_int)]
        lib.cream_room_feature_reserved.restype=C.c_uint8
        lib.room_box_solid.restype=C.c_uint8
        lib.cream_room_route.restype=C.c_uint8
        if label=='dynamic':
            assert lib.audit_topology_size()==C.sizeof(Topology),(lib.audit_topology_size(),C.sizeof(Topology))
            lib.cream_topology_component_at.argtypes=[C.c_int,C.c_int,C.c_int]
            lib.cream_topology_local_drop.argtypes=[C.c_int,C.c_int,C.c_int,C.c_uint16,C.POINTER(C.c_int),C.POINTER(C.c_int),C.POINTER(C.c_int)]
            lib.cream_topology_local_drop.restype=C.c_uint8
        return lib

    def geometry(self):
        control=self.host('control',self.base);lib=self.host('dynamic',self.rom,current=getattr(self.args,'unfrozen_host',False))
        world=G.World.in_dll(lib,'gCreamWorld');oldworld=G.World.in_dll(control,'gCreamWorld')
        room=P.Room.in_dll(lib,'gRoom');info=Info.in_dll(lib,'gCreamRoom');topology=Topology.in_dll(lib,'gCreamTopology')
        opened=(C.c_uint8*50).in_dll(lib,'gCreamOpenEdges');meta={k:self.rom.array('metatile_'+k) for k in ('type','coll','prop','glitter')}
        ttfloor=self.rom.defs['TT_FLOOR'];ttclimb=self.rom.defs['TT_CLIMB'];ttmyst=self.rom.defs.get('TT_MYST',24)
        counts=Counter();archetypes=Counter();height_sets=Counter();islands=Counter();failures=[];samples=[];widths=set();plans={}
        def verify(ok,name,detail):
            counts[name]+=1
            if not ok and len(failures)<100:failures.append(dict(name=name,**detail))
        def build(cell,visual=True):
            lib.cream_room_build(cell)
            lib.cream_topology_sync()
            if visual:lib.cream_visuals_build()
        def clear(x,y):
            return 0<=x<32 and 0<=y<24 and not lib.room_box_solid(x*16+3,y*16+7,x*16+12,y*16+13)
        def valid(x,y,t):
            # Border aprons outside a closed side gate belong to the next
            # room approach. They are tested by gate/arrival qualification,
            # not required to be reachable from this sealed component.
            if x in (0,31) or y in (0,23):return False
            if not clear(x,y):return False
            mt=room.ground[y*32+x];kind=meta['type'][mt];c=topology.cells[y*32+x]
            return kind in (ttfloor,ttmyst,ttclimb) and (c&16) and bool(c&8)==bool(t) and not (kind==ttclimb and (c&7)==7)
        def physical_components(t):
            vertices={(x,y) for y in range(24) for x in range(32) if valid(x,y,t)}
            links={p:[] for p in vertices}
            for x,y in vertices:
                for q in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                    if q in vertices:links[(x,y)].append(q)
            for drop in topology.drop[:topology.drops]:
                a=(drop.x//16,(drop.y-4)//16);b=(drop.landing_x//16,(drop.landing_y-4)//16)
                if drop.owner==t and a in vertices and b in vertices:links[a].append(b)
            return vertices,links
        def flood(links,start):
            seen={start};queue=deque([start])
            while queue:
                for target in links[queue.popleft()]:
                    if target not in seen:seen.add(target);queue.append(target)
            return seen
        for seed in range(self.args.geometry_seeds):
            assert control.cream_generate(seed) and lib.cream_generate(seed)
            verify(bytes(world)==bytes(oldworld),'macro capability graph exact',dict(seed=seed))
            try:G.independent(G.plain(world));graph_ok=True
            except AssertionError:graph_ok=False
            verify(graph_ok,'independent400state gate/no-trap solver',dict(seed=seed))
            for gates in (0,63):
                for n in range(50):opened[n]=gates
                for cell in range(25):
                    build(cell);detail=dict(seed=seed,cell=cell,gates=gates);counts['room_builds']+=1
                    verify(topology.active and topology.cell==cell,'active topology matches actualroom',detail)
                    plan=bytes(topology.platform)+bytes(topology.climb)+bytes(topology.drop)+b''.join(
                        bytes(getattr(info.terrace[t],name)) for t in (0,1) for name in ('chest','npc','heal','cache','mission','spawns'))
                    if gates==0:plans[(seed,cell)]=plan
                    else:verify(plan==plans[(seed,cell)],'opening macro gates never remodels local platforms/content',detail)
                    verify(topology.archetype<8 and topology.climbs<=8 and topology.drops<=8,'topology boundedrecords',detail)
                    for platform in topology.platform[:topology.platforms]:
                        verify(bool(platform.content),'new local deadend platform has content',detail|{'xy':[platform.x,platform.y]})
                    prior=(bytes(room),bytes(info),bytes(topology),bytes(world),bytes(opened))
                    preview_info=Info();preview_topology=Topology()
                    lib.cream_topology_preview(cell,C.byref(preview_info),C.byref(preview_topology))
                    verify(prior==(bytes(room),bytes(info),bytes(topology),bytes(world),bytes(opened)),
                           'map topology preview never mutates loaded game',detail)
                    verify(all(bytes(getattr(preview_info.terrace[t],name))==bytes(getattr(info.terrace[t],name))
                               for t in (0,1) for name in ('chest','npc','heal','cache','mission')),
                           'map content coordinates match actual relocated features',detail)
                    lib.cream_topology_preview((cell+7)%25,C.byref(preview_info),C.byref(preview_topology))
                    verify(prior==(bytes(room),bytes(info),bytes(topology),bytes(world),bytes(opened)),
                           'previewing another room never changes loaded game',detail)
                    archetypes[topology.archetype]+=1
                    heights=sorted({c&7 for c in topology.cells if c&16 and (c&7)<7});height_sets[len(heights)]+=1
                    verify(all(0<=h<=6 for h in heights),'physical floorheight valid',detail)
                    for t in (0,1):
                        vertices,links=physical_components(t)
                        verify(bool(vertices),'each macrocomponent has supported physicalfloor',detail|{'owner':t})
                        if not vertices:continue
                        start=min(vertices,key=lambda p:abs(p[0]-16)+abs(p[1]-(6 if t else 19)))
                        reached=flood(links,start);reverse={p:[] for p in vertices}
                        for a,targets in links.items():
                            for b in targets:reverse[b].append(a)
                        can_return=flood(reverse,start)
                        verify(reached==vertices,'allsameownerplatforms reachable viarealwalk/climb/drop',detail|{'owner':t,'unreached':sorted(vertices-reached)[:15]})
                        verify(can_return==vertices,'local routes have no physicaltrap',detail|{'owner':t,'trapped':sorted(vertices-can_return)[:15]})
                        # Count actual floorislands without climbing to show
                        # that heightvariation is physical, not just labels.
                        floors={p for p in vertices if meta['type'][room.ground[p[1]*32+p[0]]]!=ttclimb};pieces=0
                        while floors:
                            pieces+=1;a=floors.pop();q=[a]
                            for x,y in q:
                                for b in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                                    if b in floors:floors.remove(b);q.append(b)
                        islands[pieces]+=1
                        spots=info.terrace[t]
                        for flag,name in ((2,'chest'),(4,'npc'),(8,'heal'),(16,'cache'),(32,'mission')):
                            if spots.content&flag:
                                p=getattr(spots,name)
                                verify(any(abs(x-p.x)<=1 and abs(y-(p.y+1))<=1 for x,y in reached),
                                       'reachable content approach '+name,detail|{'owner':t,'xy':[p.x,p.y]})
                        for p in spots.spawns[:spots.spawn_count]:verify((p.x,p.y) in reached,'enemy spawn supported/reachable',detail|{'owner':t,'xy':[p.x,p.y]})
                    for y in range(24):
                        for x in range(32):
                            at=y*32+x;c=topology.cells[at]
                            if not c&16 or not clear(x,y):continue
                            if (c&7)!=7:verify(lib.cream_topology_component_at(x*16+8,y*16+14,0)==bool(c&8),
                                'livecomponent matches supported owner',detail|{'xy':[x,y]})
                            for xx,yy in ((x+1,y),(x,y+1)):
                                if xx>=32 or yy>=24 or not clear(xx,yy):continue
                                b=topology.cells[yy*32+xx]
                                if not b&16 or (c&32) or (b&32):continue
                                verify(bool(c&8)==bool(b&8),'no unguardedwalk bypass betweenmacroowners',detail|{'xy':[x,y],'neighbor':[xx,yy]})
                                verify((c&7)==(b&7),'heightchange usesactualclimb/face',detail|{'xy':[x,y],'neighbor':[xx,yy],'height':[c&7,b&7]})
                    for drop in topology.drop[:topology.drops]:
                        d=detail|{'source':[drop.x,drop.y],'target':[drop.landing_x,drop.landing_y]}
                        verify(drop.owner in (0,1) and drop.height>0,'localdrop sameowner positiveheight',d)
                        verify(not lib.room_box_solid(drop.landing_x-4,drop.landing_y-7,drop.landing_x+3,drop.landing_y-1),
                               'localdrop actuallanding supported',d)
                        lx=C.c_int();ly=C.c_int();h=C.c_int()
                        accepted=lib.cream_topology_local_drop(drop.x,drop.y,2,128,C.byref(lx),C.byref(ly),C.byref(h))
                        verify(accepted and (lx.value,ly.value)==(drop.landing_x,drop.landing_y),'actuallocaldrop routes exacttarget',d)
                        verify(not lib.cream_topology_local_drop(drop.x,drop.y,0,128,C.byref(lx),C.byref(ly),C.byref(h)) and
                               not lib.cream_topology_local_drop(drop.x,drop.y,2,64,C.byref(lx),C.byref(ly),C.byref(h)),
                               'localdrop respectsdirection/intention',d)
                    for node in (cell*2,cell*2+1):
                        for i in range(world.degree[node]):
                            edge=world.edges[node][i];px=C.c_int();py=C.c_int();face=C.c_int()
                            owner=node&1;cx=info.climb_x;intent=0;facing=0
                            if edge.kind==1:
                                lib.cream_room_walk_pos(node,i,C.byref(px),C.byref(py))
                                west=edge.target//2%5<cell%5;px.value=10 if west else 502;intent=32 if west else 16
                            elif edge.kind==2:
                                px.value=cx*16+16
                                py.value=min(info.upper_bottom[cx],info.upper_bottom[cx+1])*16+12 if edge.target//2==cell else 16
                                intent=64
                            elif edge.kind==3:
                                lib.cream_room_drop_pos(node,i,C.byref(px),C.byref(py));intent=128
                            elif edge.kind==4:
                                lib.cream_room_cave_pos(owner,C.byref(px),C.byref(py));intent=64
                            route=Route();accepted=lib.cream_room_route(node,px.value,py.value,facing,intent,C.byref(route))
                            admits=not edge.require or edge.require==4 or bool(opened[node]&(1<<i))
                            verify((accepted and route.edge==i and route.target==edge.target) if admits else not accepted,
                                   'every real macro route trigger matches graph',detail|{'edge':[node,i],'kind':edge.kind,'xy':[px.value,py.value],
                                   'route':[accepted,route.edge,route.target]})
                            if edge.kind==1:
                                reverse=next(j for j in range(world.degree[edge.target]) if world.edges[edge.target][j].target==node)
                                ax=C.c_int();ay=C.c_int();lib.cream_room_walk_pos(edge.target,reverse,C.byref(ax),C.byref(ay))
                                verify(ay.value==py.value,'reciprocal variable WALK lanes align',detail|{'edge':[node,i]})
                            lib.cream_room_arrival(node,C.byref(edge),C.byref(px),C.byref(py),C.byref(face))
                            target=edge.target//2;build(target,False)
                            verify((not gates and edge.require) or not lib.room_box_solid(px.value-4,py.value-7,px.value+3,py.value-1),'alladmittedmacroarrivals physicallyclear',
                                   detail|{'edge':[node,i],'target':edge.target,'xy':[px.value,py.value]})
                            build(cell)
                    snapshot=bytes(room);saved=bytes(topology)
                    paints=bytes((C.c_uint16*1024).in_dll(lib,'gCreamPolishWallPaint'))
                    roles=bytes((C.c_uint8*768).in_dll(lib,'gCreamPolishShadeRole'))
                    lib.cream_visuals_refresh()
                    verify(bytes(room)==snapshot and bytes(topology)==saved,'cosmeticrefresh preservesnewphysicaltopology',detail)
                    verify(paints==bytes((C.c_uint16*1024).in_dll(lib,'gCreamPolishWallPaint')) and
                           roles==bytes((C.c_uint8*768).in_dll(lib,'gCreamPolishShadeRole')),
                           'cosmeticrefresh preserves complete paint and shade roles',detail)
                    overflow=C.c_uint16.in_dll(lib,'gCreamPolishBlendOverflow').value
                    verify(overflow==0,'nativeblendcapacity neveroverflows',detail)
                    fallbacks=C.c_uint16.in_dll(lib,'gCreamPolishClimbFallbacks').value
                    verify(fallbacks==0,'allcompleteclimbglyphs fitwithoutfallback',detail|{'fallbacks':fallbacks})
                    fall=P.Fall.in_dll(lib,'gCreamPolishFall')
                    if fall.w:widths.add(fall.w)
                    if seed<2 and gates==63:samples.append(dict(**detail,archetype=topology.archetype,
                        heights=heights,climbs=topology.climbs,drops=topology.drops,platforms=topology.platforms,
                        topology_sha256=sha(bytes(topology)),ground_sha256=sha(bytes(room.ground))))
        self.check('geometry','new physical routes/content/elevation invariants',not failures,dict(counts=counts,failures=failures))
        self.check('variety','atleast6actualarchetypes generated',len(archetypes)>=6,dict(archetypes))
        self.check('variety','genuine3pluselevation layouts generated',any(h>=3 and n for h,n in height_sets.items()),dict(height_sets))
        self.check('variety','multiplefloorislands connected byclimbs/drops occur',any(n>=2 and count for n,count in islands.items()),dict(islands))
        report=dict(counts=counts,failures=failures,archetypes=archetypes,height_counts=height_sets,
                    physical_islands=islands,waterfall_widths=sorted(widths),samples=samples,
                    scope='Pinned actualC core room/topology/compositor. Regional furniture is covered separately in actual native runs.')
        (self.out.parent/'geometry-audit.json').write_text(json.dumps(report,indent=2)+'\n')
        return dict(counts)

    def run(self):
        self.provenance();self.identifiers();self.backgrounds();self.sprites();self.other_assets();frames=self.source()
        geometry=self.geometry() if self.args.geometry_seeds else None
        self.check('provenance','candidate unchanged throughaudit',sha(Path(self.args.bundle)/'bartgame.gba')==self.digest)
        self.check('provenance','audited source unchanged throughaudit',self.source_snapshot=={n:sha(ROOT/n) for n in self.source_snapshot})
        report=dict(method=__doc__.strip(),baseline_rom_sha256=BASELINE_SHA,rom_sha256=self.digest,source_commit=self.commit,
            source_sha256=self.source_snapshot,source_native_frames=frames,actual_C_geometry=geometry,
            budgets={a:{k:self.rom.tileset(a)[k] for k in ('tile_count','palette_count')} for a in ('forest','sewer','myst','cream')},
            checks=self.checks,passed=sum(c['passed'] for c in self.checks),total=len(self.checks),failures=[c for c in self.checks if not c['passed']],
            limits='Finite host geometry and readonly native/source fidelity. Actual room motion, mapreadonly behavior and artistic quality have separate mGBA review.')
        self.out.write_text(json.dumps(report,indent=2)+'\n');print('RESULT',report['passed'],'/',report['total'],self.out,flush=True)
        return int(bool(report['failures']))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle');p.add_argument('--baseline',default='/workspace/setup/cream-studies/frozen/style-0-r2')
    p.add_argument('--out',default='/workspace/setup/cream-dynamic/qa/native-audit.json');p.add_argument('--pin');p.add_argument('--geometry-seeds',type=int,default=64)
    p.add_argument('--export-source',action='store_true',help=argparse.SUPPRESS);p.add_argument('--source-options',default='{}',help=argparse.SUPPRESS)
    a=p.parse_args()
    if a.export_source:export_source(json.loads(a.source_options));return 0
    if not a.bundle:p.error('--bundle required')
    return Audit(a).run()


if __name__=='__main__':raise SystemExit(main())

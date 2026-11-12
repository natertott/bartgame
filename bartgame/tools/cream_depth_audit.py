#!/usr/bin/env python3
"""Independent read-only audit of the optional Cream depth refinement.

Decode native ROM 4bpp pixels, BG quarter flips/palettes and animation payloads
without importing the asset builder. The approved exception is Cream paintings,
the Cream-only return doorway, and appended Cream environment metatiles. Existing
IDs, physical metadata, other regions, Bloom, HUD and original music are exact.
This static audit does not establish artistic quality or replace real mGBA drops.
"""
import argparse
import ast
from collections import Counter
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys

from cream_art_study_audit import BASELINE_SHA, native_color, rodata, songs
from sewer_concept_audit import NativeRom, SHAPES, decode_metatile, decode_sprite

ROOT = Path(__file__).resolve().parents[1]
sha = lambda data: hashlib.sha256(data).hexdigest()
INDEX_U8 = ('metatile_type', 'metatile_coll', 'metatile_prop', 'metatile_glitter',
            'forest_v2_canopy_kind', 'forest_v2_water_kind', 'forest_v2_special_tree',
            'forest_v2_overhead', 'forest_v2_low_fringe')
INDEX_U16 = ('forest_v2_visual_parent',)


def export_source(options):
    for name, value in options.items():
        if name.startswith('BART_'): os.environ[name] = str(value)
    os.environ['BART_CREAM'] = '6'
    sys.path.insert(0, str(ROOT/'art'))
    import tiles
    import cream_terrain as terrain
    import cream_actors as actors
    import cream_depth_assets as depth
    output = {'palettes': {name: [native_color(c) for c in colors]
                           for name, colors in terrain.PALETTES.items()},
              'tables': depth.TABLES, 'tiles': {}}
    for mt in tiles.METATILES:
        if not mt['name'].startswith('cream_'): continue
        frames = []
        for rows in mt.get('frames') or [mt['art']]:
            assert len(rows) == 16 and all(len(row) == 16 for row in rows), mt['name']
            frames.append(bytes(0 if c in '. ' else int(c,16) for row in rows for c in row).hex())
        output['tiles'][mt['name'].upper()] = {
            'frames': frames, 'palettes': mt.get('qpals') or [mt['pal']]*4,
            'type': mt['type'], 'coll': mt.get('coll', tiles.default_coll(mt['type'])),
            'prop': int(bool(mt.get('prop'))), 'glitter': int(bool(mt.get('glitter'))),
            'speed': mt.get('anim_speed',8) if len(frames)>1 else None,
        }
    doorway = next(sh for sh in actors.build_sheets() if sh['name']=='creamdoors')
    output['cream_return'] = bytes(0 if c in '. ' else int(c,16)
                                    for row in doorway['frames']['return'] for c in row).hex()
    print(json.dumps(output,separators=(',',':')))


class Audit:
    def __init__(self,args):
        self.args=args
        self.base=NativeRom(args.baseline)
        self.rom=NativeRom(args.bundle)
        self.checks=[]
        self.out=Path(args.out)
        self.out.parent.mkdir(parents=True,exist_ok=True)

    def check(self,group,name,passed,detail=None):
        row={'group':group,'name':name,'passed':bool(passed)}
        if detail is not None:row['detail']=detail
        self.checks.append(row)
        if not passed:print('FAIL',group,name,detail,flush=True)

    def equal(self,group,name,a,b):
        self.check(group,name,a==b,None if a==b else {
            'before_bytes':len(a),'after_bytes':len(b),
            'before_sha256':sha(a),'after_sha256':sha(b)})

    def provenance(self):
        a,b=self.base,self.rom
        self.check('provenance','production baseline exact pin',sha(a.rom)==BASELINE_SHA,sha(a.rom))
        self.check('provenance','optional Cream refinement6',b.defs.get('BART_CREAM_VARIANT')==6)
        self.digest=sha(b.rom)
        if self.args.pin:self.check('provenance','candidate exact supplied pin',self.digest==self.args.pin,self.digest)
        path=Path(self.args.bundle)
        self.options=json.loads((path/'build-options.json').read_text())
        if 'options' in self.options:self.options=self.options['options']
        self.check('provenance','frozen build option agrees with header',int(self.options['BART_CREAM'])==6)
        if 'rom_sha256' in self.options:self.check('provenance','candidate frozen SHA256 pin',self.options['rom_sha256']==self.digest)
        self.commit=(path/'source-commit.txt').read_text().strip()
        files=sorted((ROOT/'art').glob('cream_*.py'))+[ROOT/'art/tiles.py',ROOT/'tools/build_assets.py',
               ROOT/'Makefile',ROOT/'src/cream_room.c',ROOT/'src/cream_visuals.c',ROOT/'src/cream_visuals.h']
        self.source_snapshot={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in files if p.exists()}
        prefix=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','--show-prefix'],text=True).strip()
        mismatch=[]
        for name,digest in self.source_snapshot.items():
            r=subprocess.run(['git','-C',str(ROOT),'show',self.commit+':'+prefix+name],capture_output=True)
            if r.returncode or sha(r.stdout)!=digest:mismatch.append(name)
        self.check('provenance','audited art/runtime matches pinned source commit',not mismatch,mismatch or self.commit)

    def identifiers(self):
        a,b=self.base,self.rom
        self.old_count=a.defs['METATILE_COUNT'];self.new_count=b.defs['METATILE_COUNT']
        self.added={name:index for name,index in b.tile_ids.items() if name not in a.tile_ids}
        self.check('identifiers','old metatile IDs exact',all(b.tile_ids.get(n)==v for n,v in a.tile_ids.items()))
        self.check('identifiers','only contiguous Cream metatiles appended',bool(self.added) and
                   all(n.startswith('CREAM_') for n in self.added) and
                   sorted(self.added.values())==list(range(self.old_count,self.new_count)),len(self.added))
        self.check('identifiers','sprite sheet IDs/count exact',a.sheet_ids==b.sheet_ids)
        keys={k:v for k,v in a.defs.items() if k.startswith(('F_','SHEET_','TS_','PAL_','TT_'))}
        self.check('identifiers','frame/canvas/palette/type/tileset constants exact',all(b.defs.get(k)==v for k,v in keys.items()))
        for name in INDEX_U8+INDEX_U16:
            if name not in a.sections:
                self.check('metadata',name+' remains unlinked/no ROM payload',name not in b.sections)
                continue
            old,new=a.array(name),b.array(name)
            width=2 if name in INDEX_U16 else 1
            self.check('metadata',name+' exact old-indexed prefix',len(old)==self.old_count*width and
                       len(new)==self.new_count*width and old==new[:len(old)])
            if name.startswith('forest_'):
                expected=(struct.pack('<%dH'%len(self.added),*range(self.old_count,self.new_count))
                          if width==2 else bytes(len(self.added)))
                self.equal('metadata',name+' neutral appended classifier',expected,new[len(old):])

    def backgrounds(self):
        a,b=self.base,self.rom
        for area in ('forest','sewer','myst','cream'):
            old,new=a.tileset(area),b.tileset(area)
            self.check('native_limits',area+' BG<=1024',0<new['tile_count']<=1024,new['tile_count'])
            self.check('native_limits',area+' palettes<=12',0<new['palette_count']<=12,new['palette_count'])
            colors=struct.unpack('<%dH'%(len(new['palettes'])//2),new['palettes'])
            self.check('native_limits',area+' RGB555',all(c<0x8000 for c in colors))
            entries=struct.unpack('<%dH'%(len(new['map'])//2),new['map'])
            self.check('native_limits',area+' map entries address resident tiles/palettes',
                       all((e&1023)<new['tile_count'] and (e>>12)<new['palette_count'] for e in entries))
            self.check('native_limits',area+' animation blocks/timings legal',all(
                an['base']+3<new['tile_count'] and an['frames']>1 and an['speed']>0 and
                len(an['data'])==an['frames']*128 for an in new['animations']))
            if area!='cream':
                for field in ('tiles','palettes'):self.equal('retained_'+area,field,old[field],new[field])
                self.equal('retained_'+area,'old map exact prefix',old['map'],new['map'][:self.old_count*8])
                self.equal('retained_'+area,'appended Cream IDs absent',bytes(len(self.added)*8),new['map'][self.old_count*8:])
                self.check('retained_'+area,'complete animation pixels/timing exact',old['animations']==new['animations'])
            else:
                retained=[n for n in a.tile_ids if not n.startswith('CREAM_')]
                for name in retained:
                    p,q=decode_metatile(a,old,name),decode_metatile(b,new,name)
                    self.check('retained_cream_residents',name,p['frames']==q['frames'] and p['speed']==q['speed'])

    def sprites(self):
        a,b=self.base,self.rom
        for name in a.sheet_ids:
            old,op=a.sheet(name);new,np=b.sheet(name)
            self.check('sprite_contracts',name+' exact descriptor',old==new)
            self.check('native_limits',name+' legal OBJ shape/4bpp stride',(new['width'],new['height']) in SHAPES and
                       new['frame_tiles']*64==new['width']*new['height'] and new['tile_count']%new['frame_tiles']==0)
            if name=='creamdoors':
                stride=old['frame_tiles']*32;exception=a.defs['F_CREAMDOORS_RETURN']
                for i in range(old['tile_count']//old['frame_tiles']):
                    if i!=exception:self.equal('retained_sprites',name+' frame'+str(i),op[i*stride:(i+1)*stride],np[i*stride:(i+1)*stride])
                pixels=decode_sprite(np[exception*stride:(exception+1)*stride],new['width'],new['height'])
                self.check('cream_return','16 transparent padding rows',not any(pixels[:16*32]))
            else:self.equal('retained_sprites',name,op,np)

    def other_assets(self):
        a,b=self.base,self.rom
        exclude={'tilesets','sheets','room_defs',*INDEX_U8,*INDEX_U16}
        prefixes=('sheet_','tileset_','metatile_map_','tile_anim_','tile_anims_')
        protected=[n for n in a.sections if n not in exclude and not n.startswith(prefixes)]
        for name in protected:
            self.check('retained_assets',name+' exists',name in b.sections)
            if name in b.sections:self.equal('retained_assets',name,a.array(name),b.array(name))
        for i in range(a.defs['ROOM_COUNT']):
            p=a.unpack('<BB2xIIIB3x',a.symbols['room_defs']+i*20)
            q=b.unpack('<BB2xIIIB3x',b.symbols['room_defs']+i*20)
            self.check('retained_rooms','room descriptor '+str(i),p[:2]+p[-1:]==q[:2]+q[-1:] and
                       tuple(bool(v) for v in p[2:5])==tuple(bool(v) for v in q[2:5]))
        self.equal('retained_music','original PCM section and loop continuations',rodata(a,'original_music_pcm'),rodata(b,'original_music_pcm'))
        self.check('retained_music','resolved titles and descriptors',songs(a)==songs(b))

    def source(self):
        command=[sys.executable,str(Path(__file__).resolve()),'--export-source','--source-options',json.dumps(self.options)]
        result=subprocess.run(command,capture_output=True,text=True,check=True,
                              env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
        source=json.loads(result.stdout)
        (self.out.parent/'source-depth.json').write_text(json.dumps(source,indent=2)+'\n')
        rom=self.rom;ts=rom.tileset('cream');total=0
        self.check('source','complete Cream source IDs match native ROM',set(source['tiles'])=={
            n for n in rom.tile_ids if n.startswith('CREAM_')})
        arrays={name:rom.array('metatile_'+name) for name in ('type','coll','prop','glitter')}
        for name,spec in source['tiles'].items():
            actual=decode_metatile(rom,ts,name);index=rom.tile_ids[name]
            self.check('source',name+' animation count/timing',len(actual['frames'])==len(spec['frames']) and actual['speed']==spec['speed'])
            self.check('source_metadata',name+' exact physical/source contract',
                       arrays['type'][index]==rom.defs['TT_'+spec['type']] and all(
                           arrays[k][index]==spec[k] for k in ('coll','prop','glitter')))
            if name in self.added:
                self.check('appended_contract',name+' opaque visual-only floor/solid',
                           (spec['type'],spec['coll'],spec['prop']) in {('FLOOR',0,0),('SOLID',15,0)} and
                           not spec['glitter'] and all(0 not in bytes.fromhex(f) for f in spec['frames']))
            for number,((indices,colors),frame) in enumerate(zip(actual['frames'],spec['frames'])):
                expected=bytes.fromhex(frame)
                self.equal('source_native_pixels',name+' frame'+str(number),expected,indices)
                rgb=struct.pack('<256H',*[source['palettes'][spec['palettes'][(y//8)*2+x//8]][expected[y*16+x]]
                    if expected[y*16+x] else 0x8000 for y in range(16) for x in range(16)])
                self.equal('source_native_colors',name+' frame'+str(number),rgb,colors);total+=1
        sh,pixels=rom.sheet('creamdoors');stride=sh['frame_tiles']*32;frame=rom.defs['F_CREAMDOORS_RETURN']
        self.equal('source_native_sprites','Cream return doorway exact pixels',bytes.fromhex(source['cream_return']),
                   decode_sprite(pixels[frame*stride:(frame+1)*stride],sh['width'],sh['height']))
        expected=b''.join(struct.pack('<HBB',rom.tile_ids[p['first'].upper()],p['w'],p['h'])
                          for stage in source['tables']['panels'] for p in stage)
        self.equal('native_composition_tables','panel starts/dimensions match native source',expected,rom.array('cream_visual_panels'))
        for stage in source['tables']['panels']:
            self.check('native_composition_tables','seven unequal native panel footprints',
                       [(p['w'],p['h']) for p in stage]==[(4,2),(4,2),(6,2),(6,2),(4,3),(2,2),(2,2)])
            for panel in stage:
                first=rom.tile_ids[panel['first'].upper()]
                ids=range(first,first+panel['w']*panel['h'])
                self.check('native_composition_tables',panel['first']+' solid contiguous full panel',
                           all(i in self.added.values() and arrays['type'][i]==rom.defs['TT_SOLID'] and
                               arrays['coll'][i]==15 and arrays['prop'][i]==0 for i in ids))
        def flatten(values):
            for value in values:
                if isinstance(value,list):yield from flatten(value)
                else:yield rom.tile_ids[value.upper()]
        for key in ('rim','drop','edge','landing','floor_toe','landing_path'):
            ids=list(flatten(source['tables'][key]))
            self.equal('native_composition_tables',key+' resolves exact source IDs',
                       struct.pack('<%dH'%len(ids),*ids),rom.array('cream_visual_'+key))
        return total

    def geometry(self):
        """Compile both pinned actual C room generators in isolated host adapters.

        Room rendering is deliberately a no-op here. The real renderer and
        falling player are covered by the separately recorded native mGBA run.
        """
        from cream_graph_review import World, Edge
        class Room(C.Structure):
            _fields_=[('w',C.c_uint8),('h',C.c_uint8),('ground',C.c_uint16*1024),
                      ('overlay',C.c_uint16*1024),('solid',C.c_uint8*4096),('underlay',C.c_uint16*1024)]
        class Landing(C.Structure):
            _fields_=[('x',C.c_int16),('y',C.c_int16),('from_node',C.c_uint8),('edge',C.c_uint8),
                      ('x0',C.c_uint8),('y0',C.c_uint8),('parts',C.c_uint8),('flags',C.c_uint8)]
        syntax=ast.parse((ROOT/'tools/cream_room_review.py').read_text())
        fixture=next(ast.literal_eval(n.value) for n in syntax.body if isinstance(n,ast.Assign) and
                     any(isinstance(t,ast.Name) and t.id=='FIXTURE' for t in n.targets))
        prefix=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','--show-prefix'],text=True).strip()
        repository=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','--show-toplevel'],text=True).strip()
        def host(label,rom):
            directory=self.out.parent/('host-'+label);directory.mkdir(parents=True,exist_ok=True)
            commit=(rom.directory/'source-commit.txt').read_text().strip()
            def show(name):
                return subprocess.check_output(['git','-C',str(ROOT),'show',commit+':'+prefix+'src/'+name])
            names=subprocess.check_output(['git','-C',repository,'ls-tree','-r','--name-only',commit,'--',prefix+'src'],text=True).splitlines()
            for name in names:
                if name.endswith(('.h','.inc')):(directory/Path(name).name).write_bytes(show(Path(name).name))
            (directory/'assets.h').write_text(rom.header)
            sources=['cream_world.c','cream_room.c']+(['cream_visuals.c'] if label=='depth' else [])
            for name in sources:(directory/name).write_bytes(show(name))
            aliases=[]
            for index,name in enumerate(n for n in rom.sections if n.startswith(('metatile_','cream_visual_'))):
                data=rom.array(name)
                aliases.append('const unsigned char audit_asset_%d[] __asm__("%s") '
                               '__attribute__((aligned(4)))={%s};'%(index,name,','.join(map(str,data))))
            (directory/'meta.inc').write_text('\n'.join(aliases)+'\n')
            (directory/'host.c').write_text(fixture)
            command=['gcc','-shared','-fPIC','-O2','-w','-fno-builtin','-I',str(directory),
                     *[str(directory/name) for name in sources],str(directory/'host.c'),'-o',str(directory/'room.so')]
            result=subprocess.run(command,capture_output=True,text=True)
            (directory/'compile.log').write_text(result.stdout+result.stderr);result.check_returncode()
            library=C.CDLL(str(directory/'room.so'))
            library.cream_generate.argtypes=[C.c_uint32];library.cream_generate.restype=C.c_uint8
            library.cream_room_arrival.argtypes=[C.c_int,C.POINTER(Edge),C.POINTER(C.c_int),C.POINTER(C.c_int),C.POINTER(C.c_int)]
            library.cream_room_feature_reserved.restype=C.c_uint8
            return library
        before,after=host('baseline',self.base),host('depth',self.rom)
        worlds=[World.in_dll(lib,'gCreamWorld') for lib in (before,after)]
        rooms=[Room.in_dll(lib,'gRoom') for lib in (before,after)]
        opened=[(C.c_uint8*50).in_dll(lib,'gCreamOpenEdges') for lib in (before,after)]
        meta=[{key:rom.array('metatile_'+key) for key in ('type','coll','prop','glitter')}
              for rom in (self.base,self.rom)]
        landing_ids=struct.unpack('<18H',self.rom.array('cream_visual_landing'))
        path_ids=struct.unpack('<72H',self.rom.array('cream_visual_landing_path'))
        old_names={v:k for k,v in self.base.tile_ids.items()}
        count=Counter();failures=[]
        def verify(ok,name,detail):
            count[name]+=1
            if not ok and len(failures)<100:failures.append({'name':name,**detail})
        def typed(room,table,layer,key):
            return bytes(255 if value==65535 else table[key][value] for value in getattr(room,layer)[:768])
        info_size=118
        for seed in range(self.args.geometry_seeds):
            for lib in (before,after):assert lib.cream_generate(seed)
            verify(bytes(worlds[0])==bytes(worlds[1]),'directed graph exact',{'seed':seed})
            for gate_state in (0,63):
                for values in opened:
                    for n in range(50):values[n]=gate_state
                for cell in range(25):
                    for values in opened:
                        for n in range(50):values[n]=gate_state
                    detail={'seed':seed,'cell':cell,'gates':gate_state}
                    for lib in (before,after):lib.cream_room_build(cell)
                    count['room_builds']+=1
                    verify(bytes(rooms[0].solid)==bytes(rooms[1].solid),'8px collision exact',detail)
                    verify(bytes(rooms[0].overlay)==bytes(rooms[1].overlay),'original overlays exact IDs/placement',detail)
                    verify(bytes((C.c_uint8*info_size).in_dll(before,'gCreamRoom'))==
                           bytes((C.c_uint8*info_size).in_dll(after,'gCreamRoom')),'room profile/features exact',detail)
                    for layer in ('ground','overlay','underlay'):
                        for key in ('type','coll','prop','glitter'):
                            verify(typed(rooms[0],meta[0],layer,key)==typed(rooms[1],meta[1],layer,key),
                                   layer+' '+key+' exact',detail)
                    world=worlds[1]
                    expected={(n,i) for n in range(50) for i in range(world.degree[n])
                              if world.edges[n][i].kind==3 and world.edges[n][i].target//2==cell}
                    size=C.c_uint16.in_dll(after,'gCreamVisualLandingCount').value
                    verify(size==len(expected),'complete incoming drop cache',detail|{'count':size,'expected':len(expected)})
                    if size>300:raise AssertionError('landing cache overflow')
                    cache=(Landing*300).in_dll(after,'gCreamVisualLandings')
                    found=set()
                    for anchor in cache[:size]:
                        pair=(anchor.from_node,anchor.edge);found.add(pair)
                        verify(pair in expected,'cache contains only real incoming drop edges',detail|{'edge':pair})
                        if pair not in expected:continue
                        edge=world.edges[pair[0]][pair[1]];x=C.c_int();y=C.c_int();face=C.c_int()
                        after.cream_room_arrival(pair[0],C.byref(edge),C.byref(x),C.byref(y),C.byref(face))
                        verify((anchor.x,anchor.y)==(x.value,y.value),'anchor exact authoritative arrival',detail|{'edge':pair})
                        active=not edge.require or edge.require==4 or gate_state==63
                        verify(bool(anchor.flags&4)==active,'shadow active only for physical admitted source',detail|{'edge':pair})
                        verify((anchor.x0,anchor.y0)==(anchor.x//16-1,anchor.y//16),'shadow follows landing feet',detail|{'edge':pair})
                        if not active:verify(anchor.parts==0,'closed source has no landing cue',detail|{'edge':pair})
                        foot_x,foot_y=anchor.x//16,anchor.y//16
                        if active and 0<=foot_x<32 and 0<=foot_y<24:
                            foot_at=foot_y*32+foot_x;original=rooms[0].ground[foot_at]
                            if old_names[original].startswith(('CREAM_FLOOR_','CREAM_PATH_')):
                                verify(bool(anchor.parts&2),'actual landing feet receive shadow center',detail|{'edge':pair})
                        for part in range(6):
                            if not (anchor.parts>>part)&1:continue
                            xx,yy=anchor.x0+part%3,anchor.y0+part//3
                            valid=0<=xx<32 and 0<=yy<24
                            verify(valid,'painted shadow within room',detail|{'xy':[xx,yy]})
                            if valid:
                                at=yy*32+xx
                                original=rooms[0].ground[at]
                                verify(meta[0]['type'][original]==self.base.defs['TT_FLOOR'] and
                                       meta[0]['coll'][original]==0 and meta[0]['prop'][original]==0 and
                                       rooms[0].overlay[at]==rooms[1].overlay[at],
                                       'shadow uses dry traversable substrate preserving overlay',detail|{'xy':[xx,yy],'edge':pair})
                                verify(rooms[1].ground[at] in self.added.values(),
                                       'reported painted part is real new native art',detail|{'xy':[xx,yy]})
                                stage=min(world.corruption[cell],2)
                                allowed={landing_ids[stage*6+part],*[path_ids[stage*24+v*6+part] for v in range(4)]}
                                verify(rooms[1].ground[at] in allowed,'painted shadow uses correct stage/part table',
                                       detail|{'xy':[xx,yy],'edge':pair,'part':part})
                                count['painted_shadow_parts']+=1
                    verify(found==expected,'drop cache no omissions/duplicates',detail)
                    snapshot=bytes(rooms[1]);cache_snapshot=bytes(cache)[:size*C.sizeof(Landing)]
                    after.cream_visuals_refresh()
                    verify(bytes(rooms[1])==snapshot,'visual refresh idempotent room pixels/contracts',detail)
                    verify(C.c_uint16.in_dll(after,'gCreamVisualLandingCount').value==size and
                           bytes(cache)[:size*C.sizeof(Landing)]==cache_snapshot,'visual refresh idempotent landing cache',detail)
                    if not gate_state and seed<8:
                        for node in (cell*2,cell*2+1):
                            for index in range(world.degree[node]):
                                if not world.edges[node][index].require:continue
                                before.cream_room_unlock_edge(node,index);after.cream_room_unlock_edge(node,index)
                                unlocked=detail|{'edge':[node,index]}
                                verify(bytes(rooms[0].solid)==bytes(rooms[1].solid),'real gate unlock collision exact',unlocked)
                                verify(bytes(rooms[0].overlay)==bytes(rooms[1].overlay),'real gate unlock overlays exact',unlocked)
                                for layer in ('ground','underlay'):
                                    for key in ('type','coll','prop','glitter'):
                                        verify(typed(rooms[0],meta[0],layer,key)==typed(rooms[1],meta[1],layer,key),
                                               'real gate unlock '+layer+' '+key+' exact',unlocked)
        self.check('actual_C_geometry','graph/physics/room content/landing-coordinate sweep',not failures,
                   {'counts':dict(count),'failures':failures,'seeds':self.args.geometry_seeds,
                    'gate_states':'all physically closed and all physically opened',
                    'scope':'Host actual pinned C generators; renderer stubbed; real mGBA proof separate'})
        (self.out.parent/'geometry-audit.json').write_text(json.dumps({'counts':dict(count),'failures':failures},indent=2)+'\n')
        return dict(count)

    def run(self):
        self.provenance();self.identifiers();self.backgrounds();self.sprites();self.other_assets();frames=self.source()
        geometry=self.geometry() if self.args.geometry_seeds else None
        self.check('provenance','candidate unchanged throughout audit',sha((Path(self.args.bundle)/'bartgame.gba').read_bytes())==self.digest)
        self.check('provenance','baseline unchanged throughout audit',sha((Path(self.args.baseline)/'bartgame.gba').read_bytes())==BASELINE_SHA)
        self.check('provenance','audited source unchanged throughout audit',self.source_snapshot=={
            n:sha((ROOT/n).read_bytes()) for n in self.source_snapshot})
        report={'method':__doc__.strip(),'baseline_rom_sha256':BASELINE_SHA,'rom_sha256':self.digest,
                'source_commit':self.commit,'source_sha256':self.source_snapshot,
                'appended_metatiles':self.added,'source_native_frames':frames,
                'actual_C_geometry':geometry,
                'budgets':{a:{k:self.rom.tileset(a)[k] for k in ('tile_count','palette_count')}
                           for a in ('forest','sewer','myst','cream')},
                'checks':self.checks,'passed':sum(c['passed'] for c in self.checks),'total':len(self.checks),
                'failures':[c for c in self.checks if not c['passed']],
                'limits':'Read-only ROM/source audit. It does not certify artistic quality, actual landing visibility, '
                         'runtime coordinate correspondence, room composition or collision agreement in play; '
                         'those require the separate geometry and real mGBA reviews.'}
        self.out.write_text(json.dumps(report,indent=2)+'\n')
        print('RESULT','FAIL' if report['failures'] else 'PASS',str(report['passed'])+'/'+str(report['total']),str(self.out))
        return bool(report['failures'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',default='/workspace/setup/cream-studies/frozen/style-0-r2')
    p.add_argument('--bundle',default='/workspace/setup/cream-depth/frozen/style-6')
    p.add_argument('--out',default='/workspace/setup/cream-depth/audit/native-audit.json')
    p.add_argument('--pin')
    p.add_argument('--geometry-seeds',type=int,default=64,help='actual C geometry seeds;0 skips host sweep')
    p.add_argument('--export-source',action='store_true',help=argparse.SUPPRESS)
    p.add_argument('--source-options',default='{}',help=argparse.SUPPRESS)
    a=p.parse_args()
    if a.export_source:export_source(json.loads(a.source_options));return 0
    return Audit(a).run()


if __name__=='__main__':raise SystemExit(main())

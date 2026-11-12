#!/usr/bin/env python3
"""Independent native-ROM and actual-C checks for Cream polish studies7..11.

The audit decodes 4bpp BG pixels, quarter flips, palette entries and animation
payloads independently of the builder. Physical and art-role checks use pinned
actual room C code in isolated host adapters. Real mGBA input/captures qualify
visible blending, ladder motion, flowing water and supported drop landings.
"""
import argparse
import ast
from collections import Counter
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys

import cream_depth_audit as D
from cream_art_study_audit import BASELINE_SHA, native_color
from sewer_concept_audit import NativeRom, decode_metatile, decode_sprite

ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p if isinstance(p,bytes) else Path(p).read_bytes()).hexdigest()


def source_export(options):
    for name,value in options.items():
        if name.startswith('BART_'):os.environ[name]=str(value)
    sys.path.insert(0,str(ROOT/'art'))
    import tiles
    import cream_terrain as terrain
    import cream_actors as actors
    import cream_polish_assets as polish
    out=dict(palettes={name:[native_color(c) for c in bank] for name,bank in terrain.PALETTES.items()},
             tables=polish.TABLES,tiles={})
    for mt in tiles.METATILES:
        if not mt['name'].startswith('cream_'):continue
        if mt['name'].startswith('cream_depth_'):continue
        frames=[]
        for rows in mt.get('frames') or [mt['art']]:
            assert len(rows)==16 and all(len(row)==16 for row in rows),mt['name']
            frames.append(bytes(0 if c in '. ' else int(c,16) for row in rows for c in row).hex())
        out['tiles'][mt['name'].upper()]=dict(frames=frames,palettes=mt.get('qpals') or [mt['pal']]*4,
            type=mt['type'],coll=mt.get('coll',tiles.default_coll(mt['type'])),
            prop=int(bool(mt.get('prop'))),glitter=int(bool(mt.get('glitter'))),
            speed=mt.get('anim_speed',8) if len(frames)>1 else None)
    doorway=next(s for s in actors.build_sheets() if s['name']=='creamdoors')
    out['cream_return']=bytes(0 if c in '. ' else int(c,16)
                             for row in doorway['frames']['return'] for c in row).hex()
    print(json.dumps(out,separators=(',',':')))


class Room(C.Structure):
    _fields_=[('w',C.c_uint8),('h',C.c_uint8),('ground',C.c_uint16*1024),
              ('overlay',C.c_uint16*1024),('solid',C.c_uint8*4096),('underlay',C.c_uint16*1024)]


class Landing(C.Structure):
    _fields_=[('x',C.c_int16),('y',C.c_int16),('from_node',C.c_uint8),('edge',C.c_uint8),
              ('x0',C.c_uint8),('y0',C.c_uint8),('parts',C.c_uint8),('flags',C.c_uint8)]


class Fall(C.Structure):
    _fields_=[('x',C.c_uint8),('y',C.c_uint8),('w',C.c_uint8),('h',C.c_uint8)]


class Audit(D.Audit):
    def provenance(self):
        a,b=self.base,self.rom
        self.check('provenance','production baseline exact pin',sha(a.rom)==BASELINE_SHA)
        self.profile=b.defs.get('BART_CREAM_VARIANT')
        self.check('provenance','optional Cream polish profile7..11',self.profile in range(7,12),self.profile)
        self.digest=sha(b.rom)
        if self.args.pin:self.check('provenance','candidate exact supplied pin',self.digest==self.args.pin)
        self.options=json.loads((Path(self.args.bundle)/'build-options.json').read_text())
        if 'options' in self.options:self.options=self.options['options']
        self.check('provenance','frozen option/header agree',int(self.options['BART_CREAM'])==self.profile)
        if 'rom_sha256' in self.options:self.check('provenance','candidate frozen SHA256 pin',self.options['rom_sha256']==self.digest)
        self.commit=(Path(self.args.bundle)/'source-commit.txt').read_text().strip()
        files=sorted((ROOT/'art').glob('cream_*.py'))+[ROOT/'art/tiles.py',ROOT/'tools/build_assets.py',ROOT/'Makefile',
            ROOT/'src/cream_room.c',ROOT/'src/cream_visuals.c',ROOT/'src/cream_visuals.h',
            ROOT/'src/cream_polish.c',ROOT/'src/cream_polish.h',ROOT/'src/cream_polish_blend.c',
            ROOT/'src/cream_polish_blend.h',ROOT/'src/room.c',ROOT/'src/game.c']
        self.source_snapshot={str(p.relative_to(ROOT)):sha(p) for p in files if p.exists()}
        prefix=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','--show-prefix'],text=True).strip()
        mismatch=[]
        for name,digest in self.source_snapshot.items():
            result=subprocess.run(['git','-C',str(ROOT),'show',self.commit+':'+prefix+name],capture_output=True)
            if result.returncode or sha(result.stdout)!=digest:mismatch.append(name)
        self.check('provenance','audited art/runtime matches pinned source',not mismatch,mismatch or self.commit)

    def source(self):
        command=[sys.executable,str(Path(__file__).resolve()),'--export-source','--source-options',json.dumps(self.options)]
        result=subprocess.run(command,capture_output=True,text=True,check=True,
                              env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
        source=json.loads(result.stdout);self.source_data=source
        (self.out.parent/'source-native.json').write_text(json.dumps(source,indent=2)+'\n')
        rom=self.rom;ts=rom.tileset('cream');total=0
        self.check('source','complete resident Cream source/native IDs',set(source['tiles'])=={
            n for n in rom.tile_ids if n.startswith('CREAM_') and not n.startswith('CREAM_DEPTH_')})
        old_depth={n:i for n,i in rom.tile_ids.items() if n.startswith('CREAM_DEPTH_')}
        self.check('native_limits','polish staticCream<=896 leaving128 blendchars',ts['tile_count']<=896,ts['tile_count'])
        self.check('retained_nonresident','old Cream6 depth IDs remain blank/nonresident',
                   all(rom.array('metatile_map_cream')[i*8:i*8+8]==bytes(8) for i in old_depth),len(old_depth))
        arrays={key:rom.array('metatile_'+key) for key in ('type','coll','prop','glitter')}
        for name,spec in source['tiles'].items():
            actual=decode_metatile(rom,ts,name);index=rom.tile_ids[name]
            self.check('source',name+' frames/timing',len(actual['frames'])==len(spec['frames']) and actual['speed']==spec['speed'])
            self.check('source_metadata',name+' exact native/source contract',
                       arrays['type'][index]==rom.defs['TT_'+spec['type']] and
                       all(arrays[key][index]==spec[key] for key in ('coll','prop','glitter')))
            if name in self.added:
                self.check('appended_contract',name+' legal visual-only terrain',
                    (spec['type'],spec['coll'],spec['prop']) in {('FLOOR',0,0),('SOLID',15,0),('CLIMB',0,0)}
                    and not spec['glitter'] and
                    ('_PANEL_' in name or all(0 not in bytes.fromhex(frame) for frame in spec['frames'])))
            for number,((indices,colors),frame) in enumerate(zip(actual['frames'],spec['frames'])):
                expected=bytes.fromhex(frame)
                self.equal('native_pixels',name+' frame'+str(number),expected,indices)
                expected_rgb=struct.pack('<256H',*[source['palettes'][spec['palettes'][(y//8)*2+x//8]][expected[y*16+x]]
                    if expected[y*16+x] else 0x8000 for y in range(16) for x in range(16)])
                self.equal('native_colors',name+' frame'+str(number),expected_rgb,colors);total+=1
        sheet,pixels=rom.sheet('creamdoors');stride=sheet['frame_tiles']*32;frame=rom.defs['F_CREAMDOORS_RETURN']
        self.equal('native_sprite','Cream return frame exact source',bytes.fromhex(source['cream_return']),
                   decode_sprite(pixels[frame*stride:(frame+1)*stride],sheet['width'],sheet['height']))
        def flatten(values):
            for v in values:
                if isinstance(v,list):yield from flatten(v)
                elif isinstance(v,str):yield rom.tile_ids[v.upper()]
                elif v is None:yield 65535
                else:raise TypeError(type(v))
        panels=source['tables'].get('panels',[])
        alpha=rom.array('cream_polish_tile_alpha')
        expected_alpha=[]
        for i in range(ts['tile_count']):
            packed=ts['tiles'][i*32:(i+1)*32]
            values=[v for b in packed for v in (b&15,b>>4)]
            expected_alpha.append(0 if not any(values) else 1 if all(values) else 2)
        self.equal('native_blend','static tile alpha classes match independently decoded4bpp',bytes(expected_alpha),alpha)
        if panels:
            expected=b''.join(struct.pack('<HBB',rom.tile_ids[p['first'].upper()],p['w'],p['h'])
                              for stage in panels for p in stage)
            symbol=next((s for s in ('cream_polish_panels','cream_visual_panels') if s in rom.sections),None)
            self.check('native_tables','panel table exists',symbol is not None)
            if symbol:self.equal('native_tables','panel starts/footprints',expected,rom.array(symbol))
            for stage in panels:
                for p in stage:
                    first=rom.tile_ids[p['first'].upper()];w,h=p['w'],p['h']
                    self.check('native_tables',p['first']+' contiguous solid footprint',
                        all(i in self.added.values() and arrays['type'][i]==rom.defs['TT_SOLID'] and arrays['coll'][i]==15
                            for i in range(first,first+w*h)))
                    master=bytearray(w*16*h*16)
                    for dy in range(h):
                        for dx in range(w):
                            mt=first+dy*w+dx
                            name=next(n for n,index in rom.tile_ids.items() if index==mt)
                            indices=bytes.fromhex(source['tiles'][name]['frames'][0])
                            for yy in range(16):
                                start=(dy*16+yy)*w*16+dx*16
                                master[start:start+16]=indices[yy*16:(yy+1)*16]
                    border=[master[y*w*16+x] for y in range(h*16) for x in range(w*16)
                            if x<2 or y<2 or x>=w*16-2 or y>=h*16-2]
                    self.check('native_blend',p['first']+' complete silhouette has safe2px alpha margin',not any(border))
        for key,values in source['tables'].items():
            if key=='panels':continue
            symbol=next((prefix+key for prefix in ('cream_polish_','cream_visual_') if prefix+key in rom.sections),None)
            if not symbol:continue
            try:ids=list(flatten(values))
            except (TypeError,KeyError):continue
            self.equal('native_tables',symbol+' exact source IDs',struct.pack('<%dH'%len(ids),*ids),rom.array(symbol))
        blue=source['palettes'].get('cream_water',[])
        # RGB555's blue field occupies bits10..14. The body's middle inks
        # must be recognizably blue rather than the previous beige-green.
        self.check('water_color','native water body blue exceeds red',len(blue)==16 and
            sum(((color>>10)&31)-(color&31) for color in blue[3:9])>24,blue[3:9])
        return total

    def host(self,label,rom):
        from cream_graph_review import Edge
        directory=self.out.parent/('host-'+label);directory.mkdir(parents=True,exist_ok=True)
        commit=(rom.directory/'source-commit.txt').read_text().strip()
        prefix=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','--show-prefix'],text=True).strip()
        repository=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','--show-toplevel'],text=True).strip()
        def show(name):return subprocess.check_output(['git','-C',str(ROOT),'show',commit+':'+prefix+'src/'+name])
        names=subprocess.check_output(['git','-C',repository,'ls-tree','-r','--name-only',commit,'--',prefix+'src'],text=True).splitlines()
        for name in names:
            if name.endswith(('.h','.inc')):(directory/Path(name).name).write_bytes(show(Path(name).name))
        (directory/'assets.h').write_text(rom.header)
        sources=['cream_world.c','cream_room.c']+(['cream_polish.c','cream_polish_blend.c'] if label=='polish' else [])
        for name in sources:(directory/name).write_bytes(show(name))
        aliases=[];alias_names={}
        for index,name in enumerate(n for n in rom.sections if n.startswith(('metatile_','cream_visual_','cream_polish_')) or
                                    n in ('tileset_cream_tiles','tileset_cream_pals')):
            data=rom.array(name)
            alias_names[name]='audit_asset_'+str(index)
            aliases.append('const unsigned char audit_asset_%d[] __asm__("%s") __attribute__((aligned(4)))={%s};'
                           %(index,name,','.join(map(str,data))))
        if label=='polish':
            ts=rom.tileset('cream')
            aliases.append('const Tileset tilesets[4]={[TS_CREAM]={.tiles=(const u16*)%s,.tile_count=%d,'
                           '.map=(const u16*)%s,.anims=0,.anim_count=0,.pals=(const u16*)%s,.pal_count=%d}};'%
                           (alias_names['tileset_cream_tiles'],ts['tile_count'],alias_names['metatile_map_cream'],
                            alias_names['tileset_cream_pals'],ts['palette_count']))
        (directory/'meta.inc').write_text('\n'.join(aliases)+'\n')
        syntax=ast.parse((ROOT/'tools/cream_room_review.py').read_text())
        fixture=next(ast.literal_eval(n.value) for n in syntax.body if isinstance(n,ast.Assign) and
                     any(isinstance(t,ast.Name) and t.id=='FIXTURE' for t in n.targets))
        (directory/'host.c').write_text(fixture)
        command=['gcc','-shared','-fPIC','-O2','-w','-fno-builtin','-DCREAM_POLISH_HOST_AUDIT=1','-I',str(directory),
                 *[str(directory/name) for name in sources],str(directory/'host.c'),'-o',str(directory/'room.so')]
        result=subprocess.run(command,capture_output=True,text=True)
        (directory/'compile.log').write_text(result.stdout+result.stderr);result.check_returncode()
        lib=C.CDLL(str(directory/'room.so'))
        lib.cream_generate.argtypes=[C.c_uint32];lib.cream_generate.restype=C.c_uint8
        lib.cream_room_arrival.argtypes=[C.c_int,C.POINTER(Edge),C.POINTER(C.c_int),C.POINTER(C.c_int),C.POINTER(C.c_int)]
        lib.cream_room_feature_reserved.restype=C.c_uint8
        return lib

    def geometry(self):
        from cream_graph_review import World
        from cream_art_study_capture import Info
        before,after=self.host('control',self.base),self.host('polish',self.rom)
        worlds=[World.in_dll(lib,'gCreamWorld') for lib in (before,after)]
        rooms=[Room.in_dll(lib,'gRoom') for lib in (before,after)]
        infos=[Info.in_dll(lib,'gCreamRoom') for lib in (before,after)]
        opened=[(C.c_uint8*50).in_dll(lib,'gCreamOpenEdges') for lib in (before,after)]
        meta=[{key:rom.array('metatile_'+key) for key in ('type','coll','prop','glitter')} for rom in (self.base,self.rom)]
        names=[{index:name for name,index in rom.tile_ids.items()} for rom in (self.base,self.rom)]
        counts=Counter();failures=[];widths=set()
        panel_specs=[(self.rom.tile_ids[p['first'].upper()],p['w'],p['h'])
                     for stage in self.source_data['tables']['panels'] for p in stage]
        def verify(ok,name,detail):
            counts[name]+=1
            if not ok and len(failures)<100:failures.append(dict(name=name,**detail))
        def typed(room,table,layer,key):
            return bytes(255 if v==65535 else table[key][v] for v in getattr(room,layer)[:768])
        def same(detail):
            verify(bytes(rooms[0].solid)==bytes(rooms[1].solid),'8px collision exact',detail)
            verify(bytes(rooms[0].overlay)==bytes(rooms[1].overlay),'semantic overlays exact IDs',detail)
            verify(bytes(infos[0])==bytes(infos[1]),'room profile/features exact',detail)
            for layer in ('ground','overlay','underlay'):
                for key in ('type','coll','prop','glitter'):
                    verify(typed(rooms[0],meta[0],layer,key)==typed(rooms[1],meta[1],layer,key),layer+' '+key+' exact',detail)
        for seed in range(self.args.geometry_seeds):
            for lib in (before,after):assert lib.cream_generate(seed)
            verify(bytes(worlds[0])==bytes(worlds[1]),'directed graph exact',dict(seed=seed))
            for gates in (0,63):
                for cell in range(25):
                    for op in opened:
                        for n in range(50):op[n]=gates
                    before.cream_room_build(cell);after.cream_room_build(cell)
                    # Polish is intentionally deferred until gameplay's
                    # regional stamping phase has finished. The host core
                    # scope has no regional stamps, so finalize it here.
                    after.cream_visuals_build()
                    detail=dict(seed=seed,cell=cell,gates=gates);same(detail);counts['room_builds']+=1
                    world=worlds[1];stage=min(world.corruption[cell],2)
                    roles=(C.c_uint8*768).in_dll(after,'gCreamPolishShadeRole')
                    paint=(C.c_uint16*1024).in_dll(after,'gCreamPolishWallPaint')
                    mids={self.base.defs['MT_CREAM_CLIFF_MID_S%d_V%d'%(stage,v)] for v in range(2)}
                    for at,mt in enumerate(paint[:768]):
                        if mt==65535:continue
                        x,y=at%32,at//32
                        verify(rooms[0].ground[at] in mids and rooms[0].overlay[at]==65535 and
                               not before.cream_room_feature_reserved(x,y),
                               'render-only masked wall stays on eligible original midface',detail|{'xy':[x,y]})
                        spec=next(((first,w,h) for first,w,h in panel_specs if first<=mt<first+w*h),None)
                        verify(spec is not None,'render-only paint has actual whole-panel source',detail|{'xy':[x,y],'id':mt})
                        if spec:
                            first,w,h=spec;part=mt-first;x0=x-part%w;y0=y-part//w
                            verify(x0>=0 and y0>=0 and x0+w<=32 and y0+h<=24 and
                                   all(paint[(y0+dy)*32+x0+dx]==first+dy*w+dx for dy in range(h) for dx in range(w)),
                                   'every masked panel admitted as complete unsliced footprint',detail|{'xy':[x,y],'id':mt})
                        counts['masked_paint_cells']+=1
                    for at,role in enumerate(roles):
                        verify(role<=3,'shade role legal',detail|{'xy':[at%32,at//32]})
                        if role:
                            mt=rooms[0].ground[at]
                            verify(meta[0]['type'][mt]==self.base.defs['TT_FLOOR'] and meta[0]['coll'][mt]==0 and meta[0]['prop'][mt]==0,
                                   'shade only dry floor/path',detail|{'xy':[at%32,at//32]})
                            actual_name=names[1].get(rooms[1].ground[at],'')
                            verify(('LANDING' in actual_name if role==3 else 'SHADE' in actual_name or 'SHADOW' in actual_name),
                                   'shade role corresponds actual shade artwork',detail|{'xy':[at%32,at//32],'id':rooms[1].ground[at]})
                            counts['shade_cells']+=1
                    fall=Fall.in_dll(after,'gCreamPolishFall')
                    if fall.w:
                        widths.add(fall.w)
                        verify(1<=fall.w<=3 and 0<=fall.x<32 and 0<=fall.y<24 and fall.x+fall.w<=32 and fall.y+fall.h<=24,
                               'generated waterfall footprint legal',detail|{'fall':list(bytes(fall))})
                        for yy in range(fall.y,fall.y+fall.h):
                            for xx in range(fall.x,fall.x+fall.w):
                                at=yy*32+xx;original=rooms[0].ground[at]
                                verify(meta[0]['type'][original]==self.base.defs['TT_SOLID'] and meta[0]['coll'][original]==15 and
                                       rooms[0].overlay[at]==65535 and not before.cream_room_feature_reserved(xx,yy),
                                       'waterfall only measured unoccupied solid face',detail|{'xy':[xx,yy]})
                                verify('FALL' in names[1].get(rooms[1].ground[at],''),'fall telemetry matches nativewater art',detail|{'xy':[xx,yy]})
                    expected={(n,i) for n in range(50) for i in range(world.degree[n])
                              if world.edges[n][i].kind==3 and world.edges[n][i].target//2==cell}
                    size=C.c_uint16.in_dll(after,'gCreamVisualLandingCount').value
                    verify(size==len(expected),'complete incoming drop cache',detail)
                    if size>300:raise AssertionError('landing cache overflow')
                    cache=(Landing*300).in_dll(after,'gCreamVisualLandings');found=set()
                    for entry in cache[:size]:
                        pair=entry.from_node,entry.edge;found.add(pair)
                        if pair not in expected:verify(False,'only real incoming drop records',detail|{'edge':pair});continue
                        edge=world.edges[pair[0]][pair[1]];xx=C.c_int();yy=C.c_int();face=C.c_int()
                        after.cream_room_arrival(pair[0],C.byref(edge),C.byref(xx),C.byref(yy),C.byref(face))
                        verify((entry.x,entry.y)==(xx.value,yy.value),'anchor exact actual gameplay arrival',detail|{'edge':pair})
                        active=not edge.require or edge.require==4 or gates==63
                        verify(bool(entry.flags&4)==active,'shadow source gate admission truthful',detail|{'edge':pair})
                        if not active:verify(entry.parts==0,'closed source no terminal cue',detail|{'edge':pair});continue
                        fx,fy=entry.x//16,entry.y//16
                        if 0<=fx<32 and 0<=fy<24:
                            verify(roles[fy*32+fx]>0,'actual landing feet shaded',detail|{'edge':pair})
                            # Independently find the first supporting solid cell
                            # above this actual arrival through compatible floor.
                            top=fy
                            while top>0:
                                mt=rooms[0].ground[(top-1)*32+fx]
                                if meta[0]['type'][mt]!=self.base.defs['TT_FLOOR'] or meta[0]['coll'][mt] or meta[0]['prop'][mt]:break
                                top-=1
                            if top>0 and (meta[0]['coll'][rooms[0].ground[(top-1)*32+fx]]==15 or
                                          meta[0]['type'][rooms[0].ground[(top-1)*32+fx]]==self.base.defs['TT_CLIMB']):
                                for sy in range(top,fy+1):
                                    verify(roles[sy*32+fx]>0,'shadow connected from real wall toe to actual feet',
                                           detail|{'edge':pair,'xy':[fx,sy],'toe_row':top,'foot_row':fy})
                    verify(found==expected,'incoming cache no omitted/duplicate edge',detail)
                    snapshot=bytes(rooms[1]);saved_roles=bytes(roles);saved_cache=bytes(cache)[:size*C.sizeof(Landing)];saved_fall=bytes(fall);saved_paint=bytes(paint)
                    after.cream_visuals_refresh()
                    verify(bytes(rooms[1])==snapshot,'refresh pixel/contract idempotent',detail)
                    verify(bytes(roles)==saved_roles and bytes(fall)==saved_fall and bytes(cache)[:size*C.sizeof(Landing)]==saved_cache and bytes(paint)==saved_paint,
                           'refresh telemetry idempotent',detail)
                    if gates==0 and seed<8:
                        for node in (cell*2,cell*2+1):
                            for index in range(world.degree[node]):
                                if not world.edges[node][index].require:continue
                                before.cream_room_unlock_edge(node,index);after.cream_room_unlock_edge(node,index)
                                same(detail|{'unlock':[node,index]});counts['real_unlocks']+=1
        self.check('actual_C_geometry','pinned physical/connectedshade/waterfall sweep',not failures,
                   dict(counts=counts,failures=failures,seeds=self.args.geometry_seeds,waterfall_widths=sorted(widths)))
        self.check('waterfall_variation','all requested generated widths1/2/3 occur',widths=={1,2,3},sorted(widths))
        (self.out.parent/'geometry-audit.json').write_text(json.dumps(dict(counts=counts,failures=failures,waterfall_widths=sorted(widths)),indent=2)+'\n')
        return dict(counts)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',default='/workspace/setup/cream-studies/frozen/style-0-r2')
    parser.add_argument('--bundle',required=False)
    parser.add_argument('--out',default='/workspace/setup/cream-polish/qa/audit.json')
    parser.add_argument('--pin')
    parser.add_argument('--geometry-seeds',type=int,default=64)
    parser.add_argument('--export-source',action='store_true',help=argparse.SUPPRESS)
    parser.add_argument('--source-options',default='{}',help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.export_source:source_export(json.loads(args.source_options));return 0
    if not args.bundle:parser.error('--bundle is required')
    return Audit(args).run()


if __name__=='__main__':raise SystemExit(main())

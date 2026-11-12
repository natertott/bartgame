#!/usr/bin/env python3
"""Actual mGBA review of Cream12 terrain, local traversal and ten map concepts.

Room surveys use the existing frozen registered renderer hook; ordinary clips
use fresh live cores, real keys and positive health. Explicit seed, ordinary
room-load requests and hero position/facing navigation are disclosed fixtures.
The atlas fixture visits generated rooms through ordinary load requests rather
than writing discovery/inventory/progression results. Pause-map captures prove
readonly game state, not an unassisted exploration route.
"""
import argparse
import ctypes as C
import hashlib
import json
import inspect
from pathlib import Path
import runpy
import struct
import subprocess
import sys
from types import SimpleNamespace

from PIL import Image
import cream_art_study_capture as A
import cream_polish_capture as P
import cream_depth_capture as D
from cream_dynamic_audit import Topology
from regional_native_support import sha
import probe as Q

TOOLS=Path(__file__).resolve().parent


class MapMarker(C.Structure):
    _fields_=[(n,C.c_uint8) for n in ('x','y','kind','state')]


class MapData(C.Structure):
    _fields_=[(n,C.c_uint32) for n in ('kind','height','owner')]
    _fields_ += [(n,C.c_uint8) for n in ('selected','current','here_x','here_y','zoom','concept','marker_count')]
    _fields_ += [(n,C.c_uint8*25) for n in ('known','visited','events','summit','corruption','low','high','levels')]
    _fields_ += [('markers',MapMarker*32)]


def dynamic_abi(run):
    folder=run.out/'dynamic-abi';folder.mkdir(exist_ok=True)
    expressions=dict(topology_size='sizeof(CreamTopology)',progress_size='sizeof(CreamProgress)',player_size='sizeof(PlayerState)',
        topology_cells='offsetof(CreamTopology,cells)',topology_platform='offsetof(CreamTopology,platform)',topology_climb='offsetof(CreamTopology,climb)',
        topology_drop='offsetof(CreamTopology,drop)',drop_size='sizeof(CreamTopologyDrop)',climb_size='sizeof(CreamTopologyClimb)')
    expressions.update(map_size='sizeof(CreamMapData)',map_markers='offsetof(CreamMapData,markers)',map_known='offsetof(CreamMapData,known)')
    text='#include <stddef.h>\n#include "cream_topology.h"\n#include "cream_runtime.h"\n#include "cream_map_concepts.h"\n#include "player.h"\n'
    text+='const unsigned values[] __attribute__((used,section(".dynamic_abi")))={' + ','.join(expressions.values())+'};\n'
    unit,obj,binary=(folder/name for name in ('abi.c','abi.o','abi.bin'));unit.write_text(text)
    command=['arm-none-eabi-gcc','-mcpu=arm7tdmi','-mthumb','-std=c99','-DBART_FOREST_VARIANT=32',
             '-I',str(run.out/'abi/headers'),'-c',str(unit),'-o',str(obj)]
    result=subprocess.run(command,capture_output=True,text=True);(folder/'compile.log').write_text(result.stdout+result.stderr);result.check_returncode()
    subprocess.run(['arm-none-eabi-objcopy','-O','binary','-j','.dynamic_abi',str(obj),str(binary)],check=True)
    abi=dict(zip(expressions,struct.unpack('<'+'I'*len(expressions),binary.read_bytes())))
    assert abi['topology_size']==C.sizeof(Topology),(abi,C.sizeof(Topology))
    assert abi['topology_cells']==Topology.cells.offset and abi['topology_drop']==Topology.drop.offset
    assert abi['map_size']==C.sizeof(MapData) and abi['map_markers']==MapData.markers.offset and abi['map_known']==MapData.known.offset
    A.write_json(folder/'provenance.json',dict(command=command,values=abi,unit_sha256=sha(unit)))
    return abi


class DynamicCapture(P.PolishCapture):
    def __init__(self,bundle,out,seed):
        super().__init__(bundle,out,seed);self.dynamic=dynamic_abi(self.run)

    def topology(self):
        return Topology.from_buffer_copy(A.raw(self.c,Q.sym('gCreamTopology'),self.dynamic['topology_size']))

    def safe_position(self):
        """Move off the ordinary loader's enemy-spawn default, before AI runs."""
        st=self.state();t=self.topology();owner=st['node']&1
        enemies=[Q.actor(self.c,i) for i in range(1,96) if Q.r8(self.c,Q.sym('gActors')+i*64)==2]
        candidates=[(x*16+8,y*16+14) for y in range(1,23) for x in range(4,28)
                    if (t.cells[y*32+x]&16) and not (t.cells[y*32+x]&32) and
                    int(bool(t.cells[y*32+x]&8))==owner and self.tile_type(x*16+8,y*16+10)==0 and
                    self.feet_clear(x*16+8,y*16+14)]
        if candidates:
            point=max(candidates,key=lambda p:(min((abs(p[0]-e['x'])+abs(p[1]-e['y']) for e in enemies),default=999),
                                               -abs(p[0]-256)-abs(p[1]-(110 if owner else 318))))
            self.nav(*point,0)

    def request(self,cell):
        changed=self.state()['cell']!=cell
        super().request(cell)
        if changed:self.safe_position()

    def request_node(self,node):
        """Disclosed ordinary room-load request, choosing its macrocomponent."""
        cell=node//2
        if self.state()['cell']==cell and self.state()['node']==node:return
        before=self.state()
        values=[('sNextArea',3),('sNextCell',cell),('sNextSide',2),('sTransPhase',0),
                ('sCreamNextNode',node),('sCreamNextFacing',0),('sCreamDropRows',0)]
        for name,value in values:
            address=next(self.run.sections[prefix+name] for prefix in ('.bss.','.data.','.ewram_bss.')
                         if prefix+name in self.run.sections)
            Q.w8(self.c,address,value)
        for name in ('sCreamNextX','sCreamNextY'):
            address=next(self.run.sections[prefix+name] for prefix in ('.bss.','.data.','.ewram_bss.')
                         if prefix+name in self.run.sections)
            Q.w16(self.c,address,65535)
        Q.w8(self.c,Q.sym('gGame')+self.run.abi['game_state'],self.run.abi['enum_transition'])
        self.run.fixtures.append(dict(kind='ordinary Cream room-load request for isolated local traversal',
                                      cell=cell,node=node,before=before))
        self.run.settle(3);self.run.dismiss()
        self.check('ordinary load selected actual generated component',self.state()['node']==node,self.state())
        self.safe_position()

    def metrics(self):
        value=super().metrics();t=self.topology()
        value['topology']=dict(active=t.active,cell=t.cell,archetype=t.archetype,platforms=t.platforms,
                               climbs=t.climbs,drops=t.drops,max_height=t.max_height,
                               supported_heights=sorted({c&7 for c in t.cells if c&16 and (c&7)<7}))
        return value

    def readonly(self):
        st=self.state()
        return dict(room=A.digest(A.raw(self.c,Q.sym('gRoom'),self.extra['room_size'])),
                    topology=A.digest(A.raw(self.c,Q.sym('gCreamTopology'),self.dynamic['topology_size'])),
                    world=A.digest(A.raw(self.c,Q.sym('gCreamWorld'),C.sizeof(A.G.World))),
                    progress=A.digest(A.raw(self.c,Q.sym('gCreamProgress'),self.dynamic['progress_size'])),
                    player=A.digest(A.raw(self.c,Q.sym('gPl'),self.dynamic['player_size'])),
                    inventory=A.digest(A.raw(self.c,Q.sym('gLegacyInventory'),self.run.abi['inventory_size'])),
                    handoff=A.digest(A.raw(self.c,Q.sym('gHandoffState'),self.run.abi['handoff_size'])),
                    actors=A.digest(A.raw(self.c,Q.sym('gActors'),64*96)),
                    gates=A.digest(A.raw(self.c,Q.sym('gCreamOpenEdges'),50)),
                    node=self.run.u8('gCreamNode'),run_frames=st['run_frames'],
                    actor={k:st['actor'][k] for k in ('kind','state','x','y','z','facing')})

    def map_data(self):
        """Read the native atlas input, never fabricate its terrain/markers."""
        if not hasattr(self,'map_pointer_symbol'):
            symbols=subprocess.check_output(['arm-none-eabi-nm','-an',str(self.run.bundle/'bartgame.elf')],text=True)
            candidates=[int(line.split()[0],16) for line in symbols.splitlines() if len(line.split())==3 and line.split()[2]=='sWork']
            if len(candidates)!=1:raise AssertionError(('ambiguous native map pointer',candidates))
            self.map_pointer_symbol=candidates[0]
        pointer=self.map_pointer_symbol
        address=Q.r32(self.c,pointer)
        d=MapData.from_buffer_copy(A.raw(self.c,address,C.sizeof(MapData)))
        arrays={name:list(A.raw(self.c,getattr(d,name),768)) for name in ('kind','height','owner')}
        arrays.update({name:list(getattr(d,name)) for name in ('known','visited','events','summit','corruption','low','high','levels')})
        arrays['markers']=[{name:getattr(m,name) for name,_ in m._fields_} for m in d.markers[:d.marker_count]]
        arrays.update({name:getattr(d,name) for name in ('selected','current','here_x','here_y','zoom','concept','marker_count')})
        self.check('atlas metadata names the real live room',d.current==self.state()['cell'])
        self.check('unknown rooms expose no event information',all(k or not e for k,e in zip(d.known,d.events)))
        if not d.known[d.selected]:
            self.check('unknown selected room hides all terrain and markers',not d.marker_count and
                       not any(arrays['kind']) and not any(arrays['height']) and not any(arrays['owner']))
        elif d.selected==d.current:
            t=self.topology()
            self.check('native atlas heights match every actual physical room cell',arrays['height']==[c&7 for c in t.cells])
            self.check('native atlas owners match every actual physical room cell',arrays['owner']==[int(bool(c&8)) for c in t.cells])
            st=self.state()['actor']
            self.check('native atlas player marker uses actual room position',
                       any(m['kind']==8 and m['x']==st['x']//16 and m['y']==(st['y']-4)//16 for m in arrays['markers']))
        return arrays

    def composites(self,folder):
        """Exact native union, with12's actual remaining character capacity."""
        folder.mkdir(parents=True,exist_ok=True)
        ground=P.u16s(A.raw(self.c,Q.sym('gRoom')+self.run.abi['room_ground'],2048))
        paints=P.u16s(A.raw(self.c,Q.sym('gCreamPolishWallPaint'),2048))
        checks=[];dynamic=set();records=[]
        for at,paint in enumerate(paints[:768]):
            if paint==65535:continue
            x,y=at%32,at//32;bi,bc=self.mt(ground[at]);pi,pc=self.mt(paint)
            expected=b''.join(pc[i*2:i*2+2] if pi[i] else bc[i*2:i*2+2] for i in range(256))
            actual,tiles,entries=self.bg2(x,y);dynamic|={tile for tile in tiles if tile>=self.static['tile_count']}
            ok=actual==expected
            records.append(dict(cell=[x,y],base=ground[at],paint=paint,screen_entries=entries,
                                expected_sha256=A.digest(expected),actual_sha256=A.digest(actual),exact=ok))
            checks.append(dict(name='native BG2 equals real backing plus alpha paint at%d,%d'%(x,y),passed=ok))
        capacity=1024-self.static['tile_count']
        checks.append(dict(name='room contains actual masked art',passed=bool(records)))
        checks.append(dict(name='dynamic blend subtiles fit native residual character capacity',passed=
                           len(dynamic)<=capacity and all(self.static['tile_count']<=t<1024 for t in dynamic)))
        report=dict(method='Independently decode frozen-ROM base/alpha4bpp and compare exact RGB555 to actual BG2map/VRAM/palette.',
                    rom_sha256=sha(self.run.bundle/'bartgame.gba'),static_bg_tiles=self.static['tile_count'],
                    dynamic_capacity=capacity,dynamic_tiles=sorted(dynamic),painted_cells=records,checks=checks,
                    complete=all(c['passed'] for c in checks))
        A.write_json(folder/'native-composites.json',report)
        self.check('all native BG2 masked cells exactly preserve actual backing',report['complete'],
                   dict(painted_cells=len(records),dynamic_subtiles=len(dynamic),capacity=capacity))
        return report

    def record_action(self,folder,keys,limit,stop):
        folder.mkdir(parents=True,exist_ok=True);self.c.bg_video.to_pil().convert('RGB').save(folder/'before.png')
        images,trace=self.advance(keys,limit,stop=stop,record=folder)
        self.advance([],2)
        after=self.state();self.c.bg_video.to_pil().convert('RGB').save(folder/'landed.png')
        pictures=[im for _,im,_,_ in images]
        if pictures:pictures[0].save(folder/'motion.gif',save_all=True,append_images=pictures[1:],duration=67,loop=0,optimize=False)
        A.write_json(folder/'input-trace.json',self.identity())
        return images,trace,after


def room_survey(bundle,out,seed,count=8):
    out.mkdir(parents=True,exist_ok=True)
    selections={};room_metrics=[]
    for attempt in range(4):
        chosen_seed=seed if not attempt else attempt-1
        survey=DynamicCapture(bundle,out/('survey-core-%d'%chosen_seed),chosen_seed)
        for cell in range(25):
            survey.request(cell);survey.advance([],4);t=survey.topology()
            row=dict(seed=chosen_seed,cell=cell,archetype=t.archetype,platforms=t.platforms,climbs=t.climbs,drops=t.drops,
                     max_height=t.max_height,heights=sorted({c&7 for c in t.cells if c&16 and (c&7)<7}))
            room_metrics.append(row)
            score=t.climbs*3+t.drops*2+len(row['heights'])
            if t.archetype not in selections or (not attempt and score>selections[t.archetype][0]):
                selections[t.archetype]=(score,cell,chosen_seed)
        if len(selections)==8:break
    A.write_json(out/'selection.json',dict(seed=seed,rooms=room_metrics,selections=selections))
    cases=[]
    for archetype,(_,cell,chosen_seed) in sorted(selections.items())[:count]:
        folder=out/('archetype-%02d-cell-%02d'%(archetype,cell));folder.mkdir(exist_ok=True)
        renderer=DynamicCapture(bundle,out/('private-cores/render-%d'%archetype),chosen_seed)
        renderer.request(cell);renderer.advance([],8)
        before=renderer.readonly();native=renderer.composites(folder/'registered-renderer')
        pano=renderer.panorama(folder/'registered-renderer');after=renderer.readonly()
        renderer.check('frozen whole-room survey preserves physical/topology state',before==after,dict(before=before,after=after))
        t=renderer.topology();A.write_json(folder/'topology.json',dict(archetype=t.archetype,cell=t.cell,cells=list(t.cells),
            platforms=t.platforms,climbs=[dict((n,getattr(c,n)) for n,_ in c._fields_) for c in t.climb[:t.climbs]],
            drops=[dict((n,getattr(d,n)) for n,_ in d._fields_) for d in t.drop[:t.drops]]))
        A.write_json(folder/'provenance.json',renderer.identity())
        cases.append(dict(seed=chosen_seed,cell=cell,archetype=archetype,file=folder.name+'/registered-renderer/full-room.png',
                          native_BG2_exact=native['complete'],checks=renderer.checks,room_unchanged=pano['room_unchanged']))
    report=dict(rom_sha256=sha(bundle/'bartgame.gba'),source_commit=(bundle/'source-commit.txt').read_text().strip(),
                seed=seed,cases=cases,complete=len(cases)>=count and all(c['passed'] for case in cases for c in case['checks']))
    A.write_json(out/'report.json',report);return report


def extra_actions(bundle,out,seed):
    out.mkdir(parents=True,exist_ok=True);survey=DynamicCapture(bundle,out/'survey-core',seed);choices={}
    for cell in range(25):
        survey.request(cell);survey.advance([],4);t=survey.topology()
        if t.climbs and 'climb' not in choices:choices['climb']=dict(cell=cell,index=0,owner=t.climb[0].owner)
        if t.drops and 'drop' not in choices:choices['drop']=dict(cell=cell,index=0,owner=t.drop[0].owner)
        if len(choices)==2:break
    checks=[];cases=[]
    for kind,choice in choices.items():
        folder=out/kind;live=DynamicCapture(bundle,out/('private-cores/'+kind),seed)
        live.request(choice['cell']);live.advance([],26)
        t=live.topology();node=live.state()['node']
        if node%2!=choice['owner']:
            # Use the existing ordinary request mechanism to choose the
            # correct macroowner rather than assigning gCreamNode/results.
            live.request_node(choice['cell']*2+choice['owner'])
            live.advance([],26);t=live.topology();node=live.state()['node']
        if kind=='climb':
            c=t.climb[choice['index']];px=(c.x+1)*16
            candidates=[y for y in range(min(383,(c.bottom+2)*16),max(0,c.bottom*16-8),-1)
                        if live.tile_type(px,y-4)==live.rom.defs['TT_FLOOR'] and
                        live.tile_type(px,y-11)==live.rom.defs['TT_CLIMB'] and live.feet_clear(px,y)]
            if not candidates:raise AssertionError(('no real extra-climb dry foot',choice,list(bytes(c))))
            live.nav(px,candidates[0],0);live.advance([],2);before=live.state()
            images,trace,after=live.record_action(folder,'UP',320,lambda st:st['actor']['state']==live.extra['enum_normal'] and
                st['actor']['z']==0 and st['actor']['y']<=(c.top*16-2))
            live.check('actual extra-climb input uses climb animation',trace['climb_frames']>0)
            live.check('extra climb reaches supported higher platform',after['actor']['y']<before['actor']['y']-16 and
                       after['actor']['state']==live.extra['enum_normal'] and after['actor']['z']==0,after)
        else:
            d=t.drop[choice['index']];live.nav(d.x,d.y-3,2);live.advance([],2);before=live.state()
            images,trace,after=live.record_action(folder,'DOWN',220,lambda st:st['actor']['state']==live.extra['enum_normal'] and
                st['actor']['z']==0 and abs(st['actor']['x']-d.landing_x)<=1 and abs(st['actor']['y']-d.landing_y)<=1)
            fall=[st for _,_,st,_ in images if st['actor']['z']>0]
            live.check('actual extra-drop input produces physical falling body',bool(fall),trace)
            live.check('extra drop lands at authoritative local target',abs(after['actor']['x']-d.landing_x)<=1 and
                       abs(after['actor']['y']-d.landing_y)<=1 and after['actor']['z']==0,after)
        live.check('local elevation traversal preserves macrocomponent',after['node']==node,dict(before=node,after=after['node']))
        live.check('local traversal preserves positive health',trace['minimum_health']>0)
        detail=dict(kind=kind,selection=choice,before=before,after=after,trace=trace,checks=live.checks)
        A.write_json(folder/'provenance.json',detail);checks.extend(live.checks);cases.append(detail)
    report=dict(rom_sha256=sha(bundle/'bartgame.gba'),choices=choices,cases=cases,checks=checks,
                complete=set(choices)=={'climb','drop'} and all(c['passed'] for c in checks))
    A.write_json(out/'report.json',report);return report


def edge_signature(image):
    im=image.crop((4,22,236,146)).convert('RGB');pixels=list(im.getdata());w,h=im.size
    return A.digest(bytes(int(pixels[y*w+x]!=pixels[y*w+x-1])|int(pixels[y*w+x]!=pixels[(y-1)*w+x])<<1
                          for y in range(1,h) for x in range(1,w)))


def map_redraw(live,key,concept,zoom,limit=1000):
    """Wait for the actual final bitmap upload, not an assumed render time."""
    old=A.digest(A.raw(live.c,0x06008000,19200));before=live.run.frames
    live.advance(key,2)
    for frame in range(limit):
        live.advance([],1)
        if frame%4:continue
        if Q.r16(live.c,0x0400000e)!=0x1f08:continue
        if live.run.u8('gCreamMapConcept')!=concept or live.run.u8('gCreamMapZoom')!=zoom:continue
        if A.digest(A.raw(live.c,0x06008000,19200))==old:continue
        live.advance([],2)
        return dict(key=key,concept=concept,zoom=zoom,hardware_frames=live.run.frames-before)
    raise AssertionError(('native map redraw did not upload its completed bitmap',key,concept,zoom,live.state(),hex(Q.r16(live.c,0x0400000e))))


def maps(bundle,out,seed,charted=True):
    out.mkdir(parents=True,exist_ok=True);live=DynamicCapture(bundle,out/'private-core',seed)
    if charted:
        choices=[]
        for cell in range(25):
            live.request(cell);live.advance([],2);t=live.topology()
            choices.append((len({c&7 for c in t.cells if c&16 and (c&7)<7}),t.climbs+t.drops,cell))
        _,_,selected=max(choices)
        if seed==0xb4a7 and choices[5][0]>=5:selected=5
        live.request(selected);live.advance([],2)
    before_map=live.state();live.advance('START',1);live.advance([],48)
    live.check('real START opens the pause menu',live.state()['state']==4)
    # The ordinary pause's two R pages use its queued VBlank input. SELECT
    # is handled earlier by the old menu and can lose a one-frame tap.
    live.advance('R',1);live.advance([],48)
    redraws=[map_redraw(live,'R',0,0)]
    live.check('real menu navigation opens graphical Cream map',live.state()['state']==4 and
               ((Q.r16(live.c,0x0400000e)>>2)&3)==2 and ((Q.r16(live.c,0x0400000e)>>8)&31)==31)
    paused=live.readonly();checks=[];images=[];overview_edges=[];zoom_edges=[];data_fingerprint=None
    for concept in range(10):
        active=live.run.u8('gCreamMapConcept')
        if active!=concept:
            raise AssertionError(('concept input cycle out of order',concept,active))
        live.check('actual map concept selector matches '+str(concept+1),active==concept)
        for zoom,label in ((0,'overview'),(1,'zoom')):
            if zoom:redraws.append(map_redraw(live,'A',concept,1))
            live.check('actual map zoom matches input',live.run.u8('gCreamMapZoom')==zoom)
            data=live.map_data();A.write_json(out/('%02d-%s-data.json'%(concept+1,label)),data)
            fingerprint=A.digest(json.dumps({k:v for k,v in data.items() if k not in ('concept','zoom')},sort_keys=True).encode())
            if data_fingerprint is None:data_fingerprint=fingerprint
            live.check('all concepts and scales use identical actual room data',fingerprint==data_fingerprint)
            im=live.c.bg_video.to_pil().convert('RGB').copy();name='%02d-%s.png'%(concept+1,label);im.save(out/name)
            signature=edge_signature(im);images.append(dict(concept=concept,zoom=zoom,file=name,sha256=sha(out/name),edge_sha256=signature))
            (zoom_edges if zoom else overview_edges).append(signature)
            live.check('pause-map view never mutates live game state',live.readonly()==paused,
                       dict(concept=concept,zoom=zoom,before=paused,after=live.readonly()))
        redraws.append(map_redraw(live,'B',concept,0))
        if concept<9:redraws.append(map_redraw(live,'L',concept+1,0))
    live.check('ten overview bodies have distinct native edge layouts',len(set(overview_edges))==10)
    live.check('ten zoom bodies have distinct native edge layouts',len(set(zoom_edges))==10)
    live.check('charted atlas redraws complete within48hardwareframes',not charted or max(r['hardware_frames'] for r in redraws)<=48,redraws)
    original=live.run.u8('gCreamMapCell');key='UP' if original>=5 else 'DOWN'
    redraws.append(map_redraw(live,key,9,0));selected=live.map_data()
    live.check('actual Dpad selects another generated room',selected['selected']!=original)
    live.check('selecting another room leaves live terrain/progression untouched',live.readonly()==paused)
    redraws.append(map_redraw(live,'A',9,1));selected_zoom=live.map_data()
    live.check('actual A zoom retains the selected room',selected_zoom['selected']==selected['selected'] and selected_zoom['zoom']==1)
    live.c.bg_video.to_pil().convert('RGB').save(out/'neighbor-zoom.png');A.write_json(out/'neighbor-zoom-data.json',selected_zoom)
    live.check('zooming another room leaves all paused gameplay untouched',live.readonly()==paused)
    live.advance('START',2);live.advance([],600,stop=lambda st:st['state']==1 and st['actor']['state']==0 and st['actor']['z']==0)
    live.advance([],2)
    live.check('actual START closes atlas to living game',live.state()['state']==1 and live.state()['health'][0]>0)
    composite=live.composites(out/'restored-native-BG2');live.c.bg_video.to_pil().convert('RGB').save(out/'returned.png')
    report=dict(rom_sha256=sha(bundle/'bartgame.gba'),source_commit=(bundle/'source-commit.txt').read_text().strip(),
                tool_sha256=sha(__file__),charted_fixture=charted,
                fixture='Ordinary room-load requests visit25rooms for a surveyed concept comparison; no discovery/inventory/results written.' if charted else 'Fresh normal discovery state.',
                before=before_map,paused_snapshot=paused,images=images,redraw_timings=redraws,checks=live.checks,
                native_world_restored=composite['complete'],complete=all(c['passed'] for c in live.checks))
    A.write_json(out/'report.json',report);A.write_json(out/'input-trace.json',live.identity());return report


def earned_progression(bundle,out,seed,long_only=False):
    """Reuse the earned-input harness; adapt only its WALK navigation Y.

    The old harness's fixed row6/19 waypoints predate variable side hinges.
    A Python observer wraps its disclosed hero navigation, asking the exact
    pinned C helper for the new row. No game result or terrain is assigned.
    """
    from cream_dynamic_audit import Audit
    out.mkdir(parents=True,exist_ok=True)
    audit=Audit(SimpleNamespace(bundle=str(bundle),baseline='/workspace/setup/cream-studies/frozen/style-0-r2',out=str(out/'helper-report.json')))
    host=audit.host('dynamic',audit.rom)
    native_world=A.G.World.in_dll(host,'gCreamWorld')
    script=TOOLS/'cream_runtime_review.py';context={};adaptations=[];observations=[];original_tp=None
    def tp(core,x,y):
        frame=inspect.currentframe().f_back
        if frame.f_code.co_name in ('edge','use_gate'):
            edge=frame.f_locals.get('e')
            if edge is not None and edge.kind==1:
                node,index=frame.f_locals['n'],frame.f_locals['i']
                C.memmove(C.addressof(native_world),A.raw(core,Q.sym('gCreamWorld'),C.sizeof(native_world)),C.sizeof(native_world))
                px=C.c_int();py=C.c_int();host.cream_room_walk_pos(node,index,C.byref(px),C.byref(py))
                adaptations.append(dict(node=node,edge=index,old_y=y,actual_C_hinge_y=py.value,x=x))
                y=py.value
        return original_tp(core,x,y)
    def observe(frame,event,arg):
        nonlocal context,original_tp
        if Path(frame.f_code.co_filename)!=script:return
        context=frame.f_globals
        if original_tp is None and event=='call' and frame.f_code.co_name=='check' and 'tp' in context:
            original_tp=context['tp'];context['tp']=tp
        if event=='return' and frame.f_code.co_name=='status' and context.get('active_capture') is not None and isinstance(arg,dict):
            if arg.get('area')==3:
                observations.append(dict(state=arg,landings=D.read_landings(context['c'],landing)))
    from regional_native_support import compile_abi
    compile_abi(bundle,out/'observer-abi')
    landing=D.landing_abi(bundle,out/'landing-abi',out/'observer-abi/headers')
    previous_argv=sys.argv[:]
    sys.argv=[str(script),'--bundle',str(bundle),'--out',str(out/'earned-runtime'),'--seed',str(seed)]
    if long_only:sys.argv.append('--stop-after-long-drop')
    code=0
    try:
        sys.setprofile(observe);runpy.run_path(str(script),run_name='__main__')
    except SystemExit as error:code=error.code or 0
    finally:
        sys.setprofile(None);sys.argv=previous_argv
    checks=context.get('checks',[])
    report=dict(rom_sha256=sha(bundle/'bartgame.gba'),source_commit=(bundle/'source-commit.txt').read_text().strip(),
                original_harness_sha256=sha(script),observer_sha256=sha(__file__),seed=seed,long_only=long_only,
                exit_code=code,checks=checks,walk_navigation_adaptations=adaptations,
                fixture_scope='Original earned-input harness and its disclosed hero navigation fixtures. Only fixed WALK waypoint Y is replaced by exact pinned pure C hinge data. No inventory, health, gate, terrain, completion or combat results are written.',
                complete=code==0 and context.get('review_complete',False) and all(c['passed'] for c in checks))
    A.write_json(out/'landing-observations.json',observations);A.write_json(out/'report.json',report)
    return report


def performance(bundle,baseline,out,seed):
    """Count emulated hardware frames and actual gameplay updates.

    This is a finite ordinary-core timing sample, not host wall-clock FPS or
    an instrumented cycle profile. It includes ordinary room transitions and
   60 stationary live frames per room with the generated enemies unchanged.
    """
    out.mkdir(parents=True,exist_ok=True);runs=[]
    for label,source in (('previous-weathered',baseline),('dynamic',bundle)):
        live=A.Capture(source,out/label,seed);rows=[]
        for cell in range(25):
            before=live.state();physical=live.run.frames
            live.request(cell);loaded=live.state();load_frames=live.run.frames-physical
            enemies=[Q.actor(live.c,i) for i in range(1,96) if Q.r8(live.c,Q.sym('gActors')+i*64)==2]
            candidates=[(x*16+8,y*16+14) for y in range(18,22) for x in range(4,28)
                        if live.tile_type(x*16+8,y*16+10)==0 and live.feet_clear(x*16+8,y*16+14)]
            if candidates:
                safe=max(candidates,key=lambda p:min((abs(p[0]-e['x'])+abs(p[1]-e['y']) for e in enemies),default=999))
                live.nav(*safe,0)
            live.advance([],12)
            steady=live.state();physical=live.run.frames
            _,trace=live.advance([],60)
            after=live.state();frames=live.run.frames-physical
            updates=(after['run_frames']-steady['run_frames'])&0xffffffff
            rows.append(dict(cell=cell,load_hardware_frames=load_frames,
                             load_vblanks=(loaded['clock']-before['clock'])&0xffffffff,
                             steady_hardware_frames=frames,steady_updates=updates,updates_per_frame=updates/frames,
                             min_health=trace['minimum_health'],generated_enemies=len(enemies),
                             before_state=steady['state'],after_state=after['state'],after_health=after['health'][0]))
        runs.append(dict(label=label,rom_sha256=sha(source/'bartgame.gba'),rooms=rows,
                         steady_updates=sum(r['steady_updates'] for r in rows),
                         steady_frames=sum(r['steady_hardware_frames'] for r in rows)))
        A.write_json(out/(label+'-input-trace.json'),live.identity())
    old,new=runs
    old_ratio=old['steady_updates']/old['steady_frames'];new_ratio=new['steady_updates']/new['steady_frames']
    old_load=sorted(r['load_hardware_frames'] for r in old['rooms'] if r['load_hardware_frames'])
    new_load=sorted(r['load_hardware_frames'] for r in new['rooms'] if r['load_hardware_frames'])
    checks=[dict(name='steady simulation retains at least95percent of prior hardware-frame update rate',passed=new_ratio>=old_ratio*.95,
                 observed=dict(previous=old_ratio,dynamic=new_ratio)),
            dict(name='room-load95percentile adds at most24hardware frames',passed=new_load[int(.95*(len(new_load)-1))]<=old_load[int(.95*(len(old_load)-1))]+24,
                 observed=dict(previous_frames=old_load,dynamic_frames=new_load))]
    checks.append(dict(name='all50timing samples remain living ordinary gameplay',passed=all(
        r['min_health']>0 and r['after_health']>0 and r['before_state']==1 and r['after_state']==1 for run in runs for r in run['rooms'])))
    report=dict(seed=seed,runs=runs,checks=checks,complete=all(c['passed'] for c in checks),
                limits='Finite25-room stationary comparison. Frame ratios count actual emulated vblanks/updates. Transition timing includes fade and room-generation/upload work. No maximum-enemy stress claim.')
    A.write_json(out/'report.json',report);return report


def forest_cache(bundle,out,seed):
    """Real-input Forest -> Cream atlas -> Forest borrowed-cache proof."""
    out.mkdir(parents=True,exist_ok=True)
    live=DynamicCapture(bundle,out/'private-core',seed)
    symbols={}
    for line in subprocess.check_output(['arm-none-eabi-nm','-S','-an',str(bundle/'bartgame.elf')],text=True).splitlines():
     fields=line.split()
     if len(fields)==4:
      try:address,size=int(fields[0],16),int(fields[1],16)
      except ValueError:continue
      if fields[3] not in symbols or size>symbols[fields[3]][1]:symbols[fields[3]]=(address,size)
    def read(name):
     address,size=symbols[name];return A.raw(live.c,address,size)
    def wait_area(area):
     live.advance([],800,stop=lambda s:s['area']==area and s['state']==1 and s['actor']['state']==0 and not s['actor']['z'])
     live.check('ordinary transition reaches living area%d'%area,live.state()['area']==area and live.state()['state']==1 and live.state()['health'][0]>0)
    def leave_cream():
     live.request(live.world.entry_node//2);d=live.info().return_door
     live.nav((d.x+1)*16,(d.y+1)*16+14,0);live.advance('A',2);wait_area(0)
    def enter_forest():
     candidates=[(x,y) for y in range(24) for x in range(32) if live.tile_type(x*16+8,y*16+10)==live.rom.defs['TT_EXIT'] and abs(x*16+8-live.run.abi['hub_ladder_x'])>16]
     if not candidates:raise AssertionError('actual Forest ladder not found')
     x,y=min(candidates,key=lambda p:(p[1],p[0]));live.nav(x*16+8,(y+2)*16+14,0)
     live.advance('UP',500,stop=lambda s:s['area']==1 and s['state']==1);wait_area(1)
    def forest_map(label):
     live.advance('START',2);live.advance([],48)
     for _ in range(2):live.advance('R',2);live.advance([],48)
     live.advance([],1000,stop=lambda st:live.run.u8('gMenuStudyPage')==2)
     live.check('real2R opens Forest map',live.state()['state']==4 and live.state()['area']==1 and live.run.u8('gMenuStudyPage')==2)
     cell=live.state()['cell']
     live.c.bg_video.to_pil().convert('RGB').save(out/(label+'-overview.png'))
     live.advance('A',2);live.advance([],1000,stop=lambda st:live.run.u8('gMenuStudyZoom')==1);live.advance([],2);live.c.bg_video.to_pil().convert('RGB').save(out/(label+'-zoom.png'))
     done=int.from_bytes(read('sMaskDone'),'little')
     live.check('Forest zoom computes the current room terrain mask',bool(done&(1<<cell)))
     mask=read('sMasks')[cell*768:(cell+1)*768]
     state=dict(cell=cell,mask_sha256=A.digest(mask),mask_done=done,mask_bytes=list(mask))
     live.advance('START',2);wait_area(1)
     return state
    def leave_forest():
     candidates=[(x,y) for y in range(24) for x in range(32) if live.tile_type(x*16+8,y*16+10)==live.rom.defs['TT_STAIRS']]
     if not candidates:raise AssertionError('actual Forest return stairs not found')
     x,y=candidates[0];live.nav(x*16+8,(y+1)*16+14,0);live.advance('UP',180,stop=lambda s:s['area']==0 and s['state']==1);wait_area(0)
    def enter_cream():
     live.nav(live.run.abi['hub_ladder_x'],live.run.abi['hub_ladder_return'],0)
     live.advance('UP',500,stop=lambda s:s['area']==3 and s['state']==1);wait_area(3)
    leave_cream();enter_forest();first=forest_map('before');leave_forest();enter_cream()
    live.advance('START',2);live.advance([],48)
    live.advance('R',2);live.advance([],48);map_redraw(live,'R',0,0)
    live.check('real2R opens Cream graphical atlas',Q.r16(live.c,0x0400000e)==0x1f08)
    map_redraw(live,'A',0,1);live.c.bg_video.to_pil().convert('RGB').save(out/'cream-borrowed-atlas.png')
    invalidated=int.from_bytes(read('sMaskDone'),'little')
    live.check('Cream atlas explicitly invalidates borrowed Forest masks',invalidated==0)
    live.check('Cream atlas really overwrites the borrowed mask storage',A.digest(read('sMasks')[first['cell']*768:(first['cell']+1)*768])!=first['mask_sha256'])
    live.advance('START',2);wait_area(3);leave_cream();enter_forest();second=forest_map('after')
    live.check('returning Forest map recomputes identical actual room terrain',first['cell']==second['cell'] and first['mask_sha256']==second['mask_sha256'])
    A.write_json(out/'input-trace.json',live.identity())
    report=dict(rom_sha256=A.digest((bundle/'bartgame.gba').read_bytes()),source_commit=(bundle/'source-commit.txt').read_text().strip(),
     tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),before=first,after=second,checks=live.checks,complete=all(c['passed'] for c in live.checks),
     fixture='Hero position/facing navigation to the real return stairs and both Drain ladders. All travel and menu selection uses real inputs. No discovery, inventory, health, terrain, cache bits or result writes.')
    A.write_json(out/'report.json',report)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',required=True);p.add_argument('--out',required=True)
    p.add_argument('--seed',type=lambda x:int(x,0),default=0xb4a7);p.add_argument('--rooms',action='store_true')
    p.add_argument('--maps',action='store_true');p.add_argument('--actions',action='store_true');p.add_argument('--waterfalls',action='store_true')
    p.add_argument('--earned',action='store_true');p.add_argument('--earned-long',action='store_true')
    p.add_argument('--forest-cache',action='store_true');p.add_argument('--performance',action='store_true');p.add_argument('--performance-baseline',default='/workspace/setup/cream-polish/frozen/style-10-r2')
    p.add_argument('--fresh-map',action='store_true');a=p.parse_args();bundle=Path(a.bundle).resolve();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
    sections={}
    if a.rooms:sections['rooms']=room_survey(bundle,out/'rooms',a.seed)
    if a.actions:sections['local_actions']=extra_actions(bundle,out/'local-actions',a.seed)
    if a.maps:sections['maps']=maps(bundle,out/'maps',a.seed,not a.fresh_map)
    if a.waterfalls:sections['waterfalls']=P.waterfalls(bundle,out/'waterfalls',a.seed)
    if a.earned or a.earned_long:sections['earned']=earned_progression(bundle,out/'earned',a.seed,a.earned_long)
    if a.forest_cache:sections['forest_cache']=forest_cache(bundle,out/'forest-cache',a.seed)
    if a.performance:sections['performance']=performance(bundle,Path(a.performance_baseline).resolve(),out/'performance',a.seed)
    report=dict(rom_sha256=sha(bundle/'bartgame.gba'),source_commit=(bundle/'source-commit.txt').read_text().strip(),
                tool_sha256=sha(__file__),sections=sections,complete=bool(sections) and all(r['complete'] for r in sections.values()))
    A.write_json(out/'report.json',report);return int(not report['complete'])


if __name__=='__main__':raise SystemExit(main())

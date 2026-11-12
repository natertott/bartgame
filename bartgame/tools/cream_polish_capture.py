#!/usr/bin/env python3
"""Real mGBA review of Cream polish7..11, including native BG2 alpha union.

Frozen registered room mosaics and ordinary advancing-input footage use separate
fresh cores. Explicit seed, hero navigation/facing and ordinary load requests
select isolated cases. No health, inventory, enemy, gates, terrain, palette,
VRAM or framebuffer results are assigned. The optional earned long-drop proof
reuses the established real-tool harness and discloses its standing/z waypoint
normalization. Source art sheets remain separate from these renderer captures.
"""
import argparse
import ctypes as C
import json
from pathlib import Path
import runpy
import struct
import subprocess
import sys

from PIL import Image
import cream_art_study_capture as A
import cream_depth_capture as D
import cream_graph_review as G
import probe as P
from regional_native_support import compile_abi,sha
from sewer_concept_audit import NativeRom,decode_metatile

TOOLS=Path(__file__).resolve().parent
PHYSICAL=D.PHYSICAL


def u16s(data):return struct.unpack('<%dH'%(len(data)//2),data)


def read_shadows(core,abi,rom):
    """Verify final ground IDs against the actual stage's shade tables."""
    count=P.r16(core,P.sym('gCreamVisualLandingCount'))
    if count>abi['capacity']:raise AssertionError('landing cache capacity exceeded')
    stage=P.r8(core,P.sym('gCreamRoom')+abi['info_stage'])
    shade=u16s(rom.array('cream_polish_shade'));per_stage=len(shade)//3
    allowed=set(shade[stage*per_stage:(stage+1)*per_stage])
    terminals=u16s(rom.array('cream_visual_landing'))
    paths=u16s(rom.array('cream_visual_landing_path'))
    answer=[]
    for i in range(count):
        entry=D.Landing.from_buffer_copy(A.raw(core,P.sym('gCreamVisualLandings')+i*abi['size'],abi['size']))
        verified=0;parts=[]
        for part in range(6):
            if not entry.parts&(1<<part):continue
            x,y=entry.x0+part%3,entry.y0+part//3
            mt=P.r16(core,P.sym('gRoom')+abi['room_ground']+(y*32+x)*2)
            role=P.r8(core,P.sym('gCreamPolishShadeRole')+y*32+x)
            exact_terminal={terminals[stage*6+part],*[paths[stage*24+variant*6+part] for variant in range(4)]}
            ok=mt in exact_terminal and role==3
            if ok:verified|=1<<part
            parts.append(dict(part=part,cell=[x,y],actual_metatile=mt,shade_role=role,actual_match=ok))
        answer.append(dict(x=entry.x,y=entry.y,from_node=entry.from_node,edge=entry.edge,
                           x0=entry.x0,y0=entry.y0,parts=entry.parts,flags=entry.flags,
                           verified_parts=verified,final_ground_parts=parts))
    return answer


class PolishCapture(D.DepthCapture):
    def __init__(self,bundle,out,seed):
        super().__init__(bundle,out,seed)
        self.rom=NativeRom(bundle)
        self.static=self.rom.tileset('cream')
        self.decoded={}

    def state(self):
        state=super().state()
        state['camera']=[P.r16(self.c,P.sym('gCamX')),P.r16(self.c,P.sym('gCamY'))]
        return state

    def shadows(self):return read_shadows(self.c,self.landing_layout,self.rom)

    def fall(self):
        data=A.raw(self.c,P.sym('gCreamPolishFall'),4)
        return dict(zip(('x','y','w','h'),data))

    def metrics(self):
        value=super().metrics();value['fall']=self.fall()
        value['painted_wall_cells']=sum(mt!=65535 for mt in u16s(A.raw(self.c,P.sym('gCreamPolishWallPaint'),2048)))
        return value

    def mt(self,index):
        if index not in self.decoded:
            name=next(name for name,value in self.rom.tile_ids.items() if value==index)
            self.decoded[index]=decode_metatile(self.rom,self.static,name)['frames'][0]
        return self.decoded[index]

    def bg2(self,x,y):
        """Read native BG2 screen entries and VRAM, including both flip bits."""
        tx,ty=x*2,y*2;sb=28+((ty>>5)<<1)+(tx>>5)
        address=0x06000000+sb*2048+(ty&31)*64+(tx&31)*2
        entries=[P.r16(self.c,address+offset) for offset in (0,2,64,66)]
        colors=bytearray();tiles=[]
        for yy in range(16):
            for xx in range(16):
                entry=entries[(yy//8)*2+xx//8];tile=entry&1023;tiles.append(tile)
                u,v=xx&7,yy&7
                if entry&1024:u=7-u
                if entry&2048:v=7-v
                value=P.r8(self.c,0x06000000+tile*32+v*4+u//2)
                ink=(value>>(4*(u&1)))&15
                color=P.r16(self.c,0x05000000+(entry>>12)*32+ink*2)
                colors+=struct.pack('<H',color)
        return bytes(colors),set(tiles),entries

    def composites(self,folder):
        """Compare every actual blend cell to independent native alpha union."""
        folder.mkdir(parents=True,exist_ok=True)
        ground=u16s(A.raw(self.c,P.sym('gRoom')+self.run.abi['room_ground'],2048))
        paints=u16s(A.raw(self.c,P.sym('gCreamPolishWallPaint'),2048))
        checks=[];dynamic=set();records=[]
        for at,paint in enumerate(paints[:768]):
            if paint==65535:continue
            x,y=at%32,at//32
            bi,bc=self.mt(ground[at]);pi,pc=self.mt(paint)
            expected=b''.join(pc[i*2:i*2+2] if pi[i] else bc[i*2:i*2+2] for i in range(256))
            actual,tiles,entries=self.bg2(x,y)
            dynamic|={tile for tile in tiles if tile>=self.static['tile_count']}
            ok=actual==expected
            records.append(dict(cell=[x,y],base=ground[at],paint=paint,screen_entries=entries,
                                expected_sha256=A.digest(expected),actual_sha256=A.digest(actual),exact=ok))
            checks.append(dict(name='native BG2 equals real backing plus alpha paint at%d,%d'%(x,y),passed=ok))
        checks.append(dict(name='room contains actual whole-panel wall paint',passed=bool(records)))
        checks.append(dict(name='dynamic blend subtiles fit128reserved chars',passed=len(dynamic)<=128 and
                           all(self.static['tile_count']<=t<self.static['tile_count']+128 and t<1024 for t in dynamic)))
        report=dict(method='Decode frozen ROM base and alpha4bpp independently; compare exact RGB555 against actual BG2map/VRAM/palette.',
                    rom_sha256=sha(self.run.bundle/'bartgame.gba'),static_bg_tiles=self.static['tile_count'],
                    dynamic_tiles=sorted(dynamic),painted_cells=records,checks=checks,complete=all(c['passed'] for c in checks))
        A.write_json(folder/'native-composites.json',report)
        self.check('all native BG2 masked cells exactly preserve actual backing',report['complete'],
                   dict(painted_cells=len(records),dynamic_subtiles=len(dynamic)))
        return report


def matched(bundle,out,seed):
    out.mkdir(parents=True,exist_ok=True)
    initial=PolishCapture(bundle,out/'private-cores/healthy-renderer',seed)
    cases=A.select(initial.world)
    selection=dict(seed=seed,generated_seed=initial.world.seed,graph=G.plain(initial.world),
                   graph_sha256=A.digest(bytes(initial.world)),cases=cases)
    A.write_json(out/'selection.json',selection)
    report=dict(source_commit=(bundle/'source-commit.txt').read_text().strip(),rom_sha256=sha(bundle/'bartgame.gba'),
                tool_sha256=sha(__file__),seed=seed,generated_seed=initial.world.seed,graph_sha256=selection['graph_sha256'],
                cases=[],complete=False,scope=__doc__.strip())
    A.write_json(out/'report.json',report)
    try:
        for case in cases:
            name,cell=case['name'],case['cell'];folder=out/name;folder.mkdir(exist_ok=True)
            renderer=initial if name=='healthy' else PolishCapture(bundle,out/('private-cores/'+name+'-renderer'),seed)
            info=renderer.prepare(cell)
            composite=renderer.composites(folder/'registered-renderer')
            panorama=renderer.panorama(folder/'registered-renderer')
            A.write_json(folder/'renderer-trace.json',renderer.identity())
            live=PolishCapture(bundle,out/('private-cores/'+name+'-live'),seed)
            live_info=live.prepare(cell);assert info==live_info
            semantics=live.semantics()
            live.check('renderer and ordinary core physical semantics identical',semantics==panorama['semantics'])
            live_case=live.live(folder/'ordinary-live',cell)
            A.write_json(folder/'live-input-trace.json',live.identity())
            report['cases'].append(dict(**case,info=info,semantics=semantics,
                panorama=dict(file=name+'/registered-renderer/full-room.png',room_unchanged=panorama['room_unchanged'],
                              all_player_fields_unchanged=panorama['all_player_fields_unchanged'],crop_copy_exact=panorama['crop_copy_exact']),
                native_alpha_composite=dict(file=name+'/registered-renderer/native-composites.json',
                    cells=len(composite['painted_cells']),dynamic_tiles=len(composite['dynamic_tiles']),exact=composite['complete']),
                live=dict(file=name+'/ordinary-live/climb.gif',frames=live_case['frames'],
                          minimum_health=live_case['minimum_health'],climb_frames=live_case['climb_frames']),
                checks=renderer.checks+live.checks))
            A.write_json(out/'report.json',report)
        report['complete']=all(c['passed'] for case in report['cases'] for c in case['checks'])
    finally:A.write_json(out/'report.json',report)
    return report


def isolated_drops(bundle,out,seed):
    out.mkdir(parents=True,exist_ok=True)
    report=dict(seed=seed,rom_sha256=sha(bundle/'bartgame.gba'),cases=[],complete=False)
    for kind in ('local','one-row'):
        capture=PolishCapture(bundle,out/('private-cores/'+kind),seed)
        candidates=[(n,i,e) for n in range(50) for i,e in enumerate(capture.world.edges[n][:capture.world.degree[n]])
                    if e.kind==3 and not e.require and ((e.target//2==n//2) if kind=='local' else
                        (e.target//10==n//10+1 and e.target//2!=n//2))]
        priority={21:0,18:1,0:2}
        candidates.sort(key=lambda row:(priority.get(row[0]//2,3),priority.get(row[2].target//2,3),row[0]))
        if not candidates:raise AssertionError('no genuine ungated '+kind+' DROP')
        n,i,e=candidates[0];detail=capture.drop(out/kind,n,i)
        report['cases'].append(dict(kind=kind,detail=detail,checks=capture.checks))
        A.write_json(out/'report.json',report)
    report['complete']=all(c['passed'] for case in report['cases'] for c in case['checks'])
    A.write_json(out/'report.json',report);return report


def waterfalls(bundle,out,seed):
    """Select actual generated width1/2/3 falls; never stamp test water."""
    out.mkdir(parents=True,exist_ok=True);found={};selections=[]
    finder=PolishCapture(bundle,out/'private-cores/finder',seed)
    for cell in [21,18,0]+[c for c in range(25) if c not in (21,18,0)]:
        finder.request(cell)
        fall=finder.fall()
        if fall['w'] and fall['w'] not in found:
            found[fall['w']]=cell;selections.append(dict(width=fall['w'],cell=cell,fall=fall))
        if set(found)=={1,2,3}:break
    if set(found)!={1,2,3}:raise AssertionError('seed lacks requested widths:'+str(found))
    cases=[]
    for width,cell in sorted(found.items()):
        folder=out/('width-'+str(width));folder.mkdir(exist_ok=True)
        renderer=PolishCapture(bundle,out/('private-cores/width%d-renderer'%width),seed)
        renderer.request(cell);renderer.advance([],8)
        renderer.panorama(folder/'registered-renderer')
        live=PolishCapture(bundle,out/('private-cores/width%d-live'%width),seed)
        live.request(cell);fall=live.fall()
        # Keep the real camera near the flow by navigating to safe dry floor
        # beneath it; no camera/clock assignment enters this ordinary core.
        info=live.info();px=(fall['x']+fall['w']//2)*16+8
        candidates=[(px,y*16+14) for y in range(fall['y']+fall['h'],min(23,fall['y']+fall['h']+5))
                    if live.tile_type(px,y*16+10)==0 and live.feet_clear(px,y*16+14)]
        if candidates:live.nav(*candidates[0],0)
        # Real camera easing is limited to4px/frame. Direct hero navigation
        # from a right-hand spawn can otherwise leave the entire fall off
        # screen for the first half of a stationary clip. Observe and wait
        # for the game's camera; never assign camera/scroll values here.
        settle_frames=0
        while settle_frames<160:
            st=live.state();cx,cy=st['camera'];actor=st['actor']
            target=[max(0,min(272,actor['x']-120)),max(0,min(224,actor['y']-104))]
            if [cx,cy]==target:break
            live.advance([],1);settle_frames+=1
        before=live.state()
        live.check('ordinary camera has naturally settled near actualwaterfall',before['camera']==[
            max(0,min(272,before['actor']['x']-120)),max(0,min(224,before['actor']['y']-104))],
            dict(camera=before['camera'],settle_frames=settle_frames))
        frames=folder/'raw-frames';frames.mkdir(exist_ok=True)
        pictures=[];water_hashes=[];minimum_health=before['health'][0]
        for step in range(12):
            chunk=frames/('step-%02d'%step);chunk.mkdir(exist_ok=True)
            samples,trace=live.advance([],8,record=chunk)
            minimum_health=min(minimum_health,trace['minimum_health'])
            pictures.extend((step*8+i,im,st,'step-%02d/'%step+file) for i,im,st,file in samples)
            payload=b''.join(live.bg2(x,y)[0] for y in range(fall['y'],fall['y']+fall['h'])
                             for x in range(fall['x'],fall['x']+fall['w']))
            water_hashes.append(dict(step=step,clock=live.state()['clock'],native_BG2_flow_sha256=A.digest(payload)))
        images=[im for _,im,_,_ in pictures]
        visibility=[]
        for index,im,st,file in pictures:
            cx,cy=st['camera'];left=fall['x']*16-cx;right=(fall['x']+fall['w'])*16-cx
            top=fall['y']*16-cy;bottom=(fall['y']+fall['h'])*16-cy
            y0,y1=max(20,top),min(160,bottom)
            horizontal=left>=0 and right<=240
            visible_height=max(0,y1-y0)
            enough=visible_height>=min(64,fall['h']*16-16)
            blue=0;area=0
            if horizontal and visible_height:
                crop=im.crop((left,y0,right,y1));area=crop.width*crop.height
                blue=sum(b-r>=24 and b-g>=8 for r,g,b in crop.getdata())
            pixels=blue>=max(12,area//10) and area>0
            visibility.append(dict(frame=index,camera=[cx,cy],fall_screen_rect=[left,top,right,bottom],
                                   visible_height=visible_height,blue_pixels=blue,sample_area=area,
                                   horizontal_complete=horizontal,body_visible=enough,blue_in_actual_image=pixels))
        images[0].save(folder/'flow.gif',save_all=True,append_images=images[1:],duration=67,loop=0,optimize=False)
        images[0].save(folder/'flow.png')
        after=live.state()
        # Confirm actual animation payload in VRAM changes with time. Still
        # PNGs/GIFs remain real complete frames, not repainted source crops.
        live.check('ordinary water clip uses advancing positive-health simulation',after['clock']>before['clock'] and minimum_health>0)
        live.check('water width comes from actual generated region',live.fall()['w']==width and 1<=width<=3)
        live.check('actual native waterfall BG2 pixels animate',len({row['native_BG2_flow_sha256'] for row in water_hashes})>1)
        live.check('ordinary water never enables frozen camera',live.run.u8('gForestReviewEnabled')==0)
        live.check('every ordinaryclipframe visibly contains fullfallwidth and enoughbody',
                   all(v['horizontal_complete'] and v['body_visible'] and v['blue_in_actual_image'] for v in visibility),visibility)
        detail=dict(width=width,cell=cell,fall=fall,before=before,after=after,frames=96,
                    minimum_health=minimum_health,checks=live.checks,native_water_animation=water_hashes,
                    ordinary_camera_settle_frames=settle_frames,actual_frame_water_visibility=visibility,
                    raw_frames=[dict(frame=i,file='raw-frames/'+file,state=st) for i,_,st,file in pictures])
        A.write_json(folder/'provenance.json',detail);A.write_json(folder/'input-trace.json',live.identity());cases.append(detail)
    report=dict(seed=seed,rom_sha256=sha(bundle/'bartgame.gba'),tool_sha256=sha(__file__),selections=selections,cases=cases,
                complete=all(c['passed'] for case in cases for c in case['checks']))
    A.write_json(out/'report.json',report);return report


def observe_runtime(bundle,out,seed):
    """Established real trial/bombgate harness with read-only polish observer."""
    compile_abi(bundle,out/'observer-abi');abi=D.landing_abi(bundle,out/'landing-abi',out/'observer-abi/headers')
    rom=NativeRom(bundle);script=TOOLS/'cream_runtime_review.py';observations=[];last=None
    def observe(frame,event,arg):
        nonlocal last
        if event!='return' or frame.f_code.co_name!='status' or Path(frame.f_code.co_filename)!=script:return
        context=frame.f_globals
        if context.get('active_capture') is None or not isinstance(arg,dict):return
        core=context.get('c')
        if core is None or arg.get('area')!=3:return
        clock=P.r32(core,P.sym('gFrame'))
        if clock==last:return
        last=clock;observations.append(dict(clock=clock,state=arg.copy(),landings=read_shadows(core,abi,rom)))
    sys.argv=[str(script),'--bundle',str(bundle),'--out',str(out/'earned-runtime'),'--seed',str(seed),'--stop-after-long-drop']
    code=0
    try:
        sys.setprofile(observe);runpy.run_path(str(script),run_name='__main__')
    except SystemExit as e:code=e.code or 0
    finally:
        sys.setprofile(None);A.write_json(out/'read-only-cache-observations.json',observations)
    path=out/'earned-runtime/long-drop.json';checks=[]
    if code==0 and path.exists():
        detail=json.loads(path.read_text());target=detail['frames'][-1]['node']
        upright=[r for r in observations if r['state']['node']==target and r['state']['state']==1
                 and r['state']['actor']['kind']==1 and r['state']['actor']['z']==0 and r['state']['actor']['state']==0]
        chosen=upright[0] if upright else None
        own=[] if chosen is None else [e for e in chosen['landings'] if e['flags']&1 and
             (e['x'],e['y'])==(chosen['state']['actor']['x'],chosen['state']['actor']['y'])]
        checks=[dict(name='earned input/tool harness completes long fall',passed=code==0),
                dict(name='fall renders at least3interveningrows',passed=detail['span']>=3),
                dict(name='real landing matches exact incoming arrival',passed=bool(own)),
                dict(name='actual foot stands on final verified shadow art',passed=bool(chosen and any(D.in_shadow(e,chosen['state']['actor']) for e in own)))]
    else:checks=[dict(name='earned real-input long drop exists',passed=False,observed=dict(code=code,path_exists=path.exists()))]
    report=dict(rom_sha256=sha(bundle/'bartgame.gba'),seed=seed,checks=checks,observations=len(observations),
                complete=all(c['passed'] for c in checks),fixture='Established harness standing/z waypoint normalization; real tools/rewards/gates/fall outcomes.')
    A.write_json(out/'report.json',report);return int(not report['complete'])


def menu_cache(bundle,out,seed):
    """Actual START open/close must preserve the dynamic world characters."""
    out.mkdir(parents=True,exist_ok=True)
    capture=PolishCapture(bundle,out/'private-core',seed)
    capture.prepare(21)
    before=capture.state()
    room_before=A.raw(capture.c,P.sym('gRoom'),capture.extra['room_size'])
    paint_before=A.raw(capture.c,P.sym('gCreamPolishWallPaint'),2048)
    native_before=capture.composites(out/'before')
    capture.c.bg_video.to_pil().convert('RGB').save(out/'before.png')
    capture.advance('START',1)
    capture.advance([],12)
    paused=capture.state()
    capture.check('real START opens the actual item menu',paused['state']==4 and paused['health'][0]>0,paused)
    capture.c.bg_video.to_pil().convert('RGB').save(out/'menu.png')
    capture.advance('START',1)
    capture.advance([],12)
    after=capture.state()
    capture.check('real START closes menu to living field play',after['state']==capture.run.abi['enum_play'] and after['health'][0]>0,after)
    capture.check('menu roundtrip preserves complete semantic room and paintmap',
        room_before==A.raw(capture.c,P.sym('gRoom'),capture.extra['room_size']) and
        paint_before==A.raw(capture.c,P.sym('gCreamPolishWallPaint'),2048))
    native_after=capture.composites(out/'after')
    capture.check('actual menu close preserves exact native BG2alpha unions',native_before['complete'] and native_after['complete'])
    overflow=P.r16(capture.c,P.sym('gCreamPolishBlendOverflow'))
    capture.check('menu close produces no blend overflow',overflow==0,overflow)
    capture.check('menu probe never enables frozen camera',capture.run.u8('gForestReviewEnabled')==0)
    capture.c.bg_video.to_pil().convert('RGB').save(out/'after.png')
    report=dict(rom_sha256=sha(bundle/'bartgame.gba'),source_commit=(bundle/'source-commit.txt').read_text().strip(),
        tool_sha256=sha(__file__),seed=seed,before=before,paused=paused,after=after,
        blend_overflow=overflow,checks=capture.checks,complete=all(c['passed'] for c in capture.checks),
        assignments='Only existing disclosed title seed, room request and hero navigation/facing; actual START input opens/closes menu. No cache/VRAM/palette assignments.')
    A.write_json(out/'report.json',report);A.write_json(out/'input-trace.json',capture.identity())
    return report


def run_logged(command,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w') as log:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle',required=True);p.add_argument('--out',required=True)
    p.add_argument('--seed',type=lambda text:int(text,0),default=0xb4a7)
    p.add_argument('--compare',action='append',default=[],metavar='LABEL=BUNDLE')
    p.add_argument('--waterfalls',action='store_true');p.add_argument('--earned-long',action='store_true')
    p.add_argument('--water-only',action='store_true',help='Replace only water evidence for the exact already captured ROM.')
    p.add_argument('--menu-cache-only',action='store_true',help='Actual menu roundtrip with native alpha-cache checks.')
    p.add_argument('--observe-runtime',action='store_true',help=argparse.SUPPRESS)
    a=p.parse_args();bundle=Path(a.bundle).resolve();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
    if a.observe_runtime:return observe_runtime(bundle,out,a.seed)
    if a.menu_cache_only:
        report=menu_cache(bundle,out/'menu-cache',a.seed)
        return int(not report['complete'])
    if a.water_only:
        water=waterfalls(bundle,out/'waterfalls',a.seed)
        report=json.loads((out/'report.json').read_text())
        if report['rom_sha256']!=sha(bundle/'bartgame.gba'):raise AssertionError('water-only bundle does not match existing report')
        report['water_capture_tool_sha256']=sha(__file__)
        report['water_capture_note']='Reframed through observed naturalcamera easing; everyactualGIFframe checked for onscreenblueflow. No game source changed.'
        report['checks']=[c for c in report['checks'] if c['name']!='actual1/2/3wide blue falls captured']
        report['checks'].append(dict(name='actual1/2/3wide blue falls captured',passed=water['complete']))
        report['complete']=all(c['passed'] for c in report['checks']);A.write_json(out/'report.json',report)
        return int(not report['complete'])
    report=dict(rom_sha256=sha(bundle/'bartgame.gba'),source_commit=(bundle/'source-commit.txt').read_text().strip(),
                tool_sha256=sha(__file__),checks=[],comparisons=[],complete=False)
    A.write_json(out/'report.json',report)
    current=matched(bundle,out/'matched/polish',a.seed)
    report['checks'].append(dict(name='matched rooms/climbs/native BG2 alpha unions pass',passed=current['complete']))
    for spec in a.compare:
        label,path=spec.split('=',1);control=Path(path).resolve();dest=out/'matched'/label
        run_logged([sys.executable,str(TOOLS/'cream_art_study_capture.py'),'--bundle',str(control),'--out',str(dest),'--seed',str(a.seed)],out/('logs/'+label+'.log'))
        prior=json.loads((dest/'report.json').read_text());checks=[dict(name='generated graph exact',passed=current['graph_sha256']==prior['graph_sha256'])]
        for new,old in zip(current['cases'],prior['cases']):
            checks.append(dict(name=new['name']+' profile/features exact',passed=new['info']==old['info']))
            checks.extend(dict(name=new['name']+' '+key,passed=new['semantics'][key]==old['semantics'][key]) for key in PHYSICAL)
        report['comparisons'].append(dict(label=label,rom_sha256=prior['rom_sha256'],checks=checks));report['checks'].extend(checks)
    drops=isolated_drops(bundle,out/'isolated-drops',a.seed)
    report['checks'].append(dict(name='actual short drops land on final shade art',passed=drops['complete']))
    if a.waterfalls:
        water=waterfalls(bundle,out/'waterfalls',a.seed);report['checks'].append(dict(name='actual1/2/3wide blue falls captured',passed=water['complete']))
    if a.earned_long:
        run_logged([sys.executable,str(Path(__file__).resolve()),'--observe-runtime','--bundle',str(bundle),'--out',str(out/'earned-long'),'--seed','1432'],out/'logs/earned-long.log')
        long=json.loads((out/'earned-long/report.json').read_text());report['checks'].append(dict(name='earned four-row drop supported shadow proof',passed=long['complete']))
    report['complete']=all(c['passed'] for c in report['checks']);A.write_json(out/'report.json',report)
    return int(not report['complete'])


if __name__=='__main__':raise SystemExit(main())

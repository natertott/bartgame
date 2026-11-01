#!/usr/bin/env python3
"""Focused canopy review using real mGBA framebuffer, OAM, VRAM and inputs.

Profiles11..18 change canopy art over the preserved base6 environment. A fresh
base6 capture is a historical visual control, not a passing never-hidden
implementation. Natural cases select generated rooms, health/inventory,
unrelated-enemy clearing and initial standing position/facing. Separate
diagnostic cases replace semantic terrain and invoke the frozen ROM renderer;
no framebuffer, sprite pose, z, actor timer or video tile is painted.

Every recorded action frame independently decodes the native body and any
foreground safety fragment. The latter must be an exact subset of that same
displayed body frame. Actual BG1 coverage is combined with their OAM priorities.
Displayed character-color proof includes only the body and a byte-validated,
current native cape at the exact body anchor; the body guard is checked
independently. Other effects, weapons, UI and nearby actors never count.
Native PNGs are authoritative. MP4s are lossy full-rate viewing copies; GIFs
are kept only when every sampled color is exact. Raw movie frames stay local.
"""
import argparse
import json
import shutil
import struct
import sys
from pathlib import Path

import forest_v2_review as V2
import forest_concept_review as F
import probe as P
import bloom_probe as BP
import critical_path as C

GROUPS={'landscapes','walk','actions','menu','diagnostic'}
VALID={6,*range(11,19)}
FACES=('n','e','s','w')
LANDSCAPES=(('healthy-canopy','0xb4a7',16,[280,236]),
            ('mixed-forest','0xb4a7',0,[264,252]),
            ('deep-blight','0x6',4,[312,252]))
FEATURES={
    'living':{'seed':'0xb4a7','cell':4,'position':[408,118],
              'under_position':[408,98],'target':[25,5],'stage':1},
    'sick':{'seed':'0xb4a7','cell':20,'position':[184,118],
            'under_position':[184,98],'target':[11,5],'stage':3},
}
sha=F.sha


def component(points):
    points=set(points);largest=0
    while points:
        todo=[points.pop()];size=0
        while todo:
            x,y=todo.pop();size+=1
            for at in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if at in points:points.remove(at);todo.append(at)
        largest=max(largest,size)
    return largest


class Review(V2.Review):
    def __init__(self,args):
        match=args.match;only=args.only
        args.match=None;args.only='landscapes,depth,diagnostic'
        super().__init__(args)
        args.match=match;args.only=only
        self.groups=set(only.split(',')) if only else set(GROUPS)
        if self.groups-GROUPS:raise ValueError('Unknown focused group')
        if args.variant is not None:
            self.check('requested profile matches frozen header',self.variant==args.variant)
        self.old=json.loads(Path(match).read_text()) if match else None
        self.old_rows={row['name']:row for row in self.old['captures']} if self.old else {}
        self.old_plan=self.old.get('plan',{}) if self.old else {}
        self.v3_tool_hash=sha(Path(__file__).read_bytes())
        self.dependencies['forest_v2_review.py']=sha(Path(V2.__file__).read_bytes())
        # Bind every local helper actually imported by this capture process,
        # including the older harnesses' transitive tool imports.
        for module in list(sys.modules.values()):
            filename=getattr(module,'__file__',None)
            if filename:
                path=Path(filename).resolve()
                if path.parent==Path(__file__).resolve().parent and path.name!=Path(__file__).name:
                    self.dependencies[path.name]=sha(path.read_bytes())
        self.recipe=self.freeze.get('label',f'Canopy profile {self.variant}')
        self.finished=False;self.frame_observations=[];self.action_images={}
        self._taking_scanout=False;self._scanout_pending=None;self._scanout_completed=None
        self.cape_fx_refs={};self.cape_body_refs={}
        fx_info,fx_payload=self.rom.sheet('bloomfx')
        hero_info,hero_payload=self.rom.sheet('hero')
        fx_palettes=self.rom.array('bloomfx_frame_pal')
        for face in ('N','E','S'):
            for phase in range(3):
                f=self.defs['F_BLOOMFX_CAPE_'+face+str(phase)]
                size=fx_info['frame_tiles']*32
                self.cape_fx_refs.setdefault(fx_payload[f*size:(f+1)*size],[]).append(
                    {'face':face,'phase':phase,'frame':f,'palette':fx_palettes[f],
                     'frame_name':'cape_'+face.lower()+str(phase)})
                h=self.defs['F_HERO_CAPE_'+face+str(phase+1)]
                size=hero_info['frame_tiles']*32
                self.cape_body_refs.setdefault(hero_payload[h*size:(h+1)*size],[]).append((face,phase))
        if self.old:
            self.check('matched baseline used this focused capture tool',
                       self.old.get('capture_tool_sha256')==self.v3_tool_hash)
            self.check('matched baseline is preserved base6 or first canopy study',
                       self.old.get('forest_variant') in VALID)
            self.check('matched baseline has the same game/art source revision',
                       self.old.get('source_commit')==self.freeze.get('source_commit'))

    def boot(self,row):
        super().boot(row)
        self._scanout_pending=None;self._scanout_completed=None
        # mGBA starts a video frame at visible scanline0 and ends it at160.
        # Pair the hardware that drew that frame with its finished image.
        # Post-run CPU/hardware state can already describe the next frame.
        self.c._callbacks.video_frame_started.append(self.scanout_start)
        self.c.add_frame_callback(self.scanout_end)

    def scanout_start(self):
        if not getattr(self,'recording_case',None) or not self.recording_state_calls:return
        self._taking_scanout=True
        try:
            model=self.depth_visibility()
            model['scanout_frame_counter']=self.c.frame_counter
            model['scanout_start_vcount']=P.r16(self.c,0x04000006)
            model['scanout_world_planes']=(P.r16(self.c,0x04000000)&0x600)==0x600
            self._scanout_pending=model
        finally:self._taking_scanout=False

    def scanout_end(self):
        if self._scanout_pending is None:return
        model=self._scanout_pending;self._scanout_pending=None
        image=self.c.bg_video.to_pil().convert('RGB')
        for kind,key in (('body','_expected_visible_pixels'),('character','_expected_character_pixels')):
            matches=[]
            for x,y,sx,sy,r,g,b in model.pop(key,[]):
                if image.getpixel((sx,sy))==(r,g,b):matches.append((x,y))
            model['framebuffer_exact_'+kind+'_color_pixels']=len(matches)
            model['framebuffer_exact_'+kind+'_color_component']=component(matches)
        model['scanout_end_vcount']=P.r16(self.c,0x04000006)
        model['scanout_end_frame_counter']=self.c.frame_counter
        model['hardware_image_pairing']='Native OAM/VRAM at mGBA scanline0; unchanged framebuffer at the same scanout end, line160.'
        self._scanout_completed=model

    def check(self,name,condition,detail=None):
        if name in ('valid forest study profile','valid second-round forest study profile'):
            name='valid canopy comparison profile';condition=self.variant in VALID
        F.Review.check(self,name,condition,detail)

    def clear(self):
        super().clear()
        calls=getattr(self,'recording_state_calls',0)
        row=getattr(self,'recording_case',None)
        if row and calls:
            tick=calls-1
            schedule=row.get('equipment_schedule',{})
            if str(tick) in schedule and tick not in self.equipment_applied:
                C.equip_b(self.c,schedule[str(tick)])
                self.equipment_applied.add(tick)

    def state(self,target=None):
        result=super().state(target)
        pl=P.sym('gPl')
        result['equipment']=list(F.read(self.c,pl+9,3))
        result['shield_up']=P.r8(self.c,pl+34)
        result['item_active']=P.r8(self.c,pl+21)
        result['displayed_world_planes']=(P.r16(self.c,0x04000000)&0x600)==0x600
        if getattr(self,'recording_case',None):
            tick=self.recording_state_calls-2
            if 0<=tick<self.recording_case.get('frames',0):
                result['depth_visibility']=self.depth_visibility()
                sample={'tick':tick,'position':result['position'],'state':result['state'],
                        'game_state':result['game_state'],
                        'displayed_world_planes':result['depth_visibility'].get('scanout_world_planes',result['displayed_world_planes']),
                        'irq_counter':P.r32(self.c,P.sym('gFrame')),
                        'gameplay_update_counter':P.r32(self.c,P.sym('gGame')+8),
                        'z_q16':result['z_q16'],'facing':P.r8(self.c,P.sym('gActors')+7),
                        'visibility':result['depth_visibility']}
                self.frame_observations.append(sample)
                if tick in (0,12,18,64,72,112,120,128):
                    self.action_images[tick]=self.c.bg_video.to_pil().convert('RGB').copy()
                v=sample['visibility']
                score=v.get('visible_colored_pixels',0)
                eligible=result['game_state']==1 and v.get('scanout_world_planes',result['displayed_world_planes']) and v.get('body_found')
                if eligible:
                    image=None
                    if self.worst_image is None or score<self.worst_image[0]:
                        image=self.c.bg_video.to_pil().convert('RGB').copy();self.worst_image=(score,tick,image)
                    shown=v.get('framebuffer_exact_character_color_pixels',0)
                    if self.worst_character_image is None or shown<self.worst_character_image[0]:
                        image=image or self.c.bg_video.to_pil().convert('RGB').copy()
                        self.worst_character_image=(shown,tick,image)
                    body_only=v.get('framebuffer_exact_body_color_pixels',0)
                    if v.get('attached_cape') and (self.cape_overlap_image is None or body_only<self.cape_overlap_image[0]):
                        image=image or self.c.bg_video.to_pil().convert('RGB').copy()
                        self.cape_overlap_image=(body_only,tick,image)
        return result

    def depth_visibility(self):
        """Independent native body/foreground fragment and BG1 composition."""
        if not self._taking_scanout and self._scanout_completed is not None:
            return self._scanout_completed
        c=self.c;oam=BP.oam(c);hero=next((o for o in oam if o['tile']==0),None)
        if hero is None:return {'body_found':False}
        w,h=self.hero_info['width'],self.hero_info['height']
        camera=P.sym('gForestV2DisplayedCamera')
        camx,camy=struct.unpack('<hh',F.read(c,camera,4))
        telemetry=None;guard=None
        if 'gForestV3Visibility' in self.rom.symbols:
            telemetry=list(struct.unpack('<12H',F.read(c,P.sym('gForestV3Visibility'),24)))
            if telemetry[2]:guard=next((o for o in oam if o['tile']==telemetry[2]),None)
        colors=struct.unpack('<16H',F.read(c,0x05000200+hero['pal']*32,32))
        colored=[bool(i and max(v&31,(v>>5)&31,(v>>10)&31)>=5 and
                      (v&31)+((v>>5)&31)+((v>>10)&31)>=10) for i,v in enumerate(colors)]
        pixels=F.read(c,0x06010000,w*h//2)
        guard_pixels=F.read(c,0x06010000+guard['tile']*32,w*h//2) if guard else None
        def ink(data,x,y):
            at=((y//8)*(w//8)+x//8)*32+(y&7)*4+(x&7)//2
            return (data[at]>>((x&1)*4))&15
        exact_guard=True;guard_opaque=guard_colored=0
        if guard:
            exact_guard &= all(guard[k]==hero[k] for k in ('x','y','pal','flip','shape','size'))
            exact_guard &= guard['priority']==1
            for y in range(h):
                for x in range(w):
                    g=ink(guard_pixels,x,y)
                    if g:
                        exact_guard &= g==ink(pixels,x,y)
                        guard_opaque+=1;guard_colored+=colored[g]
        counts={'upper_body_opaque':0,'upper_body_covered':0,'feet_opaque':0,'feet_covered':0,
                'opaque_colored_pixels':0,'visible_colored_pixels':0,
                'native_opaque_pixels':0,'body_pixels_covered_without_guard':0}
        visible=set();actual_matches=set();cache={}
        overhead=P.sym('forest_v2_overhead');visual=P.sym('gRoomVisualOverlay')
        def bg_covers(wx,wy,priority):
            if priority<=1 or not(0<=wx<512 and 0<=wy<384):return False
            cell=(wx//16,wy//16)
            if cell not in cache:
                mt=P.r16(c,visual+(cell[1]*32+cell[0])*2)&65535
                cache[cell]=mt!=65535 and bool(P.r8(c,overhead+mt))
            if not cache[cell]:return False
            tx,ty=wx//8,wy//8;sb=24+(ty>>5)*2+(tx>>5)
            entry=P.r16(c,0x06000000+sb*2048+((ty&31)*32+(tx&31))*2)&65535
            xx,yy=wx&7,wy&7
            if entry&0x400:xx=7-xx
            if entry&0x800:yy=7-yy
            return bool((P.r8(c,0x06000000+(entry&1023)*32+yy*4+xx//2)>>((xx&1)*4))&15)
        image=None if self._taking_scanout else c.bg_video.to_pil().convert('RGB')
        expected_pixels=[]
        for y in range(h):
            for x in range(w):
                source_x=w-1-x if hero['flip'] else x
                color=ink(pixels,source_x,y)
                if not color:continue
                counts['native_opaque_pixels']+=1
                group='feet' if y>=h-4 else 'upper_body' if y<h-8 else None
                if group:counts[group+'_opaque']+=1
                wx,wy=hero['x']+x+camx,hero['y']+y+camy
                if not(0<=wx<512 and 0<=wy<384):continue
                covered=bg_covers(wx,wy,hero['priority'])
                if covered:counts['body_pixels_covered_without_guard']+=1
                rescued=bool(guard and exact_guard and ink(guard_pixels,source_x,y)==color)
                covered &= not rescued
                if covered and group:counts[group+'_covered']+=1
                if colored[color]:
                    counts['opaque_colored_pixels']+=1
                    if not covered:
                        visible.add((x,y));sx,sy=hero['x']+x,hero['y']+y
                        if 0<=sx<240 and 0<=sy<160:
                            v=colors[color]
                            expected=tuple((part<<3)|(part>>2) for part in
                                           (v&31,(v>>5)&31,(v>>10)&31))
                            expected_pixels.append((x,y,sx,sy,*expected))
                            if image is not None and image.getpixel((sx,sy))==expected:actual_matches.add((x,y))
        counts['visible_colored_pixels']=len(visible)
        counts['largest_visible_colored_component']=component(visible)
        character={(p[0],p[1]):p for p in expected_pixels}
        attached_cape=None
        # Only the validated current, anchored native cape joins Bloom's
        # character composite. Weapons, effects, UI and nearby actors do not.
        body_cape_poses=self.cape_body_refs.get(pixels,[])
        if body_cape_poses:
            action_tile=P.r16(c,self.static_address('sActionTile'))&65535
            cape=next((o for o in oam if o['tile']==action_tile),None)
            if cape and all(cape[k]==hero[k] for k in ('x','y','shape','size','flip')):
                cape_pixels=F.read(c,0x06010000+cape['tile']*32,w*h//2)
                reference=next((ref for ref in self.cape_fx_refs.get(cape_pixels,[]) if
                                (ref['face'],ref['phase']) in body_cape_poses and ref['palette']==cape['pal']),None)
                if reference:
                    cape_colors=struct.unpack('<16H',F.read(c,0x05000200+cape['pal']*32,32))
                    attached_cape={'OAM':cape,'native_frame':reference,'VRAM_sha256':sha(cape_pixels),
                                   'native_body_pose_candidates':body_cape_poses,
                                   'anchor_projection_delta':[cape['x']-hero['x'],cape['y']-hero['y']],
                                   'exact_current_native_pose_and_anchor':True}
                    for y in range(h):
                        for x in range(w):
                            sx=w-1-x if cape['flip'] else x
                            ci=ink(cape_pixels,sx,y)
                            if not ci:continue
                            wx,wy=cape['x']+x+camx,cape['y']+y+camy
                            if bg_covers(wx,wy,cape['priority']):continue
                            # Resolve original body, safety fragment and cape
                            # using the GBA priority and OAM-index ordering.
                            body_y=y
                            depth=[];bi=ink(pixels,sx,body_y) if 0<=body_y<h else 0
                            if bi and not bg_covers(wx,wy,hero['priority']):depth.append((hero['priority'],hero['index']))
                            if guard and exact_guard and 0<=body_y<h and ink(guard_pixels,sx,body_y):depth.append((guard['priority'],guard['index']))
                            if depth and (cape['priority'],cape['index'])>=min(depth):continue
                            color=cape_colors[ci]
                            meaningful=max(color&31,(color>>5)&31,(color>>10)&31)>=5 and (color&31)+((color>>5)&31)+((color>>10)&31)>=10
                            px,py=cape['x']+x,cape['y']+y
                            if meaningful and 0<=px<240 and 0<=py<160:
                                rgb=tuple((v<<3)|(v>>2) for v in (color&31,(color>>5)&31,(color>>10)&31))
                                character[x,body_y]=(x,body_y,px,py,*rgb)
                            else:character.pop((x,body_y),None)
        character_pixels=list(character.values())
        actual_character=[(x,y) for x,y,sx,sy,r,g,b in character_pixels if image is not None and image.getpixel((sx,sy))==(r,g,b)]
        result={'body_found':True,'body_priority':hero['priority'],
                'body_VRAM_sha256':sha(pixels),
                'applied_camera':[camx,camy],'camera_source':'actual applied BG1 scroll telemetry',
                'guard_telemetry':telemetry,'guard_OAM':guard,'guard_exact_native_subset':bool(exact_guard),
                'guard_opaque_pixels':guard_opaque,'guard_colored_pixels':guard_colored,
                'guard_VRAM_sha256':sha(guard_pixels) if guard_pixels is not None else None,
                'attached_cape':attached_cape,
                'native_body_matches_cape_bitmap':bool(body_cape_poses),
                'framebuffer_exact_body_color_pixels':len(actual_matches),
                'framebuffer_exact_body_color_component':component(actual_matches),
                'framebuffer_exact_character_color_pixels':len(actual_character),
                'framebuffer_exact_character_color_component':component(actual_character),**counts}
        if self._taking_scanout:
            result['_expected_visible_pixels']=expected_pixels
            result['_expected_character_pixels']=character_pixels
        return result

    def record(self,row,point,target=None,facing=0,events=None,extra=None):
        row=dict(row);point=list(point);target=list(target) if target is not None else None
        extra=dict(extra or {})
        extra['fixture_kind']=('diagnostic logical-room adjacency fixture' if self.diagnostic_context
                               else 'natural generated room; navigation/inventory/player fixtures only')
        if self.diagnostic_context:extra['diagnostic_room']=self.diagnostic_context
        self.recording_action=row.get('action');self.recording_case=row
        self.recording_state_calls=0;self.recording_initial_state=None
        self.pending_barrier_frame=None;self.first_barrier_clear_tick=None
        self.roll_samples=[];self.previous_recorded_z=0
        self.frame_observations=[];self.action_images={};self.worst_image=None
        self.worst_character_image=None;self.cape_overlap_image=None
        self._scanout_pending=None;self._scanout_completed=None
        self.equipment_applied=set()
        old=self.old_rows.pop(row['name'],None)
        F.Review.record(self,row,point,target,facing,events,extra)
        r=self.rows[-1]
        if old:
            self.old_rows[row['name']]=old
            fields=('seed','cell','position','target','facing','physical_contract',
                    'final_physical_contract','maze_sha256','initial_progress_sha256',
                    'final_progress_sha256','initial_rng','final_rng','inputs','equipment_schedule')
            match={field:old.get(field)==r.get(field) for field in fields}
            visual={'oam','player_priority','bg_palette_sha256','obj_palette_sha256',
                    'protected_UI_palette_sha256','authored_BG_palette_phase','depth_oam',
                    'displayed_BG_palette_phase','target_BG_ground_quarters','chest_stream',
                    'landmark_stream','depth_visibility'}
            for field in ('initial','final'):
                match[field+'_logical_state']={k:v for k,v in old[field].items() if k not in visual}=={k:v for k,v in r[field].items() if k not in visual}
            match['mechanic_transition_order']=[t['state'] for t in old['mechanic_transitions']]==[t['state'] for t in r['mechanic_transitions']]
            r['matched_case']=match
            self.check(row['name']+' matches frozen baseline physical/gameplay contract',all(match.values()),match)
            if old.get('cadence_observation'):
                expected=old['cadence_observation']['zero_update_video_intervals']
                # inspect_case computes the candidate interval summary below.
                r['baseline_zero_update_video_intervals']=expected
        self.inspect_case(r);self.extra_keyframes(r);self.save()
        self.recording_case=None;self.recording_action=None

    def inspect_case(self,r):
        name=r['name'];samples=self.frame_observations
        self.check(name+' all actual recorded frames have native visibility observations',len(samples)==r['video_frames'])
        self.check(name+' every image is paired with its actual scanline0 hardware',
                   all(s['visibility'].get('scanout_start_vcount')==0 and
                       s['visibility'].get('scanout_end_vcount')==160 and
                       s['visibility'].get('scanout_frame_counter')==s['visibility'].get('scanout_end_frame_counter')
                       for s in samples))
        self.check(name+' actual selected OBJ colors remain native ROM colors',
                   all(s['selected_OBJ_palette_bytes_match_ROM'] for s in r['hardware_samples']))
        self.check(name+' retains semantic geometry',r['physical_contract']==r['final_physical_contract'])
        menu_gap=[s['tick'] for s in samples if r.get('action')=='canopy-menu' and
                  s['game_state']==1 and s['displayed_world_planes'] and not s['visibility'].get('body_found')]
        gameplay=[s for s in samples if s['game_state']==1 and s['displayed_world_planes'] and s['tick'] not in menu_gap]
        if r.get('action')=='canopy-menu':
            r['menu_resume_hardware_gap']={'ticks':menu_gap,
                'note':'Recorded sourceGS_PLAY/world-plane return boundary before hardware OAM contains a player. This existing interface-to-world transfer is not canopy coverage; resumed body frames are checked without omissions.'}
            previous=self.old_rows.get(name,{}).get('menu_resume_hardware_gap')
            if previous is not None:
                self.check(name+' menu return introduces no additional missing-player hardware frames',
                           len(menu_gap)<=len(previous['ticks']),{'baseline':previous['ticks'],'candidate':menu_gap})
        violations=[]
        for s in gameplay:
            v=s['visibility'];minimum=max(12,(v.get('opaque_colored_pixels',0)+3)//4)
            if not(v.get('body_found') and v.get('visible_colored_pixels',0)>=minimum and
                   v.get('largest_visible_colored_component',0)>=8):
                violations.append({'tick':s['tick'],'state':s['state'],'z_q16':s['z_q16'],
                                   'visible':v.get('visible_colored_pixels',0),'minimum':minimum,
                                   'component':v.get('largest_visible_colored_component',0)})
        r['visibility_observations']=samples
        intervals=[{'from_tick':a['tick'],'to_tick':b['tick'],
                    'irq_delta':(b['irq_counter']-a['irq_counter'])&0xffffffff,
                    'gameplay_update_delta':(b['gameplay_update_counter']-a['gameplay_update_counter'])&0xffffffff}
                   for a,b in zip(samples,samples[1:]) if
                   a['game_state']==b['game_state']==1 and a['displayed_world_planes'] and b['displayed_world_planes']]
        r['cadence_observation']={'intervals':intervals,
            'zero_update_video_intervals':sum(v['gameplay_update_delta']==0 for v in intervals),
            'maximum_update_delta':max((v['gameplay_update_delta'] for v in intervals),default=0),
            'maximum_irq_delta':max((v['irq_delta'] for v in intervals),default=0),
            'note':'Counters read after each real mGBA video frame. Recorded gameplay cadence only; these are not CPU-cycle benchmarks or a universal performance guarantee.'}
        if 'baseline_zero_update_video_intervals' in r:
            self.check(name+' adds no missed gameplay-update video intervals',
                       r['cadence_observation']['zero_update_video_intervals']<=r['baseline_zero_update_video_intervals'],
                       {'baseline':r['baseline_zero_update_video_intervals'],
                        'candidate':r['cadence_observation']['zero_update_video_intervals']})
        r['visibility_summary']={'frames':len(samples),'gameplay_frames':len(gameplay),
            'interface_or_transition_frames':[s['tick'] for s in samples if s not in gameplay],
            'violations':violations,
            'minimum_visible_colored_pixels':min((s['visibility'].get('visible_colored_pixels',0) for s in gameplay),default=0),
            'minimum_connected_colored_component':min((s['visibility'].get('largest_visible_colored_component',0) for s in gameplay),default=0),
            'minimum_displayed_character_colored_pixels':min((s['visibility'].get('framebuffer_exact_character_color_pixels',0) for s in gameplay),default=0),
            'minimum_displayed_character_component':min((s['visibility'].get('framebuffer_exact_character_color_component',0) for s in gameplay),default=0),
            'minimum_body_only_displayed_colored_pixels':min((s['visibility'].get('framebuffer_exact_body_color_pixels',0) for s in gameplay),default=0),
            'scope':'All actual recorded video frames. Baseline6 deficits are retained as historical observations; new studies enforce at least25% of colored body ink,12colored pixels and an8pixel connected component.'}
        if self.variant>=11:
            self.check(name+' never loses a meaningful connected native body',not violations,violations)
            self.check(name+' foreground safety fragment uses exact current native frame pixels',
                       all(s['visibility'].get('guard_exact_native_subset',False) for s in gameplay))
            self.check(name+' actual framebuffer retains a recognizable native character',
                       all(s['visibility'].get('framebuffer_exact_character_color_pixels',0)>=12 and
                           s['visibility'].get('framebuffer_exact_character_color_component',0)>=8
                           for s in gameplay),
                       {'minimum_pixels':min((s['visibility'].get('framebuffer_exact_character_color_pixels',0) for s in gameplay),default=0),
                        'minimum_component':min((s['visibility'].get('framebuffer_exact_character_color_component',0) for s in gameplay),default=0),
                        'note':'Body remains subject to its separate native25%/12/8 canopy guard test. Only a byte-validated current anchored cape may replace body-color pixels in this displayed character proof.'})
        if r.get('action')=='canopy-actions':
            self.check(name+' actual sword state occurs',any(s['state']==2 for s in samples))
            self.check(name+' shield is actually raised',any(t.get('shield_up') for t in r['trace']))
        if r.get('action')=='canopy-cape':
            self.check(name+' ordinary cape input creates actual airborne jump',any(s['state']==5 and s['z_q16']>0 for s in samples))
            self.check(name+' cape returns to ordinary standing',r['final']['state']==0 and not r['final']['z_q16'])
            # Idle and cape anticipation intentionally share some body
            # bitmaps. The actual anchored cape OBJ establishes ownership;
            # an idle body alone is not evidence that a cape should exist.
            capes=[s['visibility']['attached_cape'] for s in gameplay if s['visibility'].get('attached_cape')]
            self.check(name+' actual jump includes a current native cape at the exact body anchor',
                       bool(capes) and all(v['exact_current_native_pose_and_anchor'] for v in capes))
        if r.get('action')=='canopy-menu':
            self.check(name+' ordinary Start input opens actual menu',any(s['game_state']==4 for s in samples))
            self.check(name+' actual menu closes and resumes under-canopy play',
                       r['final']['game_state']==1 and len(gameplay)>=64)
            self.check(name+' native world palette and mappings restore after menu',
                       all(s['world_palette_bytes_match_ROM'] and s['native_room_mappings'] for s in r['hardware_samples']))
        if r.get('action')=='canopy-depth':
            self.check(name+' ordinary input moves beneath actual foreground',
                       any(s['position']!=r['initial']['position'] for s in samples))
            self.check(name+' actual partial upper-body occlusion remains',
                       any(0<s['visibility'].get('upper_body_covered',0)<s['visibility'].get('upper_body_opaque',0) for s in samples))
        if r.get('group')=='diagnostic':
            self.check(name+' diagnostic room is explicitly disclosed',r['fixture_kind'].startswith('diagnostic'))

    def extra_keyframes(self,r):
        selected_images=dict(self.action_images)
        for item in (self.worst_image,self.worst_character_image,self.cape_overlap_image):
            if item:selected_images[item[1]]=item[2]
        def native(tick):
            relative=f'{r["name"]}/frame-{tick:03}.png';destination=self.out/relative
            if not destination.exists():
                raw=self.out/'all-frames'/r['name']/f'frame-{tick:03}.png'
                if raw.exists():shutil.copyfile(raw,destination)
                elif tick in selected_images:selected_images[tick].save(destination)
                else:raise RuntimeError('Native frame unavailable: '+relative)
            if relative not in r['native_frames']:r['native_frames'].append(relative)
            return {'tick':tick,'path':relative,'sha256':sha(destination.read_bytes())}
        if self.worst_image:
            item=native(self.worst_image[1]);item['label']='Least visible body'
            r['worst_visibility_keyframe']=item
        if r.get('action')=='canopy-depth' and r.get('movie'):
            samples=self.frame_observations
            cover=[s for s in samples if s['state']==0 and not s['z_q16'] and
                   0<s['visibility'].get('upper_body_covered',0)<s['visibility'].get('upper_body_opaque',0)]
            keys=[]
            if cover:
                under=max(cover,key=lambda s:s['visibility']['upper_body_covered'])
                before=next((s for s in samples if s['tick']<under['tick'] and not s['visibility'].get('upper_body_covered',0)),None)
                after=next((s for s in reversed(samples) if s['tick']>under['tick'] and not s['visibility'].get('upper_body_covered',0)),None)
                for label,sample in (('Before',before),('Under',under),('Emerged',after)):
                    if sample:keys.append(dict(native(sample['tick']),label=label,visibility=sample['visibility']))
            r['phase_keyframes']=keys
            self.check(r['name']+' native before/under/emerged frames selected',len(keys)==3,keys)
        labels=({12:'Sword action',64:'Shield held'} if r.get('action')=='canopy-actions' else
                {18:'Cape flight'} if r.get('action')=='canopy-cape' else
                {0:'Before menu',18:'Menu open',64:'After resume'} if r.get('action')=='canopy-menu' else {})
        r['action_keyframes']=[dict(native(tick),label=label) for tick,label in labels.items()]
        if self.worst_character_image:
            item=dict(native(self.worst_character_image[1]),label='Least visible displayed character')
            r['displayed_character_keyframe']=item
            r['action_keyframes'].append(item)
        if self.cape_overlap_image:
            tick=self.cape_overlap_image[1]
            sample=next(s for s in self.frame_observations if s['tick']==tick)
            r['action_keyframes'].append(dict(native(tick),label='Cape overlaps body',visibility=sample['visibility']))
        if r['name']=='deep-blight' and r.get('movie'):
            phases={}
            for sample in r['trace']:
                if sample.get('displayed_BG_palette_phase') is not None:
                    phases.setdefault(sample['displayed_BG_palette_phase'],sample['tick'])
            r['pulse_phase_keyframes']=[dict(native(tick),phase=phase) for phase,tick in sorted(phases.items())]

    def landscapes(self):
        for name,seed,cell,point in LANDSCAPES:
            row={'name':name,'seed':seed,'cell':cell,'group':'landscapes','frames':48,'movie':True}
            self.boot(row)
            self.check(name+' chosen generated standing point is physically safe',self.safe(*point))
            self.record(row,point,extra={'note':'Matched naturally generated healthy/mixed/deep canopy context. No terrain injection.'})

    def walk(self):
        for kind,feature in FEATURES.items():
            row=dict(feature,name=kind+'-canopy-walkunder',group='walk',action='canopy-depth',movie=True,frames=128)
            self.boot(row);C.equip_b(self.c,C.EQ_SWORD)
            events={8:[('UP',True)],20:[('R',True)],22:[('R',False)],
                    64:[('UP',False),('DOWN',True)],96:[('DOWN',False)]}
            self.record(row,feature['position'],feature['target'],events=events,
                        extra={'note':'Ordinary walk, roll, real wall impact/recoil and retreat at generated canopy edge.'})

    def actions(self):
        for kind,feature in FEATURES.items():
            for face,direction in enumerate(FACES):
                row=dict(feature,name=f'{kind}-actions-{direction}',group='actions',action='canopy-actions',
                         frames=100,movie=kind=='sick' and face==0,
                         equipment_schedule={'0':C.EQ_SWORD,'48':C.EQ_SHIELD})
                self.boot(row);C.equip_b(self.c,C.EQ_SWORD)
                self.check(row['name']+' initial under-canopy point physically safe',self.safe(*feature['under_position']))
                self.record(row,feature['under_position'],feature['target'],face,
                            {8:[('A',True)],10:[('A',False)],56:[('A',True)],80:[('A',False)]},
                            {'note':'Initial facing/inventory fixture; real sword input followed by disclosed A-slot shield assignment and ordinary held input. No pose/timer assignment.'})
            row=dict(feature,name=kind+'-cape-under-canopy',group='actions',action='canopy-cape',
                     frames=64,movie=False)
            self.boot(row);C.equip_b(self.c,C.EQ_CLOAK)
            self.record(row,feature['under_position'],feature['target'],0,{8:[('A',True)],10:[('A',False)]},
                        {'note':'Actual cape jump facing the generated canopy collision limit; real z and timers.'})

    def diagnostic(self):
        for kind in ('living-canopy','sick-canopy'):
            for shape in ('isolated-sizes','narrow-inner-corners'):
                row={'name':'diagnostic-'+kind+'-'+shape,'group':'diagnostic','seed':hex(self.seed),
                     'cell':16,'frames':24,'movie':False}
                self.boot(row);point=self.diagnostic_fixture(kind,shape)
                self.record(row,point,extra={'note':'Explicit semantic adjacency fixture, not a naturally generated room.'})
                self.diagnostic_context=None
            row={'name':'diagnostic-'+kind+'-corner-motion','group':'diagnostic','seed':hex(self.seed),
                 'cell':16,'frames':128,'movie':kind=='sick-canopy','action':'canopy-depth'}
            self.boot(row);self.diagnostic_fixture(kind,'narrow-inner-corners')
            point=[200,230]
            self.record(row,point,events={8:[('UP',True)],20:[('R',True)],22:[('R',False)],
                                         64:[('UP',False),('DOWN',True)],96:[('DOWN',False)]},
                        extra={'note':'Explicit semantic narrow/concave canopy fixture with ordinary walk/roll/recoil inputs.'})
            self.diagnostic_context=None

    def menu(self):
        feature=FEATURES['sick']
        row=dict(feature,name='sick-canopy-menu-resume',group='menu',action='canopy-menu',frames=128,movie=False)
        self.boot(row)
        self.record(row,feature['under_position'],feature['target'],0,
                    {8:[('START',True)],10:[('START',False)],40:[('START',True)],42:[('START',False)]},
                    {'note':'One focused ordinary menu open/close under generated foliage. Interface frames are explicitly outside the player-visibility scope; every displayed world frame before and after is checked.'})

    def save(self):
        F.Review.save(self)
        path=self.out/'capture.json';r=json.loads(path.read_text())
        r.update(schema=3,method=__doc__.strip(),forest_study_round=3,canopy_focus=True,
                 display_variant=self.variant-10 if self.variant>=11 else 0,recipe=getattr(self,'recipe',None),
                 complete=getattr(self,'finished',False),groups=sorted(self.groups),
                 capture_tool_sha256=getattr(self,'v3_tool_hash',None),
                 inherited_capture_tool_sha256=self.tool_hash,
                 capture_dependency_sha256=getattr(self,'dependencies',{}),
                 capture_command=[sys.executable,str(Path(__file__).resolve()),'--bundle',str(self.frozen),
                                  '--variant',str(self.variant),'--out',str(self.out),'--seed',hex(self.seed)]+
                                  (['--matchbase',self.args.match] if self.args.match else [])+
                                  (['--only',self.args.only] if self.args.only else []),
                 natural_capture_count=sum(x.get('group')!='diagnostic' for x in self.rows),
                 diagnostic_capture_count=sum(x.get('group')=='diagnostic' for x in self.rows),
                 comparison_scope='Strict physical/gameplay comparison with fresh preserved base6 or first new canopy study. Only new profiles enforce never-hidden body; base6 deficits are historical observations.')
        path.write_text(json.dumps(r,indent=2)+'\n')

    def run(self):
        for group in ('landscapes','walk','actions','menu','diagnostic'):
            if group in self.groups:getattr(self,group)()
        self.check('frozen bundle stayed immutable',all(sha((self.frozen/n).read_bytes())==v for n,v in self.frozen_hashes.items()))
        self.check('focused capture tool stayed immutable',sha(Path(__file__).read_bytes())==self.v3_tool_hash)
        self.check('capture dependencies stayed immutable',all(sha((Path(__file__).parent/n).read_bytes())==v for n,v in self.dependencies.items()))
        self.finished=self.groups==GROUPS
        if self.finished:
            self.check('all22 focused actual canopy contexts captured',len(self.rows)==22,len(self.rows))
            self.check('seven focused actual motion clips captured',sum(bool(r.get('movie')) for r in self.rows)==7)
            self.check('six semantic diagnostic contexts separately disclosed',sum(r.get('group')=='diagnostic' for r in self.rows)==6)
        self.save();print('RESULT',sum(r['passed'] for r in self.checks),'/',len(self.checks),'contexts',len(self.rows),flush=True)
        return int(any(not r['passed'] for r in self.checks))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle','--frozen',dest='frozen',required=True)
    p.add_argument('--variant',type=int)
    p.add_argument('--out',required=True)
    p.add_argument('--matchbase','--match',dest='match')
    p.add_argument('--seed',default='0xB4A7')
    p.add_argument('--only',help='Focused pilot groups: landscapes,walk,actions,menu,diagnostic. Partial reports remain incomplete.')
    return Review(p.parse_args()).run()


if __name__=='__main__':raise SystemExit(main())

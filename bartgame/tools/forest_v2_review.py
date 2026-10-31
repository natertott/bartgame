#!/usr/bin/env python3
"""Review the second five forest studies in actual mGBA runs.

Profiles 6..10 share a new generated-room plan. Seed, navigation, inventory,
health, player position and unrelated-enemy clearing are disclosed fixtures.
Natural cases never assign terrain, mystery descriptors, poses or pictures.
Separate `diagnostic` cases deliberately replace the logical room with small
adjacency shapes and invoke the ROM's renderer/collision builder. Those are
actual diagnostic-room framebuffers, not naturally generated landscapes.

The old production/control ROM is reviewed separately with
forest_concept_review.py. It is not the logical-geometry baseline for these
new studies: their larger-log placement is intentionally different.
"""
import argparse
import contextlib
import json
import shutil
import struct
import sys
from collections import deque
from pathlib import Path

import forest_concept_review as F
import probe as P
import bloom_probe as BP
import critical_path as C
import interactive_review as IR
import generation_review as G
import myst_probe as M

GROUPS=(*F.GROUPS, 'depth', 'diagnostic', 'routes')
RECIPES={6:'Black Sap Oak',7:'Violet Strangler',8:'Witchfire Weep',
         9:'Amethyst Canker',10:'Royal Bruise'}
sha=F.sha


def w32(c,address,value):
    P.w16(c,address,value);P.w16(c,address+2,value>>16)


def hash32(a,b):
    mask=0xffffffff
    h=((a*0x9e3779b1)&mask)^((b+0x7f4a7c15)&mask)
    h^=h>>15;h=(h*0x85ebca77)&mask
    h^=h>>13;h=(h*0xc2b2ae3d)&mask
    return (h^(h>>16))&mask


class Review(F.Review):
    def __init__(self,args):
        # The parent initializes all provenance and mGBA bindings. Its old
        # profile check is specialized below; all other checks are retained.
        super().__init__(args)
        self.groups=set(args.only.split(',')) if args.only else set(GROUPS)
        unknown=self.groups-set(GROUPS)
        if unknown:raise ValueError('Unknown review groups: '+', '.join(sorted(unknown)))
        self.v2_tool_hash=sha(Path(__file__).read_bytes())
        self.dependencies={name:sha((Path(__file__).parent/name).read_bytes())
                           for name in ('forest_concept_review.py','probe.py','interactive_review.py',
                                        'critical_path.py','bloom_probe.py','lift_probe.py',
                                        'myst_probe.py','generation_review.py','bloom_suite_gallery.py',
                                        'sewer_concept_audit.py')}
        self.diagnostic_context=None
        self.feature_catalog={}
        self.route_results=[]
        self.diagnostic_contracts=[]
        self.static_addresses={}
        self.hero_info=self.rom.sheet('hero')[0]
        self.obj_reference=self.rom.array('pal_obj')
        faces=self.rom.array('pal_face')
        self.face_palette_references=[faces[i:i+32] for i in range(0,len(faces),32)]
        if self.old:
            self.check('comparison baseline is a new-generation study',self.old.get('forest_study_round')==2 and self.old.get('forest_variant') in RECIPES)
            self.check('comparison baseline binds the same frozen source',self.old.get('source_commit')==self.freeze.get('source_commit'))
            self.check('comparison baseline used the identical capture tool',self.old.get('capture_tool_sha256')==self.v2_tool_hash)

    def static_address(self,name):
        if name not in self.static_addresses:self.static_addresses[name]=BP.static_symbol(name)
        return self.static_addresses[name]

    def check(self,name,condition,detail=None):
        if name=='valid forest study profile':
            name='valid second-round forest study profile';condition=self.variant in RECIPES
        super().check(name,condition,detail)

    def state(self,target=None):
        result=super().state(target)
        recoil=getattr(self,'recording_case',{}).get('name')=='sick-canopy-walkunder' and result['state']==0 and (
            result['z_q16']>0 or getattr(self,'previous_recorded_z',0)>0)
        result['motion_phase']='roll' if result['state']==1 else 'airborne wall recoil' if recoil else 'grounded' if result['z_q16']==0 else 'other airborne'
        result['safe_position']=[P.r16(self.c,P.sym('gPl')+14),P.r16(self.c,P.sym('gPl')+16)]
        px,py=result['position'];room=P.sym('gRoom')
        if 0<=px<P.r8(self.c,room)*16 and 6<=py<P.r8(self.c,room+1)*16:
            mt=P.r16(self.c,room+2+(((py-6)//16)*32+px//16)*2)&65535
            result['standing_type']=P.r8(self.c,P.sym('metatile_type')+mt)
        result['player_priority']=P.r8(self.c,P.sym('gActors')+40)
        result['bg_palette_sha256']=sha(F.read(self.c,P.sym('gPalBg'),384))
        result['obj_palette_sha256']=sha(F.read(self.c,P.sym('gPalObj'),512))
        result['protected_UI_palette_sha256']=sha(F.read(self.c,P.sym('gPalBg')+384,128))
        area=('sewer','forest','myst')[result['area']]
        ts=self.ts_cache[area];phases=self.authored_palettes(area,ts)
        colors=F.read(self.c,P.sym('gPalBg'),ts['palette_count']*32)
        result['authored_BG_palette_phase']=phases.index(colors) if colors in phases else None
        shown=F.read(self.c,0x05000000,ts['palette_count']*32)
        result['displayed_BG_palette_phase']=phases.index(shown) if shown in phases else None
        if getattr(self,'recording_action',None) in ('canopy-depth','root-underpass','blocked-log','ledge-drop'):
            result['depth_oam']=[{k:o[k] for k in ('x','y','tile','pal','priority')}
                                 for o in BP.oam(self.c) if o['tile']<876]
            x,y=result['position'];at=(max(0,y-6)//16)*32+max(0,x)//16
            result['feet_ground']=self.names.get(P.r16(self.c,P.sym('gRoom')+2+at*2)&65535)
            result['feet_collision']=P.r8(self.c,P.sym('gRoom')+4098+max(0,y-6)//8*64+max(0,x)//8)
            if P.r32(self.c,P.sym('gFrame'))&7==1 or result['motion_phase'] in ('roll','airborne wall recoil'):
                result['depth_visibility']=self.depth_visibility()
        if target:
            tx,ty=target;at=ty*32+tx;room=P.sym('gRoom')
            sb=28+((ty*2>>5)<<1)+(tx*2>>5)
            bg=0x06000000+sb*2048+((ty*2&31)*32+(tx*2&31))*2
            result['target_BG_ground_quarters']=[P.r16(self.c,bg+n)&65535 for n in (0,2,64,66)]
            result['target_underlay']=self.names.get(P.r16(self.c,room+8194+at*2)&65535,'none')
        if getattr(self,'recording_action',None)=='chest':
            frame=P.r8(self.c,self.static_address('sChestFrame'))
            tile=P.r16(self.c,self.static_address('sChestTile'))&65535
            info,payload=self.rom.sheet('interactivechest');size=info['frame_tiles']*32
            result['chest_stream']={'frame':frame,'tile':tile,
                'actual_VRAM_matches_authored_frame':bool(tile and frame*size+size<=len(payload) and
                    F.read(self.c,0x06010000+tile*32,size)==payload[frame*size:(frame+1)*size])}
        if 'SHEET_FORESTLANDMARK' in self.defs:
            tiles=[P.r16(self.c,self.static_address('sLandmarkTile')+i*2)&65535 for i in range(4)]
            frames=[P.r8(self.c,self.static_address('sLandmarkFrame')+i) for i in range(4)]
            oam=BP.oam(self.c)
            result['landmark_stream']={'tiles':tiles,'frames':frames,
                'visible_counts':[sum(o['tile']==tile for o in oam) if tile else 0 for tile in tiles]}
        if getattr(self,'recording_case',None):
            calls=self.recording_state_calls;self.recording_state_calls+=1
            if calls==0:self.recording_initial_state=result
            elif self.pending_barrier_frame is None:
                case=self.recording_case;initial=self.recording_initial_state
                barrier=case.get('action') in ('bomb','lamp') or (case.get('action')=='gate' and case.get('gate_kind') in (2,3,4,5))
                cleared=barrier and result['cell']==initial['cell'] and result.get('target_ground')!=initial.get('target_ground')
                cleared &= result.get('target_BG_ground_quarters')==initial.get('target_BG_ground_quarters')
                if cleared and case.get('gate_kind')==5:
                    cleared=result.get('landmark_stream',{}).get('visible_counts',[1]*4)[3]==0
                if cleared:
                    tick=calls-1
                    if self.first_barrier_clear_tick is None:self.first_barrier_clear_tick=tick
                    delay=0 if case.get('gate_kind')==5 else 16
                    if tick>=self.first_barrier_clear_tick+delay:
                        self.pending_barrier_frame={'tick':tick,'state':result,
                            'image':self.c.bg_video.to_pil().convert('RGB').copy()}
            if calls and result['motion_phase'] in ('roll','airborne wall recoil') and 'depth_visibility' in result:
                self.roll_samples.append({'tick':calls-1,'position':result['position'],'phase':result['motion_phase'],
                    'z_q16':result['z_q16'],
                    'timer':P.r8(self.c,P.sym('gActors')+4),'visibility':result['depth_visibility'],
                    'actual_hero_frame_sha256':sha(F.read(self.c,0x06010000,self.hero_info['frame_tiles']*32))})
            self.previous_recorded_z=result['z_q16']
        # Palette phases are visual evidence, not logical comparison fields.
        return result

    def depth_visibility(self):
        """Count genuine opaque hero pixels covered by overhead BG1 ink.

        Both planes are decoded from actual VRAM/OAM. This does not paint a
        preview; it distinguishes upper-body cover from a hidden foot lane.
        """
        c=self.c;hero=next((o for o in BP.oam(c) if o['tile']==0),None)
        if hero is None:return {'body_found':False}
        w,h=self.hero_info['width'],self.hero_info['height']
        if 'gForestV2DisplayedCamera' in self.rom.symbols:
            cam=P.sym('gForestV2DisplayedCamera');camx=P.r16(c,cam);camy=P.r16(c,cam+2)
            camera_source='actual applied BG1 scroll telemetry'
        else:
            camx=P.r16(c,P.sym('gCamX'));camy=P.r16(c,P.sym('gCamY'))
            camera_source='DRAFT fallback shadow camera; moving-camera counts are provisional'
        counts={'upper_body_opaque':0,'upper_body_covered':0,'feet_opaque':0,'feet_covered':0,
                'opaque_colored_pixels':0,'visible_colored_pixels':0}
        overhead=P.sym('forest_v2_overhead');visual=P.sym('gRoomVisualOverlay')
        cache={};visible=set()
        colors=struct.unpack('<16H',F.read(c,0x05000200+hero['pal']*32,32))
        colored=[bool(ink and max(color&31,(color>>5)&31,(color>>10)&31)>=5 and
                      (color&31)+((color>>5)&31)+((color>>10)&31)>=10) for ink,color in enumerate(colors)]
        for iy in range(max(0,h-24),h):
            for ix in range(max(0,w//2-10),min(w,w//2+10)):
                sx=w-1-ix if hero['flip'] else ix
                address=0x06010000+((iy//8)*(w//8)+sx//8)*32+(iy&7)*4+(sx&7)//2
                ink=(P.r8(c,address)>>((sx&1)*4))&15
                if not ink:continue
                # The bottom four native rows are soles/feet. The eight-row
                # lower-body band includes sleeves/leaf skirt and is not a
                # reliable definition of the visible foot lane.
                group='feet' if iy>=h-4 else 'upper_body' if iy<h-8 else None
                if group:counts[group+'_opaque']+=1
                wx=hero['x']+ix+camx;wy=hero['y']+iy+camy
                if not(0<=wx<512 and 0<=wy<384):continue
                cell=(wx//16,wy//16)
                if cell not in cache:
                    mt=P.r16(c,visual+(cell[1]*32+cell[0])*2)&65535
                    cache[cell]=mt!=65535 and bool(P.r8(c,overhead+mt))
                covered=False
                if cache[cell]:
                    tx=wx//8;ty=wy//8;sb=24+(ty>>5)*2+(tx>>5)
                    entry=P.r16(c,0x06000000+sb*2048+((ty&31)*32+(tx&31))*2)&65535
                    x=wx&7;y=wy&7
                    if entry&0x400:x=7-x
                    if entry&0x800:y=7-y
                    bg=(P.r8(c,0x06000000+(entry&1023)*32+y*4+x//2)>>((x&1)*4))&15
                    covered=bool(bg and hero['priority']>1)
                if covered and group:counts[group+'_covered']+=1
                if colored[ink]:
                    counts['opaque_colored_pixels']+=1
                    if not covered:visible.add((ix,iy))
        counts['visible_colored_pixels']=len(visible);largest=0
        while visible:
            todo=[visible.pop()];size=0
            while todo:
                x,y=todo.pop();size+=1
                for p in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                    if p in visible:visible.remove(p);todo.append(p)
            largest=max(largest,size)
        counts['largest_visible_colored_component']=largest
        return {'body_found':True,'body_priority':hero['priority'],
                'applied_camera':[camx,camy],'camera_source':camera_source,**counts}

    def hardware(self):
        result=super().hardware()
        c=self.c;ts=self.ts_cache[result['active_tileset']]
        actual=F.read(c,P.sym('gPalBg'),ts['palette_count']*32)
        phases=self.authored_palettes(result['active_tileset'],ts)
        result['world_palette_bytes_match_ROM']=actual in phases
        result['world_palette_is_authored_phase']=actual in phases
        result['authored_palette_phase']=phases.index(actual) if actual in phases else None
        displayed=F.read(c,0x05000000,ts['palette_count']*32)
        result['actual_hardware_palette_is_authored_phase']=displayed in phases
        result['world_palette_bytes_match_ROM'] &= displayed in phases
        obj=F.read(c,0x05000200,256)
        protected=all(obj[slot*32:(slot+1)*32]==self.obj_reference[slot*32:(slot+1)*32]
                      for slot in (0,1,2,3,4,5,7))
        portrait=obj[6*32:7*32]
        result['selected_OBJ_palette_bytes_match_ROM']=protected and portrait in (
            [self.obj_reference[6*32:7*32]]+self.face_palette_references)
        # Resolved aliases are what the actual renderer writes, while logical
        # room arrays remain stable for movement and gameplay comparisons.
        if 'gRoomVisualGround' in self.rom.symbols:
            room=P.sym('gRoom');w,h=P.r8(c,room),P.r8(c,room+1);valid=True;ids=[]
            for symbol in ('gRoomVisualGround','gRoomVisualOverlay'):
                base=P.sym(symbol)
                for y in range(h):
                    for x in range(w):
                        mt=P.r16(c,base+(y*32+x)*2)&65535
                        ids.append(mt)
                        if mt==65535:continue
                        if mt>=self.defs['METATILE_COUNT']:valid=False;continue
                        entries=struct.unpack_from('<4H',ts['map'],mt*8)
                        valid &= all((q&1023)<ts['tile_count'] and (q>>12)<ts['palette_count'] for q in entries)
            result['resolved_visual_mappings_valid']=bool(valid)
            result['native_room_mappings'] &= bool(valid)
            result['resolved_visual_ids_sha256']=sha(struct.pack('<%dH'%len(ids),*ids))
        return result

    def authored_palettes(self,area,ts):
        """Read generated four-phase palette payloads from the frozen ROM.

        The engine's pulse metadata is explicitly decoded here after its
        contract is frozen. Until a profile declares pulse arrays, only the
        unchanged native base palette is accepted; no broad colour tolerance.
        """
        result=[ts['palettes']]
        # Per-tileset slot bytes (255 absent), followed by shared four-phase
        # native bank payloads. One phase applies to every active pulse bank.
        if 'forest_v2_pulse_slots' in self.rom.symbols:
            index=self.defs['TS_'+area.upper()]
            count=self.defs['FOREST_V2_PULSE_COUNT']
            slots=self.rom.read(self.rom.symbols['forest_v2_pulse_slots']+index*count,count)
            result=[]
            for phase in range(4):
                colors=bytearray(ts['palettes'])
                for i,slot in enumerate(slots):
                    if slot==255:continue
                    payload=self.rom.symbols['forest_v2_pulse_colors']+(i*4+phase)*32
                    colors[slot*32:(slot+1)*32]=self.rom.read(payload,32)
                result.append(bytes(colors))
        return result

    def record(self,row,point,target=None,facing=0,events=None,extra=None):
        row=dict(row)
        point=list(point)
        target=list(target) if target is not None else None
        extra=dict(extra or {})
        self.recording_action=row.get('action')
        self.recording_case=row;self.recording_state_calls=0;self.pending_barrier_frame=None
        self.first_barrier_clear_tick=None
        self.roll_samples=[]
        self.previous_recorded_z=0
        if self.diagnostic_context:
            extra['fixture_kind']='diagnostic logical-room adjacency fixture'
            extra['diagnostic_room']=self.diagnostic_context
        else:extra['fixture_kind']='natural generated room; navigation/inventory/player fixtures only'
        # The historical strict comparator excludes only OAM. Keep the new
        # visual palette/priority observations outside that logical state.
        before=len(self.rows)
        old=self.old_rows.pop(row['name'],None)
        super().record(row,point,target,facing,events,extra)
        if old:
            self.old_rows[row['name']]=old
            current=self.rows[-1]
            fields=('seed','cell','position','target','facing','physical_contract',
                    'final_physical_contract','maze_sha256','initial_progress_sha256',
                    'final_progress_sha256','initial_rng','final_rng','inputs')
            match={field:old.get(field)==current.get(field) for field in fields}
            visual={'oam','player_priority','bg_palette_sha256','obj_palette_sha256',
                    'protected_UI_palette_sha256','authored_BG_palette_phase','depth_oam',
                    'displayed_BG_palette_phase','target_BG_ground_quarters','chest_stream',
                    'landmark_stream','depth_visibility'}
            for field in ('initial','final'):
                match[field+'_logical_state']={k:v for k,v in old[field].items() if k not in visual}=={k:v for k,v in current[field].items() if k not in visual}
            match['mechanic_transition_order']=[t['state'] for t in old['mechanic_transitions']]==[t['state'] for t in current['mechanic_transitions']]
            current['matched_case']=match
            current['transition_tick_observation']={'baseline':[t['tick'] for t in old['mechanic_transitions']],
                'candidate':[t['tick'] for t in current['mechanic_transitions']],
                'note':'Native graphics loads may finish on different VBlanks. Ordered states and logical endpoints are strict.'}
            self.check(row['name']+' matches first new study physical/gameplay contract',all(match.values()),match)
        assert len(self.rows)==before+1
        self.inspect_case(self.rows[-1]);self.extra_keyframes(self.rows[-1]);self.save()

    def extra_keyframes(self,r):
        if self.roll_samples:
            r['roll_visibility_samples']=self.roll_samples
            self.check(r['name']+' every tested roll/recoil frame retains a connected colored body',
                       all(s['visibility']['visible_colored_pixels']>=max(12,s['visibility']['opaque_colored_pixels']//4) and
                           s['visibility']['largest_visible_colored_component']>=8 for s in self.roll_samples),self.roll_samples)
            recoil=[s for s in self.roll_samples if s['phase']=='airborne wall recoil']
            if recoil:
                foreground=[i for i,s in enumerate(recoil) if s['visibility']['body_priority']==1]
                r['wall_recoil_priority_observation']={'frames':[{'tick':s['tick'],'priority':s['visibility']['body_priority']} for s in recoil],
                    'note':'Brief wall recoil is coarsely sorted in front of a low leaf fringe. This is a readability exception; z, physics and timers remain real, and ground shadow stays behind.'}
                self.check(r['name']+' wall-recoil foreground interval has no one-frame priority flicker',
                           len(foreground)>=4 and foreground==list(range(min(foreground),max(foreground)+1)),
                           r['wall_recoil_priority_observation'])
        if r.get('action')=='canopy-depth':
            observations=[{'tick':t['tick'],'position':t['position'],'state':t['state'],
                           'phase':t['motion_phase'],'z_q16':t['z_q16'],
                           'visibility':t['depth_visibility']} for t in r['trace'] if 'depth_visibility' in t]
            nearest=min(t['position'][1] for t in observations)
            r['closest_canopy_collision_limit']={'minimum_feet_y':nearest,
                'observations':[t for t in observations if t['position'][1]==nearest],
                'note':'The direction input reaches the real collision limit; recovery/standing observations are retained even when the roll has already ended.'}
        if self.pending_barrier_frame:
            selected=self.pending_barrier_frame;tick=selected['tick']
            relative=f'{r["name"]}/frame-{tick:03}.png';selected['image'].save(self.out/relative)
            if relative not in r['native_frames']:r['native_frames'].append(relative)
            r['cleared_barrier_keyframe']={'tick':tick,'path':relative,
                'sha256':sha((self.out/relative).read_bytes()),'cell':selected['state']['cell'],
                'target_ground':selected['state'].get('target_ground'),
                'target_BG_ground_quarters':selected['state'].get('target_BG_ground_quarters'),
                'camera':selected['state']['camera'],
                'note':'Actual same-room frame after ordinary clearing; exact original displayed substrate retained.'}
        if not r.get('movie'):return
        def frame(tick):
            relative=f'{r["name"]}/frame-{tick:03}.png'
            source=self.out/r['all_frames']/f'frame-{tick:03}.png'
            destination=self.out/relative
            if not destination.exists():shutil.copy2(source,destination)
            if relative not in r['native_frames']:r['native_frames'].append(relative)
            return relative
        if r.get('action') in ('canopy-depth','root-underpass'):
            samples=[t for t in r['trace'] if 'depth_visibility' in t]
            covered=[t for t in samples if t['motion_phase']=='grounded' and 0<t['depth_visibility'].get('upper_body_covered',0)<t['depth_visibility'].get('upper_body_opaque',0)
                     and not t['depth_visibility'].get('feet_covered',0)]
            keys=[]
            if covered:
                under=max(covered,key=lambda t:t['depth_visibility']['upper_body_covered'])
                before=next((t for t in samples if t['tick']<under['tick'] and not t['depth_visibility'].get('upper_body_covered',0)),None)
                after=next((t for t in reversed(samples) if t['tick']>under['tick'] and not t['depth_visibility'].get('upper_body_covered',0)),None)
                for label,sample in (('Before',before),('Under',under),('Emerged',after)):
                    if sample:
                        relative=frame(sample['tick']);keys.append({'label':label,'tick':sample['tick'],'path':relative,
                            'sha256':sha((self.out/relative).read_bytes()),'visibility':sample['depth_visibility']})
            r['phase_keyframes']=keys
            self.check(r['name']+' before/under/emerged native evidence selected',len(keys)==3,keys)
        if r['name']=='deep-blight':
            samples={}
            for t in r['trace']:
                phase=t.get('displayed_BG_palette_phase')
                if phase is not None:samples.setdefault(phase,t)
            keys=[]
            for phase,t in sorted(samples.items()):
                relative=frame(t['tick']);keys.append({'phase':phase,'tick':t['tick'],'path':relative,
                    'sha256':sha((self.out/relative).read_bytes())})
            r['pulse_phase_keyframes']=keys
            slots=self.rom.read(self.rom.symbols['forest_v2_pulse_slots']+self.defs['TS_FOREST']*self.defs['FOREST_V2_PULSE_COUNT'],self.defs['FOREST_V2_PULSE_COUNT'])
            r['pulse_contract']={'actual_displayed_phases':sorted(samples),'authored_BG_banks':[
                {'slot':slot,'rgb555_phases':[list(self.rom.unpack('<16H',self.rom.symbols['forest_v2_pulse_colors']+(index*4+phase)*32)) for phase in range(4)]}
                for index,slot in enumerate(slots) if slot!=255],
                'selected_OBJ_palette_bytes_match_ROM':all(s['selected_OBJ_palette_bytes_match_ROM'] for s in r['hardware_samples']),
                'protected_UI_palette_sha256':r['initial']['protected_UI_palette_sha256']}
            self.check('deep-blight four exact displayed glow phase frames selected',set(samples)=={0,1,2,3},keys)

    def inspect_case(self,r):
        action=r.get('action');name=r['name'];trace=r['trace']
        self.check(name+' actual selected OBJ palette bytes remain native ROM colors',
                   all(s['selected_OBJ_palette_bytes_match_ROM'] for s in r['hardware_samples']))
        if not action and r.get('group')=='landscapes':
            self.check(name+' pulse leaves selected OBJ palettes unchanged',
                       len({t['obj_palette_sha256'] for t in trace})==1)
            self.check(name+' pulse leaves protected UI palettes unchanged',
                       len({t['protected_UI_palette_sha256'] for t in trace})==1)
        if name in ('mixed-forest','deep-blight','heart-glade'):
            self.check(name+' all four authored BG glow phases run',
                       {t['authored_BG_palette_phase'] for t in trace}=={0,1,2,3} and
                       {t['displayed_BG_palette_phase'] for t in trace}=={0,1,2,3})
        if action in ('bomb','lamp') or (action=='gate' and r.get('gate_kind') in (2,3,4,5)):
            initial=r['initial'];blocked=initial.get('target_ground')
            cleared=next((t for t in trace if t['cell']==initial['cell'] and t.get('target_ground')!=blocked),None)
            self.check(name+' cleared barrier exposes exact original displayed substrate',
                       cleared is not None and initial.get('target_BG_ground_quarters')==cleared.get('target_BG_ground_quarters'),
                       {'before':initial.get('target_BG_ground_quarters'),
                        'after':cleared.get('target_BG_ground_quarters') if cleared else None})
        if action=='gate' and r.get('gate_kind')==5:
            self.check(name+' exactly one visible large keyhole for paired gate',
                       r['initial']['landmark_stream']['visible_counts'][3]==1,r['initial']['landmark_stream'])
            self.check(name+' large keyhole disappears after genuine key use',
                       any(t['cell']==r['initial']['cell'] and t.get('target_ground')!='door_locked' and
                           t['landmark_stream']['visible_counts'][3]==0 for t in trace))
        if r.get('wooden_variant')=='B':
            self.check(name+' actual wooden B closed frame6 is streamed',
                       r['initial']['chest_stream']['frame']==self.defs['F_INTERACTIVECHEST_WOODEN_B_CLOSED'] and
                       r['initial']['chest_stream']['actual_VRAM_matches_authored_frame'],r['initial']['chest_stream'])
            self.check(name+' actual wooden B open frame7 is streamed',
                       r['final']['chest_stream']['frame']==self.defs['F_INTERACTIVECHEST_WOODEN_B_OPEN'] and
                       r['final']['chest_stream']['actual_VRAM_matches_authored_frame'],r['final']['chest_stream'])
        if action=='blocked-log':
            delta=[r['final']['position'][i]-r['initial']['position'][i] for i in (0,1)]
            self.check(name+' genuine solid trunk blocks ordinary walking',max(map(abs,delta))<24,delta)
        elif action=='ledge-drop':
            self.check(name+' genuine ledge starts jump without cape input',any(t['state']==5 and t['z_q16']>0 for t in trace),trace)
            self.check(name+' genuine ledge lands normally',r['final']['state']==0,r['final'])
            self.check(name+' actual drop changes standing position',r['initial']['position']!=r['final']['position'])
        elif action=='diagnostic-drown':
            self.check(name+' ordinary walking enters logical water and actually drowns',any(t['state']==4 for t in trace))
            self.check(name+' drowning returns to actual last safe standing ground',
                       r['final']['state']==0 and r['final']['position']==r['final']['safe_position'] and
                       r['final'].get('standing_type')==self.defs['TT_FLOOR'],r['final'])
            self.check(name+' real water hazard leaves fixture geometry intact',r['physical_contract']==r['final_physical_contract'])
        elif action in ('canopy-depth','root-underpass'):
            start=r['initial']['position']
            self.check(name+' ordinary walking passes through open depth surface',
                       max(sum(abs(t['position'][i]-start[i]) for i in (0,1)) for t in trace)>10)
            self.check(name+' depth movement remains on ground',all(t['state'] not in (4,5) for t in trace))
            self.check(name+' visible feet remain on real non-solid ground',all(not t.get('feet_collision') for t in trace),trace)
            visibility=[t['depth_visibility'] for t in trace if 'depth_visibility' in t]
            self.check(name+' real overhead pixels partially cover upper body',
                       any(v.get('upper_body_covered',0)>0 and v.get('upper_body_covered',0)<v.get('upper_body_opaque',0) for v in visibility),visibility)
            if action=='canopy-depth':
                self.check(name+' real sole lane stays fully visible under canopy fringe',
                           all(t['depth_visibility'].get('feet_covered',0)==0 for t in trace if t['motion_phase']=='grounded' and 'depth_visibility' in t),visibility)
            else:
                # A genuine raised span passes in front of the traveller as
                # he crosses beneath it; a deeper roof may briefly cover him.
                # The selected partial-cover Under proof below must retain
                # fully visible soles, together with clear entry/emergence.
                self.check(name+' under-span partial cover includes a clear sole lane',
                           any(v.get('upper_body_covered',0)>0 and v.get('feet_opaque',0)>0 and
                               v.get('feet_covered',0)==0 for v in visibility),visibility)
            self.check(name+' body shown before cover and after emerging',
                       bool(visibility) and visibility[0].get('upper_body_covered',0)==0 and
                       visibility[-1].get('upper_body_covered',0)==0,visibility)
        if r.get('group')=='diagnostic':
            self.check(name+' diagnostic fixture disclosed',r.get('fixture_kind','').startswith('diagnostic'))

    def landscape_plan(self):
        plan=super().landscape_plan()
        if self.old:return plan
        # The primary seed's only stage3 room is the Heart. A separate real
        # stage3 ordinary room makes the diseased terrain review independent
        # of the arena dressing. Its actual geometry is never transplanted.
        for row in plan:
            if row['name']!='deep-blight':continue
            choices=[]
            for seed in (6,7,9,11):
                self.boot({'name':'find-deep','seed':hex(seed),'cell':None})
                for cell,d in enumerate(self.world['cells']):
                    if d['stage']>=3 and d['role']!=2:
                        choices.append((seed,cell))
                if choices:break
            for seed,cell in choices:
                self.boot({'name':'find-deep','seed':hex(seed),'cell':cell})
                point=self.still_point(F.FEATURES['deep-blight'])
                if point is not None:
                    row.update(seed=hex(seed),cell=cell,position=point,
                               note='Ordinary naturally generated deep room, separate from Heart arena.')
                    break
        return plan

    def scan_feature(self,name,prefixes,stage=None,all_seeds=False):
        old=self.old_plan.get('features',{}).get(name)
        if old:return old
        choices=[]
        for seed in (self.seed,6,7,9,11):
            self.boot({'name':'search-'+name,'seed':hex(seed),'cell':None})
            for cell,d in enumerate(self.world['cells']):
                if stage is not None and not stage(d['stage']):continue
                self.warp(cell)
                for (x,y),ns in self.grid()[2].items():
                    if any(n.startswith(prefixes) for n in ns[:2]):
                        choices.append({'seed':hex(seed),'cell':cell,'target':[x,y],
                                        'logical_names':list(ns[:2]),'stage':d['stage']})
            if choices and not all_seeds:break
        self.feature_catalog[name]=choices
        return choices[0] if choices else None

    def candidate_motion(self,name,prefixes,action,stage=None):
        """Find actual safe standing approaches, keeping renderer art in place."""
        saved=self.old_plan.get('features',{}).get(name)
        if saved:return saved
        if action=='canopy-depth':return self.canopy_approach(name,stage)
        self.scan_feature(name,prefixes,stage,all_seeds=action=='root-underpass')
        for feature in self.feature_catalog.get(name,[]):
            self.boot({'name':'choose-'+name,**feature})
            tx,ty=feature['target']
            if action=='ledge-drop':
                approaches=[([tx*16+8,ty*16-4],2,'DOWN')]
            elif action=='blocked-log':
                approaches=[([tx*16+8,ty*16+40],0,'UP'),([tx*16-24,ty*16+12],1,'RIGHT')]
            elif action=='root-underpass':
                approaches=[([tx*16+dx,ty*16+44],0,'UP') for dx in (24,8,16)]
            else:
                approaches=[([tx*16+8,ty*16+44],0,'UP'),([tx*16-24,ty*16+12],1,'RIGHT')]
            for point,face,key in approaches:
                route_clear=action!='root-underpass' or all(self.safe(point[0],ty*16+dy) for dy in (-20,-4,12,28,44))
                if self.safe(*point) and route_clear:
                    if action=='root-underpass':
                        self.settle(point,face);before=self.depth_visibility()
                        self.settle([point[0],ty*16-16],face);after=self.depth_visibility()
                        if any(v.get('upper_body_covered',0) or v.get('feet_covered',0) for v in (before,after)):continue
                    return {**feature,'position':point,'facing':face,'key':key}
        return None

    def canopy_approach(self,name,stage):
        """Select a real open fringe, not a collision-solid canopy trunk."""
        overhead=self.rom.symbols.get('forest_v2_overhead')
        if overhead is None:return None
        for seed in (self.seed,6,7,9,11):
            self.boot({'name':'search-'+name,'seed':hex(seed),'cell':None})
            for cell,desc in enumerate(self.world['cells']):
                if not stage(desc['stage']):continue
                self.warp(cell);w,h,g=self.grid();base=P.sym('gRoomVisualOverlay')
                for y in range(3,h-4):
                    for x in range(3,w-3):
                        alias=P.r16(self.c,base+(y*32+x)*2)&65535
                        if alias==65535 or not P.r8(self.c,overhead+alias):continue
                        # North-only fringe provides a clean before/under/
                        # emerged comparison. A side wall's projecting leaf
                        # strip can remain beside the entire walk.
                        if not self.names.get(alias,'').startswith('f2_fringe_') or not self.names[alias].endswith('_1'):continue
                        point=[x*16+8,y*16+38]
                        if self.safe(*point) and all(self.safe(x*16+8,y*16+dy) for dy in (14,22,30,46,54)):
                            return {'seed':hex(seed),'cell':cell,'target':[x,y],
                                    'logical_names':list(g[x,y][:2]),'stage':desc['stage'],
                                    'position':point,'facing':0,'key':'UP'}
        return None

    def depth(self):
        self.plan['features']={}
        requests=[
            ('living-canopy-walkunder',('canopy','forest_canopy'), 'canopy-depth',lambda s:s<2),
            ('sick-canopy-walkunder',('canopy_blight','forest_blight_canopy'), 'canopy-depth',lambda s:s>=3),
            ('large-log-collision',('hlog_0',), 'blocked-log',None),
            ('raised-ledge-drop',('ledge_s',), 'ledge-drop',None),
            ('root-arch-underpass',('f2_arch_0',), 'root-underpass',None),
        ]
        for name,prefixes,action,stage in requests:
            feature=self.candidate_motion(name,prefixes,action,stage)
            if feature is None:
                self.missing.append({'name':name,'reason':'No safe naturally generated feature approach found.'})
                self.check(name+' natural feature exists',False);continue
            self.plan['features'][name]=feature
            row=dict(feature,name=name,group='depth',action=action,movie=True,frames=128)
            self.boot(row)
            events={8:[(feature['key'],True)],64:[(feature['key'],False)]}
            pl=P.sym('gPl');P.w8(self.c,pl+8,127)
            if name=='living-canopy-walkunder':
                C.equip_b(self.c,C.EQ_SWORD)
                events={8:[('UP',True)],24:[('UP',False),('A',True)],26:[('A',False)],
                        56:[('DOWN',True)],80:[('DOWN',False)]}
            elif name=='sick-canopy-walkunder':
                events={8:[('UP',True)],20:[('R',True)],22:[('R',False)],
                        64:[('UP',False),('DOWN',True)],96:[('DOWN',False)]}
            elif name=='root-arch-underpass':
                C.equip_b(self.c,C.EQ_LAMP)
                events={8:[('UP',True)],24:[('UP',False),('A',True)],26:[('A',False)],
                        56:[('UP',True)],88:[('UP',False)]}
            self.record(row,feature['position'],feature['target'],feature['facing'],events,
                {'note':'Actual generated feature and ordinary direction input. No terrain or animation pose assignment.'})
        # Additional static landmarks use naturally generated placement.
        for name,prefixes,role,spot,flag in (('shrine-plinth-depth',('statue',),9,42,52),
                                            ('relic-plinth-depth',('mossy_stone',),8,29,50)):
            feature=self.old_plan.get('features',{}).get(name)
            if feature is None:
                for seed in (self.seed,0xDEADBEEF,6,7,9,11):
                    self.boot({'name':'find-'+name,'seed':hex(seed),'cell':None})
                    for cell,desc in enumerate(self.world['cells']):
                        if desc['role']!=role:continue
                        self.warp(cell);s=P.sym('gSpots')
                        if P.r8(self.c,s+flag):
                            feature={'seed':hex(seed),'cell':cell,
                                     'target':[P.r8(self.c,s+spot),P.r8(self.c,s+spot+1)]};break
                    if feature is not None:break
            if feature is None:
                self.missing.append({'name':name,'reason':'No generated landmark.'});continue
            self.plan['features'][name]=feature;row=dict(feature,name=name,group='depth',frames=32)
            self.boot(row);tx,ty=feature['target'];point=[tx*16+8,ty*16+48]
            if not self.safe(*point):point=self.still_point(prefixes)
            self.record(row,point,feature['target'],extra={'note':'Tall actual landmark on natural generated ground.'})
        self.wood_chest_b()

    def wood_chest_b(self):
        name='forest-wood-B-chest';feature=self.old_plan.get('features',{}).get(name)
        if feature is None:
            for candidate in IR.plan():
                if 'wood-chest' in candidate['name'] and hash32(int(candidate['seed'],0),candidate['cell'])&1:
                    feature=dict(candidate);break
        if feature is None:
            self.missing.append({'name':name,'reason':'No natural wooden B chest candidate.'});return
        self.plan['features'][name]=feature
        row=dict(feature,name=name,group='depth',action='chest',frames=112,movie=False)
        self.boot(row);chosen=self.target(row)
        if chosen is None:
            self.missing.append({'name':name,'reason':'Natural wooden B chest missing.'});return
        target,point,face,extra=chosen
        point=[target[0]*16+8,target[1]*16+46]
        if not self.safe(*point):point=[target[0]*16+8,target[1]*16+30]
        self.record(row,point,target,face,{8:[('UP',True)],36:[('UP',False)]},
                    {**extra,'wooden_variant':'B','note':'Natural wood-tier chest selected by stable seed/cell hash. Actual closed/open action; no chest tier, reward or RNG assignment.'})

    def invoke_void(self,name):
        """Invoke an existing idempotent void ROM function by real IRQ.

        Used only for explicitly labelled room fixtures. The original hook
        is restored before ordinary scene capture; game/render code is never
        patched and no video pixels or animation frames are assigned.
        """
        address=P.sym('gVBlankHook');original=P.r32(self.c,address)
        clock=P.r32(self.c,P.sym('gFrame'))
        try:
            w32(self.c,address,P.sym(name)|1)
            # mGBA may return exactly before the pending VBlank IRQ. Two
            # observed IRQ entries prove at least one complete callback has
            # run even if the first callback spans several video frames.
            for _ in range(180):
                P.run(self.c,1)
                if ((P.r32(self.c,P.sym('gFrame'))-clock)&0xffffffff)>=2:break
            else:raise RuntimeError('ROM callback did not receive actual VBlank IRQs: '+name)
        finally:w32(self.c,address,original)
        updates=P.r32(self.c,P.sym('gGame')+8)
        # A video-frame boundary may fall inside a long IRQ callback. Wait
        # for three real game updates, so even an update immediately before
        # that IRQ cannot be mistaken for the callback having returned.
        for _ in range(180):
            if ((P.r32(self.c,P.sym('gGame')+8)-updates)&0xffffffff)>=3:break
            P.run(self.c,1)
        else:raise RuntimeError('ROM callback failed to return to actual game updates: '+name)

    def diagnostic_fixture(self,kind,shape):
        c=self.c;room=P.sym('gRoom');floor=self.defs['MT_MOSS0'];none=65535
        for y in range(24):
            for x in range(32):
                for offset,mt in ((2,floor),(2050,none),(8194,floor)):
                    P.w16(c,room+offset+(y*32+x)*2,mt)
        # Fresh boot per fixture avoids streaming/ambient allocation leaks.
        for i in range(1,96):P.w8(c,P.sym('gActors')+i*64,0)
        for i in range(58):P.w8(c,P.sym('gSpots')+i,0)
        names={'water':('WATER','WATER0'),
               'living-canopy':('CANOPY','CANOPY0','FOREST_CANOPY'),
               'sick-canopy':('CANOPY_BLIGHT','CANOPY_BLIGHT0','FOREST_BLIGHT_CANOPY')}
        mt=next((self.defs['MT_'+n] for n in names[kind] if 'MT_'+n in self.defs),None)
        if mt is None:
            prefix={'water':'water','living-canopy':'canopy','sick-canopy':'canopy_blight'}[kind]
            mt=next((n for n,label in self.names.items() if label.startswith(prefix)),None)
        if mt is None:raise RuntimeError('No diagnostic semantic tile for '+kind)
        if shape=='isolated-sizes':
            if kind=='water':
                cells={(12,9),(8,12),(13,12)}|{(x,y) for y in range(8,10) for x in range(6,8)}|{(x,y) for y in range(7,10) for x in range(16,19)}
                point=[200,178]
            else:
                cells={(6,8)}|{(x,y) for y in range(7,9) for x in range(10,12)}|{(x,y) for y in range(6,9) for x in range(15,18)}
                point=[200,180]
        else:
            cells={(x,7) for x in range(6,18)}|{(8,y) for y in range(8,12)}|{(x,y) for y in range(9,12) for x in range(11,16) if not(x>=13 and y<=10)}
            point=[200,196]
        swatches=[]
        if kind=='water' and shape=='isolated-sizes':
            for label,(tx,ty),substrate in (('healthy',(12,9),floor),
                    ('sick',(8,12),self.defs['MT_FOREST_ROT0']),
                    ('dirt',(13,12),self.defs['MT_PATH'])):
                for yy in range(ty-1,ty+2):
                    for xx in range(tx-1,tx+2):
                        for offset in (2,8194):P.w16(c,room+offset+(yy*32+xx)*2,substrate)
                swatches.append({'floor':label,'cell':[tx,ty],'substrate_id':substrate,
                                 'substrate':self.names[substrate]})
        assigned=[]
        for x,y in sorted(cells):
            picture=mt
            if kind=='water':
                sides=sum((1<<bit) for bit,(dx,dy) in enumerate(((0,-1),(1,0),(0,1),(-1,0))) if (x+dx,y+dy) not in cells)
                corners=sum((1<<bit) for bit,(dx,dy) in enumerate(((-1,-1),(1,-1),(1,1),(-1,1))) if (x+dx,y+dy) not in cells)
                picture=self.defs['MT_WATER']+sides if sides else self.defs['MT_WATER_C1']+corners-1 if corners else self.defs['MT_WATER']
            P.w16(c,room+2+(y*32+x)*2,picture)
            assigned.append({'cell':[x,y],'semantic_tile':self.names[picture]})
        self.invoke_void('room_render');self.invoke_void('ambient_room_reset')
        self.diagnostic_context={'kind':kind,'shape':shape,'semantic_tile':self.names[mt],
            'cells':[list(p) for p in sorted(cells)],'assigned_semantic_tiles':assigned,'floor':'moss0',
            'substrate_swatches':swatches,
            'method':'Logical gRoom fixture; existing idempotent room_render and ambient_room_reset invoked through a temporary restored VBlank hook. No framebuffer/VRAM painting.'}
        return point

    def diagnostic(self):
        for kind in ('water','living-canopy','sick-canopy'):
            for shape in ('isolated-sizes','narrow-inner-corners'):
                row={'name':'diagnostic-'+kind+'-'+shape,'group':'diagnostic','seed':hex(self.seed),
                     'cell':None,'frames':32}
                self.boot(row);P.enter_forest(self.c);row['cell']=C.cell(self.c)
                point=self.diagnostic_fixture(kind,shape)
                events={};extra={'note':'Explicit diagnostic room fixture, not a naturally generated room. Same frozen ROM art, adjacency renderer and collision builder.'}
                if kind=='water' and shape=='isolated-sizes':
                    row.update(action='diagnostic-drown',frames=112)
                    events={8:[('UP',True)],32:[('UP',False)]};extra['middle_frame']=34
                    self.water_substrate_checks()
                self.record(row,point,facing=0,events=events,extra=extra)
                self.diagnostic_context=None
        self.adjacency_contract_probe()

    def water_substrate_checks(self):
        ts=self.ts_cache['forest'];c=self.c
        for swatch in self.diagnostic_context['substrate_swatches']:
            x,y=swatch['cell'];at=y*32+x
            actual=P.r16(c,P.sym('gRoomVisualGround')+at*2)&65535
            overlay=P.r16(c,P.sym('gRoomVisualOverlay')+at*2)&65535
            addr=0x06000000+28*2048+((y*2)*32+x*2)*2
            quarters=[P.r16(c,addr+n)&65535 for n in (0,2,64,66)]
            expected=list(struct.unpack_from('<4H',ts['map'],swatch['substrate_id']*8))
            overhead=False if overlay==65535 else bool(P.r8(c,P.sym('forest_v2_overhead')+overlay))
            result={'expected_floor':swatch['substrate'],'actual_BG2_visual_id':actual,
                    'actual_BG1_visual_id':overlay,'actual_floor_quarters':quarters,
                    'expected_floor_quarters':expected,'overlay_is_overhead':overhead,
                    'passed':actual==swatch['substrate_id'] and quarters==expected and overlay!=65535 and not overhead}
            swatch['actual_substrate_proof']=result
            self.check('diagnostic isolated water exact '+swatch['floor']+' substrate/priority contract',result['passed'],result)

    def adjacency_contract_probe(self):
        """Exercise every valid renderer mask without hundreds of PNGs.

        This is explicitly a diagnostic logical-room fixture. Expected
        cardinal/corner relationships are constructed independently of the
        renderer. Actual resolved IDs, hardware BG entries and unchanged
        semantic collision are checked after the ROM renders each shape.
        """
        self.boot({'name':'adjacency-contract-probe','seed':hex(self.seed),'cell':None})
        P.enter_forest(self.c)
        c=self.c;room=P.sym('gRoom');floor=self.defs['MT_MOSS0']
        for i in range(1,96):P.w8(c,P.sym('gActors')+i*64,0)
        for i in range(58):P.w8(c,P.sym('gSpots')+i,0)
        for y in range(24):
            for x in range(32):
                for offset,mt in ((2,floor),(2050,65535),(8194,floor)):
                    P.w16(c,room+offset+(y*32+x)*2,mt)
        ts=self.ts_cache['forest'];cx=8;cy=8
        kinds=F.read(c,P.sym('forest_v2_canopy_kind'),self.defs['METATILE_COUNT'])
        waterkinds=F.read(c,P.sym('forest_v2_water_kind'),self.defs['METATILE_COUNT'])
        canopy=[next(i for i,k in enumerate(kinds) if k==kind) for kind in (1,2)]
        cards=((0,-1),(1,0),(0,1),(-1,0))
        diagonals=((-1,-1),(1,-1),(1,1),(-1,1))
        def put(dx,dy,mt):P.w16(c,room+2+((cy+dy)*32+cx+dx)*2,mt)
        def clearpatch():
            for dy in range(-2,3):
                for dx in range(-2,3):put(dx,dy,floor)
        def observe(family,kind,mask,corner,expected):
            self.invoke_void('room_render')
            composited=family in ('canopy','fringe','isolated-water') or (family=='water' and mask==15)
            symbol='gRoomVisualOverlay' if composited else 'gRoomVisualGround'
            actual=P.r16(c,P.sym(symbol)+(cy*32+cx)*2)&65535
            sb=24 if composited else 28
            at=0x06000000+sb*2048+((cy*2)*32+cx*2)*2
            hardware=[P.r16(c,at+offset)&65535 for offset in (0,2,64,66)]
            expected_map=[0]*4 if expected==65535 else list(struct.unpack_from('<4H',ts['map'],expected*8))
            logical=P.r16(c,room+2+(cy*32+cx)*2)&65535
            coll=P.r8(c,P.sym('metatile_coll')+logical)
            collision=[P.r8(c,room+4098+(cy*2+dy)*64+cx*2+dx) for dy,dx in ((0,0),(0,1),(1,0),(1,1))]
            expected_collision=[(coll>>b)&1 for b in (3,2,1,0)]
            ok=actual==expected and hardware==expected_map and collision==expected_collision
            result={'family':family,'kind':kind,'cardinal_mask':mask,'inner_corner_mask':corner,
                    'quadrant':(cx&1)|((cy&1)<<1),
                    'expected_visual_id':expected,'actual_visual_id':actual,
                    'hardware_map_matches_ROM':hardware==expected_map,
                    'semantic_collision_preserved':collision==expected_collision,'passed':ok}
            self.diagnostic_contracts.append(result)
            self.check(f'diagnostic {family}{kind} q{result["quadrant"]} mask{mask:x} corner{corner:x} actual renderer/collision',ok,result)
        def combinations():
            for mask in range(16):
                eligible=0
                for bit,(a,b) in enumerate(((0,3),(0,1),(2,1),(2,3))):
                    if not(mask&(1<<a)) and not(mask&(1<<b)):eligible|=1<<bit
                for corner in range(16):
                    if not corner&~eligible:yield mask,corner
        for kind,mt in enumerate(canopy,1):
            for quadrant in range(4):
                cx,cy=8+(quadrant&1),8+(quadrant>>1)
                for mask,corner in combinations():
                    clearpatch();put(0,0,mt)
                    for bit,(dx,dy) in enumerate(cards):
                        if not mask&(1<<bit):put(dx,dy,mt)
                    for bit,(dx,dy) in enumerate(diagonals):
                        if not corner&(1<<bit):put(dx,dy,mt)
                    offset=((((kind-1)*4+quadrant)*16+mask)*16+corner)*2
                    expected=P.r16(c,P.sym('forest_v2_canopy_alias')+offset)&65535
                    observe('canopy',kind,mask,corner,expected)
            cx=cy=8
            for mask in range(16):
                clearpatch()
                for bit,(dx,dy) in enumerate(cards):
                    if mask&(1<<bit):put(dx,dy,mt)
                expected=P.r16(c,P.sym('forest_v2_fringe_alias')+((kind-1)*16+mask)*2)&65535
                observe('fringe',kind,mask,0,expected)
        cx=cy=8;water=next(i for i,k in enumerate(waterkinds) if k==1)
        for mask,corner in combinations():
            clearpatch();put(0,0,water)
            for bit,(dx,dy) in enumerate(cards):
                if not mask&(1<<bit):put(dx,dy,water)
            for bit,(dx,dy) in enumerate(diagonals):
                if not corner&(1<<bit):put(dx,dy,water)
            expected=P.r16(c,P.sym('forest_v2_water_alias')+(mask*16+corner)*2)&65535
            observe('water',1,mask,corner,expected)
        for kind in (2,3):
            clearpatch();mt=next(i for i,k in enumerate(waterkinds) if k==kind);put(0,0,mt)
            expected=P.r16(c,P.sym('forest_v2_water_isolated')+(kind-2)*2)&65535
            observe('isolated-water',kind,15,0,expected)
        self.save()

    def routes(self):
        for seed in (self.seed,6,7,9,11):
            self.boot({'name':'route-'+hex(seed),'seed':hex(seed),'cell':None})
            world=C.world(self.c);pacing=G.pacing(world)
            self.check(hex(seed)+' all four gated progression legs reachable',len(pacing['legs'])==4)
            self.check(hex(seed)+' required route retains optional rooms',pacing['optional_rooms']>0,pacing)
            result={'seed':hex(seed),'world':world,'pacing':pacing,'rooms':[]}
            P.enter_forest(self.c)
            for cell,desc in enumerate(world['cells']):
                self.warp(cell);w,h,grid=self.grid()
                # Collision-space floodfill on the real generated 8px grid.
                room=P.sym('gRoom');solid=F.read(self.c,room+4098,4096)
                def openp(x,y):return 0<=x<w*2 and 0<=y<h*2 and not solid[y*64+x]
                starts=[(x,y) for y in range(2,h*2-2) for x in range(2,w*2-2) if openp(x,y)]
                components=[];seen=set()
                for start in starts:
                    if start in seen:continue
                    q=deque([start]);seen.add(start);component=[]
                    while q:
                        x,y=q.popleft();component.append((x,y))
                        for v in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                            if openp(*v) and v not in seen:seen.add(v);q.append(v)
                    components.append(component)
                logs=[p for p,ns in grid.items() if ns[0]=='hlog_0']
                pairs=[grid.get((x+1,y),('',''))[0]=='hlog_1' for x,y in logs]
                self.check(f'{hex(seed)} room{cell} all large logs have two logical cells',all(pairs),logs)
                result['rooms'].append({'cell':cell,'physical_contract':self.contract(),
                    'log_left_cells':[list(p) for p in logs],'collision_component_sizes':sorted(map(len,components),reverse=True)})
            self.route_results.append(result);self.save()
        self.critical_path()
        self.palette_restore_probe()

    def palette_restore_probe(self):
        row={'name':'palette-restore-probe','seed':hex(self.seed),'cell':None}
        self.boot(row);P.enter_forest(self.c);self.settle([256,240])
        obj=F.read(self.c,P.sym('gPalObj'),512)
        ui=F.read(self.c,P.sym('gPalBg')+384,128)
        phases=[]
        for phase in range(4):
            while (P.r32(self.c,P.sym('gFrame'))>>3)&3!=phase:P.run(self.c,1)
            P.press(self.c,'START',2,16)
            self.check(f'phase{phase} ordinary Start opens item menu',C.gstate(self.c)==4)
            P.press(self.c,'START',2,16)
            hw=self.hardware();phases.append(hw)
            self.check(f'phase{phase} menu close restores exact authored world palette',hw['world_palette_bytes_match_ROM'])
            self.check(f'phase{phase} menu close restores selected OBJ palettes',F.read(self.c,P.sym('gPalObj'),512)==obj)
            self.check(f'phase{phase} menu close preserves protected HUD/map palettes',F.read(self.c,P.sym('gPalBg')+384,128)==ui)
        # Actual area transition logic restores the base Drain before the
        # next forest load resumes its authored glow banks.
        import lift_probe as L
        for area in (0,1):
            for name,value in (('sNextArea',area),('sNextCell',self.world['entry']),('sNextSide',2),('sTransPhase',0)):
                P.w8(self.c,L.ssym(name),value)
            P.w8(self.c,P.sym('gGame'),2);P.run(self.c,100);C.wait_play(self.c,area)
            self.check(f'area{area} native world palettes restored',self.hardware()['world_palette_bytes_match_ROM'])
        self.route_results.append({'palette_restore':{'four_menu_entry_phases':phases,
            'method':'Ordinary Start open/close at each actual glow phase; actual area-transition path selected by disclosed navigation fixtures.'}})

    def critical_path(self):
        folder=self.out/'critical-path';folder.mkdir(exist_ok=True)
        original_boot=P.boot;original_argv=sys.argv;original_snaps=C.S;original_tiles_of=M.tiles_of
        original_earn=C.earn_trial;original_open=M.open_chest
        def frozen_boot(*a,**kw):
            kw['rom']=self.args.rom
            return original_boot(*a,**kw)
        # Older helper modules import a current-source tile list. Resolve
        # their predicates through this frozen ROM's type table instead, so
        # appended logical root-arch IDs cannot be mistaken for old tiles.
        types={value:name[3:] for name,value in self.defs.items() if name.startswith('TT_')}
        rawtypes=self.rom.read(self.rom.symbols['metatile_type'],self.defs['METATILE_COUNT'])
        metadata=[{'name':self.names[i],'type':types[kind]} for i,kind in enumerate(rawtypes)]
        def frozen_tiles_of(c,pred,layer=0):
            return [point for point,mt in M.grid(c,layer)[2].items() if mt!=65535 and pred(metadata[mt])]
        def trial_state(c):
            here=C.cell(c);world=P.sym('gWorld')
            return {'area':C.area(c),'cell':here,'game':C.gstate(c),'player':P.actor(c,0),
                'items':P.r8(c,P.sym('gPl')+8),'textbox':P.r8(c,P.sym('gTbActive')),
                'packed_mystery':P.r8(c,world+M.MYST_OFF+here),
                'mystery_flags':P.r8(c,world+M.FLAGS_OFF+here),
                'chest_ground':frozen_tiles_of(c,lambda m:m['type'] in ('CHEST','CHEST_OPEN')),
                'chest_overlay':frozen_tiles_of(c,lambda m:m['type'] in ('CHEST','CHEST_OPEN'),1),
                'enemies':[P.actor(c,i) for i in range(1,96) if P.actor(c,i)['kind']==2]}
        def traced_open(c):
            print('CHEST_BEFORE',json.dumps(trial_state(c),sort_keys=True),flush=True)
            result=original_open(c)
            print('CHEST_AFTER',result,json.dumps(trial_state(c),sort_keys=True),flush=True)
            return result
        def retreat(c):
            room=P.sym('gRoom');w,h=P.r8(c,room),P.r8(c,room+1)
            enemies=[P.actor(c,i) for i in range(1,96) if P.actor(c,i)['kind']==2]
            choices=[]
            for ty in range(2,h-2):
                for tx in range(2,w-2):
                    x,y=tx*16+8,ty*16+12
                    mt=P.r16(c,room+2+(ty*32+tx)*2)&65535
                    if mt==65535 or metadata[mt]['type']!='FLOOR':continue
                    if any(P.r8(c,room+4098+(py//8)*64+px//8)
                           for py in range(y-12,y,4) for px in range(x-6,x+6,4)):continue
                    score=min(((x-e['x'])**2+(y-e['y'])**2 for e in enemies),default=100000)
                    choices.append((score,x,y))
            if not choices:return False
            _,x,y=max(choices);actor=P.sym('gActors')
            before=P.actor(c,0)
            # A position fixture only: preserve natural hurt, knockback,
            # invulnerability and attack timers until the ROM recovers.
            w32(c,actor+8,x<<16);w32(c,actor+12,y<<16)
            P.w16(c,P.sym('gPl')+14,x);P.w16(c,P.sym('gPl')+16,y)
            print('PLAYER_RETREAT_POSITION_FIXTURE',json.dumps({'from':[before['x'],before['y']],
                'to':[x,y],'preserved_state':before['state'],'preserved_timer':before['timer'],
                'preserved_knockback_timer':P.r8(c,actor+29)},sort_keys=True),flush=True)
            return True
        def adaptive_earn(c,claim=True):
            if not C.enter_trial(c):return False
            world=P.sym('gWorld');here=C.cell(c);packed=P.r8(c,world+M.MYST_OFF+here)
            kind=M.KINDS[packed&15]
            if not P.r8(c,world+M.FLAGS_OFF+here)&4:
                if frozen_tiles_of(c,lambda m:m['type']=='CHEST'):return False
                if kind=='switches':
                    for tx,ty in frozen_tiles_of(c,lambda m:m['name']=='myst_switch',1):
                        C.heal(c);C.teleport(c,tx*16+8,ty*16+12);P.run(c,8)
                elif kind in ('waves','miniboss'):
                    for turn in range(600):
                        C.heal(c)
                        if C.area(c)!=2 or C.cell(c)!=here:return False
                        if frozen_tiles_of(c,lambda m:m['type']=='CHEST'):break
                        if P.actor(c,0)['state']!=0 or P.r8(c,P.sym('gActors')+29):
                            if P.actor(c,0)['state']==3 or P.r8(c,P.sym('gActors')+29):retreat(c)
                            P.run(c,16);continue
                        enemies=[(i,P.actor(c,i)) for i in range(1,96) if P.actor(c,i)['kind']==2]
                        # Remove approachable fast escorts before the slow
                        # captain; always targeting actor1 can lock a probe
                        # in a contact/hurt cluster even when combat is valid.
                        enemies.sort(key=lambda v:(v[1]['type']==4,v[1]['hp'],v[0]))
                        chosen=None
                        for index,enemy in enemies:
                            approach=C.trial_attack_position(c,enemy,turn)
                            if approach is not None:chosen=(index,enemy,approach);break
                        if chosen:
                            index,enemy,(x,y,key)=chosen;C.teleport(c,x,y)
                            P.hold(c,key,1);P.press(c,'B',2,16)
                            after=P.actor(c,index)
                            if after['kind']!=2 or after['hp']!=enemy['hp']:
                                print('ACTUAL_SWORD_DAMAGE',json.dumps({'turn':turn,'actor':index,
                                    'type':enemy['type'],'HP_before':enemy['hp'],'HP_after':after['hp'],
                                    'kind_after':after['kind']},sort_keys=True),flush=True)
                        elif enemies:retreat(c);P.run(c,32)
                        else:P.run(c,60)
                else:return False
            won=C.area(c)==2 and C.cell(c)==here and bool(P.r8(c,world+M.FLAGS_OFF+here)&4)
            if not won or not claim:return won
            if not P.r8(c,world+M.FLAGS_OFF+here)&1 and not traced_open(c):return False
            C.dismiss(c)
            return M.leave(c)==1
        def traced_earn(c,*a,**kw):
            print('TRIAL_BEFORE',json.dumps(trial_state(c),sort_keys=True),flush=True)
            result=adaptive_earn(c,*a,**kw)
            print('TRIAL_AFTER',result,json.dumps(trial_state(c),sort_keys=True),flush=True)
            return result
        C.res=[]
        try:
            P.boot=frozen_boot;M.tiles_of=frozen_tiles_of;C.earn_trial=traced_earn;M.open_chest=traced_open
            sys.argv=['critical_path.py','--seed',hex(self.seed)];C.S=str(folder)
            with (folder/'run.log').open('w') as log,contextlib.redirect_stdout(log):
                status=C.main()
        finally:
            P.boot=original_boot;M.tiles_of=original_tiles_of;C.earn_trial=original_earn;M.open_chest=original_open
            sys.argv=original_argv;C.S=original_snaps
        result={'seed':hex(self.seed),'status':status,'checks':list(map(bool,C.res)),
                'passed':sum(bool(v) for v in C.res),'total':len(C.res),
                'log':'critical-path/run.log','images':['critical-path/cp%d.png'%n for n in range(1,6)],
                'method':'Actual required events, earned three rewards, real bomb/lamp/cape gate actions and Heart entry. Navigation/health/attack-position fixtures; fast escorts targeted before captain, far-floor recovery position fixtures preserve natural hurt/knockback timers. No enemy HP/AI/timer, event flag, reward or descriptor writes.'}
        self.route_results.append({'critical_path':result})
        self.check('actual three trials and gated critical path complete',status==0 and all(C.res),result)

    def save(self):
        super().save()
        path=self.out/'capture.json';r=json.loads(path.read_text())
        r.update(schema=2,method=__doc__.strip(),forest_study_round=2,
                 display_variant=self.variant-5,recipe=RECIPES.get(self.variant),
                 capture_command=[sys.executable,str(Path(__file__).resolve()),'--frozen',str(self.frozen),
                                  '--out',str(self.out),'--seed',hex(self.seed)]+
                                  (['--match',self.args.match] if self.args.match else [])+
                                  (['--only',self.args.only] if self.args.only else []),
                 capture_tool_sha256=getattr(self,'v2_tool_hash',None),
                 inherited_capture_tool_sha256=self.tool_hash,
                 capture_dependency_sha256=getattr(self,'dependencies',{}),
                 complete=self.groups==set(GROUPS),routes=getattr(self,'route_results',[]),
                 diagnostic_contracts=getattr(self,'diagnostic_contracts',[]),
                 natural_capture_count=sum(x.get('group')!='diagnostic' for x in self.rows),
                 diagnostic_capture_count=sum(x.get('group')=='diagnostic' for x in self.rows),
                 comparison_scope='Strict logical/gameplay comparison among new profiles6..10. Previous production0 is a separate protected control, not a geometry baseline.')
        path.write_text(json.dumps(r,indent=2)+'\n')

    def run(self):
        if 'control' in self.groups:
            row={'name':'drain-control','group':'control','seed':hex(self.seed),'cell':None,'frames':16}
            self.boot(row);self.record(row,[200,270])
        if self.groups&{'rooms','landscapes','npcs'}:self.natural_rooms()
        if 'landscapes' in self.groups:self.landscapes()
        if 'npcs' in self.groups:self.npcs()
        if 'interiors' in self.groups:self.interiors()
        if 'interactive' in self.groups:
            for row in IR.plan():
                if row['cell'] is not None:self.interactive(row)
        if 'gates' in self.groups:self.gates()
        if 'depth' in self.groups:self.depth()
        if 'diagnostic' in self.groups:self.diagnostic()
        if 'routes' in self.groups:self.routes()
        self.check('entire frozen bundle stayed immutable during capture',all(sha((self.frozen/n).read_bytes())==v for n,v in self.frozen_hashes.items()))
        self.check('new capture tool stayed immutable during capture',sha(Path(__file__).read_bytes())==self.v2_tool_hash)
        self.check('inherited capture dependencies stayed immutable',all(sha((Path(__file__).parent/n).read_bytes())==v for n,v in self.dependencies.items()))
        if self.groups==set(GROUPS):
            self.check('precise actual BG1 scroll telemetry is available','gForestV2DisplayedCamera' in self.rom.symbols)
            self.check('all97 requested native framebuffer cases captured',len(self.rows)==97,len(self.rows))
            self.check('fifteen meaningful actual motion clips captured',sum(bool(r.get('movie')) for r in self.rows)==15)
            self.check('all25 primary generated rooms captured',sum(r.get('group')=='rooms' for r in self.rows)==25)
            self.check('all three natural mystery styles captured',{r['natural_mystery']['style'] for r in self.rows if r.get('group')=='interiors'}=={0,1,2})
            self.check('all three natural NPC bodies and dialogues captured',sum(r.get('group')=='npcs' for r in self.rows)==3)
            self.check('six diagnostic adjacency contexts explicitly captured',sum(r.get('group')=='diagnostic' for r in self.rows)==6)
            self.check('all457 renderer mask/collision contracts exercised',len(self.diagnostic_contracts)==457,len(self.diagnostic_contracts))
            self.check('every requested feature found',not self.missing,self.missing)
        self.save();print('RESULT',sum(r['passed'] for r in self.checks),'/',len(self.checks),
            'captures',len(self.rows),'movies',sum(r.get('movie',False) for r in self.rows),flush=True)
        return int(any(not r['passed'] for r in self.checks) or bool(self.missing))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--frozen',required=True);p.add_argument('--out',required=True)
    p.add_argument('--match',help='First NEW study capture.json; never previous-generation baseline0/1.')
    p.add_argument('--seed',default='0xB4A7')
    p.add_argument('--only',help='Comma-separated groups; partial runs remain explicitly incomplete.')
    return Review(p.parse_args()).run()


if __name__=='__main__':raise SystemExit(main())

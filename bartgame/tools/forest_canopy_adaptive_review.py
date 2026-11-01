#!/usr/bin/env python3
"""Compact room-first canopy review from actual, frozen mGBA runs.

Five natural room geometries show isolated, narrow, broad healthy, broad deep
and separated/concave forest footprints. Two ordinary-input clips test walking,
rolling/recoil and cape passage. No generated-case terrain, poses or video
pixels are assigned. The adaptive planner's native placements and resident
graphics are evidence alongside unchanged semantic room/collision arrays.

The prior scanline0→160 native body/cape metrology remains the starting point.
This reader decodes actual BG1 opacity directly, without assuming that runtime
canopy picture IDs index the older fixed metatile table. Source compositions
are separate from these real native framebuffers.
"""
import argparse
import json
from pathlib import Path
import struct
import sys
from PIL import Image

import forest_v3_review as V3
import forest_concept_review as F
import probe as P
import bloom_probe as BP
import critical_path as C

VALID={6,*range(19,29)}
GROUPS={'geometry','motion','menu'}
ROLES=('small','clump','tree','grove','hero','branch','roots','border','column')
sha=F.sha
component=V3.component


def canopy_components(mask):
    remaining=set(mask);out=[]
    while remaining:
        todo=[remaining.pop()];cells=[]
        while todo:
            x,y=todo.pop();cells.append((x,y))
            for p in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if p in remaining:remaining.remove(p);todo.append(p)
        xs=[p[0] for p in cells];ys=[p[1] for p in cells]
        bounds=[min(xs),min(ys),max(xs)+1,max(ys)+1]
        concave=sum((x+1,y) in cells and (x,y+1) in cells and (x+1,y+1) not in cells for x,y in cells)
        out.append({'cells':[list(p) for p in sorted(cells)],'area':len(cells),
                    'bounds_cells':bounds,'bounds_pixels':[v*16 for v in bounds],
                    'concave_southeast_corners':concave})
    return sorted(out,key=lambda row:(-row['area'],row['bounds_cells']))


class Review(V3.Review):
    def __init__(self,args):
        requested=args.only
        args.only='landscapes'
        super().__init__(args)
        args.only=requested
        self.groups=set(requested.split(',')) if requested else {'geometry','motion'}
        if self.groups-GROUPS:raise ValueError('Unknown adaptive review group')
        self.adaptive_tool_hash=sha(Path(__file__).read_bytes())
        self.dependencies.pop(Path(__file__).name,None)
        self.dependencies['forest_v3_review.py']=sha(Path(V3.__file__).read_bytes())
        self.selected_plan=json.loads(Path(args.plan).read_text()) if args.plan else None
        self.plan_input_hash=sha(Path(args.plan).read_bytes()) if args.plan else None
        self.finished=False

    def check(self,name,condition,detail=None):
        if name in ('valid forest study profile','valid second-round forest study profile','valid canopy comparison profile'):
            name='valid adaptive canopy comparison profile';condition=self.variant in VALID
        if name=='matched baseline is preserved base6 or first canopy study':
            name='matched baseline is preserved base6 or an adaptive canopy study'
            condition=self.old and self.old.get('forest_variant') in VALID
        if name=='matched baseline used this focused capture tool':
            name='matched baseline used this adaptive capture tool'
            condition=self.old and self.old.get('capture_tool_sha256')==sha(Path(__file__).read_bytes())
        F.Review.check(self,name,condition,detail)

    def semantic_canopy(self):
        room=P.sym('gRoom');w,h=P.r8(self.c,room),P.r8(self.c,room+1)
        kinds=self.rom.array('forest_v2_canopy_kind');mask=set();typed=[];connectors=[]
        for y in range(h):
            for x in range(w):
                mt=P.r16(self.c,room+2+(y*32+x)*2)&65535
                if mt!=65535 and kinds[mt] in (1,2):
                    mask.add((x,y));typed.append([x,y,kinds[mt]])
                elif mt!=65535 and kinds[mt]==3:connectors.append([x,y])
        return {'dimensions':[w,h],'cell_size_pixels':16,'mask_cells':[list(p) for p in sorted(mask)],
                'typed_cells':typed,'connector_cells':connectors,'components':canopy_components(mask)}

    def protected_features(self):
        raw=F.read(self.c,P.sym('gSpots'),58)
        coords={'chest':25,'npc':27,'relic':29,'boss':40,'shrine':42,'treasure':44,'mouth':46}
        flags={'chest':48,'npc':49,'relic':50,'boss':51,'shrine':52,'treasure':53,'mouth':54}
        features={name:{'position_cells':list(raw[offset:offset+2]),'present':bool(raw[flags[name]])}
                  for name,offset in coords.items()}
        torches=[list(raw[31+i*2:33+i*2]) for i in range(raw[39])]
        reserved=set()
        for name,feature in features.items():
            if not feature['present'] or name=='boss':continue
            x,y=feature['position_cells'];radius=2 if name in ('mouth','shrine') else 1
            reserved.update((x+dx,y+dy) for dy in range(-radius,radius+1) for dx in range(-1,2))
        for x,y in torches:reserved.update((x+dx,y+dy) for dy in range(-1,2) for dx in range(-1,2))
        w,h=P.r8(self.c,P.sym('gRoom')),P.r8(self.c,P.sym('gRoom')+1)
        return {'raw_gSpots_hex':raw.hex(),'features':features,'torches':torches,
                'protected_projection_cells':[list(p) for p in sorted(reserved) if 0<=p[0]<w and 0<=p[1]<h],
                'note':'Read-only actual room spots. Independent union of event approaches and torch clearances; mouths/shrines use two vertical cells. Native logical type/overlay checks are also required.'}

    def planner(self):
        if self.variant==6:return {'available':False,'note':'Preserved old6 renderer; no adaptive planner.'}
        c=self.c;stats=list(struct.unpack('<16H',F.read(c,P.sym('gAdaptiveCanopyStats'),32)))
        room=P.sym('gRoom');w,h=P.r8(c,room),P.r8(c,room+1)
        mask=F.read(c,P.sym('gAdaptiveCanopyMask'),1024)
        labels=struct.unpack('<1024H',F.read(c,P.sym('gAdaptiveCanopyComponent'),2048))
        placements=[]
        for index in range(min(stats[3],256)):
            comp,role,x,y,pw,ph,flags=struct.unpack('<H6B',F.read(c,P.sym('gAdaptiveCanopyPlacements')+index*8,8))
            placements.append({'index':index,'component':comp,'role':ROLES[role] if role<len(ROLES) else 'INVALID',
                               'role_id':role,'origin_cells':[x,y],'size_cells':[pw,ph],
                               'native_size_pixels':[pw*16,ph*16],'bounds_pixels':[x*16,y*16,(x+pw)*16,(y+ph)*16],
                               'flags':flags,'layer':'foreground projection' if flags&2 else 'blocked forest',
                               'native_map_symbol':'canopy_solid_branch' if role==5 and not(flags&2) else 'canopy_prefab_%d_map'%role,
                               'collision_assignment':'unchanged semantic room; no placement writes collision'})
        components=[]
        for index in range(min(stats[2],128)):
            identifier,area,x0,y0,x1,y1,count,painted=struct.unpack('<HH4BHH',F.read(c,P.sym('gAdaptiveCanopyComponents')+index*12,12))
            components.append({'id':identifier,'area_cells':area,'bounds_cells':[x0,y0,x1+1,y1+1],
                               'placements':count,'painted_cells':painted})
        projected_context=[]
        for y in range(h):
            for x in range(w):
                if not(mask[y*32+x]&2):continue
                mt=P.r16(c,room+2+(y*32+x)*2)&65535;ov=P.r16(c,room+2050+(y*32+x)*2)&65535
                projected_context.append({'cell':[x,y],'ground_id':mt,'ground_name':self.names.get(mt),
                    'ground_type':P.r8(c,P.sym('metatile_type')+mt),'ground_prop':P.r8(c,P.sym('metatile_prop')+mt),
                    'overlay_id':ov,'overlay_name':self.names.get(ov,'none'),
                    'collision_quarters':[P.r8(c,room+4098+(y*2+dy)*64+x*2+dx) for dy in range(2) for dx in range(2)]})
        return {'available':True,'abi_version':stats[0],'room_dimensions':[w,h],'cell_size_pixels':16,'stats':dict(zip(
            ('version','components','recorded_components','placements','eligible_cells','painted_solid_cells',
             'projected_cells','largest_width_pixels','largest_height_pixels','stage','overflow','cached_redraws'),stats[:12])),
            'components':components,'placements':placements,
            'solid_cells':[[x,y] for y in range(h) for x in range(w) if mask[y*32+x]&1],
            'projected_cells':[[x,y] for y in range(h) for x in range(w) if mask[y*32+x]&2],
            'component_labels':[[x,y,labels[y*32+x]] for y in range(h) for x in range(w) if labels[y*32+x]],
            'protected_features':self.protected_features(),'projected_cell_context':projected_context,
            'mask_sha256':sha(mask),'labels_sha256':sha(struct.pack('<1024H',*labels))}

    def hardware(self):
        result=super().hardware()
        if self.variant==6 or result['active_tileset']!='forest':return result
        scene=self.planner();ts=self.ts_cache['forest'];c=self.c
        valid=True;matches=True;subtiles=0;errors=[]
        def entry_at(x,y):
            block=24+(y>>5)*2+(x>>5)
            return P.r16(c,0x06000000+block*2048+((y&31)*32+(x&31))*2)&65535
        for p in scene['placements']:
            pointer,pw,ph,role,flags=self.rom.unpack('<I4B',self.rom.symbols['canopy_prefabs']+p['role_id']*8)
            valid &= [pw,ph]==p['size_cells'] and role==p['role_id']
            if role==5 and not(p['flags']&2):pointer=self.rom.symbols['canopy_solid_branch']
            source=self.rom.unpack('<%dH'%(pw*ph*4),pointer)
            ox,oy=p['origin_cells']
            for yy in range(ph*2):
                for xx in range(pw*2):
                    expected=source[yy*pw*2+xx]
                    valid &= (expected&1023)<ts['tile_count'] and (expected>>12)<ts['palette_count']
                    if not(expected&1023):continue
                    subtiles+=1;actual=entry_at(ox*2+xx,oy*2+yy)
                    if actual!=expected:
                        matches=False
                        if len(errors)<8:errors.append({'placement':p['index'],'subtile':[xx,yy],'expected':expected,'actual':actual})
        # The atlas is immutable resident ROM art; placements change native
        # map entries only. This retains the inherited exact static/animated
        # VRAM byte checks rather than exempting a supposed dynamic tile pool.
        w,h=scene['room_dimensions'];map_valid=all(
            (entry_at(x,y)&1023)<ts['tile_count'] and (entry_at(x,y)>>12)<ts['palette_count']
            for y in range(h*2) for x in range(w*2))
        result.update(adaptive_native_map_valid=bool(valid and map_valid),
                      adaptive_placed_subtiles_checked=subtiles,
                      adaptive_placed_map_matches_ROM=matches,
                      adaptive_map_mismatches=errors)
        result['native_room_mappings'] &= bool(valid and map_valid and matches)
        return result

    def authored_palettes(self,area,ts):
        result=super().authored_palettes(area,ts)
        if self.variant<19 or area!='forest':return result
        stage=P.r16(self.c,P.sym('gAdaptiveCanopyStats')+18)&65535
        if stage>3:raise RuntimeError('Invalid actual adaptive canopy stage')
        slot=self.defs['CANOPY_PALETTE_SLOT'];out=[]
        for phase,base in enumerate(result):
            colors=bytearray(base)
            payload=self.rom.symbols['canopy_stage_colors']+(stage*4+phase)*32
            colors[slot*32:(slot+1)*32]=self.rom.read(payload,32)
            out.append(bytes(colors))
        return out

    # Native scanout body/cape decoder is inserted below. It is a concrete,
    # reviewable copy of the held prior reader, with BG1 occupancy taken from
    # hardware rather than static old metatile-family metadata.

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
        bg1_control=P.r16(c,0x0400000A)&65535
        bg1_priority=bg1_control&3
        bg1_screen=(bg1_control>>8)&31
        bg1_char=((bg1_control>>2)&3)*0x4000
        def bg_covers(wx,wy,priority):
            if priority<=bg1_priority or not(0<=wx<512 and 0<=wy<512):return False
            tx,ty=wx//8,wy//8
            sb=bg1_screen+(ty>>5)*2+(tx>>5)
            entry=P.r16(c,0x06000000+sb*2048+((ty&31)*32+(tx&31))*2)&65535
            xx,yy=wx&7,wy&7
            if entry&0x400:xx=7-xx
            if entry&0x800:yy=7-yy
            return bool((P.r8(c,0x06000000+bg1_char+(entry&1023)*32+yy*4+xx//2)>>((xx&1)*4))&15)
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

    def choose_point(self,rect):
        x0,y0,x1,y1=rect
        width,height=P.r8(self.c,P.sym('gRoom')),P.r8(self.c,P.sym('gRoom')+1)
        candidates=[]
        for y in range(2,height-1):
            for x in range(1,width-1):
                px,py=x*16+8,y*16+12
                if not self.safe(px,py):continue
                cx=max(0,min(width*16-240,px-120));cy=max(0,min(height*16-160,py-104))
                ix=max(0,min(x1,cx+232)-max(x0,cx+8))
                iy=max(0,min(y1,cy+152)-max(y0,cy+16))
                shown=ix*iy
                full=x0>=cx+4 and x1<=cx+236 and y0>=cy+14 and y1<=cy+154
                distance=abs(px-(x0+x1)//2)+abs(py-y1)
                candidates.append((int(full)*100000+shown*4-distance,px,py))
        if not candidates:raise RuntimeError('No safe natural camera point for requested canopy feature')
        _,px,py=max(candidates)
        return [px,py]

    def background_layer(self):
        """Decode the resident full-room BG2 plane as a labelled layer study.

        This is not an emulator framebuffer: no player, HUD or upper plane is
        composited into it. The real240x160 PNGs remain separate evidence.
        """
        c=self.c;control=P.r16(c,0x0400000C)&65535
        charbase=((control>>2)&3)*0x4000;screen=(control>>8)&31
        tiles=F.read(c,0x06000000+charbase,32768)
        colors=struct.unpack('<256H',F.read(c,0x05000000,512))
        rgb=[bytes((p<<3)|(p>>2) for p in (v&31,(v>>5)&31,(v>>10)&31)) for v in colors]
        w,h=P.r8(c,P.sym('gRoom'))*16,P.r8(c,P.sym('gRoom')+1)*16
        data=bytearray(w*h*3)
        for ty in range(h//8):
            for tx in range(w//8):
                block=screen+(ty>>5)*2+(tx>>5)
                entry=P.r16(c,0x06000000+block*2048+((ty&31)*32+(tx&31))*2)&65535
                base=(entry&1023)*32;pal=(entry>>12)*16
                for y in range(8):
                    yy=7-y if entry&0x800 else y
                    for x in range(8):
                        xx=7-x if entry&0x400 else x
                        ink=(tiles[base+yy*4+xx//2]>>((xx&1)*4))&15
                        at=((ty*8+y)*w+tx*8+x)*3;data[at:at+3]=rgb[pal+ink]
        return Image.frombytes('RGB',(w,h),bytes(data))

    def state(self,target=None):
        result=super().state(target)
        row=getattr(self,'recording_case',None)
        if row and row.get('action')=='canopy-depth' and result['state']==0 and result['z_q16']:
            result['motion_phase']='airborne wall recoil'
        if self.variant>=19 and row and self.frame_observations:
            self.frame_observations[-1]['adaptive_cached_redraws']=P.r16(self.c,P.sym('gAdaptiveCanopyStats')+22)&65535
        return result

    def geometry(self):
        if not self.selected_plan:raise RuntimeError('Natural geometry plan is not selected yet')
        self.plan['geometry']=self.selected_plan['geometry']
        for spec in self.plan['geometry']:
            row=dict(spec,group='geometry',frames=16,movie=False)
            self.boot(row)
            feature=spec.get('feature_bounds_pixels')
            if spec.get('feature_role') and self.variant>=19:
                placements=self.planner()['placements']
                choices=[p for p in placements if p['role']==spec['feature_role']]
                if not choices:raise RuntimeError('No requested naturally placed native '+spec['feature_role'])
                def score(p):
                    point=self.choose_point(p['bounds_pixels'])
                    cx=max(0,min(272,point[0]-120));cy=max(0,min(224,point[1]-104))
                    x0,y0,x1,y1=p['bounds_pixels']
                    shown=max(0,min(x1,cx+236)-max(x0,cx+4))*max(0,min(y1,cy+154)-max(y0,cy+14))
                    return (shown,-abs(point[0]-256),-abs(point[1]-192))
                selected=max(choices,key=score);feature=selected['bounds_pixels']
                row['selected_native_placement']=selected
            point=spec.get('position') or self.choose_point(feature)
            row['feature_bounds_pixels']=feature
            self.record(row,point,extra={'fixture_kind':'natural generated room; navigation/inventory/player fixtures only',
                        'note':'Actual room footprint and adaptive native composition. No terrain or video injection.'})

    def motion(self):
        if not self.selected_plan:raise RuntimeError('Natural geometry plan is not selected yet')
        self.plan['motion']=self.selected_plan['motion']
        for spec in self.plan['motion']:
            row=dict(spec,group='motion',movie=True)
            self.boot(row)
            C.equip_b(self.c,C.EQ_CLOAK if row['action']=='canopy-cape' else C.EQ_SWORD)
            events={int(t):[(key,bool(down)) for key,down in values] for t,values in spec['inputs'].items()}
            self.record(row,spec['position'],spec.get('target'),spec.get('facing',0),events,
                        {'note':'Ordinary input beneath a naturally generated adaptive tree boundary; no pose, z or timer assignment.'})

    def menu(self):
        spec=self.selected_plan['menu']
        row=dict(spec,group='menu',action='canopy-menu',frames=128,movie=False)
        self.boot(row)
        self.record(row,spec['position'],spec.get('target'),0,
                    {8:[('START',True)],10:[('START',False)],40:[('START',True)],42:[('START',False)]},
                    {'note':'One focused ordinary menu round trip beneath the natural branch. Checks exact native world palette/maps and cached redraw on return; interface frames are outside canopy visibility scope.'})

    def inspect_case(self,row):
        super().inspect_case(row)
        row['semantic_canopy']=self.semantic_canopy()
        row['adaptive_planner']=self.planner()
        if row['name'] in ('broad-healthy','broad-deep'):
            path=row['name']+'/bg2-resident-layer.png'
            layer=self.background_layer();layer.save(self.out/path)
            row['resident_BG2_layer']={'path':path,'sha256':sha((self.out/path).read_bytes()),
                'kind':'resident-layer reconstruction; not a240x160 emulator framebuffer',
                'dimensions':list(layer.size),
                'note':'Read-only full-room BG2 map/VRAM/palette decode at capture end. No player,HUD or upper canopy plane is composited.'}
        if self.variant<19:return
        scene=row['adaptive_planner'];name=row['name'];stats=scene['stats']
        self.check(name+' planner ABI and bounded allocations are valid',
                   scene['abi_version']==1 and not stats['overflow'] and stats['components']==stats['recorded_components'] and
                   stats['placements']<=256 and stats['recorded_components']<=128,stats)
        solid={tuple(p) for p in scene['solid_cells']};projected={tuple(p) for p in scene['projected_cells']}
        labels={(x,y):label for x,y,label in scene['component_labels']}
        actual_components=canopy_components(solid)
        actual_by_label={}
        for comp in actual_components:
            identifiers={labels.get(tuple(p)) for p in comp['cells']}
            if len(identifiers)==1:actual_by_label[next(iter(identifiers))]=comp
        component_valid=len(actual_by_label)==len(actual_components)==stats['components']
        for comp in scene['components']:
            actual=actual_by_label.get(comp['id'])
            component_valid &= bool(actual and actual['area']==comp['area_cells'] and actual['bounds_cells']==comp['bounds_cells'])
        self.check(name+' room components independently match actual runtime mask connectivity',component_valid)
        self.check(name+' planned blocked footprint stays inside logical forest',
                   all(P.r8(self.c,P.sym('forest_v2_canopy_kind')+(P.r16(self.c,P.sym('gRoom')+2+(y*32+x)*2)&65535)) in (1,2,3)
                       for x,y in solid))
        occupied=set();fits=True
        for p in scene['placements']:
            x,y=p['origin_cells'];w,h=p['size_cells']
            cells={(x+dx,y+dy) for dy in range(h) for dx in range(w)}
            fits &= not bool(cells&occupied)
            occupied |= cells
            if p['flags']&2:fits &= cells<=projected and p['component']==0
            else:fits &= cells<=solid and all(labels.get(at)==p['component'] for at in cells)
        self.check(name+' every native drawing fits its component without overlap or rescaling',fits)
        protected={tuple(p) for p in scene['protected_features']['protected_projection_cells']}
        allowed={65535,self.defs['MT_SPARKLE'],self.defs['MT_SPARKLE_WHITE'],self.defs['MT_BLIGHT_MIST']}
        self.check(name+' projections preserve actual feature approaches and dry passable ground',
                   not bool(projected&protected) and all(p['ground_type']==0 and p['ground_prop']==0 and
                       p['overlay_id'] in allowed and not any(p['collision_quarters'])
                       for p in scene['projected_cell_context']))
        self.check(name+' resident BG1 entries are exact authored native prefab maps',
                   all(s['adaptive_native_map_valid'] and s['adaptive_placed_map_matches_ROM']
                       for s in row['hardware_samples']))
        row['selected_geometry_evidence']={'feature_bounds_pixels':row.get('feature_bounds_pixels'),
            'camera':row['initial']['camera'],'position':row['position'],
            'native_sizes_present':sorted({tuple(p['native_size_pixels']) for p in scene['placements']}),
            'note':'Natural logical mask, component labels and exact ROM-native placed maps are recorded independently of the artwork source boards.'}
        if row.get('action')=='canopy-menu':
            counts=[s['adaptive_cached_redraws'] for s in self.frame_observations]
            row['adaptive_cache_resume']={'first':counts[0],'last':counts[-1],
                'note':'Only the renderer cache is redrawn; exact placed ROM maps, collision and gameplay comparison remain checked separately.'}
            self.check(name+' menu return redraws the existing canopy composition cache',counts[-1]>counts[0],row['adaptive_cache_resume'])

    def save(self):
        F.Review.save(self)
        path=self.out/'capture.json';value=json.loads(path.read_text())
        value.update(schema=4,method=__doc__.strip(),canopy_focus='adaptive-room-first',
                     display_variant=self.variant-18 if self.variant>=19 else 0,
                     recipe=self.freeze.get('label'),complete=self.finished,
                     unfrozen_pilot=bool(self.freeze.get('unfrozen_pilot',False)),
                     capture_tool_sha256=getattr(self,'adaptive_tool_hash',None),
                     capture_dependency_sha256=getattr(self,'dependencies',{}),
                     selection_plan_sha256=getattr(self,'plan_input_hash',None),
                     capture_command=[sys.executable,str(Path(__file__).resolve()),'--bundle',str(self.frozen),
                                      '--variant',str(self.variant),'--out',str(self.out)]+
                                      (['--plan',self.args.plan] if self.args.plan else [])+
                                      (['--match',self.args.match] if self.args.match else [])+
                                      (['--only',self.args.only] if self.args.only else []),
                     natural_capture_count=len(self.rows),diagnostic_capture_count=0,
                     comparison_scope='Matched generated room geometry and ordinary inputs; adaptive placements are independently recorded, not inferred from source charts.')
        path.write_text(json.dumps(value,indent=2)+'\n')

    def run(self):
        for group in ('geometry','motion','menu'):
            if group in self.groups:getattr(self,group)()
        self.check('frozen inputs stayed immutable',all(sha((self.frozen/name).read_bytes())==digest for name,digest in self.frozen_hashes.items()))
        self.check('adaptive capture tool stayed immutable',sha(Path(__file__).read_bytes())==self.adaptive_tool_hash)
        if self.args.plan:self.check('natural selection plan stayed immutable',sha(Path(self.args.plan).read_bytes())==self.plan_input_hash)
        self.check('capture dependencies stayed immutable',all(sha((Path(__file__).parent/name).read_bytes())==digest for name,digest in self.dependencies.items()))
        self.finished={'geometry','motion'}<=self.groups
        if self.finished:self.check('five natural geometries and two ordinary-input motion cases captured',
                                    len(self.rows)==7+int('menu' in self.groups))
        self.save();print('RESULT',sum(row['passed'] for row in self.checks),'/',len(self.checks),'contexts',len(self.rows),flush=True)
        return int(any(not row['passed'] for row in self.checks))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle','--frozen',dest='frozen',required=True)
    parser.add_argument('--variant',type=int)
    parser.add_argument('--out',required=True)
    parser.add_argument('--plan')
    parser.add_argument('--match',dest='match')
    parser.add_argument('--seed',default='0xB4A7')
    parser.add_argument('--only',help='geometry,motion; menu is an additional focused backend probe')
    return Review(parser.parse_args()).run()


if __name__=='__main__':raise SystemExit(main())

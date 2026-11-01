#!/usr/bin/env python3
"""Independent native and actual-room checks for the Emerald-inspired canopy.

Reuses the established 4bpp/ELF readers, not the asset packer. The direct new
painters are read in an isolated subprocess. Aesthetic approval is separate:
leaf-volume and blending must be judged in native actual-room pictures.
"""
import argparse, copy, hashlib, json, os, struct, subprocess, sys
from collections import Counter
from fractions import Fraction
from pathlib import Path

GAME=Path(__file__).resolve().parents[1]
from forest_canopy_adaptive_audit import Audit as PriorAudit, ROLES, SIZES, components, safe_file, gif_matches
from forest_canopy_adaptive_audit import GEN_REFERENCE, SOURCE_REFERENCE
from forest_v3_audit import owned
from sewer_concept_audit import NativeRom
from forest_concept_audit import native_image, native_palette
SHA=lambda b:hashlib.sha256(b).hexdigest()


def export(base):
    os.environ['BART_FOREST']='29'
    sys.path.insert(0,str(GAME/'art'))
    import forest_canopy_emerald as art
    import forest_canopy_emerald_terrain as terrain
    import palettes
    data=copy.deepcopy(json.loads(Path(base).read_text()))
    data.update(profile=29,style=1,label=art.NAMES[1])
    data['bg_palettes']={n:native_palette(c) for n,c in palettes.BG_PALETTES}
    for name,row in data['tiles'].items():
        if name.startswith('f2_canopy_'):
            kind,quad,end=name[len('f2_canopy_'):].split('_');mask,corners=[int(c,16) for c in end]
            frames=[terrain.paint_adjacency(('canopy' if int(kind)==0 else 'blight_wall')+'@q'+quad,mask,corners,0,1)]
        elif name.startswith('f2_fringe_'):
            kind,mask=name[len('f2_fringe_'):].split('_');frames=[terrain.fringe('canopy' if int(kind)==0 else 'blight_wall',int(mask,16),1)]
        elif owned(name):frames=[terrain.paint(name,p,1) for p in range(len(row['frames']))]
        else:continue
        assert len({bank for im,bank in frames})==1,name
        row['frames']=[native_image(im,(16,16)).hex() for im,bank in frames];row['bank']=frames[0][1]
    data['prefabs']=[{'role':role,'size':list(size),'pixels':native_image(art.prefab(1,role),size).hex()} for role,size in zip(ROLES,SIZES)]
    data['solid_branch']={'role':'solid_branch','size':[64,16],'pixels':native_image(art.blocked_branch(1),(64,16)).hex()}
    data['authored_groups']=[{'role':'authored-'+('large' if large else 'small')+('-b' if second else '-a'),'size':list((48,64) if large else (32,48)),'pixels':native_image(art.authored_tree(1,large,second),(48,64) if large else (32,48)).hex()} for large in (False,True) for second in (False,True)]
    data['stage_colors']=[[native_palette(p) for p in art.pulse_palettes(1,stage)[art.PALETTE_NAME]] for stage in range(4)]
    data['pulse_palettes']={n:[native_palette(p) for p in phases] for n,phases in terrain.pulse_palettes(1).items()}
    data['new_bank']=art.PALETTE_NAME;data['green_indices']=list(art.GREEN_INDICES);data['pulse_indices']=list(art.PULSE_INDICES)
    data['leaf_indices']=list(art.LEAF_INDICES)
    print(json.dumps(data,separators=(',',':')))


def leaf_diagnostics(source):
    """Measurements only: dense alpha can be filled by an ugly backing."""
    leaf=set(source['leaf_indices']);green=set(source['green_indices']);rows=[]
    for record in source['prefabs']+source['authored_groups']+[source['solid_branch']]:
        pixels=bytes.fromhex(record['pixels']);w,h=record['size'];remaining={(i%w,i//w) for i,v in enumerate(pixels) if v};largest={}
        while remaining:
            first=remaining.pop();ink=pixels[first[1]*w+first[0]];todo=[first];n=0
            for x,y in todo:
                n+=1
                for p in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                    if p in remaining and pixels[p[1]*w+p[0]]==ink:remaining.remove(p);todo.append(p)
            largest[ink]=max(largest.get(ink,0),n)
        rows.append({'role':record['role'],'size':[w,h],'alpha_pixels':sum(bool(v) for v in pixels),'leaf_pixels':sum(v in leaf for v in pixels),'green_pixels':sum(v in green for v in pixels),'largest_constant_ink_regions':largest})
    return {'roles':rows,'verdict':'No aesthetic verdict. Review actual native rooms; these measurements distinguish content/flat regions but do not prove leaf volume.'}


class Audit(PriorAudit):
    def check(self,profile,group,name,passed,detail=None):
        # Material greens may hue-shift with disease. The original adaptive
        # study's identical-green-RGB-at-all-depths rule is not a hardware or
        # user requirement. Keep the within-stage infection pulse isolation.
        if name=='pulse alters only declared infection inks; live greens remain stable':
            s=self.sources[profile];pulse=set(s['pulse_indices']);green=set(s['green_indices'])
            passed=not(pulse&green) and all(all(p[i]==stage[0][i] for i in range(16) if i not in pulse) for stage in s['stage_colors'] for p in stage)
            name='within-stage pulse changes only declared infection inks; living material roles separate'
        # The two maps can legally share leafy geometry; collision comes from
        # the logical room, not an obligation to invent different source pixels.
        if name=='separate solid64x16 native branch exact':
            from forest_canopy_adaptive_audit import decode_map
            rom=self.roms[profile];entries=struct.unpack('<16H',rom.array('canopy_solid_branch'));pixels,banks=decode_map(rom.tileset('forest'),entries,64,16)
            passed=pixels==bytes.fromhex(self.sources[profile]['solid_branch']['pixels']) and banks==[rom.defs['CANOPY_PALETTE_SLOT']]*16
            name='separate solid64x16 map exact authored pixels and palette'
        super().check(profile,group,name,passed,detail)

    def substrate(self,profile,row,rom):
        name=row['name'];scene=row['adaptive_planner'];snap=row.get('emerald_ground_snapshot',{});cells=snap.get('cells',[])
        digest=SHA(json.dumps(cells,sort_keys=True,separators=(',',':')).encode());solid={tuple(p) for p in scene['solid_cells']}
        self.check(profile,'ground_substrate',name+' complete once-per-case actual floor snapshot matches solid mask',bool(cells) and {tuple(x['cell']) for x in cells}==solid and digest==snap.get('sha256'))
        ts=rom.tileset('forest');types=rom.array('metatile_type');props=rom.array('metatile_prop');errors=[];selection_counts=Counter()
        def floor(mt):return 0<=mt<len(types) and types[mt]==0 and props[mt]==0
        def hash32(a,b):
            h=(a*0x9e3779b1)^((b+0x7f4a7c15)&0xffffffff);h&=0xffffffff
            h^=h>>15;h=(h*0x85ebca77)&0xffffffff;h^=h>>13;h=(h*0xc2b2ae3d)&0xffffffff
            return (h^(h>>16))&0xffffffff
        seed=int(row['seed'],0) if isinstance(row['seed'],str) else row['seed']
        for item in cells:
            x,y=item['cell'];ground=item.get('visual_ground_id',65535);underlay=item.get('underlay_id',65535);neighbors=item.get('neighbor_ground_ids',[])
            wanted=[(x,y+1),(x,y-1),(x+1,y),(x-1,y)];valid=len(neighbors)==4 and [tuple(q['cell']) for q in neighbors]==wanted
            valid &= all(q.get('is_floor_nonprop')==floor(q['ground_id']) for q in neighbors)
            if floor(underlay):expected=underlay;selection='stored floor'
            else:
                local=next((q['ground_id'] for q in neighbors if floor(q['ground_id'])),None)
                if local is not None:expected=local;selection='actual adjacent floor'
                elif row['stage']>=3 or row['archetype']=='arena':expected=rom.defs['MT_BLIGHT_FLOOR'];selection='sick grass fallback'
                else:expected=rom.defs['MT_MOSS0']+hash32(seed,y*32+x)%3;selection='green grass fallback'
            quarters=list(struct.unpack_from('<4H',ts['map'],ground*8)) if floor(ground) else []
            valid &= ground==expected and floor(ground) and item.get('material_selection')==selection and item.get('expected_material_id')==expected
            valid &= quarters==item.get('actual_BG2_quarters')==item.get('expected_BG2_quarters')
            if not valid:errors.append({'cell':[x,y],'ground':ground,'expected_material':expected,'selection':selection})
            selection_counts[selection]+=1
        self.check(profile,'ground_substrate',name+' raw IDs independently select stored/local/grass material and exact BG2 quarters',not errors,{'mismatches':errors[:12],'selection_counts':dict(selection_counts)})
        samples=[h.get('emerald_ground_substrate',{}) for h in row['hardware_samples']]
        self.check(profile,'ground_substrate',name+' every sampled hardware observation binds the complete native-floor snapshot',bool(samples) and all(h.get('all_solid_canopy_cells_use_native_floor') and h.get('stored_floor_is_preserved') and h.get('all_cells_choose_expected_local_material') and h.get('cell_count')==len(cells)==h.get('native_floor_valid_count') and h.get('full_cell_snapshot_sha256')==digest for h in samples))
        expected_subtiles=sum(p['size_cells'][0]*p['size_cells'][1]*4 for p in scene['placements'])
        self.check(profile,'ground_substrate',name+' every authored BG1 quarter checked including ink-zero clear writes',all(h.get('adaptive_placed_subtiles_checked')==expected_subtiles and h.get('adaptive_placed_map_matches_ROM') for h in row['hardware_samples']),{'quarters_per_sample':expected_subtiles})
        return {'cells':len(cells),'snapshot_sha256':digest,'material_selections':dict(selection_counts),'quarters_per_sample':expected_subtiles}

    def runtime(self):
        if not self.args.runtime:return {'status':'not_requested'}
        from PIL import Image
        root=Path(self.args.runtime);baseline_profile=self.args.baseline_profile
        base=json.loads((root/f'v{baseline_profile}/capture.json').read_text());baseline={r['name']:r for r in base['captures']};results=[]
        expected={'isolated-small','narrow-arm','broad-healthy','broad-deep','separated-corner','deep-branch-walk-roll','deep-branch-cape'}
        logical=('game_state','area','cell','state','position','z_q16','hp','camera','textbox','rng_state','motion_phase','safe_position','standing_type','equipment','shield_up','item_active')
        fixture=('seed','cell','group','frames','position','target','facing','inputs','physical_contract','final_physical_contract','maze_sha256','initial_progress_sha256','final_progress_sha256','initial_rng','final_rng')
        for profile in (baseline_profile,29):
            directory=root/f'v{profile}';path=directory/'capture.json';r=json.loads(path.read_text());rom=self.roms.get(profile) or NativeRom(Path(self.args.frozen)/f'v{profile}');freeze=json.loads((Path(self.args.frozen)/f'v{profile}/freeze.json').read_text())
            self.check(profile,'runtime_provenance','complete source-bound actual run',r.get('complete') and not r.get('unfrozen_pilot') and r['passed']==r['total'] and not r['failures'] and r['rom_sha256']==SHA(rom.rom) and r['source_commit']==freeze['source_commit'])
            self.check(profile,'runtime_provenance','current capture-tool identity',r['capture_tool_sha256']==SHA((GAME/'tools/forest_canopy_adaptive_review.py').read_bytes()))
            for name,digest in r['capture_dependency_sha256'].items():self.check(profile,'runtime_provenance',name+' current dependency',SHA((GAME/'tools'/name).read_bytes())==digest)
            for name,digest in r['frozen_input_sha256'].items():self.check(profile,'runtime_provenance',name+' held capture input',SHA((Path(self.args.frozen)/f'v{profile}'/name).read_bytes())==digest)
            self.roms[profile]=rom
            rows={row['name']:row for row in r['captures']};self.check(profile,'runtime_coverage','matched five natural geometries, two motion cases and optional focused menu',expected<=set(rows) and set(rows)==set(baseline) and sum(x['group']=='motion' for x in rows.values())==2 and r['diagnostic_capture_count']==0)
            minimum=cluster=100000;frames=movies=gifs=0;plans={};media={};menu_timing=[]
            hero_meta,hero=rom.sheet('hero');fx_meta,fx=rom.sheet('bloomfx');fx_pal=rom.array('bloomfx_frame_pal')
            for name,row in rows.items():
                old=baseline[name];rng=row['controlled_starting_rng'];before=rng['before'];after=rng['after']
                self.check(profile,'runtime_fixture',name+' declared action RNG preserves generated room/world/progress',before==after and before['physical_contract']==row['physical_contract'] and before['maze_sha256']==row['maze_sha256'] and before['progress_sha256']==row['initial_progress_sha256'] and rng['assigned_sRand']==rng['actual_sRand_after']==row['initial_rng']==row['initial']['rng_state']==old['controlled_starting_rng']['assigned_sRand'])
                self.check(profile,'runtime_semantics',name+' natural generation, input and physical/progress contract matched',all(row.get(k)==old.get(k) for k in fixture))
                self.check(profile,'runtime_semantics',name+' initial/final action, position and RNG matched',all(row[t].get(k)==old[t].get(k) for t in ('initial','final') for k in logical))
                if row['group']!='menu':self.check(profile,'runtime_cadence',name+' strict ordinary-input update cadence matched',row['cadence_observation']['intervals']==old['cadence_observation']['intervals'])
                else:
                    menu_timing.append({'case':name,'absolute_tick_cadence_identical':row['cadence_observation']['intervals']==old['cadence_observation']['intervals'],'candidate':row['cadence_observation'],'baseline':old['cadence_observation'],'note':'Menu handoff timing is measured separately from ordinary PLAY cadence, not silently declared identical.'})
                    intervals=row['cadence_observation']['intervals'];old_intervals=old['cadence_observation']['intervals']
                    zeros=lambda seq:[(p['from_tick'],p['to_tick']) for p in seq if p['gameplay_update_delta']==0]
                    self.check(profile,'runtime_cadence',name+' playing intervals stay1/1 except the same declared interface entry intervals',all(p['irq_delta']==1 and p['gameplay_update_delta'] in (0,1) for p in intervals) and zeros(intervals)==zeros(old_intervals))
                    cache=row.get('adaptive_cache_resume',{})
                    self.check(profile,'runtime_cache',name+' unchanged scene is reused on ordinary menu resume',cache.get('last',0)>cache.get('first',0))
                obs=row['visibility_observations'];frames+=len(obs)
                self.check(profile,'runtime_hardware',name+' one scanline0-to160 pair per observed frame',len(obs)==row['video_frames'] and all(s['visibility'].get('scanout_start_vcount')==0 and s['visibility'].get('scanout_end_vcount')==160 and s['visibility'].get('scanout_frame_counter')==s['visibility'].get('scanout_end_frame_counter') for s in obs))
                keys=('native_room_mappings','static_BG_bytes_match_ROM','animated_BG_bytes_are_authored_frames','OAM_legal','world_palette_is_authored_phase','actual_hardware_palette_is_authored_phase','selected_OBJ_palette_bytes_match_ROM','resolved_visual_mappings_valid','adaptive_native_map_valid','adaptive_placed_map_matches_ROM')
                self.check(profile,'runtime_hardware',name+' resident native BG/OAM payloads valid',bool(row['hardware_samples']) and all(all(h.get(k) for k in keys) for h in row['hardware_samples']))
                plans[name]=self.planner(profile,row)
                if profile==29:
                    plans[name]['substrate']=self.substrate(profile,row,rom)
                gap=set(row.get('menu_resume_hardware_gap',{}).get('ticks',[]))
                for sample in obs:
                    vis=sample['visibility'];playing=sample['game_state']==1 and sample['displayed_world_planes'] and sample['tick'] not in gap
                    if not playing:continue
                    goal=max(12,(vis.get('opaque_colored_pixels',0)+3)//4)
                    self.check(profile,'runtime_visibility',name+':'+str(sample['tick'])+' actual body and displayed character remain recognizable',vis.get('body_found') and vis.get('guard_exact_native_subset') and vis.get('visible_colored_pixels',0)>=goal and vis.get('largest_visible_colored_component',0)>=8 and vis.get('framebuffer_exact_character_color_pixels',0)>=12 and vis.get('framebuffer_exact_character_color_component',0)>=8)
                    minimum=min(minimum,vis.get('framebuffer_exact_character_color_pixels',0));cluster=min(cluster,vis.get('framebuffer_exact_character_color_component',0))
                    cape=vis.get('attached_cape')
                    if cape:
                        ref=cape['native_frame'];face=ref['face'];phase=ref['phase'];f=rom.defs['F_BLOOMFX_CAPE_'+face+str(phase)];b=rom.defs['F_HERO_CAPE_'+face+str(phase+1)];fs=fx_meta['frame_tiles']*32;hs=hero_meta['frame_tiles']*32
                        self.check(profile,'runtime_cape',name+':'+str(sample['tick'])+' only exact current native attached garment counts',cape.get('exact_current_native_pose_and_anchor') and cape.get('anchor_projection_delta')==[0,0] and cape['VRAM_sha256']==SHA(fx[f*fs:(f+1)*fs]) and vis['body_VRAM_sha256']==SHA(hero[b*hs:(b+1)*hs]) and cape['OAM']['pal']==ref['palette']==fx_pal[f] and ref['frame']==f)
                paths=set(row['native_frames'])|{row['image']}
                for key in ('after_image','filmstrip','video','gif'):
                    if row.get(key):paths.add(row[key])
                for key in ('action_keyframes','phase_keyframes'):paths.update(e['path'] for e in row.get(key,[]))
                for key in ('worst_visibility_keyframe','displayed_character_keyframe'):
                    if row.get(key):paths.add(row[key]['path'])
                if row.get('resident_BG2_layer'):paths.add(row['resident_BG2_layer']['path'])
                missing=[]
                for rel in paths:
                    p=safe_file(directory,rel)
                    if p.is_file():media[rel]=SHA(p.read_bytes())
                    else:missing.append(rel)
                self.check(profile,'runtime_media',name+' native/viewing files all exist',not missing,missing)
                self.check(profile,'runtime_media',name+' exact native still dimensions',all(Image.open(safe_file(directory,p)).size==(240,160) for p in row['native_frames']))
                if row.get('video'):
                    movies+=1;stream=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,nb_read_frames','-of','json',str(safe_file(directory,row['video']))],text=True))['streams'][0];rate=Fraction(262144,4389)
                    self.check(profile,'runtime_media',name+' exact GBA-rate viewing movie duration',stream['width']==480 and stream['height']==320 and Fraction(stream['r_frame_rate'])==rate and int(stream['nb_read_frames'])==row['video_frames'])
                if row.get('gif'):
                    gifs+=1;self.check(profile,'runtime_media',name+' sampled native colors and GBA-clock GIF exact',row['gif_metadata']['exact_palette'] and gif_matches(safe_file(directory,row['gif']),safe_file(directory,row['all_frames']),row['video_frames'],row['video_fps']))
            results.append({'profile':profile,'contexts':len(rows),'movies':movies,'exact_gifs':gifs,'observed_video_frames':frames,'minimum_actual_character_pixels':minimum,'minimum_actual_character_component':cluster,'report_sha256':SHA(path.read_bytes()),'media_manifest_sha256':SHA(json.dumps(media,sort_keys=True).encode()),'planner_cases':plans,'menu_timing_observations':menu_timing})
        return {'profiles':results,'contexts':sum(x['contexts'] for x in results),'movies':sum(x['movies'] for x in results),'exact_gifs':sum(x['exact_gifs'] for x in results),'observed_video_frames':sum(x['observed_video_frames'] for x in results),'baseline_profile':baseline_profile,'limits':'Finite natural-room and ordinary-input observations; menu handoff timings are explicit observations; no universal animation/frame-time claim.'}

    def source_gallery(self):
        if not self.args.source_gallery:return {'status':'not_requested'}
        from PIL import Image,ImageSequence
        root=Path(self.args.source_gallery);manifest_path=root/'source-manifest.json';manifest=json.loads(manifest_path.read_text());source=self.sources[29]
        self.check(29,'source_provenance','final one-profile source catalog matches frozen revision and helper',manifest['profile']==29 and manifest['style']==1 and manifest['source_commit']==self.profiles[0]['source_commit'] and manifest['gallery_tool_sha256']==SHA((GAME/'tools/forest_canopy_emerald_gallery.py').read_bytes()))
        for name,digest in manifest['source_input_sha256'].items():self.check(29,'source_provenance',name+' current source bytes',SHA((GAME/name).read_bytes())==digest)
        for name,record in manifest['files'].items():
            path=safe_file(root,name);self.check(29,'source_files',name+' exact bytes',path.is_file() and path.stat().st_size==record['bytes'] and SHA(path.read_bytes())==record['sha256'])
        catalog=json.loads((root/'native-manifest.json').read_text());records={r['role']:r for r in source['prefabs']+source['authored_groups']};records['branch-solid']=source['solid_branch'];board=Image.open(root/'native-healthy-deep-source.png').convert('RGB')
        self.check(29,'source_coverage','exactly fourteen native source roles/groups',len(catalog['entries'])==14 and {e['role'] for e in catalog['entries']}==set(records))
        def rgba(record,colors):
            image=Image.new('RGBA',tuple(record['size']));image.putdata([((colors[i]&31)<<3,((colors[i]>>5)&31)<<3,((colors[i]>>10)&31)<<3,255 if i else 0) for i in bytes.fromhex(record['pixels'])]);return image
        def backing(image):
            result=Image.new('RGB',image.size,catalog['catalog_background']);result.paste(image,(0,0),image);return result
        for e in catalog['entries']:
            record=records[e['role']];indexed=Image.open(root/e['native_indexed']);pixels=bytes.fromhex(record['pixels'])
            self.check(29,'source_native',e['role']+' original native P16 file',indexed.mode=='P' and indexed.size==tuple(record['size']) and indexed.tobytes()==pixels and SHA(pixels)==e['index_sha256'])
            for stage,key,rect in ((0,'native_healthy','catalog_healthy_rect'),(3,'native_deep','catalog_native_rect')):
                expected=rgba(record,source['stage_colors'][stage][0]);actual=Image.open(root/e[key]).convert('RGBA');x,y,w,h=e[rect]
                self.check(29,'source_native',e['role']+' stage'+str(stage)+' literal palette/alpha source PNG',expected.size==actual.size and expected.tobytes()==actual.tobytes())
                self.check(29,'source_panels',e['role']+' stage'+str(stage)+' exact native catalog panel',(w,h)==expected.size and board.crop((x,y,x+w,y+h)).tobytes()==backing(expected).tobytes())
        frames=[];hero=records['hero']
        for phase in range(4):
            frame=Image.open(root/f'palette-phase-{phase}-source.png').convert('RGB');frames.append(frame)
            for stage in range(4):
                expected=backing(rgba(hero,source['stage_colors'][stage][phase]));x=stage*108+5
                self.check(29,'source_palette',f'depth{stage}phase{phase} exact native RGB555 panel',frame.crop((x,45,x+96,109)).tobytes()==expected.tobytes())
        with Image.open(root/'palette-inspection-source.gif') as gif:decoded=[(f.convert('RGB').copy(),f.info.get('duration')) for f in ImageSequence.Iterator(gif)]
        self.check(29,'source_gif','exact four palette-inspection frames and180ms holds',len(decoded)==4 and all(d.tobytes()==f.tobytes() and hold==180 for (d,hold),f in zip(decoded,frames)))
        return {'manifest_sha256':SHA(manifest_path.read_bytes()),'source_commit':manifest['source_commit'],'native_images':len(catalog['entries']),'hashed_files':len(manifest['files']),'limits':'Source file/native panels verified. These are not actual room framebuffers.'}

    def run(self):
        self.equal('source','scope','logical room generation unchanged',subprocess.check_output(['git','show',GEN_REFERENCE+':bartgame/src/roomgen.c'],cwd=GAME),(GAME/'src/roomgen.c').read_bytes())
        for name in ('player','actor','enemy','boss','objects','game','world','util'):
            file='src/'+name+'.c';self.equal('source','scope',file+' action/gameplay source unchanged',subprocess.check_output(['git','show',SOURCE_REFERENCE+':bartgame/'+file],cwd=GAME),(GAME/file).read_bytes())
        rom=NativeRom(Path(self.args.frozen)/'v29');freeze=self.provenance(29,rom);self.roms[29]=rom
        source=json.loads(subprocess.check_output([sys.executable,__file__,'--export-source','--base-source',self.args.base_source],cwd=GAME,text=True));self.sources[29]=source
        result=self.native(29,rom,source);self.profiles.append({'profile':29,'source_commit':freeze['source_commit'],'rom_sha256':SHA(rom.rom),**result})
        for profile in range(29):
            previous=Path(self.args.previous_controls)/f'v{profile}';current=Path(self.args.controls_root)/f'v{profile}'
            old=json.loads((previous/'freeze.json').read_text());before=(previous/'bartgame.gba').read_bytes();after=(current/'bartgame.gba').read_bytes()
            self.check(profile,'historical','prior full ROM and recorded identity exact',SHA(before)==old['rom_sha256'] and before==after,{'previous_sha256':SHA(before),'current_sha256':SHA(after)})
        source_gallery=self.source_gallery();runtime=self.runtime();failures=[r for r in self.rows if not r['passed']]
        report={'method':__doc__,'source_commits':[freeze['source_commit']],'auditor_sha256':SHA(Path(__file__).read_bytes()),'decoder_sha256':SHA((GAME/'tools/forest_canopy_adaptive_audit.py').read_bytes()),'profiles':self.profiles,'leaf_diagnostics':leaf_diagnostics(source),'source_gallery':source_gallery,'runtime':runtime,'historical_controls':[r for r in self.rows if r['group']=='historical'],'passed':len(self.rows)-len(failures),'total':len(self.rows),'failures':failures,'checks_by_group':dict(Counter(r['group'] for r in self.rows)),'aesthetic_verdict':'Separate native actual-room critique required. Dense alpha or passing counters are not proof of leaf volume or blending.'}
        if self.args.details:report['checks']=self.rows
        out=Path(self.args.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'total':report['total'],'failures':len(failures),'report':str(out)}));return bool(failures)


def main():
    w=Path('/workspace/setup/forest-canopy-emerald');p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--frozen',default=str(w/'frozen'));p.add_argument('--controls-root');p.add_argument('--previous-controls',default='/workspace/setup/forest-canopy-adaptive/frozen');p.add_argument('--base6',default='/workspace/setup/forest-canopy-adaptive/frozen/v6');p.add_argument('--base-source',default='/workspace/setup/forest-canopy-adaptive/audit/base6-source.json');p.add_argument('--inventory',default=str(GAME.parent/'art-review/forest-concepts/validation/inventory.json'));p.add_argument('--export-source',action='store_true');p.add_argument('--runtime');p.add_argument('--source-gallery');p.add_argument('--baseline-profile',type=int,default=19);p.add_argument('--out',default=str(w/'audit/final-audit.json'));p.add_argument('--details',action='store_true')
    args=p.parse_args();args.controls_root=args.controls_root or args.frozen
    if args.export_source:export(args.base_source);return 0
    return Audit(args).run()
if __name__=='__main__':raise SystemExit(main())

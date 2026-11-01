#!/usr/bin/env python3
"""Focused independent native/scope and finite actual adaptive-canopy audit.

Reads direct native painters in clean subprocesses, independently decodes packed
ROM nibbles/maps, and checks recorded planner fit, semantics and real scanout.
Technical success is not an aesthetic approval. Real room critique is separate.
No unchanged generation corpus or universal visibility/performance claim.
"""
import argparse, copy, hashlib, json, os, re, struct, subprocess, sys
from collections import Counter
from fractions import Fraction
from pathlib import Path

GAME=Path(__file__).resolve().parents[1]
WORK=Path('/workspace/setup/forest-canopy-adaptive')
from sewer_concept_audit import NativeRom, decode_metatile, decode_8x8
from forest_concept_audit import native_image, native_palette
from forest_v3_audit import Audit as VisibilityAudit, owned, HISTORICAL_SHA as OLD_SHA
from enemy_study_audit import Audit as EnemyAudit
SHA=lambda b:hashlib.sha256(b).hexdigest()
HISTORICAL={**OLD_SHA,11:'1a125213d152e764ad201f87d6097c5d16cc9c8f49ed5837c6a5c6fafd3f940c',12:'b22ee8a09b350e30a7b54aafd8dc24ca688b9c28122333576d83390dcb43bbed',13:'cb51ca2122dd0ae22796eda6d574662074d7021ce7e42ecaa1dd8e0cd62aee2f',14:'a511bfeb34db8d665fcf7fc49a643f1dd7250a4413f26f114baeb4991756bd91',15:'75706dae8ecd8bee0a7475a5eb5aaa7463cbcb23ccca627859e84b24269300c7',16:'4cdd03ae3c2f55d96dece4d0e67d0cd1838e0d3c316ed2bda711df9e2ff9a8e3',17:'4dda2734fd2f4934b08c14aa5cbb7a9854f8fecca237d7677ebcf74bfb5ee2b3',18:'54768ae3f4462743dabd72e03ddd3c9f711ad4ebff2e09474bd3bd85d427e4af'}
ROLES=('small','clump','tree','grove','hero','branch','roots','border','column')
SIZES=((16,16),(32,32),(48,48),(64,64),(96,64),(64,16),(32,16),(96,32),(16,64))
GEN_REFERENCE='0170bddf1b636afb0d251ba79536f602938d9ce8'
SOURCE_REFERENCE='01d05ace7ce771e6d3baec6be91fc9e1496ff8f4'


def export(profile,base):
    os.environ['BART_FOREST']=str(profile)
    sys.path.insert(0,str(GAME/'art'))
    import forest_canopy_adaptive as art
    import forest_canopy_adaptive_terrain as terrain
    import palettes
    style=profile-18
    data=copy.deepcopy(json.loads(Path(base).read_text()))
    data.update(profile=profile,style=style,label=art.NAMES[style])
    data['bg_palettes']={n:native_palette(c) for n,c in palettes.BG_PALETTES}
    for name,row in data['tiles'].items():
        if name.startswith('f2_canopy_'):
            kind,quad,end=name[len('f2_canopy_'):].split('_')
            mask,corners=[int(c,16) for c in end]
            frames=[terrain.paint_adjacency(('canopy' if int(kind)==0 else 'blight_wall')+'@q'+quad,mask,corners,0,style)]
        elif name.startswith('f2_fringe_'):
            kind,mask=name[len('f2_fringe_'):].split('_')
            frames=[terrain.fringe('canopy' if int(kind)==0 else 'blight_wall',int(mask,16),style)]
        elif owned(name):
            frames=[terrain.paint(name,p,style) for p in range(len(row['frames']))]
        else:continue
        assert len({bank for im,bank in frames})==1,name
        row['frames']=[native_image(im,(16,16)).hex() for im,bank in frames]
        row['bank']=frames[0][1]
    data['prefabs']=[{'role':role,'size':list(size),'pixels':native_image(art.prefab(style,role),size).hex()} for role,size in zip(ROLES,SIZES)]
    data['solid_branch']={'role':'solid_branch','size':[64,16],'pixels':native_image(art.blocked_branch(style),(64,16)).hex()}
    data['authored_groups']=[{'role':'authored-'+('large' if large else 'small')+('-b' if second else '-a'),
        'size':list((48,64) if large else (32,48)),
        'pixels':native_image(art.authored_tree(style,large,second),(48,64) if large else (32,48)).hex()}
        for large in (False,True) for second in (False,True)]
    data['stage_colors']=[[native_palette(p) for p in art.pulse_palettes(style,stage)[art.PALETTE_NAME]] for stage in range(4)]
    data['pulse_palettes']={n:[native_palette(p) for p in rows] for n,rows in terrain.pulse_palettes(style).items()}
    data['new_bank']=art.PALETTE_NAME
    data['green_indices']=list(art.GREEN_INDICES);data['pulse_indices']=list(art.PULSE_INDICES)
    print(json.dumps(data,separators=(',',':')))


def decode_map(ts,entries,w,h):
    """Decode actual GBA BG entries without the packer/deduplicator."""
    assert len(entries)==w*h//64
    pixels=bytearray(w*h);banks=[];columns=w//8
    for n,entry in enumerate(entries):
        tile=entry&1023;assert tile<ts['tile_count']
        values=decode_8x8(ts['tiles'][tile*32:(tile+1)*32]);banks.append(entry>>12)
        x0=n%columns*8;y0=n//columns*8
        for y in range(8):
            for x in range(8):
                sx=7-x if entry&1024 else x;sy=7-y if entry&2048 else y
                pixels[(y0+y)*w+x0+x]=values[sy*8+sx]
    return bytes(pixels),banks


def components(points):
    remaining=set(points);out=[]
    while remaining:
        first=min(remaining,key=lambda p:(p[1],p[0]));remaining.remove(first);todo=[first];cc={first}
        for x,y in todo:
            for p in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if p in remaining:remaining.remove(p);cc.add(p);todo.append(p)
        out.append(cc)
    return out


def safe_file(directory,name):
    root=directory.resolve();path=(directory/name).resolve()
    assert path.is_relative_to(root),('unsafe artifact reference',name)
    return path


def gif_matches(path,raw,count,fps):
    from PIL import Image,ImageSequence
    chunks=[]
    with Image.open(path) as gif:
        for frame in ImageSequence.Iterator(gif):
            duration=frame.info.get('duration',0)
            if duration<=0 or duration%10:return False
            chunks.append([frame.convert('RGB').tobytes(),duration//10])
    cursor=elapsed=0
    for tick in range(0,count,2):
        with Image.open(raw/f'frame-{tick:03}.png') as image:
            expected=image.convert('RGB').resize((480,320),Image.Resampling.NEAREST).tobytes()
        need=round(min(tick+2,count)*100/fps)-round(tick*100/fps)
        while need:
            if cursor>=len(chunks) or chunks[cursor][0]!=expected:return False
            use=min(need,chunks[cursor][1]);need-=use;elapsed+=use;chunks[cursor][1]-=use
            if chunks[cursor][1]==0:cursor+=1
    return cursor==len(chunks) and elapsed==round(count*100/fps)


class Audit:
    def __init__(self,args):
        self.args=args;self.rows=[];self.profiles=[];self.budgets=[]
        self.base=NativeRom(args.base6);self.base_source=json.loads(Path(args.base_source).read_text())
        inv=json.loads(Path(args.inventory).read_text());self.specs={x['name']:x for x in inv['tiles']}
        self.sources={};self.roms={}

    def check(self,profile,group,name,passed,detail=None):
        row={'profile':profile,'group':group,'name':name,'passed':bool(passed)}
        if detail is not None:row['detail']=detail
        self.rows.append(row)
        if not passed:print('FAIL',profile,group,name,str(detail)[:500],flush=True)

    def equal(self,profile,group,name,expected,actual):
        self.check(profile,group,name,expected==actual,{'expected_sha256':SHA(expected),'actual_sha256':SHA(actual),'expected_bytes':len(expected),'actual_bytes':len(actual)})

    def provenance(self,profile,rom):
        directory=Path(self.args.frozen)/f'v{profile}';freeze=json.loads((directory/'freeze.json').read_text())
        self.check(profile,'provenance','final source and ROM identity',not freeze.get('unfrozen_pilot') and SHA(rom.rom)==freeze['rom_sha256'] and rom.defs['BART_FOREST_VARIANT']==profile)
        for group in ('source_file_sha256','code_file_sha256'):
            for name,digest in freeze.get(group,{}).items():
                path=GAME/name;current=SHA(path.read_bytes());committed=SHA(subprocess.check_output(['git','show',freeze['source_commit']+':bartgame/'+name],cwd=GAME))
                self.check(profile,'provenance',name+' current and committed bytes',current==digest==committed)
        return freeze

    def native(self,profile,rom,source):
        self.check(profile,'scope','all semantic metatile and sheet IDs unchanged',rom.tile_ids==self.base.tile_ids and rom.sheet_ids==self.base.sheet_ids)
        for field in ('metatile_type','metatile_coll','metatile_prop','metatile_glitter','pal_obj','pal_face'):
            self.equal(profile,'scope',field+' exact preserved6',self.base.array(field),rom.array(field))
        for name in self.base.sheet_ids:
            am,a=self.base.sheet(name);bm,b=rom.sheet(name)
            self.check(profile,'scope',name+' complete OBJ source/metadata unchanged',am==bm and a==b)
            route=name+'_frame_pal'
            if route in self.base.sections:self.equal(profile,'scope',route,self.base.array(route),rom.array(route))
        self.check(profile,'scope','source tile inventory unchanged',set(source['tiles'])==set(self.base_source['tiles']))
        original_palettes=self.base_source['bg_palettes']
        self.check(profile,'scope','exactly one dedicated canopy palette; all original ramps unchanged',set(source['bg_palettes'])-set(original_palettes)=={source['new_bank']} and all(source['bg_palettes'].get(n)==v for n,v in original_palettes.items()))
        self.check(profile,'scope','original non-canopy source and pulse payloads unchanged',all(row==self.base_source['tiles'][name] for name,row in source['tiles'].items() if not owned(name)) and source['pulse_palettes']==self.base_source['pulse_palettes'])
        # The baseline source export deliberately concerns forest art, while
        # surrounding Drain/UI selectors have their own selected palettes.
        # Preserve those actual native banks instead of assuming their source
        # modules were imported under this subprocess's default selectors.
        native_pal=rom.array('pal_bg');old_pal=self.base.array('pal_bg')
        self.equal(profile,'native_palette','complete original native BG palette prefix exact',old_pal,native_pal[:len(old_pal)])
        new_slot=rom.defs['PAL_BG_'+source['new_bank'].upper()]
        self.check(profile,'native_palette','one new logical bank appended',new_slot==self.base.defs['PAL_BG_COUNT'] and len(native_pal)==len(old_pal)+32)
        self.equal(profile,'native_palette','new bank exact authored RGB555 inks',struct.pack('<16H',*source['bg_palettes'][source['new_bank']]),native_pal[new_slot*32:(new_slot+1)*32])
        counts={};budget={}
        for area in ('forest','myst','sewer'):
            ts=rom.tileset(area);old=self.base.tileset(area);budget[area]={k:ts[k] for k in ('tile_count','palette_count')}
            self.check(profile,'budget',area+' resident BG/area palette limits',ts['tile_count']<=1024 and ts['palette_count']<=12 and len(ts['animations'])<=255,budget[area])
            native_errors=[];protected_errors=[];frames=0;protected=0
            for name,row in source['tiles'].items():
                if name in self.specs and area not in self.specs[name]['areas']:continue
                if name not in self.specs and area!='forest':continue
                value=decode_metatile(rom,ts,name);colors=source['bg_palettes'][row['bank']]
                if len(value['frames'])!=len(row['frames']):native_errors.append(name+':frame_count');continue
                for phase,(indices,rgba555) in enumerate(value['frames']):
                    expected=bytes.fromhex(row['frames'][phase]);material=struct.pack('<256H',*[colors[i] if i else 0x8000 for i in expected]);frames+=1
                    if indices!=expected or rgba555!=material:native_errors.append(name+':'+str(phase))
                if not owned(name):
                    before=decode_metatile(self.base,old,name);protected+=1
                    if value['frames']!=before['frames'] or value['speed']!=before['speed']:protected_errors.append(name)
            self.check(profile,'native',area+' all direct source nibbles/materials match packed frames',not native_errors,{'frames':frames,'mismatches':native_errors[:20]})
            self.check(profile,'scope',area+' all non-canopy native colors and clocks exact',not protected_errors,{'tiles':protected,'mismatches':protected_errors[:20]})
            counts[area]={'direct_frames':frames,'protected_tiles':protected}
            if area=='sewer':self.check(profile,'scope','Drain complete native payloads remain exact',all(ts[k]==old[k] for k in ('tiles','palettes','map','animations')))
        # Resolved immutable game/art payloads exclude relocatable descriptors.
        exclusions={'tilesets','sheets','room_defs','pal_bg','metatile_map_forest','metatile_map_myst','tile_anims_forest','tile_anims_myst','tile_anims_sewer'}
        changes=[];checked=0
        for name in self.base.sections:
            if name in exclusions or name.startswith(('tileset_forest_','tileset_myst_','tile_anim_forest_','tile_anim_myst_')):continue
            if name.startswith(('forest_v2_','forest_v3_')):continue
            if name not in rom.sections or self.base.array(name)!=rom.array(name):changes.append(name)
            checked+=1
        self.check(profile,'scope','remaining immutable game/art payloads exact',not changes,{'sections':checked,'mismatches':changes[:30]})
        ts=rom.tileset('forest');slot=rom.defs['CANOPY_PALETTE_SLOT'];prefab_rows=[]
        self.check(profile,'prefabs','nine native descriptors plus solid limb map',rom.defs['CANOPY_PREFAB_COUNT']==9 and len(rom.array('canopy_prefabs'))==72 and len(rom.array('canopy_solid_branch'))==32)
        for n,record in enumerate(source['prefabs']):
            pointer,w,h,role,flags=rom.unpack('<I4B',rom.symbols['canopy_prefabs']+n*8)
            size=record['size'];entries=rom.unpack('<%dH'%(w*h*4),pointer);pixels,banks=decode_map(ts,entries,*size)
            self.check(profile,'prefabs',record['role']+' exact native dimensions and map source',role==n and flags==0 and [w*16,h*16]==size and pointer==rom.symbols['canopy_prefab_%d_map'%n] and banks==[slot]*len(entries) and pixels==bytes.fromhex(record['pixels']))
            prefab_rows.append({'role':record['role'],'native_size':size,'native_index_sha256':SHA(pixels),'map_sha256':SHA(struct.pack('<%dH'%len(entries),*entries))})
        branch=source['solid_branch'];entries=struct.unpack('<16H',rom.array('canopy_solid_branch'));pixels,banks=decode_map(ts,entries,64,16)
        self.check(profile,'prefabs','separate solid64x16 native branch exact',pixels==bytes.fromhex(branch['pixels']) and banks==[slot]*16 and pixels!=bytes.fromhex(source['prefabs'][5]['pixels']))
        colors=bytes().join(struct.pack('<16H',*p) for stage in source['stage_colors'] for p in stage)
        self.equal(profile,'palette','four depths by four pulse states by sixteen RGB555 inks',colors,rom.array('canopy_stage_colors'))
        pulse=set(source['pulse_indices']);green=set(source['green_indices']);allstates=source['stage_colors']
        self.check(profile,'palette','pulse alters only declared infection inks; live greens remain stable',not(pulse&green) and all(all(p[i]==stage[0][i] for i in range(16) if i not in pulse) for stage in allstates for p in stage) and all(allstates[s][0][i]==allstates[0][0][i] for s in range(4) for i in green))
        hero=bytes.fromhex(source['prefabs'][4]['pixels']);leaf={5,6,7,*green};den=sum(i in leaf for i in hero);green_count=sum(i in green for i in hero)
        self.check(profile,'palette','large native deep crown retains living leaf groups',green_count>=8,{'green_pixels':green_count,'leaf_underbrush_pixels':den,'percent_of_leaf_underbrush_inks':round(green_count*100/den,3) if den else None,'scope':'source hero leaf/underbrush ink composition, not screen percentage or per-tile quota'})
        visibility=VisibilityAudit.visibility_metadata(self,profile,rom)
        EnemyAudit.budget(self,profile,rom,11);union=self.budgets[-1];extra=4*rom.sheet('forestlandmark')[0]['frame_tiles']+16;union['used']+=extra;union['free']-=extra;union['allocations']['four streamed landmarks']=extra-16;union['allocations']['current-body visibility fragment']=16
        self.check(profile,'budget','OBJ superset including visibility/landmarks fits',union['used']<=union['limit'],union)
        memory={n:int(a,16) for a,n in re.findall(r'^\s+0x([0-9a-fA-F]+)\s+(__ewram_bss_end|__bss_end)\s*=',rom.linker,re.M)}
        self.check(profile,'budget','native RAM respects reserved stack and EWRAM',memory.get('__bss_end',2**32)<=0x03007e00 and memory.get('__ewram_bss_end',2**32)<=0x02040000,memory)
        return {'counts':counts,'BG_budgets':budget,'prefabs':prefab_rows,'solid_branch_sha256':SHA(pixels),'visibility':visibility,'OBJ_superset':union,'memory':memory}

    def planner(self,profile,row):
        scene=row['adaptive_planner'];name=row['name'];w,h=scene['room_dimensions'];stats=scene['stats']
        solid={tuple(p) for p in scene['solid_cells']};projected={tuple(p) for p in scene['projected_cells']}
        # Logical kind3 wall-tree connectors are separate from kind1/2 crown
        # cells in the report, but are legitimate solid planner substrate.
        semantic={tuple(p) for p in row['semantic_canopy']['mask_cells']}|{tuple(p) for p in row['semantic_canopy'].get('connector_cells',[])}
        labels={(x,y):label for x,y,label in scene['component_labels']};groups=components(solid);records={c['id']:c for c in scene['components']}
        self.check(profile,'planner',name+' bounded semantic cells/complete components',scene['available'] and stats['overflow']==0 and len(groups)==stats['components']==stats['recorded_components'] and len(solid)==stats['eligible_cells'] and solid<=semantic and not(solid&projected) and all(0<=x<w and 0<=y<h for x,y in solid|projected))
        component_errors=[]
        for n,cc in enumerate(groups,1):
            xs=[p[0] for p in cc];ys=[p[1] for p in cc];c=records.get(n,{})
            if not all(labels.get(p)==n for p in cc) or c.get('area_cells')!=len(cc) or c.get('bounds_cells')!=[min(xs),min(ys),max(xs)+1,max(ys)+1]:component_errors.append(n)
        self.check(profile,'planner',name+' independent four-connected component bounds/areas',not component_errors,component_errors)
        occupied=set();fit_errors=[];counts=Counter();areas=Counter();projected_covered=set();sizes=set()
        for p in scene['placements']:
            x,y=p['origin_cells'];pw,ph=p['size_cells'];role=p['role_id'];flags=p['flags'];cells={(x+dx,y+dy) for dy in range(ph) for dx in range(pw)}
            expected=SIZES[role] if 0<=role<9 else None
            okay=expected is not None and p['role']==ROLES[role] and [pw*16,ph*16]==list(expected)==p['native_size_pixels'] and p['bounds_pixels']==[x*16,y*16,(x+pw)*16,(y+ph)*16] and not(occupied&cells) and all(0<=cx<w and 0<=cy<h for cx,cy in cells)
            occupied|=cells;sizes.add(tuple(p['native_size_pixels']))
            if flags&2:okay &= flags==2 and role==5 and p['component']==0 and cells<=projected;projected_covered|=cells
            else:okay &= flags==0 and cells<=solid and all(labels.get(q)==p['component'] for q in cells);counts[p['component']]+=1;areas[p['component']]+=len(cells)
            expected_map='canopy_solid_branch' if role==5 and not(flags&2) else 'canopy_prefab_%d_map'%role
            okay &= p.get('native_map_symbol')==expected_map
            if not okay:fit_errors.append(p['index'])
        self.check(profile,'planner',name+' every drawing fits unchanged cells without overlap/resizing',not fit_errors and projected_covered==projected and len(scene['placements'])==stats['placements'],fit_errors)
        self.check(profile,'planner',name+' component painted/count accounting exact',all(c['placements']==counts[n] and c['painted_cells']==areas[n] for n,c in records.items()) and sum(areas.values())==stats['painted_solid_cells'])
        features=scene['protected_features'];raw=bytes.fromhex(features['raw_gSpots_hex']);reserved=set()
        for f,offset,flag in (('chest',25,48),('npc',27,49),('relic',29,50),('shrine',42,52),('treasure',44,53),('mouth',46,54)):
            feature=features['features'][f];self.check(profile,'approaches',name+' '+f+' raw spot coordinates',feature['present']==bool(raw[flag]) and feature['position_cells']==list(raw[offset:offset+2]))
            if raw[flag]:
                x,y=raw[offset:offset+2];radius=2 if f in ('shrine','mouth') else 1;reserved|={(x+dx,y+dy) for dy in range(-radius,radius+1) for dx in range(-1,2)}
        torches=[list(raw[31+i*2:33+i*2]) for i in range(raw[39])]
        for x,y in torches:reserved|={(x+dx,y+dy) for dy in range(-1,2) for dx in range(-1,2)}
        reserved={(x,y) for x,y in reserved if 0<=x<w and 0<=y<h}
        self.check(profile,'approaches',name+' raw torches/protected union exact; no projected coverage',torches==features['torches'] and reserved=={tuple(p) for p in features['protected_projection_cells']} and not(projected&reserved))
        context=scene['projected_cell_context'];rom=self.roms[profile];allowed={65535,*(rom.defs['MT_'+n] for n in ('SPARKLE','SPARKLE_WHITE','BLIGHT_MIST'))}
        self.check(profile,'approaches',name+' projections dry passable/noninteractive native context',{tuple(p['cell']) for p in context}==projected and all(p['ground_type']==rom.array('metatile_type')[p['ground_id']]==0 and p['ground_prop']==rom.array('metatile_prop')[p['ground_id']]==0 and p['overlay_id'] in allowed and not any(p['collision_quarters']) for p in context))
        if name.startswith('broad-'):self.check(profile,'planner',name+' real large native tree and unequal support scales',(96,64) in sizes and len(sizes)>=3)
        return {'components':len(groups),'placements':len(scene['placements']),'solid_cells':len(solid),'projected_cells':len(projected),'native_sizes':sorted(sizes)}

    def runtime(self):
        if not self.args.runtime:return {'status':'not_requested'}
        from PIL import Image
        root=Path(self.args.runtime);base=json.loads((root/'v6/capture.json').read_text());baseline={r['name']:r for r in base['captures']};results=[]
        expected={'isolated-small','narrow-arm','broad-healthy','broad-deep','separated-corner'}
        logical=('game_state','area','cell','state','position','z_q16','hp','camera','textbox','rng_state','motion_phase','safe_position','standing_type','equipment','shield_up','item_active')
        fixture=('seed','cell','group','frames','position','target','facing','inputs','physical_contract','final_physical_contract','maze_sha256','initial_progress_sha256','final_progress_sha256','initial_rng','final_rng')
        for profile in (6,*self.args.profiles):
            directory=root/f'v{profile}';path=directory/'capture.json';r=json.loads(path.read_text());rom=self.roms.get(profile) or NativeRom(Path(self.args.frozen)/f'v{profile}');freeze=json.loads((Path(self.args.frozen)/f'v{profile}/freeze.json').read_text())
            self.check(profile,'runtime_provenance','complete final actual run; matching ROM/source',r.get('complete') and not r.get('unfrozen_pilot') and r['passed']==r['total'] and not r['failures'] and r['rom_sha256']==SHA(rom.rom) and r['source_commit']==freeze['source_commit'])
            self.check(profile,'runtime_provenance','held current capture tool',r['capture_tool_sha256']==SHA((GAME/'tools/forest_canopy_adaptive_review.py').read_bytes()))
            for name,digest in r['capture_dependency_sha256'].items():self.check(profile,'runtime_provenance',name+' current dependency',SHA((GAME/'tools'/name).read_bytes())==digest)
            for name,digest in r['frozen_input_sha256'].items():self.check(profile,'runtime_provenance',name+' frozen capture input',SHA((Path(self.args.frozen)/f'v{profile}'/name).read_bytes())==digest)
            rows={row['name']:row for row in r['captures']}
            menu_count=int(profile in (6,19))
            matched_names={n for n,row in baseline.items() if menu_count or row['group']!='menu'}
            self.check(profile,'runtime_coverage','five natural geometries/two motions; shared menu probe on6and19',expected<=set(rows) and set(rows)==matched_names and sum(row['group']=='motion' for row in rows.values())==2 and sum(row['group']=='menu' for row in rows.values())==menu_count and len(rows)==7+menu_count and r['diagnostic_capture_count']==0)
            movies=gifs=frames=0;media={};minimum=cluster=100000;full_hidden=0;cape_count=0;plans={}
            hero_meta,hero=rom.sheet('hero');fx_meta,fx=rom.sheet('bloomfx');fx_pal=rom.array('bloomfx_frame_pal')
            for name,row in rows.items():
                old=baseline[name]
                rng=row['controlled_starting_rng'];reference_rng=old['controlled_starting_rng']
                before=rng['before'];after=rng['after']
                self.check(profile,'runtime_fixture',name+' declared post-generation RNG fixture preserves world/progress',before==after and before['physical_contract']==row['physical_contract'] and before['maze_sha256']==row['maze_sha256'] and before['progress_sha256']==row['initial_progress_sha256'] and rng['assigned_sRand']==rng['actual_sRand_after']==row['initial_rng']==row['initial']['rng_state']==reference_rng['assigned_sRand'])
                self.check(profile,'runtime_semantics',name+' generation, inputs, collision/features and progress match old6',all(row.get(k)==old.get(k) for k in fixture))
                self.check(profile,'runtime_semantics',name+' logical initial/final state and RNG match',all(row[t].get(k)==old[t].get(k) for t in ('initial','final') for k in logical))
                self.check(profile,'runtime_cadence',name+' strict observed update cadence matches old6',row['cadence_observation']['intervals']==old['cadence_observation']['intervals'])
                observations=row['visibility_observations'];frames+=len(observations)
                self.check(profile,'runtime_hardware',name+' one same-scanout hardware/image pair per video frame',len(observations)==row['video_frames'] and all(s['visibility'].get('scanout_start_vcount')==0 and s['visibility'].get('scanout_end_vcount')==160 and s['visibility'].get('scanout_frame_counter')==s['visibility'].get('scanout_end_frame_counter') for s in observations))
                keys=('native_room_mappings','static_BG_bytes_match_ROM','animated_BG_bytes_are_authored_frames','OAM_legal','world_palette_is_authored_phase','actual_hardware_palette_is_authored_phase','selected_OBJ_palette_bytes_match_ROM','resolved_visual_mappings_valid')
                if profile>=19:keys+=('adaptive_native_map_valid','adaptive_placed_map_matches_ROM')
                self.check(profile,'runtime_hardware',name+' resident native world/OAM payloads validated',bool(row['hardware_samples']) and all(all(h.get(k) for k in keys) for h in row['hardware_samples']))
                if profile>=19:plans[name]=self.planner(profile,row)
                gap=set(row.get('menu_resume_hardware_gap',{}).get('ticks',[]))
                for sample in observations:
                    v=sample['visibility'];playing=sample['game_state']==1 and sample['displayed_world_planes'] and sample['tick'] not in gap
                    if not playing:continue
                    if profile>=19:
                        goal=max(12,(v.get('opaque_colored_pixels',0)+3)//4)
                        self.check(profile,'runtime_visibility',name+':'+str(sample['tick'])+' actual native body and displayed character stay recognizable',v.get('body_found') and v.get('guard_exact_native_subset') and v.get('visible_colored_pixels',0)>=goal and v.get('largest_visible_colored_component',0)>=8 and v.get('framebuffer_exact_character_color_pixels',0)>=12 and v.get('framebuffer_exact_character_color_component',0)>=8)
                        minimum=min(minimum,v.get('framebuffer_exact_character_color_pixels',0));cluster=min(cluster,v.get('framebuffer_exact_character_color_component',0));full_hidden+=v.get('framebuffer_exact_character_color_pixels',0)==0
                    cape=v.get('attached_cape')
                    if cape:
                        cape_count+=1;ref=cape['native_frame'];face=ref['face'];phase=ref['phase'];f=rom.defs['F_BLOOMFX_CAPE_'+face+str(phase)];b=rom.defs['F_HERO_CAPE_'+face+str(phase+1)];fs=fx_meta['frame_tiles']*32;hs=hero_meta['frame_tiles']*32
                        self.check(profile,'runtime_cape',name+':'+str(sample['tick'])+' only current native attached garment counts',cape.get('exact_current_native_pose_and_anchor') and cape.get('anchor_projection_delta')==[0,0] and cape['VRAM_sha256']==SHA(fx[f*fs:(f+1)*fs]) and v['body_VRAM_sha256']==SHA(hero[b*hs:(b+1)*hs]) and cape['OAM']['pal']==ref['palette']==fx_pal[f] and ref['frame']==f)
                paths=set(row['native_frames'])|{row['image']}
                for key in ('after_image','filmstrip','video','gif'):
                    if row.get(key):paths.add(row[key])
                for key in ('action_keyframes','phase_keyframes'):
                    paths.update(entry['path'] for entry in row.get(key,[]))
                for key in ('worst_visibility_keyframe','displayed_character_keyframe'):
                    if row.get(key):paths.add(row[key]['path'])
                if row.get('resident_BG2_layer'):paths.add(row['resident_BG2_layer']['path'])
                missing=[]
                for relative in paths:
                    p=safe_file(directory,relative)
                    if not p.is_file():missing.append(relative)
                    else:media[relative]=SHA(p.read_bytes())
                self.check(profile,'runtime_media',name+' every referenced native/viewing artifact exists',not missing,missing)
                self.check(profile,'runtime_media',name+' native still dimensions',all(Image.open(safe_file(directory,p)).size==(240,160) for p in row['native_frames']))
                if row.get('video'):
                    movies+=1;stream=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,nb_read_frames','-of','json',str(safe_file(directory,row['video']))],text=True))['streams'][0]
                    rate=Fraction(262144,4389);self.check(profile,'runtime_media',name+' nativeGBA-rate exact2x movie frames',stream['width']==480 and stream['height']==320 and Fraction(stream['r_frame_rate'])==rate and int(stream['nb_read_frames'])==row['video_frames'] and abs(row['video_fps']-float(rate))<1e-8)
                if row.get('gif'):
                    gifs+=1;self.check(profile,'runtime_media',name+' exact sampled native colors and GBA clock GIF',row['gif_metadata']['exact_palette'] and gif_matches(safe_file(directory,row['gif']),safe_file(directory,row['all_frames']),row['video_frames'],row['video_fps']))
            results.append({'profile':profile,'report_sha256':SHA(path.read_bytes()),'rom_sha256':SHA(rom.rom),'contexts':len(rows),'movies':movies,'exact_gifs':gifs,'observed_video_frames':frames,'minimum_displayed_character_colored_pixels':minimum if profile>=19 else None,'minimum_displayed_character_component':cluster if profile>=19 else None,'fully_hidden_new_character_frames':full_hidden if profile>=19 else None,'validated_attached_cape_frames':cape_count,'media_manifest_sha256':SHA(json.dumps(media,sort_keys=True).encode()),'planner_cases':plans})
        return {'profiles':results,'contexts':sum(r['contexts'] for r in results),'movies':sum(r['movies'] for r in results),'exact_gifs':sum(r['exact_gifs'] for r in results),'observed_video_frames':sum(r['observed_video_frames'] for r in results),'baseline':'Preserved old forest study6, not production0.','limits':'Finite naturally generated room recordings, not exhaustive animation/world/CPU proof.'}

    def source_gallery(self):
        if not self.args.source_gallery:return {'status':'not_requested'}
        from PIL import Image,ImageSequence
        root=Path(self.args.source_gallery);manifest_path=root/'source-manifest.json';manifest=json.loads(manifest_path.read_text())
        self.check('gallery','source_provenance','held source exporter and frozen revision',manifest['tool_sha256']==SHA((GAME/'tools/forest_canopy_adaptive_gallery.py').read_bytes()) and {manifest['source_commit']}=={p['source_commit'] for p in self.profiles})
        for name,digest in manifest['source_input_sha256'].items():self.check('gallery','source_provenance',name+' current source bytes',SHA((GAME/name).read_bytes())==digest)
        for name,entry in manifest['files'].items():
            path=safe_file(root,name);self.check('gallery','source_files',name+' exact published bytes',path.is_file() and path.stat().st_size==entry['bytes'] and SHA(path.read_bytes())==entry['sha256'])
        def rgba(record,colors):
            image=Image.new('RGBA',tuple(record['size']));values=[]
            for ink in bytes.fromhex(record['pixels']):
                c=colors[ink];values.append(((c&31)<<3,((c>>5)&31)<<3,((c>>10)&31)<<3,255 if ink else 0))
            image.putdata(values);return image
        def on_background(image):
            out=Image.new('RGB',image.size,(16,24,32));out.paste(image,(0,0),image);return out
        native_count=0
        for profile in self.args.profiles:
            style=profile-18;source=self.sources[profile];base=root/f'variant-{style:02}';catalog=json.loads((base/'native-manifest.json').read_text());board=Image.open(base/'native-roles-source.png').convert('RGB')
            records={r['role']:r for r in source['prefabs']+source['authored_groups']};records['branch-solid']=source['solid_branch']
            self.check(profile,'source_coverage','all nine prefabs/four groups/separate solid limb exported',len(catalog['entries'])==14 and {r['role'] for r in catalog['entries']}==set(records))
            for entry in catalog['entries']:
                record=records[entry['role']];native_count+=1
                with Image.open(base/entry['native_indexed']) as indexed:
                    self.check(profile,'source_native',entry['role']+' exact indexed native file',indexed.mode=='P' and indexed.size==tuple(record['size']) and indexed.tobytes()==bytes.fromhex(record['pixels']))
                for stage,key in ((0,'native_healthy'),(3,'native_deep')):
                    expected=rgba(record,source['stage_colors'][stage][0]);actual=Image.open(base/entry[key]).convert('RGBA')
                    self.check(profile,'source_native',entry['role']+' stage'+str(stage)+' literal native palette PNG',actual.size==expected.size and actual.tobytes()==expected.tobytes())
                expected=on_background(rgba(record,source['stage_colors'][3][0]))
                for key,scale in (('catalog_native_rect',1),('catalog_inspection_rect',2)):
                    x,y,w,h=entry[key];image=expected if scale==1 else expected.resize((expected.width*2,expected.height*2),Image.Resampling.NEAREST)
                    self.check(profile,'source_panels',entry['role']+' '+key+' exact native/integer pixels',image.size==(w,h) and board.crop((x,y,x+w,y+h)).tobytes()==image.tobytes())
            hero=records['hero'];frames=[]
            for phase in range(4):
                frame=Image.open(base/f'hero-palette-phase-{phase}-source.png').convert('RGB');frames.append(frame)
                for stage in range(4):
                    expected=on_background(rgba(hero,source['stage_colors'][stage][phase]));x=stage*120+5;y=55
                    self.check(profile,'source_palette',f'hero stage{stage}phase{phase} exact source panel',frame.crop((x,y,x+96,y+64)).tobytes()==expected.tobytes())
            with Image.open(base/'hero-palette-pulse-source.gif') as gif:
                decoded=[(f.convert('RGB').copy(),f.info.get('duration')) for f in ImageSequence.Iterator(gif)]
            self.check(profile,'source_gif','exact four-frame source palette GIF with inspection holds',len(decoded)==4 and all(d.tobytes()==f.tobytes() and hold==180 for (d,hold),f in zip(decoded,frames)))
        comparison=json.loads((root/'source-comparison-manifest.json').read_text());board=Image.open(root/'native-hero-directions-source.png').convert('RGB')
        for panel in comparison['hero_panels']:
            profile=panel['style']+18
            if profile not in self.sources:continue
            source=self.sources[profile];hero=source['prefabs'][4];expected_rgba=rgba(hero,source['stage_colors'][panel['stage']][0]);expected=on_background(expected_rgba);x,y,w,h=panel['rect']
            self.check(profile,'source_panels','hero comparison native stage'+str(panel['stage']),panel['rgba_sha256']==SHA(expected_rgba.tobytes()) and (w,h)==expected.size and board.crop((x,y,x+w,y+h)).tobytes()==expected.tobytes())
            if panel['stage']==0:
                deep=on_background(rgba(hero,source['stage_colors'][3][0])).resize((192,128),Image.Resampling.NEAREST)
                self.check(profile,'source_panels','hero comparison exact2x deep inspection',board.crop((x+217,y,x+409,y+128)).tobytes()==deep.tobytes())
        return {'manifest_sha256':SHA(manifest_path.read_bytes()),'source_commit':manifest['source_commit'],'native_images':native_count,'hashed_files':len(manifest['files']),'exact_source_palette_GIFs':len(self.args.profiles),'limits':'Native assets/catalog/comparison/palette panels verified. Recorded-plan source figures are labelled schematic explanations, not actual framebuffers; their files are hash bound here.'}

    def run(self):
        self.equal('source','scope','generation source unchanged from pre-canopy reference',subprocess.check_output(['git','show',GEN_REFERENCE+':bartgame/src/roomgen.c'],cwd=GAME),(GAME/'src/roomgen.c').read_bytes())
        for name in ('player','actor','enemy','boss','objects','game','world','util'):
            file='src/'+name+'.c'
            self.equal('source','scope',file+' gameplay/action source unchanged before adaptive pass',subprocess.check_output(['git','show',SOURCE_REFERENCE+':bartgame/'+file],cwd=GAME),(GAME/file).read_bytes())
        for profile in self.args.profiles:
            rom=NativeRom(Path(self.args.frozen)/f'v{profile}');freeze=self.provenance(profile,rom);self.roms[profile]=rom
            source=json.loads(subprocess.check_output([sys.executable,__file__,'--export-source',str(profile),'--base-source',self.args.base_source],cwd=GAME,text=True));self.sources[profile]=source
            result=self.native(profile,rom,source);self.profiles.append({'profile':profile,'label':source['label'],'source_commit':freeze['source_commit'],'rom_sha256':SHA(rom.rom),'frozen_input_sha256':{n:SHA((Path(self.args.frozen)/f'v{profile}'/n).read_bytes()) for n in ('bartgame.gba','bartgame.map','assets.h','freeze.json')},**result})
        for profile in self.args.controls:
            actual=SHA((Path(self.args.controls_root)/f'v{profile}/bartgame.gba').read_bytes());self.check(profile,'historical','whole historical ROM byte-identical',actual==HISTORICAL[profile],{'expected_sha256':HISTORICAL[profile],'actual_sha256':actual})
        source_gallery=self.source_gallery();runtime=self.runtime();failures=[r for r in self.rows if not r['passed']]
        dependencies=('tools/forest_v3_audit.py','tools/forest_v2_audit.py','tools/forest_concept_audit.py','tools/sewer_concept_audit.py','tools/enemy_study_audit.py')
        report={'method':__doc__,'source_commits':sorted({r['source_commit'] for r in self.profiles}),'auditor_sha256':SHA(Path(__file__).read_bytes()),'audit_dependency_sha256':{p:SHA((GAME/p).read_bytes()) for p in dependencies},'base_source_sha256':SHA(Path(self.args.base_source).read_bytes()),'profiles':self.profiles,'source_gallery':source_gallery,'runtime':runtime,'historical_controls':[r for r in self.rows if r['group']=='historical'],'passed':len(self.rows)-len(failures),'total':len(self.rows),'failures':failures,'checks_by_group':dict(Counter(r['group'] for r in self.rows)),'aesthetic_verdict':'Not established by this technical audit. See independent actual-room critique.','limits':'No unchanged generator corpus rerun; finite actual observations; source green percentages are not screen quotas.'}
        if self.args.details:report['checks']=self.rows
        out=Path(self.args.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'total':report['total'],'failures':len(failures),'report':str(out)}));return bool(failures)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--frozen',default=str(WORK/'frozen'));p.add_argument('--controls-root');p.add_argument('--profiles',type=int,nargs='+',default=list(range(19,29)));p.add_argument('--controls',type=int,nargs='*',default=list(range(19)))
    p.add_argument('--base6');p.add_argument('--base-source',default=str(WORK/'audit/base6-source.json'));p.add_argument('--inventory',default=str(GAME.parent/'art-review/forest-concepts/validation/inventory.json'));p.add_argument('--export-source',type=int)
    p.add_argument('--runtime');p.add_argument('--source-gallery');p.add_argument('--out',default=str(WORK/'audit/final-audit.json'));p.add_argument('--details',action='store_true')
    args=p.parse_args();args.controls_root=args.controls_root or args.frozen;args.base6=args.base6 or str(Path(args.controls_root)/'v6')
    if not Path(args.base_source).exists():
        data=subprocess.check_output([sys.executable,str(GAME/'tools/forest_v2_audit.py'),'--export-source','6','--inventory',args.inventory],cwd=GAME,text=True);Path(args.base_source).parent.mkdir(parents=True,exist_ok=True);Path(args.base_source).write_text(data)
    if args.export_source is not None:export(args.export_source,args.base_source);return 0
    return Audit(args).run()
if __name__=='__main__':raise SystemExit(main())

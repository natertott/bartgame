#!/usr/bin/env python3
"""Independent focused canopy source/native and scope audit.

Uses direct new painters with independently enumerated valid adjacency cases,
then decodes the frozen ROM using native GBA map entries/flip bits/palettes.
No generation corpus is repeated: roomgen source is separately byte checked.
"""
import argparse, copy, hashlib, json, os, re, struct, subprocess, sys
from pathlib import Path
GAME=Path(__file__).resolve().parents[1]
ROOT=GAME
WORK=Path('/workspace/setup/forest-canopy-v3')
sys.path.insert(0,str(GAME/'tools'))
from forest_v2_audit import Audit as PriorAudit, valid_adjacencies, BANKS, GLITTER
from sewer_concept_audit import NativeRom, decode_metatile, decode_sprite
from forest_concept_audit import native_palette,native_image,LEGAL_CANVASES
from enemy_study_audit import Audit as EnemyAudit
SHA=lambda b:hashlib.sha256(b).hexdigest()
# Whole-ROM identities recorded before this canopy pass.
HISTORICAL_SHA={0: '9330a44a4e27d99606a757134aa41a62adb122a74315c400e1ad3427048c8661', 1: 'aa1dda5a1fe8bb31982d7f5beaeba7497011badccc34900037ef687cb0bc3067', 2: '50f559ec16aaa2e08bb446349c8a8e122ff5ec6b983cea6b32a0b2d5be3cc515', 3: '85238cd938ef2778f651bf005eb9655216569d8194f9aefe81cc9e3c70f85673', 4: '411035db3a288fabe0aef2f3cabc21199be324d1445de5c6a8323942cda44214', 5: '0904dd78511be6df01adb8e49e40064b7a6d95b4c07368e4a0699077d003e8a5', 6: 'fc8e92f92a4aa43aa5cc56c0caff7a6dc1394f21dc356e7830ef9a7e07f234a1', 7: '3fe6143a9c9de8ccb79248e20b69b199aa462078c92827e71805ebf5826e11df', 8: 'c72c07bf22bd15eaf3898e1fb0a75eabb7b2dc4c85ead74e68ba30a5f181e8f9', 9: '6e5af6e3ec8e960f2e11cbd485a4c6e8d11f4e6eca202d46f15246cc3cca7538', 10: '3876a966293a6cfd68eb39f881dd107b1da4bc14f0b764223712251321784d07'}
CANOPY_NAMES={'canopy','canopy2','canopy_s','canopy_n','canopy_blight','canopy_blight2','canopy_lantern','canopy_glint','blight_wall','blight_wall2','blight_wall_lit','dead_tree','forest_blight_dead_tree'}
PREFIXES=('tree_top_','tree_mid_','tree_trunk_','tree2_','gtree_','gtree2_','btree_','birch_','fir_','sicktree_','forest_blight_tree','forest_canopy','f2_canopy_','f2_fringe_')
def owned(n):return n in CANOPY_NAMES or n.startswith(PREFIXES)
def export(profile,base):
    os.environ['BART_FOREST']=str(profile)
    sys.path.insert(0,str(GAME/'art'))
    import forest_concepts_v3_terrain as artist
    import palettes
    local=profile-10
    result=copy.deepcopy(json.loads(Path(base).read_text()))
    result.update(profile=profile,local_variant=local)
    result['bg_palettes']={n:native_palette(colors) for n,colors in palettes.BG_PALETTES}
    for name,row in result['tiles'].items():
        if name.startswith('f2_canopy_'):
            kind,quad,end=name[len('f2_canopy_'):].split('_');mask,corners=map(lambda c:int(c,16),end)
            frames=[artist.paint_adjacency(('canopy' if int(kind)==0 else 'blight_wall')+'@q'+quad,mask,corners,0,local)]
        elif name.startswith('f2_fringe_'):
            kind,mask=name[len('f2_fringe_'):].split('_')
            frames=[artist.fringe('canopy' if int(kind)==0 else 'blight_wall',int(mask,16),local)]
        elif owned(name):
            frames=[artist.paint(name,p,local) for p in range(len(row['frames']))]
        else:continue
        assert len({b for _,b in frames})==1,(name,'changing bank')
        row['frames']=[native_image(im,(16,16)).hex() for im,_ in frames]
        row['bank']=frames[0][1]
    result['pulse_palettes']={n:[native_palette(p) for p in phases] for n,phases in artist.pulse_palettes(local).items()}
    result['pulse_indices']={n:list(indices) for n,indices in artist.PULSE_INDICES.items()}
    print(json.dumps(result,separators=(',',':')))
class Audit(PriorAudit):
    def __init__(self,args):
        self.args=args;self.rows=[];self.profiles=[];self.budgets=[]
        self.inv=json.loads(Path(args.inventory).read_text());self.specs={x['name']:x for x in self.inv['tiles']}
        self.base=NativeRom(args.baseline)
    def native(self, v, rom, source):
        counts = {}; changes = 0
        for bank in (*BANKS,'forest_obj_foliage','forest_obj_stone'):
            slot=rom.defs['PAL_BG_'+bank.upper()]
            self.equal(v,'native_palette',bank+' complete authored global bank',
                       struct.pack('<16H',*source['bg_palettes'][bank]),rom.array('pal_bg')[slot*32:(slot+1)*32])
        self.check(v, 'direct_coverage', 'all 461 retained owned IDs plus direct topology aliases',
                   set(source['tiles']) == (set(self.inv['required']['bg_names'])-GLITTER) |
                   {r['name'] for r in source['topology']})
        old_names = set(self.base.tile_ids)
        appended = {n.upper() for n in source['tiles'] if n.upper() not in old_names}
        self.check(v, 'identifiers', 'only approved new metatile IDs appended', set(rom.tile_ids)-old_names == appended)
        for offset,alias in enumerate(source['topology']):
            self.check(v,'identifiers',alias['name']+' stable append-order ID',
                       rom.tile_ids[alias['name'].upper()]==self.base.defs['METATILE_COUNT']+offset)
        for name, number in self.base.tile_ids.items():
            self.check(v, 'identifiers', name+' old ID stable', rom.tile_ids.get(name) == number)
        for field, key in [('metatile_type','type_id'), ('metatile_coll','coll'), ('metatile_prop','prop'), ('metatile_glitter','glitter')]:
            before, current = self.base.array(field), rom.array(field)
            self.equal(v, 'physical', field+' complete original prefix exact', before, current[:len(before)])
            for alias in source['topology']:
                index = rom.tile_ids[alias['name'].upper()]; parent = self.base.tile_ids[alias['parent'].upper()]
                expected = alias.get('glitter', before[parent]) if field == 'metatile_glitter' else before[parent]
                self.check(v, 'physical_alias', alias['name']+'.'+field+' semantic parent', current[index] == expected)
        overhead=rom.array('forest_v2_overhead')
        # New profiles replace the old recoil exception, so its unused flag
        # table may be garbage-collected. Never invent a native payload.
        lowfringe=rom.array('forest_v2_low_fringe') if 'forest_v2_low_fringe' in rom.sections else None
        if lowfringe is None:
            self.check(v,'native_lookup','unused legacy low-fringe data and consumer are both unlinked',
                       'room_recoil_fringe_front' not in rom.symbols)
        parents=None
        if 'forest_v2_visual_parent' in rom.sections:
            data=rom.array('forest_v2_visual_parent');parents=struct.unpack('<%dH'%(len(data)//2),data)
        else:
            # This generated documentation table has no C consumer and is
            # garbage-collected. Physical semantics are checked against the
            # parent's actual native type/collision/prop/glitter words above.
            referenced=any('forest_v2_visual_parent' in p.read_text() for p in (ROOT/'src').glob('*.c'))
            self.check(v,'native_lookup','unlinked parent metadata has no gameplay consumer',not referenced,
                       'Unused generated table removed by linker; no native payload is claimed.')
        for alias in source['topology']:
            index=rom.tile_ids[alias['name'].upper()]
            if parents is not None:
                self.check(v,'physical_alias',alias['name']+' exact visual semantic parent lookup',parents[index]==rom.tile_ids[alias['parent'].upper()])
            self.check(v,'physical_alias',alias['name']+' correct foreground/depth classification',
                       overhead[index]==int(alias['family'] in ('canopy','fringe','overhead_root_arch')))
            if lowfringe is not None:
                self.check(v,'physical_alias',alias['name']+' low-fringe presentation flag',lowfringe[index]==int(alias['family']=='fringe'))
        def eligible(mask):
            return sum((1<<q) for q,sides in enumerate((9,3,6,12)) if not(mask&sides))
        canopy=[]
        for kind in range(2):
            for quadrant in range(4):
                for mask in range(16):
                    for corners in range(16):
                        canopy.append(rom.tile_ids[f'F2_CANOPY_{kind}_{quadrant}_{mask:X}{corners&eligible(mask):X}'])
        self.equal(v,'native_lookup','all2048canopy topology table entries independently resolved',
                   struct.pack('<2048H',*canopy),rom.array('forest_v2_canopy_alias'))
        water=[rom.tile_ids[f'F2_WATER_{m:X}{c&eligible(m):X}'] for m in range(16) for c in range(16)]
        self.equal(v,'native_lookup','all256water topology table entries independently resolved',struct.pack('<256H',*water),rom.array('forest_v2_water_alias'))
        fringe=[65535 if m==0 else rom.tile_ids[f'F2_FRINGE_{kind}_{m:X}'] for kind in range(2) for m in range(16)]
        self.equal(v,'native_lookup','all32fringe table entries independently resolved',struct.pack('<32H',*fringe),rom.array('forest_v2_fringe_alias'))
        self.equal(v,'native_lookup','two isolated specialwater bindings',
                   struct.pack('<2H',rom.tile_ids['F2_WATER_LILY_ISOLATED'],rom.tile_ids['F2_WATER_FOAM_ISOLATED']),rom.array('forest_v2_water_isolated'))
        healthy={'canopy','canopy2','canopy_s','canopy_n','canopy_lantern','canopy_glint',*(f'forest_canopy{i}' for i in range(4))}
        sick={'canopy_blight','canopy_blight2','blight_wall','blight_wall2','blight_wall_lit'}
        connectors={f'forest_blight_tree{i}' for i in range(6)}
        ordered=[n.lower() for n,i in sorted(rom.tile_ids.items(),key=lambda r:r[1])]
        classes=bytes(1 if n in healthy else 2 if n in sick else 3 if n in connectors else 0 for n in ordered)
        self.equal(v,'native_lookup','complete logical canopy/connector classification',classes,rom.array('forest_v2_canopy_kind'))
        waterclasses=bytes(2 if n=='water_lily' else 3 if n=='water_foam' else
                           1 if n=='water' or n.startswith('water_') else
                           4 if n in ('waterfall','bridge','bridge_v') or n.startswith('raft_') else 0 for n in ordered)
        self.equal(v,'native_lookup','complete logical water/connectivity classification',waterclasses,rom.array('forest_v2_water_kind'))
        special=bytes(int(n in connectors or n in ('dead_tree','forest_blight_dead_tree')) for n in ordered)
        self.equal(v,'native_lookup','all special tree bindings',special,rom.array('forest_v2_special_tree'))
        crowns=set()
        for group in self.inv['groups']:
            if group['role']=='tree':
                count=9 if len(group['members'])==12 else 4
                crowns.update(group['members'][:count])
        self.check(v,'native_lookup','alloriginal authored tree crown depth flags',
                   all(overhead[i]==int(n.lower() in crowns) for n,i in self.base.tile_ids.items()))
        if lowfringe is not None:
            self.equal(v,'native_lookup','original IDs never acquire low-fringe exception',bytes(self.base.defs['METATILE_COUNT']),lowfringe[:self.base.defs['METATILE_COUNT']])
        if parents is not None:
            self.check(v,'native_lookup','alloriginal IDs retain identity semantic lookup',all(parents[i]==i for i in range(self.base.defs['METATILE_COUNT'])))
        for area in ('forest','myst'):
            ts = rom.tileset(area); frames = 0
            for name, authored in source['tiles'].items():
                # Original membership is independently frozen. New render-only
                # topology pictures are forest-local unless explicitly mapped.
                if name in self.specs and area not in self.specs[name]['areas']:continue
                if name not in self.specs and area != 'forest':continue
                decoded = decode_metatile(rom, ts, name)
                parent = self.specs[authored['parent']]
                self.check(v, 'native', area+'.'+name+' frame count', len(decoded['frames']) == len(authored['frames']))
                speed = parent['anim_speed'] if len(authored['frames']) > 1 else None
                self.check(v, 'native', area+'.'+name+' declared clock', decoded['speed'] == speed)
                palette = source['bg_palettes'][authored['bank']]
                for q, entry in enumerate(decoded['entries']):
                    bank = entry >> 12
                    self.equal(v, 'material', area+'.'+name+' quadrant'+str(q)+' exact bank',
                               struct.pack('<16H',*palette), ts['palettes'][bank*32:(bank+1)*32])
                for phase, (expected, (indices, colors)) in enumerate(zip(authored['frames'],decoded['frames'])):
                    pixels = bytes.fromhex(expected); label = area+'.'+name+':'+str(phase)
                    self.equal(v, 'native', label+' direct pixels vs ROM nibbles', pixels, indices)
                    self.equal(v, 'native', label+' direct RGB555 base material',
                               struct.pack('<256H',*[palette[p] if p else 0x8000 for p in pixels]), colors)
                    frames += 1
            counts[area] = frames
        owned = {(s,f) for s, frames in source['sprites'].items() for f in frames}
        for sheet, images in source['sprites'].items():
            meta, raw = rom.sheet(sheet); stride = meta['frame_tiles']*32
            for name, image in images.items():
                index = rom.defs['F_'+sheet.upper()+'_'+name.upper()]
                actual = decode_sprite(raw[index*stride:(index+1)*stride],meta['width'],meta['height'])
                self.equal(v, 'native_sprite', sheet+'.'+name+' direct pixels', bytes.fromhex(image['pixels']), actual)
                self.check(v, 'native_sprite', sheet+'.'+name+' legal canvas', image['canvas'] == [meta['width'],meta['height']] and tuple(image['canvas']) in LEGAL_CANVASES)
                if sheet == 'face':
                    self.equal(v, 'portrait_palette', name+' direct native palette',
                               struct.pack('<16H',*source['portrait_palettes'][name]),rom.array('pal_face')[index*32:(index+1)*32])
                else:
                    route = rom.array(sheet+'_frame_pal')[index] if sheet+'_frame_pal' in rom.sections else meta['pal']
                    self.check(v, 'sprite_material', sheet+'.'+name+' direct OBJ route', route == rom.defs['PAL_OBJ_'+image['bank'].upper()])
        for sheet in self.inv['sheets']:
            name = sheet['name']; a, old = self.base.sheet(name); b, raw = rom.sheet(name)
            expected = dict(a)
            if name == 'interactivechest':expected['tile_count'] += a['frame_tiles']*2
            self.check(v, 'sprite_contract', name+' exact canvas/shape/approved count', expected == b)
            stride = a['frame_tiles']*32
            for frame in sheet['frames']:
                if (name, frame['name']) not in owned:
                    i = frame['id']; self.equal(v, 'protected_sprite', name+'.'+frame['name']+' exact pixels', old[i*stride:(i+1)*stride],raw[i*stride:(i+1)*stride])
                self.check(v, 'identifiers', name+'.'+frame['name']+' original frame ID stable',rom.defs['F_'+name.upper()+'_'+frame['name'].upper()] == frame['id'])
        self.check(v, 'identifiers', 'only appended landmark sheet', set(rom.sheet_ids)-set(self.base.sheet_ids) == {'forestlandmark'})
        for name,index in self.base.sheet_ids.items():
            self.check(v,'identifiers',name+' original sheet ID stable',rom.sheet_ids[name]==index)
        landmark,_=rom.sheet('forestlandmark')
        self.check(v,'sprite_contract','landmark exact four16x32 native frames, one8tile streamed canvas',
                   landmark['width']==16 and landmark['height']==32 and landmark['frame_tiles']==8 and landmark['tile_count']==32 and landmark['shape']==2 and landmark['size']==2)
        self.check(v,'identifiers','landmark sheet appended after alloriginals',rom.sheet_ids['forestlandmark']==self.base.defs['SHEET_COUNT'])
        self.check(v, 'identifiers', 'new wooden B pair appended as6/7',rom.defs['F_INTERACTIVECHEST_WOODEN_B_CLOSED'] == 6 and rom.defs['F_INTERACTIVECHEST_WOODEN_B_OPEN'] == 7)
        for index,name in enumerate(('relic','shrine_available','shrine_spent','keylock')):
            self.check(v,'identifiers','landmark '+name+' stable declared frame ID',rom.defs['F_FORESTLANDMARK_'+name.upper()]==index)
        for tile,frame in [('bush','bush'),('rock_small','rock'),('boulder','boulder'),('myst_pot','pot')]:
            a=source['tiles'][tile];b=source['sprites']['lift'][frame]
            self.check(v,'carry_identity',tile+' exact floor/carried native pixels',a['frames'][0]==b['pixels'])
            slot=rom.defs['PAL_OBJ_'+b['bank'].upper()]
            self.equal(v,'carry_identity',tile+' exact floor/carried material',
                       struct.pack('<16H',*source['bg_palettes'][a['bank']]),rom.array('pal_obj')[slot*32:(slot+1)*32])
        return {'unique_BG_IDs':len(source['tiles']), 'unique_BG_frames':sum(len(t['frames']) for t in source['tiles'].values()),
                'topology_IDs':len(source['topology']), 'OBJ_frame_instances':len(owned), 'area_frame_instances':counts}

    def scope(self,profile,rom,source,base_source,base6):
        self.equal(profile,'scope','src/roomgen.c unchanged from pre-canopy0170bddf',subprocess.check_output(['git','show','0170bddf1b636afb0d251ba79536f602938d9ce8:bartgame/src/roomgen.c'],cwd=GAME), (GAME/'src/roomgen.c').read_bytes())
        self.check(profile,'scope','metatile IDs exactly prior6',rom.tile_ids==base6.tile_ids)
        self.check(profile,'scope','sheet IDs exactly prior6',rom.sheet_ids==base6.sheet_ids)
        for key in ('metatile_type','metatile_coll','metatile_prop','metatile_glitter','pal_obj','pal_face'):
            self.equal(profile,'protected',key+' exact prior6',base6.array(key),rom.array(key))
        for name in base6.sheet_ids:
            am,a=base6.sheet(name);bm,b=rom.sheet(name)
            self.check(profile,'protected',name+' exact native sheet metadata',am==bm)
            self.equal(profile,'protected',name+' complete native pixel bytes',a,b)
        for name,colors in base_source['bg_palettes'].items():
            self.check(profile,'protected_palette',name+' complete original RGB555 ramp unchanged',source['bg_palettes'].get(name)==colors)
        for name,row in source['tiles'].items():
            if owned(name):continue
            before=base_source['tiles'][name]
            self.check(profile,'noncanopy',name+' exact source material/frame payload',row['frames']==before['frames'] and row['bank']==before['bank'])
        for name,phases in base_source['pulse_palettes'].items():
            self.check(profile,'protected_pulse',name+' original native pulse unchanged',source['pulse_palettes'].get(name)==phases)
        self.check(profile,'scope','only one dedicated canopy BG palette appended',set(source['bg_palettes'])-set(base_source['bg_palettes'])=={'canopy3_blight'})
        colors=source['bg_palettes']['canopy3_blight']
        green={i for i,c in enumerate(colors) if i and ((c>>5)&31)>(c&31) and ((c>>5)&31)>((c>>10)&31)}
        macro=[]
        for q in range(4):macro.extend(bytes.fromhex(source['tiles'][f'f2_canopy_1_{q}_00']['frames'][0]))
        painted=sum(p!=0 for p in macro);green_count=sum(p in green for p in macro)
        self.check(profile,'living_canopy','full32px infected crown keeps roughly20% living green',0.15<=green_count/painted<=0.28,{'green_pixels':green_count,'painted_pixels':painted,'green_percent':round(green_count*100/painted,3),'scope':'one complete full32px macro, not a whole-room quota'})
        for q in range(4):
            for mask,corners in valid_adjacencies():
                name=f'f2_canopy_1_{q}_{mask:x}{corners:x}';pixels=bytes.fromhex(source['tiles'][name]['frames'][0]);count=sum(p in green for p in pixels)
                self.check(profile,'living_canopy',name+' preserves a visible green leaf cluster',count>=8,{'green_pixels':count})
        for area in ('forest','myst','sewer'):
            ts=rom.tileset(area)
            self.check(profile,'budget',area+' legal <=1024tiles <=12worldbanks <=255animations',ts['tile_count']<=1024 and ts['palette_count']<=12 and len(ts['animations'])<=255,{k:ts[k] for k in ('tile_count','palette_count')})
            for name,before in base_source['tiles'].items():
                if owned(name):continue
                if name in self.specs and area not in self.specs[name]['areas']:continue
                if name not in self.specs and area!='forest':continue
                a=decode_metatile(base6,base6.tileset(area),name);b=decode_metatile(rom,ts,name)
                self.check(profile,'noncanopy_native',area+'.'+name+' exact native color and clock',a['frames']==b['frames'] and a['speed']==b['speed'])
    def visibility_metadata(self,profile,rom):
        meta,raw=rom.sheet('hero');stride=meta['frame_tiles']*32
        count=meta['tile_count']//meta['frame_tiles']
        table=rom.array('forest_v3_body_visibility')
        self.check(profile,'visibility_metadata','one five-halfword row per unchanged32x32 body frame',len(table)==count*10 and meta['width']==32 and meta['height']==32 and count==rom.defs['SHEET_HERO_FRAMES'])
        pal=rom.defs['PAL_OBJ_HERO'];colors=struct.unpack_from('<16H',rom.array('pal_obj'),pal*32)
        colored={i for i,c in enumerate(colors) if i and max(c&31,(c>>5)&31,(c>>10)&31)>=5 and (c&31)+((c>>5)&31)+((c>>10)&31)>=10}
        def component(pixels,cut):
            remaining={i for i,p in enumerate(pixels) if i//32>=cut and p in colored};largest=0
            while remaining:
                seed=remaining.pop();part={seed};todo=[seed]
                while todo:
                    at=todo.pop();x=at%32;y=at//32
                    for n in (at-32 if y>cut else -1,at+32 if y<31 else -1,at-1 if x else -1,at+1 if x<31 else -1):
                        if n in remaining:remaining.remove(n);part.add(n);todo.append(n)
                largest=max(largest,len(part))
            return largest
        for frame in range(count):
            row=struct.unpack_from('<5H',table,frame*10);cut,total,lower,ctotal,clower=row
            pixels=decode_sprite(raw[frame*stride:(frame+1)*stride],32,32)
            actual_total=sum(p!=0 for p in pixels);actual_colored=sum(p in colored for p in pixels)
            tail=pixels[min(cut,32)*32:];actual_lower=sum(p!=0 for p in tail);actual_clower=sum(p in colored for p in tail)
            self.check(profile,'visibility_metadata',f'frame{frame} native source counts and legal cutoff',0<=cut<32 and (total,lower,ctotal,clower)==(actual_total,actual_lower,actual_colored,actual_clower))
            og=min(actual_total,max(48,(actual_total+2)//3));cg=min(actual_colored,max(24,(actual_colored+2)//3));requested=min(12,actual_colored)
            available=component(pixels,0);goal=min(requested,available);cluster=component(pixels,cut)
            full_exception=available<requested
            self.check(profile,'visibility_metadata',f'frame{frame} meaningful protected source portion',actual_lower>=og and actual_clower>=cg and cluster>=goal,{'cutoff':cut,'opaque':actual_lower,'opaque_goal':og,'colored':actual_clower,'colored_goal':cg,'largest_colored_cluster':cluster,'requested_cluster_goal':requested,'available_source_cluster':available,'effective_cluster_goal':goal,'tiny_source_exception':full_exception})
            if full_exception:
                self.check(profile,'visibility_metadata',f'frame{frame} tiny disconnected original pose protected in full',actual_lower==actual_total and actual_clower==actual_colored,{'reason':'FALL_3 has four colored pixels in two disconnected pairs; unchanged source cannot supply a four-pixel colored component'})
            unnecessary=False
            for farther_cut in range(cut+1,32):
                farther=pixels[farther_cut*32:];op=sum(p!=0 for p in farther);co=sum(p in colored for p in farther)
                if op==actual_lower:continue  # excluding empty rows does not change any protected source pixel
                if op>=og and co>=cg and component(pixels,farther_cut)>=goal:unnecessary=True;break
            self.check(profile,'visibility_metadata',f'frame{frame} excludes unnecessary extra source pixels',not unnecessary)
            if actual_total==0:self.check(profile,'visibility_metadata',f'frame{frame} legitimate blank pose stays empty',actual_lower==0 and actual_clower==0)
        return {'frames':count,'row_bytes':10,'table_sha256':SHA(table),'criterion':'native source counts plus independent four-connected component and minimal-row proof; actual framebuffer visibility checked separately'}
    def source_gallery(self, root):
        from PIL import Image, ImageSequence
        root=Path(root);manifest=json.loads((root/'source-manifest.json').read_text())
        self.check('source','source_provenance','declared final game/art revision',manifest['source_commit']==self.profiles[0]['source_commit'] and manifest['status']=='FINAL FROZEN SOURCE')
        self.check('source','source_provenance','current source exporter hash',manifest['review_tool_sha256']==SHA((GAME/'tools/forest_v3_gallery.py').read_bytes()))
        for name,expected in manifest['current_source_input_sha256'].items():
            self.check('source','source_provenance',name+' exact current source input',SHA((GAME/name).read_bytes())==expected)
        for name,row in manifest['files'].items():
            path=root/name
            self.check('source','source_files',name+' exact output bytes',path.is_file() and path.stat().st_size==row['bytes'] and SHA(path.read_bytes())==row['sha256'])
        def rgba(entry,phase=0,snapshot=None):
            colors=entry['colors']
            if snapshot and entry['palette'] in snapshot['pulse_palettes']:
                colors=snapshot['pulse_palettes'][entry['palette']][phase]
            im=Image.new('RGBA',tuple(entry['canvas']))
            im.putdata([tuple(int(colors[p][i:i+2],16) for i in (1,3,5))+(255 if p else 0,) for p in entry['indices']])
            return im
        def floor(snapshot,size,name):
            im=Image.new('RGB',size,'#101820');tile=rgba(snapshot['context'][name])
            for y in range(0,size[1],16):
                for x in range(0,size[0],16):im.paste(tile,(x,y),tile)
            return im
        snapshots={};native_instances=0;source_panels=0
        for profile in self.args.profiles:
            local=profile-10;directory=root/f'variant-{local:02}'
            snapshot=json.loads((directory/'snapshot.json').read_text());snapshots[profile]=snapshot
            rom=NativeRom(Path(self.args.frozen)/f'v{profile}');ts=rom.tileset('forest')
            entries={(e['name'],e['phase']):e for e in snapshot['entries']}
            self.check(profile,'source_coverage','all494 canopy instances declared',len(entries)==494)
            for key,entry in entries.items():
                decoded=decode_metatile(rom,ts,key[0]);indices,words=decoded['frames'][key[1]]
                self.check(profile,'source_native',key[0]+':'+str(key[1])+' exact ROM indices',indices==bytes(entry['indices']))
                colors=native_palette(entry['colors']);expected=struct.pack('<256H',*[colors[p] if p else 0x8000 for p in entry['indices']])
                self.equal(profile,'source_native',key[0]+':'+str(key[1])+' exact ROM color words',expected,words)
            native=json.loads((directory/'native-manifest.json').read_text())
            for entry in native['canonical_frames']:
                key=entry['name'],entry['phase'];expected=entries[key];image=rgba(expected)
                a=Image.open(directory/entry['native_indexed_png']);b=Image.open(directory/entry['native_rgba_png']).convert('RGBA')
                self.check(profile,'source_png',str(key)+' indexed native PNG',a.mode=='P' and a.size==(16,16) and bytes(a.getdata())==bytes(expected['indices']) and a.convert('RGBA').tobytes()==image.tobytes())
                self.check(profile,'source_png',str(key)+' RGBA native PNG',b.size==(16,16) and b.tobytes()==image.tobytes())
                native_instances+=1
            for sheet in native['alias_sheets']:
                a=Image.open(directory/sheet['indexed_png']);b=Image.open(directory/sheet['rgba_png']).convert('RGBA')
                for panel in sheet['entries']:
                    x,y,w,h=panel['rect'];key=panel['name'],panel['phase'];expected=entries[key];image=rgba(expected)
                    ai=a.crop((x,y,x+w,y+h));bi=b.crop((x,y,x+w,y+h))
                    self.check(profile,'source_png',str(key)+' indexed alias-sheet rectangle',a.mode=='P' and (w,h)==(16,16) and bytes(ai.getdata())==bytes(expected['indices']) and ai.convert('RGBA').tobytes()==image.tobytes())
                    self.check(profile,'source_png',str(key)+' RGBA alias-sheet rectangle',bi.tobytes()==image.tobytes());native_instances+=1
            assembly=json.loads((directory/'assembly-manifest.json').read_text())
            for stage,panels in assembly['all47'].items():
                board=Image.open(directory/f'all47-{stage}-source.png').convert('RGB')
                for panel in panels:
                    tile=rgba(entries[(panel['name'],panel['phase'])]);expected=floor(snapshot,(16,16),panel['source_substrate']);expected.paste(tile,(0,0),tile)
                    x,y,w,h=panel['rect'];actual=board.crop((x,y,x+w,y+h))
                    self.check(profile,'source_assemblies','all47 '+panel['name']+' literal floor/alpha',actual.tobytes()==expected.tobytes());source_panels+=1
            board=Image.open(directory/'palette-inks-source.png').convert('RGB')
            for swatch in assembly['palette_swatches']:
                x,y,w,h=swatch['swatch_rect'];expected=Image.new('RGB',(w,h),swatch['rgb555_color'])
                self.check(profile,'source_assemblies',swatch['bank']+str(swatch['phase'])+':'+str(swatch['index'])+' literal palette swatch',board.crop((x,y,x+w,y+h)).tobytes()==expected.tobytes());source_panels+=1
            islands=Image.open(directory/'adjacency-islands-source.png').convert('RGB')
            for island in assembly['islands']:
                cells=island['cells'];expected=floor(snapshot,(len(cells[0])*16,len(cells)*16),'moss0' if island['kind']==1 else 'blight_floor')
                for panel in island['panels']:
                    tile=rgba(entries[(panel['name'],panel['phase'])]);expected.paste(tile,tuple(panel['rect'][:2]),tile)
                for rect,scale in ((island['native_rect'],1),(island['inspection_rect'],island['inspection_scale'])):
                    x,y,w,h=rect;scaled=expected.resize((w,h),Image.Resampling.NEAREST)
                    self.check(profile,'source_assemblies',island['name']+' literal island scale'+str(scale),islands.crop((x,y,x+w,y+h)).tobytes()==scaled.tobytes());source_panels+=1
            branches=Image.open(directory/'foreground-branch-layers-source.png').convert('RGB')
            for row,layers in enumerate(assembly['branch_layers']):
                ground=floor(snapshot,(64,64),layers['floor']);roof=Image.new('RGBA',(64,64))
                for panel in layers['alias_panels']:
                    tile=rgba(entries[(panel['name'],panel['phase'])]);roof.paste(tile,tuple(panel['rect'][:2]),tile)
                composite=ground.copy();composite.paste(roof,(0,0),roof)
                for col,(image,key) in enumerate(((ground,'floor_rgb_sha256'),(roof,'roof_rgba_sha256'),(composite,'composite_rgb_sha256'))):
                    self.check(profile,'source_assemblies',key+' independent layer reconstruction',SHA(image.tobytes())==layers[key])
                    field=Image.new('RGB',(64,64),'#101820')
                    field.paste(image,(0,0),image if image.mode=='RGBA' else None)
                    expected=field.resize((192,192),Image.Resampling.NEAREST);x=col*220+5;y=85+row*244
                    self.check(profile,'source_assemblies',key+' exact threefold board panel',branches.crop((x,y,x+192,y+192)).tobytes()==expected.tobytes());source_panels+=1
            gif=Image.open(directory/'palette-pulse-source.gif');decoded=[frame.convert('RGB').copy() for frame in ImageSequence.Iterator(gif)]
            self.check(profile,'source_gif','exact four fixed-inspection GIF frames',len(decoded)==4)
            for phase,image in enumerate(decoded):
                expected=Image.open(directory/f'palette-phase-{phase}-source.png').convert('RGB')
                self.check(profile,'source_gif','phase'+str(phase)+' decoded RGB exact PNG',image.size==expected.size and image.tobytes()==expected.tobytes())
                gif.seek(phase)
                self.check(profile,'source_gif','phase'+str(phase)+' declared180ms inspection hold',gif.info.get('duration')==180)
        comparison=json.loads((root/'source-comparison-manifest.json').read_text());board=Image.open(root/'eight-canopy-directions-source.png').convert('RGB')
        for panel in comparison['canopy_assemblies']:
            profile=panel['profile'];snapshot=snapshots[profile];entries={(e['name'],e['phase']):e for e in snapshot['entries']}
            expected=floor(snapshot,(96,64),'moss0' if panel['stage']=='healthy' else 'blight_floor')
            for item in panel['alias_definitions']:
                tile=rgba(entries[(item['name'],item['phase'])]);expected.paste(tile,tuple(item['rect'][:2]),tile)
                wx,wy=item['world_cell'];q=(wx&1)|((wy&1)<<1)
                self.check(profile,'source_topology','comparison '+item['name']+' uses declared world parity',int(item['name'].split('_')[3])==q)
                x,y=item['cell'];kind=1 if panel['stage']=='healthy' or (panel['stage']=='mixed' and x<3) else 2
                occupied=lambda xx,yy:1<=xx<=4 and 1<=yy<=2
                mask=(0 if occupied(x,y-1) else 1)|(0 if occupied(x+1,y) else 2)|(0 if occupied(x,y+1) else 4)|(0 if occupied(x-1,y) else 8)
                self.check(profile,'source_topology','comparison '+item['name']+' follows actual two-crown adjacency',item['name']==f'f2_canopy_{kind-1}_{q}_{mask:x}0' and [wx,wy]==[x+1,y+1])
            self.check(profile,'source_assemblies','comparison '+panel['stage']+' exact source hash',SHA(expected.tobytes())==panel['source_rgb_sha256'])
            x,y,w,h=panel['rect'];scaled=expected.resize((w,h),Image.Resampling.NEAREST)
            self.check(profile,'source_assemblies','comparison '+panel['stage']+' exact integer-enlarged panel',board.crop((x,y,x+w,y+h)).tobytes()==scaled.tobytes());source_panels+=1
        return {'manifest_sha256':SHA((root/'source-manifest.json').read_bytes()),'source_commit':manifest['source_commit'],'native_instances':native_instances,'source_panels':source_panels,'exact_source_gifs':len(self.args.profiles),'note':'Source artwork and fixed inspection holds; not emulator screenshots or live timing.'}

    def runtime(self):
        if not self.args.runtime:return {'status':'not_requested'}
        from PIL import Image,ImageSequence
        root=Path(self.args.runtime);baseline=json.loads((root/'v6/capture.json').read_text())
        old={row['name']:row for row in baseline['captures']}
        reports=[];total_cases=total_movies=total_gifs=0
        logical=('game_state','area','cell','state','position','z_q16','hp','camera','textbox','rng_state','motion_phase','safe_position','standing_type','equipment','shield_up','item_active')
        fixture=('seed','cell','group','frames','position','target','facing','inputs','physical_contract','final_physical_contract','maze_sha256','initial_progress_sha256','final_progress_sha256','initial_rng','final_rng')
        def file(directory,name):
            path=(directory/name).resolve()
            assert path.is_relative_to(directory.resolve()),('unsafe media reference',name)
            return path
        def gif_matches(path,raw,count,fps):
            gif=Image.open(path);chunks=[]
            for frame in ImageSequence.Iterator(gif):
                duration=frame.info.get('duration',0)
                if duration<=0 or duration%10:return False
                chunks.append([frame.convert('RGB').tobytes(),duration//10])
            cursor=0;elapsed=0
            for tick in range(0,count,2):
                expected=Image.open(raw/f'frame-{tick:03}.png').convert('RGB').resize((480,320),Image.Resampling.NEAREST).tobytes()
                need=round(min(tick+2,count)*100/fps)-round(tick*100/fps)
                while need:
                    if cursor>=len(chunks) or chunks[cursor][0]!=expected:return False
                    use=min(need,chunks[cursor][1]);need-=use;elapsed+=use;chunks[cursor][1]-=use
                    if chunks[cursor][1]==0:cursor+=1
            return cursor==len(chunks) and elapsed==round(count*100/fps)
        for profile in (6,*self.args.profiles):
            directory=root/f'v{profile}';report_path=directory/'capture.json';report=json.loads(report_path.read_text())
            frozen_dir=Path(self.args.frozen)/f'v{profile}';frozen=json.loads((frozen_dir/'freeze.json').read_text());rom=NativeRom(frozen_dir)
            self.check(profile,'runtime_provenance','actual source/ROM bound to final frozen build',report['source_commit']==frozen['source_commit'] and report['rom_sha256']==SHA(rom.rom))
            self.check(profile,'runtime_provenance','complete focused report and22 contexts all pass',report.get('complete') and len(report['captures'])==22 and report['passed']==report['total'] and not report['failures'])
            self.check(profile,'runtime_provenance','current focused capture tool exact',report['capture_tool_sha256']==SHA((GAME/'tools/forest_v3_review.py').read_bytes()))
            for name,expected in report['capture_dependency_sha256'].items():
                self.check(profile,'runtime_provenance',name+' current capture dependency',SHA((GAME/'tools'/name).read_bytes())==expected)
            for name,expected in report['frozen_input_sha256'].items():
                self.check(profile,'runtime_provenance',name+' captured frozen file exact',SHA((frozen_dir/name).read_bytes())==expected)
            rows={row['name']:row for row in report['captures']};self.check(profile,'runtime_comparison','same focused case names',set(rows)==set(old))
            media={};natural=diagnostic=movies=gifs=0;minimum_body=minimum_character=10000;minimum_character_cluster=10000;cape_frames=0
            cape_body,body_raw=rom.sheet('hero');fx_meta,fx_raw=rom.sheet('bloomfx');fx_pal=rom.array('bloomfx_frame_pal')
            for name,row in rows.items():
                reference=old[name]
                for key in fixture:self.check(profile,'runtime_comparison',name+' exact '+key,row.get(key)==reference.get(key))
                for phase in ('initial','final'):
                    for key in logical:self.check(profile,'runtime_comparison',name+' '+phase+' '+key,row[phase].get(key)==reference[phase].get(key))
                is_diagnostic=row['group']=='diagnostic';diagnostic+=is_diagnostic;natural+=not is_diagnostic
                self.check(profile,'runtime_labels',name+' diagnostic provenance label agrees',row.get('fixture_kind','').startswith('diagnostic')==is_diagnostic)
                samples=row['visibility_observations']
                self.check(profile,'runtime_hardware',name+' one paired native observation per video frame',len(samples)==row['video_frames'] and all(s['visibility'].get('scanout_start_vcount')==0 and s['visibility'].get('scanout_end_vcount')==160 and s['visibility'].get('scanout_frame_counter')==s['visibility'].get('scanout_end_frame_counter') for s in samples))
                self.check(profile,'runtime_cadence',name+' exact video/gameplay cadence',row['cadence_observation']['intervals']==reference['cadence_observation']['intervals'])
                self.check(profile,'runtime_hardware',name+' real resident native hardware payloads',all(all(h.get(k) for k in ('native_room_mappings','static_BG_bytes_match_ROM','animated_BG_bytes_are_authored_frames','OAM_legal','world_palette_is_authored_phase','actual_hardware_palette_is_authored_phase','selected_OBJ_palette_bytes_match_ROM','resolved_visual_mappings_valid')) for h in row['hardware_samples']))
                gap=set(row.get('menu_resume_hardware_gap',{}).get('ticks',[]))
                for sample in samples:
                    v=sample['visibility'];playing=sample['game_state']==1 and sample['displayed_world_planes'] and sample['tick'] not in gap
                    if not playing:continue
                    if profile>=11:
                        goal=max(12,(v.get('opaque_colored_pixels',0)+3)//4)
                        self.check(profile,'runtime_visibility',name+':'+str(sample['tick'])+' meaningful canopy-visible native body',v.get('body_found') and v.get('guard_exact_native_subset') and v.get('visible_colored_pixels',0)>=goal and v.get('largest_visible_colored_component',0)>=8)
                        self.check(profile,'runtime_visibility',name+':'+str(sample['tick'])+' displayed current character remains visible',v.get('framebuffer_exact_character_color_pixels',0)>=12 and v.get('framebuffer_exact_character_color_component',0)>=8)
                        minimum_body=min(minimum_body,v.get('visible_colored_pixels',0));minimum_character=min(minimum_character,v.get('framebuffer_exact_character_color_pixels',0));minimum_character_cluster=min(minimum_character_cluster,v.get('framebuffer_exact_character_color_component',0))
                    cape=v.get('attached_cape')
                    if cape:
                        cape_frames+=1;ref=cape['native_frame'];face=ref['face'];phase=ref['phase'];fx=rom.defs['F_BLOOMFX_CAPE_'+face+str(phase)];hero=rom.defs['F_HERO_CAPE_'+face+str(phase+1)]
                        expected_fx=fx_raw[fx*fx_meta['frame_tiles']*32:(fx+1)*fx_meta['frame_tiles']*32];expected_body=body_raw[hero*cape_body['frame_tiles']*32:(hero+1)*cape_body['frame_tiles']*32]
                        self.check(profile,'runtime_cape',name+':'+str(sample['tick'])+' exact current attached native garment',cape.get('exact_current_native_pose_and_anchor') and cape.get('anchor_projection_delta')==[0,0] and cape['VRAM_sha256']==SHA(expected_fx) and v['body_VRAM_sha256']==SHA(expected_body) and cape['OAM']['pal']==ref['palette']==fx_pal[fx] and ref['frame']==fx)
                paths=set(row['native_frames'])|{row['image']}
                for key in ('after_image','filmstrip','video','gif'):
                    if row.get(key):paths.add(row[key])
                for key in ('action_keyframes','phase_keyframes'):
                    for entry in row.get(key,[]):paths.add(entry['path'])
                if row.get('worst_visibility_keyframe'):paths.add(row['worst_visibility_keyframe']['path'])
                for relative in paths:
                    path=file(directory,relative);self.check(profile,'runtime_media',relative+' exists',path.is_file())
                    if path.is_file():media[relative]=SHA(path.read_bytes())
                for relative in row['native_frames']:
                    image=Image.open(file(directory,relative));self.check(profile,'runtime_media',relative+' native240x160',image.size==(240,160))
                if row.get('video'):
                    movies+=1;stream=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,nb_read_frames','-of','json',str(file(directory,row['video']))],text=True))['streams'][0]
                    from fractions import Fraction
                    rate=Fraction(stream['r_frame_rate']);native_rate=Fraction(262144,4389)
                    self.check(profile,'runtime_media',name+' nativeGBA-rate2x viewing movie',stream['width']==480 and stream['height']==320 and int(stream['nb_read_frames'])==row['video_frames'] and rate==native_rate and abs(row['video_fps']-float(native_rate))<1e-8)
                if row.get('gif'):
                    gifs+=1;self.check(profile,'runtime_media',name+' GIF exact native colors and sampledGBA timeline',row['gif_metadata']['exact_palette'] and gif_matches(file(directory,row['gif']),file(directory,row['all_frames']),row['video_frames'],row['video_fps']))
            self.check(profile,'runtime_coverage','16 generated plus6 explicit diagnostic contexts and7 movies',natural==16 and diagnostic==6 and movies==7)
            total_cases+=len(rows);total_movies+=movies;total_gifs+=gifs
            reports.append({'profile':profile,'capture_sha256':SHA(report_path.read_bytes()),'rom_sha256':report['rom_sha256'],'source_commit':report['source_commit'],'contexts':len(rows),'natural':natural,'diagnostic':diagnostic,'capture_passed':report['passed'],'capture_total':report['total'],'movies':movies,'exact_gifs':gifs,'media_count':len(media),'media_manifest_sha256':SHA(json.dumps(media,sort_keys=True).encode()),'minimum_body_canopy_visible_colored':minimum_body if profile>=11 else None,'minimum_displayed_character_colored':minimum_character if profile>=11 else None,'minimum_displayed_character_component':minimum_character_cluster if profile>=11 else None,'validated_attached_cape_frames':cape_frames})
        return {'reports':reports,'contexts':total_cases,'movies':total_movies,'exact_gifs':total_gifs,'baseline':'Preserved previous forest study6; not production0.','limits':'Finite real mGBA recordings and exact source/character compositing proof; does not assert universal CPU timing or arbitrary-scene visibility.'}

    def run(self):
        base_source=json.loads(Path(self.args.base_source).read_text());base6=NativeRom(self.args.base6)
        for profile in self.args.profiles:
            directory=Path(self.args.frozen)/f'v{profile}';rom=NativeRom(directory)
            frozen=json.loads((directory/'freeze.json').read_text())
            self.check(profile,'provenance','frozen ROM SHA exact',frozen['rom_sha256']==SHA(rom.rom))
            self.check(profile,'provenance','frozen compiler selector matches profile',rom.defs['BART_FOREST_VARIANT']==profile)
            for group in ('source_file_sha256','code_file_sha256'):
                for name,expected in frozen.get(group,{}).items():
                    self.check(profile,'provenance',name+' current input matches captured frozen source',SHA((GAME/name).read_bytes())==expected)
                    committed=subprocess.check_output(['git','show',frozen['source_commit']+':bartgame/'+name],cwd=GAME)
                    self.check(profile,'provenance',name+' exact declared committed source',SHA(committed)==expected)
            source=json.loads(subprocess.check_output([sys.executable,__file__,'--export',str(profile),'--base-source',self.args.base_source],cwd=GAME,text=True))
            self.scope(profile,rom,source,base_source,base6)
            counts=self.native(profile,rom,source);pulse=self.pulses(profile,rom,source)
            self.preserved(profile,rom)
            visibility=self.visibility_metadata(profile,rom)
            EnemyAudit.budget(self,profile,rom,11)
            union=copy.deepcopy(self.budgets[-1])
            extra=4*rom.sheet('forestlandmark')[0]['frame_tiles']+16
            union['allocations']['four streamed forestlandmarks']=extra-16
            union['allocations']['foreground lower-body visibility fragment']=16
            union['used']+=extra;union['free']-=extra
            self.budgets[-1]=union
            self.check(profile,'obj_budget','complete superset includes landmarks and visibility fragment',union['used']<=union['limit'],union)
            memory={name:int(address,16) for address,name in re.findall(r'^\s+0x([0-9a-fA-F]+)\s+(__ewram_bss_end|__bss_end)\s*=',rom.linker,re.M)}
            self.check(profile,'budget','EWRAM below256KiB and IWRAM below declared stack reservation',memory.get('__ewram_bss_end',0xFFFFFFFF)<=0x02040000 and memory.get('__bss_end',0xFFFFFFFF)<=0x03007E00,memory)
            self.profiles.append({'profile':profile,'source_commit':frozen['source_commit'],'frozen_input_sha256':{name:SHA((directory/name).read_bytes()) for name in ('bartgame.gba','bartgame.map','assets.h','freeze.json')},'rom_sha256':SHA(rom.rom),'native':counts,'pulse':pulse,'visibility_metadata':visibility,'obj_budget':union,'memory':memory})
        for profile in self.args.controls:
            candidate=Path(self.args.frozen)/f'v{profile}'/'bartgame.gba'
            actual=SHA(candidate.read_bytes())
            self.check(profile,'historical','complete prior-profile ROM bytes preserved',actual==HISTORICAL_SHA[profile],{'expected_sha256':HISTORICAL_SHA[profile],'actual_sha256':actual})
        native_check_count=len(self.rows)
        source_proof=self.source_gallery(self.args.source_gallery) if self.args.source_gallery else {'status':'not_requested'}
        runtime_proof=self.runtime()
        failures=[x for x in self.rows if not x['passed']]
        from collections import Counter
        dependencies=['tools/forest_v2_audit.py','tools/sewer_concept_audit.py','tools/forest_concept_audit.py','tools/enemy_study_audit.py']
        out={'method':__doc__,'source_commits':sorted({row['source_commit'] for row in self.profiles}),'auditor_sha256':SHA(Path(__file__).read_bytes()),'audit_dependency_sha256':{n:SHA((GAME/n).read_bytes()) for n in dependencies},'base_source_sha256':SHA(Path(self.args.base_source).read_bytes()),'inventory_sha256':SHA(Path(self.args.inventory).read_bytes()),'profiles':self.profiles,'obj_budgets':self.budgets,'native_check_count':native_check_count,'source_gallery':source_proof,'runtime':runtime_proof,'passed':len(self.rows)-len(failures),'total':len(self.rows),'failures':failures,'checks_by_group':dict(Counter(r['group'] for r in self.rows)),'historical_controls':[{r['variant']:r.get('detail')} for r in self.rows if r['group']=='historical'],'limits':'Native source/ROM/metadata and scope proof, plus optional exact source-art and finite actual motion/PPU checks. No new generation corpus or universal visual/performance claim.'}
        if self.args.details:out['checks']=self.rows
        Path(self.args.out).parent.mkdir(parents=True,exist_ok=True)
        Path(self.args.out).write_text(json.dumps(out,indent=2)+'\n')
        print(json.dumps({'passed':out['passed'],'total':out['total'],'failures':len(failures)}));return bool(failures)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--export',type=int)
    p.add_argument('--profiles',type=int,nargs='+',default=list(range(11,19)))
    p.add_argument('--controls',type=int,nargs='*',default=list(range(11)))
    p.add_argument('--base-source',default=str(WORK/'audit/base6-source.json'))
    p.add_argument('--base6',help='Prior-profile6 native bundle; defaults to frozen/v6 (which must match its recorded legacy hash).')
    p.add_argument('--baseline',help='Production0 native bundle; defaults to frozen/v0 (which must match its recorded legacy hash).')
    p.add_argument('--inventory',default=str(GAME.parent/'art-review/forest-concepts/validation/inventory.json'))
    p.add_argument('--frozen',default=str(WORK/'frozen'))
    p.add_argument('--out',default=str(WORK/'audit/independent-native.json'))
    p.add_argument('--source-gallery',help='Verify the exported native source PNGs, declarations and exact inspection GIFs.')
    p.add_argument('--runtime',help='Verify completed focused mGBA reports and native/viewing artifacts for v6 and v11..18.')
    p.add_argument('--details',action='store_true',help='Include individual passing checks; default is compact counts/failures and artifact hashes.')
    args=p.parse_args()
    if not args.baseline:args.baseline=str(Path(args.frozen)/'v0')
    if not args.base6:args.base6=str(Path(args.frozen)/'v6')
    if not Path(args.base_source).exists():
        base=subprocess.check_output([sys.executable,str(GAME/'tools/forest_v2_audit.py'),'--export-source','6','--inventory',args.inventory],cwd=GAME,text=True)
        Path(args.base_source).parent.mkdir(parents=True,exist_ok=True);Path(args.base_source).write_text(base)
    if args.export is not None:export(args.export,args.base_source);return 0
    return Audit(args).run()
if __name__=='__main__':raise SystemExit(main())

#!/usr/bin/env python3
"""Independent ROM and HUD regression audit for the final Drain/UI studies.

The native painters provide expected indexed pixels. This tool never imports
build_assets, its deduplicator, parse_art or 4bpp packer. ROM pixels are decoded
independently, including hardware flips and RGB555 banks. The original room's
resolved type/collision/prop/glitter values stay exact despite new picture IDs.
Runtime checks use real mGBA OAM/VRAM and normal menu inputs; disclosed resource,
equipment and isolated contact fixtures do not substitute mockup framebuffers.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'tools'))
from sewer_concept_audit import NativeRom, decode_8x8, decode_sprite, decode_metatile, rgb555, SHAPES

SHA = lambda data: hashlib.sha256(data).hexdigest()
CONTRACT = json.loads((ROOT/'art/reboot_contracts.json').read_text())
KEEPERS = {'peddler_head','peddler_body','gatekeeper','wisp'}
UI_SHEETS = {'uimarks','huditems'}
CHANGED_FACE_NAMES = {'peddler','gatekeeper'}
ROOM_ARRAYS = {'room_sewer_main_ground','room_sewer_main_overlay'}
ALLOWED_SCALARS = {'ui_tiles','hud_tiles','vwf_w','vwf_bits','orb_glow','huditems_frame_pal'} | ROOM_ARRAYS
ALLOWED_BG_BANKS = {'drain','ui','menu','map','hud'}
ALLOWED_OBJ_BANKS = {'peddler','gatekeeper','ui','uikit'}
METADATA = ('type','coll','prop','glitter')


def source_export(ui):
    os.environ['BART_SEWER']='9'; os.environ['BART_UI']=str(ui)
    sys.path.insert(0,str(ROOT/'art'))
    import sewer_final as final
    import sewer_final_contracts as fc
    import sewer_concepts as recipes
    import sprites
    import palettes
    import ui_kit
    import ui_font
    import ui_studies
    # All rows are final-size source drawings. No builder utility participates.
    tiles={}
    for clone in fc.CLONES:
        count,hold=final.frame_spec(clone['layer'],clone['x'],clone['y'])
        pictures=[]
        for frame in range(count):
            im=final.paint(clone['name'],frame)
            assert im.mode=='P' and im.size==(16,16)
            assert all(0<=v<16 for v in im.tobytes())
            pictures.append(im.tobytes().hex())
        tiles[clone['name']]={'source':clone['source'],'source_id':clone['source_id'],
            'layer':clone['layer'],'x':clone['x'],'y':clone['y'],
            'frames':pictures,'count':count,'hold':hold}
    sheets={}
    for sheet in sprites.SHEETS:
        if sheet['name'] not in KEEPERS|UI_SHEETS|{'sewerrail','face'}:continue
        frames={}
        for name,rows in sheet['frames'].items():
            if sheet['name']=='face' and name not in CHANGED_FACE_NAMES:continue
            pixels=bytes(0 if ch=='.' else int(ch,16) for row in rows for ch in row)
            assert len(pixels)==sheet['w']*sheet['h']
            frames[name]=pixels.hex()
        sheets[sheet['name']]={'w':sheet['w'],'h':sheet['h'],'pal':sheet['pal'],
            'frames':frames,'frame_pal':sheet.get('frame_pal'),
            'frame_ids':{name:index for index,name in enumerate(sheet['frames'])},
            'frame_count':len(sheet['frames'])}
    kit={name:bytes(ui_kit.INDEX.get(ch,0) for row in rows for ch in row).hex()
         for name,rows in ui_kit.TILES.items()}
    hud={name:bytes(ui_kit.HUD_INDEX.get(ch,0) for row in rows for ch in row).hex()
         for name,rows in ui_kit.HUD_TILES.items()}
    widths=[];bits=[]
    for code in range(32,129):
        width,rows=ui_font.glyph(chr(code));widths.append(width)
        for row in rows:bits.append(sum(1<<x for x,ch in enumerate(row) if ch=='#'))
    output={'ui':ui,'style':getattr(ui_studies,'STYLE_NAMES',{}).get(ui,str(ui)),
        'recipe':recipes.recipe(9),'room':fc.ROOM,'tiles':tiles,
        'palette':[rgb555(c) for c in final.palette()],
        'bg_palettes':{n:[rgb555(c) for c in p] for n,p in palettes.BG_PALETTES},
        'obj_palettes':{n:[rgb555(c) for c in p] for n,p in palettes.OBJ_PALETTES},
        'face_palettes':[[rgb555(c) for c in p] for p in palettes.FACE_PALETTES],
        'sheets':sheets,'kit':kit,'hud':hud,'font_widths':widths,'font_bits':bits,
        'font_height':ui_font.HEIGHT}
    print(json.dumps(output,separators=(',',':')))


class Audit:
    def __init__(self,args):
        self.args=args;self.base=NativeRom(args.baseline);self.checks=[];self.details=[]
    def check(self,ui,group,name,passed,detail=None):
        row={'ui':ui,'group':group,'name':name,'passed':bool(passed)}
        if detail is not None:row['detail']=detail
        self.checks.append(row)
        if not passed:print('FAIL',ui,group,name,detail,flush=True)
    def equal(self,ui,group,name,before,after):
        self.check(ui,group,name,before==after,None if before==after else {
            'expected_sha256':SHA(before),'actual_sha256':SHA(after),
            'expected_bytes':len(before),'actual_bytes':len(after)})
    def source(self,ui):
        result=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--export-source',str(ui)],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,check=True)
        return json.loads(result.stdout)
    def source_snapshot(self):
        return {str(p.relative_to(ROOT)):SHA(p.read_bytes()) for p in sorted((ROOT/'art').glob('*'))
                if p.is_file() and p.suffix in ('.py','.json')}
    def provenance(self,ui,rom,snapshot):
        freeze=json.loads((rom.directory/'freeze.json').read_text())
        self.check(ui,'provenance','ROM hash matches frozen build',freeze['rom_sha256']==SHA(rom.rom))
        frozen=freeze['source_file_sha256']
        bad={name:value for name,value in snapshot.items()
             if frozen.get(name,frozen.get(name.removeprefix('art/')))!=value}
        self.check(ui,'provenance','all native art inputs match frozen source hashes',not bad,list(bad))
        self.check(ui,'profile','final Drain profile9 selected',rom.defs.get('BART_SEWER_VARIANT')==9)
        self.check(ui,'profile','requested UI profile selected',rom.defs.get('BART_UI_VARIANT')==ui,
                   rom.defs.get('BART_UI_VARIANT'))
    def retained(self,ui,rom):
        before=self.base
        self.check(ui,'identifiers','original metatile IDs remain stable',
            all(rom.tile_ids.get(n)==v for n,v in before.tile_ids.items()))
        self.check(ui,'identifiers','all original sheet identifiers remain stable',
            all(rom.sheet_ids.get(n)==v for n,v in before.sheet_ids.items()))
        old_count=before.defs['METATILE_COUNT']
        added=set(rom.tile_ids)-set(before.tile_ids)
        expected={f"SWH_F_{'G' if layer=='ground' else 'O'}_{x:02}_{y:02}"
                  for layer in ('ground','overlay') for y,row in enumerate(CONTRACT['rooms'][0][layer])
                  for x,n in enumerate(row) if n is not None}
        self.check(ui,'identifiers','exactly657 independent final placement IDs appended',added==expected and len(added)==657,
                   {'added':len(added),'unexpected':sorted(added-expected)})
        self.check(ui,'identifiers','new picture IDs append beyond original range',
                   all(rom.tile_ids[n]>=old_count for n in added))
        for field in METADATA:
            a=before.array('metatile_'+field);b=rom.array('metatile_'+field)
            self.equal(ui,'physical_metadata','all original '+field+' entries',a,b[:len(a)])
        for area in ('forest','myst'):
            a=before.tileset(area);b=rom.tileset(area)
            for name in ('tile_count','palette_count'):
                self.check(ui,'retained_'+area,name,a[name]==b[name],b[name])
            for name in ('tiles','palettes'):
                self.equal(ui,'retained_'+area,name,a[name],b[name])
            self.equal(ui,'retained_'+area,'all original metatile mappings',a['map'],b['map'][:len(a['map'])])
            self.check(ui,'retained_'+area,'new final Drain IDs have no mapping in other areas',
                not any(b['map'][len(a['map']):]))
            self.check(ui,'retained_'+area,'exact animation descriptors and frame data',a['animations']==b['animations'])
        protected=[]
        for name in before.sheet_ids:
            a,apix=before.sheet(name);b,bpix=rom.sheet(name)
            if name in KEEPERS|UI_SHEETS:continue
            self.check(ui,'retained_sprite_contracts',name+' hardware descriptor',a==b)
            if name=='face':
                stride=a['frame_tiles']*32
                allowed={before.defs['F_FACE_'+n.upper()] for n in CHANGED_FACE_NAMES}
                for index in range(before.defs['SHEET_FACE_FRAMES']):
                    if index not in allowed:self.equal(ui,'retained_faces','portrait '+str(index),
                        apix[index*stride:(index+1)*stride],bpix[index*stride:(index+1)*stride])
            else:
                self.equal(ui,'retained_sprite_pixels',name,apix,bpix);protected.append(name)
        skip={'tilesets','sheets','room_defs','pal_bg','pal_obj','pal_face','sheet_face_tiles'}|ALLOWED_SCALARS
        for name in before.sections:
            if name in skip or name.startswith(('sheet_','tileset_','metatile_','tile_anim')):continue
            self.check(ui,'retained_scalar_assets',name+' present',name in rom.sections)
            if name in rom.sections:self.equal(ui,'retained_scalar_assets',name,before.array(name),rom.array(name))
        for array,prefix,allowed,count in (
            ('pal_bg','PAL_BG_',ALLOWED_BG_BANKS,before.defs['PAL_BG_COUNT']),
            ('pal_obj','PAL_OBJ_',ALLOWED_OBJ_BANKS,before.defs['PAL_OBJ_COUNT'])):
            excepted={before.defs[prefix+n.upper()] for n in allowed}
            for bank in range(count):
                if bank not in excepted:self.equal(ui,'retained_palettes',array+str(bank),
                    before.array(array)[bank*32:(bank+1)*32],rom.array(array)[bank*32:(bank+1)*32])
        for bank in range(before.defs['SHEET_FACE_FRAMES']):
            if bank not in {before.defs['F_FACE_'+n.upper()] for n in CHANGED_FACE_NAMES}:
                self.equal(ui,'retained_palettes','face'+str(bank),
                    before.array('pal_face')[bank*32:(bank+1)*32],rom.array('pal_face')[bank*32:(bank+1)*32])
        return protected
    def room(self,ui,rom,source):
        old=CONTRACT['rooms'][0];room=source['room'];name=old['name']
        self.check(ui,'physical_room','room dimensions and object anchors unchanged',
            (room['w'],room['h'],room['objects'])==(old['w'],old['h'],old['objects']))
        self.equal(ui,'physical_room','original object data',self.base.array('room_'+name+'_objects'),rom.array('room_'+name+'_objects'))
        checked=0
        for layer in ('ground','overlay'):
            actual=struct.unpack('<%dH'%(room['w']*room['h']),rom.array('room_'+name+'_'+layer))
            previous=struct.unpack('<%dH'%(old['w']*old['h']),self.base.array('room_'+name+'_'+layer))
            for y,row in enumerate(room[layer]):
                for x,picture in enumerate(row):
                    index=y*room['w']+x;mt=actual[index]
                    self.check(ui,'physical_room',f'{layer}({x},{y}) exact expected picture identity',
                        mt==(65535 if picture is None else rom.tile_ids[picture.upper()]))
                    if picture is None:
                        self.check(ui,'physical_room',f'{layer}({x},{y}) original empty placement',previous[index]==65535)
                        continue
                    record=source['tiles'][picture]
                    self.check(ui,'physical_room',f'{layer}({x},{y}) same source cell',record['source_id']==previous[index])
                    for field in METADATA:
                        expected=self.base.array('metatile_'+field)[previous[index]]
                        value=rom.array('metatile_'+field)[mt]
                        self.check(ui,'physical_room',f'{layer}({x},{y}) resolved '+field,value==expected)
                    checked+=1
        self.check(ui,'physical_room','all657 occupied placements retain physical meaning',checked==657,checked)
    def native(self,ui,rom,source):
        counts={};tiles=rom.tileset('sewer');frames=0;changing=0
        self.check(ui,'native_art','all657 source picture identities',len(source['tiles'])==657)
        self.equal(ui,'native_palette','final Drain resident bank',struct.pack('<16H',*source['palette']),tiles['palettes'])
        for name,spec in source['tiles'].items():
            actual=decode_metatile(rom,tiles,name)
            self.check(ui,'native_art',name+' frame count',len(actual['frames'])==spec['count'])
            self.check(ui,'native_art',name+' frame hold',actual['speed']==(spec['hold'] if spec['count']>1 else None))
            for phase,(encoded,(indices,colours)) in enumerate(zip(spec['frames'],actual['frames'])):
                expected=bytes.fromhex(encoded)
                self.equal(ui,'native_indexed_art',name+f' frame{phase}',expected,indices)
                rgb=struct.pack('<256H',*[source['palette'][i] if i else 0x8000 for i in expected])
                self.equal(ui,'native_rgb555_art',name+f' frame{phase}',rgb,colours);frames+=1
            changing+=len(set(spec['frames']))>1
        for group,array,prefix in [('bg_palettes','pal_bg','PAL_BG_'),('obj_palettes','pal_obj','PAL_OBJ_')]:
            for name,colours in source[group].items():
                bank=rom.defs[prefix+name.upper()]
                self.equal(ui,'source_palette',group+'.'+name,struct.pack('<16H',*colours),rom.array(array)[bank*32:(bank+1)*32])
        for index,colours in enumerate(source['face_palettes']):
            self.equal(ui,'source_palette','face'+str(index),struct.pack('<16H',*colours),rom.array('pal_face')[index*32:(index+1)*32])
        sheet_frames={}
        for sheet,spec in source['sheets'].items():
            meta,data=rom.sheet(sheet);stride=meta['frame_tiles']*32
            self.check(ui,'native_sheet',sheet+' source native canvas',
                [meta['width'],meta['height']]==[spec['w'],spec['h']] and (spec['w'],spec['h']) in SHAPES)
            sheet_frames[sheet]=0
            self.check(ui,'native_sheet',sheet+' source palette slot',meta['pal']==rom.defs['PAL_OBJ_'+spec['pal'].upper()])
            self.check(ui,'native_sheet',sheet+' source frame count',meta['tile_count']==spec['frame_count']*meta['frame_tiles'])
            for name,encoded in spec['frames'].items():
                frame=rom.defs['F_'+sheet.upper()+'_'+name.upper()]
                self.check(ui,'native_sheet',sheet+'.'+name+' exact source frame ID',frame==spec['frame_ids'][name])
                decoded=decode_sprite(data[frame*stride:(frame+1)*stride],spec['w'],spec['h'])
                self.equal(ui,'native_sheet',sheet+'.'+name,bytes.fromhex(encoded),decoded)
                sheet_frames[sheet]+=1
            if spec['frame_pal']:
                expected=bytes(rom.defs['PAL_OBJ_'+spec['frame_pal'][name].upper()] for name in spec['frame_ids'])
                self.equal(ui,'source_palette',sheet+' per-frame palette selection',expected,rom.array(sheet+'_frame_pal'))
        for bank in ('kit','hud'):
            array=rom.array('ui_tiles' if bank=='kit' else 'hud_tiles')
            self.check(ui,'ui_source',bank+' tile count',len(array)==len(source[bank])*32)
            for index,(name,pixels) in enumerate(source[bank].items()):
                expected=bytes.fromhex(pixels)
                self.equal(ui,'ui_source',bank+'.'+name,expected,bytes(decode_8x8(array[index*32:(index+1)*32])))
        self.equal(ui,'font_source','all97 glyph widths',bytes(source['font_widths']),rom.array('vwf_w'))
        self.equal(ui,'font_source','all glyph pixel rows',bytes(source['font_bits']),rom.array('vwf_bits'))
        self.check(ui,'font_source','native variable font metrics',rom.defs['VWF_HEIGHT']==source['font_height'] and max(source['font_widths'])<=8)
        for area in ('forest','myst','sewer'):
            ts=rom.tileset(area)
            self.check(ui,'native_budget',area+' tiles <=1024',ts['tile_count']<=1024,ts['tile_count'])
            self.check(ui,'native_budget',area+' palette banks <=12',ts['palette_count']<=12,ts['palette_count'])
            self.check(ui,'native_budget',area+' all resident colors RGB555',
                all(v<32768 for v in struct.unpack('<%dH'%(len(ts['palettes'])//2),ts['palettes'])))
        self.check(ui,'native_budget','OBJ palette banks <=16',rom.defs['PAL_OBJ_COUNT']<=16)
        return {'native_drain_frame_count':frames,'changing_placement_ids':changing,'source_sheet_frames':sheet_frames,
            'budgets':{name:{'tiles':rom.tileset(name)['tile_count'],'palettes':rom.tileset(name)['palette_count']} for name in ('forest','myst','sewer')}}
    def run(self):
        snapshot=self.source_snapshot()
        for ui in self.args.variants:
            rom=NativeRom(Path(self.args.frozen)/f'v{ui}');source=self.source(ui)
            self.provenance(ui,rom,snapshot);protected=self.retained(ui,rom)
            self.room(ui,rom,source);details=self.native(ui,rom,source)
            details.update({'ui':ui,'style':source['style'],'rom_sha256':SHA(rom.rom),'protected_sprite_sheets':protected})
            if self.args.runtime:details['runtime']=runtime_checks(rom,ui,self.check,self.args.runtime_trials)
            self.details.append(details)
            rows=[r for r in self.checks if r['ui']==ui]
            print('UI',ui,'PASS' if all(r['passed'] for r in rows) else 'FAIL',sum(r['passed'] for r in rows),'/',len(rows),flush=True)
        self.check(-1,'provenance','source remains unchanged during audit',snapshot==self.source_snapshot())
        report={'method':__doc__,'baseline_sha256':SHA(self.base.rom),'source_file_sha256':snapshot,
            'allowed_changes':{'drain':'Final657 independent picture IDs, native geometry/palette/animations; original per-cell collision/type/prop/glitter and objects unchanged.',
                'interface':'Five UI material/frame/mark/HUD studies; compact12px top HUD, conditional equipped ammunition and native16px bottom-right minimap; interface palettes/font presentation may change.',
                'actors':'Selected first frog and pointed wizard; keeper face banks; HUD miniatures/markers; rail source art.',
                'protected':'Bloom/Step-and-cut, all other actor/item/enemy pixel payloads, title bitmap, forest/interior art/animation, original gameplay metadata, item tables and interaction timing arrays.'},
            'variants':self.details,'passed':sum(r['passed'] for r in self.checks),'total':len(self.checks),
            'checks':self.checks,'failures':[r for r in self.checks if not r['passed']],
            'limits':'Exact source/ROM and physical-map verification is not a taste score. Runtime coverage is disclosed; art gallery captures separately review composition and readability. UI appearance differs intentionally; original default ROM hash is not required.'}
        Path(self.args.out).parent.mkdir(parents=True,exist_ok=True)
        Path(self.args.out).write_text(json.dumps(report,indent=2)+'\n')
        compact={k:v for k,v in report.items() if k!='checks'}
        Path(self.args.out).with_name('audit-summary.json').write_text(json.dumps(compact,indent=2)+'\n')
        print('RESULT',report['passed'],'/',report['total'],flush=True)
        return int(bool(report['failures']))


def hud_plane(c):
    """Decode actual nontransparent BG0 and priority-zero OBJ pixels only."""
    import probe as P
    control=P.r16(c,0x04000008)&65535
    chars=0x06000000+((control>>2)&3)*16384
    screen=0x06000000+((control>>8)&31)*2048
    rgba=[65535]*(240*160)
    for ty in range(20):
        for tx in range(30):
            entry=P.r16(c,screen+(ty*32+tx)*2)&65535;tile=entry&1023
            for y in range(8):
                for x in range(8):
                    xx=7-x if entry&0x400 else x;yy=7-y if entry&0x800 else y
                    byte=P.r8(c,chars+tile*32+yy*4+xx//2)
                    ink=(byte>>((xx&1)*4))&15
                    if ink:rgba[(ty*8+y)*240+tx*8+x]=P.r16(c,0x05000000+(entry>>12)*32+ink*2)&65535
    sizes=(((8,8),(16,16),(32,32),(64,64)),((16,8),(32,8),(32,16),(64,32)),((8,16),(8,32),(16,32),(32,64)))
    for index in reversed(range(128)):
        at=0x07000000+index*8;a0=P.r16(c,at)&65535;a1=P.r16(c,at+2)&65535;a2=P.r16(c,at+4)&65535
        if a0&0x300==0x200 or (a2>>10)&3 or a0>>14==3:continue
        width,height=sizes[a0>>14][a1>>14];sx=a1&511;sy=a0&255
        if sx>=256:sx-=512
        if sy>=160:sy-=256
        if sx+width<=0 or sx>=240 or sy+height<=0 or sy>=160:continue
        for y in range(height):
            for x in range(width):
                px,py=sx+x,sy+y
                if not (0<=px<240 and 0<=py<160):continue
                xx=width-1-x if a1&0x1000 else x;yy=height-1-y if a1&0x2000 else y
                tile=(a2&1023)+(yy//8)*(width//8)+(xx//8)
                byte=P.r8(c,0x06010000+tile*32+(yy%8)*4+(xx%8)//2)
                ink=(byte>>((xx&1)*4))&15
                if ink:rgba[py*240+px]=P.r16(c,0x05000200+(a2>>12)*32+ink*2)&65535
    positions=[(i%240,i//240) for i,pixel in enumerate(rgba) if pixel!=65535]
    return bytes(struct.pack('<%dH'%len(rgba),*rgba)),positions


def runtime_checks(rom,ui,check,trials):
    import bloom_probe as B
    import critical_path as CP
    import probe as P
    import wood_probe as W
    B.configure(SimpleNamespace(map=str(rom.directory/'bartgame.map'),assets_header=str(rom.directory/'assets.h')))
    P.ROM=str(rom.directory/'bartgame.gba')
    c=P.boot(rom=P.ROM,seed=0xB4A7);CP.dismiss(c);P.run(c,12)
    pl=P.sym('gPl');rows=[];map_trace=[]
    def crop(plane,box):
        x0,y0,x1,y1=box
        return b''.join(plane[(y*240+x0)*2:(y*240+x1)*2] for y in range(y0,y1))
    def capture(label):
        plane,positions=hud_plane(c)
        allowed=lambda x,y:y<12 or 222<=x<238 and 142<=y<158
        check(ui,'runtime_hud',label+' stays within compact top HUD and16px minimap',
              bool(positions) and all(allowed(x,y) for x,y in positions),
              {'painted_pixels':len(positions),'top_max_y':max((y for x,y in positions if y<142),default=-1),
               'outside_regions':sum(not allowed(x,y) for x,y in positions)})
        check(ui,'runtime_hud',label+' central top gap stays transparent',
              not any(116<=x<148 and y<12 for x,y in positions))
        return plane
    def map_information(label):
        data=B.bytes_at(c,0x06010000+1008*32,128)
        pixels=decode_sprite(data,16,16)
        game=P.sym('gGame');world=P.sym('gWorld');state=CP.world(c)
        area=P.r8(c,game+1);here=P.r8(c,game+2) if area==1 else state['entry']
        valid=[];seen_count=0
        for index in range(25):
            seen=bool(P.r8(c,world+4+index*13+11)&1);seen_count+=seen
            cx=1+(index%5)*3;cy=1+(index//5)*3
            cell=[pixels[(cy+y)*16+cx+x] for y in range(2) for x in range(2)]
            if index==here:
                expected=[rom.defs['UI_INK_PALE'],rom.defs['UI_INK_RED']]*2 if area==1 else [rom.defs['UI_INK_CREAM']]*4
            elif not seen:expected=[rom.defs['UI_INK_RAISED']]*4
            elif index==state['goal']:expected=[rom.defs['UI_INK_GOLD']]*4
            else:expected=[rom.defs['OBJ_INK_GREEN_LIT']]*2+[rom.defs['OBJ_INK_GREEN']]*2
            valid.append(cell==expected)
        check(ui,'runtime_minimap',label+' shows exact current/explored/goal state for all25 cells',all(valid),
              {'area':area,'current':here,'explored':seen_count,'matching_cells':sum(valid)})
        entry=next((o for o in B.oam(c) if o['tile']==1008 and o['priority']==0),None)
        check(ui,'runtime_minimap',label+' uses a native16x16 bottom-right map',entry is not None and
              (entry['x'],entry['y'],entry['shape'],entry['size'])==(222,142,0,1))
        map_trace.append({'label':label,'area':area,'current':here,'seen':seen_count,'sha256':SHA(data)})
        return pixels
    P.w16(c,pl,52);P.w16(c,pl+2,80);P.w16(c,pl+4,999)
    P.w8(c,pl+7,7);P.w8(c,pl+35,11)
    for index,value in enumerate((2,1,6)):P.w8(c,pl+9+index,value)
    P.run(c,4);normal=capture('max hearts / gilt999 / three equipment slots')
    mini,data=rom.sheet('huditems');stride=mini['frame_tiles']*32
    active=[o for o in B.oam(c) if o['priority']==0]
    expected_tiles={876+16*slot for slot in range(3)}|{1008}
    check(ui,'runtime_hud','ordinary-play HUD OAM contains equipped pictograms plus minimap',
          {o['tile'] for o in active}==expected_tiles and len(active)==4)
    for slot,name in enumerate(('BOMBS','SWORD','BOW')):
        frame=rom.defs['F_ICON32_'+name];tile=876+16*slot
        source=data[frame*stride:(frame+1)*stride]
        check(ui,'runtime_hud',f'slot{slot} uploads the exact selected {name.lower()} frame',
              B.bytes_at(c,0x06010000+tile*32,stride)==source)
        entry=next((o for o in active if o['tile']==tile),None)
        expected_pal=rom.array('huditems_frame_pal')[frame]
        check(ui,'runtime_hud',f'slot{slot} uses the item material palette',
              entry is not None and entry['pal']==expected_pal)
    map_information('Drain entry')
    P.w8(c,pl+6,255);P.run(c,4);changed=capture('hidden key count changed')
    check(ui,'runtime_hud','keys never alter HUD pixels',normal==changed)
    P.w8(c,pl+7,8);P.run(c,4);bombs=capture('equipped bomb ammunition changed')
    check(ui,'runtime_ammo','bomb changes affect only the equipped bomb pod',
          crop(bombs,(148,0,178,12))!=crop(changed,(148,0,178,12)) and
          crop(bombs,(178,0,238,12))==crop(changed,(178,0,238,12)))
    P.w8(c,pl+35,12);P.run(c,4);arrows=capture('equipped bow ammunition changed')
    check(ui,'runtime_ammo','arrow changes affect only the equipped bow pod',
          crop(arrows,(208,0,238,12))!=crop(bombs,(208,0,238,12)) and
          crop(arrows,(148,0,208,12))==crop(bombs,(148,0,208,12)))
    P.w16(c,pl,48);heart_trace=[]
    for tick in range(4):
        P.run(c,1);plane,_=hud_plane(c)
        heart_trace.append({'tick':tick+1,'hp':P.r16(c,pl),'changed':plane!=arrows,
                           'cached_hp':P.r16(c,B.static_symbol('sHudHp'))})
    first=next((r['tick'] for r in heart_trace if r['changed']),None)
    check(ui,'runtime_hud','heart damage reaches hardware within2 VBlanks',first is not None and first<=2,heart_trace)
    P.w16(c,pl+4,0)
    for index,value in enumerate((0,0,0)):P.w8(c,pl+9+index,value)
    P.run(c,4);empty=capture('gilt0 / empty equipment')
    check(ui,'runtime_hud','removing equipment changes hardware',empty!=arrows)
    check(ui,'runtime_hud','gilt cache updates to0',P.r32(c,B.static_symbol('sPurseGilt'))==0)
    cache=B.static_symbol('sHudEq')
    check(ui,'runtime_hud','all equipment caches update to empty',all(P.r8(c,cache+i)==0 for i in range(3)))
    check(ui,'runtime_hud','empty equipment retains only the minimap HUD sprite',
          [o['tile'] for o in B.oam(c) if o['priority']==0]==[1008])
    P.w8(c,pl+7,9);P.w8(c,pl+35,13);P.run(c,4);hidden=capture('unequipped ammunition changed')
    check(ui,'runtime_ammo','ammunition is hidden when its item is unequipped',hidden==empty)
    P.w8(c,pl+9,6);P.run(c,4);bow_only=capture('bow equipped without bombs')
    P.w8(c,pl+7,10);P.run(c,4);bomb_hidden,_=hud_plane(c)
    check(ui,'runtime_ammo','bomb count does not alter an equipped bow HUD',bomb_hidden==bow_only)
    P.w8(c,pl+35,14);P.run(c,4);bow_updated,_=hud_plane(c)
    check(ui,'runtime_ammo','equipped bow still updates its own count',bow_updated!=bow_only)
    P.w8(c,pl+9,0);P.run(c,4)
    P.press(c,'START',2,8)
    check(ui,'runtime_menu','Start opens actual pause page',P.r8(c,P.sym('gGame'))==4)
    P.press(c,'R',2,8);P.press(c,'R',2,8);P.press(c,'A',2,8);P.press(c,'B',2,8)
    P.press(c,'START',2,8)
    check(ui,'runtime_menu','normal pause navigation returns to gameplay',P.r8(c,P.sym('gGame'))==1)
    capture('HUD restored after menu pool reuse');map_information('After pause navigation')
    P.enter_forest(c);CP.dismiss(c);P.run(c,12)
    first_map=map_information('Forest entry')
    state=CP.world(c);current=P.r8(c,P.sym('gGame')+2)
    other=next((i for i,cell in enumerate(state['cells']) if i not in (current,state['goal']) and cell['role']==0),
               next(i for i in range(25) if i not in (current,state['goal'])))
    import lift_probe as L
    L.warp(c,other,2);CP.dismiss(c);P.run(c,8)
    second_map=map_information('Visited another forest room')
    check(ui,'runtime_minimap','current-room marker changes after real room transition',first_map!=second_map)
    # Existing isolated ordinary-enemy contact fixture, no visual substitution.
    c=B.boot(P.ROM);B.floor_fixture(c,rom.defs)
    for hp_max in (24,80):
        for trial in range(trials):
            actor,pl=B.reset_player(c);P.w16(c,pl,hp_max);P.w16(c,pl+2,hp_max);P.run(c,12)
            enemy=W.spawn_enemy(c,0,100,100);at=P.sym('gActors')+enemy*64
            P.w8(c,at+31,8);P.w8(c,at+47,2);P.w8(c,at+29,200);P.w16(c,at+32,0)
            P.press(c,'B',2,3)
            P.w16(c,at+8,0);P.w16(c,at+10,256);P.w16(c,at+12,0);P.w16(c,at+14,230)
            action_tile=P.r16(c,B.static_symbol('sActionTile'));contact=None;replacement=None;old_oam=None;trace=[]
            for tick in range(12):
                P.run(c,1);live=B.live(c);oam=B.bytes_at(c,0x07000000,1024)
                trace.append({'video':tick,'logic':P.r32(c,P.sym('gGame')+8),'vblank':P.r32(c,P.sym('gFrame')),
                    **live,'hp':P.r16(c,pl),'hardware_sword_effect':B.effect(c,action_tile) is not None})
                if contact is None and live['state']==3:contact=tick;old_oam=oam
                elif contact is not None and replacement is None and oam!=old_oam:replacement=tick
            valid=contact is not None and replacement is not None
            check(ui,'runtime_damage',f'HPmax{hp_max} trial{trial} ordinary contact occurs',valid)
            if valid:
                delay=replacement-contact
                check(ui,'runtime_damage',f'HPmax{hp_max} trial{trial} replacement OAM within1 frame',delay<=1,delay)
                check(ui,'runtime_damage',f'HPmax{hp_max} trial{trial} sword clears on hurt',trace[contact]['active']==0)
                check(ui,'runtime_damage',f'HPmax{hp_max} trial{trial} no sword effect after replacement',not trace[replacement]['hardware_sword_effect'])
                rows.append({'max_hp':hp_max,'trial':trial,'replacement_delay':delay,'trace':trace})
    return {'emulator':'mGBA0.10.5','damage_samples':rows,'hud_hp_upload_trace':heart_trace,'minimap_trace':map_trace,
        'fixture_note':'Inventory/resources are explicit HUD state fixtures; action timing uses an isolated ordinary enemy on a local floor fixture. All observed art is real ROM OAM/VRAM.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frozen',default='/workspace/setup/drain-ui-final')
    parser.add_argument('--baseline',default='/workspace/setup/sewer-concepts-v3/v0')
    parser.add_argument('--variants',nargs='+',type=int,default=list(range(6)))
    parser.add_argument('--out',default='/workspace/setup/drain-ui-final/audit.json')
    parser.add_argument('--runtime',action='store_true')
    parser.add_argument('--runtime-trials',type=int,default=3)
    parser.add_argument('--export-source',type=int)
    args=parser.parse_args()
    if args.export_source is not None:source_export(args.export_source);return 0
    return Audit(args).run()

if __name__=='__main__':raise SystemExit(main())

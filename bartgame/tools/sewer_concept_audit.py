#!/usr/bin/env python3
"""Independent static ROM/art scope audit for the nine frozen Drain builds.

The source painter supplies native indexed images; this script does not import
build_assets, its Tileset deduplicator, parse_art or tile_bytes packer. It reads
actual 4bpp nibbles from the ROM, applies each hardware BG quarter's flips and
palette selection, and compares every active tile frame and keeper frame.
Unrelated assets are compared as resolved payloads, never relocated pointers.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys

ROOT=Path(__file__).resolve().parent.parent
FROZEN=Path('/workspace/setup/sewer-concepts')
CONTRACT=json.loads((ROOT/'art/reboot_contracts.json').read_text())
ROOM=CONTRACT['rooms'][0]
ACTIVE=sorted({n for layer in ('ground','overlay') for row in ROOM[layer] for n in row if n})
CONTRACT_TILES={t['name']:t for t in CONTRACT['tiles']}
KEEPERS={'peddler_head','peddler_body','gatekeeper','wisp'}
FACE_EXCEPTIONS={'peddler','gatekeeper'}
RELEASED_SHA='547674bfd44f79cd5614f3188bad86f8ed8a4a9ea9cee060e1236ca0c832c97a'
SHAPES={(8,8),(16,16),(32,32),(64,64),(16,8),(32,8),(32,16),(64,32),(8,16),(8,32),(16,32),(32,64)}
sha=lambda x:hashlib.sha256(x).hexdigest()


def rgb555(color):
    values=[int(color[i:i+2],16) for i in (1,3,5)]
    assert all(value%8==0 for value in values),(color,'source is not native RGB555')
    return sum((value//8)<<(index*5) for index,value in enumerate(values))


def source_export(variant):
    """Called in a clean subprocess so per-recipe import caches cannot leak."""
    os.environ['BART_SEWER']=str(variant)
    sys.path.insert(0,str(ROOT/'art'))
    import sewer_concepts as recipes
    import reboot_core as core
    import reboot_terrain as base_terrain
    import reboot_actors as base_actors
    import reboot_ui as base_ui
    recipe=recipes.recipe(variant)
    if variant:
        import sewer_concepts_terrain as terrain
        import sewer_concepts_npcs as npcs
        palette=terrain.palette(recipe['style'])
    else:
        palette=core.PALETTES['drain']
    output={'variant':variant,'recipe':recipe,'palette':[rgb555(c) for c in palette],
            'tiles':{},'sprites':{},'palettes':{}}
    for name in ACTIVE:
        images=[]
        for phase in range(CONTRACT_TILES[name]['frames']):
            image=terrain.paint(name,phase,recipe) if variant else base_terrain.paint(name,phase)[0]
            assert image.mode=='P' and image.size==(16,16),(variant,name,phase,image.mode,image.size)
            indices=list(image.getdata())
            assert max(indices)<=15 and min(indices)>=0
            images.append(bytes(indices).hex())
        output['tiles'][name]=images
    sheet_specs={s['name']:s for s in CONTRACT['sheets']}
    if variant:
        painters={'peddler_head':(npcs.peddler_head,recipe['peddler']),
                  'peddler_body':(npcs.peddler_body,recipe['peddler']),
                  'gatekeeper':(npcs.wizard,recipe['wizard']),
                  'wisp':(npcs.flame,recipe['wizard'])}
        output['palettes']['peddler']=[rgb555(c) for c in npcs.peddler_palette(recipe['peddler'])]
        output['palettes']['gatekeeper']=[rgb555(c) for c in npcs.wizard_palette(recipe['wizard'])]
    else:
        painters={'peddler_head':(lambda style,name:base_actors.peddler_head(name),0),
                  'peddler_body':(lambda style,name:base_actors.peddler_body(name),0),
                  'gatekeeper':(lambda style,name:base_actors.gatekeeper_frame(name),0),
                  'wisp':(lambda style,name:base_actors.wisp_frame(name),0)}
        output['palettes']['peddler']=[rgb555(c) for c in core.PALETTES['gold']]
        output['palettes']['gatekeeper']=[rgb555(c) for c in core.PALETTES['stone']]
    for sheet,(painter,style) in painters.items():
        output['sprites'][sheet]={}
        names=list(sheet_specs[sheet]['frames'])
        if variant and sheet=='peddler_body':names.append('breathe')
        for name in names:
            image=painter(style,name)
            assert image.mode=='P' and max(image.getdata())<=15
            output['sprites'][sheet][name]={'size':list(image.size),'pixels':bytes(image.getdata()).hex()}
    if variant:
        rail=terrain.rail_sprite(recipe['metal'])
        assert rail.mode=='P' and rail.size==(16,8) and max(rail.getdata())<=15
        output['sprites']['sewerrail']={'rail':{'size':[16,8],'pixels':bytes(rail.getdata()).hex()}}
        output['palettes']['sewerrail']=[rgb555(c) for c in core.PALETTES['gold']]
    output['sprites']['face']={}
    for name in FACE_EXCEPTIONS:
        if variant:
            style=recipe['peddler' if name=='peddler' else 'wizard']
            image=npcs.portrait(style,name)
        else:image=base_ui.portrait(name)
        assert image.mode=='P' and image.size==(48,48) and max(image.getdata())<=15
        pixels=bytearray(4096)
        for y in range(48):pixels[y*64:y*64+48]=bytes(image.crop((0,y,48,y+1)).getdata())
        output['sprites']['face'][name]={'size':[64,64],'pixels':bytes(pixels).hex()}
    print(json.dumps(output,separators=(',',':')))


class NativeRom:
    def __init__(self,directory):
        self.directory=Path(directory)
        self.rom=(self.directory/'bartgame.gba').read_bytes()
        self.header=(self.directory/'assets.h').read_text()
        self.linker=(self.directory/'bartgame.map').read_text()
        self.defs={name:int(value,0) for name,value in re.findall(r'^#define\s+(\w+)\s+(0x[\da-fA-F]+|\d+)\b',self.header,re.M)}
        self.symbols={name:int(address,16) for address,name in re.findall(r'^\s+0x([\da-fA-F]{8,16})\s+([A-Za-z_]\w*)\s*$',self.linker,re.M)}
        self.sections={name:(int(address,16),int(size,16)) for name,address,size in re.findall(r'^\s+\.rodata\.(\w+)\s+0x([\da-fA-F]+)\s+0x([\da-fA-F]+)\s+\S*assets\.o\s*$',self.linker,re.M) if int(address,16)>=0x08000000}
        self.tile_ids={name[3:]:value for name,value in self.defs.items() if name.startswith('MT_')}
        self.sheet_ids={name[6:].lower():value for name,value in self.defs.items() if name.startswith('SHEET_') and not name.endswith(('_TILES','_FRAMES','_COUNT'))}

    def read(self,address,size):
        offset=address-0x08000000
        assert 0<=offset and offset+size<=len(self.rom),(hex(address),size)
        return self.rom[offset:offset+size]

    def unpack(self,fmt,address):
        return struct.unpack(fmt,self.read(address,struct.calcsize(fmt)))

    def array(self,name):
        address,size=self.sections[name]
        assert self.symbols.get(name,address)==address,(name,'map symbol/section disagreement')
        return self.read(address,size)

    def tileset(self,name):
        index=self.defs['TS_'+name.upper()]
        tiles,count,mapping,anim,nanim,pals,npals=self.unpack('<IH2xIIB3xIB3x',self.symbols['tilesets']+index*28)
        animations=[]
        for i in range(nanim):
            base,frames,speed,data=self.unpack('<HBBI',anim+i*8)
            animations.append({'base':base,'frames':frames,'speed':speed,'data':self.read(data,frames*128)})
        return {'tiles':self.read(tiles,count*32),'tile_count':count,'map':self.read(mapping,self.defs['METATILE_COUNT']*8),
                'palettes':self.read(pals,npals*32),'palette_count':npals,'animations':animations}

    def sheet(self,name):
        data,count,frame_tiles,shape,size,pal,width,height=self.unpack('<IH6B',self.symbols['sheets']+self.sheet_ids[name]*12)
        return {'tile_count':count,'frame_tiles':frame_tiles,'shape':shape,'size':size,'pal':pal,'width':width,'height':height},self.read(data,count*32)


def decode_8x8(block):
    assert len(block)==32
    # Decode each byte's low/high nibble into two consecutive pixels.
    result=[]
    for value in block:result.extend((value&15,value>>4))
    return result


def decode_sprite(data,width,height):
    result=bytearray(width*height)
    for tile in range(width*height//64):
        pixels=decode_8x8(data[tile*32:tile*32+32])
        ox=(tile%(width//8))*8;oy=(tile//(width//8))*8
        for y in range(8):result[(oy+y)*width+ox:(oy+y)*width+ox+8]=bytes(pixels[y*8:y*8+8])
    return bytes(result)


def decode_metatile(rom,ts,name):
    index=rom.tile_ids[name.upper()]
    entries=struct.unpack_from('<4H',ts['map'],index*8)
    animations=[a for a in ts['animations'] if a['base']==entries[0]&1023]
    assert len(animations)<=1,(name,'duplicate animation base')
    animation=animations[0] if animations else None
    frame_count=animation['frames'] if animation else 1
    output=[]
    for frame in range(frame_count):
        inks=bytearray(256);rgb=[]
        quarters=[]
        for q,entry in enumerate(entries):
            tile=entry&1023;palette=entry>>12
            assert tile<ts['tile_count'] and palette<ts['palette_count'],(name,tile,palette)
            block=animation['data'][frame*128+q*32:frame*128+(q+1)*32] if animation else ts['tiles'][tile*32:(tile+1)*32]
            pixels=decode_8x8(block)
            colors=struct.unpack_from('<16H',ts['palettes'],palette*32)
            for y in range(8):
                for x in range(8):
                    source_x=(7-x) if entry&0x400 else x
                    source_y=(7-y) if entry&0x800 else y
                    value=pixels[source_y*8+source_x]
                    inks[(q//2*8+y)*16+q%2*8+x]=value
            quarters.append(colors)
        for y in range(16):
            for x in range(16):
                value=inks[y*16+x]
                rgb.append(quarters[(y//8)*2+x//8][value] if value else 0x8000)
        output.append((bytes(inks),struct.pack('<256H',*rgb)))
    return {'entries':list(entries),'frames':output,'speed':animation['speed'] if animation else None}


class Audit:
    def __init__(self,args):
        self.args=args;self.base=NativeRom(args.baseline);self.checks=[];self.variants=[]
    def check(self,variant,group,name,passed,detail=None):
        row={'variant':variant,'group':group,'name':name,'passed':bool(passed)}
        if detail is not None:row['detail']=detail
        self.checks.append(row)
        if not passed:print('FAIL',variant,group,name,detail,flush=True)
    def equal(self,variant,group,name,a,b):
        self.check(variant,group,name,a==b,None if a==b else {'before_sha256':sha(a),'after_sha256':sha(b),'before_bytes':len(a),'after_bytes':len(b)})
    def scope(self,variant,rom):
        before=self.base
        self.check(variant,'identifiers','all metatile IDs stable',rom.tile_ids==before.tile_ids)
        self.check(variant,'identifiers','all original sprite sheet IDs stable',all(rom.sheet_ids.get(name)==index for name,index in before.sheet_ids.items()))
        expected_new={'sewerrail'} if variant else set()
        self.check(variant,'identifiers','only approved appended sewerrail sheet exists',set(rom.sheet_ids)-set(before.sheet_ids)==expected_new)
        if variant:
            self.check(variant,'identifiers','sewerrail appended after all original sheet IDs',rom.sheet_ids.get('sewerrail')==before.defs['SHEET_COUNT'])
        for area in ('forest','myst'):
            a,b=before.tileset(area),rom.tileset(area)
            for field in ('tile_count','palette_count'):
                self.check(variant,'retained_'+area,field,a[field]==b[field],b[field])
            for field in ('tiles','map','palettes'):
                self.equal(variant,'retained_'+area,field,a[field],b[field])
            self.check(variant,'retained_'+area,'animation metadata and complete frame payloads',a['animations']==b['animations'])
        for area in ('forest','myst','sewer'):
            ts=rom.tileset(area)
            self.check(variant,'native_limits',area+' hardware BG tile budget',ts['tile_count']<=1024,ts['tile_count'])
            self.check(variant,'native_limits',area+' palette bank budget',ts['palette_count']<=rom.defs['PAL_AREA_SLOTS'],ts['palette_count'])
            colors=struct.unpack('<%dH'%(len(ts['palettes'])//2),ts['palettes'])
            self.check(variant,'native_limits',area+' all colors fit RGB555',all(c<0x8000 for c in colors))
        for name in before.sheet_ids:
            a,apixels=before.sheet(name);b,bpixels=rom.sheet(name)
            self.check(variant,'sprite_contracts',name+' canvas/shape/frame count/palette slot',a==b)
            self.check(variant,'native_limits',name+' legal hardware canvas',(b['width'],b['height']) in SHAPES and b['frame_tiles']*64==b['width']*b['height'])
            if name in KEEPERS:continue
            if name=='face':
                stride=a['frame_tiles']*32
                for frame in range(before.defs['SHEET_FACE_FRAMES']):
                    allowed={before.defs['F_FACE_'+n.upper()] for n in FACE_EXCEPTIONS}
                    if frame in allowed:continue
                    self.equal(variant,'retained_face_pixels','face frame'+str(frame),apixels[frame*stride:(frame+1)*stride],bpixels[frame*stride:(frame+1)*stride])
            else:self.equal(variant,'retained_sprite_pixels',name,apixels,bpixels)
        # Generated assets.o rodata arrays carry the complete UI/font/title,
        # item data and contact clocks. Pointer-bearing tables are validated
        # through resolved descriptors above, not compared as raw addresses.
        special={'tilesets','sheets','room_defs','pal_bg','pal_obj','pal_face','orb_glow','sheet_face_tiles'}
        special|={'sheet_'+name+'_tiles' for name in KEEPERS}
        protected=[]
        for name in before.sections:
            if name in special or 'sewer' in name and not name.startswith('room_'):continue
            if name.startswith('tile_anims_'):continue
            if name.startswith('sheet_'):continue # sheet descriptors resolved above
            if name.startswith(('tileset_','metatile_map_','tile_anim_')):continue # area descriptors resolved above
            protected.append(name)
            self.check(variant,'retained_scalar_assets',name+' exists',name in rom.sections)
            if name in rom.sections:self.equal(variant,'retained_scalar_assets',name,before.array(name),rom.array(name))
        for name,allow,count in [('pal_obj',{'peddler','gatekeeper'},before.defs['PAL_OBJ_COUNT']),
                                 ('pal_bg',{'drain'},before.defs['PAL_BG_COUNT'])]:
            prefix='PAL_OBJ_' if name=='pal_obj' else 'PAL_BG_'
            allowed={before.defs[prefix+n.upper()] for n in allow}
            for bank in range(count):
                if bank in allowed:continue
                self.equal(variant,'retained_palettes',name+' bank'+str(bank),before.array(name)[bank*32:(bank+1)*32],rom.array(name)[bank*32:(bank+1)*32])
        for bank in range(before.defs['SHEET_FACE_FRAMES']):
            if bank in {before.defs['F_FACE_'+n.upper()] for n in FACE_EXCEPTIONS}:continue
            self.equal(variant,'retained_palettes','portrait bank'+str(bank),before.array('pal_face')[bank*32:(bank+1)*32],rom.array('pal_face')[bank*32:(bank+1)*32])
        return {'protected_linked_scalar_arrays':protected,'protected_sprite_sheets':len(before.sheet_ids)-len(KEEPERS)-1,
                'protected_individual_portraits':before.defs['SHEET_FACE_FRAMES']-len(FACE_EXCEPTIONS)}
    def art(self,variant,rom):
        result=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--export-source',str(variant)],capture_output=True,text=True,check=True)
        source=json.loads(result.stdout)
        ts=rom.tileset('sewer');frames=0;changed=0;source_hashes={};contract_anim=0;moving=0
        self.check(variant,'source_art','source active IDs cover all370 room IDs',set(source['tiles'])==set(ACTIVE) and len(ACTIVE)==370)
        for name in ACTIVE:
            actual=decode_metatile(rom,ts,name);expected=source['tiles'][name];spec=CONTRACT_TILES[name]
            self.check(variant,'native_drain_art',name+' frame count',len(actual['frames'])==len(expected)==spec['frames'])
            self.check(variant,'native_drain_art',name+' frame hold matches contract',actual['speed']==(spec['anim_speed'] if spec['frames']>1 else None))
            before=decode_metatile(self.base,self.base.tileset('sewer'),name)
            if [x[1] for x in actual['frames']]!=[x[1] for x in before['frames']]:changed+=1
            source_hashes[name]=[]
            if spec['frames']>1:contract_anim+=1
            for phase,(hex_pixels,(inks,colors)) in enumerate(zip(expected,actual['frames'])):
                indices=bytes.fromhex(hex_pixels);label=name+' frame'+str(phase)
                self.equal(variant,'source_indexed_pixels',label,indices,inks)
                expected_colors=struct.pack('<256H',*[source['palette'][i] if i else 0x8000 for i in indices])
                self.equal(variant,'source_rgb555_pixels',label,expected_colors,colors)
                source_hashes[name].append({'phase':phase,'indexed_sha256':sha(indices),'rendered_rgb555_sha256':sha(expected_colors)})
                frames+=1
            if spec['frames']>1 and len({row['indexed_sha256'] for row in source_hashes[name]})>1:moving+=1
        self.check(variant,'source_art','all623 native tile frames decoded',frames==623,frames)
        self.check(variant,'source_art','all38 animation descriptors present',contract_anim==len(ts['animations'])==38,len(ts['animations']))
        self.equal(variant,'source_palettes','Drain resident RGB555 bank',struct.pack('<16H',*source['palette']),ts['palettes'])
        keeper_frames=0;rail_frames=0;keeper_hashes={}
        for sheet,images in source['sprites'].items():
            metadata,pixels=rom.sheet(sheet);stride=metadata['frame_tiles']*32
            keeper_hashes[sheet]={}
            for name,image in images.items():
                index=rom.defs['F_'+sheet.upper()+'_'+name.upper()]
                selected=pixels[index*stride:(index+1)*stride]
                decoded=decode_sprite(selected,metadata['width'],metadata['height'])
                indices=bytes.fromhex(image['pixels'])
                self.check(variant,'keeper_native_art',sheet+'.'+name+' exact native dimensions',image['size']==[metadata['width'],metadata['height']])
                self.equal(variant,'keeper_native_art',sheet+'.'+name+' independently decoded source pixels',indices,decoded)
                keeper_hashes[sheet][name]=sha(decoded)
                if sheet=='sewerrail':rail_frames+=1
                else:keeper_frames+=1
        expected_keeper_frames=32 if variant else 31
        self.check(variant,'keeper_native_art','all retained keeper/portrait frames plus concept breathing pose verified',
                   keeper_frames==expected_keeper_frames,keeper_frames)
        for spec in CONTRACT['sheets']:
            if spec['name'] not in KEEPERS:continue
            for index,name in enumerate(spec['frames']):
                self.check(variant,'keeper_frame_contract',spec['name']+'.'+name+' retains original frame ID',
                           rom.defs['F_'+spec['name'].upper()+'_'+name.upper()]==index)
        self.check(variant,'keeper_frame_contract','Peddler body has only the approved extra breathing frame in concepts',
                   rom.defs['SHEET_PEDDLER_BODY_FRAMES']==(15 if variant else 14))
        if variant:
            self.check(variant,'keeper_frame_contract','new breathing pose appends after the14 retained body frames',
                       rom.defs['F_PEDDLER_BODY_BREATHE']==14)
            rest=bytes.fromhex(source['sprites']['peddler_body']['rest']['pixels'])
            breath=bytes.fromhex(source['sprites']['peddler_body']['breathe']['pixels'])
            self.check(variant,'keeper_idle_pose','breathing preserves the bottom three foot/contact rows',
                       rest[-96:]==breath[-96:])
            self.check(variant,'keeper_idle_pose','breathing articulates the upper mass instead of duplicating rest',
                       rest[:-96]!=breath[:-96])
        self.check(variant,'rail_native_art','exactly one approved16x8 rail frame in concepts',rail_frames==(1 if variant else 0),rail_frames)
        if variant:
            metadata,_=rom.sheet('sewerrail')
            self.check(variant,'rail_native_art','rail canvas/tile count/palette/frame count',
                       metadata['width']==16 and metadata['height']==8 and metadata['frame_tiles']==2 and metadata['tile_count']==2 and metadata['shape']==1 and metadata['size']==0 and metadata['pal']==rom.defs['PAL_OBJ_FX'])
            bank=metadata['pal']
            self.equal(variant,'rail_native_art','rail uses unchanged global gold OBJ palette',struct.pack('<16H',*source['palettes']['sewerrail']),rom.array('pal_obj')[bank*32:(bank+1)*32])
        for name in ('peddler','gatekeeper'):
            pal=struct.pack('<16H',*source['palettes'][name]);bank=rom.defs['PAL_OBJ_'+name.upper()]
            self.equal(variant,'source_palettes',name+' OBJ bank',pal,rom.array('pal_obj')[bank*32:(bank+1)*32])
            face=rom.defs['F_FACE_'+name.upper()]
            self.equal(variant,'source_palettes',name+' portrait bank',pal,rom.array('pal_face')[face*32:(face+1)*32])
        return {'recipe':source['recipe'],'native_tile_frames':frames,'animated_metatile_ids':contract_anim,'animated_ids_with_changing_pixels':moving,'keeper_and_portrait_frames':keeper_frames,'new_rail_frames':rail_frames,
                'changed_rendered_metatile_ids':changed,'source_frame_hashes':source_hashes,'keeper_source_hashes':keeper_hashes}
    def run(self):
        files=['sewer_concepts.py','sewer_concepts_terrain.py','sewer_concepts_npcs.py','reboot_core.py','reboot_terrain.py','reboot_actors.py','reboot_ui.py','reboot_contracts.json']
        snapshot={name:sha((ROOT/'art'/name).read_bytes()) for name in files}
        self.check(0,'default_release','BART_SEWER0 equals released Step-and-cut ROM',sha(self.base.rom)==RELEASED_SHA,sha(self.base.rom))
        for variant in self.args.variants:
            path=Path(self.args.frozen)/('v'+str(variant));rom=NativeRom(path)
            self.check(variant,'build_recipe','header selects requested sewer profile',rom.defs.get('BART_SEWER_VARIANT')==variant,rom.defs.get('BART_SEWER_VARIANT'))
            detail=self.scope(variant,rom);detail.update(self.art(variant,rom))
            detail.update({'variant':variant,'rom_sha256':sha(rom.rom),'rom_bytes':len(rom.rom),
                           'budgets':{area:{'subtiles':rom.tileset(area)['tile_count'],'palette_banks':rom.tileset(area)['palette_count']} for area in ('forest','myst','sewer')}})
            self.variants.append(detail)
            rows=[r for r in self.checks if r['variant']==variant]
            print('VARIANT',variant,'PASS' if all(r['passed'] for r in rows) else 'FAIL',sum(r['passed'] for r in rows),'/',len(rows),flush=True)
        self.check(0,'source_snapshot','source painter snapshot remained unchanged throughout audit',snapshot=={name:sha((ROOT/'art'/name).read_bytes()) for name in files})
        report={'method':__doc__.strip(),'baseline_sha256':sha(self.base.rom),'variants':self.variants,
                'source_file_sha256':snapshot,
                'passed':sum(r['passed'] for r in self.checks),'total':len(self.checks),'checks':self.checks,
                'failures':[r for r in self.checks if not r['passed']],
                'limits':'Static payload/source verification proves authored native images survive ROM encoding and unrelated art stays exact. It does not prove visual taste, gameplay traversal, runtime animation phase selection or OAM presentation. Unlinked/discarded arrays have no ROM payload to compare; use the separate real-mGBA review for those.'}
        Path(self.args.out).write_text(json.dumps(report,indent=2)+'\n')
        print('RESULT','FAIL' if report['failures'] else 'PASS',str(report['passed'])+'/'+str(report['total']))
        return int(bool(report['failures']))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frozen',default=str(FROZEN));parser.add_argument('--baseline',default=str(FROZEN/'v0'))
    parser.add_argument('--variants',nargs='+',type=int,default=list(range(9)))
    parser.add_argument('--out',default=str(FROZEN/'audit-scope.json'))
    parser.add_argument('--export-source',type=int)
    args=parser.parse_args()
    if args.export_source is not None:source_export(args.export_source);return 0
    return Audit(args).run()

if __name__=='__main__':raise SystemExit(main())

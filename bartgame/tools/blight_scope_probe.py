"""Verify artwork-only scope against a frozen ROM, without booting an emulator.

python tools/blight_scope_probe.py --out /workspace/setup/blight-scope.json

Decode real packed BG subtiles, flips and RGB555 palettes before comparing:
healthy forest and every resident Drain tile must render identically even
when blight additions move tile indices or palette banks. Sprite bytes,
metadata, item palette tables, OBJ colours and the title bitmap stay exact.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

ROOT=Path(__file__).resolve().parent.parent
BASELINE=Path('/workspace/setup/blight-reference-before')
ALLOW_PREFIXES=('BLIGHT','FOREST_ROT','ROT_','BTREE_','SICKTREE_','SICK_',
                'MOSS_BLIGHT','CANOPY_BLIGHT')


def digest(value):
    return hashlib.sha256(value).hexdigest()


class Rom:
    def __init__(self,rom,linker_map,header):
        self.path=Path(rom);self.data=self.path.read_bytes()
        self.defs={n:int(v,0) for n,v in re.findall(
            r'^#define\s+(\w+)\s+(0x[0-9a-fA-F]+|\d+)\b',Path(header).read_text(),re.M)}
        self.symbols={n:int(a,16) for a,n in re.findall(
            r'^\s+0x([0-9a-fA-F]{8,16})\s+([A-Za-z_]\w*)\s*$',Path(linker_map).read_text(),re.M)}
        self.metatiles={n[3:]:v for n,v in self.defs.items() if n.startswith('MT_')}
        self.sheet_names={n[6:].lower():v for n,v in self.defs.items()
                          if n.startswith('SHEET_') and not n.endswith(('_FRAMES','_TILES','_COUNT'))}

    def read(self,address,size):
        offset=address-0x08000000
        assert 0<=offset and offset+size<=len(self.data),(self.path,hex(address),size)
        return self.data[offset:offset+size]

    def named(self,name,size):
        return self.read(self.symbols[name],size)

    def unpack(self,fmt,address):
        return struct.unpack(fmt,self.read(address,struct.calcsize(fmt)))

    def tileset(self,name):
        index=self.defs['TS_'+name.upper()]
        # ARM ABI: pointers are4 bytes; padding follows each u16/u8 field.
        a=self.symbols['tilesets']+index*28
        tiles,count,mapping,animations,nanim,palettes,npal=self.unpack('<IH2xIIB3xIB3x',a)
        anim={}
        for i in range(nanim):
            tile,frames,speed,data=self.unpack('<HBBI',animations+i*8)
            anim[tile]=(frames,speed,data)
        return {'tiles':tiles,'tile_count':count,'mapping':mapping,'palettes':palettes,
                'palette_count':npal,'animations':anim}

    def tile_art(self,set_,name):
        index=self.metatiles[name]
        entries=self.unpack('<4H',set_['mapping']+index*8)
        if not any(entries):return None
        animation=set_['animations'].get(entries[0]&1023)
        count,speed=(animation[0],animation[1]) if animation else (1,None)
        frames=[]
        for frame in range(count):
            pixels=bytearray(16*16*4)
            for q,entry in enumerate(entries):
                tile=entry&1023;bank=entry>>12
                assert tile<set_['tile_count'] and bank<set_['palette_count'],(name,tile,bank)
                data=(self.read(animation[2]+frame*128+q*32,32) if animation else
                      self.read(set_['tiles']+tile*32,32))
                palette=self.unpack('<16H',set_['palettes']+bank*32)
                for y in range(8):
                    for x in range(8):
                        tx=7-x if entry&1024 else x;ty=7-y if entry&2048 else y
                        byte=data[ty*4+tx//2];ink=(byte>>(4*(tx&1)))&15
                        if not ink:continue  # transparent BG pixel; ignore colour0
                        rgb=palette[ink];r=rgb&31;g=(rgb>>5)&31;b=(rgb>>10)&31
                        at=(((q//2)*8+y)*16+(q%2)*8+x)*4
                        pixels[at:at+4]=bytes(((r<<3)|(r>>2),(g<<3)|(g>>2),(b<<3)|(b>>2),255))
            frames.append(bytes(pixels))
        return count,speed,frames

    def sheet(self,name):
        index=self.sheet_names[name]
        fields=self.unpack('<IH6B',self.symbols['sheets']+index*12)
        return fields[1:],self.read(fields[0],fields[1]*32)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--before-rom',default=str(BASELINE/'bartgame.gba'))
    ap.add_argument('--before-map',default=str(BASELINE/'bartgame.map'))
    ap.add_argument('--before-header',default=str(BASELINE/'assets.h'))
    ap.add_argument('--rom',default=str(ROOT/'bartgame.gba'))
    ap.add_argument('--map',default=str(ROOT/'build/bartgame.map'))
    ap.add_argument('--header',default=str(ROOT/'build/gen/assets.h'))
    ap.add_argument('--out',default='/workspace/setup/blight-scope.json')
    args=ap.parse_args()
    before=Rom(args.before_rom,args.before_map,args.before_header)
    after=Rom(args.rom,args.map,args.header)
    checks=[];mismatches=[];counts={}

    def check(group,name,ok,detail=None):
        row={'group':group,'name':name,'passed':bool(ok)}
        if detail is not None:row['detail']=detail
        checks.append(row)
        if not ok:mismatches.append(row)

    common=sorted(before.metatiles)
    for name in common:
        check('metatile_ids',name,name in after.metatiles and before.metatiles[name]==after.metatiles.get(name))
    skipped=[]
    for set_name in ('forest','sewer'):
        oldset,newset=before.tileset(set_name),after.tileset(set_name)
        checked=frames=0
        for name in common:
            if set_name=='forest' and name.startswith(ALLOW_PREFIXES):
                skipped.append(name);continue
            old=before.tile_art(oldset,name)
            new=after.tile_art(newset,name) if name in after.metatiles else None
            if old is None and new is None:continue
            ok=old==new
            detail=None
            if not ok:
                detail={'before':None if old is None else {'frames':old[0],'speed':old[1],'rgba_sha256':[digest(f) for f in old[2]]},
                        'after':None if new is None else {'frames':new[0],'speed':new[1],'rgba_sha256':[digest(f) for f in new[2]]}}
            check(set_name+'_rendered_art',name,ok,detail)
            checked+=1;frames+=old[0] if old else 0
        counts[set_name+'_tiles']=checked;counts[set_name+'_frames']=frames

    names=sorted(before.sheet_names,key=before.sheet_names.get)
    check('sprites','sheet names and order',before.sheet_names==after.sheet_names)
    for name in names:
        old=before.sheet(name);new=after.sheet(name)
        check('sprite_metadata',name,old[0]==new[0])
        check('sprite_pixels',name,old[1]==new[1],None if old[1]==new[1] else {'before':digest(old[1]),'after':digest(new[1])})
    counts['sprite_sheets']=len(names)

    arrays={'pal_obj':512,'title_bitmap':240*160*2}
    for name in ('items','pick32','icon32','shield','bloomfx'):
        arrays[name+'_frame_pal']=before.defs['SHEET_'+name.upper()+'_FRAMES']
    arrays['icon32_exact_tiles']=before.defs['SHEET_ICON32_TILES']*32
    arrays['icon32_exact_pal']=before.defs['SHEET_ICON32_FRAMES']*32
    for name,size in arrays.items():
        old,new=before.named(name,size),after.named(name,size)
        check('retained_assets',name,old==new,None if old==new else {'before':digest(old),'after':digest(new)})
    report={'before_rom_sha256':digest(before.data),'rom_sha256':digest(after.data),
            'method':'Static real-ROM decoding: 4bpp subtiles, hardware flips, per-quarter palette bank and RGB555 colours; all retained animation frames. No emulator or source-art imports.',
            'allowed_blight_prefixes':ALLOW_PREFIXES,'allowed_blight_tiles':skipped,
            'counts':counts,'passed':sum(c['passed'] for c in checks),'total':len(checks),
            'mismatches':mismatches,'checks':checks}
    output=Path(args.out);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n')
    for row in mismatches:print('FAIL',row['group'],row['name'],row.get('detail',''))
    print('RESULT %s %d/%d scope checks; %d forest tiles, %d Drain tiles, %d sprite sheets'%(
        'PASS' if not mismatches else 'FAIL',report['passed'],report['total'],counts['forest_tiles'],counts['sewer_tiles'],counts['sprite_sheets']))
    return int(bool(mismatches))


if __name__=='__main__':raise SystemExit(main())

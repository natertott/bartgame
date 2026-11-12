#!/usr/bin/env python3
"""Compare protected native art in two frozen ROM/header/map bundles."""
import argparse,hashlib,json,struct
from pathlib import Path
from sewer_concept_audit import NativeRom

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',required=True);p.add_argument('--current',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();old,new=NativeRom(a.baseline),NativeRom(a.current);checks=[];appended=[];activated=[];referenced=[]
    def check(label,ok):
        checks.append({'check':label,'pass':bool(ok)})
        if not ok:print('FAIL',label)
    for name,index in old.sheet_ids.items():
        check('stable sheet ID '+name,new.sheet_ids.get(name)==index)
        before,pixels_before=old.sheet(name);after,pixels_after=new.sheet(name)
        # A sheet may append new poses without changing any existing frame or
        # its hardware geometry. Count growth alone is not an art regression;
        # reordered/repainted old pixels, a palette change or a partial frame is.
        frame_tiles=before['frame_tiles']
        geometry=all(after[key]==value for key,value in before.items() if key!='tile_count')
        complete_frames=(frame_tiles>0 and before['tile_count']%frame_tiles==0 and
                         after['tile_count']>=before['tile_count'] and after['tile_count']%frame_tiles==0)
        check('unchanged original sheet frames/geometry '+name,
              geometry and complete_frames and pixels_after[:len(pixels_before)]==pixels_before)
        if after['tile_count']>before['tile_count']:
            appended.append({'sheet':name,'original_frames':before['tile_count']//frame_tiles,
                             'current_frames':after['tile_count']//frame_tiles,
                             'original_pixels_preserved':pixels_after[:len(pixels_before)]==pixels_before})
    for name,index in old.tile_ids.items():check('stable metatile ID '+name,new.tile_ids.get(name)==index)
    for name in ('forest','sewer','myst'):
        before,after=old.tileset(name),new.tileset(name)
        if name=='forest':
            # These seventeen original IDs were deliberately all-zero in the
            # Forest bank; their first usable art is needed by newly deployed
            # regional transport. Existing pictures and their tile storage are
            # still byte-exact. No other empty slot is an implicit exception.
            permitted={'LH_MOB_'+suffix for suffix in ('WATER','PIT','RAIL_H','RAIL_V','RAIL_SE','RAIL_NW','STOP','DECK','DECK_W','DECK_E','RAMP','CLIFF','LAUNCH','SOCKET','PRIZE','OPEN','SIGN')}
            original=struct.unpack('<'+'H'*(len(before['map'])//2),before['map'])
            allowed={old.tile_ids[n]:n for n in permitted if n in old.tile_ids}
            mappings_ok=len(after['map'])>=len(before['map']);used=set(entry&1023 for entry in original)
            for animation in before['animations']:used.update(range(animation['base'],animation['base']+4))
            for index in range(len(before['map'])//8):
                a0=before['map'][index*8:index*8+8];a1=after['map'][index*8:index*8+8]
                if a0==a1:continue
                if index not in allowed or a0!=bytes(8):mappings_ok=False
                else:activated.append({'tileset':name,'metatile':allowed[index],'id':index,'original_mapping':'all zero','new_mapping':list(struct.unpack('<4H',a1))})
            check('unchanged forest original mappings; explicit empty mobility slots only',mappings_ok)
            check('unchanged forest tiles referenced by original mappings/animations',all(after['tiles'][tile*32:tile*32+32]==before['tiles'][tile*32:tile*32+32] for tile in used))
            referenced.append({'tileset':name,'protected_physical_tiles':len(used),'original_physical_tiles':before['tile_count']})
        else:
            for field in ('tiles','map'):
                check('unchanged '+name+' '+field+' prefix',after[field][:len(before[field])]==before[field])
        check('unchanged '+name+' palettes prefix',after['palettes'][:len(before['palettes'])]==before['palettes'])
        check('unchanged '+name+' animations',after['animations'][:len(before['animations'])]==before['animations'])
    for name in ('metatile_type','metatile_coll','metatile_prop','metatile_glitter','pal_obj','pal_face','title_bitmap'):
        if name in old.sections:
            before=old.array(name);check('unchanged '+name,new.array(name)[:len(before)]==before)
    result={'checks':checks,'passed':sum(c['pass'] for c in checks),'failed':sum(not c['pass'] for c in checks),
            'baseline_sheets':len(old.sheet_ids),'current_sheets':len(new.sheet_ids),
            'baseline_metatiles':len(old.tile_ids),'current_metatiles':len(new.tile_ids),
            'appended_sheet_frames':appended,
            'activated_empty_mobility_mappings':activated,
            'referenced_tile_protection':referenced,
            'baseline_rom_sha256':hashlib.sha256(old.rom).hexdigest(),
            'current_rom_sha256':hashlib.sha256(new.rom).hexdigest(),
            'tool_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'scope':'Stable sheet/metatile IDs, unchanged hardware geometry/palette and every original frame byte; complete new frames may append. Original mappings and all referenced tile pixels/animations stay protected; only explicitly listed all-zero Forest LH_MOB slots may receive new regional mechanism art. Existing other tileset/palette/title prefixes stay protected.'}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='checks'}))
    if result['failed']:raise SystemExit(1)
if __name__=='__main__':main()

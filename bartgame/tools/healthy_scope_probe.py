"""Decode the ROM to verify the regular-forest artwork pass stays in scope.

Uses the same 4bpp, flips and RGB555 decoder as blight_scope_probe. The
explicit material list authorizes healthy forest changes, not unrelated
assets. Blight-specific materials are always compared, including animation.
"""
import argparse
import json
from pathlib import Path
from blight_scope_probe import Rom, digest

ROOT=Path(__file__).resolve().parent.parent
BASELINE=Path('/workspace/setup/healthy-reference-before')
BLIGHT_PREFIXES=('BLIGHT_','CANOPY_BLIGHT','FOREST_BLIGHT_','FOREST_ROT',
                 'ROT_','BTREE_','SICKTREE_','SICK_','MOSS_BLIGHT','DEAD_TREE')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--before-rom',default=str(BASELINE/'bartgame.gba'))
    ap.add_argument('--before-map',default=str(BASELINE/'bartgame.map'))
    ap.add_argument('--before-header',default=str(BASELINE/'assets.h'))
    ap.add_argument('--rom',default=str(ROOT/'bartgame.gba'))
    ap.add_argument('--map',default=str(ROOT/'build/bartgame.map'))
    ap.add_argument('--header',default=str(ROOT/'build/gen/assets.h'))
    ap.add_argument('--changed-materials',required=True)
    ap.add_argument('--out',default='/workspace/setup/healthy-scope.json')
    args=ap.parse_args()
    declared=json.loads(Path(args.changed_materials).read_text())
    allowed={n.upper() for n in (declared['changed_names'] if isinstance(declared,dict) else declared)}
    assert not any(n.startswith(BLIGHT_PREFIXES) for n in allowed), 'blight material in healthy change list'
    before=Rom(args.before_rom,args.before_map,args.before_header)
    after=Rom(args.rom,args.map,args.header)
    checks=[];counts={};changed={};mismatches=[]

    def check(group,name,ok,detail=None):
        row={'group':group,'name':name,'passed':bool(ok)}
        if detail is not None:row['detail']=detail
        checks.append(row)
        if not ok:mismatches.append(row)

    check('metatile_contracts','names and ids',before.metatiles==after.metatiles)
    for name,index in before.metatiles.items():
        for field in ('type','coll','prop'):
            old=before.read(before.symbols['metatile_'+field]+index,1)
            new=after.read(after.symbols['metatile_'+field]+after.metatiles[name],1)
            check('metatile_contracts',name+' '+field,old==new)

    for area in ('forest','sewer','myst'):
        oldset,newset=before.tileset(area),after.tileset(area)
        retained=frames=blight_tiles=blight_frames=0;changed[area]=[]
        for name in sorted(before.metatiles):
            old=before.tile_art(oldset,name);new=after.tile_art(newset,name)
            if old is None and new is None:continue
            if old!=new:
                changed[area].append(name.lower())
                permitted=area!='sewer' and name in allowed
                detail={'allowed':permitted,'before_frames':old[0] if old else None,
                        'after_frames':new[0] if new else None}
                check('art_scope',area+' '+name,permitted,detail)
            else:
                retained+=1;frames+=old[0] if old else 0
                check('retained_art',area+' '+name,True)
            if area=='forest' and name.startswith(BLIGHT_PREFIXES):
                blight_tiles+=1;blight_frames+=old[0] if old else 0
                check('retained_blight',name,old==new)
        check('hardware_budget',area+' tiles',newset['tile_count']<=1024)
        check('hardware_budget',area+' palettes',newset['palette_count']<=12)
        counts[area]={'retained_tiles':retained,'retained_animation_frames':frames,
                      'changed_tiles':len(changed[area]),'subtiles':newset['tile_count'],
                      'palettes':newset['palette_count'],'animated_metatiles':len(newset['animations'])}
        if area=='forest':counts['retained_blight']={'tiles':blight_tiles,'animation_frames':blight_frames}

    check('sprites','sheet names and order',before.sheet_names==after.sheet_names)
    for name in before.sheet_names:
        old,new=before.sheet(name),after.sheet(name)
        check('sprite_metadata',name,old[0]==new[0])
        check('sprite_pixels',name,old[1]==new[1])
    counts['sprite_sheets']=len(before.sheet_names)
    arrays={'pal_obj':512,'title_bitmap':240*160*2}
    for name in ('items','pick32','icon32','shield','bloomfx'):
        arrays[name+'_frame_pal']=before.defs['SHEET_'+name.upper()+'_FRAMES']
    arrays['icon32_exact_tiles']=before.defs['SHEET_ICON32_TILES']*32
    arrays['icon32_exact_pal']=before.defs['SHEET_ICON32_FRAMES']*32
    for name,size in arrays.items():
        check('retained_assets',name,before.named(name,size)==after.named(name,size))
    report={'before_rom_sha256':digest(before.data),'rom_sha256':digest(after.data),
            'method':'Static ROM decoding: all resident BG animation frames, 4bpp, flips, RGB555, metadata and exact sprite/title/item arrays.',
            'declared_materials':sorted(n.lower() for n in allowed),'changed_materials':changed,
            'counts':counts,'passed':sum(c['passed'] for c in checks),'total':len(checks),
            'mismatches':mismatches,'checks':checks}
    path=Path(args.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2)+'\n')
    path.with_name(path.stem+'-changed.json').write_text(json.dumps({'changed_names':sorted(set(changed['forest']+changed['myst']))},indent=2)+'\n')
    for row in mismatches:print('FAIL',row['group'],row['name'],row.get('detail',''))
    print('RESULT %s %d/%d; %d healthy forest materials changed, %d blight materials retained'%(
        'FAIL' if mismatches else 'PASS',report['passed'],report['total'],len(changed['forest']),counts['retained_blight']['tiles']))
    return int(bool(mismatches))


if __name__=='__main__':raise SystemExit(main())

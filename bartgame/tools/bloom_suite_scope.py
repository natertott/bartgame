"""Verify Bloom action changes leave environments and unrelated artwork exact."""
import argparse
import json
from pathlib import Path
from blight_scope_probe import Rom, digest

ROOT=Path(__file__).resolve().parent.parent
BASE=Path('/workspace/setup/bloom-suite-before')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--before-rom',default=str(BASE/'bartgame.gba'))
    ap.add_argument('--before-map',default=str(BASE/'bartgame.map'))
    ap.add_argument('--before-header',default=str(BASE/'assets.h'))
    ap.add_argument('--rom',default=str(ROOT/'bartgame.gba'))
    ap.add_argument('--map',default=str(ROOT/'build/bartgame.map'))
    ap.add_argument('--header',default=str(ROOT/'build/gen/assets.h'))
    ap.add_argument('--out',default='/workspace/setup/bloom-suite-scope.json')
    args=ap.parse_args();old=Rom(args.before_rom,args.before_map,args.before_header)
    new=Rom(args.rom,args.map,args.header);checks=[];counts={}

    def check(group,name,ok):checks.append({'group':group,'name':name,'passed':bool(ok)})

    check('metatiles','all ids',old.metatiles==new.metatiles)
    for name,index in old.metatiles.items():
        for field in ('type','coll','prop'):
            check('metatiles',name+' '+field,
                  old.read(old.symbols['metatile_'+field]+index,1)==
                  new.read(new.symbols['metatile_'+field]+new.metatiles[name],1))
    for area in ('forest','sewer','myst'):
        before,after=old.tileset(area),new.tileset(area);tiles=frames=0
        for name in old.metatiles:
            a,b=old.tile_art(before,name),new.tile_art(after,name)
            if a is None and b is None:continue
            check('terrain',area+' '+name,a==b);tiles+=1;frames+=a[0] if a else 0
        counts[area]={'tiles':tiles,'animation_frames':frames,'subtiles':after['tile_count'],
                      'palettes':after['palette_count'],'animated_metatiles':len(after['animations'])}
    allowed={'hero','bloomfx','lift'}
    for name in old.sheet_names:
        before,after=old.sheet(name),new.sheet(name)
        if name=='hero':check('bloom_contracts','hero frame shape and palette',before[0][1:]==after[0][1:])
        else:check('sheet_metadata',name,before[0]==after[0])
        if name not in allowed:check('retained_sprites',name,before[1]==after[1])
    counts['retained_sprite_sheets']=len(old.sheet_names)-len(allowed)
    check('bloom_contracts','one new ground-shadow sheet',set(new.sheet_names)-set(old.sheet_names)=={'bloomshadow'})
    check('bloom_contracts','hero remains 32 resident tiles',new.sheet('hero')[0][1]==32)
    check('bloom_contracts','shadow uses only two resident tiles',new.sheet('bloomshadow')[0][0]==2)
    for prefix in ('F_HERO_','F_BLOOMFX_','F_LIFT_'):
        for name,value in old.defs.items():
            if name.startswith(prefix):check('frame_ids',name,new.defs.get(name)==value)
    before,after=old.sheet('hero')[1],new.sheet('hero')[1];stride=32*32
    for name,index in old.defs.items():
        if name.startswith(('F_HERO_IDLE_','F_HERO_WALK_')):
            check('retained_bloom',name,before[index*stride:(index+1)*stride]==after[index*stride:(index+1)*stride])
    arrays={'pal_obj':512,'title_bitmap':240*160*2}
    for name in ('items','pick32','icon32','shield','bloomfx'):
        arrays[name+'_frame_pal']=old.defs['SHEET_'+name.upper()+'_FRAMES']
    arrays['icon32_exact_tiles']=old.defs['SHEET_ICON32_TILES']*32
    arrays['icon32_exact_pal']=old.defs['SHEET_ICON32_FRAMES']*32
    for name,size in arrays.items():check('retained_assets',name,old.named(name,size)==new.named(name,size))
    failures=[c for c in checks if not c['passed']]
    counts['hero_source_frames']=new.defs['SHEET_HERO_FRAMES']
    report={'before_rom_sha256':digest(old.data),'rom_sha256':digest(new.data),
            'method':'Actual packed ROM comparison: all environment animation frames decoded to RGBA via hardware flips and RGB555; exact unrelated sprite arrays, item/title palettes and idle/walk frames; stable physical contracts and source frame ids.',
            'counts':counts,'passed':len(checks)-len(failures),'total':len(checks),
            'failures':failures,'checks':checks}
    path=Path(args.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2)+'\n')
    for c in failures:print('FAIL',c['group'],c['name'])
    print('RESULT %s %d/%d environment, retained-art and animation-contract checks'%(
        'FAIL' if failures else 'PASS',report['passed'],report['total']))
    return int(bool(failures))


if __name__=='__main__':raise SystemExit(main())

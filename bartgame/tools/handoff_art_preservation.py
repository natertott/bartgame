#!/usr/bin/env python3
"""Compare protected native art in two frozen ROM/header/map bundles."""
import argparse,json
from pathlib import Path
from sewer_concept_audit import NativeRom

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',required=True);p.add_argument('--current',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();old,new=NativeRom(a.baseline),NativeRom(a.current);checks=[]
    def check(label,ok):
        checks.append({'check':label,'pass':bool(ok)})
        if not ok:print('FAIL',label)
    for name,index in old.sheet_ids.items():
        check('stable sheet ID '+name,new.sheet_ids.get(name)==index)
        check('unchanged sheet pixels/geometry '+name,old.sheet(name)==new.sheet(name))
    for name,index in old.tile_ids.items():check('stable metatile ID '+name,new.tile_ids.get(name)==index)
    for name in ('forest','sewer','myst'):
        before,after=old.tileset(name),new.tileset(name)
        # Mystic adds surface art/palettes after its original resident data.
        for field in ('tiles','map','palettes'):
            check('unchanged '+name+' '+field+' prefix',after[field][:len(before[field])]==before[field])
        check('unchanged '+name+' animations',after['animations'][:len(before['animations'])]==before['animations'])
    for name in ('metatile_type','metatile_coll','metatile_prop','metatile_glitter','pal_obj','pal_face','title_bitmap'):
        if name in old.sections:
            before=old.array(name);check('unchanged '+name,new.array(name)[:len(before)]==before)
    result={'checks':checks,'passed':sum(c['pass'] for c in checks),'failed':sum(not c['pass'] for c in checks),
            'baseline_sheets':len(old.sheet_ids),'current_sheets':len(new.sheet_ids),
            'baseline_metatiles':len(old.tile_ids),'current_metatiles':len(new.tile_ids)}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='checks'}))
    if result['failed']:raise SystemExit(1)
if __name__=='__main__':main()

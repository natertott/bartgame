#!/usr/bin/env python3
"""Compare decoded native assets with the previous main ROM and three-enemy lab.

Pointer-bearing tables are compared through their decoded contents. The only
existing authored-room change allowed here is the appended arcade object.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from sewer_concept_audit import NativeRom

SHA=lambda b:hashlib.sha256(b).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('before','old-lab','after','out'):p.add_argument('--'+n,required=True)
    a=p.parse_args();before,lab,after=[NativeRom(x) for x in (a.before,a.old_lab,a.after)]
    rows=[]
    def check(name,ok,detail=None):
        rows.append(dict(name=name,passed=bool(ok),detail=detail));print(('PASS ' if ok else 'FAIL ')+name)
    check('normal production entry mode',after.defs['BART_ENEMY_LAB']==0)
    for n in before.sheet_ids:
        check(n+' original sprite and ID exact',before.sheet_ids[n]==after.sheet_ids[n] and before.sheet(n)==after.sheet(n))
    for n in ('proto_rope','proto_leever','proto_helmasaur'):
        check(n+' approved study pixels preserved',lab.sheet(n)==after.sheet(n))
    for n in ('forest','sewer','myst'):
        check(n+' decoded tiles/map/palettes/animations exact',before.tileset(n)==after.tileset(n))
    exclude={'sheets','tilesets','room_defs','room_sewer_main_objects'}
    for n in before.sections:
        if n in exclude or n.startswith('tile_anims_'):continue
        check(n+' native packed payload exact',n in after.sections and before.array(n)==after.array(n))
    check('old room object list retained plus one cabinet',after.array('room_sewer_main_objects')==before.array('room_sewer_main_objects')+bytes([6,24,6,0]))
    meta,pixels=after.sheet('arcade')
    check('cabinet valid32x64 two native frames',meta['width']==32 and meta['height']==64 and meta['tile_count']==64 and meta['frame_tiles']==32 and len(pixels)==2048,meta)
    changed=[]
    for i,(x,y) in enumerate(zip(pixels[:1024],pixels[1024:])):
        if x!=y:changed.append(i)
    check('cabinet screen-only slow pulse remains compact',0<len(changed)<=12,len(changed))
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    report=dict(method=__doc__,before_rom_sha256=SHA(before.rom),old_lab_sha256=SHA(lab.rom),rom_sha256=SHA(after.rom),tool_sha256=SHA(Path(__file__).read_bytes()),checks=rows,passed=sum(r['passed'] for r in rows),total=len(rows))
    out.write_text(json.dumps(report,indent=2)+'\n');print('RESULT',report['passed'],'/',report['total'])
    return int(report['passed']!=report['total'])


if __name__=='__main__':raise SystemExit(main())

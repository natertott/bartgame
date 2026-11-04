#!/usr/bin/env python3
"""Compare decoded production assets and verify lab run-save isolation in mGBA.

Uses one ordinary death/save record as input to a fresh lab core. No external
save file is opened; only the emulator's private SRAM is used. Actor death and
its timer are disclosed fixtures to exercise the real save path.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from sewer_concept_audit import NativeRom
import probe as P
import critical_path as C
import save_probe as S
import mgba.core
import mgba.image

SHA = lambda x: hashlib.sha256(x).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('before','normal','lab','out'):p.add_argument('--'+name,required=True)
    args=p.parse_args();out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    before,normal,lab=[NativeRom(getattr(args,n)) for n in ('before','normal','lab')]
    rows=[]
    def check(name,ok,detail=None):
        rows.append(dict(name=name,passed=bool(ok),detail=detail))
        print(('PASS ' if ok else 'FAIL ')+name,flush=True)
    check('normal excludes optional lab',normal.defs.get('BART_ENEMY_LAB')==0 and
          not any(n.startswith('proto_') for n in normal.sheet_ids))
    check('lab is explicitly marked',lab.defs.get('BART_ENEMY_LAB')==1)
    for kind in ('forest','sewer','myst'):
        check(kind+' original decoded terrain preserved',before.tileset(kind)==normal.tileset(kind)==lab.tileset(kind))
    check('normal sheet IDs unchanged',before.sheet_ids==normal.sheet_ids)
    for name in before.sheet_ids:
        check(name+' original native sprite preserved',before.sheet(name)==normal.sheet(name)==lab.sheet(name) and
              before.sheet_ids[name]==lab.sheet_ids[name])
    # Pointer-bearing tables relocate as code size changes. Compare their
    # decoded targets above; all other packed art payloads compare directly.
    pointer_tables={'sheets','tilesets','vwf_fonts','room_defs'}
    for name in before.sections:
        if name in pointer_tables or name.startswith(('anim_','tile_anims_')):continue
        a=before.array(name)
        # Animation descriptors contain ROM pointers; decoded tilesets cover them.
        if name.endswith('_anims'):continue
        check(name+' packed native payload preserved',name in normal.sections and
              name in lab.sections and a==normal.array(name)==lab.array(name))
    for name in ('proto_rope','proto_leever','proto_helmasaur'):
        meta,data=lab.sheet(name)
        check(name+' native16x16 one-OBJ32-pose sheet',meta['width']==meta['height']==16 and
              meta['frame_tiles']==4 and meta['tile_count']==128 and len(data)==4096,meta)
    # Prove that a valid ordinary run record cannot be loaded or overwritten by
    # the optional tool-rich lab. Appearance preferences are a separate record.
    P.MAP=str(Path(args.normal)/'bartgame.map');P._syms=None
    c=P.boot(rom=str(Path(args.normal)/'bartgame.gba'));C.dismiss(c,1000)
    version,raw=S.save_on_death(c)
    check('normal produces valid version2 run save',version==2)
    P.MAP=str(Path(args.lab)/'bartgame.map');P._syms=None
    c=mgba.core.load_path(str(Path(args.lab)/'bartgame.gba'))
    c.bg_video=mgba.image.Image(240,160);c.set_video_buffer(c.bg_video);c.reset()
    for i,b in enumerate(raw):P.w8(c,S.SRAM+i,b)
    P.run(c,45);P.press(c,'START',2,80)
    for _ in range(400):
        if P.r8(c,P.sym('gEnemyPrototypeSpawned')) and not P.r8(c,P.sym('gEnemyPrototypeRequest')):break
        if P.r8(c,P.sym('gTbActive')):P.press(c,'A',2,6)
        else:P.run(c,8)
    P.run(c,10)
    check('lab starts new forest experiment instead of continuing run',C.area(c)==1 and
          P.r8(c,P.sym('gEnemyPrototypeSpawned'))==1 and P.r8(c,P.sym('gPl')+8)==0x6f,
          dict(area=C.area(c),spawned=P.r8(c,P.sym('gEnemyPrototypeSpawned')),items=P.r8(c,P.sym('gPl')+8)))
    check('starting lab preserves original run record',S.ram(c,S.SRAM,len(raw))==raw)
    P.w8(c,P.sym('gActors')+2,7);P.w8(c,P.sym('gPl')+24,121)
    P.run(c,10)
    check('lab death cannot overwrite ordinary run record',S.ram(c,S.SRAM,len(raw))==raw)
    report=dict(method=__doc__,roms={n:SHA(r.rom) for n,r in zip(('before','normal','lab'),(before,normal,lab))},
                tool_sha256=SHA(Path(__file__).read_bytes()),checks=rows,passed=sum(r['passed'] for r in rows),total=len(rows))
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',report['passed'],'/',report['total'])
    return int(report['passed']!=report['total'])


if __name__=='__main__':raise SystemExit(main())

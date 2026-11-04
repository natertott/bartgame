#!/usr/bin/env python3
"""Real mGBA menu equivalence through all nine title appearance settings.

Every skin/palette pair is selected using the real title Options and D-pad
controls. A seeded new game reaches the Drain normally. An explicit full
inventory fixture then exercises item/key/region/zoom pages through ordinary
Start/R/A inputs. Native screenshots are untouched240x160 framebuffers; no
palette, frame clock, menu cursor, input-global or framebuffer is injected.
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

import probe as P
import critical_path as C

SHA = lambda data: hashlib.sha256(data).hexdigest()
TOOL = Path(__file__).resolve()


def memory(core, at, count):
    return bytes(P.r8(core, at+i) for i in range(count))


def rgb_sha(path):
    with Image.open(path) as im:
        assert im.size == (240,160), (path, im.size)
        return SHA(im.convert('RGB').tobytes())


def capture(bundle, phase, out):
    bundle = Path(bundle).resolve()
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    P.MAP = str(bundle/'bartgame.map')
    P._syms = None
    checks, media, settings = [], [], []

    def check(name, passed, detail=None):
        row = dict(name=name, passed=bool(passed))
        if detail is not None:
            row['detail'] = detail
        checks.append(row)
        print(('PASS ' if passed else 'FAIL ')+name, flush=True)
        assert passed, row

    def wait(core, condition, limit=2400):
        for _ in range(limit):
            if condition():
                return True
            P.run(core, 1)
        return False

    def snapshot(core, name, style, palette, page=None, zoom=None):
        path = out/(name+'.png')
        P.snap(core, str(path))
        row = dict(file=path.name, bytes=path.stat().st_size, sha256=SHA(path.read_bytes()),
                   RGB_sha256=rgb_sha(path), size=[240,160], style=style, palette=palette,
                   gFrame=P.r32(core,P.sym('gFrame')), game_state=C.gstate(core), area=C.area(core))
        if page is not None:
            row.update(page=P.r8(core,P.sym('gMenuStudyPage')),
                       cursor=P.r8(core,P.sym('gMenuStudyCursor')),
                       map_cell=P.r8(core,P.sym('gMenuStudyMapCell')),
                       zoom=P.r8(core,P.sym('gMenuStudyZoom')))
            check(name+' actual page', row['page']==page and row['zoom']==zoom, row)
        media.append(row)

    error = None
    try:
        for style in range(3):
            for palette in range(3):
                tag='style%d-palette%d'%(style,palette)
                core=P.boot(rom=str(bundle/'bartgame.gba'), start=False)
                check(tag+' native title', C.gstate(core)==0)
                # The last title entry is Options with or without a save.
                P.press(core,'UP',3,50)
                P.press(core,'A',3,60)
                check(tag+' real Options opens', P.r8(core,P.sym('gTitleOptions'))==1)
                current=P.r8(core,P.sym('gAppearanceStyle'))
                for _ in range((style-current)%3):
                    P.press(core,'RIGHT',3,50)
                P.press(core,'DOWN',3,50)
                current=P.r8(core,P.sym('gAppearancePalette'))
                for _ in range((palette-current)%3):
                    P.press(core,'RIGHT',3,50)
                check(tag+' physical controls select appearance',
                      P.r8(core,P.sym('gAppearanceStyle'))==style and
                      P.r8(core,P.sym('gAppearancePalette'))==palette)
                snapshot(core, tag+'-options', style,palette)
                P.press(core,'B',3,60)
                check(tag+' Options closes to title', C.gstate(core)==0 and not P.r8(core,P.sym('gTitleOptions')))
                seed=P.sym('gSeedOverride')
                P.w16(core,seed,0xb4a7)
                P.w16(core,seed+2,0)
                # Closing Options focuses that last entry. Its previous entry
                # is New Game in both the saved and unsaved title layouts.
                P.press(core,'UP',3,40)
                P.press(core,'START',3,40)
                check(tag+' actual new game reaches Drain',
                      wait(core,lambda:C.gstate(core)==1 and C.area(core)==0))
                C.dismiss(core,1000)
                check(tag+' opening dialogue dismissed normally',
                      not P.r8(core,P.sym('gTbActive')) and P.actor(core,0)['state']==0)
                pl=P.sym('gPl')
                for offset,value in ((0,68),(2,80),(4,999)):
                    P.w16(core,pl+offset,value)
                for offset,value in ((6,5),(7,99),(8,0x7f),(30,2),(35,99),(36,0x0f)):
                    P.w8(core,pl+offset,value)
                for slot,equipment in enumerate((4,1,5)):
                    P.w8(core,pl+9+slot,equipment)
                P.run(core,12)
                inventory=SHA(memory(core,pl,38))
                P.press(core,'START',3,120)
                check(tag+' actual item menu opens', C.gstate(core)==4)
                snapshot(core,tag+'-items',style,palette,0,0)
                P.press(core,'R',3,120)
                snapshot(core,tag+'-keys',style,palette,1,0)
                P.press(core,'R',3,120)
                snapshot(core,tag+'-overview',style,palette,2,0)
                P.press(core,'A',3,120)
                snapshot(core,tag+'-zoom',style,palette,2,1)
                settings.append(dict(style=style,palette=palette,inventory_sha256=inventory,
                                     seed=P.r32(core,P.sym('gWorld')),
                                     selected_style=P.r8(core,P.sym('gAppearanceStyle')),
                                     selected_palette=P.r8(core,P.sym('gAppearancePalette'))))
    except Exception as exc:
        error=repr(exc)
        checks.append(dict(name='capture completes without exception',passed=False,detail=error))
    report=dict(method=__doc__.strip(),phase=phase,
                source_commit=(bundle/'source-commit.txt').read_text().strip(),
                rom_sha256=SHA((bundle/'bartgame.gba').read_bytes()),tool_sha256=SHA(TOOL.read_bytes()),
                emulator='mGBA0.10.5',fixtures=[
                    'Seed0xb4a7 written through the existing seed override before real title New Game.',
                    'Ordinary title Options/D-pad selects each3x3 style/palette combination; settings globals are read only.',
                    'Full inventory, keys/heart fragments, hearts/gilt/ammo and A/B/L assignments are explicit resource fixtures.',
                    'No actor, terrain, palette, framebuffer, UI cursor, input-global or animation clock is modified.',
                ],settings=settings,media=media,checks=checks,
                passed=sum(row['passed'] for row in checks),total=len(checks),
                complete=error is None and len(settings)==9 and len(media)==45,error=error)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('phase','passed','total','complete','error')}))
    return report


def compare(before, after, out):
    before,after=Path(before).resolve(),Path(after).resolve()
    left=json.loads((before/'report.json').read_text())
    right=json.loads((after/'report.json').read_text())
    assert left['complete'] and right['complete']
    assert left['passed']==left['total'] and right['passed']==right['total']
    rows=[]
    new={row['file']:row for row in right['media']}
    for row in left['media']:
        name=row['file'];other=new[name]
        b=rgb_sha(before/name);a=rgb_sha(after/name)
        metadata=all(row.get(key)==other.get(key) for key in ('style','palette','page','cursor','map_cell','zoom','game_state','area'))
        equal=b==a
        rows.append(dict(file=name,passed=equal and metadata,before_RGB_sha256=b,after_RGB_sha256=a,
                         native_pixels_equal=equal,menu_state_equal=metadata))
        print(('PASS ' if equal and metadata else 'FAIL ')+name,flush=True)
    report=dict(method=__doc__.strip(),before_rom_sha256=left['rom_sha256'],after_rom_sha256=right['rom_sha256'],
                before_source=left['source_commit'],after_source=right['source_commit'],
                tool_sha256=SHA(TOOL.read_bytes()),checks=rows,
                passed=sum(row['passed'] for row in rows),total=len(rows))
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+'\n')
    return report


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bundle')
    ap.add_argument('--phase',default='before')
    ap.add_argument('--out',required=True)
    ap.add_argument('--compare',nargs=2,metavar=('BEFORE','AFTER'))
    args=ap.parse_args()
    if args.compare:
        report=compare(*args.compare,args.out)
    else:
        if not args.bundle:
            ap.error('--bundle is required for capture')
        report=capture(args.bundle,args.phase,args.out)
    return 0 if report['passed']==report['total'] and report.get('complete',True) else 1


if __name__=='__main__':
    raise SystemExit(main())

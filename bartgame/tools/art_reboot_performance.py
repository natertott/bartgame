"""Measure native rendering and surface glitter in representative mGBA rooms.

Inventory, safe position/facing and clearing unrelated actors are fixtures.
Terrain and action poses are not modified. Real sword, shield and cape inputs
run while game updates, VBlanks, hardware OAM and glitter counters are sampled.
This is isolated action performance, not a worst-case combat benchmark.
"""
import argparse
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import probe as P
import critical_path as C
import bloom_probe as B
from art_reboot_review import NativeSuite, actual_mystery


def measure(args):
    out=Path(args.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    P.ROM=str(Path(args.rom).resolve())
    rom_hash=hashlib.sha256(Path(P.ROM).read_bytes()).hexdigest()
    suite=NativeSuite(SimpleNamespace(rom=P.ROM,map=args.map,
        assets_header=args.assets_header,out=str(out.parent),seed=args.seed,
        only=None,match=None))
    contexts=[]
    for background in args.backgrounds.split(','):
        suite.seed=int(args.cave_seed if background=='cave' else args.seed,0)
        suite.enter(background)
        point=suite.spot(0,0)
        suite.reset(point,0,1)
        c=suite.c;pl=P.sym('gPl');actor=P.sym('gActors')
        # A=sword, B=shield, L=cape. No action state or pose is injected.
        for slot,equipment in enumerate((1,5,4)):
            P.w8(c,pl+9+slot,equipment)
        P.run(c,4)
        initial={'area':C.area(c),'cell':C.cell(c),'position':list(P.player_pos(c)),
                 'camera':[P.r16(c,P.sym('gCamX')),P.r16(c,P.sym('gCamY'))]}
        packed=actual_mystery(c,suite.cell) if C.area(c)==2 else None
        frame0=P.r32(c,P.sym('gFrame'))
        update0=P.r32(c,P.sym('gGame')+8)
        rows=[]
        for tick in range(args.frames):
            c.clear_keys(*range(10))
            phase=tick%64
            if phase==0:c.set_keys(P.key(c,'A'))
            elif 16<=phase<32:c.set_keys(P.key(c,'B'))
            elif phase==40:c.set_keys(P.key(c,'L'))
            C.heal(c)
            c.run_frame()
            rows.append({'tick':tick,'sites':P.r16(c,P.sym('gAmbientSiteCount')),
                'potential':P.r8(c,P.sym('gAmbientPotential')),
                'visible':P.r8(c,P.sym('gAmbientVisible')),
                'peaks':P.r8(c,P.sym('gAmbientPeaks')),
                'prepared_oam':P.r8(c,P.sym('gOamCount')),
                'hardware_oam':len(B.oam(c)),
                'state':P.r8(c,actor+2),'sword_active':P.r8(c,pl+21),
                'shield_up':P.r8(c,pl+34),'area':C.area(c),'cell':C.cell(c)})
        c.clear_keys(*range(10))
        vblanks=P.r32(c,P.sym('gFrame'))-frame0
        updates=P.r32(c,P.sym('gGame')+8)-update0
        checks={
            'one_game_update_per_video_frame':updates==vblanks==args.frames,
            'viewport_glitter_limit':all(row['potential']<=24 and row['visible']<=24 for row in rows),
            'hardware_oam_limit':all(max(row['prepared_oam'],row['hardware_oam'])<=128 for row in rows),
            'real_sword_action':any(row['sword_active'] for row in rows),
            'real_guard_action':any(row['shield_up'] for row in rows),
            'real_cape_jump':any(row['state']==5 for row in rows),
            'background_remained_loaded':all(row['area']==initial['area'] and row['cell']==initial['cell'] for row in rows),
        }
        result={'background':background,'seed':hex(suite.seed),'cell':suite.cell,
            'initial':initial,'natural_mystery':packed,'video_frames':args.frames,
            'vblanks':vblanks,'game_updates':updates,
            'ambient_visible_min':min(row['visible'] for row in rows),
            'ambient_visible_max':max(row['visible'] for row in rows),
            'ambient_visible_mean':sum(row['visible'] for row in rows)/len(rows),
            'potential_max':max(row['potential'] for row in rows),
            'peaks_max':max(row['peaks'] for row in rows),
            'oam_max':max(max(row['prepared_oam'],row['hardware_oam']) for row in rows),
            'checks':checks,'samples':rows}
        contexts.append(result)
        print(background,updates,'updates /',vblanks,'VBlanks;',
              'glitter %.2f mean, %d potential; OAM %d; %s'%(
                  result['ambient_visible_mean'],result['potential_max'],result['oam_max'],
                  'PASS' if all(checks.values()) else 'FAIL'),flush=True)
    unchanged=hashlib.sha256(Path(P.ROM).read_bytes()).hexdigest()==rom_hash
    report={'rom_sha256':rom_hash,'emulator':'mGBA','method':__doc__.strip(),
        'video_frames_per_context':args.frames,
        'input_cycle':{'frames':64,'sword_press':0,'shield_hold':[16,31],'cape_press':40},
        'rom_unchanged_during_measurement':unchanged,'contexts':contexts,
        'passed':sum(value for row in contexts for value in row['checks'].values())+int(unchanged),
        'total':sum(len(row['checks']) for row in contexts)+1}
    out.write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT %s %d/%d representative native performance checks'%(
        'PASS' if report['passed']==report['total'] else 'FAIL',report['passed'],report['total']))
    return int(report['passed']!=report['total'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',default=P.ROM)
    parser.add_argument('--map',default=P.MAP)
    parser.add_argument('--assets-header',default=str(Path(P.ROOT)/'build/gen/assets.h'))
    parser.add_argument('--out',required=True)
    parser.add_argument('--seed',default='0xB4A7')
    parser.add_argument('--cave-seed',default='11',help='A seed with a natural quiet medium/large cave.')
    parser.add_argument('--frames',type=int,default=192)
    parser.add_argument('--backgrounds',default='drain,forest,blight,cave')
    args=parser.parse_args()
    if args.frames<64:parser.error('--frames must cover at least one 64-frame input/glitter cycle')
    if any(name not in ('drain','forest','blight','cave') for name in args.backgrounds.split(',')):
        parser.error('--backgrounds accepts drain,forest,blight,cave')
    return measure(args)


if __name__=='__main__':raise SystemExit(main())

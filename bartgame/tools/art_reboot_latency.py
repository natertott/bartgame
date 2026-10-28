"""Paired real-ROM HUD/damage latency samples, separate from art gallery runs.

The disclosed local floor fixture and frozen ordinary beetle isolate contact.
Video frames, actual logic counters and hardware OAM distinguish preparation
latency from an action effect surviving a replacement upload.
"""
import argparse
import hashlib
import json
from pathlib import Path

import bloom_probe as B
import probe as P
import wood_probe as W


def sample(directory,trials,max_hp=24):
    directory=Path(directory);rom=directory/'bartgame.gba'
    P.MAP=str(directory/'bartgame.map');P._syms=None
    defs=B.definitions(directory/'assets.h')
    c=B.boot(str(rom));B.floor_fixture(c,defs)
    rows=[]
    for trial in range(trials):
        a,pl=B.reset_player(c)
        P.w16(c,pl,max_hp);P.w16(c,pl+2,max_hp)
        P.run(c,12)
        index=W.spawn_enemy(c,0,100,100)
        at=P.sym('gActors')+index*64
        P.w8(c,at+31,8);P.w8(c,at+47,2)
        P.w8(c,at+29,200);P.w16(c,at+32,0)
        P.press(c,'B',2,3)
        P.w16(c,at+8,0);P.w16(c,at+10,256)
        P.w16(c,at+12,0);P.w16(c,at+14,230)
        trace=[];contact=None;old_oam=None;replacement=None
        tile=P.r16(c,B.static_symbol('sActionTile'))
        for video in range(12):
            P.run(c,1)
            row={'video':video,'logic':P.r32(c,P.sym('gGame')+8),
                 'vblank':P.r32(c,P.sym('gFrame')),
                 **B.live(c),'hp':P.r16(c,pl),
                 'hardware_sword_effect':B.effect(c,tile) is not None}
            trace.append(row)
            current=B.bytes_at(c,0x07000000,1024)
            if contact is None and row['state']==3:
                contact=video;old_oam=current
            elif contact is not None and replacement is None and current!=old_oam:
                replacement=video
        assert contact is not None,'ordinary enemy contact did not hurt Bloom'
        assert trace[contact]['active']==0,'hurt did not immediately clear damage'
        assert replacement is not None,'no replacement hardware OAM observed'
        assert not trace[replacement]['hardware_sword_effect'],'sword survived replacement OAM'
        rows.append({'trial':trial,'contact_video':contact,
                     'replacement_video':replacement,
                     'replacement_delay_video_frames':replacement-contact,
                     'trace':trace})
    return {'rom_sha256':hashlib.sha256(rom.read_bytes()).hexdigest(),'max_hp':max_hp,
            'samples':rows,'replacement_delays':[r['replacement_delay_video_frames'] for r in rows]}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--before',default='/workspace/setup/art-reboot-before')
    ap.add_argument('--after',default='/workspace/setup/art-reboot-second')
    ap.add_argument('--trials',type=int,default=5)
    ap.add_argument('--max-hp',type=int,default=24,help='24 normal HP or80 maximum ten-heart HUD')
    ap.add_argument('--out',default='/workspace/setup/art-reboot-hud-latency.json')
    args=ap.parse_args()
    report={'method':__doc__,'emulator':'mGBA 0.10.5',
            'before':sample(args.before,args.trials,args.max_hp),
            'after':sample(args.after,args.trials,args.max_hp)}
    Path(args.out).write_text(json.dumps(report,indent=2)+'\n')
    print('before',report['before']['replacement_delays'])
    print('after ',report['after']['replacement_delays'])


if __name__=='__main__':main()

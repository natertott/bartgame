"""Exercise Bloom's real-ROM action timing, reach and streamed effects in mGBA.

python tools/bloom_probe.py [--rom ROM --map MAP --assets-header HEADER] [--out JSON]

Boundary targets use the game's HB_SMALL box and frozen AI. A local floor
fixture isolates combat from procedural hazards; no fixture sprite is an art
preview. Hardware OAM/VRAM checks account for the one-frame VBlank upload.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
import probe as P
import critical_path as C
import lift_probe as L
import wood_probe as W

FACES=('n','e','s','w')
BOXES=((-14,-32,13,-12),(4,-22,22,2),(-14,-6,13,12),(-23,-22,-5,2))
PL_ACTIVE,PL_PHASE,PL_LAMP,PL_COOLDOWN=21,22,23,25
checks=[]


def definitions(path):
    return {k:int(v,0) for k,v in re.findall(r'^#define\s+(\w+)\s+(0x[0-9a-fA-F]+|\d+)\b',Path(path).read_text(),re.M)}


def static_symbol(name):
    lines=Path(P.MAP).read_text().splitlines()
    for i,line in enumerate(lines):
        words=line.split()
        if words and words[0] in ('.bss.'+name,'.data.'+name):
            return int(words[1],16) if len(words)>1 else int(lines[i+1].split()[0],16)
    raise KeyError(name)


def configure(args):
    P.MAP=str(Path(args.map).resolve());P._syms=None
    return definitions(args.assets_header)


def check(name,ok,detail=''):
    checks.append({'name':name,'passed':bool(ok),'detail':detail})
    print(('PASS' if ok else 'FAIL'),name,detail,flush=True)


def clear_actors(c):
    a=P.sym('gActors')
    for i in range(1,96):P.w8(c,a+i*64,0)


def reset_player(c,x=256,y=230,facing=0,equipment=(0,1,5)):
    c.clear_keys(*range(10));clear_actors(c)
    a=P.sym('gActors');pl=P.sym('gPl')
    P.w8(c,a+2,0);P.w8(c,a+3,0);P.w8(c,a+4,0)
    for off in (16,18,20,22,24,28,29):P.w16(c,a+off,0)
    P.w8(c,a+31,0)
    for off in (PL_ACTIVE,PL_PHASE,PL_LAMP,PL_COOLDOWN,31,32,33,34):P.w8(c,pl+off,0)
    P.w8(c,pl+8,0x7f);P.w8(c,pl+36,0x0f);P.w8(c,pl+7,9);P.w8(c,pl+35,30)
    P.w16(c,pl,24);P.w16(c,pl+2,24)
    for i,e in enumerate(equipment):P.w8(c,pl+9+i,e)
    C.teleport(c,x,y)
    P.w8(c,a+7,facing);P.w8(c,a+6,facing*8)
    P.run(c,3)
    return a,pl


def boot(rom,seed=0xB4A7):
    c=P.boot(rom=rom,seed=seed);C.dismiss(c);P.enter_forest(c)
    w=C.world(c);L.warp(c,w['entry'],2);clear_actors(c)
    return c


def floor_fixture(c,defs):
    room=P.sym('gRoom');mt=defs['MT_MOSS0']
    for ty in range(6,20):
        for tx in range(8,25):
            at=ty*32+tx
            P.w16(c,room+2+at*2,mt);P.w16(c,room+2050+at*2,65535)
            P.w16(c,room+8194+at*2,mt)
            for qy in (ty*2,ty*2+1):
                for qx in (tx*2,tx*2+1):P.w8(c,room+4098+qy*64+qx,0)
    reset_player(c);P.run(c,96)


def live(c):
    a=P.sym('gActors');pl=P.sym('gPl')
    return {'state':P.r8(c,a+2),'timer':P.r8(c,a+4),'active':P.r8(c,pl+PL_ACTIVE),
            'phase':P.r8(c,pl+PL_PHASE),'facing':P.r8(c,a+7),'position':list(P.player_pos(c))}


def oam(c,hardware=True):
    at=0x07000000 if hardware else P.sym('gOam')
    out=[]
    for i in range(128 if hardware else P.r8(c,P.sym('gOamCount'))):
        a0=P.r16(c,at+i*8)&65535;a1=P.r16(c,at+i*8+2)&65535;a2=P.r16(c,at+i*8+4)&65535
        if (a0&0x0300)==0x0200:continue
        x=a1&511;y=a0&255
        if x>=256:x-=512
        if y>=160:y-=256
        out.append({'index':i,'x':x,'y':y,'tile':a2&1023,'pal':a2>>12,
                    'shape':a0>>14,'size':a1>>14,'priority':(a2>>10)&3,'flip':bool(a1&0x1000)})
    return out


def bytes_at(c,at,n):return bytes(P.r8(c,at+i) for i in range(n))


def sheet_metadata(c,index):
    """Read the live ROM descriptor, including native canvas/OAM shape."""
    at=P.sym('sheets')+index*12
    return {'source':P.r32(c,at),'tiles':P.r16(c,at+4)&65535,
            'frame_tiles':P.r8(c,at+6),'shape':P.r8(c,at+7),'size':P.r8(c,at+8),
            'pal':P.r8(c,at+9),'width':P.r8(c,at+10),'height':P.r8(c,at+11)}


def hero_oam(c,hardware=True):
    # HERO is contract sheet0 and resident tile0 in both the frozen and
    # reboot builds. Its canvas is metadata, not an assumed64x32 shape.
    sh=sheet_metadata(c,0)
    return next((entry for entry in oam(c,hardware) if entry['tile']==0 and
                 entry['shape']==sh['shape'] and entry['size']==sh['size'] and
                 entry['pal']==sh['pal']),None)


def fixed_tiles(c,defs):
    """The reboot derives its fixed bases from actual sheet dimensions."""
    hero=sheet_metadata(c,defs['SHEET_HERO'])
    sword=sheet_metadata(c,defs['SHEET_SWORD'])
    shield=sheet_metadata(c,defs['SHEET_SHIELD'])
    return {'hero':0,'sword':hero['frame_tiles'],
            'shield':hero['frame_tiles']+sword['tiles'],
            'minimum_free':hero['frame_tiles']+sword['tiles']+shield['frame_tiles']}


def sword_step(age):return 0 if age<2 else 1 if age<5 else 2 if age<9 else 3 if age<13 else 4


def phase_geometry(c):
    try:P.sym('bloom_sword_hit');P.sym('bloom_sword_origin');return True
    except KeyError:return False


def phase_box(c,facing,age):
    if not phase_geometry(c):return BOXES[facing]
    at=P.sym('bloom_sword_hit')+(facing*5+sword_step(age))*4
    return tuple((v-256 if v>=128 else v) for v in bytes_at(c,at,4))


def sword_origin(c,facing):
    if not phase_geometry(c):
        x,y,_,_=BOXES[facing];return x,y-(8 if facing==2 else 0)
    at=P.sym('bloom_sword_origin')+facing*2
    return tuple((v-256 if v>=128 else v) for v in bytes_at(c,at,2))


def effect(c,tile,hardware=True):
    return next((a for a in oam(c,hardware) if a['tile']==tile and a['shape']==0 and a['size']==2),None)


def pixels(blob,w=32,h=32):
    pts=[]
    for y in range(h):
        for x in range(w):
            at=((y//8)*(w//8)+x//8)*32+(y%8)*4+(x%8)//2
            if (blob[at]>>(4*(x&1)))&15:pts.append((x,y))
    return pts


def effect_contract(c,defs):
    sh=P.sym('sheets')+defs['SHEET_BLOOMFX']*12
    source=P.r32(c,sh);frame_tiles=P.r8(c,sh+6)
    frames={k[len('F_BLOOMFX_'):].lower():v for k,v in defs.items() if k.startswith('F_BLOOMFX_')}
    blobs={name:bytes_at(c,source+idx*frame_tiles*32,frame_tiles*32) for name,idx in frames.items()}
    tile=P.r16(c,static_symbol('sActionTile'))&65535
    minimum=fixed_tiles(c,defs)['minimum_free']
    check('action frame occupies one reserved 32px slot',frame_tiles==16 and minimum<=tile and tile+16<=defs.get('OBJ_TILE_HUD_ICONS',876),f'tile {tile}, frame tiles {frame_tiles}')
    return tile,blobs


def timing_and_render(c,defs):
    tile,blobs=effect_contract(c,defs)
    traces=[]
    for f,d in enumerate(FACES):
        reset_player(c,facing=f);previous=live(c);trace=[]
        c.set_keys(P.key(c,'B'))
        for tick in range(18):
            c.run_frame()
            if tick==0:c.clear_keys(P.key(c,'B'))
            state=live(c);trace.append(state)
            fx=effect(c,tile);blob=bytes_at(c,0x06010000+tile*32,512)
            matches=[n for n,b in blobs.items() if b==blob]
            if previous['state']==2 and previous['active']:
                check(f'{d} active effect present in hardware OAM at tick {tick}',fx is not None)
                check(f'{d} streamed frame agrees with live damage window at tick {tick}',any(re.fullmatch('sword_'+d+'[123]',n) for n in matches),str(matches))
                if fx:
                    hx,hy=previous['position'];x0,y0,x1,y1=phase_box(c,f,previous['timer'])
                    cy=P.r16(c,P.sym('gCamY'));cx=P.r16(c,P.sym('gCamX'))
                    if cx>=32768:cx-=65536
                    if cy>=32768:cy-=65536
                    origin=sword_origin(c,f)
                    want=(hx+origin[0]-cx,hy+origin[1]-cy)
                    check(f'{d} effect anchored to combat box at tick {tick}',(fx['x'],fx['y'])==want,f'{(fx["x"],fx["y"])} == {want}')
                    pts=pixels(blob)
                    if phase_geometry(c):
                        # Read the independently rendered pixels inside the
                        # damaging distal-blade/trail box. The harmless grip
                        # is deliberately excluded; no old sweep cage is
                        # required merely to fill an obsolete envelope.
                        pts=[(x+origin[0],y+origin[1]) for x,y in pts
                             if x0<=x+origin[0]<=x1 and y0<=y+origin[1]<=y1]
                        expected=(x0,y0,x1,y1)
                    else:
                        if f==2:pts=[(x,y-8) for x,y in pts if y>=8]
                        expected=(0,0,x1-x0,y1-y0)
                    got=(min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts),max(y for x,y in pts)) if pts else None
                    check(f'{d} visible blade/trail reaches its phase collision boundaries at tick {tick}',got==expected,{'visible':got,'contact':expected,'age':previous['timer']})
                    hero=hero_oam(c)
                    check(f'{d} sword precedes Bloom in OAM at tick {tick}',hero is not None and fx['index']<hero['index'])
            previous=state
        check(d+' attack starts without an invisible hit',trace[0]['state']==2 and not trace[0]['active'] and not trace[1]['active'])
        check(d+' damage window remains timer2 through12',all(t['active']==(2<=t['timer']<=12) for t in trace if t['state']==2))
        check(d+' recovery and return to normal',trace[13]['state']==2 and not trace[13]['active'] and trace[15]['state']==0)
        traces.append({'direction':d,'frames':trace})
    return tile,traces


def boundary_targets(f,box=None):
    x0,y0,x1,y1=BOXES[f] if box is None else box
    center_x=(x0+x1)//2;center_y=(y0+y1)//2+6
    # HB_SMALL is x[-5..4], y[-11..-2], not a point at its feet.
    return [('left',(x0-4,center_y),(-1,0)),('right',(x1+5,center_y),(1,0)),
            ('top',(center_x,y0+2),(0,-1)),('bottom',(center_x,y1+11),(0,1))]


def boundaries(c):
    for f,d in enumerate(FACES):
        ages=(2,5,9) if phase_geometry(c) else (None,)
        for age in ages:
            box=phase_box(c,f,age) if age is not None else BOXES[f]
            for edge,(dx,dy),(ox,oy) in boundary_targets(f,box):
                for outside in (False,True):
                    a,pl=reset_player(c,facing=f)
                    target_x=256+dx+(ox if outside else 0)
                    target_y=230+dy+(oy if outside else 0)
                    # The debug spawn helper itself advances two updates.
                    # Spawn before starting the attack, park it outside all
                    # reach, then move the frozen target into the one tested
                    # phase rather than silently testing age+2.
                    i=W.spawn_enemy(c,0,100 if age is not None else target_x,
                                    100 if age is not None else target_y)
                    at=P.sym('gActors')+i*64
                    P.w8(c,at+31,2);P.w8(c,at+34,2);P.w16(c,at+26,20)
                    P.w8(c,at+29,200);P.w16(c,at+32,0);P.w8(c,at+28,0)
                    if age is None:P.press(c,'B',1,15)
                    else:
                        P.press(c,'B',1,age-1)
                        P.w16(c,at+8,0);P.w16(c,at+10,target_x)
                        P.w16(c,at+12,0);P.w16(c,at+14,target_y)
                        P.run(c,1)
                        check(f'{d} phase contact actually tests age{age}',P.r8(c,a+4)==age,P.r8(c,a+4))
                    hp=P.actor(c,i)['hp'] if P.actor(c,i)['kind']==2 else 0
                    label=f'{d} '+('age%d '%age if age is not None else '')+edge
                    check(label+' '+('one pixel outside misses' if outside else 'inclusive edge lands'),hp==(20 if outside else 18),f'target hp {hp}')


def interactions(c,defs,tile):
    a,pl=reset_player(c)
    # Pickup at the far edge is beyond body contact but within the swing.
    x0,y0,x1,y1=phase_box(c,0,5);tx=256+(x0+x1)//2
    heart_y=230+y0+2 if phase_geometry(c) else 200
    P.w16(c,pl,16);W.put_actor(c,1,4,0,tx,heart_y,2,timer=10)
    P.run(c,2);check('heart beyond body contact stays before swing',P.r16(c,pl)==16)
    P.press(c,'B',1,15);check('sword still gathers a reached heart',P.r16(c,pl)==24)
    a,pl=reset_player(c)
    projectile_y=230+y0+4 if phase_geometry(c) else 202
    W.put_actor(c,1,3,0,tx,projectile_y,6,flags=1,dir_=16,speed=0,damage=2,timer=1)
    P.press(c,'B',1,5)
    at=P.sym('gActors')+64
    check('sword still deflects an incoming seed',P.actor(c,1)['kind']==3 and P.r8(c,at+48)==1 and P.r8(c,at+6)==0)
    a,pl=reset_player(c)
    tx,ty=16,12;room=P.sym('gRoom')
    P.w16(c,room+2+(ty*32+tx)*2,defs['MT_BUSH'])
    P.press(c,'B',1,15)
    check('sword still cuts a reached bush',P.r16(c,room+2+(ty*32+tx)*2)!=defs['MT_BUSH'])
    # Contact from a non-hittable enemy interrupts the action through normal
    # player_hurt, rather than assigning a hurt animation in RAM.
    a,pl=reset_player(c);P.press(c,'B',1,3)
    W.put_actor(c,1,2,0,256,230,2,flags=8,damage=2,timer=200)
    at=P.sym('gActors')+64;P.w8(c,at+29,200);P.w16(c,at+32,0)
    P.run(c,1)
    check('damage interrupts the sword and clears its hitbox',P.r8(c,a+2)==3 and not P.r8(c,pl+PL_ACTIVE))
    P.run(c,1)
    check('hurt Bloom has no lingering action effect',effect(c,tile) is None)
    # Keep a harmless test enemy aligned with the rolling player to verify
    # invulnerability while the roll is protected.
    a,pl=reset_player(c)
    W.put_actor(c,1,2,0,256,230,2,flags=8,damage=2,timer=200)
    at=P.sym('gActors')+64;P.w8(c,at+29,200);P.w16(c,at+32,0)
    c.set_keys(P.key(c,'RIGHT'),P.key(c,'R'))
    protected=True
    for tick in range(16):
        hx,hy=P.player_pos(c);P.w16(c,at+10,hx+2);P.w16(c,at+14,hy)
        c.run_frame()
        if tick==0:c.clear_keys(P.key(c,'R'))
        protected=protected and P.r16(c,pl)==24 and P.r8(c,a+2)==1
    check('roll retains its protected opening',protected)
    # Test queued attack separately, with no enemy or collision interruption.
    a,pl=reset_player(c)
    c.set_keys(P.key(c,'RIGHT'),P.key(c,'R'));P.run(c,1);c.clear_keys(P.key(c,'R'))
    P.run(c,19);c.set_keys(P.key(c,'B'));P.run(c,1);c.clear_keys(P.key(c,'B'))
    check('late roll still queues a sword input',P.r8(c,pl+32)==1)
    states=[]
    for _ in range(10):c.run_frame();states.append(P.r8(c,a+2))
    c.clear_keys(*range(10))
    check('queued sword follows roll recovery',2 in states)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--rom',default=P.ROM);ap.add_argument('--map',default=P.MAP)
    ap.add_argument('--assets-header',default=str(Path(P.ROOT)/'build/gen/assets.h'))
    ap.add_argument('--out',default='/tmp/bloom-probe.json');ap.add_argument('--seed',default='0xB4A7')
    args=ap.parse_args();defs=configure(args);seed=int(args.seed,0)
    c=boot(args.rom,seed);floor_fixture(c,defs)
    tile,traces=timing_and_render(c,defs);boundaries(c);interactions(c,defs,tile)
    report={'rom_sha256':hashlib.sha256(Path(args.rom).read_bytes()).hexdigest(),'seed':hex(seed),
            'emulator':'mGBA 0.10.5','method':'real button actions; frozen-AI HB_SMALL boundary targets and local physical-floor fixture; real hardware OAM/OBJ VRAM inspection',
            'passed':sum(t['passed'] for t in checks),'total':len(checks),'checks':checks,'attack_traces':traces}
    Path(args.out).write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT %s %d/%d'%('PASS' if all(t['passed'] for t in checks) else 'FAIL',report['passed'],report['total']))
    return int(not all(t['passed'] for t in checks))


if __name__=='__main__':raise SystemExit(main())

"""The game's boxes and menus captured from the ROM, as a player sees them:
the Gatekeeper's words, the Peddler's shop and his words after a sale,
the pause menu's pages and the map, looked at closer.

    cd bartgame && make && python3 tools/ui_shots.py OUTDIR [--rom ROM]

Writes, raw 240x160: dialogue_gatekeeper.png, shop.png, dialogue_peddler.png,
pause_items.png, pause_keys.png, pause_map.png, pause_zoom.png,
pause_map_full.png and pause_zoom_full.png (with the Map and the
Astrolabe); and
ui_sheet.png, all of them at 2x side by side.
"""
import os
import sys
import json
import hashlib
from pathlib import Path

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import probe as P  # noqa: E402
import critical_path as CP  # noqa: E402
import lift_probe as LP  # noqa: E402

args = sys.argv[1:]
ROM = P.ROM
if '--rom' in args:
    i = args.index('--rom')
    ROM = args[i + 1]
    del args[i:i + 2]
if '--map' in args:
    i=args.index('--map');P.MAP=args[i+1];P._syms=None
    del args[i:i+2]
EXTRA_PORTRAITS='--portraits' in args
if EXTRA_PORTRAITS:args.remove('--portraits')
OUT = args[0]
os.makedirs(OUT, exist_ok=True)
shots = []


def snap(c, name):
    p = os.path.join(OUT, name + '.png')
    P.snap(c, p)
    shots.append(p)


def additional_portraits():
    """Real NPC A-talks, plus a contact-death return; no pose/frame assignment."""
    import bloom_probe as B
    face_addr=B.static_symbol('sTbFace')
    c=P.boot(rom=ROM,seed=0xB4A7);CP.dismiss(c);world=CP.world(c);P.enter_forest(c);rows=[]
    for role,name,face in [(5,'hermit',3),(6,'nun',4),(7,'gardener',5)]:
        cell=next(i for i,d in enumerate(world['cells']) if d['role']==role)
        LP.warp(c,cell,next(i for i,g in enumerate(world['cells'][cell]['gate']) if g));CP.dismiss(c);CP.clear_enemies(c)
        at=P.sym('gSpots');nx,ny=P.r8(c,at+27),P.r8(c,at+28)
        CP.teleport(c,nx*16+8,(ny+1)*16+14);P.run(c,48);P.hold(c,'UP',1);P.press(c,'A',2,120)
        active=P.r8(c,P.sym('gTbActive'));got=P.r8(c,face_addr)
        assert active and got==face,(name,active,got,P.player_pos(c),nx,ny)
        snap(c,'dialogue_'+name);rows.append({'name':name,'cell':cell,'face':got,'method':'actual A talk at naturally generated NPC; position/cleared enemies are fixtures'})
        CP.dismiss(c)
    c=P.boot(rom=ROM,seed=0xB4A7);CP.dismiss(c);CP.teleport(c,200,240);P.run(c,48)
    P.w16(c,P.sym('gPl'),1);P.w16(c,P.sym('gDbgSpawn'),256);P.run(c,1)
    enemy=next(i for i in range(1,96) if P.actor(c,i)['kind']==2)
    x,y=P.player_pos(c);at=P.sym('gActors')+enemy*64
    for off,val in [(8,0),(10,x),(12,0),(14,y)]:P.w16(c,at+off,val)
    for tick in range(360):
        c.run_frame()
        if P.r8(c,P.sym('gTbActive')) and P.r8(c,face_addr)==0 and CP.area(c)==0:break
    else:raise AssertionError('real contact death did not reach Bloom return dialogue')
    P.run(c,120);snap(c,'dialogue_bloom_return')
    rows.append({'name':'bloom','face':0,'method':'real contact death from a placed beetle after debug spawn; normal save/return path','frames_to_dialogue':tick})
    Path(OUT,'additional-portraits.json').write_text(json.dumps({'rom_sha256':hashlib.sha256(Path(ROM).read_bytes()).hexdigest(),'captures':rows},indent=2)+'\n')


def main():
    c = P.boot(rom=ROM, seed=0xB4A7)
    P.run(c, 40)
    CP.dismiss(c)
    pl = P.sym('gPl')
    P.w16(c, pl + 4, 123)       # gilt to buy with
    # the Gatekeeper's words
    CP.teleport(c, 21 * 16 + 8, 7 * 16 + 4)
    P.run(c, 60)
    P.hold(c, 'UP', 6)
    P.press(c, 'A', 2, 90)
    snap(c, 'dialogue_gatekeeper')
    CP.dismiss(c)
    # the shop, and the Peddler's words after a sale
    CP.teleport(c, 4 * 16 + 8, 7 * 16 + 6)
    P.run(c, 60)
    P.hold(c, 'UP', 6)
    P.press(c, 'A', 2, 30)
    snap(c, 'shop')
    P.press(c, 'A', 2, 90)
    snap(c, 'dialogue_peddler')
    CP.dismiss(c)
    # the pause menu, in the wood, with a full bag
    P.w8(c, pl + 8, 0x7F)
    P.w8(c, pl + 36, 3)
    P.w8(c, pl + 7, 3)
    w = CP.world(c)
    P.enter_forest(c)
    LP.warp(c, w['entry'], 2)
    P.run(c, 30)
    P.press(c, 'START', 2, 12)
    snap(c, 'pause_items')
    P.press(c, 'R', 2, 12)
    snap(c, 'pause_keys')
    P.press(c, 'R', 2, 20)
    snap(c, 'pause_map')
    P.press(c, 'A', 2, 20)
    snap(c, 'pause_zoom')
    P.press(c, 'B', 2, 20)
    P.press(c, 'START', 2, 20)
    # the map again with the Map and the Astrolabe: every cell drawn, the
    # chests, the Heart and the barriers marked; a cell up the wood closer
    P.w8(c, pl + 36, P.r8(c, pl + 36) | 0x0C)
    P.run(c, 30)
    P.press(c, 'START', 2, 20)
    P.press(c, 'R', 2, 16)
    P.press(c, 'R', 2, 60)       # the first look at every cell takes a moment
    snap(c, 'pause_map_full')
    P.press(c, 'UP', 2, 20)
    P.press(c, 'A', 2, 20)
    snap(c, 'pause_zoom_full')
    P.press(c, 'B', 2, 20)
    P.press(c, 'START', 2, 20)
    if EXTRA_PORTRAITS:additional_portraits()
    cols = 4
    rows = (len(shots) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * 496, rows * 336), (24, 24, 24))
    for i, p in enumerate(shots):
        im = Image.open(p).resize((480, 320), Image.NEAREST)
        sheet.paste(im, ((i % cols) * 496 + 8, (i // cols) * 336 + 8))
    sheet.save(os.path.join(OUT, 'ui_sheet.png'))
    print('wrote %d screens to %s' % (len(shots), OUT))


if __name__ == '__main__':
    main()

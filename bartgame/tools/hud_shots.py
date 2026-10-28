"""The HUD captured from the ROM in the states a player meets: the first
steps in the hall, a long bar with the purse and both counts, the other
items, nothing held, the wood, and the gardener's dark room.

    cd bartgame && make && python3 tools/hud_shots.py OUTDIR [--rom ROM]

Writes, raw 240x160: hud_hall.png, hud_counts.png (ten hearts, six and a
half full, the seeds on A, the bow on L), hud_others.png (the lamp, the
cloak, the cap), hud_empty.png (half a heart, nothing held), hud_wood.png
and hud_dark.png; and hud_sheet.png, all of them at 2x, and
hud_bands.png, the top 24 rows of each at 4x, plus hardware alpha checks in hud.json.
"""
import os
import sys
import json
import hashlib

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
OUT = args[0]
os.makedirs(OUT, exist_ok=True)
shots = []
checks=[]
HUD_HEIGHT=24
ROLE_NPC_TORCH = 7
# gPl: hp, hp_max, gilt (s16, s16, u16), keys, bombs, items, equip[3]
# (A, B, L) from 6, arrows at 35
HP, HP_MAX, GILT, KEYS, BOMBS, ITEMS, EQUIP, ARROWS = 0, 2, 4, 6, 7, 8, 9, 35
EQ_NONE, EQ_SWORD, EQ_BOMBS, EQ_LAMP, EQ_CLOAK, EQ_SHIELD, EQ_BOW, EQ_HUBCAP = range(8)


def hud_alpha(c):
    """Decode actual BG0 and priority-zero OAM alpha, including OBJ windows."""
    points=[];cb=0x06008000;sb=0x0600B800
    for ty in range(20):
        for tx in range(30):
            e=P.r16(c,sb+(ty*32+tx)*2)&65535;t=e&1023
            if not t:continue
            for y in range(8):
                for x in range(8):
                    xx=7-x if e&0x400 else x;yy=7-y if e&0x800 else y
                    b=P.r8(c,cb+t*32+yy*4+xx//2)
                    if (b>>((xx&1)*4))&15:points.append((tx*8+x,ty*8+y))
    sizes=(((8,8),(16,16),(32,32),(64,64)),((16,8),(32,8),(32,16),(64,32)),((8,16),(8,32),(16,32),(32,64)))
    for i in range(128):
        at=0x07000000+i*8;a0=P.r16(c,at)&65535;a1=P.r16(c,at+2)&65535;a2=P.r16(c,at+4)&65535
        if a0&0x300==0x200 or (a2>>10)&3 or a0>>14==3:continue
        w,h=sizes[a0>>14][a1>>14];sx=a1&511;sy=a0&255
        if sx>=256:sx-=512
        if sy>=160:sy-=256
        if sx+w<=0 or sx>=240 or sy+h<=0 or sy>=160:continue
        for y in range(h):
            for x in range(w):
                wx,wy=sx+x,sy+y
                if not 0<=wx<240 or not 0<=wy<160:continue
                xx=w-1-x if a1&0x1000 else x;yy=h-1-y if a1&0x2000 else y
                tile=(a2&1023)+(yy//8)*(w//8)+(xx//8)
                b=P.r8(c,0x06010000+tile*32+(yy%8)*4+(xx%8)//2)
                if (b>>((xx&1)*4))&15:points.append((wx,wy))
    return {'painted_pixels':len(points),'top':min((y for x,y in points),default=None),'bottom':max((y for x,y in points),default=None),'below_band':sum(y>=HUD_HEIGHT for x,y in points)}


def snap(c, name):
    p = os.path.join(OUT, name + '.png')
    P.snap(c, p)
    shots.append(p)
    alpha=hud_alpha(c);ok=alpha['painted_pixels']>100 and alpha['below_band']==0
    checks.append({'name':name+' all real HUD alpha stays within24px','passed':ok,'detail':alpha})
    print(('PASS' if ok else 'FAIL'),checks[-1]['name'],alpha,flush=True)


def equip(c, a, b, l):
    pl = P.sym('gPl')
    for s, eq in enumerate((a, b, l)):
        P.w8(c, pl + EQUIP + s, eq)


def main():
    c = P.boot(rom=ROM, seed=0xB4A7)
    P.run(c, 40)
    CP.dismiss(c)
    pl = P.sym('gPl')
    CP.teleport(c, 12 * 16 + 8, 9 * 16 + 4)
    P.run(c, 30)
    snap(c, 'hud_hall')
    P.w16(c, pl + HP_MAX, 80)
    P.w16(c, pl + HP, 52)
    P.w16(c, pl + GILT, 999)
    P.w8(c, pl + KEYS, 255)
    P.w8(c, pl + ITEMS, 0x7F)
    P.w8(c, pl + BOMBS, 30)
    P.w8(c, pl + ARROWS, 50)
    P.w8(c, pl + 36, 0x0F)
    equip(c, EQ_BOMBS, EQ_SWORD, EQ_BOW)
    P.run(c, 4)
    snap(c, 'hud_counts')
    equip(c, EQ_LAMP, EQ_CLOAK, EQ_HUBCAP)
    P.w16(c, pl + HP, 80)
    P.run(c, 4)
    snap(c, 'hud_others')
    equip(c, EQ_NONE, EQ_NONE, EQ_NONE)
    P.w16(c, pl + HP_MAX, 24)
    P.w16(c, pl + HP, 4)
    P.run(c, 4)
    snap(c, 'hud_empty')
    equip(c, EQ_BOMBS, EQ_SWORD, EQ_SHIELD)
    P.w16(c, pl + HP_MAX, 48)
    P.w16(c, pl + HP, 48)
    w = CP.world(c)
    P.enter_forest(c)
    P.run(c, 30)
    snap(c, 'hud_wood')
    dark = [i for i, cl in enumerate(w['cells']) if cl['role'] == ROLE_NPC_TORCH]
    if dark:
        LP.warp(c, dark[0], 2)
        P.run(c, 40)
        snap(c, 'hud_dark')
    cols = 2
    rows = (len(shots) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * 496, rows * 336), (24, 24, 24))
    for i, p in enumerate(shots):
        im = Image.open(p).resize((480, 320), Image.NEAREST)
        sheet.paste(im, ((i % cols) * 496 + 8, (i // cols) * 336 + 8))
    sheet.save(os.path.join(OUT, 'hud_sheet.png'))
    bands = Image.new('RGB', (960, len(shots) * 104 - 8), (24, 24, 24))
    for i, p in enumerate(shots):
        im = Image.open(p).crop((0, 0, 240, HUD_HEIGHT)).resize((960, HUD_HEIGHT*4), Image.NEAREST)
        bands.paste(im, (0, i * 104))
    bands.save(os.path.join(OUT, 'hud_bands.png'))
    report={'rom_sha256':hashlib.sha256(open(ROM,'rb').read()).hexdigest(),'emulator':'mGBA 0.10.5','method':'Real HUD; inventory/resources/position are fixtures. Native screenshots unchanged; hardware BG0 and priority-zero OBJ alpha decoded to prove24px limit.','passed':sum(c['passed'] for c in checks),'total':len(checks),'checks':checks,'native_frames':[os.path.basename(p) for p in shots]}
    open(os.path.join(OUT,'hud.json'),'w').write(json.dumps(report,indent=2)+'\n')
    print('wrote %d screens to %s' % (len(shots), OUT))
    if report['passed']!=report['total']:raise SystemExit(1)


if __name__ == '__main__':
    main()

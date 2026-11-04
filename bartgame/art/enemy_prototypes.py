"""Original native 16px studies for the optional enemy-mechanics laboratory.

These are provisional readable silhouettes, not adopted production characters.
Every pose is painted at 16x16, using existing literal RGB555 material banks.
No reference image, resizing or palette conversion supplies game pixels.
"""
from pathlib import Path
import hashlib
import json

from PIL import Image, ImageDraw, ImageFont

import reboot_core as R

POSES = ('idle', 'walk1', 'walk2', 'tell', 'attack', 'recover', 'hurt', 'buried')
FACES = ('n', 'e', 's', 'w')
SPECS = (
    ('proto_rope', 'Gilt Leech', 'items', 'Line-up, brace, straight rush'),
    ('proto_leever', 'Root Maw', 'blight', 'Mound, emergence, exposed pursuit'),
    ('proto_helmasaur', 'Reliquary Snout', 'fx', 'Gold front armor / soft red rear'),
)


def _canvas():
    return R.indexed(16, 16)


def _oval(d, box, base, light, shade, outline=1):
    """Connected broad volume with a fixed upper-left light plane."""
    x0, y0, x1, y1 = box
    d.ellipse(box, fill=outline)
    d.ellipse((x0+1, y0+1, x1-1, y1-1), fill=base)
    if x1-x0 > 5 and y1-y0 > 4:
        d.polygon([(x0+2,y0+2), ((x0+x1)//2,y0+1),
                   ((x0+x1)//2+1,(y0+y1)//2-1), (x0+2,(y0+y1)//2)], fill=light)
        d.line((x0+3,y1-2,x1-3,y1-2), fill=shade)


def _mound(d, bank='earth', tremor=False):
    # A connected low soil ridge; no detached sparkle/pickup-like marks.
    lo, mid, hi = (8, 9, 11) if bank == 'earth' else (3, 5, 6)
    d.polygon([(1,13),(3,11),(6,10),(9,10),(13,12),(14,14),(2,14)], fill=1)
    d.polygon([(3,12),(6,11),(9,11),(12,13),(3,13)], fill=mid)
    d.line((4,12,7,11), fill=hi)
    d.line((8,13,12,13), fill=lo)
    if tremor:
        d.line([(5,12),(7,11),(9,12)], fill=hi)


def rope(pose, face):
    im, d = _canvas()
    horizontal = face in ('e', 'w')
    step = 1 if pose == 'walk2' else 0
    if pose == 'buried':
        _mound(d)
        return im
    if pose == 'attack':
        box = (0,6,15,13) if horizontal else (4,0,11,15)
    elif pose == 'tell':
        box = (3,5,12,14)
    elif pose == 'recover':
        box = (2,8,13,14)
    else:
        box = (1,6+step,14,14) if horizontal else (3,2+step,12,14)
    _oval(d, box, 4, 6 if pose != 'hurt' else 14, 3)
    if horizontal:
        # One gold segmented dorsal ridge, clearly attached to the leech.
        y = box[1]+2
        for x in (4,7,10):
            d.line((x,y,x,y+3), fill=12)
            d.point((x,y), fill=15)
        hx = 12 if face == 'e' else 3
        hy = 9 + (1 if pose == 'recover' else 0)
        if pose == 'tell': hx = 11 if face == 'e' else 4
        _oval(d, (hx-2,hy-3,hx+2,hy+2), 5, 7, 3)
        eye_x = hx+1 if face == 'e' else hx-1
        d.point((eye_x,hy-1), fill=15)
        d.point((eye_x,hy), fill=1)
        if pose == 'attack':
            tip = 15 if face == 'e' else 0
            d.line((hx,hy+1,tip,hy+1), fill=1)
            d.point((tip,hy), fill=12)
    else:
        ridge_rows = (10, 12) if pose == 'recover' else (7, 10, 12) if pose == 'tell' else (5, 8, 11)
        for y in ridge_rows:
            d.line((5,y,9,y), fill=12)
            d.point((5,y), fill=15)
        hy = 3 if face == 'n' else 12
        if pose == 'recover': hy = 10
        if pose == 'tell': hy = 6 if face == 'n' else 11
        _oval(d, (4,hy-2,11,min(15,hy+3)), 5, 7, 3)
        ey = hy-1 if face == 'n' else hy+1
        d.point((6,ey), fill=15); d.point((9,ey), fill=15)
        if pose == 'attack':
            d.line((7,1 if face == 'n' else 14,8,1 if face == 'n' else 14), fill=12)
    if pose == 'tell':
        d.line((5,box[1]+1,9,box[1]+1), fill=15)
    return im


def leever(pose, face):
    im, d = _canvas()
    if pose == 'buried':
        _mound(d, tremor=True)
        return im
    _mound(d)
    spread = 1 if pose in ('walk2','attack') else 0
    # Root feet connect to the dark central body instead of loose debris.
    for pts in ([(6,10),(3,11),(1,13-spread)],
                [(9,10),(12,11),(14,13-spread)],
                [(6,11),(5,14)],[(9,11),(10,14)]):
        d.line(pts, fill=1, width=2)
        d.point(pts[-1], fill=11)
    y0 = 5 if pose == 'tell' else 3
    if pose == 'recover': y0 = 6
    _oval(d, (3,y0,12,13), 4, 6, 2)
    # Ivory rim around a truly dark mouth reads as an emerging hazard.
    d.ellipse((4,y0+1,11,12), fill=15)
    d.ellipse((5,y0+2,10,11), fill=1)
    center = 8 if face in ('s','n') else 9 if face == 'e' else 6
    d.line((center, y0+4, center, 10), fill=13)
    d.point((center, y0+4), fill=14)
    d.point((6,y0+2), fill=15);d.point((9,y0+2), fill=15)
    d.point((6,11), fill=15);d.point((9,11), fill=15)
    if pose == 'attack':
        d.rectangle((6,5,9,10), fill=1)
        d.line((7,7,8,7), fill=13)
        d.point((7,8), fill=14)
    if pose == 'hurt':
        d.line((4,6,4,9), fill=14)
    return im


def helmasaur(pose, face):
    im, d = _canvas()
    if pose == 'buried':
        pose = 'idle'  # Not a burrowing species; unused closed resting pose.
    dy = 1 if pose in ('walk2','recover') else 0
    _oval(d, (3,3+dy,12,13+dy), 13, 14, 2)
    # Four connected beetle feet carry its weight; walking alternates stance.
    for x,y,end in ((4,7,1),(11,7,14),(4,11,2),(11,11,13)):
        ty = y+(1 if pose=='walk1' and x<8 else -1 if pose=='walk2' and x>8 else 0)
        d.line([(x,ty),(end,ty+1),(end,ty+2)], fill=1)
        d.point((end,ty+1), fill=8)
    # The soft rear stays red in every orientation, never gold like armor.
    back = {'n':(5,9,10,13),'e':(3,6,6,12),
            's':(5,3,10,6),'w':(9,6,12,12)}[face]
    d.ellipse(back, fill=15)
    if pose == 'hurt':d.point((back[0]+1,back[1]+1), fill=12)
    plate = {'n':(3,1,12,9),'e':(7,3,15,13),
             's':(3,6,12,15),'w':(0,3,8,13)}[face]
    _oval(d, plate, 9, 11, 7)
    px0,py0,px1,py1=plate
    d.line((px0+2,py0+2,px1-3,py0+2), fill=12)
    # A single raised ridge distinguishes polished shell from cloth/body.
    if face in ('n','s'):
        d.line((7,py0+2,7,py1-2), fill=10)
        ey = py0+2 if face=='n' else py1-2
        d.line((5,ey,9,ey), fill=2)
        d.point((5,ey), fill=12)
    else:
        d.line((px0+2,6,px1-2,6), fill=10)
        ex = px1-2 if face=='e' else px0+2
        d.line((ex,7,ex,10), fill=2)
        d.point((ex,7), fill=12)
    if pose == 'tell':
        d.line((px0+2,py0+1,px1-2,py0+1), fill=12)
    if pose == 'attack':
        x,y = {'n':(7,0),'e':(15,8),'s':(7,15),'w':(0,8)}[face]
        d.point((x,y), fill=10)
    return im


PAINTERS = {'proto_rope':rope, 'proto_leever':leever, 'proto_helmasaur':helmasaur}


def rows(image):
    return [''.join(format(image.getpixel((x,y)), 'x') for x in range(16)) for y in range(16)]


def build_sheets():
    sheets=[]
    for name, _, palette, _ in SPECS:
        frames={}
        for pose in POSES:
            for face in FACES:
                image=PAINTERS[name](pose,face)
                assert image.mode=='P' and image.size==(16,16)
                assert set(image.getdata())<=set(range(16))
                frames[pose+'_'+face]=rows(image)
        sheets.append(dict(name=name,w=16,h=16,pal=palette,frames=frames))
    return sheets


def export(directory):
    """Separate source catalog, not emulator evidence; integer inspection only."""
    import palettes
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    banks=dict(palettes.OBJ_PALETTES)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)
    board=Image.new('RGB',(708,52+len(POSES)*96),'#101820')
    d=ImageDraw.Draw(board);d.fontmode='1'
    d.text((8,7),'SOURCE STUDIES / original native16px / 1x + 3x nearest inspection',font=font,fill='#f0d898')
    records=[]
    for col,(name,title,bank,meaning) in enumerate(SPECS):
        x=col*236
        d.text((x+8,27),title+' — '+bank,font=font,fill='#f0d898')
        for row,pose in enumerate(POSES):
            y=52+row*96
            d.text((x+8,y),pose+' / N E S W',font=font,fill='#b0c0b0')
            for f,face in enumerate(FACES):
                image=PAINTERS[name](pose,face)
                flat=[v for color in banks[bank] for v in R.rgb(color)]
                image.putpalette(flat+[0]*(768-len(flat)))
                image.info['transparency']=0
                p=directory/(name+'-'+pose+'_'+face+'.png');image.save(p)
                rgba=R.rgba(image,banks[bank]);board.paste(rgba,(x+8+f*55,y+18),rgba)
                zoom=rgba.resize((48,48),Image.Resampling.NEAREST)
                board.paste(zoom,(x+8+f*55,y+40),zoom)
                records.append(dict(sheet=name,frame=pose+'_'+face,palette=bank,file=p.name,
                                    native_size=[16,16],bbox=image.getbbox(),
                                    sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    board.save(directory/'source-poses.png')
    (directory/'manifest.json').write_text(json.dumps({'kind':'Native provisional SOURCE art; not emulator output.',
        'states':POSES,'directions':FACES,'hardware_tiles_per_sheet':128,
        'palette_banks':{name:banks[name] for name in sorted({s[2] for s in SPECS})},
        'assets':records},indent=2)+'\n')


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',default='/workspace/setup/glitter-enemies/prototype-source')
    export(parser.parse_args().out)

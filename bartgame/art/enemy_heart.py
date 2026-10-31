"""The selected Blight Heart: a bruised purple organ broken down its middle.

Every pose is authored directly in the existing32x64 hardware canvas, using
the unchanged sixteen-ink blight bank. The actor's feet, hitbox and floating
movement belong to the engine. This module only changes the native drawing.
"""
from pathlib import Path
import hashlib
import json

from PIL import Image, ImageDraw, ImageFont, ImageSequence
import reboot_core as C

FRAMES = ('pulse1', 'pulse2', 'hurt', 'charge1', 'charge2', 'release1',
          'release2', 'spawn1', 'spawn2', 'lunge1', 'lunge2', 'dying1', 'dying2')
SIZE = (32, 64)
PALETTE_NAME = 'blight'

# Values move native vertices/material masses rather than resizing a picture.
# The lower point stays anchored: breathing is upper-tissue compression.
# bulk, top, middle, gap, twist, heat, collapse
POSES = {
    'pulse1':  (0,  0, 0, 1,  0, 0, 0),
    'pulse2':  (1, -1, 0, 1,  0, 1, 0),
    'hurt':    (0,  0, 1, 2, -1, 3, 0),
    'charge1': (1, -1, 0, 2,  0, 1, 0),
    'charge2': (1, -2, 1, 3,  0, 2, 0),
    'release1':(0,  0, 1, 3,  1, 2, 0),
    'release2':(-1, 1, 1, 2,  1, 1, 0),
    'spawn1':  (0, -1, 1, 2,  0, 1, 0),
    'spawn2':  (1,  0, 2, 2,  0, 2, 0),
    'lunge1':  (0,  1, 2, 2, -1, 1, 0),
    'lunge2':  (1,  2, 1, 2, -1, 2, 0),
    'dying1':  (-1, 2, 1, 3,  0, 0, 1),
    'dying2':  (-2, 4, 2, 4,  1, 0, 2),
}

OUTER = ((16,30),(13,25),(9,23),(5,23),(2,26),(1,30),(1,35),
         (3,40),(6,45),(10,51),(13,56),(16,61),(19,57),(23,52),
         (27,46),(30,40),(31,34),(30,29),(27,26),(24,24),
         (20,25),(18,27))
SPLIT = ((16,21),(16,29),(14,34),(17,38),(14,42),(17,46),
         (15,50),(18,54),(16,58),(17,63))


def _warp(point, pose):
    x,y = point
    bulk,top,middle,gap,twist,heat,collapse = pose
    # Larger lobes swell outwards, while the bottom remains a tapered organ.
    if y < 46:
        x += -bulk if x < 16 else bulk
    if y < 34:
        y += top
    elif y < 50:
        y += middle
    if y < 54:
        x += twist
    if collapse:
        # Tissue folds toward its own lower point, rather than translating.
        y += (54-y)//5*collapse if y < 54 else 0
    return max(0,min(31,x)), max(0,min(62,y))


def _plane(im, polygon, ink):
    layer = Image.new('1', SIZE)
    ImageDraw.Draw(layer).polygon(polygon, fill=1)
    # Preserve the hand-authored dark outline, including narrow concave turns.
    for y in range(64):
        for x in range(32):
            if layer.getpixel((x,y)) and im.getpixel((x,y)) not in (0,1):
                im.putpixel((x,y), ink)


def _tissue_line(im, points, ink, width=1):
    layer = Image.new('1', SIZE)
    ImageDraw.Draw(layer).line(points, fill=1, width=width)
    for y in range(64):
        for x in range(32):
            if layer.getpixel((x,y)) and im.getpixel((x,y)) not in (0,1):
                im.putpixel((x,y), ink)


def split_columns(name):
    """Native transparent wound span per row, useful to independent review."""
    pose = POSES[name]
    gap,twist = pose[3],pose[4]
    points = list(SPLIT)
    out = {}
    for y in range(21,64):
        for (ax,ay),(bx,by) in zip(points, points[1:]):
            if ay <= y <= by:
                x = round(ax+(bx-ax)*(y-ay)/(by-ay))
                if 31 <= y <= 54:
                    x += twist
                lo = x-gap//2
                out[y] = (lo,lo+gap-1)
                break
    return out


def frame(name):
    assert name in FRAMES, name
    pose = POSES[name]
    bulk,top,middle,gap,twist,heat,collapse = pose
    im = Image.new('P',SIZE,0)
    d = ImageDraw.Draw(im)

    # Two short, connected severed arteries establish an organic boss rather
    # than a menu/pickup symbol. Their short rims follow the same light.
    left = [_warp(p,pose) for p in ((10,25),(8,20),(9,17),(12,16))]
    right = [_warp(p,pose) for p in ((24,27),(26,23),(25,20),(23,19))]
    for path in (left,right):
        d.line(path,fill=1,width=4)
        d.line(path,fill=4 if collapse else 5,width=2)
        d.line([(x-1,y) for x,y in path[1:]],fill=6)

    # A broad, asymmetric pair of lobes and a long lower point. There is no
    # face, black central maw or hole which competes with the HEART outline.
    hull = [_warp(p,pose) for p in OUTER]
    d.polygon(hull,fill=4,outline=1)
    warp = lambda points: [_warp(p,pose) for p in points]
    _plane(im,warp(((3,29),(7,25),(11,26),(14,31),(12,39),(8,45),(4,38))),6 if not collapse else 5)
    _plane(im,warp(((5,27),(8,25),(11,27),(12,31),(9,34),(5,32))),7 if not collapse else 6)
    _plane(im,warp(((18,31),(21,27),(25,27),(28,31),(28,37),(24,41),(20,39))),5)
    _plane(im,warp(((21,28),(24,27),(27,30),(25,34),(21,33))),6 if not collapse else 5)
    _plane(im,warp(((5,40),(9,44),(13,48),(16,54),(16,59),(12,53),(8,47))),5 if not collapse else 3)
    _plane(im,warp(((22,40),(28,37),(27,43),(23,50),(20,54),(19,50))),3)
    _plane(im,warp(((13,50),(16,54),(19,51),(19,57),(16,60))),2 if collapse else 3)

    # Greasy lower folds and irregular surface vessels are attached to broad
    # tissue planes; they are not a checkerboard of independent decoration.
    _tissue_line(im,warp(((5,35),(8,37),(9,40),(12,42))),12)
    _tissue_line(im,warp(((7,36),(6,39),(7,42))),3)
    _tissue_line(im,warp(((24,35),(22,38),(23,42),(20,46))),12)
    _tissue_line(im,warp(((25,45),(22,46),(21,49))),6)
    _tissue_line(im,warp(((11,48),(12,51),(14,53))),6 if not collapse else 4)

    if name.startswith('spawn'):
        # Existing add-release phase: the lower vessels swell in sequence.
        # Solid tissue, not a pair of eyes or an invented shield weak point.
        if name == 'spawn1':
            _tissue_line(im,warp(((4,38),(6,41),(6,45),(9,48))),12,3)
            _tissue_line(im,warp(((5,39),(7,42),(7,45))),14)
        else:
            _tissue_line(im,warp(((27,36),(25,40),(25,45),(22,49))),12,3)
            _tissue_line(im,warp(((26,38),(24,42),(24,45))),14)

    # Wound edges and the air between them stay visible in EVERY pose. The
    # cut goes through native pixels, not a shading line over an intact heart.
    wound = split_columns(name)
    before_split = im.copy()
    for y,(lo,hi) in wound.items():
        for x in range(lo,hi+1):
            if 0 <= x < 32:im.putpixel((x,y),0)
        for x in (lo-1,hi+1):
            if 0 <= x < 32 and before_split.getpixel((x,y)):
                im.putpixel((x,y),1)
        for x,ink in ((lo-2,12 if collapse else 13),(hi+2,3 if collapse else 12)):
            if 0 <= x < 32 and im.getpixel((x,y)) not in (0,1):
                im.putpixel((x,y),ink)
        if not collapse and y in (32,33,39,40,46,47,52,53):
            x = lo-2
            if 0 <= x < 32 and im.getpixel((x,y)) not in (0,1):
                im.putpixel((x,y),15 if heat >= 3 else 14 if heat >= 1 else 7)
        if not collapse and heat >= 2 and y in (36,37,44,45):
            x = hi+2
            if 0 <= x < 32 and im.getpixel((x,y)) not in (0,1):
                im.putpixel((x,y),14)

    # Attached wet speculars. Upper-left diffuse volume remains the principal
    # light; bright wound reflections are small local material exceptions.
    if not collapse:
        _tissue_line(im,warp(((5,28),(7,27),(9,28))),14)
        _tissue_line(im,warp(((5,29),(5,31))),7)
        if heat >= 1:
            _tissue_line(im,warp(((6,27),(8,27))),15)
        if name == 'hurt':
            _tissue_line(im,warp(((7,29),(9,30),(10,33))),15)
            _tissue_line(im,warp(((22,29),(24,30))),14)

    # Reassert the gap after all tissue/specular operations; no glint stitches
    # the organ back together or creates detached fluff in its negative space.
    for y,(lo,hi) in wound.items():
        for x in range(max(0,lo),min(31,hi)+1):im.putpixel((x,y),0)
    return im


def previews(out):
    """Native/source inspection only; actual mGBA footage is parent-owned."""
    out = Path(out);out.mkdir(parents=True,exist_ok=True)
    palette = C.PALETTES[PALETTE_NAME]
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)
    atlas = Image.new('RGB',(5*160,36+3*236),'#101820')
    draw = ImageDraw.Draw(atlas);draw.fontmode='1'
    draw.text((6,6),'BROKEN PURPLE HEART / native1x +3x / SOURCE ART, not emulator output',font=font,fill='#f0d898')
    motion = []
    checks = []
    hashes = []
    for i,name in enumerate(FRAMES):
        image = frame(name)
        rgb = C.rgba(image,palette)
        x=i%5*160;y=36+i//5*236
        big=rgb.resize((96,192),Image.Resampling.NEAREST)
        atlas.paste(big,(x+4,y+4),big);atlas.paste(rgb,(x+116,y+128),rgb)
        draw.text((x+5,y+202),name,font=font,fill='#f0d898')
        native=out/(name+'.png');rgb.save(native)
        indexed=image.copy();indexed.putpalette([n for color in palette for n in C.rgb(color)]+[0]*(768-48));indexed.save(out/(name+'-indexed.png'),transparency=0)
        card=Image.new('RGB',(320,252),'#283838');d=ImageDraw.Draw(card);d.fontmode='1'
        d.text((8,6),'SOURCE pose / '+name,font=font,fill='#f0d898')
        card.paste(big,(48,34),big);card.paste(rgb,(216,160),rgb)
        d.text((8,234),'150ms inspection hold; not AI timing',font=font,fill='#f0d898')
        motion.append(card)
        wound = split_columns(name)
        gap = all(image.getpixel((x,yy))==0 for yy,(lo,hi) in wound.items() for x in range(max(0,lo),min(31,hi)+1))
        assert image.mode=='P' and image.size==SIZE and set(image.tobytes())<=set(range(16))
        assert image.getbbox() and gap
        hashes.append(hashlib.sha256(image.tobytes()).hexdigest())
        checks.append({'frame':name,'canvas':list(image.size),'indices':sorted(set(image.tobytes())),
                       'bounds':image.getbbox(),'full_height_gap_clear':gap,
                       'native_indices_sha256':hashes[-1]})
    assert len(set(hashes))==len(FRAMES),'Every presentation state must have its own meaningful pose'
    atlas.save(out/'broken-heart-all-poses-source.png')
    def rgb_pixels(image):
        raw=image.tobytes()
        return zip(raw[0::3],raw[1::3],raw[2::3])
    colors=sorted({pixel for im in motion for pixel in rgb_pixels(im)});assert len(colors)<=256
    pal=[v for color in colors for v in color]+[0]*(768-len(colors)*3)
    lookup={color:i for i,color in enumerate(colors)};indexed=[]
    for im in motion:
        p=Image.new('P',im.size);p.putpalette(pal);p.putdata([lookup[pix] for pix in rgb_pixels(im)]);indexed.append(p)
    gif=out/'broken-heart-all-poses-source.gif'
    indexed[0].save(gif,save_all=True,append_images=indexed[1:],duration=150,loop=0,disposal=2,optimize=False)
    with Image.open(gif) as im:
        decoded=[g.convert('RGB').copy() for g in ImageSequence.Iterator(im)]
        assert len(decoded)==len(motion) and all(a.tobytes()==b.tobytes() for a,b in zip(decoded,motion))
    # Solid material/source context backgrounds show1x legibility. These are
    # labelled assemblies, never advertised as real arena screenshots.
    context=Image.new('RGB',(640,236),'#101820');d=ImageDraw.Draw(context);d.fontmode='1'
    d.text((6,6),'SOURCE contexts /1x +3x / not emulator footage',font=font,fill='#f0d898')
    for i,(label,color) in enumerate((('forest','#385038'),('blight','#483048'),('Drain','#384848'),('cave','#202830'))):
        x=i*160;d.rectangle((x,30,x+159,235),fill=color)
        sprite=C.rgba(frame('pulse1'),palette);context.paste(sprite.resize((96,192),Image.Resampling.NEAREST),(x+4,36),sprite.resize((96,192),Image.Resampling.NEAREST));context.paste(sprite,(x+116,150),sprite)
        d.text((x+4,32),label,font=font,fill='#f0d898')
    context.save(out/'broken-heart-context-source.png')
    report={'method':'Direct native legal-canvas/index/continuous-split/unique-pose checks; exact-palette GIF RGB roundtrip. These source checks do not replace actual mGBA review.',
            'frames':checks,'passed':len(checks),'total':len(checks),'gif_exact_palette':True,'gif_colors':len(colors),'gif_pose_ms':150,
            'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (out/'native-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True)
    a=p.parse_args();r=previews(a.out)
    print(json.dumps({'passed':r['passed'],'total':r['total'],'source_sha256':r['source_sha256'],'gif_exact':r['gif_exact_palette']}))

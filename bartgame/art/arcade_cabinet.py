"""A native GBA archive cabinet for the Drain.

Painted directly into a32x64,4bpp hardware canvas. The26x44 cabinet shares
PAL_OBJ_FX's existing gold/teal/wine material bank with Drain brass. Source
previews are assemblies for inspection, never emulator renders.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw
import reboot_core as R

FRAME_NAMES = ('idle', 'glow')
PALETTE = 'fx'
WIDTH, HEIGHT = 32, 64
# Draw placement uses this contact point; margins do not define collision.
CONTACT = (16, 62)
PAINTED_FOOTPRINT = (4, 50, 27, 62)


def paint(frame='idle'):
    assert frame in FRAME_NAMES, frame
    im, d = R.indexed(WIDTH, HEIGHT)
    bright = frame == 'glow'
    # A short contact shadow belongs to the foot, with real local floor under
    # every exterior transparent pixel. No rectangular color backing.
    d.ellipse((3, 59, 28, 63), fill=1)
    # Top and right return establish the same raised three-quarter view as
    # the Drain's architecture. The front is broad; the far side is narrow.
    silhouette = [(6, 19), (23, 19), (27, 22), (28, 28), (26, 31),
                  (26, 42), (29, 47), (28, 50), (28, 60), (26, 62),
                  (5, 62), (3, 60), (3, 49), (5, 44), (6, 31), (4, 28),
                  (4, 22)]
    d.polygon(silhouette, fill=1)
    # Matte wine-brown housing, with a distinct darker right side.
    d.polygon([(6, 22), (23, 22), (25, 29), (24, 42), (27, 48),
               (26, 59), (24, 61), (6, 61), (4, 59), (5, 48), (7, 42),
               (7, 30), (5, 27)], fill=4)
    d.polygon([(24, 23), (26, 24), (27, 28), (25, 31), (25, 42),
               (28, 47), (27, 59), (25, 61), (25, 49), (23, 42),
               (24, 29)], fill=2)
    d.polygon([(7, 20), (22, 20), (25, 22), (6, 22)], fill=5)
    d.line((7, 20, 21, 20), fill=9)
    d.line((6, 23, 6, 28), fill=6)
    # The recessed marquee has one short gleaming edge. "PLAY" is literal
    # native3x5 lettering, not a reduced font or a decorative pseudo-script.
    d.rectangle((6, 22, 24, 29), fill=7)
    d.line((7, 22, 22, 22), fill=10)
    d.line((7, 23, 7, 27), fill=9)
    d.rectangle((8, 23, 22, 27), fill=10)
    glyphs = {
        'P': ('110', '101', '110', '100', '100'),
        'L': ('100', '100', '100', '100', '111'),
        'A': ('010', '101', '111', '101', '101'),
        'Y': ('101', '101', '010', '010', '010'),
    }
    for index, letter in enumerate('PLAY'):
        for y, row in enumerate(glyphs[letter]):
            for x, pixel in enumerate(row):
                if pixel == '1': d.point((8+index*4+x, 23+y), fill=2)
    # Monitor: an actual dark cavity, teal phosphor and one joined glass
    # reflection. Narrow upper-left brass edges never become a second outline.
    d.polygon([(8, 30), (23, 30), (23, 40), (21, 43), (9, 43),
               (7, 40), (7, 32)], fill=1)
    d.line((9, 30, 22, 30), fill=8)
    d.line((8, 31, 8, 39), fill=7)
    d.polygon([(10, 32), (21, 32), (22, 33), (21, 40), (19, 41),
               (10, 41), (9, 39), (9, 34)], fill=13)
    d.line((10, 33, 19, 33), fill=14)
    d.line((10, 34, 10, 37), fill=14)
    # A small bright open-book glyph suggests this is a catalogue terminal,
    # not a door, chest or loose pickup. Both pages share one physical spine.
    d.polygon([(12, 35), (14, 35), (15, 36), (16, 35), (19, 35),
               (19, 39), (16, 39), (15, 40), (14, 39), (12, 39)], fill=1)
    d.rectangle((12, 35, 14, 38), fill=11)
    d.rectangle((16, 35, 18, 38), fill=12 if bright else 11)
    d.line((15, 36, 15, 39), fill=14)
    d.line((12, 35, 14, 35), fill=12)
    d.point((18, 36), fill=13)
    d.line((12, 37, 13, 37), fill=9)
    d.line((16, 37, 17, 37), fill=9)
    # Cabinet waist leans inward, then the control deck projects toward the
    # viewer. These planes, joystick and two round buttons carry arcade identity.
    d.polygon([(6, 42), (24, 42), (28, 47), (26, 50), (5, 50),
               (4, 47)], fill=1)
    d.polygon([(7, 43), (23, 43), (26, 46), (25, 47), (6, 47)], fill=5)
    d.line((7, 43, 22, 43), fill=8)
    d.line((6, 48, 25, 48), fill=7)
    d.line((6, 49, 24, 49), fill=3)
    # A connected black stick, red cap and clear button separation.
    d.ellipse((8, 45, 12, 47), fill=2)
    d.line((10, 43, 10, 46), fill=1)
    d.rectangle((9, 41, 11, 43), fill=1)
    d.rectangle((9, 41, 10, 42), fill=15)
    d.point((9, 41), fill=11)
    d.ellipse((17, 44, 19, 46), fill=2)
    d.line((17, 44, 18, 44), fill=15)
    d.ellipse((22, 44, 24, 46), fill=2)
    d.line((22, 44, 23, 44), fill=10)
    # Quiet lower kick panel and a small unmistakable coin slot. No miniature
    # inventory item is painted on the floor around the machine.
    d.rectangle((6, 51, 24, 59), fill=3)
    d.line((6, 51, 6, 58), fill=5)
    d.rectangle((12, 51, 20, 58), fill=2)
    d.line((12, 51, 19, 51), fill=6)
    d.line((13, 52, 18, 52), fill=1)
    d.line((14, 52, 17, 52), fill=8)
    d.rectangle((15, 55, 18, 57), fill=1)
    d.line((15, 55, 17, 55), fill=7)
    # Wear stays attached to seams and the damp base, not scattered sparkles.
    d.line((7, 54, 8, 54), fill=6)
    d.line((22, 56, 23, 56), fill=2)
    d.line((5, 60, 24, 60), fill=7)
    d.line((6, 60, 11, 60), fill=9)
    d.point((6, 59), fill=10)
    d.line((7, 61, 10, 61), fill=13)
    d.line((21, 60, 24, 60), fill=13)
    d.point((22, 59), fill=14)
    # One short, static material glint; animation belongs only to the CRT.
    d.line((8, 21, 10, 21), fill=11)
    return im


def _rows(im):
    return [''.join(format(im.getpixel((x, y)), 'x') for x in range(im.width))
            for y in range(im.height)]


def build_sheet():
    return {'name': 'arcade', 'w': WIDTH, 'h': HEIGHT, 'pal': PALETTE,
            'frames': {name: _rows(paint(name)) for name in FRAME_NAMES}}


SHEET = build_sheet()


def export(directory):
    directory = Path(directory); directory.mkdir(parents=True, exist_ok=True)
    palette = R.PALETTES['gold']
    images = {name: paint(name) for name in FRAME_NAMES}
    for name, im in images.items():
        im.putpalette([v for color in palette for v in R.rgb(color)] + [0]*720)
        im.info['transparency'] = 0
        im.save(directory/(name+'.png'))
    # Integer inspection copies only. The background is a comparison matte,
    # not an extra square painted into the game sprite.
    board = Image.new('RGB', (360, 276), '#182828')
    d = ImageDraw.Draw(board); d.fontmode = '1'
    d.text((8, 8), 'SOURCE ART / native32x64 / existing FX bank', fill='#f0d898')
    d.text((8, 23), 'Cabinet body26x44; floor is transparent', fill='#b0c0b0')
    for i, (name, im) in enumerate(images.items()):
        x = 18+i*174
        d.text((x, 43), name+' / 1x', fill='#f0d898')
        rgba = R.rgba(im, palette); board.paste(rgba, (x, 57), rgba)
        d.text((x+55, 43), '3x nearest', fill='#b0c0b0')
        zoom = rgba.resize((96, 192), Image.Resampling.NEAREST)
        board.paste(zoom, (x+55, 57), zoom)
    d.text((8, 258), 'Source assembly, not an emulator render', fill='#b0c0b0')
    board.save(directory/'source-inspection.png')
    changed = sum(a != b for a, b in zip(images['idle'].getdata(), images['glow'].getdata()))
    manifest = {
        'kind': 'Native authored source art, not emulator output',
        'sheet': 'arcade', 'hardware_canvas': [WIDTH, HEIGHT],
        'palette': 'PAL_OBJ_FX, unchanged reboot_core.PALETTES[gold]',
        'contact': CONTACT, 'physical_suggestion': PAINTED_FOOTPRINT,
        'frames': {}, 'changed_pixels_between_frames': changed,
        'obj_tiles_per_frame': 32, 'obj_tiles_total': 64,
    }
    for name, im in images.items():
        manifest['frames'][name] = {'bbox': im.getbbox(),
                                   'indices': sorted(set(im.getdata())),
                                   'sha256': hashlib.sha256((directory/(name+'.png')).read_bytes()).hexdigest()}
    (directory/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', default='/workspace/setup/arcade-release/cabinet-source')
    args = parser.parse_args(); print(json.dumps(export(args.out), indent=2))

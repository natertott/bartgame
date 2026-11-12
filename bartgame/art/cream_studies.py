"""Optional native Cream studies and the review-led synthesis; zero unchanged.

These are unselected review directions. No high-resolution image is reduced
into a game asset: painters return final-size indexed pixels directly.
"""
import importlib
import os
from PIL import Image, ImageDraw

VARIANT = int(os.environ.get('BART_CREAM', '0'))
if not 0 <= VARIANT <= 12:
    raise ValueError('BART_CREAM must be one integer in 0..12')
STYLES = (
    ('Original Cream', None),
    ('Curdstone Karst', 'cream_style_karst'),
    ('Brine Basilica', 'cream_style_basilica'),
    ('Moldglass Crags', 'cream_style_moldglass'),
    ('Gilt Quarry', 'cream_style_quarry'),
    ('Black Rind Terraces', 'cream_style_rind'),
    ('Fractured Rind', 'cream_style_depth'),
    ('Pearlstone Folds', 'cream_style_polish'),
    ('Faulted Chalk', 'cream_style_polish'),
    ('Ribbed Karst', 'cream_style_polish'),
    ('Weathered Curdstone', 'cream_style_polish'),
    ('Velvet Travertine', 'cream_style_polish'),
    ('Weathered Heights', 'cream_style_polish'),
)
PAINTERS = ('floor', 'cliff', 'climb', 'rim', 'cave', 'water', 'prop', 'chest', 'pit')
BANKS = ('cream_floor0', 'cream_floor1', 'cream_floor2',
         'cream_cliff0', 'cream_cliff1', 'cream_cliff2', 'cream_water', 'cream_props')


def selected():
    return importlib.import_module(STYLES[VARIANT][1]) if VARIANT else None


def install(namespace):
    painter = selected()
    if painter is None:
        return
    assert set(painter.PALETTES) == set(BANKS)
    for colors in painter.PALETTES.values():
        assert len(colors) == 16
        assert all(len(c) == 7 and c.startswith('#') and
                   all(int(c[i:i+2], 16) % 8 == 0 for i in (1, 3, 5)) for c in colors)
    namespace['PALETTES'] = painter.PALETTES
    for name in PAINTERS:
        namespace[name] = getattr(painter, name)

    # Shared verbs override a misleading decorative symbol in a source study.
    # A magic capability ward is not a key lock; an unlit cage has no flame.
    def role_prop(kind='mold', stage=0, phase=0):
        image = painter.prop(kind, stage, phase).copy()
        draw = ImageDraw.Draw(image)
        if kind == 'ward':
            draw.ellipse((3, 2, 12, 14), fill=1)
            draw.ellipse((4, 3, 11, 13), fill=12)
            draw.line([(5, 5), (11, 5), (8, 11), (5, 5)], fill=13)
            for x,y in ((5,5), (11,5), (8,11)):
                draw.polygon([(x,y-2),(x+1,y),(x,y+1),(x-1,y)],fill=6)
                draw.point((x,y-1),fill=8)
        elif kind == 'switch' and 0 in image.getdata():
            # The existing switch contract is opaque, rather than an overlay.
            # Give it a complete deliberately square stone plinth.
            image.putdata([3 if v == 0 else v for v in image.getdata()])
            draw.line((0,0,15,0),fill=5)
            draw.line((0,1,0,14),fill=4)
            draw.line((0,15,15,15),fill=2)
            draw.line((15,1,15,14),fill=2)
        elif kind == 'lamp' and not phase:
            if VARIANT == 3:
                draw.rectangle((6,4,9,7),fill=2)
                draw.line((7,6,7,7),fill=3)
            elif VARIANT == 4:
                draw.rectangle((5,0,10,5),fill=0)
                draw.line((7,4,7,5),fill=3)
            elif VARIANT >= 5:
                draw.rectangle((6,5,8,8),fill=2)
                draw.point((7,7),fill=3)
        return image
    namespace['prop'] = role_prop
    if VARIANT == 5:
        def quiet_rind_floor(stage=0, variant=0, path=False):
            image = painter.floor(stage, variant, path).copy()
            if not path and variant % 4 == 0:
                draw = ImageDraw.Draw(image)
                draw.rectangle((0,0,7,2),fill=4)
                draw.line([(4,10),(7,9),(9,9)],fill=3)
                draw.line((5,11,8,10),fill=5)
            return image
        namespace['floor'] = quiet_rind_floor


def return_door():
    """Cream-only return, native32x48 illustration in a legal32x64 canvas.

    The shared iron OBJ bank stays intact. Native color-to-bank assignment
    translates the selected cliff material without spatial filtering.
    """
    import reboot_core as core
    painter = selected()
    assert painter is not None
    source = painter.cave(0)
    assert source.mode == 'P' and source.size == (32, 48)
    def rgb(c):
        return tuple(int(c[i:i+2], 16) for i in (1, 3, 5))
    source_bank = list(map(rgb, painter.PALETTES['cream_cliff0']))
    target_bank = list(map(rgb, core.PALETTES['stone']))
    lookup = [0] + [min(range(1, 16), key=lambda k: sum((a-b)**2 for a,b in zip(color, target_bank[k])))
                    for color in source_bank[1:]]
    image = Image.new('P', (32, 48), 0)
    image.putdata([lookup[p] for p in source.getdata()])
    draw = ImageDraw.Draw(image)
    # Clear stair treads and a filled down arrow preserve the existing verb.
    for y,width in ((25,7),(30,10),(36,13),(42,17)):
        x = 16-width//2
        draw.rectangle((x-1,y,x+width+1,y+3),fill=1)
        draw.rectangle((x,y,x+width,y+1),fill=7)
        draw.line((x,y,x+width,y),fill=15)
        draw.line((x,y+2,x+width,y+2),fill=4)
    draw.polygon([(13,0),(19,0),(19,4),(23,4),(16,11),(9,4),(13,4)],fill=1)
    draw.polygon([(15,2),(17,2),(17,6),(20,6),(16,9),(12,6),(15,6)],fill=15)
    padded = Image.new('P', (32, 64), 0)
    padded.paste(image, (0, 16))
    return padded

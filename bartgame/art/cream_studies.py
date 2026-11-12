"""Five optional native Cream environment studies; zero retains selected art.

These are unselected review directions. No high-resolution image is reduced
into a game asset: painters return final-size indexed pixels directly.
"""
import importlib
import os
from PIL import Image, ImageDraw

VARIANT = int(os.environ.get('BART_CREAM', '0'))
if not 0 <= VARIANT <= 5:
    raise ValueError('BART_CREAM must be one integer in 0..5')
STYLES = (
    ('Original Cream', None),
    ('Curdstone Karst', 'cream_style_karst'),
    ('Brine Basilica', 'cream_style_basilica'),
    ('Moldglass Crags', 'cream_style_moldglass'),
    ('Gilt Quarry', 'cream_style_quarry'),
    ('Black Rind Terraces', 'cream_style_rind'),
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

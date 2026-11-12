"""Append-only native panel/edge kit for optional Cream synthesis6.

Every original metatile keeps its ID. Large pictures are cut into hardware
cells only after drawing, so cracks and strata may span unequal wall areas.
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import json
import cream_depth_walls as walls
import cream_depth_edges as edges
from cream_style_depth import floor as floor_art

DIGITS = '0123456789abcdef'
EDGE_KINDS = ('solid_left', 'solid_right', 'drop_left', 'drop_right', 'toe')


def rows(image):
    assert image.mode == 'P' and image.size == (16, 16)
    assert 0 not in image.getdata()
    return [''.join(DIGITS[image.getpixel((x, y))] for x in range(16)) for y in range(16)]


def landing_path(stage, variant, part):
    """Shade the route's actual material, retaining its pressed pale grain."""
    image = floor_art(stage, variant, True).copy()
    mask = edges.landing(stage, part)
    for y in range(16):
        for x in range(16):
            if mask.getpixel((x, y)) == 3:
                ink = image.getpixel((x, y))
                # Pressed path ink5 remains one value lighter inside shade.
                image.putpixel((x, y), 4 if ink >= 5 else 3)
    return image


def build():
    result, panels, rims, drops, sides, landings, floor_toes, path_landings = [], [], [], [], [], [], [], []

    def add(name, image, palette, solid=False):
        result.append(dict(name=name, pal=palette, art=rows(image),
                           type='SOLID' if solid else 'FLOOR',
                           coll=15 if solid else 0, prop=0))
        return name

    for stage in range(3):
        cb, fb = 'cream_cliff%d' % stage, 'cream_floor%d' % stage
        stage_panels = []
        for number, spec in enumerate(walls.SPECS):
            image = walls.panel(stage, spec['kind'], spec['variant'])
            w, h = spec['w'], spec['h']
            assert image.size == (w*16, h*16)
            names = []
            for y in range(h):
                for x in range(w):
                    names.append(add('cream_depth_panel_s%d_p%d_%d_%d' % (stage, number, x, y),
                                     image.crop((x*16, y*16, x*16+16, y*16+16)), cb, True))
            stage_panels.append(dict(first=names[0], w=w, h=h))
        panels.append(stage_panels)
        rims.append([add('cream_depth_rim_s%d_v%d' % (stage, v), edges.rim(stage, v, False), fb, True) for v in range(2)])
        drops.append([add('cream_depth_drop_s%d_v%d' % (stage, v), edges.rim(stage, v, True), fb) for v in range(2)])
        sides.append([add('cream_depth_edge_s%d_%s' % (stage, kind), edges.edge(stage, kind),
                          fb if kind.startswith('drop_') else cb, not kind.startswith('drop_')) for kind in EDGE_KINDS])
        landings.append([add('cream_depth_landing_s%d_p%d' % (stage, part), edges.landing(stage, part), fb) for part in range(6)])
        floor_toes.append([add('cream_depth_floor_toe_s%d_v%d' % (stage, v), edges.floor_toe(stage, v), fb) for v in range(2)])
        path_landings.append([[add('cream_depth_landing_path_s%d_v%d_p%d' % (stage, v, part),
                                   landing_path(stage, v, part), fb) for part in range(6)] for v in range(4)])
    backings = []
    for stage in range(3):
        image = walls.backing(stage)
        assert image.size == (128, 48)
        backings.append([add('cream_depth_backing_s%d_%d_%d' % (stage, x, y),
                             image.crop((x*16, y*16, x*16+16, y*16+16)),
                             'cream_cliff%d' % stage, True)
                         for y in range(3) for x in range(8)])
    assert len(panels[0]) == 7
    return result, dict(panels=panels, rim=rims, drop=drops, edge=sides, landing=landings,
                        floor_toe=floor_toes, landing_path=path_landings, backing=backings)


METATILES, TABLES = build()


def write_review(folder):
    """Source atlas, explicitly separate from emulator evidence."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    width = 352
    canvas = Image.new('RGB', (width, 474), '#15141c')
    draw = ImageDraw.Draw(canvas)
    draw.text((5, 4), 'NATIVE SOURCE ART / NOT A GAME CAPTURE', fill='#e0d8c0')
    for stage in range(3):
        x, y = 4, 22 + stage*150
        draw.text((x, y), ('HEALTHY', 'SOUR', 'DEEP')[stage], fill='#e0d8c0')
        y += 15
        for spec in walls.SPECS:
            im = walls.panel(stage, spec['kind'], spec['variant']).copy()
            colors = [int(c[i:i+2],16) for c in walls.PALETTES['cream_cliff%d' % stage] for i in (1,3,5)]
            im.putpalette(colors + [0]*(768-len(colors)))
            if x + im.width > width:
                x, y = 4, y+50
            canvas.paste(im.convert('RGB'), (x,y))
            x += im.width+4
        for v in range(2):
            for drop in (False,True):
                im=edges.rim(stage,v,drop).copy()
                colors=[int(c[i:i+2],16) for c in edges.PALETTES['cream_floor%d'%stage] for i in (1,3,5)]
                im.putpalette(colors+[0]*(768-len(colors)))
                canvas.paste(im.convert('RGB'),(264+v*36+drop*18,22+stage*150+113))
    canvas.save(folder/'native-source-atlas.png')
    canvas.resize((width*3,474*3),Image.Resampling.NEAREST).save(folder/'source-atlas-3x.png')
    backing_sheet = Image.new('RGB', (256, 222), '#15141c')
    labels = ImageDraw.Draw(backing_sheet)
    labels.text((4, 2), '128x48 NATIVE ROCK / SOURCE ONLY', fill='#e0d8c0')
    for stage in range(3):
        im = walls.backing(stage).copy()
        colors = [int(c[i:i+2],16) for c in walls.PALETTES['cream_cliff%d' % stage] for i in (1,3,5)]
        im.putpalette(colors + [0]*(768-len(colors)))
        y = 22 + stage*64
        backing_sheet.paste(im.convert('RGB'), (4,y))
        labels.text((140,y+12), ('HEALTHY','SOUR','DEEP')[stage], fill='#e0d8c0')
    backing_sheet.save(folder/'backing-source-native.png')
    backing_sheet.resize((768,666),Image.Resampling.NEAREST).save(folder/'backing-source-3x.png')
    (folder/'source-inventory.json').write_text(json.dumps(dict(panels=walls.SPECS, tables=TABLES,
                                                            added_metatiles=len(METATILES)),indent=2)+'\n')

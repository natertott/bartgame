"""Native source crops from the supplied Blighted Forest atlas.

This module only extracts and scales the reference. Final hardware palettes,
terrain edge blending and collision-compatible installation live elsewhere.
The preview is source art, not an emulator screenshot.
"""
from functools import lru_cache
from pathlib import Path
import hashlib
import json
import importlib.util

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ART_ROOT = Path(__file__).resolve().parent
# The repository contains the same illustrated atlas before screenshot
# resizing/JPEG compression. Use it as the pixel source; retain the user's
# supplied screenshot alongside it to make that provenance explicit.
SOURCE = ART_ROOT / 'ref' / 'tile_art' / 'blight.webp'
UPLOADED_SOURCE = ART_ROOT / 'ref' / 'blight-reference.jpg'
TOOLS = ART_ROOT.parent / 'tools'
_spec = importlib.util.spec_from_file_location('_blight_atlas_import', TOOLS / 'import_tiles.py')
_import = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_import)

# Established sample bounds from tools/import_tiles.py. Atlas.cell snaps
# these rough bounds past the gray frames and trims empty paper edge rows.
CROPS = {
    'canopy_sick': ((47,133,141,226),),
    'canopy_sick_lit': ((209,133,303,226),(322,133,416,226)),
    'blight_wall': ((479,133,573,226),(590,133,684,226)),
    'blight_wall_lit': ((750,133,844,226),(863,133,956,226)),
    'blight_ground': ((35,330,127,422),(144,330,236,422)),
    'blight_ground_lit': ((269,330,361,422),(379,330,471,422)),
    'blight_floor': ((510,330,616,422),),
    'blight_floor_pits': ((656,330,762,422),(776,330,872,422)),
    'blight_vein': ((910,330,1006,422),(1030,330,1126,422)),
    'blight_pool': ((1180,330,1276,422),(1303,330,1399,422)),
    'crystal': ((36,536,121,622),),
    'dead_tree': ((132,535,270,662),),
    'mist': ((800,536,872,611),(883,536,956,611)),
    'sparkle': ((988,536,1061,611),(1072,536,1145,611),(1167,536,1240,611)),
    'sparkle_white': ((1270,536,1341,611),(1345,536,1415,611)),
}
TREE_CROP = (537,470,742,707)
ANIMATED = {'canopy_sick_lit','blight_wall_lit','blight_ground_lit',
            'blight_floor_pits','blight_vein','blight_pool','mist','sparkle','sparkle_white'}
TRANSPARENT = {'crystal','dead_tree','blight_vein','mist','sparkle','sparkle_white'}
ALIASES = {'canopy_blight':'canopy_sick','canopy_blight2':'canopy_sick_lit',
           'blight_crystal':'crystal','blight_mist':'mist','blight_floor2':'blight_floor_pits'}


@lru_cache(maxsize=1)
def source_image():
    with Image.open(SOURCE) as im:
        return im.convert('RGB')


@lru_cache(maxsize=1)
def _atlas():
    return _import.Atlas('blight')


def _image(pixels):
    return Image.fromarray(np.clip(np.rint(pixels),0,255).astype('uint8'))


@lru_cache(maxsize=None)
def _tile(name,index):
    atlas=_atlas();box=CROPS[name][index]
    if name in ('crystal','dead_tree'):
        return _image(atlas.thing(box,tol=26,margin=2,snap_it=name!='dead_tree'))
    if name=='mist':
        # Keep the imported alpha for the renderer to dither/composite;
        # no opaque rectangle is baked into the vapour source.
        return _image(atlas.thing(box,margin=0,tol=16,how='center'))
    if name.startswith('sparkle'):
        return _image(_import.glow_only(atlas.thing(box,margin=2,tol=20,how='center'),100))
    pixels=atlas.tile(box,accent=name in ANIMATED or name.startswith('canopy'))
    if name=='blight_vein':pixels=_import.cracks(pixels,lum=70,chroma=55)
    return _image(pixels)


def rgba_tile(name,variant=0,frame=0):
    """Return a 16x16 RGBA sample; terrain is opaque, props/veins are clear."""
    name=ALIASES.get(name,name)
    index=frame if name in ANIMATED else variant
    return _tile(name,index%len(CROPS[name])).copy()


@lru_cache(maxsize=1)
def _tree():
    return _image(_atlas().thing(TREE_CROP,32,48,margin=2,tol=26,snap_it=False))


def tree_image():
    """The complete illustrated tree fitted to the existing 2x3 tile frame."""
    return _tree().copy()


def metadata():
    return {'source':'art/ref/tile_art/blight.webp',
            'supplied_screenshot':'art/ref/blight-reference.jpg',
            'supplied_screenshot_sha256':hashlib.sha256(UPLOADED_SOURCE.read_bytes()).hexdigest(),
            'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            'source_size':list(source_image().size),'tile_crops':CROPS,
            'tree_crop':TREE_CROP,'tree_native_size':[32,48],
            'native_tile_size':[16,16],
            'resample':'Existing Atlas importer: weighted area reduction, middle-tone median, dark and bright-accent preservation',
            'transparent_samples':sorted(TRANSPARENT),
            'alpha':'Existing edge-keyed source object alpha retained. Mist carries area alpha; sparkles keep bright cores; veins retain luminous cracks.',
            'composition':'Source sample interiors only; no text, sample frames or gold atlas border.'}


def catalogue(path='/workspace/setup/blight-source-preview.png'):
    entries=[]
    for name,crops in CROPS.items():
        for index in range(len(crops)):
            im=rgba_tile(name,frame=index) if name in ANIMATED else rgba_tile(name,variant=index)
            entries.append((name,index,im))
    w,h=200,120;cols=6
    out=Image.new('RGB',(cols*w,48+((len(entries)+cols-1)//cols)*h),'#101820')
    d=ImageDraw.Draw(out);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
    d.text((12,10),'Source atlas crops — native16 and nearest4x (not emulator captures)',font=font,fill='#eee9d7')
    for i,(name,index,im) in enumerate(entries):
        x=(i%cols)*w;y=48+(i//cols)*h
        large=im.resize((64,64),Image.Resampling.NEAREST)
        out.paste(large,(x+10,y),large);out.paste(im,(x+90,y+48),im)
        d.text((x+10,y+73),name,font=font,fill='#eee9d7')
        d.text((x+10,y+90),'frame/variant '+str(index),font=font,fill='#9eafba')
    out.save(path)
    tree=tree_image();view=Image.new('RGB',(400,240),'#101820')
    zoom=tree.resize((128,192),Image.Resampling.NEAREST);view.paste(zoom,(16,24),zoom);view.paste(tree,(180,168),tree)
    ImageDraw.Draw(view).text((180,24),'Actual source tree\n32x48 / 4x preview',font=font,fill='#eee9d7')
    p=Path(path);view.save(p.with_name(p.stem+'-tree.png'))
    p.with_suffix('.json').write_text(json.dumps(metadata(),indent=2)+'\n')
    return path


if __name__=='__main__':
    import sys
    print(catalogue(sys.argv[1] if len(sys.argv)>1 else '/workspace/setup/blight-source-preview.png'))

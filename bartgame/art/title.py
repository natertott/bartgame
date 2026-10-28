"""Native240×160 title, authored as integer pixel geometry in reboot_ui."""
import hashlib,json,struct
from pathlib import Path
from PIL import Image
import reboot_ui
WIDTH,HEIGHT=240,160

def render_bitmap():
    im=reboot_ui.title_image()
    return [(r>>3)|((g>>3)<<5)|((b>>3)<<10) for r,g,b in im.getdata()]

def metadata(bitmap=None):
    if bitmap is None:bitmap=render_bitmap()
    raw=struct.pack('<%dH'%len(bitmap),*bitmap)
    return {'authoring':'Native integer pixel geometry; no imported image or resampling','producer':'art/reboot_ui.py:title_image',
            'target_size':[WIDTH,HEIGHT],'pixel_format':'GBA Mode3 RGB555 little-endian','pixel_count':len(bitmap),'bitmap_bytes':len(raw),
            'bitmap_sha256':hashlib.sha256(raw).hexdigest(),'unique_rgb555_colours':len(set(bitmap)),
            'palette_limit':48,'composition':'Native grail/stepped brass title above filthy roots and Drain masonry; quiet dark-water channel for dynamic prompts.'}

def write_metadata(path,bitmap=None):Path(path).write_text(json.dumps(metadata(bitmap),indent=2)+'\n')

def bitmap_image(bitmap=None):
    if bitmap is None:bitmap=render_bitmap()
    im=Image.new('RGB',(WIDTH,HEIGHT));im.putdata([(((v&31)<<3)|((v&31)>>2),(((v>>5)&31)<<3)|(((v>>5)&31)>>2),(((v>>10)&31)<<3)|(((v>>10)&31)>>2)) for v in bitmap]);return im

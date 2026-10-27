"""Import the supplied title artwork into the GBA's native bitmap format.

The complete reference is retained, including its border and baked lettering.
Only spatial reduction and RGB555 conversion are applied; no part is redrawn.
Mode 3 avoids reducing the artwork to the former 16-colour title palette.
"""
import hashlib
import json
from pathlib import Path
import struct
import sys

from PIL import Image, __version__ as PILLOW_VERSION

SOURCE = Path(__file__).resolve().parent / 'ref' / 'title-reference.jpg'
WIDTH, HEIGHT = 240, 160
RESAMPLE = Image.Resampling.LANCZOS


def render_bitmap():
    """Return 38,400 row-major RGB555 words for the Mode 3 framebuffer."""
    with Image.open(SOURCE) as source:
        native = source.convert('RGB').resize((WIDTH, HEIGHT), RESAMPLE)
    rgb = native.tobytes()
    return [(rgb[i] >> 3) | ((rgb[i + 1] >> 3) << 5) | ((rgb[i + 2] >> 3) << 10)
            for i in range(0, len(rgb), 3)]


def metadata(bitmap=None):
    """Record the exact source and deterministic conversion for review."""
    if bitmap is None:
        bitmap = render_bitmap()
    with Image.open(SOURCE) as source:
        size = source.size
    raw = struct.pack('<%dH' % len(bitmap), *bitmap)
    return {
        'source': 'art/ref/title-reference.jpg',
        'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'source_size': list(size),
        'crop_rect': [0, 0, *size],
        'resample': 'Pillow Image.Resampling.LANCZOS',
        'pillow_version': PILLOW_VERSION,
        'target_size': [WIDTH, HEIGHT],
        'pixel_format': 'GBA Mode 3 RGB555, little-endian u16, row-major',
        'pixel_count': len(bitmap),
        'bitmap_bytes': len(raw),
        'bitmap_sha256': hashlib.sha256(raw).hexdigest(),
        'unique_rgb555_colours': len(set(bitmap)),
        'composition': 'Entire reference retained; no crop, redraw, or added lettering.',
        'aspect': 'Full image resized to 3:2, retaining every gold border ornament.',
    }


def write_metadata(path, bitmap=None):
    Path(path).write_text(json.dumps(metadata(bitmap), indent=2) + '\n')


def bitmap_image(bitmap=None):
    """Preview the stored five-bit channels using eight-bit expansion."""
    if bitmap is None:
        bitmap = render_bitmap()
    def channel(value):
        return (value << 3) | (value >> 2)
    preview = Image.new('RGB', (WIDTH, HEIGHT))
    preview.putdata([(channel(v & 31), channel((v >> 5) & 31), channel((v >> 10) & 31))
                     for v in bitmap])
    return preview


if __name__ == '__main__':
    output = Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/title.png')
    bitmap = render_bitmap()
    preview = bitmap_image(bitmap)
    preview.save(output)
    preview.resize((WIDTH * 3, HEIGHT * 3), Image.Resampling.NEAREST).save(
        output.with_name(output.stem + '-3x.png'))
    write_metadata(output.with_suffix('.json'), bitmap)
    print('Imported title:', output)

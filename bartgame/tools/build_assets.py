"""BARTGAME asset builder.

Reads the art modules in ../art and writes OUTDIR/assets.c and assets.h:

  palettes      pal_bg[][16], pal_obj[][16] and PAL_BG_*/PAL_OBJ_* slots
  metatiles     one global 8x8 tileset (deduplicated, flips reused), the
                4 map entries per metatile, its type and collision byte,
                and the animated metatiles' frame data
  sprites       per sheet, frames of 4bpp tiles in OBJ 1D order
  ui            the UI's proportional face, its kit of frames and inks
  title         the title screen as a native RGB555 bitmap
  rooms         hand-authored rooms as metatile grids

Pixel art is written as rows of hex digits: one character per pixel, the
palette index 0-F, with '.' also meaning 0 (transparent).

    python3 tools/build_assets.py build/gen
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'art'))

import palettes  # noqa: E402
import tiles  # noqa: E402
import sprites  # noqa: E402
import title  # noqa: E402
import rooms  # noqa: E402
import reboot_actors  # noqa: E402
import sewer_concepts as SC  # noqa: E402
import ui_studies as UI_STUDIES  # noqa: E402
import forest_concepts as FOREST_CONCEPTS  # noqa: E402
import cream_terrain  # noqa: E402
import handoff_items  # noqa: E402

# Some canonical IDs (moss, a torch, a boulder) are shared between regions.
# A forest refinement must not repaint the Drain or mystery-room kit. Read
# the preceding selected painters in an isolated process so module globals
# and cached images cannot leak between the two native art configurations.
protected31 = None
if FOREST_CONCEPTS.COHESION_ROUND:
    baseline_env = dict(os.environ, BART_FOREST='31')
    baseline_code = ('import json,palettes,tiles; '
                     'print(json.dumps({"palettes":palettes.BG_PALETTES,'
                     '"metatiles":tiles.METATILES}))')
    protected31 = json.loads(subprocess.check_output(
        [sys.executable, '-c', baseline_code],
        cwd=os.path.join(HERE, '..', 'art'), env=baseline_env, text=True))
    assert [name for name, _ in protected31['palettes']] == [name for name, _ in palettes.BG_PALETTES]
    protected31['by_name'] = {mt['name']: mt for mt in protected31['metatiles']}

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'build', 'gen')
os.makedirs(OUT, exist_ok=True)


def rgb15(hexstr):
    h = hexstr.lstrip('#')
    r, g, b = int(h[0:2], 16) >> 3, int(h[2:4], 16) >> 3, int(h[4:6], 16) >> 3
    return r | (g << 5) | (b << 10)


def parse_art(rows, w, h):
    """rows: list of strings of hex digits. Returns list of lists of ints."""
    assert len(rows) == h, 'art has %d rows, want %d: %r' % (len(rows), h, rows[0] if rows else '')
    out = []
    for y, row in enumerate(rows):
        assert len(row) == w, 'row %d has %d cols, want %d: %r' % (y, len(row), w, row)
        out.append([0 if ch in '. ' else int(ch, 16) for ch in row])
    return out


def tile_bytes(pix, x0, y0):
    """One 8x8 subtile of a pixel grid as 32 bytes (4bpp, low nibble first)."""
    out = []
    for y in range(8):
        for x in range(0, 8, 2):
            a = pix[y0 + y][x0 + x]
            b = pix[y0 + y][x0 + x + 1]
            out.append(a | (b << 4))
    return bytes(out)


def tile_key(pix, x0, y0):
    return tuple(pix[y0 + y][x0 + x] for y in range(8) for x in range(8))


def flip_key(key, h, v):
    g = [list(key[y * 8:(y + 1) * 8]) for y in range(8)]
    if h:
        g = [row[::-1] for row in g]
    if v:
        g = g[::-1]
    return tuple(c for row in g for c in row)


class Tileset:
    """A deduplicating 8x8 tile store for one charblock pair (max 1024)."""

    def __init__(self, limit=1024):
        self.tiles = []        # bytes per tile
        self.index = {}        # key -> (tile, hflip, vflip)
        self.limit = limit

    def add(self, pix, x0, y0, dedup=True):
        key = tile_key(pix, x0, y0)
        if dedup:
            if key in self.index:
                return self.index[key]
        n = len(self.tiles)
        assert n < self.limit, 'tileset overflow'
        self.tiles.append(tile_bytes(pix, x0, y0))
        if dedup:
            for h in (0, 1):
                for v in (0, 1):
                    k = flip_key(key, h, v)
                    if k not in self.index:
                        self.index[k] = (n, h, v)
        return (n, 0, 0)


def c_array_u16(name, values, per_line=16, const=True):
    lines = ['%sconst u16 %s[%d] ALIGN4 = {' % ('' if const else 'static ', name, len(values))]
    for i in range(0, len(values), per_line):
        lines.append('    ' + ', '.join('0x%04x' % v for v in values[i:i + per_line]) + ',')
    lines.append('};')
    return '\n'.join(lines)


def c_array_u8(name, values, per_line=24):
    lines = ['const u8 %s[%d] ALIGN4 = {' % (name, len(values))]
    for i in range(0, len(values), per_line):
        lines.append('    ' + ', '.join('%d' % v for v in values[i:i + per_line]) + ',')
    lines.append('};')
    return '\n'.join(lines)


def bytes_to_u16(b):
    return [b[i] | (b[i + 1] << 8) for i in range(0, len(b), 2)]


def cname(s):
    return ''.join(ch if ch.isalnum() else '_' for ch in s).upper()


c = []
h = []
h.append('/* GENERATED by tools/build_assets.py. Do not edit. */')
h.append('#ifndef ASSETS_H\n#define ASSETS_H\n#include "gba.h"\n')
c.append('/* GENERATED by tools/build_assets.py. Do not edit. */')
c.append('#include "gba.h"\n#include "assets.h"\n')

# ------------------------------------------------------------ palettes --
bg_slots = {}
obj_slots = {}
vals = []
global_bg_palettes = protected31['palettes'] if protected31 else palettes.BG_PALETTES
for i, (name, cols) in enumerate(global_bg_palettes):
    assert len(cols) == 16, name
    bg_slots[name] = i
    h.append('#define PAL_BG_%s %d' % (cname(name), i))
    vals += [rgb15(x) for x in cols]
c.append(c_array_u16('pal_bg', vals))
h.append('#define PAL_BG_COUNT %d' % len(palettes.BG_PALETTES))
h.append('extern const u16 pal_bg[];')
# The hardware's 16 BG palettes: each area's tileset loads its own groups
# into the first PAL_AREA_SLOTS when the area is entered; the pause map,
# the UI kit (the boxes, the shop, the pause pages) and the HUD keep
# slots of their own after them (14 is free).
PAL_AREA_SLOTS = 12
h.append('#define PAL_AREA_SLOTS %d' % PAL_AREA_SLOTS)
h.append('#define PAL_SLOT_MAP 12 /* the pause map, its own colours */')
h.append('#define PAL_SLOT_MENU 13')
h.append('#define PAL_SLOT_HUD 15')
vals = []
for i, (name, cols) in enumerate(palettes.OBJ_PALETTES):
    assert len(cols) == 16, name
    obj_slots[name] = i
    h.append('#define PAL_OBJ_%s %d' % (cname(name), i))
    vals += [rgb15(x) for x in cols]
c.append(c_array_u16('pal_obj', vals))
h.append('#define PAL_OBJ_COUNT %d' % len(palettes.OBJ_PALETTES))
h.append('extern const u16 pal_obj[];')
assert len(palettes.OBJ_PALETTES) <= 16
# a palette per face, loaded into the portrait slot with the speaker
vals = []
for cols in palettes.FACE_PALETTES:
    assert len(cols) == 16
    vals += [rgb15(x) for x in cols]
c.append(c_array_u16('pal_face', vals))
h.append('extern const u16 pal_face[];')


# ----------------------------------------------------------- metatiles --
TYPES = tiles.TYPES
for i, t in enumerate(TYPES):
    h.append('#define TT_%s %d' % (t, i))
h.append('')

# Three tilesets, one per area, each its own charblock pair of at most
# 1024 subtiles, loaded when the area changes: the forest (everything
# not of the sewer or the mystery rooms), the sewer (its own tiles and
# whatever the hub's room uses), the mystery rooms (their three styles,
# the overlay things, and what an event may put down). A metatile keeps
# one global id; each set carries its own map entries for it, blank
# where the set does not hold it.
mt_names = {}
for i, mt in enumerate(tiles.METATILES):
    assert mt['name'] not in mt_names, 'duplicate metatile ' + mt['name']
    mt_names[mt['name']] = i
hub_used = set()
for r in rooms.ROOMS:
    for layer in ('ground', 'overlay'):
        if r.get(layer):
            hub_used |= set(rooms.expand(r[layer], r['w'], r['h'], mt_names))
MYST_EXTRA = {'torch', 'torch_lit', 'boulder', 'chest', 'chest_open', 'sparkle', 'black', 'moss0', 'moss1', 'moss2'}
SETS = [
    ('forest', lambda n, i: not n.startswith(('sw_', 'swh_', 'cave_', 'hollow_', 'thicket_', 'myst_', 'cream_', 'lh_'))),
    ('sewer', lambda n, i: i in hub_used or (SC.VARIANT != 9 and n.startswith('swh_'))),
    ('myst', lambda n, i: n.startswith(('cave_', 'hollow_', 'thicket_', 'myst_', 'lh_')) or n in MYST_EXTRA),
    ('cream', lambda n, i: n.startswith(('cream_','lh_'))),
]
TYPES_IDX = {t: i for i, t in enumerate(TYPES)}
mt_type = [TYPES_IDX[mt['type']] for mt in tiles.METATILES]
mt_coll = [mt.get('coll', tiles.default_coll(mt['type'])) for mt in tiles.METATILES]
for i, mt in enumerate(tiles.METATILES):
    h.append('#define MT_%s %d' % (cname(mt['name']), i))
h.append('#define METATILE_COUNT %d' % len(tiles.METATILES))
c.append(c_array_u8('metatile_type', mt_type))
h.append('extern const u8 metatile_type[];')
c.append(c_array_u8('metatile_coll', mt_coll))
h.append('extern const u8 metatile_coll[];')
c.append(c_array_u8('metatile_prop', [int(bool(mt.get('prop'))) for mt in tiles.METATILES]))
h.append('extern const u8 metatile_prop[];')
c.append(c_array_u8('metatile_glitter', [int(bool(mt.get('glitter'))) for mt in tiles.METATILES]))
h.append('extern const u8 metatile_glitter[];')
h.append('typedef struct { u16 tile; u8 frames; u8 speed; const u16* data; } TileAnim;')
h.append('typedef struct { const u16* tiles; u16 tile_count; const u16* map; const TileAnim* anims; u8 anim_count; const u16* pals; u8 pal_count; } Tileset;')
set_rows = []
forest_v2_pulse_slots = []
forest_v2_pulses = {}
if FOREST_CONCEPTS.VARIANT >= 6:
    _, forest_terrain = FOREST_CONCEPTS.painters()
    forest_v2_pulses = forest_terrain.pulse_palettes(FOREST_CONCEPTS.LOCAL_VARIANT)
for si, (sname, pred) in enumerate(SETS):
    area_metatiles = ([protected31['by_name'].get(mt['name'], mt) for mt in tiles.METATILES]
                     if protected31 and sname != 'forest' else tiles.METATILES)
    area_palette_colors = dict(protected31['palettes'] if protected31 and sname != 'forest'
                               else palettes.BG_PALETTES)
    if sname == 'cream':
        area_palette_colors.update(cream_terrain.PALETTES)
    if sname in ('cream','myst'):
        area_palette_colors.update(handoff_items.BGPALETTES)
    ts = Tileset(limit=768 if FOREST_CONCEPTS.TREE_WORLD and sname == 'forest' else 1024)
    ts.add([[0] * 8 for _ in range(8)], 0, 0)  # tile 0 blank
    entries = []
    anims = []
    animation_cache = {}
    held = 0
    # the set's palette groups, in the order its metatiles first use them;
    # a metatile may give each of its quarters a palette of its own (qpals)
    set_pals = []
    for i, mt in enumerate(area_metatiles):
        if pred(mt['name'], i):
            for pn in mt.get('qpals') or [mt['pal']]:
                if pn not in set_pals:
                    set_pals.append(pn)
    assert len(set_pals) <= PAL_AREA_SLOTS, ('tileset %s needs %d palettes' % (sname, len(set_pals)), set_pals)
    if FOREST_CONCEPTS.VARIANT >= 6:
        forest_v2_pulse_slots.append([set_pals.index(name) if name in set_pals
                                      and sname != 'sewer' else 255
                                      for name in forest_v2_pulses])
    for i, mt in enumerate(area_metatiles):
        if not pred(mt['name'], i):
            entries += [0, 0, 0, 0]
            continue
        held += 1
        qpals = [set_pals.index(pn) for pn in (mt.get('qpals') or [mt['pal']] * 4)]
        frames = mt.get('frames') or [mt['art']]
        pix = parse_art(frames[0], 16, 16)
        animated = len(frames) > 1
        # Placement-specific final Drain IDs need not reserve separate VRAM
        # for identical complete animations. Compare every frame, exact
        # orientation, timing and quarter palette assignment; a first-frame
        # match alone would let unrelated moving surfaces overwrite each other.
        animation_key = None
        if animated and ((SC.VARIANT == 9 and sname == 'sewer') or
                         (FOREST_CONCEPTS.VARIANT >= 6 and sname == 'forest')):
            animation_key = (tuple(tuple(fr) for fr in frames),
                             mt.get('anim_speed', 8), tuple(qpals))
            if animation_key in animation_cache:
                base = animation_cache[animation_key]
                entries += [(base + q) | (qpals[q] << 12) for q in range(4)]
                continue
        base = None
        for q, (x0, y0) in enumerate(((0, 0), (8, 0), (0, 8), (8, 8))):
            n, hf, vf = ts.add(pix, x0, y0, dedup=not animated)
            if base is None:
                base = n
            entries.append(n | (hf << 10) | (vf << 11) | (qpals[q] << 12))
        if animated:
            data = b''
            for fr in frames:
                fp = parse_art(fr, 16, 16)
                for (x0, y0) in ((0, 0), (8, 0), (0, 8), (8, 8)):
                    data += tile_bytes(fp, x0, y0)
            anims.append((base, len(frames), data, mt.get('anim_speed', 8)))
            if animation_key is not None:
                animation_cache[animation_key] = base
    if FOREST_CONCEPTS.ADAPTIVE_ROUND and not FOREST_CONCEPTS.TREE_WORLD and sname == 'forest':
        if FOREST_CONCEPTS.EMERALD_ROUND:
            import forest_canopy_emerald as ACA
        else:
            import forest_canopy_adaptive as ACA
        adaptive_specs = ACA.prefab_specs(FOREST_CONCEPTS.LOCAL_VARIANT)
        assert len(adaptive_specs) == 9
        assert ACA.PALETTE_NAME in set_pals
        adaptive_slot = set_pals.index(ACA.PALETTE_NAME)
        h.append('typedef struct { const u16* map; u8 w,h,role,flags; } CanopyPrefab;')
        h.append('#define CANOPY_PREFAB_COUNT %d' % len(adaptive_specs))
        h.append('#define CANOPY_PALETTE_SLOT %d' % adaptive_slot)
        h.append('extern const CanopyPrefab canopy_prefabs[CANOPY_PREFAB_COUNT];')
        h.append('extern const u16 canopy_solid_branch[16];')
        h.append('extern const u16 canopy_stage_colors[4][4][16];')
        adaptive_rows = []
        adaptive_coverage = []
        adaptive_base_tiles = len(ts.tiles)
        for role, spec in enumerate(adaptive_specs):
            image = ACA.prefab(FOREST_CONCEPTS.LOCAL_VARIANT, spec['role'], 0)
            w, hh = image.size
            assert image.mode == 'P' and w % 16 == hh % 16 == 0
            assert (w, hh) == (spec['w'], spec['h'])
            assert set(image.tobytes()) <= set(range(16))
            pixels = parse_art(FOREST_CONCEPTS.rows(image), w, hh)
            packed = []
            for y in range(0, hh, 8):
                for x in range(0, w, 8):
                    tile, hf, vf = ts.add(pixels, x, y)
                    packed.append(tile | (hf << 10) | (vf << 11) | (adaptive_slot << 12))
            cname_map = 'canopy_prefab_%d_map' % role
            c.append(c_array_u16(cname_map, packed))
            adaptive_rows.append('  { %s, %d, %d, %d, 0 },' % (cname_map, w//16, hh//16, role))
            adaptive_coverage.append({**spec, 'role_index': role, 'native_size': [w, hh],
                                      'map_entries': len(packed)})
        c.append('const CanopyPrefab canopy_prefabs[CANOPY_PREFAB_COUNT] = {')
        c.extend(adaptive_rows)
        c.append('};')
        image = ACA.blocked_branch(FOREST_CONCEPTS.LOCAL_VARIANT)
        assert image.mode == 'P' and image.size == (64, 16)
        assert set(image.tobytes()) <= set(range(16))
        pixels = parse_art(FOREST_CONCEPTS.rows(image), 64, 16)
        solid_branch = []
        for y in range(0, 16, 8):
            for x in range(0, 64, 8):
                tile, hf, vf = ts.add(pixels, x, y)
                solid_branch.append(tile | (hf << 10) | (vf << 11) | (adaptive_slot << 12))
        c.append(c_array_u16('canopy_solid_branch', solid_branch))
        adaptive_colors = []
        c.append('const u16 canopy_stage_colors[4][4][16] = {')
        for stage in range(4):
            phases = ACA.pulse_palettes(FOREST_CONCEPTS.LOCAL_VARIANT, stage)[ACA.PALETTE_NAME]
            assert len(phases) == 4
            adaptive_colors.append(phases)
            c.append('  {')
            for colors in phases:
                assert len(colors) == 16
                assert all(int(color[k:k+2],16)%8 == 0 for color in colors for k in (1,3,5))
                c.append('    {' + ','.join(str(rgb15(color)) for color in colors) + '},')
            c.append('  },')
        c.append('};')
        adaptive_atlas_metadata = {
            'prefabs': adaptive_coverage, 'palette_slot': adaptive_slot,
            'static_base_tiles': adaptive_base_tiles,
            'prefab_extra_tiles': len(ts.tiles)-adaptive_base_tiles,
            'total_resident_tiles': len(ts.tiles), 'stage_pulse_colors': adaptive_colors,
            'solid_branch': {'native_size': [64, 16], 'map_entries': len(solid_branch)},
            'plan': 'Map first; fit unequal native compositions to connected available space.',
            'retired_canopy_pictures': 'Quiet backing only; no previous canopy image is used.',
        }
        if FOREST_CONCEPTS.EMERALD_ROUND:
            adaptive_atlas_metadata.update(
                reference='User-supplied Pokemon Emerald tree crop; original native leaf-crown drawings.',
                retired_canopy_pictures='Dense foliage joins and overlapping crowns replace skeletal trees and flat backing.',
                substrate='Real local floor remains on BG2; transparent native BG1 entries clear prior infill.',
            )
    if FOREST_CONCEPTS.TREE_WORLD and sname == 'forest':
        import forest_tree_study as TREE_ART
        tree_slot = set_pals.index(TREE_ART.PALETTE_NAME)
        specs = TREE_ART.specs()
        assert len(specs) == 12
        h += ['#define FOREST_TREE_FRAME_COUNT 12',
              '#define FOREST_TREE_PALETTE_SLOT %d' % tree_slot,
              'extern const u16 forest_tree_entries[12][16];',
              'extern const u32 forest_tree_opaque_rows[12][32];']
        tree_rows = []
        tree_alpha = []
        tree_frames = []
        tree_base_tiles = len(ts.tiles)
        for index, spec in enumerate(specs):
            image = TREE_ART.tree(spec['size'], spec['variety'], spec['state'])
            width, height = image.size
            assert image.mode == 'P' and (width, height) in ((32, 32), (16, 32))
            assert set(image.tobytes()) <= set(range(16))
            pixels = parse_art(FOREST_CONCEPTS.rows(image), width, height)
            tree_alpha.append('  {' + ','.join('0x%08xu' % sum((1 << x) for x in range(width) if pixels[y][x])
                                               for y in range(height)) + '},')
            packed = []
            for yy in range(0, height, 8):
                for xx in range(0, width, 8):
                    tile, hf, vf = ts.add(pixels, xx, yy)
                    packed.append(tile | (hf << 10) | (vf << 11) | (tree_slot << 12))
            tree_rows.append('  {' + ','.join(str(v) for v in packed + [0]*(16-len(packed))) + '},')
            tree_frames.append({**spec, 'index': index, 'entries': len(packed)})
        c += ['const u16 forest_tree_entries[12][16] = {', *tree_rows, '};']
        c += ['const u32 forest_tree_opaque_rows[12][32] = {', *tree_alpha, '};']
        values = {
            'width': [s['size_pixels'][0] for s in specs],
            'anchor_x': [s['anchor'][0] for s in specs],
            'anchor_y': [s['anchor'][1] for s in specs],
            'state': [TREE_ART.STATES.index(s['state']) for s in specs],
            'variety': [s['variety'] for s in specs],
        }
        for field, field_values in values.items():
            symbol = 'forest_tree_' + field
            c.append(c_array_u8(symbol, field_values))
            h.append('extern const u8 %s[12];' % symbol)
        tree_world_metadata = {
            'frames': tree_frames, 'palette_slot': tree_slot,
            'source': 'forest_tree_study.py, unchanged approved twelve native pictures',
            'static_base_tiles': tree_base_tiles,
            'tree_extra_tiles': len(ts.tiles)-tree_base_tiles,
            'total_resident_tiles': len(ts.tiles), 'tile_limit': 768,
            'layer_contract': {'floor': 'BG2', 'upper16': 'BG1', 'lower16': 'BG3'},
            'retired': 'forest_trees_terrain.owns() legacy canopy and authored tree pictures',
            'collision': 'Generated solid tree-base cells preserved; no full32px canvas collider.',
        }
    c.append(c_array_u16('tileset_%s_tiles' % sname, bytes_to_u16(b''.join(ts.tiles))))
    c.append(c_array_u16('metatile_map_%s' % sname, entries, 8))
    c.append(c_array_u16('tileset_%s_pals' % sname, [rgb15(x) for n in set_pals for x in area_palette_colors[n]]))
    for k, (base, nfr, data, speed) in enumerate(anims):
        c.append(c_array_u16('tile_anim_%s_%d' % (sname, k), bytes_to_u16(data)))
    c.append('static const TileAnim tile_anims_%s[%d] = {' % (sname, max(1, len(anims))))
    for k, (base, nfr, data, speed) in enumerate(anims):
        c.append('    { %d, %d, %d, tile_anim_%s_%d },' % (base, nfr, speed, sname, k))
    if not anims:
        c.append('    { 0, 0, 0, NULL },')
    c.append('};')
    h.append('#define TS_%s %d' % (sname.upper(), si))
    set_rows.append('    { tileset_%s_tiles, %d, metatile_map_%s, tile_anims_%s, %d, tileset_%s_pals, %d },' % (sname, len(ts.tiles), sname, sname, len(anims), sname, len(set_pals)))
    print('tileset %s: %d tiles, %d metatiles held, %d animated, %d palettes' % (sname, len(ts.tiles), held, len(anims), len(set_pals)))
    assert len(anims) <= 255, ('too many animation allocations', sname, len(anims))
    if FOREST_CONCEPTS.TREE_ROUND and sname == 'forest':
        tree_study_forest_palettes = list(set_pals)
c.append('const Tileset tilesets[%d] = {' % len(SETS))
c += set_rows
c.append('};')
h.append('extern const Tileset tilesets[];')
if FOREST_CONCEPTS.TREE_ROUND:
    # A separate diagnostic atlas preserves the normal forest/canopy residency.
    import forest_tree_study as TREE_ART
    study_ts = Tileset()
    study_ts.add([[0]*8 for _ in range(8)], 0, 0)
    study_palette = TREE_ART.palette()
    assert len(study_palette) == 16
    assert all(int(color[k:k+2], 16) % 8 == 0 for color in study_palette for k in (1, 3, 5))
    assert len(tree_study_forest_palettes) <= 11
    study_slot = 11
    def study_map(pixels, width, height, slots):
        packed = []
        for yy in range(0, height, 8):
            for xx in range(0, width, 8):
                tile, hf, vf = study_ts.add(pixels, xx, yy)
                slot = slots[(yy//8)*(width//8)+xx//8] if isinstance(slots, list) else slots
                packed.append(tile | (hf << 10) | (vf << 11) | (slot << 12))
        return packed
    floor_names = ('moss0', 'path', 'blight_floor')
    floor_maps = []
    for name in floor_names:
        mt = tiles.METATILES[mt_names[name]]
        art = mt.get('art') or mt['frames'][0]
        colors = mt.get('qpals') or [mt['pal']]*4
        floor_maps.append(study_map(parse_art(art, 16, 16), 16, 16,
                                    [tree_study_forest_palettes.index(p) for p in colors]))
    specs = TREE_ART.specs()
    assert len(specs) == 12
    h += ['#define TREE_STUDY_COUNT 12', '#define TREE_STUDY_PALETTE_SLOT 11',
          'typedef struct { const u16* map; u8 w,h,size,variety,state; } TreeStudyFrame;',
          'extern const TreeStudyFrame tree_study_frames[TREE_STUDY_COUNT];',
          'extern const u16 tree_study_tiles[];', 'extern const u16 tree_study_palette[16];',
          'extern const u16 tree_study_floor[3][4];', 'extern const u16 TREE_STUDY_FLOOR_MT[3];']
    descriptor_rows = []
    packed_specs = []
    for index, spec in enumerate(specs):
        image = TREE_ART.tree(spec['size'], spec['variety'], spec['state'])
        width, height = image.size
        assert image.mode == 'P' and image.size in ((32, 32), (16, 32))
        assert set(image.tobytes()) <= set(range(16))
        packed = study_map(parse_art(FOREST_CONCEPTS.rows(image), width, height), width, height, study_slot)
        symbol = 'tree_study_map_%d' % index
        c.append(c_array_u16(symbol, packed))
        descriptor_rows.append('  { %s, %d, %d, %d, %d, %d },' %
                               (symbol, width//8, height//8, int(spec['size']=='narrow'),
                                spec['variety'], TREE_ART.STATES.index(spec['state'])))
        packed_specs.append({**spec, 'map_symbol': symbol, 'map_entries': len(packed)})
    assert len(study_ts.tiles) <= 1024
    h.append('#define TREE_STUDY_TILE_COUNT %d' % len(study_ts.tiles))
    c += ['const TreeStudyFrame tree_study_frames[TREE_STUDY_COUNT] = {', *descriptor_rows, '};']
    c.append(c_array_u16('tree_study_tiles', bytes_to_u16(b''.join(study_ts.tiles))))
    c.append(c_array_u16('tree_study_palette', [rgb15(color) for color in study_palette]))
    c += ['const u16 tree_study_floor[3][4] = {',
          *['  {'+','.join(str(v) for v in row)+'},' for row in floor_maps], '};']
    c.append(c_array_u16('TREE_STUDY_FLOOR_MT', [mt_names[n] for n in floor_names]))
    tree_study_metadata = {'scope': 'Tree-only diagnostic grove; regular forest and canopy stay at profile29.',
                           'frames': packed_specs, 'palette': study_palette, 'palette_slot': study_slot,
                           'resident_tiles': len(study_ts.tiles), 'floor_names': list(floor_names),
                           'floor_maps': floor_maps, 'origin': 'bottom-center y=30; canvas is not collider'}
if FOREST_CONCEPTS.VARIANT >= 6:
    import forest_concepts_v2_topology as F2T
    topology = tiles.FOREST_V2_TOPOLOGY
    kinds, waters = F2T.classes(tiles.METATILES)
    h += ['extern const u8 forest_v2_canopy_kind[];',
          'extern const u8 forest_v2_water_kind[];',
          'extern const u8 forest_v2_special_tree[];',
          'extern const u8 forest_v2_overhead[];',
          'extern const u8 forest_v2_low_fringe[];',
          'extern const u16 forest_v2_visual_parent[];',
          'extern const u16 forest_v2_canopy_alias[2][4][16][16];',
          'extern const u16 forest_v2_fringe_alias[2][16];',
          'extern const u16 forest_v2_water_alias[16][16];',
          'extern const u16 forest_v2_water_isolated[2];']
    c.append(c_array_u8('forest_v2_canopy_kind', kinds))
    c.append(c_array_u8('forest_v2_water_kind', waters))
    c.append(c_array_u8('forest_v2_special_tree', F2T.special_trees(tiles.METATILES)))
    parents = list(range(len(tiles.METATILES)))
    overhead = F2T.authored_crowns(tiles.METATILES)
    low_fringe = [0] * len(parents)
    for spec in topology['specs']:
        i = mt_names[spec['name']]
        parents[i] = mt_names[spec['parent']]
        overhead[i] = int(spec['family'] in ('canopy', 'fringe', 'overhead_root_arch'))
        low_fringe[i] = int(spec['family'] == 'fringe')
    c.append(c_array_u16('forest_v2_visual_parent', parents))
    c.append(c_array_u8('forest_v2_overhead', overhead))
    c.append(c_array_u8('forest_v2_low_fringe', low_fringe))
    c.append('const u16 forest_v2_canopy_alias[2][4][16][16] = {')
    for kind in range(2):
        c.append('  {')
        for quadrant in range(4):
            c.append('    {')
            for mask in range(16):
                c.append('      {' + ','.join(str(mt_names[topology['canopy'][kind][quadrant][mask][corner & F2T.eligible_corners(mask)]])
                                          for corner in range(16)) + '},')
            c.append('    },')
        c.append('  },')
    c.append('};')
    c.append('const u16 forest_v2_fringe_alias[2][16] = {')
    for row in topology['fringe']:
        c.append('  {' + ','.join(str(mt_names[name]) if name else '65535' for name in row) + '},')
    c.append('};')
    c.append(c_array_u16('forest_v2_water_isolated', [mt_names[name] for name in topology['isolated_water']]))
    c.append('const u16 forest_v2_water_alias[16][16] = {')
    for mask in range(16):
        c.append('  {' + ','.join(str(mt_names[topology['water'][mask][corner & F2T.eligible_corners(mask)]])
                                for corner in range(16)) + '},')
    c.append('};')
    h.append('#define FOREST_V2_PULSE_COUNT %d' % len(forest_v2_pulses))
    h += ['extern const u8 forest_v2_pulse_slots[%d][FOREST_V2_PULSE_COUNT];' % len(SETS),
          'extern const u16 forest_v2_pulse_colors[FOREST_V2_PULSE_COUNT][4][16];']
    c.append('const u8 forest_v2_pulse_slots[%d][FOREST_V2_PULSE_COUNT] = {' % len(SETS))
    for row in forest_v2_pulse_slots:
        c.append('  {' + ','.join(map(str, row)) + '},')
    c.append('};')
    c.append('const u16 forest_v2_pulse_colors[FOREST_V2_PULSE_COUNT][4][16] = {')
    for bank, phases in forest_v2_pulses.items():
        assert len(phases) == 4 and all(len(palette) == 16 for palette in phases), bank
        assert phases[0] == dict(palettes.BG_PALETTES)[bank], bank
        c.append('  {')
        for palette in phases:
            assert all(int(color[k:k+2],16)%8 == 0 for color in palette for k in (1,3,5)), bank
            c.append('    {' + ','.join(str(rgb15(color)) for color in palette) + '},')
        c.append('  },')
    c.append('};')
h.append('#define TILESET_COUNT %d\n' % len(SETS))

if FOREST_CONCEPTS.COHESION_ROUND:
    import forest_concepts_v2_topology as F2T
    import forest_cohesion_topology as FCT
    path_table = tiles.FOREST_COHESION_TOPOLOGY['path']
    h.append('extern const u16 forest_cohesion_path_alias[2][16][16];')
    c.append('const u16 forest_cohesion_path_alias[2][16][16] = {')
    for kind in range(2):
        c.append('  {')
        for mask in range(16):
            c.append('    {' + ','.join(str(mt_names[path_table[kind][mask][corner & F2T.eligible_corners(mask)]])
                                      for corner in range(16)) + '},')
        c.append('  },')
    c.append('};')
    decor_table = tiles.FOREST_COHESION_TOPOLOGY['decor']
    h.append('#define FOREST_COHESION_DECOR_COUNT %d' % len(FCT.DECOR_NAMES))
    h.append('extern const u16 forest_cohesion_decor_alias[2][FOREST_COHESION_DECOR_COUNT];')
    for index, name in enumerate(FCT.DECOR_NAMES):
        h.append('#define FOREST_COHESION_DECOR_%s %d' % (cname(name), index))
    c.append('const u16 forest_cohesion_decor_alias[2][FOREST_COHESION_DECOR_COUNT] = {')
    for row in decor_table:
        c.append('  {' + ','.join(str(mt_names[name]) for name in row) + '},')
    c.append('};')

# ------------------------------------------------------------- sprites --
SHAPES = {(8, 8): (0, 0), (16, 16): (0, 1), (32, 32): (0, 2), (64, 64): (0, 3),
          (16, 8): (1, 0), (32, 8): (1, 1), (32, 16): (1, 2), (64, 32): (1, 3),
          (8, 16): (2, 0), (8, 32): (2, 1), (16, 32): (2, 2), (32, 64): (2, 3)}
h.append('typedef struct { const u16* tiles; u16 tile_count; u8 frame_tiles; u8 shape; u8 size; u8 pal; u8 w; u8 h; } SpriteSheet;')
sheet_names = []
for sh in sprites.SHEETS:
    name = sh['name']
    w, hgt = sh['w'], sh['h']
    shape, size = SHAPES[(w, hgt)]
    frame_names = list(sh['frames'].keys())
    data = b''
    for fi, fname in enumerate(frame_names):
        pix = parse_art(sh['frames'][fname], w, hgt)
        for ty in range(0, hgt, 8):
            for tx in range(0, w, 8):
                data += tile_bytes(pix, tx, ty)
        h.append('#define F_%s_%s %d' % (cname(name), cname(fname), fi))
    ftiles = (w // 8) * (hgt // 8)
    c.append(c_array_u16('sheet_%s_tiles' % name, bytes_to_u16(data)))
    h.append('#define SHEET_%s_FRAMES %d' % (cname(name), len(frame_names)))
    h.append('#define SHEET_%s_TILES %d' % (cname(name), len(frame_names) * ftiles))
    sheet_names.append((name, len(frame_names) * ftiles, ftiles, shape, size, obj_slots[sh['pal']], w, hgt))
c.append('const SpriteSheet sheets[%d] = {' % len(sheet_names))
for i, (name, tc, ft, shape, size, pal, w, hgt) in enumerate(sheet_names):
    c.append('    { sheet_%s_tiles, %d, %d, %d, %d, %d, %d, %d },' % (name, tc, ft, shape, size, pal, w, hgt))
    h.append('#define SHEET_%s %d' % (cname(name), i))
c.append('};')
h.append('#define SHEET_COUNT %d' % len(sheet_names))
h.append('extern const SpriteSheet sheets[];\n')
print('sprites: %d sheets, %d tiles' % (len(sheet_names), sum(s[1] for s in sheet_names)))

# Immutable native-body metadata keeps the canopy safeguard out of the action
# update budget. Hero pixels/palette are protected; only their lower-band
# bounds/counts are computed here. The runtime copies those existing pixels.
forest_v3_body_rows = None
if FOREST_CONCEPTS.CANOPY_ROUND:
    hero = next(sh for sh in sprites.SHEETS if sh['name'] == 'hero')
    assert (hero['w'], hero['h']) == (32, 32)
    assert all(bank == hero['pal'] for bank in hero.get('frame_pal', {}).values())
    hero_colors = dict(palettes.OBJ_PALETTES)[hero['pal']]
    colored = []
    for ink, color in enumerate(hero_colors):
        value = rgb15(color)
        channels = (value & 31, (value >> 5) & 31, (value >> 10) & 31)
        colored.append(bool(ink and max(channels) >= 5 and sum(channels) >= 10))

    def connected_body(pixels, cutoff, goal):
        if not goal:
            return True
        seen = set()
        for y in range(cutoff, 32):
            for x in range(32):
                if (x, y) in seen or not colored[pixels[y][x]]:
                    continue
                queue = [(x, y)]
                seen.add((x, y))
                count = 0
                for cx, cy in queue:
                    count += 1
                    if count >= goal:
                        return True
                    for nx, ny in ((cx, cy-1), (cx+1, cy), (cx, cy+1), (cx-1, cy)):
                        if (0 <= nx < 32 and cutoff <= ny < 32 and
                                (nx, ny) not in seen and colored[pixels[ny][nx]]):
                            seen.add((nx, ny))
                            queue.append((nx, ny))
        return False

    forest_v3_body_rows = []
    for frame_name, frame in hero['frames'].items():
        pixels = parse_art(frame, 32, 32)
        opaque = sum(bool(ink) for row in pixels for ink in row)
        color_count = sum(colored[ink] for row in pixels for ink in row)
        opaque_goal = min(opaque, max(48, (opaque + 2) // 3))
        color_goal = min(color_count, max(24, (color_count + 2) // 3))
        lower = lower_color = 0
        for cutoff in range(31, -1, -1):
            lower += sum(bool(ink) for ink in pixels[cutoff])
            lower_color += sum(colored[ink] for ink in pixels[cutoff])
            if (lower >= opaque_goal and lower_color >= color_goal and
                    connected_body(pixels, cutoff, min(12, color_count))):
                break
        forest_v3_body_rows.append([cutoff, opaque, lower, color_count, lower_color])
    h.append('extern const u16 forest_v3_body_visibility[SHEET_HERO_FRAMES][5];')
    c.append('const u16 forest_v3_body_visibility[SHEET_HERO_FRAMES][5] ALIGN4 = {')
    for row in forest_v3_body_rows:
        c.append('    {' + ','.join(map(str, row)) + '},')
    c.append('};')

# The same native painter supplies the blade, its render origin and the
# phase-specific collision rectangle. No independent reach table can drift
# away from the compact actor or grow into a permanent range-outline cage.
sword_geometry = reboot_actors.sword_geometry()
origins = [value for pair in sword_geometry['origins'] for value in pair]
hitboxes = [value for facing in sword_geometry['bounds'] for phase in facing for value in phase]
assert len(origins) == 8 and len(hitboxes) == 80
for name, values in (('bloom_sword_origin', origins), ('bloom_sword_hit', hitboxes)):
    assert all(-128 <= value <= 127 for value in values), name
    c.append('const s8 %s[%d] ALIGN4 = { %s };' % (name, len(values), ', '.join(map(str, values))))
    h.append('extern const s8 %s[];' % name)

# Experimental studies append native poses without replacing the production
# frames. One generated age clock drives body, blade and contact together.
h.append('#define BLOOM_SWING_STUDY %d' % sprites.SWING_VARIANT)
sword_study_metadata=None
if sprites.SWING_VARIANT:
    profile=sprites.SWING_PROFILE
    geometry=sprites.SWING_GEOMETRY
    durations=profile['durations']
    active=profile['active_flags']
    assert len(durations)==len(active)==8
    assert all(isinstance(n,int) and n>0 for n in durations)
    assert 1<sum(durations)<256
    assert not active[0] and not active[-1] and any(active)
    assert geometry['durations']==durations and geometry['active_flags']==active
    age_phase=[phase for phase,length in enumerate(durations) for _ in range(length)]
    age_active=[int(active[phase]) for phase in age_phase]
    h.append('#define BLOOM_SWING_PHASES 8')
    h.append('#define BLOOM_SWING_FRAMES %d' % len(age_phase))
    h.append('#define BLOOM_SWING_ACTIVE_FIRST %d' % age_active.index(1))
    h.append('#define BLOOM_SWING_ACTIVE_LAST %d' % (len(age_active)-1-age_active[::-1].index(1)))
    for name,values in (('bloom_swing_age_phase',age_phase),('bloom_swing_age_active',age_active)):
        c.append(c_array_u8(name,values))
        h.append('extern const u8 %s[];' % name)
    study_origins=[v for facing in geometry['origins'] for phase in facing for v in phase]
    study_bounds=[v for facing in geometry['bounds'] for phase in facing for v in phase]
    assert len(study_origins)==64 and len(study_bounds)==128
    for name,values in (('bloom_swing_origin',study_origins),('bloom_swing_hit',study_bounds)):
        assert all(-128<=v<=127 for v in values),name
        c.append('const s8 %s[%d] ALIGN4 = { %s };' % (name,len(values),', '.join(map(str,values))))
        h.append('extern const s8 %s[];' % name)
    sword_study_metadata={**profile,'geometry':geometry,'age_phase':age_phase,
                          'age_active':age_active,'body_frame_base':101,'fx_frame_base':47}

# The supplied item frames select one of four material banks in the world.
# Paused inventory uses each original frame's own fifteen-colour ramp.
for sh in sprites.SHEETS:
    if 'frame_pal' in sh:
        name=sh['name']+'_frame_pal'
        values=[obj_slots[sh['frame_pal'][f]] for f in sh['frames']]
        c.append(c_array_u8(name,values))
        h.append('extern const u8 %s[];'%name)
    if sh['name']=='icon32':
        data=b'';cols=[]
        for frame in sh['frames']:
            rows,palette=sh['exact_frames'][frame]
            pix=parse_art(rows,32,32)
            for ty in range(0,32,8):
                for tx in range(0,32,8):data+=tile_bytes(pix,tx,ty)
            cols += [rgb15(v) for v in palette]
        c.append(c_array_u16('icon32_exact_tiles',bytes_to_u16(data)))
        c.append(c_array_u16('icon32_exact_pal',cols))
        h.append('extern const u16 icon32_exact_tiles[], icon32_exact_pal[];')
# The legacy orb and comparison wizard's staff flame share two resident inks.
import sw_folk  # noqa: E402
vals = []
if SC.VARIANT:
    flame_pulse=[('#c86820','#f0b848'),('#e07820','#f8d060'),
                 ('#f09028','#f8e888'),('#e87820','#f8d060'),
                 ('#c86820','#f0b848'),('#b85820','#e8a040')]
    for pair in flame_pulse:
        vals += [rgb15(color) for color in pair]
else:
    for pair in sw_folk.ORB_GLOW:
        vals += [rgb15('#%02x%02x%02x' % col) for col in pair]
c.append(c_array_u16('orb_glow', vals))
h.append('#define ORB_GLOW_STEPS %d' % (len(flame_pulse) if SC.VARIANT else len(sw_folk.ORB_GLOW)))
h.append('#define ORB_GLOW_INDEX %d /* reserved emissive pair */' % (13 if SC.VARIANT else (1 + [k for k, _ in sw_folk.GATEKEEPER_PAL].index('v'))))
assert [k for k, _ in sw_folk.GATEKEEPER_PAL].index('V') == [k for k, _ in sw_folk.GATEKEEPER_PAL].index('v') + 1
h.append('extern const u16 orb_glow[];')
h.append('#define WISP_X %d /* body-relative flame/wisp anchor */' % (23 if SC.VARIANT else sw_folk.WISP_AT[0]))
h.append('#define WISP_Y %d' % (1 if SC.VARIANT else sw_folk.WISP_AT[1]))
h.append('#define BART_SEWER_VARIANT %d' % SC.VARIANT)
h.append('#define BART_UI_VARIANT %d' % UI_STUDIES.VARIANT)
HUD_VARIANT = int(os.environ.get('BART_HUD', '0'))
assert HUD_VARIANT in (0, 1), 'BART_HUD must be0..1'
h.append('#define BART_HUD_VARIANT %d' % HUD_VARIANT)
h.append('#define BART_ENEMY_VARIANT %d' % sprites.ENEMY_VARIANT)
ENEMY_LAB = int(os.environ.get('BART_ENEMY_LAB', '0'))
assert ENEMY_LAB in (0, 1), 'BART_ENEMY_LAB must be0..1'
h.append('#define BART_ENEMY_LAB %d' % ENEMY_LAB)
h.append('#define BART_FOREST_VARIANT %d' % FOREST_CONCEPTS.VARIANT)
MENU_VARIANT = int(os.environ.get('BART_MENU', '0'))
assert 0 <= MENU_VARIANT <= 10, 'BART_MENU must be0..10'
h.append('#define BART_MENU_VARIANT %d' % MENU_VARIANT)
h.append('#define HUD_HEIGHT_PIXELS %d /* local pods; center stays open */' % (20 if HUD_VARIANT else 12))
# the Peddler's business: steps of (body frame, head frame, frames held),
# each act ended by a 0 hold
frame_of = {sh['name']: {f: i for i, f in enumerate(sh['frames'])} for sh in sprites.SHEETS}
vals, starts = [], []
for act in sw_folk.PEDDLER_ACTS:
    starts.append(len(vals))
    for (b, f, t) in act:
        vals += [frame_of['peddler_body'][b], frame_of['peddler_head'][f], t]
    vals += [0, 0, 0]
c.append('const u8 peddler_acts[%d] = { %s };' % (len(vals), ', '.join(str(v) for v in vals)))
c.append('const u16 peddler_act_at[%d] = { %s };' % (len(starts), ', '.join(str(v) for v in starts)))
h.append('#define PEDDLER_ACTS %d' % len(starts))
h.append('extern const u8 peddler_acts[];')
h.append('extern const u16 peddler_act_at[];')

# ----------------------------------------------------------------- hud --
# the UI's own face, set a pixel at a time (src/vwf.c): a width and nine
# rows of bits a glyph, bit x the pixel x
import ui_font  # noqa: E402
VWF_FIRST, VWF_LAST = 32, 128
widths, bits = [], []
for code in range(VWF_FIRST, VWF_LAST + 1):
    w, rows = ui_font.glyph(chr(code))
    widths.append(w)
    for r in rows:
        bits.append(sum(1 << x for x, ch in enumerate(r) if ch == '#'))
c.append('const u8 vwf_w[%d] = { %s };' % (len(widths), ', '.join(str(v) for v in widths)))
c.append('const u8 vwf_bits[%d] = { %s };' % (len(bits), ', '.join(str(v) for v in bits)))
h.append('#define VWF_FIRST %d' % VWF_FIRST)
h.append('#define VWF_COUNT %d' % len(widths))
h.append('#define VWF_HEIGHT %d' % ui_font.HEIGHT)
h.append('#define VWF_SPACE 3')
h.append('extern const u8 vwf_w[];')
h.append('extern const u8 vwf_bits[];')
h.append('#define CH_COIN "\\x7f"')
h.append('#define CH_HEART "\\x80"')

# the UI kit: frames, plates, tabs, slots (art/ui_kit.py), in its palette
import ui_kit  # noqa: E402
data = b''
for i, (name, rows) in enumerate(ui_kit.TILES.items()):
    pix = [[ui_kit.INDEX.get(ch, 0) for ch in r] for r in rows]
    data += tile_bytes(pix, 0, 0)
    h.append('#define UI_%s %d' % (cname(name), i))
c.append(c_array_u16('ui_tiles', bytes_to_u16(data)))
h.append('extern const u16 ui_tiles[];')
h.append('#define UI_TILE_COUNT %d' % len(ui_kit.TILES))
# Every runtime frame choice is authored at native8px size, not recolored
# screenshot art. The semantic role order is identical across the three kits.
appearance_data = b''
for kit in UI_STUDIES.appearance_kits(ui_kit.TILES, ui_kit.INDEX, ui_font):
    assert list(kit) == list(ui_kit.TILES)
    for rows in kit.values():
        appearance_data += tile_bytes([[ui_kit.INDEX.get(ch, 0) for ch in r] for r in rows], 0, 0)
c.append(c_array_u16('appearance_ui_tiles', bytes_to_u16(appearance_data)))
h.append('extern const u16 appearance_ui_tiles[];')
c.append(c_array_u16('appearance_palettes', [rgb15(color) for colors in UI_STUDIES.appearance_palette_colors() for color in colors]))
h.append('extern const u16 appearance_palettes[];')
h.append('#define APPEARANCE_STYLE_COUNT 3')
appearance_data = b''
for markers in UI_STUDIES.appearance_marks(ui_kit.OBJ_MARKS, ui_kit.INDEX, ui_font, ui_kit.TILES):
    for rows in markers.values():
        appearance_data += tile_bytes([[ui_kit.INDEX.get(ch, 0) for ch in r] for r in rows], 0, 0)
c.append(c_array_u16('appearance_mark_tiles', bytes_to_u16(appearance_data)))
h.append('extern const u16 appearance_mark_tiles[];')
h.append('#define APPEARANCE_MARK_COUNT %d' % len(ui_kit.OBJ_MARKS))
for nm, k in (('CREAM', 'c'), ('HIGH', 'h'), ('RED', 'r'), ('GOLD', 'G'), ('DIM', 's'), ('BROWN', 'b'),
              ('DARK', 'o'), ('DEEP', '1'), ('NAVY', '2'), ('RAISED', '3'), ('EDGE', '4'), ('PARCH', 'p'),
              ('GOLD_DARK', 'y'), ('GOLD_MID', 'Y'), ('PALE', 'W')):
    h.append('#define UI_INK_%s %d' % (nm, ui_kit.INDEX[k]))
# the sprites' copy of the kit's palette has the map's greens where the
# parchment and its ink are (ui_kit.OBJ_PAL), for the HUD's mini-map
h.append('#define OBJ_INK_GREEN %d' % ui_kit.INDEX['p'])
h.append('#define OBJ_INK_GREEN_LIT %d' % ui_kit.INDEX['b'])
# the pause map's colours, in its own palette (PAL_SLOT_MAP)
for nm, k in (('OUTLINE', 'o'), ('GROUND', 'n'), ('GRID', 'N'), ('DEEP', 'k'), ('GREEN', 'g'), ('LIT', 'G'),
              ('PALE', 'L'), ('WATER', 'w'), ('WATER_LIT', 'W'), ('BROWN', 'b'), ('BLIGHT', 'v'),
              ('BLIGHT_LIT', 'V'), ('UNKNOWN_EDGE', 'U'), ('GOLD', 'y'), ('CREAM', 'c')):
    h.append('#define MAP_INK_%s %d' % (nm, ui_kit.MAP_INDEX[k]))
h.append('')

# the HUD's hearts and R's hand, in a palette of their own (PAL_SLOT_HUD,
# ui_kit.HUD_PAL); the panels are the kit's, the figures the UI's face
data = b''
h.append('#define HUD_TILE_BASE 1 /* BG0: the blank, then these */')
for i, (name, rows) in enumerate(ui_kit.HUD_TILES.items()):
    data += tile_bytes([[ui_kit.HUD_INDEX[ch] for ch in r] for r in rows], 0, 0)
    h.append('#define HT_%s (HUD_TILE_BASE + %d)' % (cname(name), i))
c.append(c_array_u16('hud_tiles', bytes_to_u16(data)))
h.append('extern const u16 hud_tiles[];')
h.append('#define HUD_TILE_COUNT %d\n' % len(ui_kit.HUD_TILES))

# --------------------------------------------------------------- title --
title_bitmap = title.render_bitmap()
assert len(title_bitmap) == title.WIDTH * title.HEIGHT
c.append(c_array_u16('title_bitmap', title_bitmap))
h.append('#define TITLE_WIDTH %d' % title.WIDTH)
h.append('#define TITLE_HEIGHT %d' % title.HEIGHT)
h.append('#define TITLE_BITMAP_PIXELS %d' % len(title_bitmap))
h.append('#define TITLE_BITMAP_BYTES %d' % (len(title_bitmap) * 2))
h.append('extern const u16 title_bitmap[TITLE_BITMAP_PIXELS];\n')
title.write_metadata(os.path.join(OUT, 'title-import.json'), title_bitmap)
print('title: %dx%d RGB555 bitmap, %d colours' %
      (title.WIDTH, title.HEIGHT, len(set(title_bitmap))))

# --------------------------------------------------------------- rooms --
h.append('typedef struct { u8 w, h; const u16* ground; const u16* overlay; const u8* objects; u8 object_count; } RoomDef;')
rdefs = []
for r in rooms.ROOMS:
    w, hgt = r['w'], r['h']
    g = rooms.expand(r['ground'], w, hgt, mt_names)
    o = rooms.expand(r['overlay'], w, hgt, mt_names) if r.get('overlay') else None
    c.append(c_array_u16('room_%s_ground' % r['name'], g, w))
    if o:
        c.append(c_array_u16('room_%s_overlay' % r['name'], o, w))
    objs = []
    for ob in r.get('objects', []):
        objs += list(ob)
    if objs:
        c.append(c_array_u8('room_%s_objects' % r['name'], objs))
    rdefs.append((r['name'], w, hgt, bool(o), len(r.get('objects', []))))
    h.append('#define ROOM_%s %d' % (cname(r['name']), len(rdefs) - 1))
c.append('const RoomDef room_defs[%d] = {' % max(1, len(rdefs)))
for name, w, hgt, has_o, nobj in rdefs:
    c.append('    { %d, %d, room_%s_ground, %s, %s, %d },' % (
        w, hgt, name, ('room_%s_overlay' % name) if has_o else 'NULL',
        ('room_%s_objects' % name) if nobj else 'NULL', nobj))
if not rdefs:
    c.append('    { 0, 0, NULL, NULL, NULL, 0 },')
c.append('};')
h.append('extern const RoomDef room_defs[];')
h.append('#define ROOM_COUNT %d\n' % len(rdefs))

# ---------------------------------------------------------------- math --
import math  # noqa: E402
sin_q14 = [int(round(math.sin(i * 2 * math.pi / 256) * 16384)) & 0xFFFF for i in range(256)]
c.append(c_array_u16('sin_table_u', sin_q14))
h.append('extern const u16 sin_table_u[];\n#define sin_table ((const s16*)sin_table_u)')

h.append('#endif')
open(os.path.join(OUT, 'assets.c'), 'w').write('\n'.join(c) + '\n')
open(os.path.join(OUT, 'assets.h'), 'w').write('\n'.join(h) + '\n')
coverage = {
    'schema': 1,
    'method': 'Native generators; contract metadata supplies identifiers only, never old pixels.',
    'tiles': tiles.COVERAGE,
    'sprites': sprites.COVERAGE,
    'interface': [
        {'family': 'ui_kit', 'owner': 'reboot_ui', 'elements': list(ui_kit.TILES)},
        {'family': 'hud', 'owner': 'reboot_ui', 'elements': list(ui_kit.HUD_TILES)},
        {'family': 'font', 'owner': 'reboot_ui', 'elements': list(range(VWF_FIRST, VWF_LAST + 1))},
        {'family': 'portraits', 'owner': 'reboot_ui', 'elements': list(sprites.SHEETS[next(i for i, s in enumerate(sprites.SHEETS) if s['name'] == 'face')]['frames'])},
    ],
    'appearance_options': {
        'owner': 'ui_studies',
        'styles': [{'index': i, 'profile': style, 'name': UI_STUDIES.STYLE_NAMES[style],
                    'geometry': UI_STUDIES.geometry_recipe(style)} for i,style in enumerate((6,7,8))],
        'palette_profiles': [4,5,1],
        'palette_colors': UI_STUDIES.appearance_palette_colors(),
        'kit_canvas': [8,8], 'kit_tiles': len(ui_kit.TILES),
        'marker_canvas': [8,8], 'marker_frames': list(ui_kit.OBJ_MARKS),
        'selection': 'Independent native geometry and colors, persisted separately from the run.',
        'hud': 'Selected Winebound Folio in production UI6; appearance changes do not alter HUD/minimap banks.',
    },
    'title': title.metadata(title_bitmap),
    'sword_geometry': sword_geometry,
}
if sword_study_metadata:
    coverage['sword_study']=sword_study_metadata
if SC.VARIANT:
    coverage['sewer_concept']={
        'recipe':SC.RECIPE,
        'palette':dict(palettes.BG_PALETTES)['drain'],
        'peddler_palette':dict(palettes.OBJ_PALETTES)['peddler'],
        'wizard_palette':dict(palettes.OBJ_PALETTES)['gatekeeper'],
        'staff_flame_anchor':[23,1],
        'unchanged':('Room layout, per-cell physical metadata, glitter, Bloom and unrelated world art; final pictures use appended placement IDs.'
                     if SC.VARIANT == 9 else 'Room IDs, layout, physical metadata, glitter, Bloom and unrelated world art.'),
    }
    if SC.VARIANT == 9:
        import sewer_final_contracts as SFC
        coverage['sewer_final'] = {'room': SFC.ROOM, 'clone_count': len(SFC.CLONES),
            'clones': [{**clone, 'frames': len(tiles.METATILES[mt_names[clone['name']]].get('frames', [None])),
                        'anim_speed': tiles.METATILES[mt_names[clone['name']]].get('anim_speed', 8),
                        'glitter': bool(tiles.METATILES[mt_names[clone['name']]].get('glitter'))}
                       for clone in SFC.CLONES]}
coverage['ui_study'] = {'variant': UI_STUDIES.VARIANT,
                        'name': UI_STUDIES.STYLE_NAMES.get(UI_STUDIES.VARIANT, 'Compact baseline'),
                        'hud_fields': ['equipped items', 'hearts', 'gilt']}
coverage['hud_refresh'] = {
    'variant': HUD_VARIANT,
    'name': 'Gleaming gilt' if HUD_VARIANT else 'Historical compact HUD',
    'native_item_canvas': [16, 16],
    'item_art': 'Native HUD/menu/world family redraw' if HUD_VARIANT else 'Historical selected art',
    'map_grid_pixels': [20, 20] if HUD_VARIANT else [15, 15],
    'map_frame_pixels': [24, 24] if HUD_VARIANT else [16, 16],
    'fields': ['equipped items', 'A/B/L buttons', 'hearts', 'gilt', 'conditional ammunition', 'minimap'],
    'feedback': 'Physical A/B/L button illumination, current-room blink, local gold glints' if HUD_VARIANT else 'Static',
}
coverage['forest_concept'] = {
    'variant': FOREST_CONCEPTS.VARIANT,
    'name': FOREST_CONCEPTS.NAMES[FOREST_CONCEPTS.VARIANT],
    'status': ('Selected production repeated-tree integration.' if FOREST_CONCEPTS.TREE_WORLD
               else 'Historical optional environment comparison.'),
    'tile_owners': dict(tiles.FOREST_OWNERS),
    'obj_scope': 'Matching environment chests, entries and portable objects only; shared across areas in study ROMs.',
    'protected': ['Bloom', 'selected enemies', 'equipment and pickups', 'UI',
                  'Drain architecture and keepers', 'glitter', 'physical metadata'],
}
if FOREST_CONCEPTS.TREE_ROUND:
    coverage['tree_study'] = tree_study_metadata
if FOREST_CONCEPTS.VARIANT >= 6:
    coverage['forest_concept']['topology'] = tiles.FOREST_V2_TOPOLOGY
    coverage['forest_concept']['depth'] = {
        'semantic_room_arrays': 'Unchanged IDs for render-only canopy/water aliases.',
        'visual_arrays': ['gRoomVisualGround', 'gRoomVisualOverlay'],
        'foreground': 'Transparent canopy silhouettes/fringes and a two-cell raised root arch.',
        'underpass': 'Only the lower floor is a route; no accessible upper bridge level is invented.',
        'logs': 'Existing HLOG_0/1 solid two-cell kit replaces scattered one-cell logs after safety checks.',
        'landmarks': ['relic', 'shrine_available', 'shrine_spent', 'keylock'],
        'pulse_banks': list(forest_v2_pulses),
        'pulse_slots': forest_v2_pulse_slots,
        'pulse_clock': '(gFrame >> 3) & 3 while playing forest/mystery rooms',
    }
if FOREST_CONCEPTS.CANOPY_ROUND:
    coverage['forest_concept']['obj_scope'] = 'All environment OBJ and portraits retain forest profile6 artwork.'
    coverage['forest_concept']['canopy_round'] = {
        'base_forest_profile': 6,
        'local_style': FOREST_CONCEPTS.LOCAL_VARIANT,
        'scope': 'Healthy/infected crowns, tree anatomy and overhang art only.',
        'accepted_ground': 'Grey dead grass and all non-canopy pixels/palette roles retain profile6.',
        'living_green_target': 'Approximately20% across deep canopy masses, not a quota per tile.',
        'extra_bg_banks': list(forest_terrain.extra_palettes(FOREST_CONCEPTS.LOCAL_VARIANT)),
        'player_visibility': 'Conditional current-frame lower-body fragment; native body/tools/physics unchanged.',
        'extra_obj_tiles': 16,
        'native_body_visibility_rows': forest_v3_body_rows,
        'conservative_obj_union': {'used': 864, 'limit': 876},
        'generator': 'No layout, placement or lantern-generation change in this pass.',
    }
if FOREST_CONCEPTS.ADAPTIVE_ROUND and not FOREST_CONCEPTS.TREE_WORLD:
    coverage['forest_concept']['adaptive_canopy'] = adaptive_atlas_metadata
    coverage['forest_concept']['canopy_round']['scope'] = 'Retired fixed-block canopy; replaced by room-shaped native compositions.'
    coverage['forest_concept']['canopy_round']['generator'] = 'Logical maze and feature locations unchanged; room-first visual placement fits native compositions to actual canopy geometry. Lantern-generation change remains pending.'
    if FOREST_CONCEPTS.EMERALD_ROUND:
        coverage['forest_concept']['canopy_round']['scope'] = 'Leaf-first crowns and original local ground contact informed by the supplied Emerald reference; no flat canopy substrate.'
if FOREST_CONCEPTS.TREE_WORLD:
    coverage['forest_trees'] = tree_world_metadata
    coverage['forest_concept']['canopy_round']['scope'] = 'Approved compact repeated trees replace all legacy canopy/tree pictures.'
    coverage['forest_concept']['canopy_round']['generator'] = 'Logical maze preserved; deterministic root-row composition uses the generated room.'
if FOREST_CONCEPTS.COHESION_ROUND:
    coverage['forest_cohesion'] = {
        'status': 'Native forest composition and detail refinement, profile32.',
        'terrain_owner': 'forest_cohesion_terrain', 'prop_owner': 'forest_cohesion_props',
        'path_topology': tiles.FOREST_COHESION_TOPOLOGY,
        'region_scope': 'Forest tileset uses new native drawings; nonforest tilesets and global BG UI palette use isolated profile31 source.',
        'tree_source': 'Approved twelve forest_tree_study pictures, palette, anchors and alpha masks unchanged.',
        'generation': 'Room landform and protected routes precede contextual vegetation/debris/light placement.',
    }
with open(os.path.join(OUT, 'art-reboot-coverage.json'), 'w') as report:
    json.dump(coverage, report, indent=2)
    report.write('\n')
print('wrote', OUT)

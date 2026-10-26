"""Write the engine's art contract for an artist: what the game accepts and
lays, read from the art sources and from the built tables, not guessed.

    cd bartgame && make && python3 tools/engine_contract.py OUTDIR

OUTDIR/engine_asset_contract.json
    the platform and display facts; per area its tileset's pieces, palette
    slots and the palette groups in them (as built); every metatile with
    its id, areas, type, collision per 8x8 quarter, layer, frames and
    their time, palette group and slot, its four hardware 8x8 entries per
    area (piece, flips, bank, as in build/gen/assets.c), whether the game
    lays it and where its art comes from; every pack entry the importer
    reads (key, file, size, shape, frames, the metatiles it draws).
OUTDIR/key_migration.json
    every delivery key across the three tile specs (v1 the first, which
    the art pack V3 was drawn for; v2 the painted drafts, the 41-page
    PDF; v3 the current), with its file path, size and metatiles in each,
    and what the importer reads today.
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, os.path.join(ROOT, 'art'))
sys.path.insert(0, os.path.join(HERE, 'tile_spec'))

import tiles  # noqa: E402
import palettes  # noqa: E402
import rooms  # noqa: E402
import env_pack  # noqa: E402
import spec_data as V3  # noqa: E402

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
GEN = os.path.join(ROOT, 'build', 'gen')
REPO = os.path.join(ROOT, '..')


def git(*a):
    return subprocess.run(['git', '-C', REPO] + list(a), capture_output=True, text=True, check=True).stdout


# ------------------------------------------------------- the built tables
C = open(os.path.join(GEN, 'assets.c')).read()
H = open(os.path.join(GEN, 'assets.h')).read()


def c_array(name):
    m = re.search(r'const u16 %s\[(\d+)\][^{]*\{(.*?)\};' % re.escape(name), C, re.S)
    return [int(v, 0) for v in re.findall(r'0x[0-9a-fA-F]+|\d+', m.group(2))]


def h_define(name):
    return int(re.search(r'#define %s (\d+)' % name, H).group(1))


SETS = []
for m in re.finditer(r'\{ tileset_(\w+)_tiles, (\d+), metatile_map_\w+, tile_anims_\w+, (\d+), tileset_\w+_pals, (\d+) \}', C):
    SETS.append({'name': m.group(1), 'pieces': int(m.group(2)), 'animated_metatiles': int(m.group(3)), 'palettes': int(m.group(4))})
MAPS = {s['name']: c_array('metatile_map_%s' % s['name']) for s in SETS}
PALS = {s['name']: c_array('tileset_%s_pals' % s['name']) for s in SETS}


def bgr555_hex(v):
    r, g, b = v & 31, (v >> 5) & 31, (v >> 10) & 31
    return '#%02x%02x%02x' % ((r << 3) | (r >> 2), (g << 3) | (g >> 2), (b << 3) | (b >> 2))


BG = dict(palettes.BG_PALETTES)


def group_of_bank(set_name, bank):
    """the palette group whose colours sit in this area's bank"""
    vals = PALS[set_name][bank * 16:(bank + 1) * 16]
    for n, cols in BG.items():
        if [rgb15(x) for x in cols] == vals:
            return n
    return None


def rgb15(h):
    h = h.lstrip('#')
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return (r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10)


# -------------------------------------------------- what is laid, where from
v3_entries = [e for secs in (V3.WOOD, V3.MYST, V3.DRAIN) for _, _, es in secs for e in es]
LAYER = {}
SPEC_KEY = {}
for e in v3_entries:
    cols, rows = (e['shape'][1], e['shape'][2]) if e['shape'][0] == 'piece' else (len(e['mts']), 1)
    for i, n in enumerate(e['mts']):
        SPEC_KEY[n] = e['key']
        if e['layer'] == 'both':
            LAYER[n] = 'overlay' if i // cols < rows - 1 else 'ground'
        else:
            LAYER[n] = e['layer']
ALIAS = {'%s_floor_%s' % (st, k) for st in env_pack.STYLES for k in ('switch', 'lift', 'chest')}
ALIAS |= {'%s_crown' % st for st in env_pack.STYLES}
ALIAS |= {'%s_edge_%x' % (st, m) for st in env_pack.STYLES for m in range(1, 16)}
for n in ALIAS:
    LAYER[n] = 'ground'
PACK_TILE = {}
for k, (_, mts) in env_pack.ENTRIES.items():
    for i, n in enumerate(mts):
        PACK_TILE[n] = {'kind': 'pack', 'key': k, 'file': 'assets/' + env_pack.ASSETS[k]['path'], 'tile': i}
for n, (k, i) in env_pack.DERIVED.items():
    PACK_TILE[n] = {'kind': 'derived', 'key': k, 'file': 'assets/' + env_pack.ASSETS[k]['path'], 'tile': i}

names = [m['name'] for m in tiles.METATILES]
mt_names = {n: i for i, n in enumerate(names)}
hub = set()
for r in rooms.ROOMS:
    for layer in ('ground', 'overlay'):
        if r.get(layer):
            hub |= set(names[i] for i in rooms.expand(r[layer], r['w'], r['h'], mt_names) if i != 0xFFFF)
MYST_EXTRA = {'torch', 'torch_lit', 'boulder', 'chest', 'chest_open', 'sparkle', 'black', 'moss0', 'moss1', 'moss2'}


def areas_of(n):
    out = []
    if not n.startswith(('sw_', 'cave_', 'hollow_', 'thicket_', 'myst_')):
        out.append('forest')
    if n.startswith('sw_') or n in hub:
        out.append('sewer')
    if n.startswith(('cave_', 'hollow_', 'thicket_', 'myst_')) or n in MYST_EXTRA:
        out.append('myst')
    return out


QUARTERS = (('tl', 8), ('tr', 4), ('bl', 2), ('br', 1))
mts = []
for i, m in enumerate(tiles.METATILES):
    n = m['name']
    coll = m.get('coll', tiles.default_coll(m['type']))
    frames = len(m['frames']) if 'frames' in m else 1
    laid = n in SPEC_KEY or n in ALIAS or n == 'black'
    hw = {}
    for a in areas_of(n):
        ent = MAPS[a][i * 4:i * 4 + 4]
        hw[a] = [{'quarter': q, 'piece': e & 0x3FF, 'hflip': bool(e & 0x400), 'vflip': bool(e & 0x800), 'bank': e >> 12}
                 for (q, _), e in zip(QUARTERS, ent)]
    group = palettes.MERGE.get(m['pal'], m['pal'])
    mts.append({
        'id': i, 'name': n, 'areas': areas_of(n), 'type': m['type'],
        'collision_quarters': {q: bool(coll & b) for q, b in QUARTERS},
        'layer': LAYER.get(n, 'ground'), 'laid': laid, 'spec_v3_key': SPEC_KEY.get(n),
        'frames': frames, 'frame_duration_60ths': m.get('anim_speed') if frames > 1 else None,
        'palette_group': group,
        'palette_bank': {a: hw[a][0]['bank'] for a in hw},
        'hardware_8x8': hw,
        'art': PACK_TILE.get(n) or {'kind': 'spare', 'note': 'not laid: a plain pack tile so it costs no palette'},
    })

areas = {}
for s in SETS:
    banks = [group_of_bank(s['name'], b) for b in range(s['palettes'])]
    areas[s['name']] = {
        'pieces_used': s['pieces'], 'pieces_max': 1023, 'animated_metatiles': s['animated_metatiles'],
        'palette_slots_used': s['palettes'], 'palette_slots_max': h_define('PAL_AREA_SLOTS'),
        'banks': [{'bank': b, 'group': g, 'colors_bgr555': [bgr555_hex(v) for v in PALS[s['name']][b * 16:(b + 1) * 16]]}
                  for b, g in enumerate(banks)],
        'metatiles_held': sum(1 for m in mts if s['name'] in m['areas']),
        'metatiles_laid': sum(1 for m in mts if s['name'] in m['areas'] and m['laid']),
    }

contract = {
    'contract': 'BARTGAME engine asset contract',
    'engine_commit': git('rev-parse', '--short', 'HEAD').strip(),
    'platform': {
        'target': 'Game Boy Advance ROM (ARM7TDMI, Thumb code, built with arm-none-eabi gcc); runs in mGBA 0.10; not yet tried on hardware',
        'screen': [240, 160], 'refresh_hz': 59.73,
        'display_mode': 'mode 0, four tiled backgrounds, 4bpp (16-index banks, index 0 transparent), OBJ 1D mapping',
        'bg_layers': {
            'BG0': 'text, HUD, dialogue: priority 0, charblock 2, screenblock 23, 32x32 tiles',
            'BG1': "room overlay (tree crowns, sparkles, mist, the mystery rooms' pots, plates, chests, spring): priority 1, charblock 0, screenblock 24, 64x64 tiles",
            'BG2': 'room ground: priority 2, charblock 0, screenblock 28, 64x64 tiles',
            'BG3': "the pause menu's plank backdrop: priority 3, charblock 3, screenblock 22",
        },
        'sprites': ('OBJ priority 2 (above the ground, under the overlay); some effects priority 1 (above the overlay). '
                    'OBJ VRAM 1024 4bpp tiles: sheets and frames are streamed in per room, the last 16 tiles hold the mini-map. '
                    'Sprite palettes are separate from BG palettes.'),
        'bg_palettes': {'area_slots': [0, h_define('PAL_AREA_SLOTS') - 1], 'menu': h_define('PAL_SLOT_MENU'),
                        'gold_text': h_define('PAL_SLOT_GOLD'), 'text_and_hud': h_define('PAL_SLOT_TEXT')},
        'blending': 'none in rooms (BLDCNT 0); fades use brightness only',
        'colour': 'BGR555: each channel 5 bits; an 8-bit value v is stored as v >> 3, and read back as (c << 3) | (c >> 2)',
    },
    'tiles': {
        'metatile': '16x16 logical cell = four 8x8 hardware pieces, top-left, top-right, bottom-left, bottom-right',
        'palette_per_metatile': 'one bank for all four pieces of a metatile (the importer assigns one group per metatile; per-piece banks would be a small importer change)',
        'dedupe': 'identical 8x8 pieces are stored once, also when one is the other flipped horizontally, vertically or both; animated metatiles are not deduped',
        'animation': 'a metatile with N frames swaps all its four pieces every D/60 s (frame = (frame counter // D) % N); every copy in a room animates in step',
        'overlay': 'index 0 is transparent on BG1; ground tiles on BG2 must be opaque (index 0 shows the backdrop colour)',
        'collision': 'per 8x8 quarter of a metatile; types decide what a solid quarter does (wall, water, pit, thorn, lift...)',
    },
    'rooms': {
        'forest': 'generated, 32x24 metatiles (512x384 px), the camera scrolls; 25 rooms a run from a seed',
        'myst': 'generated, 12x9, 18x12 or 24x16 metatiles',
        'sewer': 'hand-laid hall, 30x18 metatiles (art/rooms.py)',
    },
    'importer': {
        'module': 'art/env_pack.py, run last in the art pipeline, in both builds',
        'reads': 'art/ref/pack_v3/manifest.json and art/ref/pack_v3/assets/<group>/<key>.png, keys of tile spec v1',
        'checks': ['every v1 key has exactly one asset and no asset is unknown (the build fails otherwise)',
                   'size = columns x 16 by rows x 16 x frames',
                   'every opaque pixel is exactly one of its group\'s 15 colours; no partial alpha',
                   'ground tiles fully opaque; transparency only in overlay entries and tree crown rows',
                   'one 16-colour palette per group across all its files'],
        'not_checked': 'resemblance to any reference image',
    },
    'areas': areas,
    'pack_entries': [{'key': k, 'file': 'assets/' + env_pack.ASSETS[k]['path'], 'group': env_pack.ASSETS[k]['group'],
                      'shape': list(sh), 'size': env_pack.ASSETS[k]['size'], 'frames': env_pack.ASSETS[k]['frame_count'],
                      'frame_duration_60ths': env_pack.ASSETS[k]['frame_duration_60ths'], 'metatiles': ms}
                     for k, (sh, ms) in env_pack.ENTRIES.items()],
    'metatiles': mts,
}
json.dump(contract, open(os.path.join(OUT, 'engine_asset_contract.json'), 'w'), indent=1)

# --------------------------------------------------------- the key migration
VERSIONS = [('v1', '4297bb8', 'the first tile spec; the art pack V3 was drawn for it'),
            ('v2', '0477e1d', 'the painted drafts; the 41-page PDF'),
            ('v3', 'HEAD', 'the current spec; what the game lays now')]
row_re = re.compile(r'\*\*(.+?)\*\*(?: \([a-z]+\))? \| `([a-z0-9_]+)/([a-z0-9_]+)\.png` (\d+)x(\d+)')


def spec_version(rev):
    """{key: entry} from the spec data and the doc of a revision"""
    src = git('show', '%s:bartgame/tools/tile_spec/spec_data.py' % rev)
    ns = {}
    exec(compile(src, 'spec_data_%s' % rev, 'exec'), ns)
    doc = git('show', '%s:docs/BARTGAME_TILE_SPEC.md' % rev)
    paths = {m.group(3): ('%s/%s.png' % (m.group(2), m.group(3)), [int(m.group(4)), int(m.group(5))]) for m in row_re.finditer(doc)}
    out = {}
    for secs in (ns['WOOD'], ns['MYST'], ns['DRAIN']):
        for _, _, es in secs:
            for e in es:
                p, size = paths.get(e['key'], (None, None))
                out[e['key']] = {'path': p, 'size': size, 'shape': list(e['shape']), 'frames': e['frames'],
                                 'layer': e['layer'], 'metatiles': e['mts']}
    return out


specs = {v: spec_version(rev) for v, rev, _ in VERSIONS}
keys = []
for v, _, _ in VERSIONS:
    for k in specs[v]:
        if k not in keys:
            keys.append(k)
rows = []
for k in keys:
    have = {v: specs[v].get(k) for v, _, _ in VERSIONS}
    note = []
    if have['v1'] and not have['v3']:
        note.append('retired in v3: the game no longer lays it' + ('' if k not in env_pack.ENTRIES else '; the importer still reads the v1 file'))
    if have['v2'] and not have['v1']:
        note.append('new in v2')
    if have['v3'] and not have['v1']:
        note.append('a v3 key the pack has no file for; its tiles are drawn from the v1 file that holds them')
    if have['v2'] and not have['v3'] and not have['v1']:
        note.append('v2 only: dropped in v3 (the art pack had none)')
    paths = {v: have[v]['path'] for v in have if have[v]}
    if len(set(paths.values())) > 1:
        note.append('path differs between versions')
    rows.append({'key': k, 'v1': have['v1'], 'v2': have['v2'], 'v3': have['v3'],
                 'importer_reads': ('assets/' + env_pack.ASSETS[k]['path']) if k in env_pack.ENTRIES else None,
                 'notes': note})
mig = {'versions': [{'version': v, 'commit': git('rev-parse', '--short', rev).strip(), 'what': w,
                     'entries': len(specs[v]), 'tiles': sum(len(e['metatiles']) for e in specs[v].values())} for v, rev, w in VERSIONS],
       'keys': rows}
json.dump(mig, open(os.path.join(OUT, 'key_migration.json'), 'w'), indent=1)
print('contract: %d metatiles, %d pack entries; areas %s' % (len(mts), len(env_pack.ENTRIES),
      {a: (v['pieces_used'], v['palette_slots_used']) for a, v in areas.items()}))
print('migration: %s, %d keys' % ([(m['version'], m['entries'], m['tiles']) for m in mig['versions']], len(rows)))

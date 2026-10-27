"""BARTGAME palettes. 16 colors each; index 0 is transparent for sprites
and the backdrop color for BG palette 0.

The look, from the concept boards: grime and glamour. Deep saturated
greens, teal water that glows, amber lantern light, warm grey-brown
stone, violet blight with magenta cracks, gold frames. Every material
has a dark hue outline, three or four body tones and a gleam. Values
are multiples of 8 so they survive the GBA's 5-bit channels.
"""

GRASS_MID = '#3a6a2c'

import ui_kit as _uk  # noqa: E402
OLD_BG_PALETTES = [
    # 0 forest ground: dark olive grass with bright tips, warm soil, flowers, blight, a gold mote
    ('forest', ['#000000',
                '#060a10',   # 1 outline, deep shadow
                '#14301c',   # 2 grass deep
                '#20482a',   # 3 grass dark
                GRASS_MID,   # 4 grass mid
                '#5c9c3a',   # 5 grass light
                '#a4dc4c',   # 6 grass bright
                '#4e3c20',   # 7 path dark
                '#86703c',   # 8 path mid
                '#b49c58',   # 9 path light
                '#4aa0ff',   # A flower blue
                '#ff78c8',   # B flower pink
                '#fff6dc',   # C cream, white petals, bone, stars
                '#6a28b8',   # D blight violet
                '#d05cff',   # E blight magenta
                '#ffe878']), # F gold mote
    # 1 wood: canopy blue-black to lit green, bark, lantern amber
    ('wood', ['#000000',
              '#04080c',     # 1 outline
              '#0a1a1c',     # 2 leaf deepest
              '#103428',     # 3 leaf dark
              '#1a5438',     # 4 leaf mid
              '#2e864c',     # 5 leaf light
              '#60c060',     # 6 leaf bright
              '#2a1a10',     # 7 bark dark
              '#4e3420',     # 8 bark mid
              '#7c5430',     # 9 bark light
              '#ac7c48',     # A bark highlight
              '#c05818',     # B lantern amber dark
              '#ffb038',     # C lantern amber
              '#fff6c0',     # D lantern bright
              GRASS_MID,     # E grass showing through
              '#d05cff']),   # F thorn magenta
    # 2 stone: ruins, water, gates, chests, torches, statues
    ('stone', ['#000000',
               '#0a1018',    # 1 outline
               '#1a2030',    # 2 stone deep
               '#303848',    # 3 stone dark
               '#565e70',    # 4 stone mid
               '#848c9c',    # 5 stone light
               '#b8c0cc',    # 6 stone bright
               '#081a48',    # 7 water deep
               '#103478',    # 8 water mid
               '#1c6cc0',    # 9 water light
               '#a8f4ff',    # A water foam
               '#8a5c18',    # B gold dark, wood shadow
               '#e8b838',    # C gold mid
               '#fff4b0',    # D gold bright, flame
               GRASS_MID,    # E moss, grass showing through
               '#a06838']),  # F wood
    # 3 blight: the deep rooms, purple ground that glows, crystals, dead trees
    ('blight', ['#000000',
                '#0c0414',   # 1 outline
                '#200c38',   # 2 blight deepest
                '#381458',   # 3 blight deep
                '#6020a8',   # 4 blight mid
                '#9a3ce8',   # 5 blight light
                '#d868ff',   # 6 magenta glow
                '#ffb4ff',   # 7 pink bright
                '#140c14',   # 8 dead bark dark
                '#30202c',   # 9 dead bark
                '#56404c',   # A dead bark light
                '#c8a0ff',   # B crystal light
                '#1e4028',   # C grass dark
                GRASS_MID,   # D grass mid
                '#ffe878',   # E gold mote
                '#ffffff']), # F white
    # 4 sewer: wet stone, moss, teal water, rust, candlelight
    ('sewer', ['#000000',
               '#0a0c12',    # 1 outline
               '#1c2028',    # 2 stone deepest
               '#343842',    # 3 stone dark
               '#555a64',    # 4 stone mid
               '#808690',    # 5 stone light
               '#b0b6bc',    # 6 stone bright
               '#2a6a30',    # 7 moss dark
               '#58a848',    # 8 moss light
               '#0c3a3c',    # 9 water deep teal
               '#188878',    # A water teal
               '#30c8b0',    # B water light teal
               '#b8f8f0',    # C water foam
               '#a05828',    # D rust, copper
               '#ffb040',    # E candle amber
               '#fff0a0']),  # F candle bright, gold
    # 5 sewer props: barrels, crates, bone, banners, awnings, the rug; 5 and F
    #   are the floor's stone tones so props sit on flagstones
    ('props', ['#000000',
               '#0a0c12',    # 1 outline
               '#3a2410',    # 2 wood dark
               '#6a4420',    # 3 wood mid
               '#a07040',    # 4 wood light
               '#555a64',    # 5 stone mid (the floor it stands on)
               '#e8e0c8',    # 6 bone
               '#a09880',    # 7 bone shadow
               '#146860',    # 8 banner teal dark
               '#28a898',    # 9 banner teal
               '#80201c',    # A red dark
               '#c83830',    # B red
               '#e8b838',    # C gold
               '#4c1c78',    # D rug violet dark
               '#8838c8',    # E rug violet
               '#808690']),  # F stone light (the floor's lit edges)
    # 6 the HUD's hearts and R's hand on the panels' navy (ui_kit.HUD_PAL),
    #   the rest unused
    ('hud', (['#000000'] + ['#%02x%02x%02x' % c for _, c in _uk.HUD_PAL] + ['#000000'] * 15)[:16]),
    # 7 cliff: rocks and ledges sunk in moss and soil
    ('cliff', ['#000000',
               '#0a1018',    # 1 outline
               '#1c2432',    # 2 stone deep
               '#34404e',    # 3 stone dark
               '#5a6878',    # 4 stone mid
               '#8a98a4',    # 5 stone light
               '#c0ccd4',    # 6 stone bright
               '#1c3a1c',    # 7 moss dark
               '#3a7a30',    # 8 moss mid
               '#7cc048',    # 9 moss light
               '#3a2a16',    # A soil dark
               '#6e5634',    # B soil
               '#fff6dc',    # C cream
               '#8a3cd8',    # D lichen violet
               GRASS_MID,    # E grass mid
               '#a4dc4c']),  # F grass bright
    # 8 menu: the UI kit's navy, gold and inks (ui_kit.py), the boxes,
    # the shop and the pause pages
    ('menu', ['#000000'] + ['#%02x%02x%02x' % c for _, c in _uk.PAL]),
    # 9 map: the pause map's ground, ways and water (ui_kit.MAP_PAL)
    ('map', ['#000000'] + ['#%02x%02x%02x' % c for _, c in _uk.MAP_PAL]),
]

OLD_OBJ_PALETTES = [
    # 0 hero: petals, a cream face, hood greens, leather, steel, gold
    ('hero', ['#000000',
              '#1a0c10',     # 1 outline
              '#b02818',     # 2 petal deep
              '#f04828',     # 3 petal red
              '#ff8030',     # 4 petal orange
              '#ffb048',     # 5 petal light tip
              '#fff8e8',     # 6 face cream
              '#e8c8a0',     # 7 face shadow
              '#1c4a28',     # 8 tunic deep
              '#2e8040',     # 9 tunic green
              '#58b858',     # A tunic light
              '#5a3418',     # B leather dark
              '#9a6030',     # C leather light
              '#b8c8d8',     # D steel
              '#f8fcff',     # E steel gleam
              '#f8d050']),   # F gold
    # 1 effects and pickups: sparks, hearts, gilt, keys, seeds
    ('fx', ['#000000',
            '#180c18',       # 1 outline
            '#901020',       # 2 red dark
            '#e83040',       # 3 red
            '#ff8080',       # 4 red bright
            '#885818',       # 5 gold dark
            '#e0b030',       # 6 gold mid
            '#fff0a0',       # 7 gold bright
            '#ffffff',       # 8 white
            '#4a2888',       # 9 violet dark
            '#8a60d8',       # A violet
            '#c8b0ff',       # B violet light
            '#383848',       # C grey dark
            '#7a7a90',       # D grey
            '#c0c0d0',       # E grey light
            '#58c8ff']),     # F blue glow
    # 2 bugs: beetle, bat, slime (violet chitin, chartreuse eyes, teal jelly)
    ('bugs', ['#000000',
              '#100818',     # 1 outline
              '#2a1840',     # 2 chitin deep
              '#482870',     # 3 chitin dark
              '#7040a8',     # 4 chitin mid
              '#a070d8',     # 5 chitin light
              '#d8b0ff',     # 6 chitin gleam
              '#88a020',     # 7 eye dark
              '#d0f040',     # 8 eye bright
              '#f8ffc0',     # 9 eye glow
              '#801828',     # A red dark
              '#e03048',     # B red
              '#186860',     # C jelly deep
              '#30b0a0',     # D jelly
              '#80f0d8',     # E jelly light
              '#e8e8f0']),   # F bone white
    # 3 blight: spitter, boss (sick greens, raw flesh, violet, bone)
    ('blight', ['#000000',
                '#141408',   # 1 outline
                '#304010',   # 2 sick deep
                '#507020',   # 3 sick dark
                '#80a830',   # 4 sick mid
                '#b8d848',   # 5 sick light
                '#e8f888',   # 6 sick bright
                '#500818',   # 7 flesh deep
                '#901030',   # 8 flesh dark
                '#d82850',   # 9 flesh
                '#ff6080',   # A flesh light
                '#ffb0c0',   # B flesh pale
                '#401058',   # C violet dark
                '#9038c0',   # D violet
                '#f0e0c0',   # E bone pale
                '#ffffff']), # F white
    # 4 iron: thorn knights and their swords (chrome plate, crimson, gold)
    ('iron', ['#000000',
              '#101420',     # 1 outline
              '#283048',     # 2 steel deep
              '#4a5878',     # 3 steel dark
              '#8090b0',     # 4 steel mid
              '#c0d0e8',     # 5 steel light
              '#f0f8ff',     # 6 steel gleam
              '#601020',     # 7 crimson dark
              '#c02038',     # 8 crimson
              '#301848',     # 9 violet dark
              '#6838a0',     # A violet
              '#f0c8a0',     # B skin
              '#b08060',     # C skin shadow
              '#906018',     # D gold dark
              '#f8d050',     # E gold
              '#ff4040']),   # F eye glow
    # 5 folk: the Peddler's purple hide and red hood, the Gatekeeper's hat
    ('folk', ['#000000',
              '#100c14',     # 1 outline
              '#5a3878',     # 2 purple hide dark
              '#8a60b0',     # 3 purple hide
              '#c8a888',     # 4 pale skin shadow
              '#f0dcc0',     # 5 pale skin
              '#801c1c',     # 6 red dark
              '#d03030',     # 7 red
              '#3c1c68',     # 8 violet dark
              '#6c38b0',     # 9 violet
              '#a068e0',     # A violet light
              '#f0c040',     # B gold
              '#906018',     # C gold dark
              '#f0f0f8',     # D white, silver
              '#7a4a24',     # E brown
              '#48a050']),   # F green
    # 6 portraits: faces for the dialogue box
    ('portrait', ['#000000',
                  '#100c14', # 1 outline
                  '#b02818', # 2 petal deep
                  '#f04828', # 3 petal red
                  '#ff8030', # 4 petal orange
                  '#fff8e8', # 5 face cream
                  '#e8c8a0', # 6 face shadow
                  '#2e8040', # 7 green
                  '#8a60b0', # 8 purple hide
                  '#5a3878', # 9 purple hide dark
                  '#d03030', # A red
                  '#801c1c', # B red dark
                  '#6c38b0', # C violet
                  '#b0a0d0', # D lavender, steel
                  '#f0c040', # E gold
                  '#ffffff']), # F white
    # 7 lift: bushes, stones and pots carried over the head
    ('lift', ['#000000',
              '#081410',     # 1 outline
              '#145838',     # 2 leaf deep
              '#1e8048',     # 3 leaf mid
              '#3aa858',     # 4 leaf light
              '#78d070',     # 5 leaf bright
              '#d060f0',     # 6 berry
              '#2c3040',     # 7 stone deep
              '#4c5060',     # 8 stone dark
              '#787c88',     # 9 stone mid
              '#aab0b8',     # A stone light
              '#3a2410',     # B clay dark
              '#6a4420',     # C clay mid
              '#a07040',     # D clay light
              '#e0e4e8',     # E gleam
              '#f8d050']),   # F gold
    # 8 ui sprites: the mini-map
    ('ui', ['#000000',
            '#161020',       # 1 dark
            '#e8d8a8',       # 2 parchment
            '#b8a070',       # 3 parchment dark
            '#8a5c18',       # 4 gold dark
            '#e8b838',       # 5 gold
            '#fff4b0',       # 6 gold bright
            '#2a6a30',       # 7 green dark
            '#58a048',       # 8 green
            '#f03030',       # 9 red dot
            '#ffffff',       # A white
            '#38a0ff',       # B blue
            '#8890a0',       # C grey
            '#3a3a48',       # D slate
            '#ff80c0',       # E pink
            '#ffe070']),     # F gold mote
]


# ------------------------------------------------- the boards' palettes --
# The forest, the water and its cliffs, the blight, the drain and its
# props, the Bloom, the folk and the faces take their colours from the
# style boards (style.py); the rest keep their hand palettes. Hand-drawn
# art in a replaced palette is remapped at build time, old index to the
# nearest new colour (REMAP_BG).
import style as _st


def _hexes(pal):
    return ['#%02x%02x%02x' % c for c in pal]


_BOARD_BG = {
    'forest': ['#000000'] + _hexes(_st.PAL_FOREST),
    'wood': ['#000000'] + _hexes(_st.PAL_FOREST),
    'stone': ['#000000'] + _hexes(_st.PAL_CLIFF),
    'cliff': ['#000000'] + _hexes(_st.PAL_CLIFF),
    'blight': ['#000000'] + _hexes(_st.PAL_BLIGHT),
    'sewer': ['#000000'] + _hexes(_st.PAL_SEWER),
    'props': ['#000000'] + _hexes(_st.PAL_PROPS),
}
BG_PALETTES = [(n, _BOARD_BG.get(n, cols)) for n, cols in OLD_BG_PALETTES]
# The OBJ palettes are the sprite pack's groups (art/pack/pack.json): the
# slots the engine has always used, then the groups drawn from the
# illustrated sheets (the sword and shields, the small items, the
# pickups, the icons), then the Drain's two keepers, drawn by hand in a
# palette each (sw_folk.py; the pack's own pair, folk32, is no longer
# drawn). The portrait slot is reloaded with each speaker's palette
# (FACE_PALETTES).
import pack as _pk  # noqa: E402
import sw_folk as _sf  # noqa: E402
_OBJ_ORDER = ['hero', 'fx', 'bugs', 'blight', 'iron', 'folk', 'portrait', 'lift', 'ui',
              'gear', 'items', 'pick', 'icons']
OBJ_PALETTES = [(n, _pk.GROUPS[n]) for n in _OBJ_ORDER]
assert set(_pk.GROUPS) - {'folk32'} == set(_OBJ_ORDER), set(_pk.GROUPS) ^ set(_OBJ_ORDER)
OBJ_PALETTES += [(n, ['#000000'] + ['#%02x%02x%02x' % c for _, c in pal])
                 for n, pal in (('peddler', _sf.PEDDLER_PAL), ('gatekeeper', _sf.GATEKEEPER_PAL),
                                ('uikit', _uk.OBJ_PAL))]
# the dialogue box's faces (faces.py), each its own palette, in the face
# sheet's order
import faces as _fc  # noqa: E402
FACE_PALETTES = [['#000000'] + ['#%02x%02x%02x' % c for _, c in _p] for _n, _p, _r in _fc.FACES]


def _rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def _remap(old, new):
    """index 1..15 of the old palette to the nearest of the new; 0 stays"""
    m = {0: 0}
    for i in range(1, 16):
        o = _rgb(old[i]) if i < len(old) else (0, 0, 0)
        best, bd = 1, 1 << 30
        for j in range(1, 16):
            if j >= len(new):
                break
            d = sum((o[k] - _rgb(new[j])[k]) ** 2 for k in range(3))
            if d < bd:
                bd = d
                best = j
        m[i] = best
    return m


REMAP_BG = {n: _remap(dict(OLD_BG_PALETTES)[n], _BOARD_BG[n]) for n in _BOARD_BG}


def remap_rows(rows, m):
    return [''.join('.' if ch in '. ' else '%x' % m[int(ch, 16)] for ch in r) for r in rows]


# The comparison build (BART_TILES=pack, `make pack-tiles`) takes the area
# palettes from the pack's own tile sheets; PACK_REMAP carries the board
# colours of the tiles the pack does not cover onto them (pack_tiles.py).
import os as _os  # noqa: E402
PACK_TILES = _os.environ.get('BART_TILES') == 'pack'
BOARD_BG_PALETTES = BG_PALETTES
PACK_REMAP = {}
if PACK_TILES:
    _pt = {n: ['#000000'] + _pk.META['tiles'][n]['palette']
           for n in ('forest', 'wood', 'stone', 'cliff', 'blight', 'sewer', 'props')}
    BG_PALETTES = [(n, _pt.get(n, cols)) for n, cols in BOARD_BG_PALETTES]
    PACK_REMAP = {n: _remap(dict(BOARD_BG_PALETTES)[n], _pt[n]) for n in _pt}

# The illustrated tile atlases (art/tile_art.py) bring palette groups of
# their own, which take the place of the board palettes they replace;
# TILE_ART_FROM keeps those, for the tiles still drawn in them.
import tile_art as _ta  # noqa: E402
TILE_ART_FROM = dict(BG_PALETTES)
BG_PALETTES = [(n, c) for n, c in BG_PALETTES if n not in _ta.RETIRE] + sorted(_ta.GROUPS.items())
# the living wood, the blight's floors and the mystery rooms drawn here
# (wood_art.py), in palettes of their own
import wood_art as _wa  # noqa: E402
BG_PALETTES += [(n, _wa.group(n)) for n in _wa.group_names()]
# the environment art pack, V3 (env_pack.py): its twelve groups as delivered
import env_pack as _ep  # noqa: E402
BG_PALETTES += sorted(_ep.GROUPS.items())
# A palette with the very colours of one before it shares that one's slot:
# the boards gave the wood the forest's colours and the cliffs the stone's.
# The metatiles drawn in it are moved over by tile_art.apply().
MERGE = {}
for _i, (_n, _c) in enumerate(BG_PALETTES):
    for _m, _d in BG_PALETTES[:_i]:
        if _d == _c and _m not in MERGE:
            MERGE[_n] = _m
            break
BG_PALETTES = [(n, c) for n, c in BG_PALETTES if n not in MERGE]
# the Drain's hall: palettes packed from its painting (sw_drain.py)
import sw_drain as _sd  # noqa: E402
BG_PALETTES += _sd.PALETTES

# Forest-only art groups. They are loaded only in the forest/interior sets.
import forest_art as _forest
BG_PALETTES += sorted(_forest.GROUPS.items())
import forest_sprites as _enemies
OBJ_PALETTES = [(n, _enemies.PALETTES.get(n, c)) for n, c in OBJ_PALETTES]

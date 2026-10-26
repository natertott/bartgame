"""Write the tile spec as a page (HTML, images inline) and as a doc
(Markdown, images beside it), from spec_data and the renders.

    cd bartgame && python3 tools/tile_spec/render.py IMGDIR
    python3 tools/tile_spec/gen.py IMGDIR CTXDIR PAGE.html ../docs/BARTGAME_TILE_SPEC.md ../docs/tile_spec

CTXDIR holds the room views named in CTX_IMAGES (in-game shots from
tools/roomshots.py, the Drain from tools/preview.py room sewer_main).
"""
import base64
import html
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spec_data as D  # noqa: E402

# what has been delivered: an entry whose every tile the tile atlases
# drew (art/tile_art/tiles.json), in the group it was imported in
import json  # noqa: E402
TILE_ART = json.load(open(os.path.join(HERE, '..', '..', 'art', 'tile_art', 'tiles.json')))['tiles']
for _secs in (D.WOOD, D.MYST, D.DRAIN):
    for _t, _i, _es in _secs:
        for _e in _es:
            _e['done'] = all(m in TILE_ART for m in _e['mts'])
            if _e['done']:
                _e['group'] = TILE_ART[_e['mts'][0]]['pal']

IMG, CTX, PAGE, DOC, DOCIMG = sys.argv[1:6]
os.makedirs(DOCIMG, exist_ok=True)
AREAS = [('wood', 'The wood', D.WOOD), ('myst', 'The mystery rooms', D.MYST), ('drain', 'The Drain', D.DRAIN)]
AREA_NOTE = {
    'wood': 'Rooms are 32x24 tiles, laid out by the game, so any tile can meet any of its listed neighbours. The wood has three moods: the living rooms (green), the sick rooms (stained grass, the canopy going violet) and the blighted rooms (purple to the walls), with the arena of the Blight Heart deepest of all. The edge tiles are used in the living rooms only.',
    'myst': 'Small rooms behind the mouths in the wood\'s walls, one of three styles. They share the wood\'s censers, boulders, gold sparkle and grass.',
    'drain': 'One hand-laid hall, 30x18 tiles, the hub under the wood: the Peddler\'s stall, the Gatekeeper\'s rug, a channel of water with a grate across it, the great drain, two pools in the lower corners, a waterfall pouring from the back wall beside the hole up to the wood.',
}
CTX_IMAGES = {
    'wood': [('wood_living', 'A living room'), ('wood_sick', 'A sick room'), ('wood_blighted', 'A blighted room'), ('wood_arena', 'The arena')],
    'myst': [('myst_cave', 'Cave'), ('myst_hollow', 'Hollow'), ('myst_thicket', 'Thicket')],
    'drain': [('drain_hall_raw', 'The whole hall'), ('drain_screen', 'One screen of it')],
}
LAYER = {'ground': 'ground', 'overlay': 'overlay (over the sprites)', 'both': 'crown on the overlay, trunk on the ground'}
GROUP_AREA = {g: a for a, g, _ in D.GROUPS}


def tiles_in(e):
    sh = e['shape']
    return {'one': 1, 'vars': sh[1] if len(sh) > 1 else 1, 'piece': (sh[1] * sh[2]) if len(sh) > 2 else 1, 'fam': 15}[sh[0]]


def cols_rows(e):
    sh = e['shape']
    if sh[0] == 'piece':
        return sh[1], sh[2]
    return tiles_in(e), 1


def size_text(e):
    sh = e['shape']
    if sh[0] == 'one':
        return '16x16'
    if sh[0] == 'vars':
        return '%d tiles, 16x16 each' % sh[1]
    if sh[0] == 'fam':
        return '15 tiles, 16x16 each'
    return '%dx%d (%d by %d tiles)' % (sh[1] * 16, sh[2] * 16, sh[1], sh[2])


def file_text(e):
    c, r = cols_rows(e)
    return '%dx%d' % (c * 16, r * 16 * e['frames'])


def frames_text(e):
    if e['frames'] <= 1:
        return 'still'
    return '%d frames, each shown %d/60 s' % (e['frames'], e['rate'])


def order_text(e):
    sh = e['shape']
    if sh[0] == 'fam':
        labels = D.SIDE if sh[1] == 'side' else D.CORNER
        return ', '.join(labels)
    return ''


def data_uri(path):
    return 'data:image/png;base64,' + base64.b64encode(open(path, 'rb').read()).decode()


def esc(s):
    return html.escape(s, quote=True)


def area_tiles(secs):
    return sum(tiles_in(e) for _, _, es in secs for e in es)


COUNTS = {a: area_tiles(s) for a, _, s in AREAS}
DONE_ENTRIES = sum(1 for _, _, s in AREAS for _, _, es in s for e in es if e['done'])
DONE_TILES = sum(tiles_in(e) for _, _, s in AREAS for _, _, es in s for e in es if e['done'])
TOTAL_ENTRIES = sum(len(es) for _, _, s in AREAS for _, _, es in s)
TOTAL_TILES = sum(COUNTS.values())

# ------------------------------------------------------------- shared prose
INTRO = ('Every background tile the game draws in the wood, its mystery rooms and the Drain: what each one is, where it goes, '
         'what it must join, and how to deliver it. Written so an artist or an art-generating model can redraw the set without '
         'reading the code. The pictures show the tiles in the game now. Use them for size, layout and joins, not for style.')
STATUS = ('The Drain and the blight of the wood are delivered: the entries marked delivered show their new art as the game draws it. '
          'Still to draw: the living wood (its ground, edges, water, canopy, trees, things on the grass, cliffs and gates) '
          'and the mystery rooms.')

SCREEN = [
    ('Tiles.', 'The world is built of 16x16 tiles. The screen shows 15 by 10 of them (240x160 pixels). The Bloom is 31 pixels tall, about two tiles; most monsters are one tile.'),
    ('View.', 'Top-down with a three-quarter tilt, as in The Minish Cap. Floors are seen from above. Walls, trunks, rocks and props show their front face. Light comes from the upper left; shadows fall down and to the right.'),
    ('Two layers.', 'Ground tiles are drawn under the sprites and must be opaque in every pixel. Overlay tiles are drawn over the sprites, so the Bloom walks behind a tree\'s crown; they are transparent outside the drawing.'),
    ('Solid.', 'Collision is decided per 8x8 quarter. "Solid" blocks the whole tile. "Bottom half" blocks only the lower 8 rows, so the Bloom can stand behind the top half. "Top half" is the reverse.'),
    ('Joins.', 'Most tiles repeat. "Tiles in every direction" means any arrangement of copies must read as one surface, with no seam at the 16-pixel grid and no feature that repeats visibly. Tiles listed together as variants must also tile with each other.'),
    ('Animation.', 'Frames play in a loop. "Each shown 20/60 s" means a frame holds for 20 of the game\'s 60 frames a second. Every copy of a tile animates in step.'),
]

RULES = [
    ('Colour.', '4 bits a pixel: each palette group has 15 colours plus transparent. All 256 pixels of one tile come from one group. Where a tile shows two materials (a shore with grass and sand, a trunk with grass and bark), both must be in its group.'),
    ('Palette budget.', 'The game has 14 background palettes for tiles and the HUD; the HUD and the pause menu keep 2 and the text 2 more of the 16. The delivered Drain uses 3, the blight 4 and the glints 1, so the living wood and the mystery rooms have 4 between them: the four wood groups below, the mystery rooms drawn in their colours. If that is too few, say so: the game can load palettes per area, which would give each area its own.'),
    ('Piece budget.', 'Each area holds at most 1,023 distinct 8x8 pieces. A 16x16 tile is four pieces; a piece repeated exactly, or mirrored, is stored once. This list is %d tiles for the wood (%d pieces), %d for the mystery rooms and %d for the Drain, so there is room for some reuse but not for many more variants. Animation frames beyond the first do not count.' % (COUNTS['wood'], COUNTS['wood'] * 4, COUNTS['myst'], COUNTS['drain'])),
    ('Pixels.', 'Exact sizes. No anti-aliasing, no partial transparency, no gradients finer than the palette. Every pixel is a palette colour or fully transparent.'),
    ('Style.', 'After the four BARTGAME style boards: "grime and glamour". Three tones per material plus a highlight; a dark outline on objects that stand up from the ground (rocks, props, trunks), none on flat ground textures. Detail should be rich but quiet: the ground is a backdrop for the sprites, so keep its contrast lower than theirs, and keep bright specks for things the player should notice.'),
]

DELIVERY = [
    'One PNG per entry, named with the entry\'s key (for example <code>grass.png</code>), in a folder named for its palette group (for example <code>wood_ground/grass.png</code>).',
    'Variants and families: the tiles side by side in the order listed, no gaps. A family of fifteen is 240 pixels wide.',
    'Pieces bigger than a tile: the whole picture at its full size, which the importer cuts into tiles.',
    'Animation: each frame is a further row below the first, the same layout again. The file size given on each entry includes the frames.',
    'Transparency: overlay entries, and the crown rows of a tree, use a real alpha channel or pure magenta <code>#FF00FF</code> for transparent. Ground entries have none.',
    'Optional and welcome: one mock-up screen per area (240x160) laid from the delivered tiles, so the joins can be checked together.',
]

CHECK = [
    'Every entry present, named by its key, in its group\'s folder, at the file size given.',
    'At most 15 colours per palette group, and no more groups per area than the budget.',
    'Ground tiles opaque in every pixel; overlay tiles transparent outside the drawing.',
    'Every repeating tile tested in a 4x4 block of itself, and every variant set in a random mix.',
    'Every edge family checked against its neighbours: a shore against water banks, a verge against the canopy, a trail edge against grass.',
    'Animation frames that differ only where they should, and loop without a jump.',
    'Lifted things (the bush, the small stone, the boulder, the pots) matching their carried sprites.',
]


# -------------------------------------------------------------------- page
def page():
    out = []
    w = out.append
    w('<title>BARTGAME Tile Spec</title>')
    w('<meta name="claude:viewport-fit-sides" content="cover">')
    w('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Nunito+Sans:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap">')
    w('''<style>
/* layout: one reading column with a sticky section index on wide screens; each tile entry is a picture beside its facts */
:root {
  --bg: #f3efe6; --surface: #faf8f2; --fg: #221c1a; --muted: #6b5f58; --line: #d9d0c2;
  --accent: #8a5c18; --accent-ink: #5a3a0c; --pic: #2a2530;
  --display: "Fraunces", Georgia, serif; --body: "Nunito Sans", "Segoe UI", system-ui, sans-serif; --mono: "JetBrains Mono", Menlo, Consolas, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg: #16131a; --surface: #1f1b24; --fg: #ebe4d8; --muted: #a79c90; --line: #3a333f; --accent: #d9ab57; --accent-ink: #f0d090; --pic: #2a2530; color-scheme: dark } }
:root[data-theme="dark"] { --bg: #16131a; --surface: #1f1b24; --fg: #ebe4d8; --muted: #a79c90; --line: #3a333f; --accent: #d9ab57; --accent-ink: #f0d090; --pic: #2a2530; color-scheme: dark }
body { background: var(--bg); color: var(--fg); font-family: var(--body); line-height: 1.55; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); padding-block: 0 48px; }
.wrap { max-width: 1060px; margin: 0 auto; display: grid; grid-template-columns: 190px minmax(0, 1fr); gap: 40px; }
@media (max-width: 760px) { .wrap { grid-template-columns: minmax(0, 1fr); gap: 0 } nav.toc { position: static; padding: 0; margin-bottom: 8px } }
nav.toc { position: sticky; top: env(safe-area-inset-top, 0px); align-self: start; padding-top: 40px; font-size: 13px; max-height: 100vh; overflow-y: auto }
nav.toc a { display: block; color: var(--muted); text-decoration: none; padding: 3px 0 3px 10px; border-left: 2px solid var(--line) }
nav.toc a.sub { padding-left: 22px; font-size: 12px }
nav.toc a:hover, nav.toc a:focus-visible { color: var(--accent-ink); border-color: var(--accent); outline: none }
main { min-width: 0; padding-top: 40px }
h1 { font-family: var(--display); font-size: clamp(30px, 5vw, 44px); line-height: 1.05; margin: 0 0 8px; text-wrap: balance; font-weight: 700 }
.lede { color: var(--muted); max-width: 64ch; margin: 0 0 18px; font-size: 16px }
.tally { display: flex; flex-wrap: wrap; gap: 8px 22px; margin: 0 0 30px; font-size: 14px; color: var(--muted); font-variant-numeric: tabular-nums }
.tally b { color: var(--fg); font-size: 18px; font-family: var(--display) }
h2 { font-family: var(--display); font-size: 26px; margin: 48px 0 10px; padding-top: 14px; border-top: 1px solid var(--line); text-wrap: balance; font-weight: 600 }
h3 { font-size: 15px; text-transform: uppercase; letter-spacing: .06em; color: var(--accent-ink); margin: 30px 0 4px; font-weight: 700 }
p { max-width: 70ch; margin: 0 0 12px }
ul, ol { max-width: 70ch; padding-left: 20px; margin: 0 0 12px } li { margin: 5px 0 }
code { font-family: var(--mono); font-size: 12.5px; background: var(--surface); border: 1px solid var(--line); border-radius: 3px; padding: 0 4px; white-space: nowrap }
.k { font-weight: 700 }
.tw { overflow-x: auto; margin: 10px 0 18px; border: 1px solid var(--line); border-radius: 6px; background: var(--surface) }
table { border-collapse: collapse; width: 100%; font-size: 14px; min-width: 520px }
th, td { text-align: left; vertical-align: top; padding: 8px 10px; border-bottom: 1px solid var(--line) }
th { font-size: 12px; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); font-weight: 700 }
tr:last-child td { border-bottom: 0 }
td.n { font-variant-numeric: tabular-nums; white-space: nowrap }
.ctx { display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 12px; margin: 14px 0 10px }
.ctx figure { margin: 0; min-width: 0 }
.ctx img, .pic img { image-rendering: pixelated; display: block; max-width: 100%; height: auto }
.ctx figcaption { font-size: 12px; color: var(--muted); margin-top: 4px }
.ctx.wide { grid-template-columns: minmax(0, 1fr) }
.entry { display: grid; grid-template-columns: minmax(0, 300px) minmax(0, 1fr); gap: 18px; padding: 16px 0; border-bottom: 1px solid var(--line) }
.entry:last-of-type { border-bottom: 0 }
.entry.wide { grid-template-columns: minmax(0, 1fr) }
.entry.wide .pic { justify-self: start; max-width: 100% }
@media (max-width: 640px) { .entry { grid-template-columns: minmax(0, 1fr) } }
.pic { background: var(--pic); border-radius: 6px; padding: 10px; align-self: start; overflow-x: auto }
.pic small { display: block; color: #c9bfd3; font-size: 11px; margin-top: 6px }
.facts h4 { margin: 0 0 2px; font-size: 17px; font-family: var(--display); font-weight: 600 }
.facts .key { font-family: var(--mono); font-size: 12.5px; color: var(--accent-ink) }
.facts dl { display: grid; grid-template-columns: max-content minmax(0, 1fr); gap: 2px 12px; margin: 8px 0; font-size: 13.5px }
.facts dt { color: var(--muted) }
.facts dd { margin: 0; min-width: 0 }
.facts p { margin: 6px 0 0; font-size: 14.5px }
.facts .done { font-family: var(--body); font-size: 11px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: var(--accent-ink); border: 1px solid var(--accent); border-radius: 3px; padding: 1px 6px; margin-left: 8px; vertical-align: 3px }
.facts .order { font-family: var(--mono); font-size: 12px; color: var(--muted); overflow-wrap: anywhere }
.note { background: var(--surface); border: 1px solid var(--line); border-left: 4px solid var(--accent); border-radius: 6px; padding: 12px 16px; margin: 14px 0 20px; max-width: 72ch }
@media (prefers-reduced-motion: reduce) { * { scroll-behavior: auto } }
</style>''')
    w('<div class="wrap">')
    w('<nav class="toc" aria-label="Sections">')
    w('<a href="#screen">How the screen is built</a><a href="#rules">Hard rules</a><a href="#groups">Palette groups</a><a href="#delivery">Delivery</a>')
    for a, name, secs in AREAS:
        w('<a href="#%s">%s</a>' % (a, esc(name)))
        for i, (t, _, _) in enumerate(secs):
            w('<a class="sub" href="#%s-%d">%s</a>' % (a, i, esc(t)))
    w('<a href="#sprites">Sprites seen here</a><a href="#additions">Additions</a><a href="#check">Checklist</a>')
    w('</nav><main>')
    w('<h1>BARTGAME tile specification</h1>')
    w('<p class="lede">%s</p>' % esc(INTRO))
    w('<div class="note"><p><span class="k">Status.</span> %s</p></div>' % esc(STATUS))
    w('<div class="tally"><span><b>%d</b> of %d entries delivered</span><span><b>%d</b> of %d tiles</span></div>' % (DONE_ENTRIES, TOTAL_ENTRIES, DONE_TILES, TOTAL_TILES))
    w('<div class="tally"><span><b>%d</b> entries</span><span><b>%d</b> tiles</span><span><b>%d</b> in the wood</span><span><b>%d</b> in the mystery rooms</span><span><b>%d</b> in the Drain</span></div>'
      % (TOTAL_ENTRIES, TOTAL_TILES, COUNTS['wood'], COUNTS['myst'], COUNTS['drain']))

    w('<h2 id="screen">How the screen is built</h2><ul>')
    for k, t in SCREEN:
        w('<li><span class="k">%s</span> %s</li>' % (esc(k), esc(t)))
    w('</ul>')
    w('<h2 id="rules">Hard rules (Game Boy Advance)</h2><ul>')
    for k, t in RULES:
        w('<li><span class="k">%s</span> %s</li>' % (esc(k), esc(t)))
    w('</ul>')
    w('<h2 id="groups">Palette groups</h2><p>Suggested groups, each up to 15 colours. Every entry names its group.</p>')
    w('<div class="tw"><table><tr><th>Group</th><th>Area</th><th>What goes in it</th></tr>')
    for a, g, what in D.GROUPS:
        w('<tr><td><code>%s</code></td><td>%s</td><td>%s</td></tr>' % (g, dict((x, n) for x, n, _ in AREAS)[a], esc(what)))
    w('</table></div>')
    w('<h2 id="delivery">Delivery</h2><ul>')
    for t in DELIVERY:
        w('<li>%s</li>' % t)
    w('</ul>')
    w('<div class="note"><p><span class="k">Reading an entry.</span> The picture is the tile in the game now, at three times its size, with each animation frame as a further row. Light lines separate the tiles of a variant set or family; they are not part of the art. The grey check is transparency.</p></div>')

    for a, name, secs in AREAS:
        w('<h2 id="%s">%s</h2>' % (a, esc(name)))
        w('<p>%s</p>' % esc(AREA_NOTE[a]))
        w('<div class="ctx%s">' % (' wide' if a == 'drain' else ''))
        for k, cap in CTX_IMAGES[a]:
            w('<figure><img src="%s" alt="%s, current tiles"><figcaption>%s, current tiles</figcaption></figure>' % (data_uri(os.path.join(CTX, k + '.png')), esc(cap), esc(cap)))
        w('</div>')
        for i, (t, intro, entries) in enumerate(secs):
            w('<h3 id="%s-%d">%s</h3>' % (a, i, esc(t)))
            if intro:
                w('<p>%s</p>' % esc(intro))
            for e in entries:
                from PIL import Image
                ipath = os.path.join(IMG, e['key'] + '.png')
                iw, ih = Image.open(ipath).size
                # small pictures at twice the render, wide strips across the whole column
                k = 2 if iw * 2 <= 280 else 1
                wide = iw > 280
                w('<div class="entry%s" id="%s">' % (' wide' if wide else '', e['key']))
                cur = e.get('current_frames', 1)
                note = '' if cur == e['frames'] else '<small>now %d frame%s; wanted %d</small>' % (cur, '' if cur == 1 else 's', e['frames'])
                w('<div class="pic"><img src="%s" width="%d" height="%d" alt="%s, current art">%s</div>' % (data_uri(ipath), iw * k, ih * k, esc(e['title']), note))
                w('<div class="facts"><h4>%s%s</h4><span class="key">%s/%s.png</span>' % (esc(e['title']), ' <span class="done">Delivered</span>' if e['done'] else '', e['group'], e['key']))
                w('<dl><dt>Size</dt><dd>%s</dd><dt>File</dt><dd>%s</dd><dt>Layer</dt><dd>%s</dd><dt>Frames</dt><dd>%s</dd><dt>Solid</dt><dd>%s</dd></dl>'
                  % (size_text(e), file_text(e), LAYER[e['layer']], frames_text(e), esc(e['solid'])))
                w('<p>%s</p>' % esc(e['what']))
                if e['needs']:
                    w('<p><span class="k">Joins.</span> %s</p>' % esc(e['needs']))
                if order_text(e):
                    w('<p class="order">Order, by the sides that carry the edge: %s</p>' % esc(order_text(e)))
                w('</div></div>')

    w('<h2 id="sprites">Sprites seen here</h2><p>These are sprites, specified in the <a href="https://claude.ai/artifact/KnDPDf4RTFYXbMnhoyyncF">BARTGAME sprite specification</a>, and are not part of this delivery. They are listed so the tiles can be judged against them.</p><ul>')
    w('<li><span class="k">The wood:</span> %s.</li><li><span class="k">The Drain:</span> %s.</li></ul>' % (esc(D.SPRITES['wood']), esc(D.SPRITES['drain'])))
    w('<h2 id="additions">Additions that would lift the quality</h2><p>Not drawn by the game today, so not required. Each would need a small change in the game to use, which will be made if they are delivered.</p><ul>')
    for k, t in D.ADDITIONS:
        w('<li><span class="k">%s.</span> %s</li>' % (esc(k), esc(t)))
    w('</ul>')
    w('<h2 id="check">Checklist for a delivery</h2><ol>')
    for t in CHECK:
        w('<li>%s</li>' % esc(t))
    w('</ol></main></div>')
    return '\n'.join(out) + '\n'


# --------------------------------------------------------------------- doc
def md_escape_cell(s):
    return s.replace('|', '\\|')


def doc():
    out = []
    w = out.append
    w('# BARTGAME tile specification\n')
    w(INTRO + '\n')
    w('**Status.** ' + STATUS + ' %d of %d entries (%d of %d tiles) are delivered.\n' % (DONE_ENTRIES, TOTAL_ENTRIES, DONE_TILES, TOTAL_TILES))
    w('%d entries, %d tiles: %d in the wood, %d in the mystery rooms, %d in the Drain. The pictures are in `tile_spec/`, one per entry (the current art at 3x, frames as rows), with room views in `tile_spec/rooms/`.\n'
      % (TOTAL_ENTRIES, TOTAL_TILES, COUNTS['wood'], COUNTS['myst'], COUNTS['drain']))
    w('## 1. How the screen is built\n')
    for k, t in SCREEN:
        w('- **%s** %s' % (k, t))
    w('\n## 2. Hard rules (Game Boy Advance)\n')
    for k, t in RULES:
        w('- **%s** %s' % (k, t))
    w('\n### Palette groups\n')
    w('| Group | Area | What goes in it |')
    w('|---|---|---|')
    names = dict((x, n) for x, n, _ in AREAS)
    for a, g, what in D.GROUPS:
        w('| `%s` | %s | %s |' % (g, names[a], what))
    w('\n## 3. Delivery\n')
    for t in DELIVERY:
        w('- ' + t.replace('<code>', '`').replace('</code>', '`'))
    w('')
    n = 4
    for a, name, secs in AREAS:
        w('## %d. %s\n' % (n, name))
        n += 1
        w(AREA_NOTE[a] + '\n')
        w(' '.join('![%s](tile_spec/rooms/%s.png)' % (cap, k) for k, cap in CTX_IMAGES[a]) + '\n')
        for t, intro, entries in secs:
            w('### %s\n' % t)
            if intro:
                w(intro + '\n')
            w('| Entry | Key and file | Size | Layer | Frames | Solid | What it is | Joins |')
            w('|---|---|---|---|---|---|---|---|')
            for e in entries:
                joins = e['needs']
                if order_text(e):
                    joins = (joins + ' ' if joins else '') + 'Order: ' + order_text(e) + '.'
                w('| ![](tile_spec/%s.png) **%s**%s | `%s/%s.png` %s | %s | %s | %s | %s | %s | %s |' % (
                    e['key'], e['title'], ' (delivered)' if e['done'] else '', e['group'], e['key'], file_text(e), size_text(e), LAYER[e['layer']],
                    frames_text(e), e['solid'], md_escape_cell(e['what']), md_escape_cell(joins)))
            w('')
    w('## %d. Sprites seen here\n' % n)
    n += 1
    w('Specified in `BARTGAME_ART_SPEC.md`, not part of this delivery.\n')
    w('- **The wood:** %s.' % D.SPRITES['wood'])
    w('- **The Drain:** %s.\n' % D.SPRITES['drain'])
    w('## %d. Additions that would lift the quality\n' % n)
    n += 1
    w('Not drawn by the game today, so not required. Each needs a small change in the game to use.\n')
    for k, t in D.ADDITIONS:
        w('- **%s.** %s' % (k, t))
    w('\n## %d. Checklist for a delivery\n' % n)
    for i, t in enumerate(CHECK):
        w('%d. %s' % (i + 1, t))
    w('')
    return '\n'.join(out)


# current frame counts, from the renders' row count
for a, _, secs in AREAS:
    for _, _, es in secs:
        for e in es:
            from PIL import Image
            im = Image.open(os.path.join(IMG, e['key'] + '.png'))
            c, r = cols_rows(e)
            h1 = r * 16 * 3
            e['current_frames'] = (im.height + 12) // (h1 + 12)
open(PAGE, 'w').write(page())
open(DOC, 'w').write(doc())
for a, _, secs in AREAS:
    for _, _, es in secs:
        for e in es:
            shutil.copy(os.path.join(IMG, e['key'] + '.png'), os.path.join(DOCIMG, e['key'] + '.png'))
os.makedirs(os.path.join(DOCIMG, 'rooms'), exist_ok=True)
for a in CTX_IMAGES:
    for k, _ in CTX_IMAGES[a]:
        shutil.copy(os.path.join(CTX, k + '.png'), os.path.join(DOCIMG, 'rooms', k + '.png'))
print('page %d bytes, doc %d bytes, %d entries, %d tiles %s' % (os.path.getsize(PAGE), os.path.getsize(DOC), TOTAL_ENTRIES, TOTAL_TILES, COUNTS))

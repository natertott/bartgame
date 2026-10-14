"""Feasibility spikes for the lantern and gust-jar ? room events.

Each case stands in a real ? room site and checks one engine primitive the
two events would be built from, by playing it (the item on B, pressed):

  TORCH    an unlit torch tile (TILE_TYPE_117) set beside the player; the
           Lantern swung at it turns it to TILE_TYPE_118 (lit). tiles.h's
           comments sit one off: 119 is a raised floor button (button.c)
  OUT      a lit torch set back to unlit by SetTileType - the timed variant
  DARK     the room darkened at two levels (vanilla's 0x80 and pitch 0x00),
           screenshots with and without the lantern lit
  DARK+TORCH  pitch black, a torch lit, the room brightened by
           ChangeLightLevel (lightLevelSetManager.c's own step)
  WEB      a SPIDER_WEB projectile spawned in the room draws, and the Gust
           Jar pulls it away; WEB lantern: the lantern burns one
  DUST     the DUST enemy's type-0 cloud (Hyrule Town's carpet dust) draws
           in a cave and the jar clears it, once MACHI_MACHIHOKORI is clear

Measured and left out, because they cannot be used as they are:
REMOVABLE_DUST type 1 (the free-standing piece) draws magenta in a cave -
its form loads no sheet and leans on Mount Crenel's area art - and the jar
never took it; the DUST enemy's type-1 piece deletes itself on its first
frame. Mount Crenel's dust patch (REMOVABLE_DUST type 0) sits on that
tileset's own dust tiles, which only 3 of the 119 sites carry
(lantern_gust_survey.py).

    python3 tools/quickstart/lantern_gust_spike.py [--rom tmc-d3.gba] [--site 3] [--out DIR]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scenario as S
import parse_tables as P
import callrom as C
from emu import here, press, snap, r16, w16, entities, PLAYER, ROOM_CONTROLS, GENT, STRIDE, KIND_OBJECT

args = sys.argv[1:]
ROM = args[args.index('--rom') + 1] if '--rom' in args else os.path.join(P.ROOT, 'tmc-d3.gba')
SITE = int(args[args.index('--site') + 1]) if '--site' in args else 3
OUT = args[args.index('--out') + 1] if '--out' in args else '/tmp/lantern_gust'
os.makedirs(OUT, exist_ok=True)
SAVE = 0x02002a40
EQUIPPED = SAVE + 0xB4
MAP_BOTTOM = 0x02025eb0
ROOM_VARS_LIGHT = 0x02034350 + 0x0c   # gRoomVars.lightLevel (room.h; 0 black, 0x100 day)
KIND_PROJ, KIND_ENEMY = 4, 3
PROJ = {v: k for k, v in P._enum(open(os.path.join(P.ROOT, 'include/projectile.h')).read()).items()}
ENEMY = {0x53: 'DUST'}   # enemy.h numbers its rows in comments
results = []
MACHI = 0x12   # MACHI_MACHIHOKORI, the town's dust sucked from the carpet (flags.h)


def check(name, ok, detail=''):
    results.append(ok)
    print('%s %-44s %s' % ('PASS' if ok else 'FAIL', name, detail), flush=True)


def run(c, n):
    for _ in range(n):
        c.memory.u8[PLAYER + 0x45] = 24
        c.run_frame()


def give_b(c, item):
    b, sh = item >> 2, (item & 3) * 2
    c.memory.u8[SAVE + 0xF2 + b] = (c.memory.u8[SAVE + 0xF2 + b] & ~(3 << sh) & 0xFF) | (1 << sh)
    c.memory.u8[EQUIPPED + 1] = item


def local(c):
    return (r16(c, PLAYER + 0x2e) - r16(c, ROOM_CONTROLS + 6), r16(c, PLAYER + 0x32) - r16(c, ROOM_CONTROLS + 8))


def tile_type(c, tpos):
    idx = r16(c, MAP_BOTTOM + 4 + 2 * tpos)
    return r16(c, MAP_BOTTOM + 0x5004 + 2 * idx)


def face_up(c):
    press(c, c.KEY_UP, 2, 4)


def boot():
    c = S.boot(ROM, S.KINDS['SITE'], SITE, S.EVENTS.index('ITEM_DROP'), 0, kit=2, diff=3, frames=300)
    for _ in range(300):
        if c.memory.u8[0x02000050]:
            press(c, c.KEY_A, 3, 17)
        else:
            break
    run(c, 30)
    return c


set_tile = C.map_sym('SetTileType')
paint = C.map_sym('SetTile')
UPDATE_VISIBLE = 0x02000070   # gUpdateVisibleTiles (tmc.map; a data symbol map_sym skips)


def put_tile(c, t, tpos):
    # SetTileType edits the map data; SetTile and the refresh flag put it on
    # the screen (QuickStartPaintChestTile's lesson).
    C.call_keep(c, set_tile, (t, tpos, 1))
    C.call_keep(c, paint, (r16(c, MAP_BOTTOM + 0x6004 + 2 * t), tpos, 1))
    c.memory.u8[UPDATE_VISIBLE] = 1
dark = C.map_sym('sub_0805BB00')
mk_proj = C.map_sym('CreateProjectile')
mk_enemy = C.map_sym('CreateEnemy')

# TORCH / OUT
c = boot()
print('site %d room %s player %s' % (SITE, here(c), local(c)))
px, py = local(c)
tpos = (px >> 4) + ((py >> 4) - 2) * 64
put_tile(c, 0x75, tpos)
run(c, 2)
snap(c, os.path.join(OUT, 'torch_placed.png'))
check('TORCH: the unlit torch tile is set', tile_type(c, tpos) == 0x75, 'type %#x' % tile_type(c, tpos))
give_b(c, P.ITEMS['ITEM_LANTERN_OFF'])
face_up(c)
press(c, c.KEY_B, 3, 30)       # light the lantern
snap(c, os.path.join(OUT, 'torch_before.png'))
for _ in range(4):
    face_up(c)
    press(c, c.KEY_B, 3, 30)   # swing it at the torch
    if tile_type(c, tpos) == 0x76:
        break
snap(c, os.path.join(OUT, 'torch_after.png'))
check('TORCH: the lantern lights it', tile_type(c, tpos) == 0x76,
      'type %#x, B item %#x' % (tile_type(c, tpos), c.memory.u8[EQUIPPED + 1]))
put_tile(c, 0x75, tpos)
run(c, 2)
check('OUT: SetTileType puts a lit torch out', tile_type(c, tpos) == 0x75, 'type %#x' % tile_type(c, tpos))

# DARK
for level, name in ((0x80, 'dim'), (0x00, 'black')):
    c = boot()
    C.call_keep(c, dark, (level, 1))
    run(c, 30)
    snap(c, os.path.join(OUT, 'dark_%s_unlit.png' % name))
    give_b(c, P.ITEMS['ITEM_LANTERN_OFF'])
    press(c, c.KEY_B, 3, 40)
    snap(c, os.path.join(OUT, 'dark_%s_lantern.png' % name))
    check('DARK %s: room darkened, lantern lit' % name, c.memory.u8[EQUIPPED + 1] == P.ITEMS['ITEM_LANTERN_ON'],
          'B item %#x' % c.memory.u8[EQUIPPED + 1])

# DARK + TORCH: pitch black, one torch lit, the room brightened by it the
# way lightLevelSetManager.c does it (ChangeLightLevel by the torch's share)
c = boot()
C.call_keep(c, dark, (0x00, 1))
run(c, 20)
px, py = local(c)
tpos = (px >> 4) + ((py >> 4) - 2) * 64
put_tile(c, 0x75, tpos)
give_b(c, P.ITEMS['ITEM_LANTERN_OFF'])
face_up(c)
press(c, c.KEY_B, 3, 30)
for _ in range(4):
    face_up(c)
    press(c, c.KEY_B, 3, 30)
    if tile_type(c, tpos) == 0x76:
        break
lit = tile_type(c, tpos) == 0x76
before = c.memory.u8[ROOM_VARS_LIGHT] | (c.memory.u8[ROOM_VARS_LIGHT + 1] << 8)
C.call_keep(c, C.map_sym('ChangeLightLevel'), (0x40,))
run(c, 30)
after = c.memory.u8[ROOM_VARS_LIGHT] | (c.memory.u8[ROOM_VARS_LIGHT + 1] << 8)
snap(c, os.path.join(OUT, 'dark_torch_lit.png'))
check('DARK+TORCH: lit in the black, the room brightens', lit and after > before,
      'torch %s, light %#x -> %#x' % ('lit' if lit else 'unlit', before, after))

# WEB and DUST by the jar
for label, kind, ident, typ in (('WEB', 'proj', 'SPIDER_WEB', 0), ('DUST cloud', 'enemy', 'DUST', 0),
                                ('WEB lantern', 'proj', 'SPIDER_WEB', 0)):
    c = boot()
    px, py = local(c)
    if ident == 'DUST':
        # it deletes itself once the town's dust is cleared (MACHI_MACHIHOKORI)
        C.call_keep(c, C.map_sym('ClearGlobalFlag'), (MACHI,))
    if kind == 'proj':
        p = C.call_keep(c, mk_proj, ({v: k for k, v in PROJ.items()}[ident],))
    else:
        p = C.call_keep(c, mk_enemy, ({v: k for k, v in ENEMY.items()}[ident], typ))
    if not p:
        check(label + ': spawned', False, 'NULL')
        continue
    c.memory.u8[p + 0x0a] = typ
    w16(c, p + 0x2e, r16(c, ROOM_CONTROLS + 6) + px)
    w16(c, p + 0x32, r16(c, ROOM_CONTROLS + 8) + py - 28)
    c.memory.u8[p + 0x38] = 1   # collisionLayer
    run(c, 20)
    alive = lambda: c.memory.u8[p + 8] != 0 and c.memory.u8[p + 9] == {v: k for k, v in (PROJ if kind == 'proj' else ENEMY).items()}[ident]
    snap(c, os.path.join(OUT, '%s_before.png' % label.replace(' ', '_')))
    check(label + ': spawned and standing', alive(), 'draw %d' % (c.memory.u8[p + 0x18] & 3))
    if 'lantern' in label:
        give_b(c, P.ITEMS['ITEM_LANTERN_OFF'])
        press(c, c.KEY_B, 3, 30)
        w16(c, PLAYER + 0x32, r16(c, p + 0x32) + 14)
        for f in range(8):
            face_up(c)
            press(c, c.KEY_B, 3, 30)
            if not alive():
                break
    else:
        give_b(c, P.ITEMS['ITEM_GUST_JAR'])
        face_up(c)
        c.set_keys(c.KEY_B)
        for f in range(240):
            c.memory.u8[PLAYER + 0x14] = 0
            run(c, 1)
            if not alive():
                break
        c.clear_keys(c.KEY_B)
    run(c, 40)
    snap(c, os.path.join(OUT, '%s_after.png' % label.replace(' ', '_')))
    check(label + (': the lantern burns it' if 'lantern' in label else ': the Gust Jar clears it'), not alive(), 'after %d steps' % f)

print('RESULT %s %d/%d' % ('PASS' if all(results) else 'FAIL', sum(results), len(results)))

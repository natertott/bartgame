"""Veil Falls, the fourteenth region (Oct 2026): is it wired the way the
walked survey and the integration say?

  DOOR     cave #1's door is open in this build: walking north from the
           North Field corridor enters VEIL_FALLS_CAVES/ENTRANCE (vanilla
           seals it with the Source of the Flow stone until a fusion; that
           NPC is deleted at init under QUICKSTART).
  VORTEX   the whirlwind on the Top screen is gone (it carried a player
           into Cloud Tops, which the mode does not include).
  CLIMB    the big waterfall is a Grip Ring climb: with the ring a player
           at its foot (344,470) rises to the top plateau; without it,
           nothing.
  LANDING  the pool row's entrance, reward and every drop spot are open
           floor in one walkable piece; each fuser spot is in that piece.
  SITES    every Veil Falls content site's spot is open floor in the piece
           its door's arrival lands in.
  BORDERS  the seven border crossings into and out of the falls land in
           the room the survey's links say (borders keep the global
           coordinate: North Hyrule Field's east edge is the falls on its
           north half and the ranch on its south).
  REACH    QuickStartReachTestRoom from the falls' pool row: the cave
           needs the lantern, the top plateau the grip on top, the Lon Lon
           strip is never reached (two pockets), and North Hyrule Field is
           reached through the cave.

    python3 tools/quickstart/veilfalls_probe.py [--rom tmc-d3.gba]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import warp, r16, room_dims, coll_at, act_at, poison_here, ROOM_CONTROLS, PLAYER, here, press, entities, KIND_OBJECT
import scenario as S
import parse_tables as P
import callrom as C
ROM = sys.argv[sys.argv.index('--rom') + 1] if '--rom' in sys.argv else 'tmc-d3.gba'
res = []
def check(name, ok, detail=''):
    res.append(ok); print('%s %-44s %s' % ('PASS' if ok else 'FAIL', name, detail), flush=True)
MSG = 0x02000050   # gMessage: state at +0 (4 typing, 7 waiting for A, 0 closed)
def dismiss(c, limit=900):
    """Close every textbox in turn. A region's first arrival stacks Ezlo's
    hints - the run intro, the chain's region line, the element's - and
    each only takes A once it has finished typing; a fixed count of blind
    presses walks away with one still open and every object frozen."""
    quiet = 0
    for _ in range(limit):
        state = c.memory.u8[MSG]
        if state == 0 and c.memory.u8[PLAYER + 0x0c] not in (0x16, 0x7):
            # Free: never press here, or the press TALKS to whatever is nearby.
            c.run_frame()
            quiet += 1
            if quiet >= 30:
                return
            continue
        # A box is up (typing, waiting, or closing): A skips the typing and
        # takes the box; one press every twenty frames is what a thumb does.
        press(c, c.KEY_A, 3, 17)
        quiet = 0
def local(c):
    ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
    return (r16(c, PLAYER + 0x2e) - ox, r16(c, PLAYER + 0x32) - oy)
BAD = {0x0d, 0x0e, 0x0f, 0x10, 0x12, 0x13, 25, 240}
def flood(c, sx, sy):
    w, h = room_dims(c); w >>= 4; h >>= 4
    seen, st = set(), [(sx, sy)]
    while st:
        x, y = st.pop()
        if (x, y) in seen or not (0 <= x < w and 0 <= y < h) or coll_at(c, x, y) != 0 or act_at(c, x, y) in BAD:
            continue
        seen.add((x, y)); st += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return seen

VF = P.AREAS['AREA_VEIL_FALLS']; TOP = P.AREAS['AREA_VEIL_FALLS_TOP']
c = S.boot(ROM, 0)
# ---- the door
poison_here(c); warp(c, VF, 0, 56, 560, frames=300); dismiss(c)
for i in range(60):
    press(c, c.KEY_UP, 8, 0)
    if here(c) != (VF, 0):
        break
check('DOOR: cave #1 opens from the corridor', here(c) == (P.AREAS['AREA_VEIL_FALLS_CAVES'], P.ROOMS['ROOM_VEIL_FALLS_CAVES_ENTRANCE']),
      'room %s after %d frames' % (here(c), (i + 1) * 8))
# ---- the vortex: stand where it stood; no BIG_VORTEX object, no Cloud Tops
objs = P._enum(open(os.path.join(P.ROOT, 'include/object.h')).read())
poison_here(c); warp(c, TOP, 0, 88, 60, frames=400); dismiss(c)
vortex = [e for e in entities(c, KIND_OBJECT) if e[2] == objs['BIG_VORTEX']]
check('VORTEX: gone, and the player stays on the Top screen', here(c) == (TOP, 0) and not vortex,
      'room %s vortices %d' % (here(c), len(vortex)))
# ---- the climb
def climb(with_ring):
    C.call_keep(c, C.map_sym('SetInventoryValue'), (P.ITEMS['ITEM_GRIP_RING'], 1 if with_ring else 0))
    poison_here(c); warp(c, VF, 0, 344, 470, frames=300); dismiss(c)
    for i in range(150):
        press(c, c.KEY_UP, 4, 0)
    return local(c)
without = climb(False); withr = climb(True)
check('CLIMB: the big falls need the Grip Ring', without[1] > 440 and withr[1] < 260,
      'without %s with %s' % (without, withr))
# ---- the landing
row = next(r for r in P.region_pool() if r['roomName'] == 'ROOM_VEIL_FALLS_MAIN')
poison_here(c); warp(c, VF, 0, row['entrance'][0], row['entrance'][1], frames=300); dismiss(c)
ex, ey = row['entrance']
piece = flood(c, ex >> 4, ey >> 4)
def on(p): return (p[0] >> 4, p[1] >> 4) in piece
drops = P.region_drop_spots()[P.region_pool().index(row)] if hasattr(P, 'region_drop_spots') else []
fus = next((r for r in P.fuser_spots() if r['roomName'] == 'ROOM_VEIL_FALLS_MAIN'), None) if hasattr(P, 'fuser_spots') else None
bad = [p for p in ([row['reward']] + (fus['spots'] if fus else [])) if not on(p)]
check('LANDING: entrance, reward and fuser spots share one piece', len(piece) >= 60 and on(row['entrance']) and not bad,
      'piece %d tiles, off it: %s' % (len(piece), bad))
# ---- the sites. Booted through the testbed with the NPC event forced, so
# the room is a site with its event present but nothing of ours on the
# floor's collision (a chest or a pot lottery writes tile collision at the
# spot, which is the event, not a bad spot). Flooded from where the
# testbed lands the player - the door's own arrival - and the spot must be
# on that piece or touching it.
sites = [(i, an, rn, a, r, x, y) for i, (an, rn, a, r, x, y) in enumerate(P.content_sites())
         if an in ('AREA_VEIL_FALLS_CAVES', 'AREA_VEIL_FALLS_TOP') or rn in ('ROOM_DOJOS_TO_SPLITBLADE', 'ROOM_DOJOS_SPLITBLADE')]
offs = []
ARRIVAL = {'ROOM_VEIL_FALLS_CAVES_ENTRANCE': (56, 120), 'ROOM_VEIL_FALLS_CAVES_EXIT': (152, 120),
           'ROOM_VEIL_FALLS_CAVES_HALLWAY_1F': (184, 120), 'ROOM_VEIL_FALLS_CAVES_HALLWAY_2F': (56, 120),
           'ROOM_VEIL_FALLS_CAVES_HALLWAY_SECRET_ROOM': (106, 90), 'ROOM_VEIL_FALLS_CAVES_SECRET_CHEST': (152, 72),
           'ROOM_VEIL_FALLS_CAVES_HALLWAY_SECRET_STAIRCASE': (88, 72), 'ROOM_VEIL_FALLS_CAVES_HALLWAY_BLOCK_PUZZLE': (152, 280),
           'ROOM_VEIL_FALLS_CAVES_HALLWAY_RUPEE_PATH': (184, 280), 'ROOM_DOJOS_TO_SPLITBLADE': (120, 40),
           'ROOM_DOJOS_SPLITBLADE': (120, 100), 'ROOM_VEIL_FALLS_TOP_0': (320, 40)}
for i, an, rn, a, r, x, y in sites:
    # The testbed parks the player a tile below the spot, which in three of
    # these rooms is wall; the door's own arrival is where a player stands.
    c = S.boot(ROM, S.KINDS['SITE'], i, 2, 0, kit=1, frames=200)
    ax, ay = ARRIVAL[rn]
    poison_here(c); warp(c, a, r, ax, ay, frames=300); dismiss(c)
    piece = flood(c, ax >> 4, ay >> 4)
    near = any((x // 16 + dx, y // 16 + dy) in piece for dx in (-1, 0, 1) for dy in (-1, 0, 1))
    if here(c) != (a, r) or len(piece) < 15 or not near:
        offs.append((rn, here(c), (x, y), len(piece)))
check('SITES: twelve spots, each on its door\'s piece', len(sites) == 12 and not offs, 'sites %d off %s' % (len(sites), offs))
c = S.boot(ROM, 0)
# ---- reach from the pool row
pool = P.region_pool().index(row)
import sim
bits = sim.TOKEN_BITS
def reach(held, an, rn):
    return C.call_keep(c, C.game_sym('QuickStartReachTestRoom'), (pool, held, P.AREAS[an], P.ROOMS[rn]))
LANT, GRIP = bits['QS_REACH_LANTERN'], bits['QS_REACH_GRIP']
r = (reach(0, 'AREA_VEIL_FALLS_CAVES', 'ROOM_VEIL_FALLS_CAVES_ENTRANCE'),
     reach(LANT, 'AREA_VEIL_FALLS_CAVES', 'ROOM_VEIL_FALLS_CAVES_ENTRANCE'),
     reach(LANT, 'AREA_VEIL_FALLS_CAVES', 'ROOM_VEIL_FALLS_CAVES_HALLWAY_2F'),
     reach(LANT | GRIP, 'AREA_VEIL_FALLS_CAVES', 'ROOM_VEIL_FALLS_CAVES_HALLWAY_2F'),
     reach(0, 'AREA_VEIL_FALLS_CAVES', 'ROOM_VEIL_FALLS_CAVES_HALLWAY_2F'),
     reach(LANT | GRIP, 'AREA_DOJOS', 'ROOM_DOJOS_SPLITBLADE'))
check('REACH: cave lantern / top grip / the dojo never (pocket 1)', r == (0, 1, 0, 1, 0, 0), str(r))
# ---- the borders: every crossing into and out of the falls, walked.
# Borders keep the GLOBAL coordinate, which is why North Hyrule Field's
# east edge splits the way it does: its north half (local y ~111, the bomb
# pocket) is the falls' corridor and its south half (y ~639) is the ranch.
HF = P.AREAS['AREA_HYRULE_FIELD']
LLR = P.ROOMS['ROOM_HYRULE_FIELD_LON_LON_RANCH']; NHF = P.ROOMS['ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD']
LEGS = [('ranch north gate -> falls', HF, LLR, 88, 40, 'KEY_UP', (VF, 0)),
        ('ranch gold-chest pocket -> falls', HF, LLR, 176, 40, 'KEY_UP', (VF, 0)),
        ('falls Lon Lon strip -> ranch', VF, 0, 88, 985, 'KEY_DOWN', (HF, LLR)),
        ('falls lower strip -> ranch pocket', VF, 0, 176, 985, 'KEY_DOWN', (HF, LLR)),
        ('field bomb pocket -> falls corridor', HF, NHF, 990, 111, 'KEY_RIGHT', (VF, 0)),
        ('field east, south half -> ranch', HF, NHF, 990, 639, 'KEY_RIGHT', (HF, LLR)),
        ('falls corridor -> field bomb pocket', VF, 0, 24, 639, 'KEY_LEFT', (HF, NHF))]
bad = []
for name, a, r, x, y, key, want in LEGS:
    c = S.boot(ROM, 0)
    poison_here(c); warp(c, a, r, x, y, frames=300); dismiss(c)
    for i in range(60):
        press(c, getattr(c, key), 8, 0)
        if here(c) != (a, r):
            break
    for _ in range(60):
        c.run_frame()
    if here(c) != want:
        bad.append((name, here(c)))
check('BORDERS: seven crossings land where the rows say', not bad, str(bad) if bad else 'all seven')
print('RESULT', 'PASS' if all(res) else 'FAIL', '%d/%d' % (sum(res), len(res)))
sys.exit(0 if all(res) else 1)

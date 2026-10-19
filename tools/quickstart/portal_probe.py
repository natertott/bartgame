"""Play the portal pairs in the ROM (docs/QUICKSTART_PORTAL_POCKETS.md).

For each pocket in include/quickstart/portals.h, the testbed pre-deals the
pair (scenario CHAIN: step 0 EVENT at a portal A site with chain_detail
0x40 | pocket, which deals the ITEM half too) with the boot kit only, and
lands in portal A's room. Then, as a player would:

  DEALT     step 0 is the EVENT at A, step 1 the pocket's ITEM; the player
            holds none of the escape items
  ASLEEP    a WARP_POINT stands on A's portal tile; its lit flag is clear
  FIGHT     A deals a fight (our enemies stand in the room)
  LIT       A's fight won and its prize taken (chain_audit.drive): the
            site is DONE, the portal's lit flag is set, step 1 is current
  RIDE      standing on the pad warps the player to the pocket's landing
            tile
  PAY       inside the pocket the prize draw (QuickStartDrawItem) is the
            escape item; for a landing ? room the fight there is won for
            real and the item is held after (step 1 met)
  BACK      (two-way) the return pad stands on the landing tile and carries
            the player back to A's tile
  OUT       the landing walks item-free to an overworld room (a room's own
            door, from the generator's floor), and the Ocarina flies the
            player home to Cloud Tops from there
  PATIENCE  a fresh boot: three prizes drawn outside the pocket are not the
            escape item, the fourth is

  --census  every candidate site, landed as portal A: the tiles its own
            objects stand on (pots, statues, NPCs: solid, and absent from
            the captured floor) and whether the player is Minish there.
            Writes build/portal_census.json, which portal_rooms.py reads;
            --only 47,65 re-measures those sites and merges them in.
  --sweep   every portal A site in the table, into the Wind Ruins: DEALT,
            ASLEEP, FIGHT, LIT and RIDE (the pad stands on open floor the
            player reaches, lights, and carries them)

    python3 tools/quickstart/portal_probe.py [--rom tmc-d3.gba] [--pocket N] [--site S] [--census] [--sweep]
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import emu
from emu import here, press, entities, r16, PLAYER, ROOM_CONTROLS, KIND_OBJECT, KIND_ENEMY
import scenario as S
import parse_tables as P
import callrom as C
import sim
from block_probe import room_flag, origin, run, dismiss, settle, MSG
from block_puzzles import Floor, ROOMS, flood
import exit_lists as X
import chain_audit as A
import carry_room_probe as R

SAVE = 0x02002a40
CHAIN_KIND, CHAIN_WHERE, CHAIN_DETAIL = SAVE + 0x26, SAVE + 0x2B, SAVE + 0x30
CHAIN_PROGRESS, CHAIN_ROLLED = SAVE + 0x35, SAVE + 0x36
EQUIPPED = SAVE + 0xB4
SNAP = os.environ.get("PORTAL_SNAP")
LIT_FLAG = 125
OBJ = open(os.path.join(P.ROOT, 'include', 'object.h')).read()
_names = re.findall(r'^\s+(\w+),', OBJ[OBJ.index('typedef enum'):], re.M)
WARP_POINT = _names.index('WARP_POINT')
ITEM_NAME = {v: k for k, v in P.ITEMS.items()}
OVERWORLD = {P.AREAS[a] for a in ('AREA_CASTOR_WILDS', 'AREA_LAKE_HYLIA', 'AREA_RUINS')}


def has(c, name):
    n = P.ITEMS[name]
    return (c.memory.u8[SAVE + 0xF2 + (n >> 2)] >> ((n & 3) * 2)) & 3


def chain(c):
    return [(c.memory.u8[CHAIN_KIND + i], c.memory.u8[CHAIN_WHERE + i], c.memory.u8[CHAIN_DETAIL + i])
            for i in range(5)], c.memory.u8[CHAIN_PROGRESS], c.memory.u8[CHAIN_ROLLED]


def pads(c):
    return [(e[4], e[5]) for e in entities(c, KIND_OBJECT, WARP_POINT)]


def tile_world(c, tx, ty):
    ox, oy = origin(c)
    return ox + tx * 16 + 8, oy + ty * 16 + 8


def stand(c, x, y):
    emu.w16(c, PLAYER + 0x2e, x)
    emu.w16(c, PLAYER + 0x32, y)


PLAYER_STATE = 0x03003f80
PL_CAPTURED = 0x10


def release(c):
    """chain_audit.drive kills by writing an enemy's health to 0. A Like
    Like killed that way while it holds the player never lets go: the
    player stays CAPTURED and uncollidable (measured in the Mayor's cabin).
    A player's own sword frees them; the probe frees them by hand."""
    f = c.memory.u32[PLAYER_STATE + 0x30]
    if f & PL_CAPTURED:
        c.memory.u32[PLAYER_STATE + 0x30] = f & ~PL_CAPTURED
        c.memory.u8[PLAYER + 0x10] |= 0x80
        run(c, 10)
        return True
    return False


def ride(c, tx, ty, frames=600):
    """Step onto the pad at (tx, ty) from the tile below and wait for the
    room to change. Returns the frame count, or None."""
    start = here(c)
    x, y = tile_world(c, tx, ty)
    stand(c, x, y + 20)
    run(c, 20)
    stand(c, x, y)
    for f in range(frames):
        A.run(c, 1)
        if c.memory.u8[MSG]:
            dismiss(c)
        if here(c) != start:
            run(c, 150)
            return f
    return None


def player_tile(c):
    ox, oy = origin(c)
    return (r16(c, PLAYER + 0x2e) - ox) // 16, (r16(c, PLAYER + 0x32) - oy) // 16


def draw(c, seed6=5):
    return C.call_keep(c, C.game_sym('QuickStartDrawItem'), (seed6, 0xff), budget=4000000) & 0xffff


def ocarina_home(c):
    c.memory.u8[EQUIPPED + 1] = P.ITEMS['ITEM_OCARINA']
    press(c, c.KEY_B, 3, 3)
    for _ in range(900):
        if c.memory.u8[MSG]:
            press(c, c.KEY_A, 3, 17)
        else:
            c.run_frame()
    return here(c)[0] == P.AREAS['AREA_CLOUD_TOPS']


# The walk out of each two-way landing, room by room, to an overworld room:
# a room edge to walk off ('S', 'N', 'E', 'W') or a door's pixel spot and
# the key that takes it. Darknut Hall's main room opens south into its
# hall, the hall's top door into the Darknut cave, the cave south onto the
# far bank; the Mayor's cabin opens south onto the lake.
ROUTES = {
    'ROOM_CASTOR_DARKNUT_MAIN': ['S', ((392, 24), 'UP'), 'S'],
    'ROOM_HOUSE_INTERIORS_4_MAYOR_LAKE_CABIN': ['S'],
}


def door_out(c, room_name):
    """Walk the route on the live collision grid (no item: the walkable
    piece is plain floor), room by room. Returns (rooms passed, note)."""
    passed = [here(c)]
    for hop in ROUTES[room_name]:
        tw, th, g = R.carry_grid(c)
        me = R.ltile(c)
        inside = R.piece(tw, th, g, me)
        if isinstance(hop, str):
            dx, dy = {'S': (0, 1), 'N': (0, -1), 'E': (1, 0), 'W': (-1, 0)}[hop]
            # the reachable tiles facing that way across a solid tile (a
            # doorway's own tile reads solid on the grid), furthest that
            # way first, then nearest
            goals = sorted((t for t in inside if (t[0] + dx, t[1] + dy) not in inside),
                           key=lambda t: (-(t[0] * dx + t[1] * dy), abs(t[0] - me[0]) + abs(t[1] - me[1])))[:16]
            key = {'S': c.KEY_DOWN, 'N': c.KEY_UP, 'E': c.KEY_RIGHT, 'W': c.KEY_LEFT}[hop]
        else:
            (px, py), k = hop
            goal = (px // 16, py // 16)
            if goal not in inside:
                goal = min(inside, key=lambda t: abs(t[0] - goal[0]) + abs(t[1] - goal[1]))
            goals = [goal]
            key = getattr(c, 'KEY_' + k)
        start = here(c)
        for goal in goals:
            R.walk_to(c, inside, goal, limit=4000)
            c.set_keys(key)
            for _ in range(120):
                A.run(c, 1)
                if here(c) != start:
                    break
            c.clear_keys(key)
            if here(c) != start:
                break
        if here(c) == start:
            emu.snap(c, os.path.join(SNAP, "stuck.png")) if SNAP else None
            return passed, "stuck at %s in %s" % (R.ltile(c), here(c))
        run(c, 120)
        settle(c, 60)
        passed.append(here(c))
    return passed, 'walked'


def probe_pocket(rom, p, site, diff, ride_only=False):
    k = sim.PORTALS[p]
    res = {}
    c = S.boot(rom, S.KINDS['CHAIN'], a=1, b=site, c=0x40 | p, kit=0, diff=diff, frames=300)
    settle(c, 200)
    s = sim.SITES[site]
    for _ in range(600):
        if c.memory.u8[CHAIN_ROLLED] >= 2:
            break
        A.run(c, 1)
    steps, prog, rolled = chain(c)
    res['DEALT'] = (steps[0] == (1, site, 0x40 | p) and steps[1][0] == 0 and steps[1][1] == 0x40 | p
                    and rolled == 2 and not any(has(c, e) for e in k['escape']) and here(c) == (s['area'], s['room']))
    tile = sim.PORTAL_TILES[site]
    want = tile_world(c, *tile)
    res['ASLEEP'] = want in pads(c) and not room_flag(c, LIT_FLAG)
    res['FIGHT'] = len(entities(c, KIND_ENEMY)) > 0
    done, note = A.drive(c, 'WAVES', site)
    if not done and release(c):
        done, note = A.drive(c, 'WAVES', site)
        note += ', released from a Like Like'
    run(c, 60)
    dismiss(c)
    run(c, 30)
    steps, prog, rolled = chain(c)
    # progress 2: A's own prize happened to be an escape item (step 1 met at once)
    res['LIT'] = bool(done and room_flag(c, LIT_FLAG) and prog >= 1)
    if not res['LIT']:
        return res, 'A not lit: %s, progress %d, lit %d' % (note, prog, room_flag(c, LIT_FLAG))
    f = ride(c, *tile)
    land = (k['land_x'], k['land_y'])
    res['RIDE'] = f is not None and here(c) == k['land'] and abs(player_tile(c)[0] - land[0]) <= 1 \
        and abs(player_tile(c)[1] - land[1]) <= 1
    if not res['RIDE']:
        return res, 'ride: frames %s, here %s, tile %s' % (f, here(c), player_tile(c))
    if ride_only:
        return res, ''
    settle(c, 120)
    paid = draw(c)
    res['PAY'] = ITEM_NAME.get(paid) == ITEM_NAME[c.memory.u8[CHAIN_DETAIL + 1]]
    if k['two_way']:
        res['BACK'] = tile_world(c, *land) in pads(c)
        f = ride(c, *land)
        res['BACK'] = res['BACK'] and f is not None and here(c) == (s['area'], s['room']) and \
            player_tile(c) == tuple(tile)
        f = ride(c, *tile)
        res['BACK'] = res['BACK'] and f is not None and here(c) == k['land']
        settle(c, 60)
        # the landing ? room's fight, won for real: the escape item paid
        done, note = A.drive(c, 'WAVES', k['land_site'])
        for _ in range(8):
            if release(c):
                note += ', released from a Like Like'

            if done:
                break
            # drive's own fallback stands on every ground item in turn and
            # can run out first: clear what is left, stand on the prize
            A.kill_all(c)
            run(c, 90)
            dismiss(c)
            want = {P.ITEMS[e] for e in k['escape']}
            items = [e for e in entities(c, KIND_OBJECT, 0) if e[3] in want]
            if items:
                A.teleport_to(c, items[0][4], items[0][5])
                run(c, 60)
                dismiss(c)
                note += ', escape item stood on'
            done = A.site_done(c, k['land_site'])
        if not done and SNAP:
            emu.snap(c, os.path.join(SNAP, 'unpaid.png'))
        run(c, 120)
        dismiss(c)
        steps, prog, rolled = chain(c)
        res['PAY'] = res['PAY'] and done and any(has(c, e) for e in k['escape']) and prog == 2
        passed, why = door_out(c, k['land_room'])
        res['OUT'] = passed[-1][0] in OVERWORLD and ocarina_home(c)
        return res, '%s; out %s %s' % (note, passed, why)
    res['OUT'] = ocarina_home(c)
    return res, 'landed tile %s' % (player_tile(c),)


PL_MINISH = 0x80
CENSUS = os.path.join(P.ROOT, 'build', 'portal_census.json')


def census(rom, diff, only=None):
    """`only`: re-measure these sites and merge them into the file."""
    rooms = json.load(open(ROOMS))
    out = {}
    if only is not None:
        out = {int(k): v for k, v in json.load(open(CENSUS)).items()}
    for key in sorted((k for k in rooms if k.startswith('site:')), key=lambda k: int(k.split(':')[1])):
        st = int(key.split(':')[1])
        if only is not None and st not in only:
            continue
        if sim.SITES[st]['kinds'] not in ('ANY', 'LARGE', 'SMALL') and st not in {k['land_site'] for k in sim.PORTALS}:
            continue
        c = S.boot(rom, S.KINDS['CHAIN'], a=1, b=st, c=0x40, kit=0, diff=diff, frames=300)
        settle(c, 200)
        ox, oy = origin(c)
        objs = sorted({((e[4] - ox) // 16, (e[5] - oy) // 16) for kind in (KIND_OBJECT, emu.KIND_NPC)
                       for e in entities(c, kind) if not (kind == KIND_OBJECT and e[2] in (WARP_POINT, 0))})
        minish = bool(c.memory.u32[PLAYER_STATE + 0x30] & PL_MINISH)
        out[st] = dict(room=sim.SITES[st]['roomName'], here=list(here(c)), objects=objs, minish=minish)
        print('site %3d %-44s minish %d objects %d' % (st, sim.SITES[st]['roomName'][5:], minish, len(objs)), flush=True)
        del c
    json.dump({k: out[k] for k in sorted(out)}, open(CENSUS, 'w'), indent=1)
    print('-> %s' % os.path.relpath(CENSUS, P.ROOT))
    return 0


def patience(rom, p, site, diff):
    """Prizes drawn outside the pocket: the fourth pays the escape item."""
    c = S.boot(rom, S.KINDS['CHAIN'], a=1, b=site, c=0x40 | p, kit=0, diff=diff, frames=300)
    settle(c, 200)
    for _ in range(600):
        if c.memory.u8[CHAIN_ROLLED] >= 2:
            break
        A.run(c, 1)
    A.drive(c, 'WAVES', site)
    run(c, 60)
    dismiss(c)
    got = [ITEM_NAME.get(draw(c, s6), s6) for s6 in (1, 2, 3, 4)]
    want = ITEM_NAME[c.memory.u8[CHAIN_DETAIL + 1]]
    return [g == want for g in got] == [False, False, False, True], got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rom', default=os.path.join(P.ROOT, 'tmc-d3.gba'))
    ap.add_argument('--pocket', type=int)
    ap.add_argument('--site', type=int)
    ap.add_argument('--diff', type=int, default=3)
    ap.add_argument('--sweep', action='store_true')
    ap.add_argument('--census', action='store_true')
    ap.add_argument('--only', help='with --census: these sites, merged into the file')
    a = ap.parse_args()
    # Portal A for the probe: a plain open-kind site on the mainland with a
    # portal tile (the North Hyrule Field fairy cave), or --site.
    site = a.site if a.site is not None else 0
    bad = 0
    if a.census:
        return census(a.rom, a.diff, [int(x) for x in a.only.split(',')] if a.only else None)
    if a.sweep:
        lands = {k['land_site'] for k in sim.PORTALS}
        for st in sorted(sim.PORTAL_TILES):
            if st in lands or sim.SITES[st]['kinds'] not in ('ANY', 'LARGE', 'SMALL'):
                continue
            res, note = probe_pocket(a.rom, 0, st, a.diff, ride_only=True)
            ok = all(res.values())
            bad += not ok
            print('site %3d %-44s %s  %s  %s' % (st, sim.SITES[st]['roomName'][5:], 'PASS' if ok else 'FAIL',
                                                 ' '.join('%s=%d' % kv for kv in res.items()), note), flush=True)
        print('%d sites failed' % bad)
        return 1 if bad else 0
    for p in range(len(sim.PORTALS)):
        if a.pocket is not None and p != a.pocket:
            continue
        res, note = probe_pocket(a.rom, p, site, a.diff)
        ok = all(res.values())
        bad += not ok
        print('pocket %d %-28s %s  %s  (%s)' % (p, sim.PORTALS[p]['land_room'][5:], 'PASS' if ok else 'FAIL',
                                              ' '.join('%s=%d' % kv for kv in res.items()), note))
    ok, got = patience(a.rom, 0, site, a.diff)
    bad += not ok
    print('PATIENCE %s  draws outside the pocket: %s' % ('PASS' if ok else 'FAIL', got))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())

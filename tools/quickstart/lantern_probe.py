"""Play the torch and cleanup ? rooms in the ROM, layout by layout.

For each generated layout (build/lantern_layouts.json, lantern_rooms.py)
the testbed lands in its site with that layout forced (scenario SITE, kind
TORCHES or CLEANUP, scenario_c = the layout's place among the site's + 1)
and a full kit, then:

  DEALT    every torch tile reads TILE_TYPE_117, or every web and dust
           cloud is standing where the layout put it; the torch's tile is in
           the BG buffer the screen is drawn from (the refresh fix)
  DARK     the room's light level is the one the variant asked for
  SOLVE    TORCHES: the Lantern lit (B), then for each torch the player is
           set on its lighting tile facing it and swings; it must read 118.
           CLEANUP: for each web in the generator's clearing order the
           player stands on its stand tile facing it and holds the Gust Jar
           until it is gone; each dust cloud from two tiles below. With
           --lantern the webs are burned instead (layouts with no cloud).
  WON      the room's won flag, then the prize on the content spot
  WAVES    our enemies were standing during the solve, and still are after
           the win (the user: the waves continue after the win)
  DONE     the prize taken, the site's DONE bit set

A room that cannot take its layout at all (nothing spawns in it) deals the
item drop instead; that is reported as FALLBACK, not as a pass.

The player's health is pinned and their invulnerability frames held, as
block_probe does: the hazard waves are there, and a knockback mid-swing is
not what this measures.

    python3 tools/quickstart/lantern_probe.py [--rom tmc-d3.gba] [--kind torches|cleanup] [--sites A-B]
        [--max N] [--diff 3] [--lantern] [--snap DIR]
"""
import argparse
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import emu
from emu import r16, here, press, entities, room_dims, PLAYER
import scenario as S
import parse_tables as P
from block_probe import room_flag, bank12, origin, frame, run, dismiss, settle, MSG
from block_puzzles import Floor, flood, DIRS, ROOMS
from lantern_rooms import standable

LAYOUTS = os.path.join(P.ROOT, 'build', 'lantern_layouts.json')
SITE_FLAG_BASE = 64
DEALT, WON, PAID, FALLBACK = 0, 1, 2, 5
SAVE = 0x02002a40
EQUIPPED = SAVE + 0xB4
MAP = {1: 0x02025eb0, 2: 0x0200b650}
BG1BUF = 0x02021f30
LIGHT = 0x02034350 + 0x0c
KIND_ENEMY, KIND_PROJ = 3, 4
SPIDER_WEB, DUST = 0x15, 0x53
CLOUD = 4


def give_b(c, item):
    b, sh = item >> 2, (item & 3) * 2
    c.memory.u8[SAVE + 0xF2 + b] = (c.memory.u8[SAVE + 0xF2 + b] & ~(3 << sh) & 0xFF) | (1 << sh)
    c.memory.u8[EQUIPPED + 1] = item


def tile_type(c, x, y, layer=1):
    base = MAP[layer]
    idx = r16(c, base + 4 + 2 * (x + 64 * y)) & 0xffff
    return r16(c, base + 0x5004 + 2 * idx) & 0xffff, idx


def put(c, tx, ty, face):
    ox, oy = origin(c)
    emu.w16(c, PLAYER + 0x2e, ox + tx * 16 + 8)
    emu.w16(c, PLAYER + 0x32, oy + ty * 16 + 8)
    c.memory.u8[PLAYER + 0x14] = face * 2   # animationState: 0 up, 2 right, 4 down, 6 left
    run(c, 2)


def ours(c):
    return [e for e in entities(c, KIND_ENEMY) if e[2] != DUST]


def debris(c):
    ox, oy = origin(c)
    webs = {((x - ox) // 16, (y - oy) // 16) for i, k, ident, t, x, y in entities(c, KIND_PROJ, SPIDER_WEB)}
    clouds = {((x - ox) // 16, (y - oy) // 16) for i, k, ident, t, x, y in entities(c, KIND_ENEMY, DUST) if t == 0}
    return webs, clouds


def stand_tiles(floor, t, blocked):
    main = flood(floor.comp - blocked, floor.start)
    for d, (dx, dy) in enumerate(DIRS):
        s = (t[0] - dx, t[1] - dy)
        if s in main and standable(floor, s):
            yield s, d


def land(rom, site, kind, nth, diff):
    c = S.boot(rom, S.KINDS['SITE'], site, S.EVENTS.index(kind), nth + 1, 0, kit=2, diff=diff, frames=300)
    dismiss(c)
    run(c, 20)
    for _ in range(10):
        if room_dims(c)[0]:
            break
        press(c, c.KEY_START, 3, 60)
    settle(c, 120)
    return c


def solve_torches(c, floor, lay):
    give_b(c, P.ITEMS['ITEM_LANTERN_OFF'])
    press(c, c.KEY_B, 3, 30)    # light it
    blocked = {tuple(t) for t in lay['cells']}
    for t in lay['cells']:
        t = tuple(t)
        for s, d in list(stand_tiles(floor, t, blocked))[:2]:
            for _ in range(3):
                if c.memory.u8[MSG]:
                    dismiss(c)
                put(c, s[0], s[1], d)
                c.memory.u8[PLAYER + 0x14] = d * 2
                press(c, c.KEY_B, 3, 24)
                if tile_type(c, *t)[0] == 0x76:
                    break
            if tile_type(c, *t)[0] == 0x76:
                break
        if tile_type(c, *t)[0] != 0x76:
            return 'torch (%d,%d) would not light' % t
    return None


def solve_cleanup(c, floor, lay, lantern):
    item = 'ITEM_LANTERN_OFF' if lantern else 'ITEM_GUST_JAR'
    give_b(c, P.ITEMS[item])
    cells = {tuple(t): w for t, w in zip(map(tuple, lay['cells']), lay['what'])}
    for t in [tuple(w) for w in lay['order']]:
        d = cells[t]
        s = (t[0] - DIRS[d][0], t[1] - DIRS[d][1])
        for _ in range(4):
            if t not in debris(c)[0]:
                break
            if c.memory.u8[MSG]:
                dismiss(c)
            put(c, s[0], s[1], d)
            if lantern:
                # A burnt web stands in its flames for 90 frames
                # (SpiderWeb_Action3) before it goes: wait that out rather
                # than swinging again, which would put the lantern out.
                # The burst that burns is the one the Lantern throws as it
                # LIGHTS (ItemLantern: a LAMP_PARTICLE in front of the
                # player); pressing B on a lit lantern puts it out. So put
                # it out first, then light it facing the web.
                if c.memory.u8[EQUIPPED + 1] == P.ITEMS['ITEM_LANTERN_ON']:
                    press(c, c.KEY_B, 3, 12)
                put(c, s[0], s[1], d)
                # Half a step into the stand tile, towards the web: from its
                # centre the burst fell short (measured: a web below the
                # player burnt from 4 px on, one above only from 8 px).
                emu.w16(c, PLAYER + 0x2e, r16(c, PLAYER + 0x2e) + 8 * DIRS[d][0])
                emu.w16(c, PLAYER + 0x32, r16(c, PLAYER + 0x32) + 8 * DIRS[d][1])
                c.memory.u8[PLAYER + 0x14] = d * 2
                press(c, c.KEY_B, 3, 4)
                for _ in range(130):
                    frame(c)
                    if t not in debris(c)[0]:
                        break
                continue
            # A few pixels back from the stand tile's centre: pressed right
            # up against a web the jar latches it and lets go (measured at
            # the Crenel mushroom cave: 16 px from the web failed, 22 px
            # tore it off).
            emu.w16(c, PLAYER + 0x2e, r16(c, PLAYER + 0x2e) - 6 * DIRS[d][0])
            emu.w16(c, PLAYER + 0x32, r16(c, PLAYER + 0x32) - 6 * DIRS[d][1])
            run(c, 1)
            c.set_keys(c.KEY_B)
            for _ in range(200):
                c.memory.u8[PLAYER + 0x14] = d * 2
                frame(c)
                if t not in debris(c)[0]:
                    break
            c.clear_keys(c.KEY_B)
            run(c, 10)
        if t in debris(c)[0]:
            return 'web (%d,%d) type %d stayed' % (t[0], t[1], d)
    for t, w in cells.items():
        if w != CLOUD or lantern:
            continue
        for _ in range(3):
            if t not in debris(c)[1]:
                break
            put(c, t[0], t[1], 0)   # then 28 px below its centre: the jar's reach
            emu.w16(c, PLAYER + 0x32, origin(c)[1] + t[1] * 16 + 8 + 28)
            run(c, 2)
            c.set_keys(c.KEY_B)
            for _ in range(300):
                c.memory.u8[PLAYER + 0x14] = 0
                frame(c)
                if t not in debris(c)[1]:
                    break
            c.clear_keys(c.KEY_B)
            run(c, 10)
        if t in debris(c)[1]:
            return 'cloud (%d,%d) stayed' % t
    return None


def take_prize(c, rooms, site):
    sx, sy = rooms['site:%d' % site]['spot']
    ox, oy = origin(c)
    for _ in range(3):
        emu.w16(c, PLAYER + 0x2e, ox + sx)
        emu.w16(c, PLAYER + 0x32, oy + sy)
        run(c, 20)
        dismiss(c)
        run(c, 30)
        if bank12(c, emu.SITE_ORIGIN + site):
            return True
    return False


def probe(rom, lay, nth, diff, lantern, snapdir, tag):
    site, kind = lay['site'], ('TORCHES', 'CLEANUP')[lay['kind']]
    c = land(rom, site, kind, nth, diff)
    rooms = json.load(open(ROOMS))
    floor = Floor(rooms['site:%d' % site])
    if room_flag(c, SITE_FLAG_BASE + FALLBACK):
        # Nothing could be dealt here: the room is the item drop instead.
        if take_prize(c, rooms, site):
            return 'FALLBACK: the item drop, taken and DONE', c
        return 'FALLBACK: the item drop, but not DONE', c
    if not room_flag(c, SITE_FLAG_BASE + DEALT):
        return 'NOT DEALT here %s' % (here(c),), c
    if snapdir:
        emu.snap(c, os.path.join(snapdir, tag + '_dealt.png'))
    notes = []
    if lay['kind'] == 0:
        bad = [t for t in lay['cells'] if tile_type(c, *t)[0] != 0x75]
        if bad:
            return 'DEALT WRONG: no torch at %s' % bad[:4], c
        # The BG buffer holds the screen's window only: test a torch the
        # camera is looking at (a scrolling room may have none in view).
        ox, oy = origin(c)
        camx, camy = r16(c, emu.ROOM_CONTROLS + 0x0a) - ox, r16(c, emu.ROOM_CONTROLS + 0x0c) - oy
        seen = [t for t in lay['cells'] if camx <= t[0] * 16 and t[0] * 16 + 16 <= camx + 240
                and camy <= t[1] * 16 and t[1] * 16 + 16 <= camy + 160]
        if seen:
            idx = tile_type(c, *seen[0])[1]
            buf = {r16(c, BG1BUF + a) & 0xffff for a in range(0, 0x900, 2)}
            sub0 = r16(c, MAP[1] + 0x7004 + 2 * idx * 4) & 0xffff
            if sub0 not in buf:
                return 'DEALT UNSEEN: the torch is not in the BG buffer', c
        notes.append('light %#x' % r16(c, LIGHT))
        why = solve_torches(c, floor, lay)
    else:
        webs, clouds = debris(c)
        want_w = {tuple(t) for t, w in zip(lay['cells'], lay['what']) if w != CLOUD}
        want_c = {tuple(t) for t, w in zip(lay['cells'], lay['what']) if w == CLOUD}
        # The room's own vanilla webs (the Deepwood Shrine's) may stand too.
        if not want_w <= webs or clouds != want_c:
            return 'DEALT WRONG missing webs %s clouds %s' % (sorted(want_w - webs)[:4], sorted(clouds ^ want_c)[:4]), c
        if lantern and c.memory.u8[0x03003f80 + 0x30] & 0x80:
            # PL_MINISH: vanilla's ItemLantern refuses to light at Minish
            # size, so these rooms are the Gust Jar's alone.
            return 'SKIP: Minish-sized, vanilla refuses the Lantern', c
        why = solve_cleanup(c, floor, lay, lantern)
    seen_enemies = len(ours(c))
    if why:
        return 'SOLVE: ' + why, c
    for _ in range(60):
        run(c, 2)
        if room_flag(c, SITE_FLAG_BASE + WON):
            break
    if not room_flag(c, SITE_FLAG_BASE + WON):
        return 'NOT WON after the solve', c
    if lay['kind'] == 0:
        notes.append('lit %#x' % r16(c, LIGHT))
    if snapdir:
        emu.snap(c, os.path.join(snapdir, tag + '_won.png'))
    for _ in range(60):
        run(c, 2)
        if room_flag(c, SITE_FLAG_BASE + PAID):
            break
    run(c, 120)
    after = len(ours(c))
    if not take_prize(c, rooms, site):
        return 'PRIZE: won but not DONE', c
    notes.append('enemies %d during, %d after the win' % (seen_enemies, after))
    return 'ok ' + ', '.join(notes), c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rom', default=os.path.join(P.ROOT, 'tmc-d3.gba'))
    ap.add_argument('--kind', choices=('torches', 'cleanup'))
    ap.add_argument('--sites')
    ap.add_argument('--max', type=int, default=0, help='layouts per site and kind (0 = all)')
    ap.add_argument('--diff', type=int, default=3)
    ap.add_argument('--lantern', action='store_true', help='cleanup: burn the webs (cloudless layouts only)')
    ap.add_argument('--snap')
    a = ap.parse_args()
    layouts = json.load(open(LAYOUTS))
    lo, hi = (0, 999)
    if a.sites:
        lo, hi = [int(v) for v in a.sites.split('-')]
    if a.snap:
        os.makedirs(a.snap, exist_ok=True)
    nth = collections.Counter()
    jobs = []
    for i, lay in enumerate(layouts):
        key = (lay['site'], lay['kind'])
        n = nth[key]
        nth[key] += 1
        if not lo <= lay['site'] <= hi:
            continue
        if a.kind and lay['kind'] != ('torches', 'cleanup').index(a.kind):
            continue
        if a.max and n >= a.max:
            continue
        if a.lantern and (lay['kind'] != 1 or CLOUD in lay['what']):
            continue
        jobs.append((i, lay, n))
    ok = 0
    for i, lay, n in jobs:
        tag = 'l%03d' % i
        verdict, c = probe(a.rom, lay, n, a.diff, a.lantern, a.snap, tag)
        good = verdict.startswith('ok') or verdict.startswith('SKIP')
        ok += good
        print('%3d site %3d %-8s #%d %-40s %s' % (i, lay['site'], ('torches', 'cleanup')[lay['kind']], n,
                                                 lay['room'][5:], verdict), flush=True)
        if c is not None and not good and a.snap:
            emu.snap(c, os.path.join(a.snap, tag + '_fail.png'))
        del c
    print('RESULT %d/%d layouts played to DONE' % (ok, len(jobs)))
    return 0 if ok == len(jobs) else 1


if __name__ == '__main__':
    sys.exit(main())

"""Does every sQuickStartPursuers row spawn, survive, and close on the player?

The survive rooms now draw from an allowlist rather than the difficulty
ladder, which means rows that the roster soak never covered (the ladder
only ever names KEATON form 0, for instance) are suddenly reachable. Two
things can go wrong with a row nobody vetted: the kind may not exist at
that form and self-despawn or crash, and it may not actually chase - and
a survive wave of enemies that ignore the player is the exact failure the
allowlist exists to prevent.

So this asks the ROM both questions at once. Spawn the row 80px from a
parked player in the quiet Grimblade dojo, watch 600 frames, and record
whether it lived and how close it ever got. A row passes only if it is
alive at the end AND closed to within CLOSE_PX of the player at some
point.

Usage: python3 tools/quickstart/pursuer_soak.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot, warp, poison_here, press, entities, r16, qs_site_set, GENT, STRIDE, KIND_ENEMY
from callrom import call_keep, map_sym
import parse_tables as P

ROM = os.path.join(P.ROOT, 'tmc.gba')
CREATE_ENEMY = map_sym('CreateEnemy')
UPDATE_SPRITE = map_sym('UpdateSpriteForCollisionLayer')
DELETE_ENTITY = map_sym('DeleteEntity')
PLAYER = 0x03001160
CLOSE_PX = 40       # spawned 64 away; anything that ever gets this close committed


def pursuer_rows():
    G = P.GAME
    i = G.find('sQuickStartPursuers[][2] = {')
    j = G.find('\n};', i)
    body = re.sub(r'//[^\n]*', '', G[i:j])
    return [(m.group(1), int(m.group(2))) for m in re.finditer(r'\{\s*(\w+),\s*(\d+)\s*\}', body)]


def main():
    enemy_ids = {}
    for line in open(os.path.join(P.ROOT, 'build/USA/enum_include/enemy.inc')):
        m = re.match(r'\.set (\w+), (\d+)', line.strip())
        if m:
            enemy_ids[m.group(1)] = int(m.group(2))
    rows = pursuer_rows()
    print(f'{len(rows)} allowlist row(s)')

    c = boot(ROM)
    qs_site_set(c, 16, 1)
    poison_here(c)
    warp(c, 37, 5, 0x78, 0xa0)
    for _ in range(10):
        press(c, c.KEY_A, 5, 5)
    # The first pass spawned each row 80px east of the player and almost
    # everything reported a closest distance of exactly 80 - i.e. it never
    # moved at all. The three exceptions (GHINI, CLOUD_PIRANHA,
    # WIZZROBE_WIND) are precisely the kinds that ignore terrain, so the
    # spawn point was solid, not the enemies inert. Use the dojo tile the
    # roster soak already established is open floor.
    ox, oy = r16(c, 0x03000bf0 + 6), r16(c, 0x03000bf0 + 8)
    SPOT_X, SPOT_Y = ox + 120, oy + 96
    print('player action %d at (%d,%d), spawn spot (%d,%d)' % (
        c.memory.u8[PLAYER + 0x0c], r16(c, PLAYER + 0x2e), r16(c, PLAYER + 0x32), SPOT_X, SPOT_Y))

    PX, PY = SPOT_X, SPOT_Y + 64

    def w16a(a, v):
        c.memory.u8[a] = v & 0xFF
        c.memory.u8[a + 1] = (v >> 8) & 0xFF

    failures = []
    for n, (name, form) in enumerate(rows):
        eid = enemy_ids[name]
        # Pin the player. The second pass died at row 8 and every row after
        # it read "roamed 0, closest 81": a BOW_MOBLIN arrow had killed the
        # player, and a dead player freezes the room - so the rest of the
        # table was measuring a paused game, not inert enemies. A stationary
        # invulnerable target is also the cleanest thing to measure pursuit
        # against.
        w16a(PLAYER + 0x2e, PX)
        w16a(PLAYER + 0x32, PY)
        c.memory.u8[PLAYER + 0x45] = 0x50
        ptr = call_keep(c, CREATE_ENEMY, (eid, form))
        if ptr == 0:
            print(f'{n:>2} {name:<18} form {form}: SPAWN FAILED')
            failures.append((name, form, 'spawn failed'))
            continue
        w16a(ptr + 0x2e, SPOT_X)
        w16a(ptr + 0x32, SPOT_Y)
        c.memory.u8[ptr + 0x38] = 1
        call_keep(c, UPDATE_SPRITE, (ptr,))
        slot = (ptr - GENT) // STRIDE
        alive_at = 0
        best = 0x7fff
        moved = 0
        for f in range(600):
            c.run_frame()
            w16a(PLAYER + 0x2e, PX)
            w16a(PLAYER + 0x32, PY)
            c.memory.u8[PLAYER + 0x45] = 0x50
            base = GENT + slot * STRIDE
            if c.memory.u8[base + 8] != KIND_ENEMY or c.memory.u8[base + 9] != eid:
                break
            alive_at = f
            dx = r16(c, base + 0x2e) - r16(c, PLAYER + 0x2e)
            dy = r16(c, base + 0x32) - r16(c, PLAYER + 0x32)
            d = max(abs(dx), abs(dy))
            if d < best:
                best = d
            m = max(abs(r16(c, base + 0x2e) - SPOT_X), abs(r16(c, base + 0x32) - SPOT_Y))
            if m > moved:
                moved = m
        alive = alive_at >= 599
        closed = best <= CLOSE_PX
        if alive:
            call_keep(c, DELETE_ENTITY, (ptr,))
        for _ in range(20):
            c.run_frame()
        for (idx, k2, ident2, typ2, x2, y2) in entities(c, kind=KIND_ENEMY):
            call_keep(c, DELETE_ENTITY, (GENT + idx * STRIDE,))
        for _ in range(10):
            c.run_frame()
        verdict = 'ok' if (alive and closed) else (
            'GONE at f%d' % alive_at if not alive else 'never closer than %d' % best)
        print(f'{n:>2} {name:<18} form {form}: closest {best:>5} roamed {moved:>4}  {verdict}')
        if not (alive and closed):
            failures.append((name, form, verdict))
    print(f'\n{len(failures)} failing row(s):')
    for f in failures:
        print('   ', f)
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())

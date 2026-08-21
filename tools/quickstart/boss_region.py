"""Vet a region for the boss allowlist (QuickStartRegionAllowsBoss).

Per the roadmap, a region gets bosses only after someone has watched one
work there. This is that watch, mechanized, per candidate room:

  1. ENGAGEMENT: spawn the family at the region's reward spot exactly as
     QuickStartSpawnRegionWave would and confirm the intro finishes and
     the fight actually engages (the family hops after the player). The
     one non-obvious prerequisite: DISMISS ANY OPEN TEXTBOX first. An
     Ezlo hint left on screen freezes the boss's whole stage machine, and
     a probe that never presses A measures a paused game while the
     player can still walk - an invisible, inert, sword-carvable stack
     that looks exactly like "the boss doesn't work in this room".
  2. FULL FIGHT: weaken the fightable pieces to 1 hp (deaths still travel
     the real damage pipeline) and drive the player into the fight until
     no piece remains. A mid-fight screenshot lands next to the report.
  3. SEAM SCROLL MID-SPAWN: respawn and immediately walk the player over
     the nearest seam during the intro - the exact move that locked
     Eastern Hills South - then confirm the game stays responsive.

Usage: python3 tools/quickstart/boss_region.py ROOM_NAME [shot.png] [--dual]

--dual spawns TWO families for step 2 (the #125 case): both are fought
down together, so their death sequences overlap.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot, warp, here, poison_here, press, entities, KIND_ENEMY, GENT, STRIDE, r16, snap
from callrom import call_keep
import parse_tables as P

ROM = os.path.join(P.ROOT, 'tmc.gba')
CREATE_ENEMY = 0x0804b160
UPDATE_SPRITE = 0x08016ea8
PLAYER = 0x03001160
GSAVE = 0x02002a40
CHUCHU_BOSS = next(int(m.group(1)) for m in
                   (re.match(r'\.set CHUCHU_BOSS, (\d+)', l.strip())
                    for l in open(os.path.join(P.ROOT, 'build/USA/enum_include/enemy.inc'))) if m)


def w16a(c, a, v):
    c.memory.u8[a] = v & 0xFF
    c.memory.u8[a + 1] = (v >> 8) & 0xFF


def clear_normals(c):
    for (idx, k, ident, typ, x, y) in entities(c, kind=KIND_ENEMY):
        if ident != CHUCHU_BOSS:
            c.memory.u8[GENT + idx * STRIDE + 8] = 0


def pieces(c):
    return [(idx, typ, c.memory.u8[GENT + idx * STRIDE + 0x45], x, y)
            for (idx, k, ident, typ, x, y) in entities(c, kind=KIND_ENEMY) if ident == CHUCHU_BOSS]


def in_room(c, x, y):
    ox, oy = r16(c, 0x03000bf0 + 6), r16(c, 0x03000bf0 + 8)
    w, h = r16(c, 0x03000bf0 + 0x1e), r16(c, 0x03000bf0 + 0x20)
    return ox <= x < ox + w and oy <= y < oy + h


def heal(c):
    c.memory.u8[GSAVE + 0xA8 + 0x02] = 40


def enter(c, region):
    poison_here(c)
    warp(c, region['area'], region['room'], region['entrance'][0], region['entrance'][1])
    for _ in range(240):
        c.run_frame()
    for _ in range(6):
        press(c, c.KEY_A, 4, 4)  # the textbox rule (see module docstring)
    clear_normals(c)


def spawn_family(c, x, y, settle=120):
    ox, oy = r16(c, 0x03000bf0 + 6), r16(c, 0x03000bf0 + 8)
    ptr = call_keep(c, CREATE_ENEMY, (CHUCHU_BOSS, 0))
    if ptr == 0:
        return None
    w16a(c, ptr + 0x2e, ox + x)
    w16a(c, ptr + 0x32, oy + y)
    c.memory.u8[ptr + 0x1d] = 1
    call_keep(c, UPDATE_SPRITE, (ptr,))
    for _ in range(settle):
        c.run_frame()
    clear_normals(c)
    return ptr


def wait_engaged(c, frames=2400):
    """The intro is done when the family's pieces MOVE. ~1000 frames from
    spawn in a hint-free room."""
    ref = {p[0]: (p[3], p[4]) for p in pieces(c)}
    for f in range(0, frames, 60):
        for _ in range(60):
            heal(c)
            c.run_frame()
        now = {p[0]: (p[3], p[4]) for p in pieces(c)}
        for idx, pos in now.items():
            if idx in ref and ref[idx] != pos and abs(ref[idx][1] - pos[1]) > 4:
                return f
    return -1


def drive_fight(c, frames, shot=None, shot_at=300):
    start_room = here(c)
    for f in range(frames):
        if here(c) != start_room:
            print('  (driver crossed into', here(c), 'at frame', f, ')')
            return -2
        ps = [p for p in pieces(c) if p[2] > 0 and in_room(c, p[3], p[4])]
        if not ps:
            return f
        heal(c)
        px, py = r16(c, PLAYER + 0x2e), r16(c, PLAYER + 0x32)
        tx, ty = min(((abs(p[3] - px) + abs(p[4] - py), p[3], p[4]) for p in ps))[1:]
        dist = abs(tx - px) + abs(ty - py)
        k = 0
        if dist < 26:
            # STANDOFF: standing inside the boss gets the player swallowed,
            # and the swallow's spit-out has no arena to respawn into out
            # here - measured, it dumped the player at world (0,0) in a
            # different room. A human fights from sword range; so does this.
            if abs(tx - px) > 2:
                k |= c.KEY_LEFT if tx > px else c.KEY_RIGHT
            if abs(ty - py) > 2:
                k |= c.KEY_UP if ty > py else c.KEY_DOWN
        else:
            if abs(tx - px) > 6:
                k |= c.KEY_RIGHT if tx > px else c.KEY_LEFT
            if abs(ty - py) > 6:
                k |= c.KEY_DOWN if ty > py else c.KEY_UP
        if (f // 12) % 2 == 0 and dist < 64:
            k |= c.KEY_B | c.KEY_A
        c.set_keys(k)
        c.run_frame()
        c.clear_keys(k)
        # Containment by teleport: a chuchu slam's knockback outruns any
        # steering rule, and the driver, not the game, is what's corrected.
        ox, oy = r16(c, 0x03000bf0 + 6), r16(c, 0x03000bf0 + 8)
        w, h = r16(c, 0x03000bf0 + 0x1e), r16(c, 0x03000bf0 + 0x20)
        nx = min(max(px, ox + 48), ox + w - 48)
        ny = min(max(py, oy + 48), oy + h - 48)
        if (nx, ny) != (px, py):
            w16a(c, PLAYER + 0x2e, nx)
            w16a(c, PLAYER + 0x32, ny)
        if shot and f == shot_at:
            snap(c, shot)
        if f % 600 == 599:
            clear_normals(c)
    return -1


def main():
    room_name = sys.argv[1]
    shot = next((a for a in sys.argv[2:] if not a.startswith('--')), None)
    dual = '--dual' in sys.argv
    region = next(r for r in P.region_pool() if r['roomName'] == room_name)
    rx, ry = region['reward']

    c = boot(ROM)
    enter(c, region)
    ok_room = here(c) == (region['area'], region['room'])
    fams = 2 if dual else 1
    for fam in range(fams):
        if spawn_family(c, rx + (fam * 96 - 48 if dual else 0), ry) is None:
            print('spawn failed')
            return 1
    ox, oy = r16(c, 0x03000bf0 + 6), r16(c, 0x03000bf0 + 8)
    w16a(c, PLAYER + 0x2e, ox + rx + 8)
    w16a(c, PLAYER + 0x32, oy + ry + 56)
    t_eng = wait_engaged(c)
    print(f'{room_name}: landed {ok_room}, {fams} family/ies of {len(pieces(c))} piece(s), '
          f'engaged {"at f%d" % t_eng if t_eng >= 0 else "NEVER"}')
    if t_eng < 0:
        return 1
    for idx, typ, hp, x, y in pieces(c):
        if hp > 1 and in_room(c, x, y):
            c.memory.u8[GENT + idx * STRIDE + 0x45] = 1
    t = drive_fight(c, 12000, shot=shot)
    left = [pc for pc in pieces(c) if pc[2] > 0 and in_room(c, pc[3], pc[4])]
    fight_ok = t >= 0 and not left
    print(f'  full fight: {"cleared in %d frames" % t if t >= 0 else "DID NOT CLEAR"}; '
          f'{len(left)} live piece(s) remain -> {"ok" if fight_ok else "FAIL"}')

    c = boot(ROM)
    enter(c, region)
    # Find genuinely open crossing columns first - marching blind from the
    # entrance reads a fence as a lockup (Eastern Hills North failed that
    # way while perfectly healthy).
    from emu import coll_at
    w, h = r16(c, 0x03000bf0 + 0x1e), r16(c, 0x03000bf0 + 0x20)
    tw, th = w // 16, h // 16
    edges = []
    for tx in range(tw):
        if coll_at(c, tx, th - 1) == 0 and coll_at(c, tx, th - 2) == 0:
            edges.append((tx * 16 + 8, h - 40, c.KEY_DOWN))
        if coll_at(c, tx, 0) == 0 and coll_at(c, tx, 1) == 0:
            edges.append((tx * 16 + 8, 40, c.KEY_UP))
    for ty in range(th):
        if coll_at(c, 0, ty) == 0 and coll_at(c, 1, ty) == 0:
            edges.append((40, ty * 16 + 8, c.KEY_LEFT))
        if coll_at(c, tw - 1, ty) == 0 and coll_at(c, tw - 2, ty) == 0:
            edges.append((w - 40, ty * 16 + 8, c.KEY_RIGHT))
    spawn_family(c, rx, ry, settle=60)
    ox, oy = r16(c, 0x03000bf0 + 6), r16(c, 0x03000bf0 + 8)
    for ex, ey, k in edges[:6]:
        w16a(c, PLAYER + 0x2e, ox + ex)
        w16a(c, PLAYER + 0x32, oy + ey)
        start = here(c)
        c.set_keys(k)
        for _ in range(300):
            heal(c)
            c.run_frame()
            if here(c) != start:
                break
        c.clear_keys(k)
        if here(c) != start:
            break
    moved_out = here(c) != (region['area'], region['room'])
    p0 = (r16(c, PLAYER + 0x2e), r16(c, PLAYER + 0x32))
    c.set_keys(c.KEY_DOWN)
    for _ in range(60):
        heal(c)
        c.run_frame()
    c.clear_keys(c.KEY_DOWN)
    responsive = p0 != (r16(c, PLAYER + 0x2e), r16(c, PLAYER + 0x32))
    print(f'  seam scroll mid-spawn: crossed={moved_out} into {here(c)}, responsive={responsive} '
          f'-> {"ok" if (moved_out and responsive) else "FAIL"}')
    return 0 if (fight_ok and moved_out and responsive) else 1


if __name__ == '__main__':
    sys.exit(main())

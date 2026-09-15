"""The seven-region overworld ring: every crossing, both ways, plus the walls.

The ring (Castle Garden, North Hyrule Field, Lon Lon Ranch, Eastern Hills,
South Hyrule Field, Western Wood, Trilby Highlands) circles the missing
Hyrule Town. Travel between ring rooms is free and vanilla-shaped; the two
"town bridge" borders (transitions.c) stitch the gap the town leaves, and
every border out of the ring is compiled away under QUICKSTART.

This walks each crossing at a known-good coordinate (found by sweeping the
seams once; see the CROSSINGS table) and each blocked edge, and reports
PASS/FAIL. Run it after anything that touches transitions.c, the containment
functions, or the ring rooms' collision.

Two probe lessons baked in, both of which produced false "broken" results
before they were learned:
  - a textbox blocks ALL input, and entering a region can pop an Ezlo hint -
    every warp is followed by a burst of A presses;
  - SHF's west edge really is walled in vanilla (Western Wood is entered via
    Trilby), and SHF's east edge opens into Eastern Hills NORTH, not South -
    the south rooms' west edges are vanilla walls too.

Usage: python3 tools/quickstart/ring.py [seed]
"""
import sys

sys.path.insert(0, __file__.rsplit('/', 1)[0])
from emu import here, warp
from seed import boot_pinned

AREA = 3
ROOMS = {'WW-S': 0, 'SHF': 1, 'EH-S': 2, 'EH-C': 3, 'EH-N': 4,
         'LLR': 5, 'NHF': 6, 'TRIL': 7, 'WW-N': 8, 'WW-C': 9}
NAMES = {v: k for k, v in ROOMS.items()}
CG_AREA, CG_ROOM = 7, 0

# (label, from(area,room), local x, y, direction, expected(area,room))
# Local coordinates are the walk's start, a few tiles inside the edge, on
# ground verified walkable by the original seam sweep.
CROSSINGS = [
    ('CG -> NHF (border)',    (7, 0), 504, 500, 'KEY_DOWN',  (3, 6)),
    ('NHF -> CG (door)',      (3, 6), 504, 70,  'KEY_UP',    (7, 0)),
    ('NHF -> SHF (bridge)',   (3, 6), 504, 760, 'KEY_DOWN',  (3, 1)),
    ('SHF -> NHF (bridge)',   (3, 1), 504, 40,  'KEY_UP',    (3, 6)),
    ('LLR -> TRIL (bridge)',  (3, 5), 40, 552,  'KEY_LEFT',  (3, 7)),
    ('TRIL -> LLR (bridge)',  (3, 7), 440, 552, 'KEY_RIGHT', (3, 5)),
    ('SHF -> EH-N (seam)',    (3, 1), 984, 120, 'KEY_RIGHT', (3, 4)),
    ('EH-N -> SHF (seam)',    (3, 4), 24, 424,  'KEY_LEFT',  (3, 1)),
    ('EH-N -> EH-C (seam)',   (3, 4), 216, 504, 'KEY_DOWN',  (3, 3)),
    ('EH-C -> EH-N (seam)',   (3, 3), 216, 40,  'KEY_UP',    (3, 4)),
    ('EH-C -> EH-S (seam)',   (3, 3), 168, 216, 'KEY_DOWN',  (3, 2)),
    ('EH-S -> EH-C (seam)',   (3, 2), 168, 40,  'KEY_UP',    (3, 3)),
    ('EH-N -> LLR (seam)',    (3, 4), 312, 40,  'KEY_UP',    (3, 5)),
    ('LLR -> EH-N (seam)',    (3, 5), 312, 920, 'KEY_DOWN',  (3, 4)),
    # x inside the seam's real open corridor (tiles 21-23 = x 336-383; the
    # measured collision row at tile y 59 is wall everywhere else). The old
    # 312 sat ON wall and only ever crossed via corner-sliding, which is
    # start-position-sensitive - it wedged when this session's RNG-stream
    # changes moved the room's obstacles, and read as a broken seam.
    ('TRIL -> WW-N (seam)',   (3, 7), 360, 920, 'KEY_DOWN',  (3, 8)),
    ('WW-N -> TRIL (seam)',   (3, 8), 312, 40,  'KEY_UP',    (3, 7)),
    ('WW-N -> WW-C (seam)',   (3, 8), 264, 600, 'KEY_DOWN',  (3, 9)),
    ('WW-C -> WW-N (seam)',   (3, 9), 24, 40,   'KEY_UP',    (3, 8)),
    ('WW-C -> WW-S (seam)',   (3, 9), 264, 120, 'KEY_DOWN',  (3, 0)),
    ('WW-S -> WW-C (seam)',   (3, 0), 312, 40,  'KEY_UP',    (3, 9)),
]

# (label, from(area,room), local x, y, direction) - must NOT leave the room.
BLOCKED = [
    ('LLR north (Veil Falls)',    (3, 5), 360, 40, 'KEY_UP'),
    ('LLR east (Lake Hylia)',     (3, 5), 680, 480, 'KEY_RIGHT'),
    ('NHF east (Veil Falls)',     (3, 6), 968, 200, 'KEY_RIGHT'),
    ('NHF west (Royal Valley)',   (3, 6), 40, 300, 'KEY_LEFT'),
    ('TRIL west (Mt Crenel)',     (3, 7), 40, 700, 'KEY_LEFT'),
    ('TRIL north (Royal Valley)', (3, 7), 240, 40, 'KEY_UP'),
    ('EH-S east (Minish Woods)',  (3, 2), 440, 100, 'KEY_RIGHT'),
    ('EH-N east (Minish Woods)',  (3, 4), 440, 270, 'KEY_RIGHT'),
    ('WW-N west (Castor Wilds)',  (3, 8), 40, 300, 'KEY_LEFT'),
]


# gSave.stats.health - pinned to full for the whole walk. The free-roam
# structure spawns waves in EVERY region now, so a probe that just walks
# through them takes hits; one death ends the session's usefulness (the
# game-over screen eats every later warp) and shows up as a cascade of
# warp-bounced results, which is exactly how it was found.
HEALTH = 0x02002a40 + 0xA8 + 2


def attempt(c, src, lx, ly, key, frames=240):
    warp(c, src[0], src[1], lx, ly, frames=180)
    if here(c) != src:
        return ('warp-bounced', here(c))
    for _ in range(90):
        c.memory.u8[HEALTH] = c.memory.u8[HEALTH + 1]
        c.set_keys(c.KEY_A)
        c.run_frame()
        c.clear_keys(c.KEY_A)
        c.run_frame()
    k = getattr(c, key)
    for _ in range(frames):
        c.memory.u8[HEALTH] = c.memory.u8[HEALTH + 1]
        c.set_keys(k)
        c.run_frame()
        if here(c) != src:
            c.clear_keys(k)
            for _ in range(90):
                c.run_frame()
            return ('crossed', here(c))
    c.clear_keys(k)
    return ('stayed', src)


def main(argv):
    sd = int(argv[0], 0) if argv else 0x1
    c = boot_pinned('tmc.gba', sd)
    fails = 0
    for label, src, lx, ly, key, want in CROSSINGS:
        # Two attempts: the walk happens through live waves now, and a
        # well-timed knockback can stall one try without the seam being
        # closed. A wall stays a wall on both attempts.
        st, got = attempt(c, src, lx, ly, key)
        if not (st == 'crossed' and got == want):
            st, got = attempt(c, src, lx, ly, key)
        ok = st == 'crossed' and got == want
        fails += 0 if ok else 1
        print(f'  [{"PASS" if ok else "FAIL"}] {label:24s} -> {st} {got}')
    for label, src, lx, ly, key in BLOCKED:
        st, got = attempt(c, src, lx, ly, key, frames=200)
        ok = st == 'stayed'
        fails += 0 if ok else 1
        print(f'  [{"PASS" if ok else "FAIL"}] wall {label:26s} -> {st} {got}')
    print(('OK' if fails == 0 else 'FAILED') + f': {fails} failure(s)')
    return 0 if fails == 0 else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

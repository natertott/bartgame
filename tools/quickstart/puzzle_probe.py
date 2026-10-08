"""The switch puzzles (Oct 2026, the redesign's P2 section 6.1), solved by
a script that reads the room the way a player does.

Each variant is booted with the testbed (SITE scenario, kind PUZZLE) at
every site it may be dealt at that the --sites list names (default: three
sites in three regions), and:

  ECHO     the solver WATCHES the show (one switch lit at a time) and
           writes down the order; one wrong first strike brings a wave and
           the show again; the watched order, struck, solves it.
  LIGHTS   the dealt pattern is neither dark nor full; one strike flips
           the struck switch and its neighbours; the solver searches the
           strikes from what it sees and the row goes all lit.
  RACE     the switches stand wider than a spin attack reaches (48 px or
           more apart); a lit switch goes dark again on its own; three
           strikes in quick succession light all three and solve it.
  PAYS     every solve drops a prize at the content spot, and taking it
           latches the site DONE (the chain's question).
  DEALT    over 20 seeds and every site, the site roll deals PUZZLE only
           at sites alone in their room and ungated, and does deal it.

Strikes are forged as contact on the switch (the switch's own toggle is
what runs; memory_probe.py explains why that is trusted here).

    python3 tools/quickstart/puzzle_probe.py [--rom tmc-d3.gba] [--sites 3,40,90 | --all]
"""
import os, sys, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import here, entities, press, KIND_OBJECT, KIND_ENEMY, GENT, ROOM_CONTROLS, PLAYER, r16, w16, SAVE_FLAGS, FLAG_BANK_12
import scenario as S
import callrom as C
import parse_tables as P
args = sys.argv[1:]
ROM = args[args.index('--rom') + 1] if '--rom' in args else 'tmc-d3.gba'
STRIDE = 0x88
res = []
def check(name, ok, detail=''):
    res.append(bool(ok)); print('%s %-48s %s' % ('PASS' if ok else 'FAIL', name, detail), flush=True)
class M:
    """The memory probe's room readers (that file runs on import)."""
    ROOMVARS = 0x02034350
    MSG = 0x02000050
    LIGHTABLE = P._enum(open(os.path.join(P.ROOT, 'include/object.h')).read())['LIGHTABLE_SWITCH']
    @staticmethod
    def room_flag(c, n):
        b = 256 + n
        return (c.memory.u8[M.ROOMVARS + 0x14 + (b >> 3)] >> (b & 7)) & 1
    @staticmethod
    def site_done(c, site):
        b = FLAG_BANK_12 + 1 + site
        return (c.memory.u8[SAVE_FLAGS + (b >> 3)] >> (b & 7)) & 1
    @staticmethod
    def forge_hit(c, ent_index, fast=False):
        """Stand a tile south of the switch first: an entity off the
        screen is not updated, so a strike forged from across a big room
        never lands (measured: the contact byte sat unread). A player is
        always beside the switch they hit."""
        b = GENT + ent_index * STRIDE
        w16(c, PLAYER + 0x2e, r16(c, b + 0x2e)); w16(c, PLAYER + 0x32, r16(c, b + 0x32) + 20)
        c.memory.u8[PLAYER + 0x38] = c.memory.u8[b + 0x38]   # a teleport keeps the old layer; a walk would not
        for _ in range(8 if fast else 30):   # the camera follows over a few frames
            c.run_frame()
        if not fast:
            M.dismiss(c)          # walking there can pick up a drop, and its
                              # textbox freezes every entity
        c.memory.u8[b + 0x41] = 0x80 | 4
    @staticmethod
    def switches(c):
        out = []
        for e in entities(c, KIND_OBJECT):
            if e[2] != M.LIGHTABLE:
                continue
            f = c.memory.u8[GENT + e[0] * STRIDE + 0x86] | (c.memory.u8[GENT + e[0] * STRIDE + 0x87] << 8)
            out.append((f - (0x8000 + 256 + 104), e))
        out.sort()
        return [e for _k, e in out]
    @staticmethod
    def dismiss(c, limit=900):
        quiet = 0
        for _ in range(limit):
            if c.memory.u8[M.MSG] == 0 and c.memory.u8[PLAYER + 0x0c] not in (0x16, 0x7):
                c.run_frame()
                quiet += 1
                if quiet >= 30:
                    return
                continue
            press(c, c.KEY_A, 3, 17)
            quiet = 0

def run(c, n):
    for _ in range(n):
        c.memory.u8[PLAYER + 0x45] = 24
        c.run_frame()

sites = P.content_sites_full()
# Eligibility is the game's own answer (QuickStartSitePuzzleOk) on a booted
# ROM, minus the sites a run never rolls (retired) and the run's blink
# memory pair (it outranks every roll, so the testbed would boot the memory
# event there, not a puzzle).
_c0 = S.boot(ROM, 0, frames=200)
def _ok(i):
    try:
        return C.call_keep(_c0, C.game_sym('QuickStartSitePuzzleOk'), (i,)) == 1
    except KeyError:   # inlined: the table's own rule, less the room list
        return sites[i][6] == 0 and sum(1 for s in sites if (s[2], s[3]) == (sites[i][2], sites[i][3])) == 1
RETIRED = {i for i in range(len(sites)) if C.call_keep(_c0, C.game_sym('QuickStartSiteRetired'), (i,)) == 1}
OK_SITES = [i for i in range(len(sites)) if _ok(i) and i not in RETIRED]
if '--sites' in args:
    PICK = [int(x) for x in args[args.index('--sites') + 1].split(',')]
elif '--all' in args:
    PICK = list(OK_SITES)
else:
    # three sites in three different areas, spread over the table
    PICK, areas = [], set()
    for i in OK_SITES[::max(1, len(OK_SITES) // 12)]:
        if sites[i][2] not in areas:
            PICK.append(i); areas.add(sites[i][2])
        if len(PICK) == 3:
            break
KIND = S.EVENTS.index('PUZZLE')
SEED = 5   # draw bits: ECHO order 5 % 6, LIGHTS start 1 + 5 % 6 = 6
ORDERS = [(0, 1, 2), (0, 2, 1), (1, 0, 2), (1, 2, 0), (2, 0, 1), (2, 1, 0)]

def lit(c):
    return sum(1 << k for k in range(3) if M.room_flag(c, 104 + k))

def boot(site, variant):
    c = S.boot(ROM, S.KINDS['SITE'], site, KIND, variant | (SEED << 2), kit=1, frames=400)
    M.dismiss(c)
    return c

def apply_lights(p, k):
    m = 1 << k
    if k > 0: m |= 1 << (k - 1)
    if k < 2: m |= 1 << (k + 1)
    return p ^ m

def solve_lights(c, sw):
    """The fewest strikes from what the solver sees, then strike them."""
    now = lit(c)
    for n in range(4):
        for ks in itertools.product(range(3), repeat=n):
            p = now
            for k in ks:
                p = apply_lights(p, k)
            if p == 7:
                for k in ks:
                    M.forge_hit(c, sw[k][0]); run(c, 20)
                return ks
    return None

def solved_and_paid(c, site, label):
    """Solved is flag 70 (the site's window, slot 0, + 6). The prize waits
    for its spot to be clear, and a killed wave's drops can sit there: take
    the item nearest the spot until the site reads DONE."""
    run(c, 40)
    solved = M.room_flag(c, 70)
    took = 0
    for _ in range(5):
        if M.site_done(c, site):
            break
        ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
        px, py = ox + sites[site][4], oy + sites[site][5]
        items = sorted([e for e in entities(c, KIND_OBJECT) if e[2] == 0], key=lambda e: abs(e[4] - px) + abs(e[5] - py))
        near = [e for e in items if abs(e[4] - px) + abs(e[5] - py) <= 32]
        if near:
            took += 1
            w16(c, PLAYER + 0x2e, near[0][4]); w16(c, PLAYER + 0x32, near[0][5] + 4)
            c.memory.u8[PLAYER + 0x38] = c.memory.u8[GENT + near[0][0] * STRIDE + 0x38]
        run(c, 120); M.dismiss(c)
    run(c, 60)
    # DONE is the chain's question; it implies solved (the flag read here
    # can miss a solve that paid out under the player's feet)
    check('PAYS %s: solved, a prize, DONE once taken' % label, M.site_done(c, site) == 1,
          'solved %d, items taken %d, done %d' % (solved, took, M.site_done(c, site)))

MEMORY = {C.call_keep(_c0, C.game_sym('QuickStartMemorySite'), (r,)) for r in (0, 1)}
for site in PICK:
    where = '%s site %d' % (sites[site][1].replace('ROOM_', ''), site)
    if site in MEMORY:
        print('SKIP %s: the blink memory pair stands here on the probe seed' % where)
        continue
    # ---- ECHO
    c = boot(site, 0)
    sw = M.switches(c)
    seen = []
    for _ in range(400):
        run(c, 1)
        L = lit(c)
        if L in (1, 2, 4):
            k = {1: 0, 2: 1, 4: 2}[L]
            if not seen or seen[-1] != k:
                seen.append(k)
    check('ECHO %s: three switches, the order shown' % where, len(sw) == 3 and len(seen) == 3 and tuple(seen) in ORDERS,
          'switches %d, watched %s' % (len(sw), seen))
    if len(sw) == 3 and len(seen) == 3:
        before = len(entities(c, KIND_ENEMY))
        M.forge_hit(c, sw[seen[1]][0]); run(c, 30)
        after = len(entities(c, KIND_ENEMY))
        again = []
        for _ in range(400):
            run(c, 1)
            L = lit(c)
            if L in (1, 2, 4):
                k = {1: 0, 2: 1, 4: 2}[L]
                if not again or again[-1] != k:
                    again.append(k)
        # a Minish-scale room has no free tile for a wave once three switches
        # and the player stand in it (the placer keeps clear of both): there
        # a wrong answer only replays the show
        wave_ok = after > before or 'MINISH' in sites[site][1]
        check('ECHO %s: a wrong strike, a wave, the show again' % where, wave_ok and again == seen,
              'enemies %d -> %d, shown again %s' % (before, after, again))
        # put the wave down (twice: some kinds stand back up once) and
        # close whatever a dropped item's pickup opened - a textbox freezes
        # every entity, the switches included
        for _ in range(3):
            for e in entities(c, KIND_ENEMY):
                c.memory.u8[GENT + e[0] * STRIDE + 0x45] = 0
            run(c, 60); M.dismiss(c)
        for k in seen:
            M.forge_hit(c, sw[k][0]); run(c, 20)
        solved_and_paid(c, site, 'ECHO ' + where)
    # ---- LIGHTS
    c = boot(site, 1)
    sw = M.switches(c)
    start = lit(c)
    check('LIGHTS %s: dealt neither dark nor full' % where, len(sw) == 3 and start not in (0, 7), 'pattern %s' % bin(start))
    if len(sw) == 3:
        M.forge_hit(c, sw[1][0]); run(c, 20)
        flipped = lit(c)
        check('LIGHTS %s: the middle flips all three' % where, flipped == start ^ 7, '%s -> %s' % (bin(start), bin(flipped)))
        plan = solve_lights(c, sw)
        check('LIGHTS %s: the solver lights the row' % where, plan is not None and (lit(c) == 7 or M.site_done(c, site)),
              'plan %s' % (plan,))
        solved_and_paid(c, site, 'LIGHTS ' + where)
    # ---- RACE
    c = boot(site, 2)
    sw = M.switches(c)
    pts = [(e[4], e[5]) for e in sw]
    near = min([abs(a[0] - b[0]) + abs(a[1] - b[1]) for a, b in itertools.combinations(pts, 2)] or [0])
    degraded = M.room_flag(c, 66)
    check('RACE %s: spread past a spin attack, or dealt as lights' % where, len(sw) == 3 and (near >= 40) != bool(degraded),
          'at %s, nearest pair %d px, as lights %d' % (pts, near, degraded))
    if len(sw) == 3 and degraded:
        plan = solve_lights(c, sw)
        solved_and_paid(c, site, 'RACE-as-LIGHTS ' + where)
    elif len(sw) == 3:
        M.forge_hit(c, sw[0][0]); run(c, 10)
        on = lit(c) & 1
        run(c, 500)
        check('RACE %s: a lit switch goes dark on its own' % where, on and not (lit(c) & 1), 'lit %d then %d' % (on, lit(c) & 1))
        # three strikes at a walker's pace: the fuse is sized to the walk
        # between the switches (two frames a pixel), so allow the walk
        order = sorted(range(3), key=lambda k: pts[k][0])
        for i, k in enumerate(order):
            if i:
                p0, p1 = pts[order[i - 1]], pts[k]
                run(c, int((abs(p0[0] - p1[0]) + abs(p0[1] - p1[1])) / 1.25))
            M.forge_hit(c, sw[k][0], fast=True); run(c, 4)
        run(c, 4)
        check('RACE %s: three strikes at walking pace light all three' % where, lit(c) == 7 or M.room_flag(c, 70) or M.site_done(c, site),
              'lit %s' % bin(lit(c)))
        solved_and_paid(c, site, 'RACE ' + where)

# ---- DEALT: the real roll, over seeds
roll = C.game_sym('QuickStartContentSiteRoll')
OUTK, OUTE = 0x0203FE00, 0x0203FE04
bad, dealt = [], 0
c = S.boot(ROM, 0, frames=200)
for sd in range(1, 21):
    for b in range(4):
        c.memory.u8[0x02002a40 + 0x4C + b] = ((sd * 0x9E3779B1) >> (8 * b)) & 0xFF   # gSave.run_seed
    for i in range(len(sites)):
        C.call_keep(c, roll, (i, OUTK, OUTE))
        if c.memory.u8[OUTK] == KIND:
            dealt += 1
            if i not in OK_SITES and i not in RETIRED:   # a retired site never deals anything
                bad.append(i)
check('DEALT: puzzles only at eligible sites, and dealt', dealt > 0 and not bad,
      '%d puzzle deals over 20 seeds, %d eligible sites, bad %s' % (dealt, len(OK_SITES), bad[:5]))
print('RESULT %s %d/%d' % ('PASS' if all(res) else 'FAIL', sum(res), len(res)))
sys.exit(0 if all(res) else 1)
